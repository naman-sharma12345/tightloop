# tasks

Empty on purpose. The 20-task shortlist (repo, license, what each task
takes) is under review before anything is vendored here. Only MIT or
Apache-2.0 licensed repositories are eligible; a repository without a
clear license is marked do-not-vendor and skipped.

Each task will be one JSON file:

```json
{
  "name": "owner-repo-short-slug",
  "source": "https://github.com/owner/repo",
  "license": "MIT",
  "commit": "<pinned sha>",
  "instruction": "what the agent is asked to change",
  "hidden_tests": ["path/to/test::case"],
  "holdout": false
}
```

`holdout: true` marks tasks the skill was never tuned on; score.py keeps
them in separate tables.
