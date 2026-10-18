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
