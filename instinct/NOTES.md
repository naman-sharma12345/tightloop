wall_comparable (sampler 6735e9c236a1, full sample, 0 hits, no window) stands on row 48 only; rows 26/32/34 tokens-only for wall (older detection)

# instinct rows - notes

- Next mutant build waits for a gap after pass b and ghcli-01b; otherwise wall stays tokens-only.
- windows_parser = "v7: bare single-timestamp lines ignored for closing, flagged unmatched". New key windows_parser on every row from 57 on; rows 1-56 were parsed by the earlier KIMO_WINDOWS parser (the current KIMO_WINDOWS.txt has no bare single-timestamp end line, so no recorded row is affected). Sampler sha unchanged: 6735e9c236a1.
- wall_comparable_v6=false on rows 26, 32, 34 (reason "detection logic predates sampler 6735e9c236a1; not replayable"). New key only; their pushed wall_comparable value is not edited.
- From row 57 on, each row has instinct/kimo_samples/row_NNN.jsonl with the raw per-sample hit list (pid, comm, cwd, exe for each 3 s sample), so wall detection can be replayed later. Rows 1-56 have none (raw samples were not kept).
- No wall claims from row 49 on until a fully sampled clean row (Pally m:26b7c234). The top line is updated if a later row is sampled in full with 0 Kimo hits and no KIMO_WINDOWS overlap.
- wall_comparable rule: true only when the session was sampled in full from its first second, with 0 Kimo hits and no KIMO_WINDOWS.txt overlap. A partial or re-attached sample is never comparable (wall_comparable_corrected=false on rows 31, 33, 35, 47).
- split key: holdout/rows.jsonl rows are 'holdout'; baseline/rows.jsonl rows are 'tuning' (pass a and pass b v8). ghcli-01b rows will be 'holdout_amended'.
- holdout/HOLDOUT_MANIFEST.tsv: blob hash of each holdout task file, plus the commit that last touched it.
- cost_weighted = in + 5*out + 0.1*cache_read + 1.25*cache_write.
- Defect score per arm: not measured.
- M2 window by timestamp (2026-10-19T06:28:03Z-06:39:59Z): wall_comparable_m2=false on rows 49, 50, 51, 52, 53, 54, 55, 56 (run interval touches the window; start = agent log mtime - wall_seconds, end = grade log mtime). row 48 interval 06:26:37Z-06:27:29Z: does NOT touch the M2 window (ends 34 s before 06:28:03Z); not flagged. Row 57 starts 06:44:4xZ, after the window.
- Rows 26, 32 and 34 are "sampler-unverified: tokens and cost_weighted only, wall_comparable=false; raw samples were not kept, so no replay is possible."
- instinct/mutation/: Kimo focus_series mutation files M1/M2 (byte-for-byte copies) + README.md (Pally m:8bb295db).
