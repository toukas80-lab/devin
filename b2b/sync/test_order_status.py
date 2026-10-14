"""B2B-49: tests για το order_status_rows() του export.py (parsing/merge, χωρίς SQL).

Τρέχει με:  python test_order_status.py   (ή pytest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export import order_status_rows


def test_parses_w_number_from_comments():
    rows = [{"comments": "B2B W-000010", "fincode": "ΠΑΡ0000890",
             "fullytransf": 0}]
    out = order_status_rows(rows)
    assert out == [{"order_no": "W-000010", "fincode": "ΠΑΡ0000890",
                    "done": 0}]


def test_full_transf_marks_done():
    rows = [{"comments": "B2B W-000010", "fincode": "ΠΑΡ0000890",
             "fullytransf": 1}]
    out = order_status_rows(rows)
    assert out[0]["done"] == 1


def test_multiple_findocs_done_if_any_transf():
    # ίδιο order_no σε 2 FINDOC (π.χ. επανεισαγωγή XXF):
    # done=1 αν έστω ένα έχει FULLYTRANSF=1
    rows = [
        {"comments": "B2B W-000010", "fincode": "ΠΑΡ0000890",
         "fullytransf": 0},
        {"comments": "B2B W-000010", "fincode": "ΠΑΡ0000895",
         "fullytransf": 1},
    ]
    out = order_status_rows(rows)
    assert len(out) == 1
    assert out[0]["order_no"] == "W-000010"
    assert out[0]["done"] == 1
    assert out[0]["fincode"] == "ΠΑΡ0000895"


def test_done_stays_when_newer_doc_not_transf():
    rows = [
        {"comments": "B2B W-000010", "fincode": "ΠΑΡ0000890",
         "fullytransf": 1},
        {"comments": "B2B W-000010", "fincode": "ΠΑΡ0000899",
         "fullytransf": 0},
    ]
    out = order_status_rows(rows)
    assert out[0]["done"] == 1


def test_ignores_comments_without_w_number():
    rows = [
        {"comments": "ΓΙΑ ΠΑΡΑΣΚΕΥΗ", "fincode": "ΠΑΡ0000887",
         "fullytransf": 0},
        {"comments": None, "fincode": "ΠΑΡ0000888", "fullytransf": 0},
        {"comments": "", "fincode": "ΠΑΡ0000889", "fullytransf": 0},
        {"comments": "W-00010", "fincode": "ΠΑΡ0000900",
         "fullytransf": 0},  # 5 ψηφία, όχι 6
    ]
    assert order_status_rows(rows) == []


def test_w_number_anywhere_in_comment():
    rows = [{"comments": "B2B W-000007 παράδοση Δευτέρα",
             "fincode": "ΠΑΡ0000888", "fullytransf": 0}]
    out = order_status_rows(rows)
    assert out[0]["order_no"] == "W-000007"


if __name__ == "__main__":
    fns = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for f in fns:
        f()
        print(f"{f.__name__}: OK")
    print(f"{len(fns)} tests passed")
