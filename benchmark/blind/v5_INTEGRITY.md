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
- Blinding (Naman m:d8220836 pt 3, the label->arm mapping lives only in the sealed key): logs, the rows file, build_log_v5.tsv and
  results_v5.tsv name a build by its Latin-square position (app-runN-pK), never by label. Each build is staged under
  OUT/.stage/<tag>; when all 5 builds of a page exist they are moved, in label order A-E, into OUT/<app>/run<N>/<label> with a
  fixed mtime, so no file, log or timestamp pairs a position with a label. The driver reads the key in its own process only to
  do that move and writes the mapping nowhere. (The Latin square is public, so position = arm: these logs are arm-labelled
  results, which is fine; the label is what stays sealed.)
- Per build, as it finishes (Naman m:98bbae98 pt 1): start, end, in+out, in+out+cache_read, cost-weighted, thinking
  (DESIGN 4.8 field, cross-checked), wall, checks, timed-out. Warm-ups go to warmups_v5.jsonl (counted in total cost only).
- After the last build: leakgrep_r2.py over the raw output tree is logged (raw, before strip/pack). The v5 blind pack and viewer
  (9 pages x 5 panels) are a later step.

| file | sha256 |
|---|---|
| benchmark/blind/v5_run/blind_driver_v5.py | f711fccad36b6cd9584004bc6a2bf6c949fb9c99b086bdd4bcf0118000d35591 |
| benchmark/blind/v5_run/argv_v5.py | 8b804c3f2f11aebb5912e20241548260d2e459b4577885e2167904f7ffdb6097 |
| benchmark/blind/v5_run/argv_test_v5.py | 4d774c9a9853d1be35ebb7da325e7d228851494ef5fa2b240d776ab64ee5df6d |
| benchmark/blind/v5_run/snap_v5.sh | cff4b589d27240aebd90bc00f28c577effe3199e6bf9ee89db764336d60803a1 |

## 4. Blind pack (benchmark/blind/v5_run/pack_v5.py)

A copy of r2_run/pack_r2.py with only the paths, the v5 key pin (sha256 only, never opened) and 9 pages x 5 labels changed: strip
version material, hint-line check, leak grep (leakgrep_r2.py) over the 45 blinded dirs, the zip listing+entries and the unzipped
tree, fixed zip timestamps, no .git. Viewer: the round-2 viewer unchanged (page ids habits-1 ... pomodoro-3; its grid has 4 columns,
so the 5th panel wraps to a second row). Dry run on 45 fake builds: 0 / 0 / 0 hits, exit 0 (results/blind_v5_pack_dryrun.txt).
pack_v5.py sha256 b0f05e6196aa37c0b36cdb56f70825d004e5ee0c3f13be2dbecd5c2432c9d575; pack_dryrun_v5.sh sha256 5e51d87d2ba6956abba6b3b4f497441fcc25b4b90afaeed0a66d4a13e94c9122.

## 5. Checker (benchmark/blind/checks/check_app_v5.py)

Written by worker 87fab574, blind to the v5 skill files: it never opened benchmark/arms/tightloop-v5*, benchmark/design/ or .claude/skills.
The specs (section 1) were written from the round-2 specs' shape only and reported at 20:07:17Z. Disclosure: from about 20:08Z the box's own
process listings showed running round-2 build command lines (spec + appended arm skill text) to every worker on the box, this one included;
that came after the specs were final. The checker and references are hidden-side and never reach a build.

Same CLI and output as check_app.py (helpers copied, check_app.py neither imported nor edited):
`check_app_v5.py <habits|recipes|pomodoro> <app_dir> <screenshot.png> <out.json> [zip] [port]`.
Page runs on Playwright's fake clock at 2026-03-18 12:00 UTC (timezone UTC); pomodoro's clock is paused and moves only by clock.run_for,
Math.random / crypto.randomUUID are seeded per page load, so timer checks, the button replay and the demo screenshot are deterministic.
Checks: ids, functional flow per spec, native confirm cancel/OK, every visible button acts (pomodoro: compared with a replay without the click),
375 px no horizontal scroll, reload persistence, a keyboard-typed value change, no external requests, no console/page errors, 1280x800 screenshot.

