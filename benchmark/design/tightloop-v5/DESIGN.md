# tightloop v5: design note, data, predictions, pre-registered test

Status: DESIGN ONLY. No agent session has run v5 or v5b. Written 2026-10-18 for Naman's ask (WhatsApp m:81a05cc7): design, quality and functioning far better than no-skill, tokens and usage far below no-skill and ponytail. Binding rules from Naman m:c9c6e9cc are folded in (real-token targets, wall cap, quality checks, new apps, new sealed key, at most one screenshot, its cost counted).

Files: `SKILL.md` (2,994 bytes, the only text added to the system prompt), `look.py` (the browser self-check, run by the agent, never in the prompt), `gate.sh` and `phases/` (copied unchanged from v4c, used only for bug fixes). `.claude/skills` stays v4. v5 is not yet registered in `benchmark/runner.py`; that is a phase-2 step.

AMENDED (amendment A1, section 5, Naman m:eac698de and m:a6fa9fc9, written before any v5 key, spec or build exists): eace66f is the BASE; this file's sections 1-3 are kept as written there, section 4 below is the amended test plan (it replaces eace66f's section 4, which stays readable at eace66f), and section 5 lists every change. This file moved from `benchmark/arms/tightloop-v5/DESIGN.md` to `benchmark/design/tightloop-v5/DESIGN.md`, because `benchmark/runner.py` copies an arm's WHOLE folder into the agent's checkout: left in place, these predictions would sit in the v5 agent's workspace.

## 1. Diagnosis (round 1 blind builds, 9 sessions, read from their stream-json transcripts)

Source: `blind_rows.jsonl` and the 9 `*.agent.stdout` transcripts of round 1 (todo, notes, units x no-skill, ponytail, v4). n = 1 per cell, so these are observations, not effects.

Where cost-weighted tokens go (cw = in + 5*out + 0.1*cache_read + 1.25*cache_creation):

| app | arm | cw | 5*out | 0.1*cache_read | 1.25*cache_creation | tool calls |
|---|---|---|---|---|---|---|
| todo | no-skill | 87,341 | 23,420 | 19,460 | 44,446 | 8 |
| todo | ponytail | 72,835 | 16,120 | 13,028 | 43,678 | 4 |
| todo | v4 | 46,076 | 19,620 | 11,823 | 14,625 | 3 |
| notes | no-skill | 95,599 | 42,765 | 31,453 | 21,362 | 11 |
| notes | ponytail | 40,790 | 21,400 | 5,431 | 13,955 | 1 |
| notes | v4 | 66,276 | 32,615 | 15,638 | 18,014 | 4 |
| units | no-skill | 55,114 | 28,640 | 11,714 | 14,752 | 3 |
| units | ponytail | 43,788 | 20,835 | 8,782 | 14,165 | 2 |
| units | v4 | 46,290 | 21,315 | 11,794 | 13,174 | 3 |

Findings:
1. Output is the biggest bucket: 27-52% of cw in every row. Of output, an estimated 35-45% is thinking (output tokens minus visible characters/3.6: v4 todo ~1,436 of 3,924; no-skill notes ~3,707 of 8,553). The app code itself is 2.0-4.8k tokens. The final reply is 936-2,085 characters (~260-580 tokens, ~1.3-2.9k cw).
2. Every tool call costs ~3-4k cw before it does anything: it re-reads ~30-40k cached tokens at 0.1, and its new content is cached at 1.25. No-skill notes made 11 calls (31.5k of cw in cache reads alone).
3. Cold cache, not the arm: todo no-skill and todo ponytail started with cache_read 0 and cache_creation ~29-31k on the first call (the system prompt was not cached yet). That is ~27k cw each that no rule could save. Round 1's todo ranking on cost is mostly this.
4. v4's rules are written for bug fixes (rg/sed, a test that fails without the fix, gate.sh). On an empty folder none of them applies; what remained was "few calls". All 3 v4 builds spent call 1 on probing an empty folder (`ls -la && ls .claude/skills/tightloop; which node`).
5. Why v4 quality was only on par: v4 says nothing about design, states or checking the UI. The task brief said v4 "never opens the app in a browser"; the transcripts show the skill text never asks for it, but the agent did screenshot on its own in 2 of 3 builds (todo, notes) and only curled the files in units. So the check happened by chance, with an ad-hoc script each time (~1-1.5k characters of test code written per build), and nothing told the agent what to look for.
6. No round-1 quality signal is clean: Naman's picks were likely made on cached files (see blind_picks.md; units C ~ B in incognito). What his words do say: picks turned on visual polish ("better visually") and on in-app guidance ("the help guide").
7. A real defect the round-1 checker did not catch: notes/A (no-skill) overflows at 375 px (scrollWidth 393), found by look.py below.

