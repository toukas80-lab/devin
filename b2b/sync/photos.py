"""B2B-13: κατέβασμα φωτογραφιών ειδών από Google Drive -> b2b/out/photos/<code>.jpg.

Για κάθε είδος του b2b/out/items.json (πεδίο `photo` = Drive file id):
1. δοκιμή https://drive.google.com/uc?export=download&id=<photo>
2. αν το αποτέλεσμα δεν είναι εικόνα, αναζήτηση <code>.jpg στον δημόσιο
   φάκελο (embeddedfolderview) και λήψη από εκεί.
Pillow: μέγιστη πλευρά 800px, JPEG ποιότητα 80.
"""
import io
import json
import re
import time
import urllib.request
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent.parent / "out"
PHOTOS = BASE / "photos"
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


def folder_map():
    """filename.lower() -> file id, από το embedded folder view."""
    html = fetch(LIST_URL, timeout=120).decode("utf-8", "replace")
    return {n.strip().lower(): i for i, n in ENTRY_RE.findall(html)}


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


def main():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    items = json.loads((BASE / "items.json").read_text(encoding="utf-8"))
    fmap = folder_map()
    print(f"folder entries: {len(fmap)}")
    stats = {"drive": 0, "folder": 0, "skip": 0, "fail": 0}
    for it in items:
        code = re.sub(r'[\\/:*?"<>|]', "_", str(it.get("code", "")).strip())
        dest = PHOTOS / f"{code}.jpg" if code else None
        if dest is None or dest.exists():
            stats["skip"] += 1
            continue
        im = None
        pid = str(it.get("photo") or "")
        if pid:
            try:
                im = load_image(fetch(DL.format(pid)))
                if im is not None:
                    stats["drive"] += 1
            except Exception:
                pass
        if im is None:
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
    print(f"photos: {stats} of {len(items)} items")


if __name__ == "__main__":
    main()
