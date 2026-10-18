# Blind round 2: integrity record (Naman m:ad61cc34, m:ed447bea, m:fe05342f, m:530473fd)

Written before any round-2 build. Nothing below names which version sits behind which label.

## KEY IN FORCE: v4 (reseal 3, 2026-10-18T19:58:37Z; Naman m:5eb8c3c4, root 19:35Z)
- **Key v4** `tl_blind/r2/KEY_v4.json` (box files area, outside the repo and every zip, mode 0600),
  sha256 `e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71` (results/blind_r2_key_v4_sha256.txt). Made 2026-10-18T19:55:39.490Z by the committed
  `benchmark/blind/make_key_r2.py` (sha256 `5ebf7d8b823c39b0f74f07397750c68cb82f63d928e5418628ab83d0cb4c85fd`, byte-identical to 9d31916;
  its `key_version` field therefore still reads 2: the file is identified by its sha256, not by that field). Fresh seed from
  `secrets.randbits(63)` (os.urandom); nothing derived from any earlier key, seed, note or transcript. Run OUTSIDE any sandbox as a
  host subprocess: argv = key path + repo path only, env = PATH + LANG only, the seed never in argv or env, never printed; the whole
  stdout was one 64-hex line; the key was not opened (sha256 only).
- **Probe during generation** (Naman m:5eb8c3c4 pt 2): while the generator ran, the hardened build sandbox (`r2_run/sandbox_r2.py`
  `prefix()`, the exact build invocation) ran the probe's process-list loop every 50 ms for 5 s: 100 samples, 3 of them inside the
  generator's 31.4 ms lifetime; at most 0 processes visible besides the probe itself, the sandbox init and the sandbox's egress
  forwarder; 0 samples with any host process or the generator visible. Positive control: the same loop in the old (b0130d7) sandbox,
  with a dummy host process, saw host processes in 89 of 89 samples (up to 157). Log: `results/blind_r2_key_v4_generation_probe.json`.
  Ran by `r2_run/gen_key_watch_r2.py` sha256 `f8f20d54c974ddef2f7675979f4162a0f816157b6cbd4f64e64741667967d22b` with `sandbox_r2.py` sha256
  `9a6dcca5e845bd09609de9cc07858243260ede488408e9703c96ace664269d21` and `egress_r2.py` sha256 `fcac2570994138cad0e1cd6fec766d5d945f665172a8d8dce5923b21c0f6376b`
  (committed in the CHECKS commit that follows; if a later fix changes them, that commit lists both versions).
- **Seed grep v4** (argv-free: the value only ever travels as a 0600 pattern FILE to `grep -F -f`, read from KEY_v4.json by a program,
  never displayed, deleted after; run before this commit): repo all-history patches (`git log --all -p | grep -cF -f`) 0 lines,
  commit messages 0, bench clone all-history patches 0; `grep -rlF -f` over the commit worktree 0, every task dir under the box's
  tasks area 0, all agent session transcripts 0, session artifacts 0, state 0, memory 0, raw build area 0, r2 snapshot 0, bench clone 0,
  egress dir 0; the box's files area 1 file = KEY_v4.json itself. It is re-run after this commit and after the CHECKS commit.
- **Key v3 is VOID-UNUSED.** `tl_blind/r2/KEY_v3.json`, sha256 `876bf126d232c1e1027e57ef62356dc5a46450ebd281bdaf6afed68c2bee364a`, made
  2026-10-18T19:40Z by make_key_r2.py, BEFORE Naman's rule (m:5eb8c3c4 pt 2, 19:40Z) to run the hardened process-list probe while the
  generator runs, so it has no such proof. Never used, left unmodified on the box; sha only. Its sha was never committed before.
  Disclosure: at 19:59Z the pre-commit secrets check of this commit read the seed field of KEY_v2.json and KEY_v3.json inside its own
  process (to count matches in the staged diff: 0 each); nothing was displayed, logged or written, and the check no longer reads them.