What a quality skill needs for UI work, and what cuts tokens:
- quality: a design pass from the brief before typing (layout, palette as CSS variables, spacing scale, type, every state), one real-browser self-check that is the same every time (console and page errors, every control used once with its result, 375 px overflow, one screenshot), and a small capped fix loop with targeted edits;
- tokens: no probe call, all files in one call together with the check, no hand-written test scripts, no whole-file rewrites, a 3-line reply, compact code, no skeptic re-read (v4 step 4 is gone; v4c already dropped it).

## 2. The rules, the data behind each, predicted effect, and what would prove it wrong

| # | rule (SKILL.md) | data behind it | predicted effect | proven wrong if |
|---|---|---|---|---|
| R1 | Design first, briefly, from the brief; decide, don't deliberate; spec ids verbatim | picks turned on visual polish and guidance (finding 6); thinking is 35-45% of output (finding 1) | quality up (states, spacing, guidance); thinking flat or down | v5's estimated thinking share > no-skill's, or v5 ranks below no-skill on design |
| R2 | No probe; write every file AND run look.py in ONE Bash call | v4 wasted call 1 on probing in 3/3 builds (finding 4); each call ~3-4k cw (finding 2) | -1 call, ~-3.5k cw per build vs v4 | v5's median tool calls >= v4's |
| R3 | Write each file once, whole and final; compact code; no debug output, no restating comments | no-skill notes re-patched app.js after writing it (finding 1); code is 2-5k output tokens | output tokens per feature down ~10-20% vs no-skill | v5's output tokens >= no-skill's median on an app |
| R4 | look.py: errors, every control used once with its result, dead-control retry, reload state, 375 px overflow, exactly ONE screenshot (1280x800 after use), ~15-30 text lines | finding 5 (no systematic check); finding 7 (overflow missed); Naman m:c9c6e9cc (text list + at most one screenshot) | catches dead controls, console errors and overflow before the reply; costs ~1.4k image tokens (~1.75k cw) + ~0.4k text + ~4-5 s per run, all counted in v5's rows | a v5 build ships with a console error, a dead control or 375 px overflow that look.py would have printed |
| R5 | Read the one screenshot once, as a strict reviewer, with a named list of what to look for | finding 5 | visual defects fixed in round 1 of the loop | the fix round changes nothing visible in >= half the builds |
| R6 | Fix loop: targeted edits + look.py rerun in ONE call; max 2 rounds; never read the screenshot again | finding 2 (calls dominate) | 3-5 tool calls per build (no-skill r1: 3-11) | any v5 build > 6 tool calls |
| R7 | Reply in at most 3 lines | replies were 936-2,085 characters (finding 1) | -1.3 to -2.5k cw per build | v5's reply > 400 characters in any build |
| R8 | Bug-fix mode = v4c unchanged (3 calls, gate.sh) | v4c is the token-cut variant already on main | none on apps; keeps v5 a drop-in skill | (not tested by this pre-registration; bug fixes are measured by pass 3) |

