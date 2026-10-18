---
name: tightloop
description: Smallest correct change, proven by a test that fails without it, in few tool calls. Use on any coding task.
---
# tightloop

Ship the smallest diff that is correct and proven. Each tool call re-sends the whole context, so calls are the main cost: aim to finish in about 5. This skill is already loaded; do not open it with the Skill tool.

1. Look once. One Bash call: `rg -n` the task's key symbols, `sed -n` the ranges around the hits, and the nearest existing test. Put independent reads in one message. Never re-read a file you already saw or dump a large file.
2. Change. Fix the root cause where it lives, in the code's own style. Add one test beside the existing tests for that code that fails without your fix. Make all edits in one message. No refactors, renames, reformatting, new dependencies, debug output, or comments that restate code.
3. Prove and gate in one call:
   `bash .claude/skills/tightloop/gate.sh "<narrowest test command>" <source files you changed, not tests>`
   It runs the test with your source change removed (must FAIL), then with it (must PASS), checks format, whitespace and debug leftovers, and prints the diff. Output is capped.
   GATE FAIL: read `.claude/skills/tightloop/phases/fail.md`, fix, rerun. After two fails for the same reason, stop and report.
4. Skeptic, no tool call: read the printed diff as a reviewer who wants to reject it. Empty, boundary and error inputs? Public behaviour changed? A line you can delete? Fix only real defects; rerun the gate only if a code or test line changed.
5. Report in at most 4 lines: what changed and why, the GATE line, what you did not check.

Risky change (concurrency, security, data loss, public API, more than 3 files or 40 lines): read `.claude/skills/tightloop/phases/risky.md` before editing.

Always: cap output (`2>&1 | tail -40`); run the narrowest test, not the whole suite; no plan, notes or todo files; no subagents. No gate.sh (e.g. Codex without the folder): do its steps by hand.
