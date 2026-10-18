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

Measurement harness and benchmark results land here as the public-repo
benchmark produces them. Method and formulas are pinned in `MEASURE.md`
before any run; only measured numbers are ever reported.