look.py validation (on copies of round-1 builds, no agent session, 3.6-5.0 s per run):
- units/C (v4, works in a clean browser): LOOK OK, 0 errors, 5 controls used, all "changed", 0 dead.
- the same build with the #swap listener broken on purpose: LOOK ISSUES, `click #swap -> no change`, 1 dead.
- todo/A: 7 controls; filter buttons All/Active print "no change" because they were already in that state (correct no-ops; the agent judges these, the tool only reports).
- notes/A (no-skill): `375px: scrollWidth 393 OVERFLOW`, a real defect the round-1 checker did not test.
Known limits: it does not drag (kanban moves are not exercised), it fills inputs with generic values, and "no change" can be a correct no-op. Its checks come from promises every spec makes (no errors, working controls, phone width), not from any checker's code.

## 3. Predicted numbers (stated before any run)

Bottom-up estimate for a round-1-size app, warm cache: ~3-4 tool calls, cache reads ~12-14k cw, cache creation ~15-17k cw (including the one image), output ~5-6k tokens (~25-30k cw). Total ~52-62k cw.

- vs no-skill (warm, round-1 size: 55-96k cw): v5 at ~60-75%. On round-2-size apps no-skill made more calls in round 1 as apps grew (notes: 11), so I predict v5 at ~45-60% there.
- vs ponytail (round 1 warm: 40.8k and 43.8k cw): v5 at ~110-140% on small apps. Ponytail writes the least code and does no browser check; v5 adds the check and more CSS. My prediction is that v5 does NOT meet "clearly under ponytail" on small apps, and is about even on round-2-size apps.
- The standing floor (<= 40% of no-skill, cost-weighted): predicted NOT met.
- Quality: v5 > no-skill on design in a clear majority of blind rankings; checker passes >= no-skill; 0 console errors. Confidence: moderate. Nothing yet backs it beyond the round-1 observations above.

