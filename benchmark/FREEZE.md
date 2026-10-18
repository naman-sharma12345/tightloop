# Benchmark freeze

Committed before any tuning run and before any real benchmark run. Nothing in
this file changes after a real run has started; if the first-5 order or any
rule must change, it changes in a commit made before that run begins.

## Holdout split (frozen)

Rule (pinned in tasks/holdout-split.json, 2026-10-18): for every source
repository, the vendored task with the highest numeric suffix is holdout. For
from-scratch app builds, every even-numbered app is holdout. A repository that
yields only one task contributes it as holdout.

Frozen holdout task IDs (15):

axios-03, bat-02, black-02, clap-02, fd-03, gin-03, prettier-01, pydantic-03,
pytest-03, ruff-02, tokio-03, vue-03, zod-03, app-02, app-04

Holdout tasks are excluded from all skill tuning. score.py reports them in
separate tables, always; they are never mixed into headline numbers.

## Arms (frozen)

Three arms, identical task sets, identical agent CLI and model:

- **no-skill**: the agent session sees no skill files.
- **ponytail**: the agent session sees only the ponytail skill.
- **tightloop**: the agent session sees only the tightloop skill.

## Pass/fail rules (frozen)

- bugfix and feature tasks: `check_command` from the task JSON exits 0 with
  the hidden patch applied = pass; anything else = fail. A run whose grader
  never executed is recorded as invalid, not as a failure.
- app builds: the pinned test script shipped with the spec exits 0 = pass;
  anything else = fail.
- Every task starts UNPROVEN. A task becomes proven only after a real run
  has exercised its grader end to end.
- Reported numbers are raw per-run records. No averages before the raw rows
  exist; holdout rows are reported separately; losses are reported.

## Run protocol (frozen)

- Runs per task per arm is a parameter (`--runs N`). First pass: N=1, so the
  first five tasks produce 5 x 3 x 1 = 15 sessions. Increase to N=3 only if
  the first pass looks sane.
- First-5 task order: fd-01, fd-02, fd-03, gin-01, gin-02. (fd tasks need a
  Rust toolchain, gin tasks need Go.) Any reorder is edited into this file
  before the run that uses it.
- Every run records: agent CLI and version, model, OS, tool versions, and
  checkout SHAs, so numbers are never read as universal.
- Tokens (input, output, cache, total) are recorded exactly as the agent CLI
  reports them. Anything the CLI does not report is recorded as "unmeasured",
  never estimated.
- The controller launches, measures and grades. It never solves tasks.

## Validity rule (frozen)

The solver in every session is a fresh-context agent CLI session. The agent
that mined these tasks has seen every fix commit, hidden test and patch, and
must never be the solver: its results would measure memory, not skill.
