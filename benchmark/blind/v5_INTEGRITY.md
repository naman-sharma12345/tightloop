# tightloop v5 blind run: integrity record

Status: PREP ONLY. No v5 build, no v5 key and no v5 session exists at the commit that adds this file.
Design and criteria: benchmark/design/tightloop-v5/DESIGN.md (base eace66f, A1 0be26dc, A2 70b7958). Nothing here
changes a criterion, a prediction or a rule in that file.

## 1. App specs (committed before any v5 key exists)

Three new apps, none of round 1 or round 2 (todo, notes, units, kanban, expenses, bookmarks):

| app | file | bytes | sha256 |
|---|---|---|---|
| habit tracker | benchmark/blind/specs/v5/habits.md | 3321 | 116b0fbedf29400a93b7de739f8f9422eaa851608d4eef47a84b9e111d7629fb |
| recipe box | benchmark/blind/specs/v5/recipes.md | 3490 | 235b01522418f1a938e24e4dff868b45818f789d6e8f5781dc76c0c264fb68e1 |
| pomodoro timer | benchmark/blind/specs/v5/pomodoro.md | 3403 | 04b99b2a8efe35b7ece9b6e935662d95eec566138bb82fcecbfe9cd7cc0c3e05 |

Who wrote them: a separate helper worker that was told not to open, list or grep benchmark/arms/tightloop-v5/,
benchmark/arms/tightloop-v5b/, benchmark/design/ or .claude/skills/, and wrote from the round-2 spec shape only
(the helper's own statement: "no v5/v5b/design/.claude files opened"). One edit after the helper handed them over,
by the prep worker: a stray ",." in pomodoro.md ("requestAnimationFrame alone,.") became "alone." (helper's sha was
6b13d19b4d1bf210291eca2fca2f69e2bccf7b583d3dd6a60328e23a2a6f8a41; the table above is the committed file).
The specs are frozen from this commit on.

## 2. Sealed label key (made after the specs commit 1bbe58e, before any v5 build)

- Path: /home/user/tab/files/tl_blind/v5/KEY.json, mode 0600 (dir 0700). Never opened; read only by sha256sum.
- sha256: 43f5a85cc299abbf0f8a7000e1e5769d75a8eca30f1511ff0465cfa88fd29544 (results/blind_v5_key_sha256.txt).
- Made 2026-10-18 20:11:42.657Z by benchmark/blind/make_key_v5.py (sha256 f3f85456dd23f7b0da5e06317c00f6e4c1aa84e17c2d2527c7baf47b768fdb51),
  the round-2 key v4 method: seed = secrets.randbits(63) (os.urandom), random.Random(seed) shuffles the 5 arms independently
  per (app, run) for habits, recipes, pomodoro x runs 1-3 into labels A-E (9 pages). Its only arguments are the key path and
  the repo path; nothing secret in argv or env; its whole stdout was one 64-hex line; it refuses to overwrite.
- Run under watch by benchmark/blind/v5_run/gen_key_watch_v5.py (sha256 af944f118103bf8b62cbdeccef8f3f4a14860ba36f62011b7041a22ee9471cfc;
  a copy of r2_run/gen_key_watch_r2.py with only the generator path changed): the hardened build sandbox's process-list loop
  (every 50 ms for 5 s, same sandbox_r2 invocation as a build) took 100 samples, 2 inside the generator's 29.3 ms lifetime,
  and saw 0 host or generator processes; the positive control (old sandbox, no pid namespace, dummy make_key process) saw
  host processes in 85 of 85 samples. Log: results/blind_v5_key_generation_probe.json (no key content).
- Disclosure: one dry run of the same watch at 20:11:26Z wrote a throwaway key to a mktemp dir (sha256 bed01975...b7c5);
  it was never opened and was shredded right after. It is not this key and is never used.
- The seed and mapping exist only inside KEY.json. Root and the building worker never see the mapping before the picks.

## 3. Driver (benchmark/blind/v5_run/blind_driver_v5.py)

Mirrors r2_run/blind_driver_r2.py at 4a42a7c; no runner, grader or sandbox file is changed:
- Same hardened sandbox: r2_run/sandbox_r2.py prefix (own pid/net/ipc namespaces, empty home with read-only toolchains, private
  tmp, egress proxy to the model API only), the same pre-session probe (S.run_probe) with the v5 key, v5 checker, prep worktree and
  v5 output dir added to its path list and v5 key/checker forms added to its name and content patterns (set in the driver), the
  same transcript audit (a checker/key/repo hit VOIDS the build; the only rerun), and a fresh CLI config per build wiped after it.
- Skill text never in argv (root steer 20:10Z): argv_v5.py writes it to the build's own config dir and passes
  --append-system-prompt-file /tmp/.claude-cfg/append.txt; the model receives the same bytes. Test: argv_test_v5.py,
  results/blind_v5_argv_test.txt (5 arms, 0 skill lines in argv, file bytes identical, no-skill gets no flag). Disclosed limit:
  argv shows whether a skill is present (no-skill has no flag), never which one.
- Guard (exit 7, refusal logged): runs only from the snapshot (snap_v5.sh), whose history must contain the commit whose subject
  starts "tightloop v5 blind run: checker"; /home/user/tab/files/tl_blind/v5/START_OK must exist (ROOT creates it); the pass-3
  hold file must read "v5 builds by ..." (ROOT writes it with START_OK; the driver removes it after the last build or on a STOP);
  no other worker (claude -p, runner.py, cargo/rustc/go, another blind driver, an unpaused pass-3/4 loop). Refusal test:
  results/blind_v5_guard_test.txt.
- Plan (DESIGN 4.1/4.10): 9 blocks (run 1 of habits, recipes, pomodoro, then run 2, then run 3); each block a no-skill "reply OK"
  warm-up, then the 5 arms in row (block index mod 5) of the cyclic Latin square over [no-skill, ponytail, tightloop-v4,
  tightloop-v5, tightloop-v5b]; cap 600 s; one session at a time; no rerun except an isolation void.
- Pins: v5/v5b SKILL.md must equal the A2 shas (runner table); KEY.json sha256 must equal 43f5a85c... (read by sha256, and by
  json.load in the driver process only to place each build in its label folder; never printed or logged).
- Blinding of logs: logs, build_log_v5.tsv and results_v5.tsv name a build by its Latin-square position (app-runN-pK), never by
  label; the label appears only in the rows file (blind_rows_v5.jsonl, task dir, never shown to the judge) and the raw output
  folder name. Since the Latin square is public, position = arm: these logs are arm-labelled results, and the label<->arm map
  stays only in the key and the rows file.
- Per build, as it finishes (Naman m:98bbae98 pt 1): start, end, in+out, in+out+cache_read, cost-weighted, thinking
  (DESIGN 4.8 field, cross-checked), wall, checks, timed-out. Warm-ups go to warmups_v5.jsonl (counted in total cost only).
- After the last build: leakgrep_r2.py over the raw output tree is logged (raw, before strip/pack). The v5 blind pack and viewer
  (9 pages x 5 panels) are a later step.

| file | sha256 |
|---|---|
| benchmark/blind/v5_run/blind_driver_v5.py | d130cd1c1d1abdeba1a6576fea822b93ee06141885f76d6848c11ef540ddc927 |
| benchmark/blind/v5_run/argv_v5.py | 8b804c3f2f11aebb5912e20241548260d2e459b4577885e2167904f7ffdb6097 |
| benchmark/blind/v5_run/argv_test_v5.py | 4d774c9a9853d1be35ebb7da325e7d228851494ef5fa2b240d776ab64ee5df6d |
| benchmark/blind/v5_run/snap_v5.sh | cff4b589d27240aebd90bc00f28c577effe3199e6bf9ee89db764336d60803a1 |
