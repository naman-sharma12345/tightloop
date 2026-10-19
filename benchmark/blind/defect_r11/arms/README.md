# Defect count r11, round "arms" (18 blind builds)

Scored with the FROZEN r11 package in the folder above (CHECKLIST_r11.md, PROTOCOL.md, ERRATA_r11.md, SCORER_PROMPT.md, make_scores.py, scorer/). None of those files was edited. Weights: blocker 10, major 3, minor 1. One root cause counts once. Unlisted defects are kept apart and are not in the score. The labels are blind: the scorers never saw which arm or run made a build.

## Inputs
- Builds: B01-B18, each with SPEC.txt (trip: B01 B13 B14 B15 B17 B18; invoice: B02 B05 B06 B11 B12 B16; habits: B03 B04 B07 B08 B09 B10). Hash manifest BUILDS_MANIFEST.json sha256 6f5fddbdf73d405b41ac298999f2d46ea8778d73c8237c1930524a6807b8eb01; all 78 files matched it before and after scoring.
- Frozen files, sha256 (equal to commit 4a635720 before and after this round):
- CHECKLIST_r11.md: 7495424dc0ab4f1df375a7802dddf1e1cc4c2e9aee2074b9adbc10d226865e99
- PROTOCOL.md: 2132b9491b35b2db02f67985829794f92b73c5524793c0b5d7f1ad1b4e06eb77
- ERRATA_r11.md: 00d016fc8505c1219093bea771ec30a5bc770c01855a22e3166e3a412775b8e6
- SCORER_PROMPT.md: 17130eb78ad77f59b5fb988cd523be05dd02299f876c24a25ed2f9fec802d153
- make_scores.py: 266c879b191c7d40a91ecfdfe88064c1030c9310f222a6a19883572142cea820
- scorer/adapters/B01.py: 9e008c4e8b46d6855675821cca50c6d9f2d2690b15e5b5432e38f341f540e076
- scorer/adapters/B02.py: c2c3ac7393d9bab4ff2ab9690065e06bbd379547d90140faa4f2041a0839c60a
- scorer/adapters/B03.py: f9484d443d3d1f6363e4814c9149e908165a81aa76e02463262d1939d71cb262
- scorer/adapters/B04.py: 4e16d3af6e41c33a59675df1979932154d15929070d23c98c2363a904856ef4c
- scorer/adapters/B05.py: dc8d57e739cc8cad8918253162cd724d29994fa25e7277670fd900a0f30ec625
- scorer/adapters/B06.py: 27b0342c575f40d1453a576d60b72ee58fa940e2e95e88b34f7598044e6d6293
- scorer/adapters/B07.py: bfba7bf716779bb221113707aafbe4363491394f0220a4537f0e3b44dbfdc00f
- scorer/adapters/B08.py: d1c2ca8c1b05d72eaf5a94631c208552a7bd7bd0c757cab7f0da45bb19a121d3
- scorer/adapters/B09.py: 1ab5b73d7793ed708019c414f8c6626b7d58cfdbfc3aa3edfad241e96fe28d29
- scorer/common.py: e9435245586ccf572a439a4a419584dc834ac0d6845773d7e77ab18ad4339ae1
- scorer/run_all.py: 7fb32affa8219df924668051061b98c6da12223adff17bef8f059b74ea57d04d
- scorer/run_build.py: 91baf01692f96228a4cce80977e65dd0d60d12ef1d7226485c25c2d32566ae23
- scorer/serve.py: 15a4f30b299b87f3feb5af963b64992a8ac4d47027bbf857675c1502ba5de5bc
- scorer/steps_habits.py: 219fc780ff9d245996e32535585b101a25b697ca28d40e32f66215b9276dd056
- scorer/steps_invoice.py: 70fbf7797523de8eccac0068283583aa1b3b16a3d211b2789899e6b4cb91cb4d
- scorer/steps_trip.py: 6fa0aba4c35dceb2ddebbb08d1ec2af6f3fc8d58bbb4749670263331493c299d

