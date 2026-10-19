---
name: tightloop
description: Few calls, proven result. Any coding task.
---
One Bash per step, then a 3-line reply (change, check, not checked). No Skill tool, plans, subagents or refactors.

Bug fix: 1) `rg -n` key symbols, then `sed -n` the 20-40 lines needed and the nearest test. 2) Heredoc the root-cause fix and a test that fails without it (check empty, boundary, error inputs), then `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed files>`. GATE FAIL: fix what its last line names, rerun once.

App: one step. Heredoc each file once, then `node --check` the JS. SVG icons, not emoji; aria-labels; empty-state hints; inline errors.
