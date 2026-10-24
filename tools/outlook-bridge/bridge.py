"""Outlook.Application stand-in for SoftOne print -> E-Mail.

SoftOne drives Outlook through COM. This script registers (per user) as the
Outlook.Application COM server, records what SoftOne puts in the mail item and
opens a small window that sends the message via SMTP from info@crazysouvle.gr.

Usage:
  pythonw bridge.py --serve            (started by COM)
  python  bridge.py --set-password     (stores the mailbox password in Windows Credential Manager)
  python  bridge.py --compose job.json (window; started by the COM server)
  python  bridge.py --check            (tests SMTP/IMAP login, sends nothing)
"""

import datetime
import email.utils
import html
import imaplib
import json
import os
import re
import shutil
import smtplib
import ssl
import subprocess
import sys
import tempfile
import time
import traceback
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
_VENV_SITE = os.path.join(HERE, ".venv", "Lib", "site-packages")
if os.path.isdir(_VENV_SITE):
    import site

    site.addsitedir(_VENV_SITE)
CLSID = "{0006F03A-0000-0000-C000-000000000046}"
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "OutlookBridge")
LOG_FILE = os.path.join(DATA_DIR, "bridge.log")


def log(msg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} [{os.getpid()}] {msg}\n")


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- COM objects

DISPATCH_PROPERTYPUT = 4
DISPATCH_PROPERTYPUTREF = 8


def _wrap(obj):
    from win32com.server.policy import DynamicPolicy
    from win32com.server.util import wrap

    return wrap(obj, usePolicy=DynamicPolicy)


class _Dyn:
    """Base for late-bound objects: logs every call, tolerates unknown members."""

    kind = "Object"

    def __init__(self):
        self.props = {}

    def _query_interface_(self, iid):
        log(f"{self.kind} QI {iid} -> not supported")
        return 0

    def _dynamic_(self, name, lcid, wflags, args):
        lname = name.lower()
        args = list(args)
        is_put = bool(wflags & (DISPATCH_PROPERTYPUT | DISPATCH_PROPERTYPUTREF))
        log(f"{self.kind}.{name} flags={wflags} put={is_put} args={args!r}"[:500])
        try:
            if is_put:
                self.props[lname] = args[-1] if args else None
                self.on_put(lname, self.props[lname])
                return None
            return self.call(lname, args)
        except Exception:
            log("ERROR " + traceback.format_exc())
            raise

    def on_put(self, lname, value):
        pass

    def call(self, lname, args):
        if lname in self.props:
            return self.props[lname]
        return _wrap(Stub(f"{self.kind}.{lname}"))


class Stub(_Dyn):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind

    def call(self, lname, args):
        if lname in self.props:
            return self.props[lname]
        if lname in ("count",):
            return 0
        if lname in ("resolve", "resolveall"):
            return True
        if lname in ("name", "address", "displayname", "version"):
            return "16.0.0.0" if lname == "version" else "info@crazysouvle.gr"
        return _wrap(Stub(f"{self.kind}.{lname}"))


class Recipient(_Dyn):
    kind = "Recipient"

    def __init__(self, address, rtype=1):
        super().__init__()
        self.props.update({"address": address, "name": address, "type": rtype})

    def call(self, lname, args):
        if lname in ("resolve",):
            return True
        if lname == "resolved":
            return True
        return super().call(lname, args)


class Collection(_Dyn):
    def __init__(self, kind, factory):
        super().__init__()
        self.kind = kind
        self.items = []
        self.factory = factory

    def call(self, lname, args):
        if lname == "add":
            item = self.factory(*args)
            self.items.append(item)
            return _wrap(item)
        if lname == "count":
            return len(self.items)
        if lname in ("item", "_value_") and args:
            return _wrap(self.items[int(args[0]) - 1])
        if lname in ("resolveall",):
            return True
        if lname == "remove" and args:
            self.items.pop(int(args[0]) - 1)
            return None
        return super().call(lname, args)


