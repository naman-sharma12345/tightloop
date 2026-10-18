# How tightloop is measured

Every number in the README comes from this harness. Nothing is estimated,
rounded up, or cherry-picked. Where tightloop loses, the loss is published.

## Arms

Each task is run three times, once per arm:

1. **no-skill** - the coding agent runs with no additional instructions.
2. **ponytail** - the agent runs with the ponytail prompt/skill installed
   (https://github.com/DietrichGebert/ponytail). Third-party baseline;
   see `arms/ponytail.md` for the exact version and license used.
3. **tightloop** - the agent runs with this repository's skill installed.

## Metrics

Per run we record:

- **tokens**: total tokens reported by the agent harness (input + output +
  cache reads), read from the agent's own usage log, not estimated.
- **hidden-test pass rate**: tests held out from the agent; run after the
  agent declares done.
- **regressions caught**: pre-existing tests that pass before the task and
  fail after.
- **reviewer-found defects**: a reviewer agent that has never seen the
  task's reference solution flags defects in the diff; count per task.
- **diff size**: lines added + deleted.

## Reporting rules

- Headline token number is the **median of per-task ratios**
  (arm tokens / no-skill tokens on the same task), reported raw.
- Headline quality number is the **ratio of defect scores**
  (no-skill defects / arm defects), reported raw.
- **Holdout tasks are reported separately** from tasks the skill was
  tuned on. They are never mixed into one average.
- No rounding up: 0.397 stays 0.397, it does not become "40%".
- The exact command, task list, model, and date are recorded with
  every published table in `results/`.

## Reproduce

```sh
benchmark/run.sh --arm all --tasks benchmark/tasks/tasks.json
python3 benchmark/score.py benchmark/results/<run-id>
```

Requires the coding agent CLI(s) you want to measure and network access
to clone the task repositories. See `benchmark/README.md`.

## Current status

Results: **pending** - no measured numbers yet. The README keeps its
placeholders until this harness produces them.
