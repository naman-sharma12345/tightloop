---
name: tightloop
description: Build or fix code with the fewest tool calls; for apps and UI, a designed result checked once in a real browser. Use on any coding task.
---
# tightloop v5

Every tool call re-sends the whole context (~30k tokens), and every output token costs 5x an input token. So: few calls, no wasted output, and quality decided before you type, not by rewriting. This skill is already loaded; never call the Skill tool.

## Building an app or UI (empty folder, a spec)
1. Design first, briefly, no tool call (the brief has already chosen most of it; decide, do not deliberate): from the spec's design brief fix the layout grid, CSS variables (palette, radius, shadow, an 8 px spacing scale), type sizes, and the states every control and list needs: hover, focus-visible, disabled, empty state with a hint of what to do, inline error text. Read the spec's exact ids, classes and file rules and keep them verbatim. No brief? Use a neutral light theme, one accent, system fonts.
2. Write everything in ONE Bash call: all files by heredoc (do not ls or probe first; the folder is empty), then in the same command `python3 .claude/skills/tightloop/look.py . 2>&1 | tail -40`. Write each file once, whole and final: style every native control (select, date, file, checkbox), cover empty, whitespace, bad and duplicate input, wrap localStorage reads in try/catch, and keep code compact (CSS variables and shared classes, no comments that restate code, no debug output).
3. Read `/tmp/look/used.png` once; it is the only screenshot you look at in the whole task. Judge it and the LOOK lines as a strict reviewer: errors, dead controls, OVERFLOW at 375 px, misalignment, cramped or uneven spacing, weak hierarchy, missing states, default-looking controls.
4. Fix only what is wrong, in ONE Bash call: targeted edits (python replace or sed), never a whole-file rewrite, then rerun look.py in the same command; its text lines are the recheck (do not read the screenshot again). At most 2 fix rounds.
5. Reply in at most 3 lines: files, the last LOOK line, anything not checked. No feature tour.

## Fixing a bug in existing code
1. One Bash: `rg -n` the key symbols, then `sed -n` only the 20-40 lines you need and the nearest test. No whole-file reads. Concurrency, security, data loss or public API: also `cat .claude/skills/tightloop/phases/risky.md` here.
2. One Bash: apply all edits (root-cause fix + one test that fails without it), then in the same command `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed source files> 2>&1 | tail -40`. Only on GATE FAIL: read `.claude/skills/tightloop/phases/fail.md`, fix, rerun once.
3. Reply in 3 lines: change, GATE line, not checked.

Always: cap output (`| tail -40`); no plan, notes or todo files; no subagents; no extra test or demo scripts (look.py and gate.sh are the checks); no refactors beyond the task. If look.py prints LOOK UNAVAILABLE, run `node --check` on the JS and say the browser check was not done.
