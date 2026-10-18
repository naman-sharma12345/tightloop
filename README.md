# tightloop

A skill for Claude Code and Codex that makes a coding agent push less code,
and only code it has proven: the smallest change, a test that fails without
it, a ship gate script, and a short skeptic read of the diff, in few tool
calls. The core is about 2 KB; heavier steps live in files the agent reads
only when it needs them.

## Install

Claude Code: copy the folder `.claude/skills/tightloop/` (SKILL.md,
gate.sh, phases/) into your project's `.claude/skills/`.

Codex: copy `AGENTS.md` to your project's root and the same
`.claude/skills/tightloop/` folder (AGENTS.md calls its gate.sh and
phases/ by that path).

The previous version (v3) is kept, unchanged, at
`benchmark/arms/tightloop-v3/SKILL.md`; `.claude/agents/` belongs to v3.

## Status

Benchmark state: **v4 numbers pending.** The first pass (v3, n=1 per arm,
3 counted tasks) is in `results/RESULTS.md` as raw rows, losses included.
This repository contains **no gain percentage of any kind**; none will
appear until it is computed from measured rows.

Method and formulas are pinned in `benchmark/MEASURE.md`; the holdout split,
pass/fail rules and run protocol are frozen in `benchmark/FREEZE.md`. Only
measured numbers are ever reported, losses included.
