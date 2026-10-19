# tightloop-v4c: see ../compare/TABLE_r11_3arms.md for the 3-arm table

| spec | arm | n | cost_weighted median [min-max] | total tokens median [min-max] | output median | cold runs | warm-only cw median [min-max] |
|---|---|---|---|---|---|---|---|
| habits | tightloop-v4c | 3 | 520k [497-526k] | 831k [227-1344k] | 65.8k | run 1 | 512k [497-526k] (n=2) |
| invoice | tightloop-v4c | 3 | 854k [616-1065k] | 1351k [417-2370k] | 110.3k | none | 854k [616-1065k] (n=3) |
| trip | tightloop-v4c | 3 | 656k [590-806k] | 651k [651-1722k] | 90.5k | none | 656k [590-806k] (n=3) |
