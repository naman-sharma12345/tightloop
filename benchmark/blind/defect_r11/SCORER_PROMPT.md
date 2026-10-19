# SCORER_PROMPT r11 - instructions for a fresh scorer to reproduce the weighted defect count

You are scoring 9 blind single-page app builds (B01-B09) with a weighted defect count: blocker = 10, major = 3, minor = 1; lower is better. Follow these steps exactly. Do not look for which run or arm made a label, and do not read any judge results, key files or other scorers' folders.

## 0. Inputs
- Builds: `<builds>/B01 .. B09`, each with index.html, styles.css, app.js (SPEC.txt names the spec and is removed before serving).
- Spec per label (from SPEC.txt): trip = B01, B08, B09; habits = B02, B04, B05; invoice = B03, B06, B07.
- This folder (`benchmark/blind/defect_r11/` on branch v6/defect-r11):
  - `CHECKLIST_r11.md` (frozen at commit 4c3b8e79; sha256 7495424dc0ab4f1df375a7802dddf1e1cc4c2e9aee2074b9adbc10d226865e99) - items H01-H35, I01-I40, T01-T31, G01-G18, each with its test, pass condition and default severity. Per build: habits 53 items, invoice 58, trip 49 (spec items + G01-G18).
  - `PROTOCOL.md` - serving, browser and recording rules.
  - `ERRATA_r11.md` - how H15 and I15 are scored where the checklist wording conflicts with the spec.
  - `scorer/` - the full Playwright scripts used for this run.

## 1. Environment
- Python 3.11 with `playwright==1.63` and its Chromium headless shell (`python -m playwright install chromium`).
- At least 3 GB free disk. No outside network is needed (the scripts block every non-127.0.0.1 request).

## 2. Run the scripts (real browser clicks)
```
cd benchmark/blind/defect_r11/scorer
python3 run_all.py <builds> <out>            # all 9, label order, ~75 s per build
python3 run_all.py <builds> <out> B05 B06    # or a subset
```
What it does per build (`run_build.py`):
1. Copies the build to a fresh temp dir as `<tmp>/app/` (SPEC.txt dropped) and serves it with `serve.py` (no-store caching) on 127.0.0.1, one port per build; the server is killed afterwards.
2. Main run at 1280x800 in a fresh context: time zone Asia/Kolkata, locale en-US, clock installed at 2026-10-22T10:00+05:30, outside network aborted and logged, console errors / page errors / HTTP>=400 / native dialogs logged. Runs `steps_<spec>.py:run` (the same logical steps and data for every build of a spec).
3. G probes on the filled app (contrast, unlabelled inputs, CSS checks, Tab walk, focus-ring check, dialog focus trap), delete-accept, import of the exported JSON into a fresh profile, a 375x812 flow (G08-G10, screenshots), and a corrupt-storage load (G05).
4. Writes `<out>/results/<label>.json` (per item: `auto` = true/false/null and `ev` = evidence text) and `<out>/evidence/<label>/` (screenshots, exported files).

`adapters/Bxx.py` hold only the locators/UI primitives for one build (labels, roles, ids, which menu holds Export). They never add or skip a step. Known adapter quirks:
- B05: in the Edit dialog the first mouse click is swallowed while the name text is pre-selected, so the adapter clicks the dialog heading first (the quirk itself is recorded as an unlisted minor).
- Drag (invoice line reorder, trip card move) uses Playwright drag_to, then a manual mouse down/move/up if the order did not change.

## 3. Judge each item (write `verdicts/<label>.json`)
For every checklist item of the build's spec plus G01-G18, read the item's evidence in results/<label>.json and the screenshots, and decide pass or fail against the checklist's pass condition. `auto` is only a hint; the checklist text decides. Items judged visually (G07, G08, dialog layout at 375, print view I34) are judged from the screenshots. G07 and G17 have no line in results/<label>.json: judge G07 from the g07_* screenshots, and G17 from the screenshots plus the state words already in the evidence ("Not done"/"done" labels, status text, conflict text, inline error messages).

Severity rules (from the checklist):
1. A failed item takes its default severity. Items marked [F] are blocker when they fail.
2. Any item escalates to blocker if the feature is absent or does nothing, or if data is lost.
3. One root cause counts once: the item that names it carries the weight; other items it breaks are recorded as `fail-shared-cause` (weight 0, `counted_on`) or blocked-by.
4. Defects outside the checklist go in the separate unlisted column (`unlisted`: severity, weight, evidence) and never into the listed score.

Measurement rules applied the same way to every build:
- G10 touch targets (375): every visible button, input, select and link in the main view and one dialog must be >= 40 px in both directions. Inline text links inside a sentence are exempt; elements <= 2 px are skipped; a checkbox/radio counts with its label box; a control whose own ::before/::after is absolutely positioned (stretched "whole card" target) counts with its positioned ancestor's box. Toast controls that are on screen when the probe runs are measured too.
- G12 focus: a visible change of outline, box-shadow, border, background or text decoration on the focused control; a ring drawn on the control's own ::before/::after counts.
- G07/G08 overlap: transient toasts are not counted as overlapping content. Page-level sideways scroll at 375 fails G08 (or is a shared cause when the same leak is counted on T06).
- G06 (invoice): the invoice row set must be the same after reload; the list order may reset with the sort control (not data).
- H07: if "N per week" is a bounded control (select or 1-7 stepper) where 0 and 8 cannot be entered, it passes.
- H15 and I15: see ERRATA_r11.md.

Verdict file shape: `{"label","spec","items":{"<id>":{"result":"pass"|"fail"|"fail-shared-cause", "severity","weight","evidence","counted_on"}}, "unlisted":[{"severity","weight","evidence"}], "note"}`.

## 4. Make the result files
```
cd benchmark/blind/defect_r11
python3 make_scores.py
```
- `DEFECTS_r11_ns.jsonl`: one line per defect: label, spec, item (or "unlisted"), severity, weight, one-line evidence (shared-cause lines have weight 0).
- `SCORES_r11_ns.jsonl`: one line per build: label, spec, items_tested, items_passed, blocker, major, minor, weighted_score (listed items only), unlisted_score (separate column).
- Report per spec: median first, then mean, of weighted_score.

## 5. Expected result of this run (the scorer's claims)
| label | spec | B | M | m | weighted | unlisted |
|---|---|---|---|---|---|---|
| B01 | trip | 0 | 1 | 0 | 3 | 0 |
| B02 | habits | 0 | 0 | 0 | 0 | 0 |
| B03 | invoice | 0 | 0 | 1 | 1 | 0 |
| B04 | habits | 0 | 0 | 0 | 0 | 0 |
| B05 | habits | 0 | 0 | 0 | 0 | 1 |
| B06 | invoice | 0 | 0 | 1 | 1 | 0 |
| B07 | invoice | 0 | 0 | 0 | 0 | 0 |
| B08 | trip | 0 | 0 | 1 | 1 | 0 |
| B09 | trip | 0 | 0 | 1 | 1 | 0 |

Per spec (median, mean): habits 0, 0.00; invoice 1, 0.67; trip 1, 1.67.
