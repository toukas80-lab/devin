"""Upload b2b/out/*.json to the B2B portal sync API.

Config lives in b2b/sync/local.json (gitignored):
    {"base_url": "https://ksilakia.gr/b2b", "token": "..."}
"""
import gzip
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / "out"
UPLOADED = OUT / "photos_uploaded.json"
DATASETS = ["item_groups", "items", "customers", "prices", "ledger", "invoices",
            "order_status"]
# dataset name -> file under b2b/out (export.py writes groups.json)
FILES = {"item_groups": "groups.json"}


def save_uploaded(data):
    UPLOADED.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")


def upload_images(cfg):
    """POST b2b/out/photos/<code>.jpg στο /api/image όταν αλλάζει το img_ver."""
    try:
        uploaded = json.loads(UPLOADED.read_text("utf-8"))
    except Exception:
        uploaded = {}
    items = json.loads((OUT / "items.json").read_text("utf-8"))
    url = cfg["base_url"].rstrip("/") + "/api/image"
    sent = 0
    posts = 0
    for it in items:
        code = str(it.get("code") or "")
        ver = str(it.get("img_ver") or "")
        if not code or not ver or uploaded.get(code) == ver:
            continue
        try:
            body = (OUT / "photos" / f"{code}.jpg").read_bytes()
        except OSError:
            print(f"image {code}: file missing, skipped")
            continue
        posts += 1
        req = urllib.request.Request(
            f"{url}?code={urllib.parse.quote(code, safe='')}",
            data=body,
            method="POST",
            headers={
                "Content-Type": "image/jpeg",
                "X-Sync-Token": cfg["token"],
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
            uploaded[code] = ver
            sent += 1
            if sent % 50 == 0:
                save_uploaded(uploaded)
        except urllib.error.HTTPError as e:
            e.read()
            if posts == 1 and e.code == 404:
                print("image endpoint not deployed yet")
                break
            print(f"image {code}: HTTP {e.code}")
        except Exception as e:
            print(f"image {code}: {e}")
    save_uploaded(uploaded)
    print(f"images: {sent} uploaded")


def main():
    cfg = json.loads((BASE / "local.json").read_text("utf-8"))
    upload_images(cfg)
    url = cfg["base_url"].rstrip("/") + "/api/sync"
    for ds in DATASETS:
        body = (OUT / FILES.get(ds, f"{ds}.json")).read_bytes()
        req = urllib.request.Request(
            f"{url}?dataset={ds}",
            data=gzip.compress(body),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Encoding": "gzip",
                "X-Sync-Token": cfg["token"],
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                print(f"{ds}: {r.status} {r.read().decode('utf-8', 'replace')}")
        except urllib.error.HTTPError as e:
            print(f"{ds}: HTTP {e.code} {e.read().decode('utf-8', 'replace')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
