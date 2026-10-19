# appv2 r11 token table: no-skill vs tightloop-v4c vs tightloop-v11 (n=3 per spec, 27 builds)
Harness v2 snapshot tl_blind_appv2b (git archive 0a98f76), driver blind_driver_v2.py <arm>, queue orders/ORDER_v2.3.json, same model (claude-opus-5-5) and settings for all arms.
Specs habits cff54483, invoice 7b6d1ac8, trip 4158176e. One build at a time, overlap clean on all 27, 0 retries, 0 voids, 0 timeouts, 0 browser crash events.
v11 ran from appv2b after its arm folder was copied in byte for byte from 40084313 (see tightloop-v11/ARM_ADDENDUM.txt; frozen files sha256 identical before/after the copy). No harness file edited.
cost_weighted = in + 5*out + 0.1*cache_read + 1.25*cache_write (recomputed from the rows; matches the rows' own field). total tokens = in + out + cache_read + cache_write.
Usage source: claude CLI final result event; checked against its modelUsage: one model, no subagent messages in any of the 27 logs.
Cold rule: a build is cold if more than 300 s passed between the previous build's end (any arm) and its start (prompt cache TTL 5 min). Cold: no-skill habits-1 (first build of the day's runs), tightloop-v4c habits-1 (14225 s gap after no-skill). v11 habits-1 started 133 s after v4c ended, so it counts warm.
No quality judged here; checks_passed is the generic v2 smoke checker only.

| spec | arm | n | cost_weighted median [min-max] | total tokens median [min-max] | output median | cold runs | warm-only cw median [min-max] |
|---|---|---|---|---|---|---|---|
| habits | no-skill | 3 | 596k [487-605k] | 1818k [1113-1870k] | 60.4k | run 1 | 546k [487-605k] (n=2) |
| habits | tightloop-v4c | 3 | 520k [497-526k] | 831k [227-1344k] | 65.8k | run 1 | 512k [497-526k] (n=2) |
| habits | tightloop-v11 | 3 | 420k [324-556k] | 174k [143-217k] | 60.2k | none | 420k [324-556k] (n=3) |
| invoice | no-skill | 3 | 877k [869-929k] | 2612k [2030-2960k] | 102.5k | none | 877k [869-929k] (n=3) |
| invoice | tightloop-v4c | 3 | 854k [616-1065k] | 1351k [417-2370k] | 110.3k | none | 854k [616-1065k] (n=3) |
| invoice | tightloop-v11 | 3 | 589k [549-650k] | 228k [215-248k] | 87.2k | none | 589k [549-650k] (n=3) |
| trip | no-skill | 3 | 859k [719-1060k] | 2687k [1995-3597k] | 92.9k | none | 859k [719-1060k] (n=3) |
| trip | tightloop-v4c | 3 | 656k [590-806k] | 651k [651-1722k] | 90.5k | none | 656k [590-806k] (n=3) |
| trip | tightloop-v11 | 3 | 516k [484-737k] | 301k [287-407k] | 73.9k | none | 516k [484-737k] (n=3) |

| arm | 9-build cw sum | median cw | vs no-skill (sum) |
|---|---|---|---|
| no-skill | 7.00M | 859k | 100% |
| tightloop-v4c | 6.13M | 616k | 88% |
| tightloop-v11 | 4.82M | 549k | 69% |

CLI list-price USD (total_cost_usd, Opus 5.5 rates, cache read 0.05x): no-skill $24.23, v4c $22.99, v11 $19.20 (9 builds each).
Turns min-max: no-skill (17, 36), v4c (3, 24), v11 (2, 3). Builds with test files: no-skill 0/9, v4c 6/9, v11 0/9.

