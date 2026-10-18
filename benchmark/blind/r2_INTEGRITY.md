# Blind round 2: integrity record (Naman m:ad61cc34, m:ed447bea, m:fe05342f, m:530473fd)

Written before any round-2 build. Nothing below names which version sits behind which label.

## Sealed key (v2, resealed before any build)
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
- benchmark/blind/r2_run/blind_driver_r2.py: `fa6d19ba7e0d3f8f01412d45e1b1b338e1c4f02ff70444691467c46cf62da645`
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
3. a probe from inside the same sandbox: `test -e` on the key and on every checker copy, plus
   `find / -xdev -name check_app.py -o -name KEY.json -o -name 'blind_rows*'` (must be empty).

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