Full sha256:
- benchmark/blind/checks/check_app_v5.py 809d4d34c0344bc630990a92e6742d71ae08748565c351b9efc2a6925889f5ae
- benchmark/blind/checks/selftest_v5.sh 859212cfdb6b4632c9714f1b49498425809584c4e1e88ae093370d9f9df0874a
- results/blind_v5_selftest.txt 9a5e4eef710ff7b0da772d2935a0257eed9c643a34973cf85a6d9ff777ebc3ce
- benchmark/blind/checks/reference_v5/habits/index.html 342150c262c7c9c58f24361ddbd121e6f00c41975dcd8a21ffe7f12884f4fac2
- benchmark/blind/checks/reference_v5/habits_deadbtn/index.html 044ed7daac44d13456be5336b638e4d7f7c347624697d2a0f4e97644be36762c
- benchmark/blind/checks/reference_v5/habits_noconfirm/index.html 2ef0256c27beee0003a10527dd085f731c60d24328a5c76ab553b08df85fa50b
- benchmark/blind/checks/reference_v5/habits_overflow/index.html c781e99c04bce5eae0198054368218b1466644c50da211646e89a68f390c8487
- benchmark/blind/checks/reference_v5/habits_streakwrong/index.html d77b3dedc8a377fd09edb570e813a069c6659e1978e3c3cb290f17cb7277cb37
- benchmark/blind/checks/reference_v5/pomodoro/index.html e54143c512da7695fd8603c837ace9aea46ade2beee6488d724bd1414a108af9
- benchmark/blind/checks/reference_v5/pomodoro_deadbtn/index.html 484ac79d92093f76f8f883034e2f567973ae73d887c2e779cadf6c36766c546a
- benchmark/blind/checks/reference_v5/pomodoro_noconfirm/index.html 3c013b271e6c38f13d370f185c32b2dc29aab48874d667beab7f166a6d4bed78
- benchmark/blind/checks/reference_v5/pomodoro_nocount/index.html fa8bbb2375b9464abc54a1bac07165ecc57e48bb2c3df7ca8011c853af3b5c38
- benchmark/blind/checks/reference_v5/pomodoro_overflow/index.html 86720ed9f7e4f2580db6fa5664b09124b6e7cd76bd3fde537c79ae521f9ff87a
- benchmark/blind/checks/reference_v5/recipes/index.html f0a1b7a6e69315f4d91f084f763e39190eeb12ac2c2fd6ea9a7cafbbadc8e488
- benchmark/blind/checks/reference_v5/recipes_deadbtn/index.html fd614ab57e85b5eea98b75fa09d38761f0cd65305db5121a93fffe9e06d81db8
- benchmark/blind/checks/reference_v5/recipes_noconfirm/index.html f2a709e8a4b07925b343271b5ae8b50e38ae935b4aedaa486f1d95b7c2376dc6
- benchmark/blind/checks/reference_v5/recipes_noscale/index.html 65947490653c4b8bbe8df0a87107324efe1c4934add72d8dfd578fed49294a56
- benchmark/blind/checks/reference_v5/recipes_overflow/index.html e1a8138d515087c7785587fda12e4d03eb052760d5c0f866c1d3213977385256

Self-test (`bash benchmark/blind/checks/selftest_v5.sh`, 3 runs at a time, each nice -n 19 + timeout -k 5 240), run after the round-2 builds ended:

```
PASS  habits                 reference 20/20  failed=none
PASS  habits_deadbtn         control   19/20  failed=['every visible button changes page state']  dead_buttons=['Export']
PASS  habits_noconfirm       control   19/20  failed=['delete asks with native confirm(); cancel keeps, OK deletes']
PASS  habits_overflow        control   19/20  failed=['375 px wide: no horizontal page scroll (scrollWidth <= viewport)']  w375=[720, 375]
PASS  habits_streakwrong     control   19/20  failed=['streak = consecutive done days ending today (or yesterday): 2, then 3 with today']
PASS  pomodoro               reference 29/29  failed=none
PASS  pomodoro_deadbtn       control   28/29  failed=['every visible button changes page state']  dead_buttons=['Long break']
PASS  pomodoro_noconfirm     control   28/29  failed=['task delete asks with native confirm(); cancel keeps, OK deletes']
PASS  pomodoro_nocount       control   28/29  failed=["a finished focus adds 1 to the active task's .count only"]
PASS  pomodoro_overflow      control   28/29  failed=['375 px wide: no horizontal page scroll (scrollWidth <= viewport)']  w375=[760, 375]
PASS  recipes                reference 24/24  failed=none
PASS  recipes_deadbtn        control   23/24  failed=['every visible button changes page state']  dead_buttons=['Print']
PASS  recipes_noconfirm      control   23/24  failed=['delete asks with native confirm(); cancel keeps, OK deletes']
PASS  recipes_noscale        control   23/24  failed=["typing servings 6 then 2 rescales (300/0.75/3/2.25, 100/0.25/1/0.75; 'salt to taste' unchanged)"]
PASS  recipes_overflow       control   23/24  failed=['375 px wide: no horizontal page scroll (scrollWidth <= viewport)']  w375=[640, 375]
SELFTEST OK: 15 apps
```
Not fully deterministic / limits: habits' clock runs (not paused) from the fixed start, so only the date is fixed; a build whose DOM is not
replay-deterministic falls back to a before/after comparison in the pomodoro button check (recorded as replay_nondeterministic); under
heavy box load the slowest pomodoro control took 179 s of the 240 s budget.