Per build:
| build | cold | in | out | thinking (in out) | cache_read | cache_write | cw | total | turns | wall s | checks | usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| appv2-no-skill-habits-1 | cold | 44 | 60365 | 18544 | 1710962 | 98707 | 596348.95 | 1870078 | 27 | 612.07 | 1/2 | 2.0432 |
| appv2-no-skill-invoice-1 | warm | 44 | 102504 | 42159 | 2365529 | 144289 | 929478.15 | 2612366 | 28 | 1024.34 | 1/2 | 3.2448 |
| appv2-no-skill-trip-1 | warm | 40 | 82630 | 23455 | 1811962 | 100086 | 719493.70 | 1994718 | 24 | 761.12 | 1/2 | 2.5156 |
| appv2-no-skill-invoice-2 | warm | 34 | 102947 | 47113 | 1779911 | 147430 | 877047.60 | 2030322 | 22 | 904.29 | 2/2 | 3.1522 |
| appv2-no-skill-trip-2 | warm | 58 | 106492 | 42918 | 3335386 | 154996 | 1059801.60 | 3596932 | 35 | 1119.37 | 1/2 | 3.5721 |
| appv2-no-skill-habits-2 | warm | 30 | 59380 | 18285 | 980656 | 73281 | 486596.85 | 1113347 | 17 | 674.82 | 1/2 | 1.7503 |
| appv2-no-skill-trip-3 | warm | 48 | 92890 | 31391 | 2476480 | 117159 | 858594.75 | 2686577 | 31 | 857.35 | 1/2 | 2.9391 |
| appv2-no-skill-habits-3 | warm | 42 | 66201 | 22945 | 1666187 | 85766 | 604873.20 | 1818196 | 25 | 635.48 | 1/2 | 2.0863 |
| appv2-no-skill-invoice-3 | warm | 60 | 90886 | 19408 | 2758777 | 110559 | 868566.45 | 2960282 | 36 | 835.17 | 2/2 | 2.9225 |
| appv2-tightloop-v4c-habits-1 | cold | 6 | 71372 | 39554 | 27276 | 127997 | 519589.85 | 226651 | 3 | 604.56 | 1/2 | 2.0729 |
| appv2-tightloop-v4c-invoice-1 | warm | 8 | 88419 | 43757 | 205699 | 122464 | 615752.90 | 416590 | 6 | 730.54 | 2/2 | 2.4219 |
| appv2-tightloop-v4c-trip-1 | warm | 14 | 79626 | 33275 | 454282 | 117070 | 589909.70 | 650992 | 10 | 648.41 | 2/2 | 2.2688 |
| appv2-tightloop-v4c-invoice-2 | warm | 34 | 128337 | 70281 | 2068604 | 173160 | 1065029.40 | 2370135 | 24 | 1222.51 | 2/2 | 3.8464 |
| appv2-tightloop-v4c-trip-2 | warm | 30 | 96854 | 47879 | 1487325 | 138207 | 805791.25 | 1722416 | 18 | 858.13 | 1/2 | 2.9257 |
| appv2-tightloop-v4c-habits-2 | warm | 20 | 65782 | 30682 | 660135 | 104987 | 526177.25 | 830924 | 11 | 574.47 | 1/2 | 1.9727 |
| appv2-tightloop-v4c-trip-3 | warm | 14 | 90526 | 39426 | 432710 | 128033 | 655956.25 | 651283 | 8 | 746.81 | 1/2 | 2.5373 |
| appv2-tightloop-v4c-habits-3 | warm | 34 | 57644 | 24566 | 1216198 | 69853 | 497190.05 | 1343729 | 19 | 555.6 | 1/2 | 1.7455 |
| appv2-tightloop-v4c-invoice-3 | warm | 24 | 110284 | 50698 | 1085500 | 154923 | 853647.75 | 1350731 | 17 | 997.76 | 2/2 | 3.1975 |
| appv2-tightloop-v11-habits-1 | warm | 4 | 81951 | 52184 | 20208 | 115129 | 555691.05 | 217292 | 2 | 682.34 | 1/2 | 2.2187 |
| appv2-tightloop-v11-invoice-1 | warm | 4 | 96993 | 50149 | 20208 | 130612 | 650254.80 | 247817 | 2 | 783.62 | 2/2 | 2.5970 |
| appv2-tightloop-v11-trip-1 | warm | 6 | 68746 | 27618 | 115457 | 102596 | 483526.70 | 286805 | 3 | 552.64 | 1/2 | 1.9110 |
| appv2-tightloop-v11-invoice-2 | warm | 4 | 87245 | 47616 | 20208 | 120757 | 589196.05 | 228214 | 2 | 720.65 | 2/2 | 2.3527 |
| appv2-tightloop-v11-trip-2 | warm | 6 | 108745 | 64848 | 155331 | 142460 | 737339.10 | 406542 | 3 | 897.15 | 2/2 | 2.9183 |
| appv2-tightloop-v11-habits-2 | warm | 4 | 60232 | 31364 | 20208 | 93587 | 420168.55 | 174031 | 2 | 494.35 | 1/2 | 1.6766 |
| appv2-tightloop-v11-trip-3 | warm | 6 | 73928 | 31874 | 120096 | 107255 | 515724.35 | 301285 | 3 | 618.67 | 1/2 | 2.0389 |
| appv2-tightloop-v11-habits-3 | warm | 4 | 44790 | 16231 | 20208 | 78452 | 324039.80 | 143454 | 2 | 364.45 | 1/2 | 1.2921 |
| appv2-tightloop-v11-invoice-3 | warm | 4 | 80797 | 39478 | 20208 | 114190 | 548747.30 | 215199 | 2 | 663.86 | 2/2 | 2.1909 |
