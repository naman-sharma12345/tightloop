# tightloop v4c (classic)

The skill tightloop shipped as its best version before 1.0. It is kept here as an
opt-in alternative to the default (v11). These files are byte copies of
`benchmark/arms/tightloop-v4c/`, the exact arm measured in the results.

When to pick it: you want the agent to add a test that fails without its fix on
every change, including app builds. In the app benchmark v4c wrote test files in 6 of 9
builds; v11 wrote none. v4c also scored lower (better) defect medians on the habits
and invoice specs. It costs more: about 27% more cost-weighted tokens than v11 over
the 9 app builds (6.13M vs 4.82M).

## Install

Use it instead of the default, not beside it. The skill calls its gate and phase
files by the path `.claude/skills/tightloop/`, so copy this folder's contents there:

```sh
mkdir -p .claude/skills/tightloop
cp -r classic/v4c/SKILL.md classic/v4c/gate.sh classic/v4c/phases .claude/skills/tightloop/
chmod +x .claude/skills/tightloop/gate.sh
```

For an agent that reads `AGENTS.md` instead of skill folders, put the body of
`SKILL.md` (everything below the front matter) into your project's `AGENTS.md`,
and keep the folder above for its gate and phase files.
