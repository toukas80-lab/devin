"""Upload b2b/out/*.json to the B2B portal sync API.

Config lives in b2b/sync/local.json (gitignored):
    {"base_url": "https://ksilakia.gr/b2b", "token": "..."}
"""
import gzip
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATASETS = ["item_groups", "items", "customers", "prices", "ledger", "invoices"]
# dataset name -> file under b2b/out (export.py writes groups.json)
FILES = {"item_groups": "groups.json"}


def main():
    cfg = json.loads((BASE / "local.json").read_text("utf-8"))
    url = cfg["base_url"].rstrip("/") + "/api/sync"
    for ds in DATASETS:
        body = (BASE.parent / "out" / FILES.get(ds, f"{ds}.json")).read_bytes()
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
