# tightloop v6 (and v7, v8): criteria and the token-only PRE-SCREEN, fixed before any v6 text or run exists

Status: DESIGN ONLY. Written 2026-10-18 ~20:20Z (Oct 19 ~01:50 IST) for Naman (WhatsApp m:fbc372c1, m:f4cffa5e pt 4,
m:50e47aef). At this commit no v6 skill text, no v6 key, no v6 app spec and no v6 session exists. Nothing below changes after
the first v6 pre-screen session starts. v5's criteria and predictions (benchmark/design/tightloop-v5/DESIGN.md, eace66f + A1
0be26dc + A2 70b7958) are not touched by this file; the v5b thinking prediction stays as registered and is reported as a miss,
with its number, if it misses.

## 1. The measured fact v6 must use: thinking is ~8% of output, not 35-45%

Source: DESIGN.md (v5) section 4.8, A2 (70b7958): the result event field usage.output_tokens_details.thinking_tokens over the
9 round-1 builds is 1.0-14.9% of output tokens, **median 8.1%** (todo 46 / 139 / 143; notes 638 / 639 / 592; units 601 / 523 / 344).
The earlier 35-45% figure came from a retired estimator and is not used anywhere below.

Consequences, binding for every v6/v7/v8 candidate:
- C-T1. A rule whose stated purpose is less thinking may claim at most 8% of the incumbent's median output tokens as its saving
  (the ceiling if thinking went to zero). If the v5 run measures a different median share for the incumbent, that measured share
  replaces 8% (computed by the 4.8 method on the incumbent's scored v5 builds); the number is written into the candidate's
  addendum before its pre-screen.
- C-T2. Every candidate's predicted saving is split by bucket (input, output minus thinking, thinking, cache_read,
  cache_creation) and each bucket's claim cites a measured number (a harness log row, or this file). A claim without a source
  counts as zero.
- C-T3. Thinking is reported for every pre-screen and full-run session (4.8 field, cross-checked with modelUsage thinkingTokens;
  a mismatch = "unmeasured" for that session).

## 2. Who the incumbent is

The incumbent is "the current best": the tightloop version that most recently PASSED its own pre-registered full-run rule.
- After the v5 run: if v5 or v5b passes DESIGN.md (v5) section 4 (both pass: the one with the lower pooled median in+out), it is
  the incumbent. If neither passes, the incumbent stays tightloop-v4 (.claude/skills/tightloop, unchanged).
- A v6 candidate that passes the pre-screen AND its own full run becomes the incumbent for v7; one that fails either is logged
  FAILED with its numbers, and v7 builds from the unchanged incumbent (Naman m:fbc372c1). Same for v8.
- The incumbent's identity and SKILL.md sha256 are written into each candidate's addendum before its pre-screen.

## 3. The pre-screen (token-only, cheap, before any full app run)

- Arms: 2. The candidate and the incumbent. Nothing else.
- Apps: the three v5 apps (benchmark/blind/specs/v5/habits.md, recipes.md, pomodoro.md, sha256s in v5_INTEGRITY.md), as the
  prompt, unchanged. They are a fixed token workload here, not a quality test; every v6 full run uses fresh apps (section 5).
- Repeats: **3 per arm per app** = 18 measured sessions + 3 warm-ups (one no-skill "reply OK" per app, excluded from medians,
  counted in total cost). Order per app: incumbent, candidate, candidate, incumbent, incumbent, candidate (ABBAAB), so neither arm
  always runs first after the warm-up.
- Box: the same hardened sandbox and session settings as the v5 driver (benchmark/blind/v5_run/blind_driver_v5.py: sandbox_r2
  prefix, skill text via --append-system-prompt-file, fresh config per session, cap 600 s, one session at a time, nothing else
  running). No blind labels, no viewer, no judge.
- Numbers: **from harness logs only**: the claude CLI stream-json final result event of each session (usage, num_turns), parsed
  by runner.launch; never the agent's own report. Per session: input, output, cache_read, cache_creation, in+out,
  in+out+cache_read, cost-weighted (in + 5*out + 0.1*cache_read + 1.25*cache_creation), thinking (4.8), tool calls, wall.
- Primary metric: in+out (real tokens). in+out+cache_read and cost-weighted are reported beside it and never replace it.
- No reruns: a timed-out, crashed or expensive session stays as it is. Only an isolation void is rerun (as in v5).

### 3.1 Pass threshold (binding)

Let M(arm, app) = median in+out over its 3 sessions; r(app) = M(candidate, app) / M(incumbent, app);
R = median in+out of the candidate's 9 sessions / median of the incumbent's 9.

The candidate PASSES the pre-screen only if ALL of:
1. R <= 0.85 (at least 15% fewer real tokens, pooled), AND
2. r(app) <= 0.90 on at least 2 of the 3 apps, AND r(app) <= 1.00 on the third, AND
3. worst-run guard: the candidate's highest single-session in+out on each app <= 1.15 x the incumbent's highest on that app, AND
4. no candidate session timed out (600 s) or produced no index.html, AND
5. sanity floor (not a quality score): on each app, the candidate's median hidden-checker pass count >= the incumbent's median
   minus 2 (check_app_v5.py, run after each session; results logged, not tuned on).

Why 15%: pass-3 repeats of the same arm on the same task already differ by 7-27% in in+out (gin-01: no-skill 2,404 vs 2,241;
ponytail 1,692 vs 2,147; tightloop-v4a 1,765 vs 1,394; harness rows, pass 3 RUN_LOG). A margin under 15% is reported as
**"within noise"** and counts as a FAIL. Anything that fails 1-5 is logged FAILED with every number and the next version builds
from the unchanged incumbent. A pass sends the candidate to a full run (section 5); it is not itself a "better" verdict.

### 3.2 Prediction (written before any v6 text exists)

Base-rate prediction, 2026-10-18 ~20:20Z: **the first v6 candidate FAILS this pre-screen**: most likely on condition 1 (pooled
R between 0.85 and 1.00, "within noise"). Reason: the two one-rule variants measured side by side so far land inside each other's repeat
spread (pass 3, gin-01, in+out: tightloop-v4a 1,765 / 1,394; tightloop-v4b 1,602 / 1,817), and with thinking at ~8% of output
the remaining levers are output text and tool-call count, which one rule has not yet moved by 15%. This prediction is reported as hit or miss with R and the three r(app), and is never edited.
Each candidate's own addendum adds its specific predicted R and r(app) per app, with the bucket split of C-T2, committed before
its pre-screen.

## 4. What each candidate's addendum must contain (committed and pushed BEFORE its first pre-screen session)

- the candidate's folder and SKILL.md sha256; its measured skill size in tokens (A2 method, measure_skill_tokens.py);
- the incumbent's name and SKILL.md sha256;
- the predicted R and r(app) per app, the bucket split (C-T2), and the thinking claim bounded by C-T1;
- the exact driver command and the commit it runs from.

## 5. After a pass: the full run

Same shape as v5 (benchmark/design/tightloop-v5/DESIGN.md section 4 as amended): fresh apps not used in any earlier round, a new
sealed key made the round-2 v4 way, the same blind pack, criteria and prediction committed before any build. A version counts as
better only if it beats the incumbent on that committed rule; otherwise it is FAILED and the next builds from the incumbent.
