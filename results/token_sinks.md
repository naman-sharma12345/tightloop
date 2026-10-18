# Token sinks per arm (mined from run transcripts)

Source: every pass-2 and pass-3 row with a transcript (superseded rows included: this is cost anatomy, not a benchmark median). Script: results/analysis/token_sinks.py.
Method: visible text = chars/3.6 tokens (estimate). A tool result or visible output added before API call k is re-read by every later call (cache_read), so its cost = tokens x calls after it. Fixed prefix = first call's input+cache_read+cache_creation (CLI system prompt + tool schemas + appended SKILL.md + task prompt), re-read by every call. Output split uses each row's exact output total; hidden thinking = output minus visible estimate. Values are medians per run.

## Per-arm shape (median per run)

| arm | runs | API calls | fixed prefix/call | cache_read | in+out | output | hidden thinking | cache_creation |
|---|---|---|---|---|---|---|---|---|
| no-skill | 8 | 6.0 | 29368 | 176978 | 2695 | 2682 | 1384 | 36156 |
| ponytail | 8 | 5.0 | 30660 | 156971 | 1854 | 1844 | 873 | 24672 |
| tightloop-v3 | 8 | 7.5 | 33888 | 267650 | 2998 | 2983 | 1686 | 17571 |
| tightloop-v4 | 3 | 4 | 30113 | 120480 | 1965 | 1957 | 890 | 11637 |
| tightloop-v4a | 4 | 4.5 | 30050 | 136268 | 1601 | 1592 | 801 | 11756 |
| tightloop-v4b | 1 | 6 | 30156 | 187734 | 2087 | 2075 | 864 | 13144 |

## Ranked sinks: tightloop-v4 (median per run; in+out+cache_read median 121996)