If the cost targets fail as predicted, the next levers, in order of expected size: (1) cut thinking (largest unmanaged bucket, 35-45% of output); (2) drop the screenshot and keep the text check (~-2-3k cw, at a quality risk); (3) a shared CSS base shipped in the skill folder and copied by the agent, so design tokens are not re-typed each build (cuts output but changes what "the agent built" means, so it needs Naman's OK first).

## 4. Pre-registered test (as amended by A1; fixed before any v5 or v5b run; nothing below changes after the first build)

Fixed ceiling, binding: **Parity or worse than ponytail on real tokens = FAIL. No re-scoring after the numbers are in.** ("Real tokens" = in+out and in+out+cache_read, read from the API usage the runner records; cost-weighted is the headline but never replaces them.)

Arms (5): no-skill; ponytail (pinned 09c434ab); tightloop-v4 (`.claude/skills/tightloop` at the commit that holds this file); tightloop-v5 (`benchmark/arms/tightloop-v5/`); tightloop-v5b (`benchmark/arms/tightloop-v5b/`, pre-registered in this amendment, see 4.3). Both candidate folders are frozen from this commit; their file sha256s are listed in 4.2 and recorded again in the run's environment file. Phase 2 registers v5 and v5b in `benchmark/runner.py` ARMS (two new entries pointing at these folders; no other runner change). The environment file's `skill_folders` must then list exactly SKILL.md, look.py, gate.sh, phases/fail.md, phases/risky.md for each of v5 and v5b (no DESIGN.md, no notes); otherwise every v5/v5b row is INVALID.

Who gets look.py: only v5 and v5b. No-skill, ponytail and v4 get no browser tool (they may write their own checks inside their session, as round 1 showed, and that cost is in their rows). Labelled plainly: **only v5/v5b get a free verifier.** This is a confound: a quality gain of v5/v5b over no-skill cannot be split between the skill text and the tool the skill ships; what is tested is the whole package (text + tool) against no package. look.py's running time, its printed lines and (v5 only) the screenshot are inside v5/v5b's sessions and counted in their tokens and wall time; nothing is excluded.

Apps: 3 NEW specs, not round 1 (todo, notes, units) and not round 2 (bookmarks, expenses, kanban). Written AFTER this commit by a worker that has not read the v5/v5b files, in the round-2 template (feature paragraph, design instructions with hex palette, type, spacing, states, responsive; file rules; checker ids and classes; native confirm() for destructive actions). Complexity at least round 2's. Specs committed and their hash milestoned before any build.

Checker: round 2's `check_app.py` method (one origin per build, no-store, served bytes = zip, console and page errors fail, every-button-changes-state, 375 px rule, confirm accept/dismiss), extended with each new app's feature checks. Self-tested before any build (a hand-written reference passes; a dead-handler, a no-confirm and an overflowing control each fail). Checker hash milestoned before any build, then frozen. look.py shares no code with it (4.4).

Key: a NEW seeded key, sealed (sha256 committed and milestoned) before any build. Letters A-E shuffled independently per (app, run) by `random.Random(seed)`, seed from os.urandom, recorded only inside the key. Root and the building worker never see the mapping before Naman's picks.

Runs: **3 per arm per app** (A1 change 1). Fresh session each, same CLI version and model (logged), skill delivered as `benchmark/runner.py` does (`--append-system-prompt` with SKILL.md + the arm's folder at `.claude/skills/<name>/`). A block = one (app, run): one discarded warm-up session first (no-skill, prompt "reply OK", so no arm pays a cold system-prompt cache), then the 5 arms back to back in the order of row ((block index) mod 5) of a cyclic 5x5 Latin square, logged. Any row whose first call has cache_read 0 is flagged "cold" and reported. One session at a time, none overlapping a pass-3 or Kimo build (logged).

Session count and time: 5 arms x 3 apps x 3 runs = **45 measured sessions + 9 warm-ups = 54 sessions** (eace66f's plan: 4 x 3 x 2 = 24 + 3 warm-ups). Estimate: round-1 agent sessions took 31-75 s (median 42 s) on smaller apps; for round-2-size apps with look.py runs and fix rounds I assume ~90 s median per agent session plus ~45 s per build for checkout, install and checker, and ~15 s per warm-up: ~45 x 135 s + 9 x 15 s = ~1.75 h of box time, call it 1.5-2.5 h, plus waits for the Kimo hold and pass-3 gaps. Hard ceiling: 45 x 600 s = 7.5 h if every build hit the cap. The extra run costs ~1 h over the n=2 plan; that is the price of a real median.

Blind format: as round 2. One zip, one plain viewer, 5 panels per page, one page per (app, run) = 9 pages, letters shuffled per page, every build on its own port. Checker results and the cost file (tokens, tool calls, wall time per build) are never in the viewer. Naman ranks the 5 versions on each page (1 = best). The checker table is shown only after the picks.

Metrics per build: in+out; in+out+cache_read; cost-weighted (in + 5*out + 0.1*cache_read + 1.25*cache_creation, headline); tool calls; turns; wall s; checker passed/total; console+page errors; first-call context (input + cache_creation + cache_read of the first API call); estimated thinking tokens (output tokens minus visible characters/3.6, the section-1 estimator; the transcripts carry thinking blocks with no text, so this stays an estimate).

### 4.1 How n = 3 is treated (A1 change 1)

Decision: 3 runs per arm per app, not 2. Reason: with 2 runs the median is the mean of 2 and the spread is one difference, so one lucky or unlucky run sets both; with 3, the median is a real middle run and the spread spans 3 points. The cost is +21 measured sessions (~1 h), which is reasonable.

- Median per arm and metric = median over its 9 builds (3 apps x 3 runs).
- Spread per arm and metric = median over the 3 apps of (max - min across that app's 3 runs).
- On top of the medians, a worst-run guard (C3) so one bad run cannot hide behind two good ones.
- With n = 3 per cell and one judge this is still a decision rule, not a statistical claim; no gain percentage is published beyond these rows.

### 4.2 Skill size counts (A1 change 2)

The skill text is part of the measured tokens; nothing is subtracted anywhere. The runner passes the arm's SKILL.md with `--append-system-prompt`, so it is in the system prompt of EVERY API call of the session: written to the prompt cache once (cache_creation, x1.25 in cost-weighted) and re-read on every later call (cache_read). It therefore already sits inside input/cache_creation/cache_read of the usage the runner records, and inside all three token metrics. The other folder files (look.py, gate.sh, phases/) are not in the prompt; they cost tokens only through what the agent runs or reads (look.py's printed lines, a `cat`), and that is in the usage too.

How it is verified: per block, delta(arm) = the arm's first-call context minus no-skill's first-call context in the same block (same spec prompt, so the difference is the skill text plus its one-line skill listing). Already measured on round 1 (3 apps, first API call of each session, read from the stream-json transcripts): ponytail +1,292 / +1,294 / +1,292 tokens; v4 +761 / +759 / +761. In phase 2 the report lists delta per build; a v5 or v5b row whose delta is under half its estimate below (skill not loaded) is INVALID and reported.

Skill size per arm (bytes measured now; tokens: "measured" = the round-1 first-call delta; "est." = bytes / 2.65, the mean bytes-per-token of the two measured skills (ponytail 2.71, v4 2.61), checked in phase 2 by the delta):

| arm | in the system prompt on every call | bytes | approx tokens | whole installed folder (bytes) |
|---|---|---|---|---|
| no-skill | nothing | 0 | 0 | 0 |
| ponytail | `skills/ponytail/SKILL.md` @ 09c434ab (sha256 9badd22a32e1...a509) | 3,496 | ~1,290 measured | 3,496 (1 file) |
| tightloop-v4 | `.claude/skills/tightloop/SKILL.md` | 1,984 | ~760 measured | 7,463 (+ gate.sh 3,608, phases 1,871) |
| tightloop-v4c (reference only, not an arm here) | `benchmark/arms/tightloop-v4c/SKILL.md` | 978 | ~370 est. | 6,457 |
| tightloop-v5 | `benchmark/arms/tightloop-v5/SKILL.md` (sha256 04e3ca1487f2...1d39, unchanged from eace66f) | 2,994 | ~1,130 est. | 13,803 (+ look.py 5,330, gate.sh 3,608, phases 1,871) |
| tightloop-v5b | `benchmark/arms/tightloop-v5b/SKILL.md` (sha256 a451229802a1...9caf) | 3,161 | ~1,190 est. | 13,847 (+ look.py 5,207, gate.sh 3,608, phases 1,871) |

look.py sha256: v5 c4d985a01ad0cb0e26fe44a5a2b6fd1c9d47b17129d79b56b05387a9069ae3d9; v5b 50fa7cf4f785020f16a4a179f2186e404b4c39cb4f34f736e72d314a2f44b958.

What a skill costs per build, roughly: S tokens x (number of calls) in in+out+cache_read, and about 1.25*S + 0.1*S*(calls - 1) in cost-weighted when warm. For v5 (~1,130 tokens, ~4 calls): ~4.5k in+out+cache_read and ~1.8k cost-weighted; for ponytail (~1,290, ~2-4 calls): ~2.6-5.2k and ~1.7-2k. The final report prints this table again next to the token results.

### 4.3 v5b, pre-registered now (A1 change 3)

v5b = v5 with two changes and nothing else (diffs: SKILL.md +4/-3 lines, look.py screenshot lines removed):
1. NO SCREENSHOT. v5b's look.py is v5's look.py with the screenshot call and its path removed; it prints the same text (errors, first-load text, every control with its result, 375 px). SKILL.md step 3 says: judge the LOOK lines; there is no screenshot; never take, write or read one. This also removes v5's Read-the-image tool call.
2. LOWER THINKING, BY SKILL TEXT ONLY. The knob facts: the runner launches `claude -p ... --append-system-prompt <SKILL.md>` with the same inherited environment for every arm and passes no thinking or effort flag; the only things an arm controls are its SKILL.md text and the files copied to `.claude/skills/<name>/`, which the CLI does not read as settings. A thinking budget is a process environment or settings value, so setting it per arm needs a runner/harness edit, which is not allowed, and a result obtained that way would not be a skill result. So v5b's lower thinking is an INSTRUCTION in SKILL.md, not a hard cap: "Think briefly: at most 3 sentences of reasoning before each tool call and before the reply. The spec and these steps have already made the choices; do not weigh alternatives, re-plan or re-check in your head." No harness arm (e.g. "v5-harness-lowthink") is defined or run.
Whether the instruction bit is measured, not assumed: it counts as having bitten if v5b's median estimated thinking tokens <= 60% of v5's; otherwise the report says "the instruction did not cut thinking".
Confound: both changes land in one arm (Naman's ask: one run tests both), so v5b's result cannot be split between the two levers; the v5 vs v5b head-to-head is reported, not attributed.

### 4.4 look.py independence from the scoring checker (Naman m:a6fa9fc9)

look.py keeps generic checks only: console and page errors; every visible control used once with its result ("changed" / "no change", confirm() auto-accepted so destructive buttons can act); horizontal overflow at 375 px; plus a readout of the first-load text and (v5 only) one screenshot. Removed in this commit from eace66f's look.py, because they were derived from or overlapped the round-2 checker's logic, or were not on the generic list:
- the dead-control retry (refill empty text inputs, click again, then count it "dead"): the same rule as the round-2 checker's "second chance 1" in `buttons_all_act()` (d43574b), so removed with the "dead" tally;
- the reload-persistence check: the checker scores "survives reload" per app;
- the off-host request listener: near-identical to the checker's `pg.on("request", ...)` line, and not on the generic list.
The LOOK OK/ISSUES verdict now rests on errors and 375 px overflow only; "no change" controls are listed for the agent to judge.
Evidence (grep of `benchmark/blind/checks/check_app.py` at ba3cef6 against both look.py files, this commit): look.py imports functools, hashlib, http.server, os, sys, threading and playwright.sync_api; it imports nothing from the repo and check_app.py imports nothing from look.py. Function names: look.py defines state, label, end_headers, log_message; check_app.py defines ck, keep, bytes_match, seed, snap, label_of, buttons_all_act and per-app helpers; shared function names: 0. Identical lines of 20+ characters: only `#!/usr/bin/env python3` and `from playwright.sync_api import sync_playwright`. The one shared string fragment is Playwright's own console-listener idiom (`on("console", lambda m: m.type == "error" ...)`), with different bodies. Neither file mentions the other.

### 4.5 Pass criteria (each of v5 and v5b judged alone; every line must hold)

- Q1 checker: on every app, the arm's checks passed summed over its 3 runs >= no-skill's sum on that app.
- Q2 errors: console + page errors = 0 on all 9 of the arm's builds.
- Q3 blind rank: ranked above no-skill on >= 8 of the 9 pages (a tie is not above), AND the arm's mean rank is better than each of no-skill's, ponytail's and v4's. (The sibling candidate is left out of this line so v5 and v5b do not block each other; their head-to-head is reported.)
- C1 vs no-skill, for EACH of cost-weighted, in+out, in+out+cache_read: the arm's median <= 60% of no-skill's median.
- C2 vs ponytail, for EACH of the same 3 metrics: the arm's median <= 85% of ponytail's median, AND (ponytail median - arm median) > max(ponytail spread, arm spread). Parity or worse than ponytail on real tokens = FAIL.
- C3 worst run (n = 3 guard): on every app and for each of the 3 metrics, the arm's highest of its 3 runs is below no-skill's median on that app AND below ponytail's median on that app.
- W wall time: no build over 600 s (a build over it counts as 0 checks and last rank on its page), and the arm's median wall <= no-skill's median wall.
- Two candidates means two chances to pass; no correction is applied beyond each having to pass every line alone. If both pass, both are reported and the choice is Naman's. Nothing is promoted to `.claude/skills` without his word.
Reported, not gating: FLOOR (cost-weighted median <= 40% of no-skill; predicted not met by either); v5 and v5b vs v4 head-to-head; v5 vs v5b; the skill-size table; first-call deltas; estimated thinking; every loss stated plainly. No re-scoring after the numbers are in.

### 4.6 Predictions for v5b (stated before any run; v5's stay as in section 3)

Bottom-up vs v5 on a round-2-size app, warm: no screenshot saves the image (~1.4k tokens, ~1.75k cw) and the Read call (~3-4k cw, finding 2), ~5k cw; if the thinking instruction halves thinking (~2-3k tokens in v5), ~1-1.5k fewer output tokens, ~5-7.5k cw. So v5b ~ v5 minus 8-12k cw, about 80-85% of v5's cost-weighted, with 1 fewer tool call (median 2-4).
- C1 cost-weighted: v5b ~37-50% of no-skill: predicted PASS. in+out (almost all output; on round 1 even v4 was 74-84% of no-skill's output): v5 ~75-100% of no-skill, v5b ~60-85%: predicted FAIL for both. in+out+cache_read: v5b ~50-70% of no-skill: borderline.
- C2 vs ponytail: cost-weighted v5b ~80-95% of ponytail, in+out ~100-130% (ponytail writes the least output): predicted FAIL for v5b, and FAIL for v5 (section 3). If this holds, neither candidate counts, and the report says so.
- Quality: Q1 and Q2 predicted PASS (look.py's text still shows errors, controls that do nothing and 375 px overflow). Blind: v5b ranks at or below v5 (no visual review), above no-skill on ~6-7 of 9 pages, so Q3 (>= 8 of 9) predicted FAIL for v5b; v5's Q3 borderline. Confidence: low to moderate; nothing backs these beyond round 1.
- Proven wrong if: v5b's median tool calls are not at least 1 below v5's; v5b's estimated thinking is not <= 60% of v5's; or v5b's mean rank beats v5's (then the screenshot was not buying quality).

### 4.7 Order (binding)

Round 2 zip delivered to Naman first (root steers); then the new specs hash, the checker hash and the key hash, each milestoned; then builds only when the Kimo hold file is gone and df >= 3000 MiB.

## 5. Amendment A1 (this commit, on top of eace66f; no v5 key, spec or build existed when it was written)

Requested by Naman on WhatsApp, m:eac698de (12:11 AM IST Oct 19) and m:a6fa9fc9 (12:15 AM IST Oct 19). Changes against eace66f:
1. n: 2 -> 3 runs per arm per app (4.1), with the C3 worst-run guard; Q3 threshold >= 8 of 9 pages (eace66f: >= 5 of 6); sessions 24 + 3 warm-ups -> 45 + 9 warm-ups.
2. Skill size: skill text counted in the measured tokens, how it is verified, and the size table (4.2).
3. v5b arm pre-registered (4.3, 4.6): `benchmark/arms/tightloop-v5b/`; thinking lowered by SKILL.md text only (an instruction, not a cap); no screenshot. 5 arms, 5 panels, letters A-E.
4. look.py made generic only, with the removals and grep evidence in 4.4 (v5's look.py changed; v5's SKILL.md is byte-identical to eace66f). "Only v5/v5b get a free verifier" stated as a confound.
5. The fixed ceiling line at the top of section 4.
6. This file moved out of the arm folder (see the note under Files).
eace66f is not amended, rebased or force-pushed; this is a new fast-forward commit.