- **Key v2 is BURNED** (not just void; Naman m:5eb8c3c4 pt 1). Exposure window: start 2026-10-18T19:06Z, when KEY_v2.json was written
  to the box's files area (mode 0600, owner uid 1000: readable by any uid-1000 process on the host); from about 19:15Z its seed also
  sat for a few seconds in the argv of a `git log -S<value>` seed-grep process, i.e. in the host process list. End: this commit,
  2026-10-18T19:58:37Z, when v4 replaces it. Who could see it: any process of uid 1000 on the box, including the old probe/build sandbox
  (b0130d7 shape: no pid namespace, host process list visible - 142 processes at 19:34Z, 157 at 19:55Z; the key file itself was under a
  tmpfs there). No build ever ran in that sandbox (0 builds ever); it ran only probes, self-tests and the network test. Kept on the box, never opened, never deleted; sha `fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c` only.
- **Old sandbox exposure: ~/.netrc and the agent CLI's 79 earlier session transcripts** (Naman m:5eb8c3c4 pt 3). The b0130d7-shape
  sandbox left /home/user visible apart from /home/user/tab and ~/.prime, and bound the CLI's shared config dir (79 earlier session
  transcripts) read-write, so any process in it could read ~/.netrc and those transcripts. netrc: only machine entry is surge.surge.sh (root checked names only, token not read); not the GitHub token.
  Neither file was opened for this record. One disclosure: at 19:52-19:54Z the first run of the new sandbox self-test ran the FULL
  probe in the old sandbox as a positive control; its content regex check reads bytes of files on bound mounts, which there included
  the shared config dir. Nothing was printed (killed by pid before any output); the old-sandbox control is now process-list only.
  The hardened sandbox removes both: /home/user is an empty tmpfs with only the toolchains read-only, and each build gets a fresh
  empty CLI config dir that is wiped after the build.

## CHECKS before build 1 (Naman m:f4cffa5e, m:b3c5c470, m:5eb8c3c4; this commit is "blind round 2 CHECKS")
The sections "Build isolation" and "Network" further down describe the b0130d7 sandbox. It is SUPERSEDED by the hardened sandbox
below; 0 builds ever ran in the old one.
- **Hardened build sandbox** (`r2_run/sandbox_r2.py` `prefix()`, used by the driver for every build and by the probe; only the
  command after the prefix differs): root filesystem read-only; own pid, ipc, uts and cgroup namespaces and a fresh /proc; NO network
  namespace access (`--unshare-net`, loopback only); `/home/user` an EMPTY tmpfs with only the 4 toolchains bound back read-only
  (tl-npm, go-dist, .cargo, .rustup); `/tmp`, `/var/tmp`, `/run`, `/dev/shm` private tmpfs; a minimal private /dev; `--new-session`,
  `--die-with-parent`; no_new_privs (sudo fails). The keys, every repo/checker copy, task logs, agent session transcripts, ~/.netrc
  and the CLI's old shared config dir are not in it. Environment cut to an allowlist (`egress_r2.ALLOW_ENV`).
- **Writable paths per build** (exactly two host paths, both fresh per build, never shared by two builds): the build's workspace
  (`mkdtemp /tmp/tlb-*`, copied to the raw build area by label after the build, then deleted) and the CLI config dir (`mkdtemp
  /tmp/tlb-cfg-*`, bound at `/tmp/.claude-cfg` = CLAUDE_CONFIG_DIR, wiped right after the build). Everything else writable inside is a
  private tmpfs that dies with the sandbox (`/home/user`, `/tmp`, `/var/tmp`, `/run`, `/dev`, `/dev/shm`). One mount, tracefs at
  /sys/kernel/debug/tracing, is mounted rw by the host but not writable by the build's user (probe: no write permission).
- **Outbound allowed** from a build: only an HTTPS CONNECT to the model API host on port 443, through the egress proxy
  (`r2_run/egress_r2.py`, which reads the host from its environment and logs it as <model-api>); the sandbox has no network of its own
  (no DNS, no direct sockets); every other host, incl. GitHub, npm, PyPI, crates.io, the Go proxy and CDNs, gets 403.
- **Registry check** (`r2_run/registry_check_r2.py`, results/blind_r2_registry_check.txt): from inside the sandbox, npm view / npm install
  github:… / pip download / pip install git+… / cargo search / go mod download / git clone, for both "tightloop" and "ponytail":
  14 of 14 BLOCKED.
