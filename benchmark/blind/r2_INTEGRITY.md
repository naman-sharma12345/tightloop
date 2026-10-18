# Blind round 2: integrity record (Naman m:ad61cc34)

Written before any round-2 build. Nothing below names which version sits behind which label.

## Sealed key
- Location: outside the repo and outside every zip (the Tab box's files area, `tl_blind/r2/KEY.json`, read-only).
- sha256 (taken with `sha256sum` only; the file was not opened for this record):
  `2fa05c9609411681d61c4eede6c0b29a5a451733a4b14a051eb5a48a47ba0433`.
  This matches the value committed at bc4b673 in results/blind_r2_key_sha256.txt.
- Labels: A-D per app. Each app has its own independent shuffle of the 4 versions (no-skill, ponytail, tightloop-v4,
  tightloop-v4c), drawn in the fixed app order bookmarks, expenses, kanban from one seeded `random.Random(seed)`. The seed is
  recorded inside the key. The key was sealed at 18:26Z on 2026-10-18 and is committed verbatim only at the reveal.
- The mapping is never in the viewer zip. verify_viewer.py lists the zip and fails on any entry named KEY / mapping / COST /
  METRIC / check / .png. Self-test: a KEY.json planted in a test zip is caught (results/blind_r2_selftest.txt).

## Hashes at ba3cef6
- benchmark/blind/checks/check_app.py: `ad6b508757dc25957e3e04d2db68a8e876c59d729e46ce2f9a5596908ee8ff72`
- benchmark/blind/specs/r2/bookmarks.md: `b737fe37e9d6bb6f341b324ff51b02da50e04a0bac72e7336f3d761dcd15e6c1`
- benchmark/blind/specs/r2/expenses.md: `cb501d9933459ec4c683eb3733ed89fed66b6cdc3b4e78be4b9e7c0080e7ccab`
- benchmark/blind/specs/r2/kanban.md: `c768cbc03511cb8a223b9b7ee7ea5e478b6c0e9fc4681c2223a0f3efc06a5b10`
  (unchanged since 3e86a80)

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

Residual, stated plainly: the session has network access, which the model API needs, and this repository is public on
GitHub. A session could in principle fetch the checker from there. The web tools are disabled for every session, as runner.py
does for all arms. After each session the driver greps the whole session transcript for `check_app`, `KEY.json`,
`blind/checks`, `checks/reference`, `blind_rows`, `tl_blind`, `raw.githubusercontent` and this repo's GitHub path, and
records the hit count per build. Any hit is reported, not hidden.

## Viewer
One zip, one server. Each label runs on its own port (its own origin, cache and storage), with no-store headers. The viewer
port serves only its page and manifest, and there are no directory listings. verify_viewer.py fetches every reachable file
and greps it for the version names; 0 hits is required. No checker result is in the viewer. The COST file (by version) and
the checker table are separate files, outside the zip.
