# tightloop

A skill for Claude Code and Codex that makes a coding agent work like a senior
maintainer: contract first, cheap recon, design before code, proof before fix,
thin slices, a separate skeptic pass, and a hard ship gate. It also cuts
wasted tokens from over-reading, noisy output and re-reading.

## Install

Claude Code:

- Copy `.claude/skills/tightloop/SKILL.md` into your project's `.claude/skills/tightloop/`.
- Copy `.claude/agents/scout.md` and `.claude/agents/skeptic.md` into your project's `.claude/agents/`.
- Add `.tightloop/` to your project's `.gitignore`.

Codex:

- Copy `AGENTS.md` to your project's root. Run the Scout and Skeptic roles as
  separate passes yourself (Skeptic reads only the diff).

## Status

Benchmark state: **pipeline verified, real numbers pending.** The harness,
grader and controller are proven end to end (pipeline check with a stub
solver; fixtures in `benchmark/tests/`). No real benchmark run has happened
yet, so this repository contains **no gain percentage of any kind** - none
will appear until it is computed from a real run.

The first run covers 5 tasks: fd-01, fd-02, fd-03, gin-01, gin-02.

Method and formulas are pinned in `benchmark/MEASURE.md`; the holdout split,
pass/fail rules and run protocol are frozen in `benchmark/FREEZE.md`. Only
measured numbers are ever reported, losses included.
