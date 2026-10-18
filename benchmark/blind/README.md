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