| rank | sink | tokens/run | which rule causes it |
|---|---|---|---|
| 1 | fixed prefix x calls | 120452 | number of API calls; SKILL.md bytes are appended to the system prompt, so they ride every call; v4 steps 1-5 are 4-5 separate calls (look, edit, gate, sometimes skeptic rerun, report); the 1984 B SKILL.md is ~550 tokens on every call (v3's 12053 B ~3.3k) |
| 2 | re-read: file views (sed -n/cat ranges) | 5659 | step 1 'sed -n the ranges around the hits' (no size cap) + re-looks; ranges of 100-140 lines (e.g. sed -n 80,215p = 6.3 KB) re-read by every later call |
| 3 | out: hidden thinking | 890 | deliberation per call; more calls = more thinking; not addressable by text directly; fewer decision points |
| 4 | re-read: own earlier output | 532 | tool inputs/edit payloads stay in context; python heredoc edit scripts carry old+new text |
| 5 | out: tool inputs (commands, edit payloads) | 417 | step 2 edit style (python heredoc rewriting blocks) and long commands; edit scripts restate surrounding code |
| 6 | re-read: gate.sh run output | 408 | step 3 gate prints test tails + the full diff; diff re-printed after the agent already wrote it |
| 7 | out: final report | 253 | step 5 'at most 4 lines'; ~200-370 tokens |

Tool calls by kind (total over runs): file views (sed -n/cat ranges) 6, gate.sh run output 4

## Ranked sinks: tightloop-v4a (median per run; in+out+cache_read median 137868)

| rank | sink | tokens/run | which rule causes it |
|---|---|---|---|
| 1 | fixed prefix x calls | 135244 | number of API calls; SKILL.md bytes are appended to the system prompt, so they ride every call; v4 steps 1-5 are 4-5 separate calls (look, edit, gate, sometimes skeptic rerun, report); the 1984 B SKILL.md is ~550 tokens on every call (v3's 12053 B ~3.3k) |
| 2 | re-read: file views (sed -n/cat ranges) | 5841 | step 1 'sed -n the ranges around the hits' (no size cap) + re-looks; ranges of 100-140 lines (e.g. sed -n 80,215p = 6.3 KB) re-read by every later call |
| 3 | re-read: own earlier output | 897 | tool inputs/edit payloads stay in context; python heredoc edit scripts carry old+new text |
| 4 | out: hidden thinking | 801 | deliberation per call; more calls = more thinking; not addressable by text directly; fewer decision points |
| 5 | out: tool inputs (commands, edit payloads) | 502 | step 2 edit style (python heredoc rewriting blocks) and long commands; edit scripts restate surrounding code |
| 6 | re-read: gate.sh run output | 369 | step 3 gate prints test tails + the full diff; diff re-printed after the agent already wrote it |
| 7 | out: final report | 196 | step 5 'at most 4 lines'; ~200-370 tokens |
| 8 | out: mid-run text/plan | 11 |  |

Tool calls by kind (total over runs): file views (sed -n/cat ranges) 9, gate.sh run output 6, scripted-edit output 1

## Ranked sinks: tightloop-v4b (median per run; in+out+cache_read median 189821)

| rank | sink | tokens/run | which rule causes it |
|---|---|---|---|
| 1 | fixed prefix x calls | 180936 | number of API calls; SKILL.md bytes are appended to the system prompt, so they ride every call; v4 steps 1-5 are 4-5 separate calls (look, edit, gate, sometimes skeptic rerun, report); the 1984 B SKILL.md is ~550 tokens on every call (v3's 12053 B ~3.3k) |
| 2 | re-read: file views (sed -n/cat ranges) | 9890 | step 1 'sed -n the ranges around the hits' (no size cap) + re-looks; ranges of 100-140 lines (e.g. sed -n 80,215p = 6.3 KB) re-read by every later call |
| 3 | re-read: own earlier output | 2064 | tool inputs/edit payloads stay in context; python heredoc edit scripts carry old+new text |
| 4 | re-read: scripted-edit output | 994 | edit scripts that print diffs; echoing the diff after editing |
| 5 | out: tool inputs (commands, edit payloads) | 918 | step 2 edit style (python heredoc rewriting blocks) and long commands; edit scripts restate surrounding code |
| 6 | out: hidden thinking | 864 | deliberation per call; more calls = more thinking; not addressable by text directly; fewer decision points |
| 7 | re-read: gate.sh run output | 423 | step 3 gate prints test tails + the full diff; diff re-printed after the agent already wrote it |
| 8 | out: final report | 270 | step 5 'at most 4 lines'; ~200-370 tokens |
| 9 | out: mid-run text/plan | 22 |  |

Tool calls by kind (total over runs): file views (sed -n/cat ranges) 3, scripted-edit output 1, gate.sh run output 1

## Ranked sinks: no-skill (median per run; in+out+cache_read median 179852)

| rank | sink | tokens/run | which rule causes it |
|---|---|---|---|
| 1 | fixed prefix x calls | 176172 | number of API calls; SKILL.md bytes are appended to the system prompt, so they ride every call; v4 steps 1-5 are 4-5 separate calls (look, edit, gate, sometimes skeptic rerun, report); the 1984 B SKILL.md is ~550 tokens on every call (v3's 12053 B ~3.3k) |
| 2 | re-read: file views (sed -n/cat ranges) | 11027 | step 1 'sed -n the ranges around the hits' (no size cap) + re-looks; ranges of 100-140 lines (e.g. sed -n 80,215p = 6.3 KB) re-read by every later call |
| 3 | re-read: own earlier output | 2870 | tool inputs/edit payloads stay in context; python heredoc edit scripts carry old+new text |
| 4 | out: hidden thinking | 1384 | deliberation per call; more calls = more thinking; not addressable by text directly; fewer decision points |
| 5 | out: tool inputs (commands, edit payloads) | 999 | step 2 edit style (python heredoc rewriting blocks) and long commands; edit scripts restate surrounding code |
| 6 | re-read: test/build run output | 401 | no-skill/v3 run tests separately before/after; v4 folds it into the gate |
| 7 | out: final report | 369 | step 5 'at most 4 lines'; ~200-370 tokens |
| 8 | out: mid-run text/plan | 19 |  |

Tool calls by kind (total over runs): file views (sed -n/cat ranges) 27, test/build run output 14, scripted-edit output 3

## What this means for the 40% floor (arithmetic, not a measurement)

- in+out+cache_read is about API calls x the fixed prefix (no-skill prefix median 29368 tokens per call; the CLI system prompt and tool schemas are most of it and no skill text can remove them). Everything a skill controls inside a run (file views, gate output, edit payloads, report) is under 10% of it.
- So 40% of no-skill on in+out+cache_read needs roughly 40% of no-skill's calls. Per task no-skill's call count is in the rows (fd-01 ~6-9, gin-01 ~4, gin-02 ~5). A fix needs at least 3 calls (look, edit+gate, report), which is about 40% only where no-skill uses 7+ calls (fd-01). On gin-01/gin-02 the floor implies 1.6-2 calls, below what any proven fix can take; I expect it to stay missed there and will report it as missed, not explain it away.
- in+out is mostly output: hidden thinking (~45-55%), tool inputs/edit payloads, final report. 40% of no-skill in+out is ~1000-1300 tokens, so v4c has to cut calls (fewer decisions = less thinking), edit payloads and the report together.
- SKILL.md is appended to the system prompt, so its bytes ride every call: v4 1984 B (~550 tokens x calls), v4c 978 B.

## Rules removed or merged in v4c (benchmark/arms/tightloop-v4c/SKILL.md, 978 B; gate.sh and phases/ byte-identical to v4)

| v4 rule | sink it drives | v4c |
|---|---|---|
| steps 2 and 3 are separate calls (edit, then gate) | +1 call = +~30k cache_read | edits and the gate run in ONE Bash call |
| step 4 skeptic pass, then rerun the gate | the only extra gate run seen (fd-01 v4, comment-only change) | no rerun; the boundary/error check happens before writing the edit |
| step 1 sed -n ranges with no size cap | rank-2 sink (file views re-read every call) | ranged reads only, 20-40 lines, no whole-file reads, no cat |
| step 5 report in at most 4 lines | 200-370 output tokens | 3 lines, no tool calls after the gate |
| 'aim to finish in about 5' | 4-6 calls observed | 'finish in 3 calls' with the per-call cost stated |
| contract/plan/notes files | none observed in v4 (rule already 'no plan, notes or todo files') | kept as one short line |
| risky.md read before editing (a separate step) | never read so far (0 reads) | read inside call 1 when it applies, so it adds no call |

