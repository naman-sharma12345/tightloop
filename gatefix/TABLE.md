# GATEFIX result: tokio-02, n=3 per arm (rows in gatefix/rows.jsonl, per-run calls and gates in gatefix/calls.jsonl)

Worker numbers (claims). cw = in + 5*out + 0.1*cache_read + 1.25*cache_write. tokens = in + out + cache_read + cache_write.
"old v4c" = instinct rows a_s30/a_s32/a_s34 (v6/instinct-rows); "old v10" = v10 rows 10-12 (v6/v10). Both used the buggy gate.

v4c-gfix (n=3): (a) model calls 5/6/5 (tool calls 4/5/4) | (b) tokens 159733, 198511, 161513 median 161513 [159733-198511]; cw 63646.65, 42931.5, 36656.7 median 42931.5 [36656.7-63646.65] | (c) hidden test 3/3 | (d) gates FAIL,PASS / FAIL,FAIL,PASS / FAIL,PASS | call1 COLD/WARM/WARM
v10-gfix (n=3): (a) model calls 5/4/5 (tool calls 4/3/4) | (b) tokens 162323, 126230, 164101 median 162323 [126230-164101]; cw 36782.9, 30243.05, 37443.1 median 36782.9 [30243.05-37443.1] | (c) hidden test 3/3 | (d) gates FAIL,PASS / FAIL,PASS / FAIL,PASS | call1 WARM/WARM/WARM
old v4c (n=3): (a) model calls 5/5/6 (tool calls 4/4/5) | (b) tokens 162834, 163047, 197994 median 163047 [162834-197994]; cw 36675.8, 36558.4, 42348.75 median 36675.8 [36558.4-42348.75] | (c) hidden test 3/3 | (d) gates FAIL,FAIL,PASS / FAIL,FAIL,PASS / FAIL,FAIL,FAIL | call1 WARM/WARM/WARM
old v10 (n=3): (a) model calls 4/4/4 (tool calls 3/3/3) | (b) tokens 127015, 128664, 128158 median 128158 [127015-128664]; cw 32433.7, 32290.3, 31463.2 median 32290.3 [31463.2-32433.7] | (c) hidden test 3/3 | (d) gates FAIL,FAIL / FAIL,FAIL / FAIL,FAIL | call1 WARM/WARM/WARM
v10-gfix vs v4c-gfix: median calls 5 vs 5 (edge 0 call(s)); tokens ratio 1.01 OVERLAP; cw ratio 0.86 OVERLAP

## Where the calls went (from each transcript's tool calls)
Every run: 1 read call, 1 edit+gate call (FAIL: cargo says `specification tokio is ambiguous`), then a fix, then the reply.
- v4c-gfix: in 3 of 3 runs, one extra call was spent finding the hidden FAIL reason (the diff printed last pushed it out of `tail -40`): `cat fail.md` + a hand cargo run (runs 1, 3) or a gate rerun piped through `grep -v '^[+ -]'` (run 2). Split read (a 2nd read call before the edit): 1 of 3 runs (run 2).
- v10-gfix: 0 of 3 runs needed a reason-finding call (the reason was on screen; the next call fixed it and the gate said PASS). Split read: 2 of 3 runs (runs 1, 3).
- old v10 (buggy gate): read, edit+gate FAIL, fixed gate = false FAIL, reply = 4 calls. With the fixed gate, that same third call says PASS and the reply follows, so 4 calls either way: the false FAIL cost old v10 0 calls ("stopped early" did not save a call). v10-gfix's 5s come from split reads.
- old v4c (buggy gate): gates FAIL, FAIL, PASS: the second FAIL was the false one after a correct fix, and the model ran a third, narrower gate (filter `rx_mark...`, "1 passed") to get PASS.

## v10's edge, gate fixed
Median model calls: v10-gfix 5 vs v4c-gfix 5 = an edge of 0 calls by median. Total over 3 runs: 14 vs 16 (2 calls, about 0.67 per run).
Tokens: median ratio 1.01, ranges OVERLAP. cw: median ratio 0.86, ranges OVERLAP (v4c-gfix run 1 had a COLD call 1, cw 63646.65; warm-only v4c-gfix cw 42931.5 and 36656.7).
The reason-visible gate still removes one "find the reason" call per FAIL (3/3 vs 0/3), but on these 6 runs split reads (v10-gfix 2/3, v4c-gfix 1/3) used up most of that.
n=3, so this is suggestive only. No wall claims.