class Attachment(_Dyn):
    kind = "Attachment"

    def __init__(self, source, *rest):
        super().__init__()
        source = str(source)
        os.makedirs(os.path.join(DATA_DIR, "att"), exist_ok=True)
        stamp = time.strftime("%Y%m%d%H%M%S")
        copy = os.path.join(DATA_DIR, "att", f"{stamp}_{os.path.basename(source)}")
        try:
            shutil.copyfile(source, copy)
        except OSError:
            log(f"cannot copy attachment {source!r}: {traceback.format_exc()}")
            copy = source
        display = rest[2] if len(rest) >= 3 and rest[2] else os.path.basename(source)
        self.props.update({"pathname": copy, "filename": str(display), "displayname": str(display)})


class MailItem(_Dyn):
    kind = "MailItem"

    def __init__(self):
        super().__init__()
        self.recipients = Collection("Recipients", lambda addr, *a: Recipient(str(addr)))
        self.attachments = Collection("Attachments", Attachment)
        self.done = False

    def call(self, lname, args):
        if lname == "recipients":
            return _wrap(self.recipients)
        if lname == "attachments":
            return _wrap(self.attachments)
        if lname in ("display", "send"):
            self.launch(auto_send=(lname == "send"))
            return None
        if lname in ("save", "close", "delete"):
            return None
        if lname in ("to", "cc", "bcc", "subject", "body", "htmlbody"):
            return self.props.get(lname, "")
        if lname == "sent":
            return self.done
        return super().call(lname, args)

    def job(self):
        to = [self.props.get("to", "")]
        cc = [self.props.get("cc", "")]
        bcc = [self.props.get("bcc", "")]
        for r in self.recipients.items:
            {1: to, 2: cc, 3: bcc}.get(int(r.props.get("type") or 1), to).append(
                str(r.props.get("address", ""))
            )
        join = lambda xs: "; ".join(x for x in (str(v).strip() for v in xs) if x)  # noqa: E731
        return {
            "to": join(to),
            "cc": join(cc),
            "bcc": join(bcc),
            "subject": str(self.props.get("subject", "") or ""),
            "body": str(self.props.get("body", "") or ""),
            "htmlbody": str(self.props.get("htmlbody", "") or ""),
            "attachments": [a.props["pathname"] for a in self.attachments.items],
        }

    def launch(self, auto_send):
        if self.done:
            return
        self.done = True
        job = self.job()
        job["auto_send"] = auto_send
        path = os.path.join(DATA_DIR, f"job_{time.strftime('%Y%m%d%H%M%S')}_{os.getpid()}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=1)
        log(f"launch compose job={path} {json.dumps(job, ensure_ascii=False)}"[:1000])
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pyw):
            pyw = sys.executable
        subprocess.Popen([pyw, os.path.abspath(__file__), "--compose", path], close_fds=True)


class OutlookApplication(_Dyn):
    kind = "Application"
    _reg_clsid_ = CLSID
    _reg_progid_ = "Outlook.Application"

    def __init__(self):
        super().__init__()
        log(f"Application created pid={os.getpid()}")

    def call(self, lname, args):
        if lname == "createitem":
            return _wrap(MailItem())
        if lname == "version":
            return "16.0.0.0"
        if lname == "name":
            return "Outlook"
        if lname == "quit":
            return None
        return super().call(lname, args)


def serve():
    import pythoncom
    import win32api
    from win32com.server import factory

    os.makedirs(DATA_DIR, exist_ok=True)
    sys.stdout = sys.stderr = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    log(f"serve start exe={sys.executable} argv={sys.argv}")
    import win32event
    import winerror

    embedded = any(a.lower() in ("-embedding", "/embedding") for a in sys.argv)
    mutex = None
    if not embedded:
        mutex = win32event.CreateMutex(None, False, "Local\\OutlookBridgeServer")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            log("serve: already running, exit")
            return
    try:
        pythoncom.CoInitialize()
        infos = factory.RegisterClassFactories([CLSID])
        pythoncom.CoResumeClassObjects()
        log(f"serve factory registered embedded={embedded}")
        if embedded:
            import threading

            import win32con

            tid = win32api.GetCurrentThreadId()
            threading.Timer(
                900, lambda: win32api.PostThreadMessage(tid, win32con.WM_QUIT, 0, 0)
            ).start()
        pythoncom.PumpMessages()
        factory.RevokeClassFactories(infos)
        pythoncom.CoUninitialize()
    except Exception:
        log("serve FAILED " + traceback.format_exc())
    log("serve stop")
    del mutex


