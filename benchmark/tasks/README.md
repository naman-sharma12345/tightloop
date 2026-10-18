# tasks

Empty on purpose. The 20-task shortlist (repo, license read from its
LICENSE file at a pinned commit, what each task takes) is under review
before anything is vendored here. Only MIT or Apache-2.0 licensed
repositories are eligible; a repository without a clear license is marked
do-not-vendor and skipped.

The task set mixes three kinds:

1. **Bug fixes** - real upstream fix commits that add tests; the agent
   starts at the parent commit and the added tests are the hidden check.
2. **New features** - real upstream feature commits; the agent implements
   from the issue/PR description, checked by the upstream tests.
3. **From-scratch app builds** - small self-contained apps built from a
   spec; no source repository needed, checked by a pinned test script.

Each task will be one JSON file:

```json
{
  "name": "owner-repo-short-slug",
  "kind": "bugfix | feature | app",
  "source": "https://github.com/owner/repo",
  "license": "MIT",
  "license_commit": "<sha the LICENSE file was read at>",
  "commit": "<pinned sha>",
  "instruction": "what the agent is asked to change or build",
  "hidden_tests": ["path/to/test::case"],
  "holdout": false
}
```

`holdout: true` marks tasks the skill was never tuned on; score.py keeps
them in separate tables, always.
