# PASS_DIFF, round "arms"

First pass = the verdicts as they stood after the first scoring pass (first_pass/). Final = the official files in this folder.

## Rerun-caused changes: none
The final rerun of all 18 builds (results/final_rerun/) gave the same step results as the first pass for every build. The only differences were timestamps, generated ids and the timing of toast / live-region text. Every screenshot that differed in pixels was checked by eye; none showed a visual change. So no score changed because of the rerun.

## Score changes in the official files: 3 builds, all from the print-method rule
The official SCORES use the FROZEN print probe (print media emulated, no beforeprint event), as in the no-skill round. The first pass scored the invoice print items WITH beforeprint. That changes 3 invoice builds. Each was then re-run ALONE (nothing else running) in frozen-probe mode (results/solo/); the solo run gave the same result.

| label | spec | first pass B/M/m | first pass score | final B/M/m | final score | cause | solo rerun (frozen probe, alone) |
|---|---|---|---|---|---|---|---|
| B02 | invoice | 0/0/1 | 1 | 0/1/1 | 4 | Method, not the rerun: official print score is now the frozen probe (no beforeprint). The print page is blank, so I34 fails (major). First pass used beforeprint. | 4 (0/1/1), same step results |
| B06 | invoice | 0/0/0 | 0 | 0/1/0 | 3 | Method, not the rerun: frozen probe. The print page is blank, so I34 fails (major). I02 has the same cause, counted once. First pass used beforeprint. | 3 (0/1/0), same step results |
| B12 | invoice | 0/0/1 | 1 | 0/1/1 | 4 | Method, not the rerun: frozen probe. The editor itself prints (2 columns, totals not break-avoid), so I34 fails (major). First pass used beforeprint. | 4 (0/1/1), same step results |

With beforeprint, all 6 invoice builds keep their first-pass scores (see PRINT_SCORES_r11_arms.jsonl).

## B09 flake (G10)
First pass, run 1: G10 minor (8 Saturday heat cells measured just under 40 px during a transition), score 1. First pass, run 2 plus a direct measurement: 0 controls under 40 px, score 0 (verdict kept 0; the run-1 results file was overwritten, so run 1 is known only from the first scorer's notes). Final rerun: 0 controls under 40 px, score 0. Same rule for every build: the final rerun decides; where it disagrees with the first pass the build gets a solo rerun. No build disagreed.