# ------------------------------------------------------------ password store


def get_password(cfg):
    import win32cred

    cred = win32cred.CredRead(cfg["credential_target"], win32cred.CRED_TYPE_GENERIC)
    blob = cred["CredentialBlob"]
    return blob.decode("utf-16-le") if isinstance(blob, bytes) else str(blob)


def set_password(cfg):
    import getpass

    import win32cred

    pw = getpass.getpass(f"Κωδικός για {cfg['from_address']} (δεν φαίνεται όσο γράφεις): ").strip()
    if not pw:
        print("Κενός κωδικός, δεν αποθηκεύτηκε.")
        return 1
    win32cred.CredWrite(
        {
            "Type": win32cred.CRED_TYPE_GENERIC,
            "TargetName": cfg["credential_target"],
            "UserName": cfg["from_address"],
            "CredentialBlob": pw,
            "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
        },
        0,
    )
    print("Αποθηκεύτηκε. Έλεγχος σύνδεσης...")
    return check(cfg)


def check(cfg):
    pw = get_password(cfg)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"], context=ctx, timeout=30) as s:
        s.login(cfg["from_address"], pw)
    print("SMTP OK")
    m = imaplib.IMAP4_SSL(cfg["imap_host"], cfg["imap_port"], ssl_context=ctx)
    m.login(cfg["from_address"], pw)
    m.logout()
    print("IMAP OK")
    return 0


# ------------------------------------------------------------------- sending


def split_addrs(value):
    return [a.strip() for a in re.split(r"[;,]", value or "") if a.strip()]


def html_to_text(value):
    value = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", value)
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def build_message(cfg, job):
    msg = EmailMessage()
    msg["From"] = email.utils.formataddr((cfg["from_name"], cfg["from_address"]))
    msg["To"] = ", ".join(split_addrs(job["to"]))
    if split_addrs(job.get("cc")):
        msg["Cc"] = ", ".join(split_addrs(job["cc"]))
    msg["Subject"] = job.get("subject", "")
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain=cfg["from_address"].split("@")[1])
    body = job.get("body") or ""
    if job.get("htmlbody") and not job.get("body_edited"):
        msg.set_content(body or html_to_text(job["htmlbody"]))
        msg.add_alternative(job["htmlbody"], subtype="html")
    else:
        msg.set_content(body)
    for path in job.get("attachments", []):
        with open(path, "rb") as f:
            data = f.read()
        name = re.sub(r"^\d{14}_", "", os.path.basename(path))
        maintype, subtype = (
            ("application", "pdf")
            if name.lower().endswith(".pdf")
            else (
                "application",
                "octet-stream",
            )
        )
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    return msg


def send(cfg, job):
    msg = build_message(cfg, job)
    rcpts = split_addrs(job["to"]) + split_addrs(job.get("cc")) + split_addrs(job.get("bcc"))
    if not rcpts:
        raise ValueError("Δεν υπάρχει παραλήπτης")
    pw = get_password(cfg)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"], context=ctx, timeout=60) as s:
        s.login(cfg["from_address"], pw)
        s.send_message(msg, from_addr=cfg["from_address"], to_addrs=rcpts)
    log(f"sent to={rcpts} subject={job.get('subject')!r}")
    try:
        m = imaplib.IMAP4_SSL(cfg["imap_host"], cfg["imap_port"], ssl_context=ctx)
        m.login(cfg["from_address"], pw)
        m.append(
            cfg["imap_sent_folder"],
            "\\Seen",
            imaplib.Time2Internaldate(time.time()),
            msg.as_bytes(),
        )
        m.logout()
    except Exception:
        log("IMAP append failed " + traceback.format_exc())