## Files here
- SCORES_r11_arms.jsonl, DEFECTS_r11_arms.jsonl: OFFICIAL. Made by the frozen make_scores.py run unchanged (byte copy, sha256 266c879b...) in a temp folder over verdicts/; it names its outputs *_ns.jsonl, which were renamed to *_arms.jsonl. It was not run in place, so the no-skill files were not touched.
- verdicts/: official per-label verdicts (final rerun; invoice print items by the frozen probe).
- verdicts_with_beforeprint/: the 6 invoice verdicts with the print items scored WITH beforeprint. Not in SCORES.
- PRINT_SCORES_r11_arms.jsonl: score_frozen_probe (official) and score_with_beforeprint side by side for each invoice build.
- first_pass/: the first scoring pass as it stood (verdicts/, DEFECTS and SCORES made the same way). Its invoice print items were scored with beforeprint.
- PASS_DIFF.md: every build whose score changed between the first pass and the final files.
- NOSKILL_PRINT_RECHECK.jsonl: print items of the 3 no-skill invoice builds, both ways.
- results/: step output of each run (first_pass, final_rerun, frozen_probe, solo, noskill_recheck). Screenshots are not committed (as in the no-skill round).
- adapters/: per-build locators (selectors and click paths only, no pass/fail logic). arms_run.py drives the frozen scorer with them. ns_print_recheck.py runs the no-skill recheck with the FROZEN no-skill adapters.
- ERRATA_r11_arms.md: new erratum I28.

## Official scores
| label | spec | B/M/m | weighted score | unlisted |
|---|---|---|---|---|
| B01 | trip | 0/0/1 | 1 | 0 |
| B02 | invoice | 0/1/1 | 4 | 0 |
| B03 | habits | 0/0/0 | 0 | 0 |
| B04 | habits | 0/0/1 | 1 | 0 |
| B05 | invoice | 0/0/1 | 1 | 0 |
| B06 | invoice | 0/1/0 | 3 | 0 |
| B07 | habits | 0/0/0 | 0 | 0 |
| B08 | habits | 0/0/1 | 1 | 0 |
| B09 | habits | 0/0/0 | 0 | 0 |
| B10 | habits | 0/0/1 | 1 | 0 |
| B11 | invoice | 0/0/1 | 1 | 0 |
| B12 | invoice | 0/1/1 | 4 | 0 |
| B13 | trip | 0/1/0 | 3 | 0 |
| B14 | trip | 0/0/0 | 0 | 0 |
| B15 | trip | 0/0/0 | 0 | 0 |
| B16 | invoice | 0/0/1 | 1 | 0 |
| B17 | trip | 0/2/1 | 7 | 0 |
| B18 | trip | 0/1/0 | 3 | 0 |

## Deviations from the protocol (named)
1. One build at a time was broken once. The final rerun of all 18 ran while 2 other scoring jobs ran on the same box (the frozen-probe invoice runs and the no-skill recheck). Its step results matched the first pass for every build, so the official verdicts did not depend on it. The 3 builds whose official score differs from the first pass (B02, B06, B12) were re-run alone afterwards, and the no-skill recheck was redone alone. Results in results/solo/ and results/noskill_recheck/.
2. Print probe. The new invoice adapters can fire the browser's beforeprint event before emulating print media. Some builds only draw their print sheet on that event. The no-skill round did not fire it. SCORES uses the frozen probe (no beforeprint) so it compares with the no-skill round. The with-beforeprint score sits beside it:
| label | score_frozen_probe (official) | score_with_beforeprint |
|---|---|---|
| B02 | 4 (0/1/1) | 1 (0/0/1) |
| B05 | 1 (0/0/1) | 1 (0/0/1) |
| B06 | 3 (0/1/0) | 0 (0/0/0) |
| B11 | 1 (0/0/1) | 1 (0/0/1) |
| B12 | 4 (0/1/1) | 1 (0/0/1) |
| B16 | 1 (0/0/1) | 1 (0/0/1) |
   The no-skill invoice builds were re-checked both ways:
