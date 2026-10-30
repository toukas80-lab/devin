# SYNC-1 — DESKTOP-3MF73OK (μαγαζί)

## hostname
DESKTOP-3MF73OK

## AGENTS.md — 6 πρώτες γραμμές
```
# Οδηγίες για Devin CLI (PC μαγαζιού DESKTOP-3MF73OK)

## ΚΟΙΝΕΣ ΟΔΗΓΙΕΣ (σπίτι + μαγαζί) — ΠΡΩΤΑ ΑΥΤΟ
Σε κάθε εκκίνηση και πριν από κάθε εντολή: git fetch origin και git show origin/cli/koina:cli/KOINA.md. Διάβασέ το όλο και ακολούθησέ το. Υπερισχύει αυτού του αρχείου.

## Ρόλος
```
Η ενότητα «## CNC (λέξη: cnc ή ψνψ) — ΠΡΟΤΕΡΑΙΟΤΗΤΑ» δεν υπήρχε στο AGENTS.md (τίποτα δεν σβήστηκε). Η αλλαγή έμεινε τοπική (untracked αρχείο) — ΔΕΝ έγινε commit.

## git -C ..\devin-cnc log --oneline -1
```
49feea6 cnc CLI.md: same for home and shop PC (paths via $HOME, first-run setup of devin-cnc/uv/cdr2xhtml)
```

## Βήμα 2 — CNC προετοιμασία (..\devin-cnc\cnc\CLI.md §1)
- Worktree `..\devin-cnc`: ΔΕΝ υπήρχε → `git worktree add --detach ..\devin-cnc origin/cnc/fylla-01` (HEAD 49feea6)
- `uv`: έλειπε → `winget install --id astral-sh.uv -e` → **uv 0.13.6** (WinGet πρόσθεσε PATH· στο τρέχον shell τρέχει από το package path)
- `C:\msys64\ucrt64\bin\cdr2xhtml.exe`: έλειπε (δεν υπήρχε καθόλου `C:\msys64`) → `winget install --id MSYS2.MSYS2 -e` + `pacman -S --noconfirm mingw-w64-ucrt-x86_64-libcdr` → **cdr2xhtml 0.1.9**
- `$HOME\Dropbox\devin\ΠΡΟΤΥΠΑ`: υπάρχει
- `git show origin/cli/koina:cli/KOINA.md`: διαβάστηκε — κοινές οδηγίες + CNC §1 (worktree/uv/cdr2xhtml/Dropbox), reports σε `runs/*.md` στα `data/*`