def compose(job_path):
    import tkinter as tk
    from tkinter import messagebox

    cfg = load_config()
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)

    if job.get("auto_send"):
        root = tk.Tk()
        root.withdraw()
        try:
            send(cfg, job)
            messagebox.showinfo("E-Mail", f"Στάλθηκε στο {job['to']}")
        except Exception as e:
            log("send failed " + traceback.format_exc())
            messagebox.showerror("E-Mail", f"Αποτυχία αποστολής:\n{e}")
        return

    root = tk.Tk()
    root.title(f"Αποστολή από {cfg['from_address']}")
    root.attributes("-topmost", True)
    fields = {}
    for row, (key, label) in enumerate([("to", "Προς"), ("cc", "Κοιν."), ("subject", "Θέμα")]):
        tk.Label(root, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=2)
        var = tk.StringVar(value=job.get(key, ""))
        tk.Entry(root, textvariable=var, width=80).grid(row=row, column=1, sticky="we", padx=4)
        fields[key] = var
    body_text = job.get("body") or html_to_text(job.get("htmlbody", ""))
    text = tk.Text(root, width=80, height=12)
    text.insert("1.0", body_text)
    text.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
    names = ", ".join(
        re.sub(r"^\d{14}_", "", os.path.basename(p)) for p in job.get("attachments", [])
    )
    tk.Label(root, text=f"Συνημμένα: {names or '—'}").grid(
        row=4, column=0, columnspan=2, sticky="w", padx=4
    )

    def do_send():
        job.update({k: v.get() for k, v in fields.items()})
        new_body = text.get("1.0", "end").rstrip("\n")
        if new_body != body_text:
            job["body"], job["body_edited"] = new_body, True
        try:
            send(cfg, job)
        except Exception as e:
            log("send failed " + traceback.format_exc())
            messagebox.showerror("E-Mail", f"Αποτυχία αποστολής:\n{e}", parent=root)
            return
        messagebox.showinfo("E-Mail", f"Στάλθηκε στο {job['to']}", parent=root)
        root.destroy()

    buttons = tk.Frame(root)
    buttons.grid(row=5, column=0, columnspan=2, pady=6)
    tk.Button(buttons, text="Αποστολή", width=14, command=do_send).pack(side="left", padx=6)
    tk.Button(buttons, text="Άκυρο", width=14, command=root.destroy).pack(side="left", padx=6)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(3, weight=1)
    root.mainloop()


def comtest():
    """Creates the COM object in-process exactly as COM would, without the registry launch."""
    import pythoncom
    import win32com.client
    from win32com.server import policy

    try:
        disp = policy.CreateInstance(CLSID, pythoncom.IID_IDispatch)
        app = win32com.client.Dispatch(disp)
        item = app.CreateItem(0)
        item.To = "test@example.com"
        item.Subject = "comtest"
        print(f"comtest OK to={item.To!r} subject={item.Subject!r}")
        log("comtest OK")
        return 0
    except Exception:
        tb = traceback.format_exc()
        print("comtest FAILED\n" + tb)
        log("comtest FAILED " + tb)
        return 1


def main(argv):
    if len(argv) >= 2 and argv[1] == "--serve" or "-Embedding" in argv or "/Embedding" in argv:
        serve()
        return 0
    if len(argv) >= 3 and argv[1] == "--compose":
        compose(argv[2])
        return 0
    if len(argv) >= 2 and argv[1] == "--set-password":
        return set_password(load_config())
    if len(argv) >= 2 and argv[1] == "--selftest":
        import pythoncom  # noqa: F401
        import win32cred  # noqa: F401

        log(f"selftest OK exe={sys.executable}")
        return 0
    if len(argv) >= 2 and argv[1] == "--comtest":
        return comtest()
    if len(argv) >= 2 and argv[1] == "--check":
        return check(load_config())
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except Exception:
        log("FATAL " + traceback.format_exc())
        raise