| label | item | frozen_probe | with_beforeprint |
|---|---|---|---|
| NS_B03 | I02 | pass | pass |
| NS_B03 | I34 | pass | pass |
| NS_B06 | I02 | pass | pass |
| NS_B06 | I34 | pass | pass |
| NS_B07 | I02 | pass | pass |
| NS_B07 | I34 | pass | pass |
   No no-skill score changes.
3. 18 labels instead of 9; each label's spec comes from its SPEC.txt. New adapters were needed for the new builds; they are locators only.

## Adapters (sha256)
- adapters/B01.py: ee1361cc8c52a0b2205badb9deb31bc545430d9729935848f039708514e437e6
- adapters/B02.py: 2bed1e8c5f420e0577cc428ee860fd3dffadd8e2132adfbbbdcfca9522679495
- adapters/B03.py: 6aea28e7a29e6aaa968113d895c88eef9df9e001ca14829e09c5f053070d95cf
- adapters/B04.py: a2602dc8af14585840fdb3666c855449a08c807736c9fb813f97096e71d242bf
- adapters/B05.py: 0104961b6c104adf05f2d0a49667e950c4da5b2d64fc2a1bb101af3a72a56c9a
- adapters/B06.py: f2ca5797a7292fc6ac7efef68a9172aa931dc478167ffc6f9e27d9712bb8c57d
- adapters/B07.py: 4fac319d432c711c1264f834d99455b43450abf5f3bc2fab34d0177400ab3887
- adapters/B08.py: 60582f8ca8eb152316aa492e1939bc4c633cd679bc5022ffc88505cf3fd91229
- adapters/B09.py: 9207562523e10d884b1e7e95802458e7d96235ea08218140bb2ea6a9a025a3be
- adapters/B10.py: c7c0d7a56943f5ddb095dbec9430618c13686be78eb769b1392821496dc3a8b0
- adapters/B11.py: b1a9bcbb7677536422762c7bb41ff48b8bd808da6838691a91c34d11d2a4d86c
- adapters/B12.py: 09d32b85434a72b9469340bffbfc789bf7629184be65b7751c67ccd5f33b0d05
- adapters/B13.py: 50d238bcaf19576d7011950326929c9177475ebb252ab6eeccf8d77e8e129cb2
- adapters/B14.py: d21f6c7c46470f8d4b0175e65c5fd29c7c7838955cf63cb9d8baa92a1e4cccfb
- adapters/B15.py: 49856dcd4b44f80cadbf5bad3d1d268595026cf2cddeaa2772f195dc954660c9
- adapters/B16.py: d5a5670e78970903405f18991b7e766a52e9be452e532444422f29ffe0e36934
- adapters/B17.py: 73dff90a9c4203093c8130e0e79b2d21b43222368426d6ac8b34354d8a6f4e6c
- adapters/B18.py: b1816e78e22c50a744fd2313a5eec653142c823b5d12226290d0e17bf353dcbd
Steps an adapter could not map: none. Note: in B07 the times-per-week control is a 1-7 select, so the H07 step cannot enter 0 or 8 (the scorer prompt counts an impossible input as a pass); this is the app's control, not a missing locator.

## Errata
- H15, I15 from ERRATA_r11.md applied as written. ERRATA_r11.md has no I28 entry.
- New: I28 in ERRATA_r11_arms.md. "92,02 €" passes (same number, the currency's own symbol, Intl formatting). It decided I28 for all 6 invoice builds. It changes no no-skill score: the no-skill round passed I28 on all 3 invoice builds.

## B09 flake
B09 G10: first pass run 1 = 1 (minor: 8 heat cells measured just under 40 px mid-transition), first pass run 2 = 0; final rerun = 0. Official 0. Rule for all builds: the final rerun decides, and a disagreement gets a solo rerun. No build disagreed.
