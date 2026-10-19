# PREREG v10 (written 2026-10-19T07:25:10Z, before any v10 run)
Owner GO: Naman "Do new skill work" (12:48 IST, 2026-10-19), after the holdout tie.
Base: v4c (benchmark/arms/tightloop-v4c), branch v6/instinct-rows head b6e8654979147fd5de85774d2b733f1a332486af.

## The one change
benchmark/arms/tightloop-v10 = tightloop-v4c byte for byte, except gate.sh no longer prints the diff
(the line `git diff HEAD | head -n 80` is removed; its header comment says so). SKILL.md, phases/fail.md
and phases/risky.md are byte-identical to v4c (SKILL.md sha256 6c2683f102dd, so the runner's arm_version
prefix reads the same as v4c; the arm name and gate.sh sha256 45087837bc28 tell them apart).
To run it, runner.py gets the same 2-line arm registration as v4c/v8 got (instinct/runner_2line.diff):
"tightloop-v10" added to ARMS and to the arm loop. Nothing else in the harness, grader or task files changes.

## Why (step-1 numbers, from the 75 stream-json transcripts in tl_instinct_out/*/logs)
- Tokens are about calls x 32k (call-1 context 29.8k: 23.5k shared prefix + ~6k per session).
- 5 of 12 v4c tuning runs (fd-01 r1 r2, tokio-02 r1 r2 r3) got GATE FAIL on the first gate. 510,197 of
  1,934,531 v4c tuning tokens (26%) were spent in calls between that first GATE FAIL and the final reply.
- In 5 of 5, the gate output the model saw held no reason line: gate.sh prints up to 80 diff lines after
  the prove/test lines, and SKILL.md step 2 pipes it to `tail -40`, so only diff lines and "GATE FAIL" showed.
  The model then re-ran the test by hand or read fail.md to learn why (tokio-02: "specification `tokio` is
  ambiguous" in all 3; fd-01: a bare test name passed as the command, then rustfmt).
- On a pass the diff echo is 680-1400 chars that repeat the edit the model just wrote (gin-04: ~1.07k chars,
  part of why v4c is 1.01x no-skill there).
With the diff gone, the whole gate output (prove lines, test tail, format, whitespace, debug, shortstat,
verdict) fits in `tail -40`, so a failing gate shows its reason in the same call.

## Prediction
- Passes: 12/12, same as v4c.
- fd-01 and tokio-02: median tokens and cw at least 10% below v4c (v4c fd-01 237290 / 49673.4;
  tokio-02 163047 / 36675.8), because a failed gate costs about 1 fix call instead of 2-5.
- gin-01 and gin-02 (no gate fails in v4c): about 0.5-1% below v4c (v4c gin-01 95145 / 27187.8;
  gin-02 128996 / 32199.8), from the dropped diff echo only. This may sit inside noise.
- No extra call to look at the diff.
Known confound: v4c rows ran in pass a, interleaved with no-skill and ponytail; v10 runs as its own pass
of 12 single-arm sessions (same shape as v8 pass b). With one arm, every session is position 1 of [v10].

## Keep rule (from the brief, fixed before running)
v10 is kept only if it passes at least as many runs as v4c (12/12) AND its median tokens and median cw are
lower than v4c on at least 3 of the 4 tuning tasks, with no task worse by separate ranges (v10 min > v4c max).
Otherwise "v10 not kept". Holdout (gin-04, ghcli-01b, n=3 each) runs only if kept. No tuning on holdout tasks.
A bad row is reported raw and never rerun.

## Run plan
4 tuning tasks (fd-01, gin-01, gin-02, tokio-02) x n=3 = 12 sessions, ORDER in instinct/ORDER_v10.json,
same seq.py per-session logic as pass b (go clean -cache before each session, sampler 6735e9c236a1 self-test,
KIMO_WINDOWS overlap with parser v7, one sidecar per row), rows in v10/rows.jsonl, same keys as instinct rows.