- **The probe, ONE command** (exit 0 only if every check passes): `python3 benchmark/blind/r2_run/sandbox_r2.py --probe`
  (from the snapshot: `python3 /home/user/tab/work/tl_blind_r2/benchmark/blind/r2_run/sandbox_r2.py --probe`). It builds a fresh
  workspace + fresh config dir + its own egress proxy + a host sentinel process exactly as a build gets them, runs `prefix()` and FAILS
  unless: (1) processes: own pid namespace, no host process and no sentinel visible (all visible besides the probe: the sandbox init
  and the egress forwarder); (2) env dump is names only and every name is allowlisted (its own and pid 1's); (3) network: 14 blocked
  hosts incl. github.com fail, a direct connection fails, and a minimal model call to the model API returns HTTP 200; (4) writable:
  the only writable host-backed mounts are the workspace and the config dir; (5) scan: every mount root plus /tmp and /home/user
  walked, names matched against `^(KEY(_v\d+)?\.json|mapping(_r\d+)?\.json|check_app\.py|blind_rows.*\.jsonl|COST|METRICS\.json|\.netrc)$` and, on every mount except / and the read-only toolchains, file bytes matched
  against a key/mapping/checker signature; (6) unix sockets: only the egress socket; (7) home: exactly the 4 read-only toolchains;
  (8) the old probe paths (keys v1-v4, checker copies, tasks, raw builds, ~/.netrc, ~/.prime, the old CLI config) absent;
  (9) sudo fails. Run at 20:03Z: ok=true; 179232 files walked; 0 name and 0 content hits; 0 host processes visible;
  model API HTTP 200; results/blind_r2_probe_hardened.json. The driver runs the same probe before every build.
- **Self-tests** (`r2_run/sandbox_selftest_r2.py`, results/blind_r2_sandbox_selftest.json), all as expected: clean probe passes;
  planted files under 3 names (KEY_v2.json, mapping_r2.json, notes.txt with key-shaped content) in 2 mount paths (workspace, CLI
  config dir) -> probe FAILS, all 6 caught (4 by name, 2 by content); an extra env name -> FAILS; an extra dir under /home/user ->
  FAILS; an extra writable host path -> FAILS; the old b0130d7 sandbox with a host sentinel -> process check FAILS (157 host
  processes visible; positive control); two fake builds: B (fresh workspace + config) cannot see A's workspace, A's config dir, the
  scratch output copy of A or the raw build area, sees an empty config dir of its own, and A's config dir is gone after A.
- **CLI smoke** (`r2_run/cli_smoke_r2.py`, results/blind_r2_cli_smoke.json; not a build, no tools): the agent CLI starts with an
  empty config in the hardened sandbox, gets "OK" from the model, wrote 4 files only into its own config dir, which was then wiped.
- **Edit audit** (`benchmark/blind/r2_EDIT_AUDIT.md`): the 12:37 IST (19:07Z) edits and every later change to blind_driver_r2.py and
  pack_r2.py, diffed line by line against the saved originals and marked WIRING or BEHAVIOUR. BEHAVIOUR hunks (for root to re-check):
  - blind_driver_r2.py S1-1 [12:37] (b55917c lines 33-33): in-sandbox probe also tests the KEY_v2 path
  - blind_driver_r2.py S1-2 [12:37] (b55917c lines 42-42): probe's find matches KEY*.json, not only KEY.json
  - blind_driver_r2.py S1-3 (b55917c lines 75-85): build ORDER from the committed random order file; labels resolved from key v2 inside the driver; usage-source text
  - blind_driver_r2.py S2-1 (b0130d7 lines 42-42): probe runs find over each mount root (old find / -xdev skipped tmpfs mounts and missed a planted KEY_v2.json)
  - blind_driver_r2.py S3-3 (this commit lines 11-58): own-hold rule, other_workers(), guard() (snapshot has CHECKS commit + START_OK + no other worker; REFUSED + exit 7), --guard-test, sandbox import
  - blind_driver_r2.py S3-4 (this commit lines 62-63): environment cut to an allowlist (sandbox_r2.clean_env); own egress proxy started
  - blind_driver_r2.py S3-5 (this commit lines 65-65): old bwrap_prefix removed; CUR carries the per-build config dir
  - blind_driver_r2.py S3-6 (this commit lines 67-67): every build runs under the hardened sandbox_r2.prefix
  - blind_driver_r2.py S3-7 (this commit lines 70-72): old probe paths replaced by isolation_check(wt, cfg)
  - blind_driver_r2.py S3-8 (this commit lines 75-82): isolation check = workspace grep + full hardened probe (sentinel host process) in the exact build invocation; transcript AUDIT also matches KEY_vN.json and mapping_rN
  - blind_driver_r2.py S3-9 (this commit lines 88-96): release_hold() + build_log.tsv writer
  - blind_driver_r2.py S3-10 (this commit lines 99-100): busy(): a foreign hold or any other worker (agent session, runner, cargo/rustc/go, other driver) blocks the next build; our own hold does not
  - blind_driver_r2.py S3-14 (this commit lines 156-156): fresh CLI config dir per build
  - blind_driver_r2.py S3-15 (this commit lines 161-162): probe gets the build config dir
  - blind_driver_r2.py S3-16 (this commit lines 164-166): ISOLATION STOP names the failed checks; wipes cfg; releases hold (run-ending STOP)
  - blind_driver_r2.py S3-17 (this commit lines 170-171): config dir wiped right after each build
  - blind_driver_r2.py S3-18 (this commit lines 176-176): INFRA STOP logs build_log row and releases hold
  - blind_driver_r2.py S3-20 (this commit lines 189-189): VOID STOP releases hold
  - blind_driver_r2.py S3-23 (this commit lines 216-216): hold removed after build 12
  - pack_r2.py S1-3 [12:37] (b55917c lines 10-13): key path/sha v2; leak-grep module imported; pack no longer reads the key
  - pack_r2.py S1-4 [12:37] (b55917c lines 15-16): more files stripped from builds before packing (md, logs, look.py output, screenshots, editor dirs)
  - pack_r2.py S1-5 (b55917c lines 24-24): raw build read by label (driver stored it so); no key lookup
  - pack_r2.py S1-7 [12:37] (b55917c lines 48-71): leak grep over build dirs, zip listing+entries, unzipped tree, mtimes, .git; any hit stops the pack (exit 3)
  - new files (all BEHAVIOUR): r2_run/sandbox_r2.py, egress_r2.py, sandbox_selftest_r2.py, gen_key_watch_r2.py, registry_check_r2.py,
    guard_refusal_test_r2.sh, snap_r2.sh, cli_smoke_r2.py.
- **Driver guard** (`blind_driver_r2.py` guard()): the driver refuses to start, logs `REFUSED: <reasons>` and exits 7, unless (a) it runs
  from the snapshot and the snapshot's commit (`.snap_commit`, written by `snap_r2.sh`) has this "blind round 2 CHECKS" commit in its
  ancestry, (b) `/home/user/tab/files/tl_blind/r2/START_OK` exists (created by root alone, after he re-checks the BEHAVIOUR hunks and
  re-runs the probe; never by a worker), and (c) no other worker runs: no agent CLI session, no runner.py, no cargo/rustc/go, no other
  round-2 driver, and no pass-3/4 driver unless our hold pauses it. The same "other worker" check gates every build.
  Refusal test (`r2_run/guard_refusal_test_r2.sh`, results/blind_r2_guard_refusal_test.txt): a real launch, an empty snapshot, and a
  fake `cargo` process each REFUSED with exit 7; START_OK was never created.
- **Hold file**: /home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold (created by root 19:33:47Z, "r2 builds by …") pauses pass 3.
  The driver treats a hold starting "r2 builds by" as its own (does not wait on it) and removes it after build 12 or on a run-ending
  STOP (isolation, infra, void), logging the time.
- **Restart record**: the driver was relaunched by worker 14334bcb at 2026-10-18T19:27:29Z (pid 3131507, snapshot b0130d7, key v2)
  before Naman's 12:53 IST checks were committed; it only waited (on a running pass-3 session); root killed it at 19:28:20Z. 0 builds.
  It has not run since.
- **Build log**: one row per build in `build_log.tsv` (header `build_label	start_utc	end_utc	df_mib_after`, results/blind_r2_build_log.tsv),
  labels only; void attempts and an infra stop get their own rows.
- **Seed grep v4 after the reseal commit 993a431** (argv-free, as above): repo history 0, commit messages 0, bench clone history 0, every
  area 0 files except the box's files area = 1 (KEY_v4.json). Re-run after this commit.
- **Order file**: the committed `results/blind_r2_order.json` (12 labels, drawn independently with `secrets`, labels only, committed in
  b55917c) is kept unchanged. It names labels, not versions, so it does not depend on which key is in force.
- **Old egress proxy**: an uncommitted proxy left by 14334bcb (pid 3149448, allowed host in its argv) was killed at 19:57Z; the
  committed sandbox starts its own proxy per process.

## Run record (12 builds) and observer exposure
- 12 builds ran back to back from the CHECKS snapshot (4a42a7c) under key v4: 2026-10-18T20:08:23Z (first start) to 20:58:26Z (last
  row). 0 isolation stops, 0 infra stops, 0 voided attempts, no reruns. Every build passed the full hardened probe right before its
  launch, and every transcript audit had 0 hits. Per-build start, end and free disk: results/blind_r2_build_log.tsv (labels only).
  The driver removed the hold file at 20:58:26Z ("after build 12"). START_OK was created by root at 20:07Z, after his own probe run.
- Observer exposure (root 20:10Z, option A): the box's process census on host lanes shows each build CLI's argv, which carries the
  skill text, so the label->version pairs are visible to worker 73adc3ad and root transcripts. The build agents can't see it (own pid
  ns, verified by probe). The blind judge is a separate worker spawned after build 12, with no build overlapping its turns, that never
  reads those transcripts. The pairs are quoted nowhere: no milestone, file or commit.
