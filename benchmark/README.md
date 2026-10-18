# benchmark

One-command, reproducible benchmark for tightloop against two baselines:
the bare coding agent (no-skill) and ponytail.

## Layout

- `tasks/` - task definitions. One JSON file per task: repo, commit,
  instruction, hidden tests. Tasks are vendored only from MIT or
  Apache-2.0 licensed repositories; the source and license of every task
  are recorded inside its file. Repositories without a clear license are
  never vendored.
- `arms/` - the three arm configurations (no-skill, ponytail, tightloop).
- `run.sh` - runs every task under every arm, capturing token usage and
  test outcomes into `results/<run-id>/`.
- `score.py` - turns a results directory into the tables published in
  MEASURE.md and the README. Reports raw medians and ratios; never
  rounds up; keeps holdout tasks separate.
- `MEASURE.md` - the methodology. Read it before trusting any number.

## Quick start

```sh
bash benchmark/run.sh --tasks benchmark/tasks/tasks.json \
  --agent-cmd '<your coding agent invocation; it must leave usage.json in $DIR>'
python3 benchmark/score.py benchmark/results/$(ls benchmark/results | tail -1)
```

Files pushed through the GitHub web UI carry no executable bit, so the
runner and arm scripts are invoked with `bash` explicitly.

## Status

The task set is being assembled. `tasks/` is empty until the shortlisted
repositories (with their licenses) are reviewed. No results exist yet;
every number in the repository marked "pending" is waiting on this
harness.
