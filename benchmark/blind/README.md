# Blind app bake-off (pass 3 side study)

Naman asked (Oct 18, via Pally) for small apps built once per arm and judged blind by looking.
The repo's existing app specs (benchmark/apps/app-01..04) are command-line tools with nothing to look at,
so three short visual web-app specs were written for this study: specs/todo.md, specs/notes.md, specs/units.md.
Each spec text is the whole prompt, identical for every arm. Arms: no-skill, ponytail (pinned), tightloop-v4
(no v4c existed in the repo when the study started; v4 is .claude/skills/tightloop at fd48849).
One fresh claude -p session per build, same model, skill delivered exactly as runner.py does it
(skill folder in the workspace + --append-system-prompt), via blind_driver.py which imports runner.py.
checks/check_app.py is a hidden smoke check (never shown to the agent) and also takes the screenshot
in an identical demo state for every build. Labels A/B/C are shuffled per app; the key is sealed until Naman picks.

## Delivery rule (added after round 1)
Round 1 gave all 9 builds the same run line (`python3 -m http.server 8000`) and the same file names, and the blinding step set every file date
equal. A browser then shows the first build's cached files for the next ones (python's server answers 304 on equal dates).
From round 2: each label gets its own port (e.g. todo A/B/C = 8001/8002/8003, notes 8011-8013, units 8021-8023), file dates are not set equal,
and the run line tells the judge to open a fresh private window. check_app.py now also fails on any console or page error, and for the
unit converter it requires a typed value to change the result to the expected number. Reference apps and two negative controls are in checks/reference/.

## Harness v2 (Pally m:5a251122 / m:c920b547), before round 2
- `serve.py <dir> <port>`: static server with `Cache-Control: no-store` that ignores conditional requests (always 200). One port per label.
- `checks/check_app.py <app> <dir> <shot> <out.json> [label.zip] [port]` now also checks that (a) the bytes the browser loaded, and a fresh fetch of every file, match the label's zip; (b) every visible button changes page state (each button is tried from a fresh demo state, then with the empty text fields filled, then after each other button has acted); (c) for the converter, a typed value changes the result to the expected number; and (d) there are no console errors or uncaught page errors.
- Self-test (18:15Z): references todo 10/10, notes 8/8, units 14/14. Negative controls fail as they should: units_dead 10/14 (conversions + typed-change), todo_err 9/10 (errors), todo_deadbtn 9/10 ("Sort" does nothing), and units/A's files checked against units/C's zip fail the bytes check. All 9 round-1 builds pass every check, each on its own port 8001-8009 (todo 10/10 x3, notes 8/8 x3, units 14/14 x3), units/C included. That fits the cache finding: units/C works when it is served on its own port.

## Round 2 harness (Pally m:92db7ccb, m:699f008f, m:c9c6e9cc)
Specs: specs/r2/{bookmarks,expenses,kanban}.md (fixed at 3e86a80). Key sha256 committed at bc4b673 (results/blind_r2_key_sha256.txt), before any build.
Versions: no-skill, ponytail, tightloop-v4, tightloop-v4c; labels A-D shuffled per app.
- checks/check_app.py, round-2 apps:
  - Native dialogs: the checker answers every dialog through page.on('dialog') and records its type. A delete is checked twice:
    Cancel must keep the item and a `confirm` dialog must have appeared; OK must remove it. A delete with no confirm() fails both.
  - Kanban drag: first REAL mouse events (down, stepped moves, up; in Chromium this also fires native HTML5 drag events on
    draggable elements). If the card did not move, synthetic HTML5 events follow (dragstart/dragenter/dragover/drop/dragend sharing
    one DataTransfer). The move counts if either works. `drag_method` and the drag events the page received are logged per build.
    `BLIND_DRAG_ONLY=pointer|html5` forces one path; it is used only for the self-test.
  - Kanban modal: #card-title, #card-desc and #card-delete inside #card-modal.
  - Expenses: #date is filled inside the month #month shows. #month must default to the current month. #total must hold only
    the number (no letters). Edit is .edit, then the field holding 4.50 changed to 5.50, then #save-edit. A past month is picked
    and an expense dated inside it must show in that month's list and total, and not in the current month's. The CSV header row
    is checked.
  - Bookmarks: .edit/.delete on every card. Export must be a JSON array of {title, url, tags[], folder}. Import goes through the
    input[type=file] in #import with one duplicate URL and one new one (3 -> 4).
  - 375 px: document.documentElement.scrollWidth <= viewport width at 375 px wide, for expenses and bookmarks. Kanban is excepted
    (its board scrolls sideways by design). For the other apps the number is recorded, not checked.
- Reference apps and controls in checks/reference/:
  - kanban (HTML5 dnd only), kanban_pointer (mouse events only), kanban_nodnd (no drag);
  - expenses, expenses_noconfirm, expenses_overflow (600 px strip), expenses_ignoredate (always saves today);
  - bookmarks, bookmarks_noconfirm.
- viewer/: one zip, one server. Every version is on its own port/origin with no-store. 4 panels per app. The viewer port answers
  only /, /index.html and /manifest.json, and there are no directory listings, so the only things reachable are the build
  folders. verify_viewer.py fetches every reachable file from every port and greps the bytes for the version names
  (no-skill, ponytail, tightloop, skill, v4, v4c); 0 hits is required. It also fails if a KEY/COST/METRICS/check/png file sits in
  the viewer folder. The viewer shows no checker results; the checker table is a separate file.
- cost_table.py: COST.json/.md by version (not by label): input, output, cache_read, cache_creation, in+out, cost-weighted,
  tool calls, turns, wall time, with v4c on the line after v4 plus v4c-v4 and v4c/v4. It is kept outside the viewer folder and
  the viewer never reads it.
- Self-test output: results/blind_r2_selftest.txt.
- Integrity and build isolation: [r2_INTEGRITY.md](r2_INTEGRITY.md), sha256 `5b5cb24336d6b1f026b92e8e767fc8e119c818472d9577d01e7b95e0cbe6cdc2` as of the probe-fix commit after b55917c. It covers key v2 (the reseal;
  v1 is VOID), the GitHub block in the build sandbox, the void-and-rerun rule, leak greps, the build order file and the full sha256 list.
