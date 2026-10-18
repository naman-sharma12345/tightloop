---
name: tightloop
description: Smallest proven fix in 3 tool calls. Use on any coding task.
---
# tightloop

Every tool call re-sends ~30k tokens, so finish in 3 calls. This skill is already loaded; never call the Skill tool.

1. One Bash: `rg -n` the key symbols, then `sed -n` only the 20-40 lines you need. Of tests, read only the lines of the failing or nearest test, by name. No whole-file reads, no cat. Concurrency, security, data loss or public API: also `cat .claude/skills/tightloop/phases/risky.md` here.
2. One Bash: apply all edits (root-cause fix + one test that fails without it) by heredoc/python, then in the same command `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed source files> 2>&1 | tail -40`. Check empty, boundary and error inputs before writing. Only on GATE FAIL: read .claude/skills/tightloop/phases/fail.md, fix, rerun once.
3. Reply in 3 lines: the diff stat, the GATE line, not checked. No other summary. No more tool calls.

No plan or notes files, subagents, refactors, or comments that restate code.
