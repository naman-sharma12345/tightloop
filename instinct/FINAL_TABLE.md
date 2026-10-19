# Final scoring table - tightloop benchmark (instinct rows)

Written 2026-10-19. Source: `baseline/rows.jsonl` (split=tuning, 48 rows) and `holdout/rows.jsonl` (split=holdout, 27 rows) at v6/instinct-rows head b6e8654. The explicit `split` key on every row is the split label used below.

Counted rows: 66 of 75. The 9 ghcli-01 holdout rows stay excluded per `holdout/LABELS.tsv` (invalid task: underspecified signature; the instruction did not name PrintUnchanged). ghcli-01b is its fixed replacement.

Ratio = median(input+output tokens) of the arm's runs on that task and split / median of no-skill on the same task and split. Token source on every row: claude CLI stream-json final result event, parsed by runner.launch. Pass rate sits beside every ratio. No cell has n<3, so no n<3 flags fire; the small-n flags on gin-04 and ghcli-01b are by design (one holdout task each, n=3 per arm: one task is not a verdict).

n per arm - tuning: no-skill 12, ponytail 12, v4c 12, v8 12. Holdout: no-skill 6, ponytail 6, v4c 6, v8 0 (v8 has no holdout rows).

## Tuning (split=tuning, baseline/rows.jsonl)

### fd-01
| arm | n | pass | median in+out (min, max) | ratio vs no-skill |
|---|---|---|---|---|
| no-skill | 3 | 3/3 | 3068 (2891, 3386) | 1.00 (base) |
| ponytail | 3 | 3/3 | 1980 (1941, 2123) | 0.65 |
| tightloop-v4c | 3 | 3/3 | 2446 (1968, 2610) | 0.80 |
| tightloop-v8 | 3 | 3/3 | 2331 (2144, 2727) | 0.76 |

### gin-01
| arm | n | pass | median in+out (min, max) | ratio vs no-skill |
|---|---|---|---|---|
| no-skill | 3 | 2/3 | 2108 (1925, 2441) | 1.00 (base) |
| ponytail | 3 | 2/3 | 1888 (1720, 1908) | 0.90 |
| tightloop-v4c | 3 | 3/3 | 1441 (1329, 1701) | 0.68 |
| tightloop-v8 | 3 | 1/3 | 1333 (1235, 1417) | 0.63 |

### gin-02
| arm | n | pass | median in+out (min, max) | ratio vs no-skill |
|---|---|---|---|---|
| no-skill | 3 | 3/3 | 2564 (2171, 2684) | 1.00 (base) |
| ponytail | 3 | 3/3 | 1644 (1615, 1660) | 0.64 |
| tightloop-v4c | 3 | 3/3 | 1551 (1427, 1597) | 0.60 |
| tightloop-v8 | 3 | 3/3 | 1461 (1432, 1480) | 0.57 |

### tokio-02
| arm | n | pass | median in+out (min, max) | ratio vs no-skill |
|---|---|---|---|---|
| no-skill | 3 | 3/3 | 1759 (1659, 1941) | 1.00 (base) |
| ponytail | 3 | 3/3 | 1580 (1506, 1635) | 0.90 |
| tightloop-v4c | 3 | 3/3 | 1730 (1674, 2058) | 0.98 |
| tightloop-v8 | 3 | 3/3 | 2110 (1906, 2163) | 1.20 |

## Holdout (split=holdout, holdout/rows.jsonl)

### gin-04 (flag: one task, n=3 per arm - not a verdict)
| arm | n | pass | median in+out (min, max) | ratio vs no-skill |
|---|---|---|---|---|
| no-skill | 3 | 3/3 | 1369 (1289, 1575) | 1.00 (base) |
| ponytail | 3 | 3/3 | 1339 (1248, 1350) | 0.98 |
| tightloop-v4c | 3 | 3/3 | 1247 (1239, 1264) | 0.91 |

### ghcli-01b (flag: one task, n=3 per arm - not a verdict; amended task added after ghcli-01 was seen, holdout only, no tuning on it)
| arm | n | pass | median in+out (min, max) | ratio vs no-skill |
|---|---|---|---|---|
| no-skill | 3 | 3/3 | 2715 (2405, 3125) | 1.00 (base) |
| ponytail | 3 | 3/3 | 2407 (2052, 2418) | 0.89 |
| tightloop-v4c | 3 | 3/3 | 2059 (1919, 2280) | 0.76 |

ghcli-01b rotation: arm order per run matches `instinct/ORDER_ghcli01b.json` (3 arms x 3 runs, rotated; per-row arm_order_repeat/position checked).

### Excluded: ghcli-01
9 rows, 0/9 pass in every arm, excluded per `holdout/LABELS.tsv`: invalid task, underspecified signature. Not counted anywhere above.

## Quality (blind round 2 only)

Quality is cited from blind round 2 only: `benchmark/blind/r2_JUDGE_RANKS.md` and `r2_REVEAL.md`. n=1 per app, single judge, not a distribution. Round 1 is void (shared port). The row files carry no quality score.

Mean rank across bookmarks/expenses/kanban: no-skill 1.00, tightloop-v4c 2.33, tightloop-v4 3.00, ponytail 3.67. v4c cost-weighted tokens were 53% of no-skill in that round.

## v8 status

v8 is tokens-only until it goes through a sealed-key blind round on the r2 apps (bookmarks/expenses/kanban) vs v4c and no-skill. No v8 better-on-tokens claim until its passes match v4c.

Per-task tuning facts (all split=tuning, n=3 per arm): fd-01 v8 0.76 with 3/3 pass vs v4c 0.80 with 3/3; gin-02 v8 0.57 with 3/3 vs v4c 0.60 with 3/3; tokio-02 v8 1.20 with 3/3 vs v4c 0.98 with 3/3, a real loss for v8 on tokio-02 (cost-weighted 1.40x vs v4c with separate ranges, per `instinct/NOTES.md`); gin-01 v8 0.63 but 1/3 pass vs v4c 3/3, so not a win regardless of tokens.

Where v8's passes match v4c (fd-01, gin-02), v8's median in+out is lower. There is no overall v8 claim: gin-01 fails the pass gate, tokio-02 is a token loss, and quality is unjudged.

## Caveats

- Holdout manifest timing: `holdout/HOLDOUT_MANIFEST.tsv` was first committed in 33f55c1 (2026-10-19T06:32:38Z); the first holdout row (c8ebc4f, ghcli-01 no-skill run1) is 2026-10-19T05:04:21Z. The manifest postdates the first holdout row by about 88 minutes. The ghcli-01b manifest line and order file landed in 0351248 (06:58:39Z), before the first ghcli-01b row (523eb20, 07:03:42Z).
- ghcli-01b rows carry split='holdout' with a holdout_variant key ("instruction names the signature; added after ghcli-01 was seen"). `instinct/NOTES.md` had said these rows would be 'holdout_amended'; the pushed value is 'holdout'.
- No pooled medians across splits are given: they would mix tuning and holdout, and v8 has no holdout rows (12 tuning rows vs 18 tuning+holdout for the other arms), so pooled lines are not comparable (Naman m:0dd4f9ac).
- 40% target: missed on both readings (<=0.40x and <=0.60x), per the pooled reading in `instinct/NOTES.md` (Naman m:0dd4f9ac). Best v4c tuning median ratio above is 0.60 (gin-02).
- Sequencer swaps, wall_comparable limits, rows 58/60 fail_reason_class, and the v8 tokio-02 loss line: `instinct/NOTES.md`.