- From 20:15Z (Naman m:d8220836) root and worker stopped reading process listings/launch commands for the rest of r2.
  (The box's census facts still arrived unrequested in this worker's tool results until build 12 ended; they were not used and are not
  quoted. After 20:15Z the worker tracked the run only from build_log.tsv, BUILD_RESULTS.tsv, the driver's own log and the driver's
  own pid.)
- As with every earlier version of the round-2 driver, its own log (workspace file list per build) and its rows file (version field)
  record which version built each label. Both stay in the worker task area, outside the repo and every zip, until the reveal.
- Viewer: files area `tl_blind/r2/viewer.zip`, sha256 `6d033cc74dad2f3b4610663ddbc0add214ad472faa18399a6307bb56b9b96764`, 40 entries,
  fixed timestamps, no .git. Leak grep: 0 hits over the 12 build dirs, the zip listing + entries, and the unzipped tree.
  verify_viewer.py: all_ok (12 builds, each on its own origin, 0 viewer errors, 0 name hits, 0 key/mapping/cost entries).

## Key history before v4 (as written at b55917c: v1 VOID; v2 is now BURNED, see above)
- **Key v1 is VOID.** `tl_blind/r2/KEY.json`, sha256 `2fa05c9609411681d61c4eede6c0b29a5a451733a4b14a051eb5a48a47ba0433`
  (committed at bc4b673), stays on the box untouched and is never used. VOID since 2026-10-18T19:06Z. Reason: seed printed once in an agent session
  transcript at 2026-10-18T18:26:32Z (shuffle code `print(ks, seed, len(b))`); 0 builds existed; resealed. Found by the
  pre-build seed grep (Naman m:fe05342f d): the value sat in exactly 1 record of 1 session transcript and nowhere else
  (repo history, commit messages, worktree, every task dir and log under the box's tasks area, files, state, memory: 0 hits).
  The mapping itself was never printed. The v1 shuffle code, verbatim as run (no seed value in it):
  `benchmark/blind/r2_key_v1_shuffle_as_run.py`, sha256 `c6a792f54059f39e0d857aa7d3fb213832c9da1733e76f84e8520bfcf2f5944e`.
- **Key v2**: `tl_blind/r2/KEY_v2.json` on the box's files area, outside the repo and outside every zip, mode 0600.
  sha256 `fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c`.
  Made by `benchmark/blind/make_key_r2.py`, sha256 `5ebf7d8b823c39b0f74f07397750c68cb82f63d928e5418628ab83d0cb4c85fd` (this exact file, committed in 9d31916).
  It draws the seed with `secrets.randbits(63)`, shuffles the 4 versions (no-skill, ponytail, tightloop-v4, tightloop-v4c)
  independently per app in the fixed app order bookmarks, expenses, kanban with `random.Random(seed)`, writes the key
  (refusing to overwrite) and prints ONLY the key's sha256. It was run as a subprocess with stdout captured to a file, which
  held exactly one 64-hex line. The key was not opened to write this record (sha256sum only).
- **Seed exists only inside the sealed key.** Seed grep for v2 (pattern taken from KEY_v2.json by a program into a 0600
  pattern file, never displayed, deleted after): `git log --all -S` = 0 commits, commit messages = 0, and `grep -rlF` over
  the commit worktree, every task dir under the box's tasks area (all round-2 driver logs, RUN_LOG copies, NOTES, transcripts),
  all agent session transcripts, session artifacts, state, memory, the raw build area, the r2 snapshot and the bench clone =
  0 files; the box's files area = 1 file, KEY_v2.json itself. results/ is inside the worktree (0).
- The key is read only by the build driver (`r2_run/blind_driver_r2.py`), programmatically, to turn each label of the committed
  build order into the version to build. It prints no mapping: its log and file names use the label only. `pack_r2.py` only
  checks the key's sha256 and never opens it.
- The reseal (key v2 sha256 + make_key_r2.py) was pushed in its own commit (9d31916) before this pre-build commit.
- Labels A-D per app; the mapping is never in the viewer zip. verify_viewer.py lists the zip and fails on any entry named
  KEY / mapping / COST / METRIC / check / .png, and the leak grep below runs on every zip entry.

## Full sha256 at this commit (check_app.py unchanged since ba3cef6, specs unchanged since 3e86a80)
- benchmark/blind/checks/check_app.py: `ad6b508757dc25957e3e04d2db68a8e876c59d729e46ce2f9a5596908ee8ff72`
- benchmark/blind/specs/r2/bookmarks.md: `b737fe37e9d6bb6f341b324ff51b02da50e04a0bac72e7336f3d761dcd15e6c1`
- benchmark/blind/specs/r2/expenses.md: `cb501d9933459ec4c683eb3733ed89fed66b6cdc3b4e78be4b9e7c0080e7ccab`
- benchmark/blind/specs/r2/kanban.md: `c768cbc03511cb8a223b9b7ee7ea5e478b6c0e9fc4681c2223a0f3efc06a5b10`
- benchmark/blind/make_key_r2.py (made key v2): `5ebf7d8b823c39b0f74f07397750c68cb82f63d928e5418628ab83d0cb4c85fd`
- benchmark/blind/r2_key_v1_shuffle_as_run.py (made the VOID key v1): `c6a792f54059f39e0d857aa7d3fb213832c9da1733e76f84e8520bfcf2f5944e`
- benchmark/blind/make_order_r2.py: `4d3329b7b40d87d1e3a07e47a55f999e54d7b9c5b5a491c5cdd73ef5f9219380`; results/blind_r2_order.json: `96938a69b4dce6a90fee96231af97a2b2e369a645bcb6b7ffb896b4a1a8f1ff5`
- benchmark/blind/leakgrep_r2.py: `cad995de7d5a06e61383e6a30566c3a87ff2299e5d633224532784210160718b`
- benchmark/blind/r2_run/blind_driver_r2.py: `8da0565b6275b0acffcc5c4b57ed5e7b25fe101da7670cc108a862678424fff0` (probe fix after b55917c)
- benchmark/blind/r2_run/pack_r2.py: `2a85c53dbab41612591c86a7100edb0caef7f9c65092ef2732e6f24d85a72ce8`
- benchmark/blind/cost_table.py: `c18e43675faa63e048c9c9c25c4f8fe9835bf3864534dd39b16c52100d3e4641`

## Build-facing spec
The r2 specs have no scoring or check section. They hold a feature paragraph, design instructions and the file rules. The
"Element ids the checker uses" sentence is build-facing: a build has to use those ids to be testable, and the text is
identical for every version. So the prompt each session gets is the committed spec file byte for byte. The stripped diff is
empty, and the prompt's sha256 equals the spec sha256 above. The driver records it per build as `prompt_sha`.

## Build isolation
Each build session runs in a fresh `/tmp/tlb-*` workspace (git init). It holds only the version's skill folder under
`.claude/skills/` (nothing for no-skill), and the spec text arrives as the prompt. The session runs inside a bubblewrap mount
namespace in which these are empty tmpfs:
- `/home/user/tab`: the key, every repo checkout including the checker and the references, the builds of other versions,
  task logs and files;
- `/tmp`: other worktrees and the commit area;
- `/home/user/.prime`;
- `/dev/shm`.
Only the session's own workspace and the agent CLI's config directory are mounted back.

Before every session the driver logs three things, and it stops the run if any of them fails:
1. the workspace file list;
2. a grep of the workspace for `check_app|KEY.json|blind/checks|checks/reference|blind_r2|COST` (must be empty);
3. a probe from inside the same sandbox: `test -e` on both keys and on every checker copy; `find -xdev` for `check_app.py`,
   `KEY*.json` and `blind_rows*` over each mount root separately (/, the workspace, /tmp, /home/user/tab, the CLI config dir,
   ~/.prime, /dev/shm), because `-xdev` from / alone skips the tmpfs mounts; and a curl to raw.githubusercontent.com. All must
   come back empty. Fixed after the pre-build commit b55917c: the negative control (a file named KEY_v2.json planted in the
   workspace) was NOT caught by the old `find / -xdev`. The new probe catches it (results/blind_r2_selftest.txt,
   r2_run/isolation_probe_test.py).

Dry run on this box: the workspace lists only `.claude/skills/tightloop/SKILL.md`; grep 0; probe 0. A planted file containing
"check_app.py" is caught by the grep.

The checker runs only after the session has ended, outside the sandbox, on a copy of the build.

## Network: GitHub blocked inside the build sandbox (Naman m:ed447bea b)
Every build session's sandbox mounts `r2_run/sandbox_hosts` (sha256 `fcea7762d46574ccd6dd1efa1c1af9717810b6918a36104cf3f7cf64648570cf`) read-only over
`/etc/hosts`. It points github.com, www., api., gist., uploads., codeload.github.com and raw., objects., media., avatars.,
gist.githubusercontent.com and github.githubassets.com to 0.0.0.0 / ::. The model API host is not touched. Proof, run with the
driver's exact sandbox prefix (`r2_run/nettest_r2.sh`, output `r2_run/nettest_r2.out`, 2026-10-18 ~19:12Z):
```
INSIDE  curl github.com -> rc=7 curl: (7) Failed to connect to github.com port 443 after 0 ms: Couldn't connect to server
INSIDE  curl raw.githubusercontent.com -> rc=7 curl: (7) Failed to connect to raw.githubusercontent.com port 443 after 0 ms: Couldn't con
INSIDE  curl api.github.com -> rc=7 curl: (7) Failed to connect to api.github.com port 443 after 0 ms: Couldn't connect to ser
INSIDE  curl codeload.github.com -> rc=7 curl: (7) Failed to connect to codeload.github.com port 443 after 0 ms: Couldn't connect t
INSIDE  git ls-remote github.com -> fatal: unable to access 'https://github.com/naman-sharma12345/tightloop/': Failed to conne
INSIDE  getent hosts github.com -> ::              github.com
OUTSIDE curl github.com -> 200 (control: host network itself works)
INSIDE  minimal model call (curl, same sandbox) -> HTTP 200 reply: OK
```
**Hard rule:** the hosts block stops name lookups but not a raw IP address. So after every session the driver greps the whole
transcript for `check_app`, `KEY.json`, `blind/checks`, `checks/reference`, `blind_rows`, `tl_blind`, `raw.githubusercontent` and
`github.com/naman-sharma12345`. **Any hit VOIDS that build, and it is rerun.** The voided attempt's folder and transcript are kept,
renamed `.VOID`, and listed in the row's `voided_attempts` with the hits. After 3 voids in a row the driver stops.
(`r2_run/blind_driver_r2.py`, the `audit()` / `VOID` block.)

## Reruns (Naman m:fe05342f)
The only rerun allowed is a build voided by an isolation hit (the transcript rule above, or a failed pre-session isolation
probe). A bad, failed or low-scoring scored build is never rerun or replaced. A session with no usable result stops the driver
(no row, no retry), and that is reported. A voided run stays in the log, marked void, with the reason.

## Build order and fairness (Naman m:530473fd pt 4)
- The 12 builds run in the order in `results/blind_r2_order.json`, labels only, drawn with `secrets.SystemRandom` by
  `make_order_r2.py` (sha256 `4d3329b7b40d87d1e3a07e47a55f999e54d7b9c5b5a491c5cdd73ef5f9219380`). The order file sha256 is
  `96938a69b4dce6a90fee96231af97a2b2e369a645bcb6b7ffb896b4a1a8f1ff5`. It was committed here, before build 1.
- All 12 builds use the same model, the same box, one session at a time, and the committed spec byte for byte as the prompt.
- Tokens and time come from the harness record, never from the agent's own report: the claude CLI's final stream-json
  `result` event (`usage`, `num_turns`) parsed by runner.launch, tool calls counted from the same log, and wall time from
  runner.launch's clock. Each row and the COST file carry this as `usage_source` / `source`.
- Before every build: the hold file must be gone, `df` must show 3000 MiB or more on /home/user, and no pass-3 session may be running.
- Residual: raw build folders (which hold each version's skill folder), the rows file and the COST file on the box carry
  version names. They are never committed, zipped or shown to the judge before the reveal.

## Blind leaks (Naman m:ed447bea c, m:530473fd pt 3)
`pack_r2.py` (sha256 `2a85c53dbab41612591c86a7100edb0caef7f9c65092ef2732e6f24d85a72ce8`) copies each build by label and drops version material:
.claude/ and other agent folders, .git, agent notes (NOTES/PLAN/TODO/AGENTS/CLAUDE/CONTRACT/SCRATCH/README/CHANGELOG, any .md),
.log and console* files, look.py and its output (look*.json/txt/png), screenshots, test files and skill/gate files. Every drop
is logged. Any remaining hint line stops the pack (exit 3). The viewer then gives each build a neutral path
(`builds/<app>-<label>-<nonce>`) and sets one fixed timestamp on every zip entry. `leakgrep_r2.py`
(sha256 `cad995de7d5a06e61383e6a30566c3a87ff2299e5d633224532784210160718b`) then runs three times, and each must be 0 hits:
1. every blinded build dir;
2. the zip listing plus every zip entry's bytes;
3. the unzipped tree.
It matches file names and bytes for: tightloop, ponytail, no-skill/noskill, skill/SKILL, .claude/claude, anthropic, gate.sh,
GATE PASS/FAIL, look.py, look_report, "controls clicked", and the version tags v3, v4, v4a, v4b, v4c, v4d, v5, v5b (v3-v6 plus
one letter). It also flags agent-note and log file kinds and any image no file of the build refers to. The pack also fails
on any zip entry with a non-fixed timestamp or any .git entry. Self-test (results/blind_r2_selftest.txt):
- clean references: 0 / 0 / 0;
- planted .claude/, look output, console.log, NOTES.md, screenshot.png, an unreferenced icon and a "v4c" comment are all caught
  (21 hits), and the pack strips the strippable ones and logs them;
- a "tightloop" comment inside app code stops the pack (exit 3);
- a "ponytail" entry planted in a zip is caught.

## Viewer
One zip, one server. Each label runs on its own port (its own origin, cache and storage), with no-store headers. The viewer
port serves only its page and manifest, and there are no directory listings. verify_viewer.py fetches every reachable file
and greps it for the version names; 0 hits is required. No checker result is in the viewer. The COST file (by version) and
the checker table are separate files, outside the zip.
