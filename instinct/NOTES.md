wall_comparable stands on rows 26, 32, 34, 48 only

# instinct rows - notes

- No wall claims from row 49 on until a fully sampled clean row (Pally m:26b7c234). The top line is updated if a later row is sampled in full with 0 Kimo hits and no KIMO_WINDOWS overlap.
- wall_comparable rule: true only when the session was sampled in full from its first second, with 0 Kimo hits and no KIMO_WINDOWS.txt overlap. A partial or re-attached sample is never comparable (wall_comparable_corrected=false on rows 31, 33, 35, 47).
- split key: holdout/rows.jsonl rows are 'holdout'; baseline/rows.jsonl rows are 'tuning' (pass a and pass b v8). ghcli-01b rows will be 'holdout_amended'.
- holdout/HOLDOUT_MANIFEST.tsv: blob hash of each holdout task file, plus the commit that last touched it.
- Defect score per arm: not measured.
