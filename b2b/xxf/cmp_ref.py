# B2B-46: συγκρίνει ένα XXF (π.χ. test_out.XXF από το test_xxf.php) με το
# reference template, αποκωδικοποιώντας ανά πεδίο μέσω xsf_ref.
# Χρήση: python cmp_ref.py [αρχείο]   (default: test_out.XXF)
# Επιτρεπτές διαφορές ΜΟΝΟ σε: SOTIME, UPDDATE, APPRVDATE, INSDATE, BGDOCDATE1.
import sys
from xsf_ref import fields, rows, groups_bytes

ALLOWED = {'SOTIME', 'UPDDATE', 'APPRVDATE', 'INSDATE', 'BGDOCDATE1'}

ref = open('../portal/app/xxf_template_7021.XXF', 'rb').read()
new = open(sys.argv[1] if len(sys.argv) > 1 else 'test_out.XXF', 'rb').read()

GA = dict(groups_bytes(ref))
GB = dict(groups_bytes(new))

bad = 0
if set(GA) != set(GB):
    print('GROUPS differ:', set(GA), '!=', set(GB))
    bad = 1
for gname in GA:
    tabsA = dict(GA[gname])
    tabsB = dict(GB.get(gname, []))
    if set(tabsA) != set(tabsB):
        print(gname, 'TABLES differ:', set(tabsA) ^ set(tabsB))
        bad = 1
    for tn in tabsA:
        blobA, blobB = tabsA[tn], tabsB[tn]
        hdrA, fsA, pA = fields(blobA)
        hdrB, fsB, pB = fields(blobB)
        if [f[0] for f in fsA] != [f[0] for f in fsB]:
            print(tn, 'FIELDS differ')
            bad = 1
            continue
        nA, RA, _ = rows(blobA, fsA, pA)
        nB, RB, _ = rows(blobB, fsB, pB)
        if nA != nB:
            print(tn, 'rows', nA, '!=', nB)
            bad = 1
            continue
        for i, ((ra, _), (rb, _)) in enumerate(zip(RA, RB), 1):
            for k in ra:
                va, vb = ra.get(k), rb.get(k)
                if va != vb:
                    mark = 'OK (allowed)' if k in ALLOWED else 'DIFF'
                    print(f'{tn} row{i} {k}: {va!r} -> {vb!r}  {mark}')
                    if k not in ALLOWED:
                        bad = 1
print('PASS' if not bad else 'FAIL')
sys.exit(bad)
