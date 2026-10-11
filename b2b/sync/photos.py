"""B2B-13b: φωτογραφίες ειδών -> b2b/out/photos/<code>.jpg, με cache.

Cache: b2b/out/photos_cache.json -> {"<code>": {"photo": <drive id>, "sha1": <hex>}}.
Είδος ξανακατεβαίνει ΜΟΝΟ αν λείπει το jpg, ή το photo διαφέρει από το cache,
ή δόθηκε --full. jpg χωρίς cache entry (παλιό run) θεωρείται τρέχον και γίνεται
seed στο cache (ίδιο photo id), χωρίς κλήση στο Drive.
Η λίστα του δημόσιου φακέλου κατέβαίνει μόνο όταν χρειαστεί fallback, μία φορά.
Στο τέλος ξαναγράφεται το items.json: μόνο είδη με jpg, με img_ver = sha1[:12].
"""
import hashlib
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent.parent / "out"
PHOTOS = BASE / "photos"
CACHE_FILE = BASE / "photos_cache.json"
ITEMS_FILE = BASE / "items.json"
FOLDER = "11pGGgh6Mg3DwjOprwqc1fg_3Qy2SGEHq"
LIST_URL = f"https://drive.google.com/embeddedfolderview?id={FOLDER}"
DL = "https://drive.google.com/uc?export=download&id={}"
ENTRY_RE = re.compile(
    r'id="entry-([A-Za-z0-9_-]{20,})".*?flip-entry-title">([^<]+)<', re.S)
UA = {"User-Agent": "Mozilla/5.0 (b2b photo sync)"}


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


_fmap = None


def folder_map():
    """lazy: filename.lower() -> file id, από το embedded folder view."""
    global _fmap
    if _fmap is None:
        html = fetch(LIST_URL, timeout=120).decode("utf-8", "replace")
        _fmap = {n.strip().lower(): i for i, n in ENTRY_RE.findall(html)}
    return _fmap


def load_image(data):
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
        return im
    except Exception:
        return None


def save_jpg(im, path):
    im.thumbnail((800, 800))
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    im.save(path, "JPEG", quality=80)


def sha1_file(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()


def safe_code(code):
    return re.sub(r'[\\/:*?"<>|]', "_", str(code).strip())


def main():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    full = "--full" in sys.argv
    try:
        items = json.loads(ITEMS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"items.json unreadable: {e}")
        sys.exit(1)
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    stats = {"drive": 0, "folder": 0, "cached": 0, "fail": 0}
    for it in items:
        code = safe_code(it.get("code", ""))
        if not code:
            stats["fail"] += 1
            continue
        dest = PHOTOS / f"{code}.jpg"
        pid = str(it.get("photo") or "")
        ent = cache.get(code) or {}
        if not full and dest.exists():
            if ent.get("photo") == pid:
                stats["cached"] += 1
                continue
            if "photo" not in ent:
                cache[code] = {"photo": pid, "sha1": sha1_file(dest)}
                stats["cached"] += 1
                continue
        im = None
        if pid:
            try:
                im = load_image(fetch(DL.format(pid)))
                if im is not None:
                    stats["drive"] += 1
            except Exception:
                pass
        if im is None:
            fmap = folder_map()
            fid = fmap.get(f"{code}.jpg".lower()) or next(
                (x for n, x in fmap.items()
                 if n.rsplit(".", 1)[0] == code.lower()), None)
            if fid:
                try:
                    im = load_image(fetch(DL.format(fid)))
                    if im is not None:
                        stats["folder"] += 1
                except Exception:
                    pass
        if im is None:
            stats["fail"] += 1
            continue
        save_jpg(im, dest)
        time.sleep(0.1)

    kept = []
    missing = []
    new_cache = {}
    for it in items:
        code = safe_code(it.get("code", ""))
        dest = PHOTOS / f"{code}.jpg" if code else None
        if dest is None or not dest.exists():
            if code:
                missing.append(code)
            continue
        sha1 = sha1_file(dest)
        it["img_ver"] = sha1[:12]
        kept.append(it)
        new_cache[code] = {"photo": str(it.get("photo") or ""), "sha1": sha1}

    if not kept:
        print("no items left with photo")
        sys.exit(2)
    ITEMS_FILE.write_text(
        json.dumps(kept, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    CACHE_FILE.write_text(
        json.dumps(new_cache, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"items: {len(items)} -> {len(kept)}")
    print(f"drive={stats['drive']} folder={stats['folder']} "
          f"cached={stats['cached']} fail={stats['fail']}")
    print("no photo:", ",".join(missing) if missing else "-")


if __name__ == "__main__":
    main()
