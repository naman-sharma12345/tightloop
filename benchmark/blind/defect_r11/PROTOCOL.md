# PROTOCOL r11 - how the defect hunt is run

Goal: a weighted defect count per build (blocker 10, major 3, minor 1; lower is better), using CHECKLIST_r11.md, which was written from the 3 specs only and committed before any build was opened.

## Inputs
- builds B01..B09 (index.html, styles.css, app.js, SPEC.txt), random labels. The tester does not know which run or arm made a label and does not try to find out. No build is hashed or diffed against anything outside the input folder.
- specs/habits.md, invoice.md, trip.md (sha256 in the checklist).

## Order and blindness
- Builds are tested one at a time, in label order B01..B09. The checklist is not changed after the first build is opened.
- The tester reads only the input folder, this branch, and its own task folder.

## Serving
- Each build alone: its files are copied to a fresh temp folder as <tmp>/app/, then served with
  python3 /home/user/tab/work/tl_blind_appv2b/benchmark/blind/serve.py <tmp> <port> on 127.0.0.1 (one port per build, no-store caching).
- The app is opened at http://127.0.0.1:<port>/app/ (tests relative paths, G03).
- The server is started with Popen (own kill, no shell), and killed after the build.

## Browser
- Headless Chromium via Playwright (Python, 1.63), a fresh browser context per build (new profile, empty localStorage), a fresh context again for G05 (corrupt storage) and for the import-into-fresh-profile steps.
- No outside network: every request to a host other than 127.0.0.1 is aborted and logged (G02).
- Time zone Asia/Kolkata, locale en-US, clock installed at Thu 22 Oct 2026 10:00 local (page.clock.install). Items that need other days move the clock with page.clock.set_system_time + reload (data made through the app's own UI), or run the clock forward (page.clock.run_for) for the midnight items.
- Viewports: 1280x800 for the main run; 375x812 for G08-G10 and spot checks of the main views and one dialog.
- Native dialogs: confirm() is answered dismiss or accept as each item says; every dialog event is logged with its type.
- Downloads are accepted and the files are read for the export items.
- Console messages of type error and pageerror events are logged for the whole run (G01).

## Steps
- Every build of a spec gets the same logical steps in the same order, with the same data (names, dates, amounts as written in the checklist). Only the locator for a control (its label, role or text in that build) is adapted per build; no step is added or skipped for one build.
- Real clicks and key presses (Playwright click, fill/type, keyboard.press, drag_to; manual mouse down/move/up as a second try for drag).
- Visual items (G07, G08, layout of dialogs, print view) are judged from screenshots, which are kept small (PNG, viewport only) as evidence under the task folder; extras are deleted.
- A step that cannot run because an earlier root cause broke its setup is marked blocked-by <id> (counted once, rule 3 of the checklist).

## Recording
- DEFECTS_r11_ns.jsonl: one line per defect: label, spec, item (or "unlisted"), severity word, weight, one-line evidence (what was done, what happened).
- SCORES_r11_ns.jsonl: one line per build: label, spec, items tested, items passed, blocker/major/minor counts, weighted score (listed items only), unlisted weighted score.
- Both committed (fast-forward) on v6/defect-r11 after all 9 builds. Scores are the tester's claims.
