# Branches before 1.0

At the 1.0 release these working branches were deleted. Each one is kept as a
lightweight tag `archive/<branch>` on its last commit, so nothing is lost:

```sh
git fetch origin 'refs/tags/archive/*:refs/tags/archive/*'
git checkout -b v6/v11 archive/v6/v11
```

"In main" means the branch's whole history is part of `main`'s history.

| branch | tag | last commit | in main | what it held |
|---|---|---|---|---|
| `v6/app-harness-v2` | `archive/v6/app-harness-v2` | `5facf2129f89` | yes | app harness v2 and the no-skill / v4c / v11 app rows |
| `v6/benchmark-rows` | `archive/v6/benchmark-rows` | `7cff76a3349b` | no (tag only) | pass rows and the final table |
| `v6/defect-r11` | `archive/v6/defect-r11` | `cc5182840412` | yes | frozen r11 defect package and scores |
| `v6/gatefix` | `archive/v6/gatefix` | `fb2379b82823` | yes | gate.sh fix rows for v4c and v10 |
| `v6/judge-r11-ns` | `archive/v6/judge-r11-ns` | `268a7ebc79eb` | no (tag only) | r11 blind judge, no-skill round |
| `v6/v10` | `archive/v6/v10` | `bbadd86001d2` | yes | v10 prereg and rows (v4c without the gate diff echo) |
| `v6/v11` | `archive/v6/v11` | `28092004a6d9` | yes | v11 prereg and arm |
| `v6/v5-prep` | `archive/v6/v5-prep` | `92d2da8f03c3` | no (tag only) | v5 / v5c blind runs and judge |
| `v6/v6c-prep` | `archive/v6/v6c-prep` | `ed5e932a54eb` | no (tag only) | v6c blind run and judge |
| `v6/v7-prep` | `archive/v6/v7-prep` | `f86c480b3f16` | no (tag only) | v7 blind run and judge |
| `v6/v8-prep` | `archive/v6/v8-prep` | `b16a28e99288` | yes | v8 / v9 blind runs and judges |
| `v8-blind-r3-prereg` | `archive/v8-blind-r3-prereg` | `66796b9711c4` | no (tag only) | blind round 3 pre-registration |

Kept as branches: `main`, `v6/instinct-rows` (live work), `rotate-flag`.
