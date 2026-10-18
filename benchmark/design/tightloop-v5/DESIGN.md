# tightloop v5: design note, data, predictions, pre-registered test

Status: DESIGN ONLY. No agent session has run v5 or v5b. Written 2026-10-18 for Naman's ask (WhatsApp m:81a05cc7): design, quality and functioning far better than no-skill, tokens and usage far below no-skill and ponytail. Binding rules from Naman m:c9c6e9cc are folded in (real-token targets, wall cap, quality checks, new apps, new sealed key, at most one screenshot, its cost counted).

Files: `SKILL.md` (2,994 bytes, the only text added to the system prompt), `look.py` (the browser self-check, run by the agent, never in the prompt), `gate.sh` and `phases/` (copied unchanged from v4c, used only for bug fixes). `.claude/skills` stays v4. v5 is not yet registered in `benchmark/runner.py`; that is a phase-2 step.

AMENDED AGAIN by amendment A2 (section 6: C3 scope, measured skill sizes, the thinking measure, look.py two ways, warm-ups and reruns, runner copy check, the dated prediction; Naman m:ed447bea and m:fe05342f, written before any v5 key, spec or build exists). AMENDED (amendment A1, section 5, Naman m:eac698de and m:a6fa9fc9, written before any v5 key, spec or build exists): eace66f is the BASE; this file's sections 1-3 are kept as written there, section 4 below is the amended test plan (it replaces eace66f's section 4, which stays readable at eace66f), and section 5 lists every change. This file moved from `benchmark/arms/tightloop-v5/DESIGN.md` to `benchmark/design/tightloop-v5/DESIGN.md`, because `benchmark/runner.py` copies an arm's WHOLE folder into the agent's checkout: left in place, these predictions would sit in the v5 agent's workspace.

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

Fixed ceiling, binding: **Parity or worse than ponytail on real tokens = FAIL. No re-scoring after the numbers are in.** (A2: computed on scored builds only; warm-ups are excluded from it, see 4.10.) ("Real tokens" = in+out and in+out+cache_read, read from the API usage the runner records; cost-weighted is the headline but never replaces them.)

Arms (5): no-skill; ponytail (pinned 09c434ab); tightloop-v4 (`.claude/skills/tightloop` at the commit that holds this file); tightloop-v5 (`benchmark/arms/tightloop-v5/`); tightloop-v5b (`benchmark/arms/tightloop-v5b/`, pre-registered in this amendment, see 4.3). Both candidate folders are frozen from this commit; their file sha256s are listed in 4.2 and recorded again in the run's environment file. Phase 2 registers v5 and v5b in `benchmark/runner.py` ARMS (two new entries pointing at these folders; no other runner change). The environment file's `skill_folders` must then list exactly SKILL.md, look.py, gate.sh, phases/fail.md, phases/risky.md for each of v5 and v5b (no DESIGN.md, no notes); otherwise every v5/v5b row is INVALID.

Who gets look.py: only v5 and v5b. No-skill, ponytail and v4 get no browser tool (they may write their own checks inside their session, as round 1 showed, and that cost is in their rows). Labelled plainly: **only v5/v5b get a free verifier.** This is a confound: a quality gain of v5/v5b over no-skill cannot be split between the skill text and the tool the skill ships; what is tested is the whole package (text + tool) against no package. look.py's running time, its printed lines and (v5 only) the screenshot are inside v5/v5b's sessions and counted in their tokens and wall time. A2: the PASS/FAIL verdict uses these included numbers; a second, look.py-excluded number is reported only to size the confound (4.9).

Apps: 3 NEW specs, not round 1 (todo, notes, units) and not round 2 (bookmarks, expenses, kanban). Written AFTER this commit by a worker that has not read the v5/v5b files, in the round-2 template (feature paragraph, design instructions with hex palette, type, spacing, states, responsive; file rules; checker ids and classes; native confirm() for destructive actions). Complexity at least round 2's. Specs committed and their hash milestoned before any build.

Checker: round 2's `check_app.py` method (one origin per build, no-store, served bytes = zip, console and page errors fail, every-button-changes-state, 375 px rule, confirm accept/dismiss), extended with each new app's feature checks. Self-tested before any build (a hand-written reference passes; a dead-handler, a no-confirm and an overflowing control each fail). Checker hash milestoned before any build, then frozen. look.py shares no code with it (4.4).

Key: a NEW seeded key, sealed (sha256 committed and milestoned) before any build. Letters A-E shuffled independently per (app, run) by `random.Random(seed)`, seed from os.urandom, recorded only inside the key. Root and the building worker never see the mapping before Naman's picks.

Runs: **3 per arm per app** (A1 change 1). Fresh session each, same CLI version and model (logged), skill delivered as `benchmark/runner.py` does (`--append-system-prompt` with SKILL.md + the arm's folder at `.claude/skills/<name>/`). A block = one (app, run): one discarded warm-up session first (no-skill, prompt "reply OK", so no arm pays a cold system-prompt cache), then the 5 arms back to back in the order of row ((block index) mod 5) of a cyclic 5x5 Latin square, logged. Any row whose first call has cache_read 0 is flagged "cold" and reported. One session at a time, none overlapping a pass-3 or Kimo build (logged).

Session count and time: 5 arms x 3 apps x 3 runs = **45 measured sessions + 9 warm-ups = 54 sessions** (eace66f's plan: 4 x 3 x 2 = 24 + 3 warm-ups). Estimate: round-1 agent sessions took 31-75 s (median 42 s) on smaller apps; for round-2-size apps with look.py runs and fix rounds I assume ~90 s median per agent session plus ~45 s per build for checkout, install and checker, and ~15 s per warm-up: ~45 x 135 s + 9 x 15 s = ~1.75 h of box time, call it 1.5-2.5 h, plus waits for the Kimo hold and pass-3 gaps. Hard ceiling: 45 x 600 s = 7.5 h if every build hit the cap. The extra run costs ~1 h over the n=2 plan; that is the price of a real median.

Blind format: as round 2. One zip, one plain viewer, 5 panels per page, one page per (app, run) = 9 pages, letters shuffled per page, every build on its own port. Checker results and the cost file (tokens, tool calls, wall time per build) are never in the viewer. Naman ranks the 5 versions on each page (1 = best). The checker table is shown only after the picks.

Metrics per build: in+out; in+out+cache_read; cost-weighted (in + 5*out + 0.1*cache_read + 1.25*cache_creation, headline); tool calls; turns; wall s; checker passed/total; console+page errors; first-call context (input + cache_creation + cache_read of the first API call); thinking tokens, measured exactly as defined in 4.8 (A2: the section-1 estimator is retired; the transcripts record the real count); look.py-attributed tokens as defined in 4.9.

### 4.1 How n = 3 is treated (A1 change 1)

Decision: 3 runs per arm per app, not 2. Reason: with 2 runs the median is the mean of 2 and the spread is one difference, so one lucky or unlucky run sets both; with 3, the median is a real middle run and the spread spans 3 points. The cost is +21 measured sessions (~1 h), which is reasonable.

- Median per arm and metric = median over its 9 builds (3 apps x 3 runs).
- Spread per arm and metric = median over the 3 apps of (max - min across that app's 3 runs).
- On top of the medians, a worst-run guard (C3) so one bad run cannot hide behind two good ones.
- With n = 3 per cell and one judge this is still a decision rule, not a statistical claim; no gain percentage is published beyond these rows.

### 4.2 Skill size counts (A1 change 2)

The skill text is part of the measured tokens; nothing is subtracted anywhere. The runner passes the arm's SKILL.md with `--append-system-prompt`, so it is in the system prompt of EVERY API call of the session: written to the prompt cache once (cache_creation, x1.25 in cost-weighted) and re-read on every later call (cache_read). It therefore already sits inside input/cache_creation/cache_read of the usage the runner records, and inside all three token metrics. The other folder files (look.py, gate.sh, phases/) are not in the prompt; they cost tokens only through what the agent runs or reads (look.py's printed lines, a `cat`), and that is in the usage too.

How it is verified: per block, delta(arm) = the arm's first-call context minus no-skill's first-call context in the same block (same spec prompt, so the difference is the skill text plus its one-line skill listing). Already measured on round 1 (3 apps, first API call of each session, read from the stream-json transcripts): ponytail +1,292 / +1,294 / +1,292 tokens; v4 +761 / +759 / +761. In phase 2 the report lists delta per build; a v5 or v5b row whose delta is under half its A2 value below (skill not loaded) is INVALID and reported.

Skill size per arm (bytes measured now; tokens: "r1" = the round-1 first-call delta; "A2" = measured in amendment A2 with the token-counting endpoint, no session, method and reproduction check in 4.2.1; A1's "est." values (bytes / 2.65) are replaced):

| arm | in the system prompt on every call | bytes | approx tokens | whole installed folder (bytes) |
|---|---|---|---|---|
| no-skill | nothing | 0 | 0 | 0 |
| ponytail | `skills/ponytail/SKILL.md` @ 09c434ab (sha256 9badd22a32e1...a509) | 3,496 | 1,292-1,294 r1 (A2 method: 1,292 calibrated) | 3,496 (1 file) |
| tightloop-v4 | `.claude/skills/tightloop/SKILL.md` | 1,984 | 759-761 r1 (A2 method: 761 calibrated) | 7,463 (+ gate.sh 3,608, phases 1,871) |
| tightloop-v4c (reference only, not an arm here) | `benchmark/arms/tightloop-v4c/SKILL.md` | 978 | 433 A2 (calibrated; raw 424) | 6,457 |
| tightloop-v5 | `benchmark/arms/tightloop-v5/SKILL.md` (sha256 04e3ca1487f2...1d39, unchanged from eace66f) | 2,994 | **1,172 A2** (calibrated; raw 1,163) | 13,803 (+ look.py 5,330, gate.sh 3,608, phases 1,871) |
| tightloop-v5b | `benchmark/arms/tightloop-v5b/SKILL.md` (sha256 a451229802a1...9caf) | 3,161 | **1,216 A2** (calibrated; raw 1,207) | 13,847 (+ look.py 5,207, gate.sh 3,608, phases 1,871) |

look.py sha256: v5 c4d985a01ad0cb0e26fe44a5a2b6fd1c9d47b17129d79b56b05387a9069ae3d9; v5b 50fa7cf4f785020f16a4a179f2186e404b4c39cb4f34f736e72d314a2f44b958.

#### 4.2.1 How the A2 token sizes were measured (no session)

Method: the token-counting endpoint (`POST /v1/messages/count_tokens`, model claude-opus-5-5, the round-1 model), which runs no model and starts no session; no agent build, no 1-token call. Script: `benchmark/design/tightloop-v5/measure_skill_tokens.py` (reads the API address and key from the environment; neither is written anywhere); its output: `benchmark/design/tightloop-v5/skill_tokens_A2.json`. It rebuilds the two things the runner adds to an arm's first API call: (1) the SKILL.md text appended to the system prompt (`--append-system-prompt`, runner.py `launch()`), and (2) the arm's one entry in the CLI's skill listing ("The following skills are available for use with the Skill tool:", one line `- <name>: <description>` from the SKILL.md front matter, for the folder `install_skill()` writes under `.claude/skills/`). raw delta(arm) = count(base system + "\n\n" + SKILL.md, listing with the arm's entry) - count(base system, listing without it). Same base, same user message, for every arm; no-skill = 0 by construction.

Reproduction check against round 1 (first API call of each round-1 session, input + cache_creation + cache_read, minus no-skill's in the same app):

| arm | round-1 deltas (todo / notes / units) | A2 raw delta | offset (r1 - raw) |
|---|---|---|---|
| ponytail | 1,294 / 1,292 / 1,292 | 1,283 | +11 / +9 / +9 |
| tightloop-v4 | 759 / 761 / 761 | 752 | +7 / +9 / +9 |

Both references sit a constant ~9 tokens above the raw count (mean of the six offsets = 9.0, range 7-11), the same size for a 3.5 KB and a 2.0 KB skill, so it is a fixed per-skill overhead of the CLI's real listing/separator that the rebuild does not reproduce exactly, not a per-byte error. Calibrated value = raw + 9, which reproduces ponytail 1,292 and v4 761 (the r1 modal values) and is stated as +-2 from the r1 range. Results: **tightloop-v5 1,172 tokens (raw 1,163), tightloop-v5b 1,216 (raw 1,207)**, tightloop-v4c 433 (raw 424). A1's estimates were 1,130 and 1,190 (bytes / 2.65), 42 and 26 tokens low. The phase-2 per-build first-call delta (above) stays the authoritative check of what each session actually loaded.

What a skill costs per build, roughly: S tokens x (number of calls) in in+out+cache_read, and about 1.25*S + 0.1*S*(calls - 1) in cost-weighted when warm. For v5 (1,172 tokens, A2, ~4 calls): ~4.7k in+out+cache_read and ~1.8k cost-weighted; for ponytail (~1,290, ~2-4 calls): ~2.6-5.2k and ~1.7-2k. The final report prints this table again next to the token results.

### 4.3 v5b, pre-registered now (A1 change 3)

v5b = v5 with two changes and nothing else (diffs: SKILL.md +4/-3 lines, look.py screenshot lines removed):
1. NO SCREENSHOT. v5b's look.py is v5's look.py with the screenshot call and its path removed; it prints the same text (errors, first-load text, every control with its result, 375 px). SKILL.md step 3 says: judge the LOOK lines; there is no screenshot; never take, write or read one. This also removes v5's Read-the-image tool call.
2. LOWER THINKING, BY SKILL TEXT ONLY. The knob facts: the runner launches `claude -p ... --append-system-prompt <SKILL.md>` with the same inherited environment for every arm and passes no thinking or effort flag; the only things an arm controls are its SKILL.md text and the files copied to `.claude/skills/<name>/`, which the CLI does not read as settings. A thinking budget is a process environment or settings value, so setting it per arm needs a runner/harness edit, which is not allowed, and a result obtained that way would not be a skill result. So v5b's lower thinking is an INSTRUCTION in SKILL.md, not a hard cap: "Think briefly: at most 3 sentences of reasoning before each tool call and before the reply. The spec and these steps have already made the choices; do not weigh alternatives, re-plan or re-check in your head." No harness arm (e.g. "v5-harness-lowthink") is defined or run.
Whether the instruction bit is measured, not assumed: it counts as having bitten only by the rule in 4.8 (A2: exact thinking tokens from the result event, per-app medians, <= 60% of v5's on every app); otherwise the report says "the instruction did not cut thinking".
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
- C3 worst run (n = 3 guard; A2: applies to tightloop-v4, tightloop-v5 and tightloop-v5b ONLY. no-skill and ponytail are the reference arms whose medians are the bars, so the guard is never applied to them): for each of v4, v5 and v5b, on every app and for each of the 3 token metrics, the arm's highest of its 3 scored runs is below no-skill's median on that app AND below ponytail's median on that app. For v5 and v5b it is a pass line; v4 is a comparison arm with no verdict in this test, so its C3 result is computed by the same rule and reported, pass or fail. Warm-ups never enter C3 (4.10).
- W wall time: no build over 600 s (a build over it counts as 0 checks and last rank on its page), and the arm's median wall <= no-skill's median wall.
- Two candidates means two chances to pass; no correction is applied beyond each having to pass every line alone. If both pass, both are reported and the choice is Naman's. Nothing is promoted to `.claude/skills` without his word.
Reported, not gating: FLOOR (cost-weighted median <= 40% of no-skill; predicted not met by either); v5 and v5b vs v4 head-to-head; v5 vs v5b; the skill-size table; first-call deltas; thinking tokens (4.8); the look.py-excluded numbers (4.9, confound sizing only); every loss stated plainly. No re-scoring after the numbers are in.

### 4.6 Predictions for v5b (stated before any run; v5's stay as in section 3)

Bottom-up vs v5 on a round-2-size app, warm: no screenshot saves the image (~1.4k tokens, ~1.75k cw) and the Read call (~3-4k cw, finding 2), ~5k cw; if the thinking instruction halves thinking (~2-3k tokens in v5), ~1-1.5k fewer output tokens, ~5-7.5k cw. So v5b ~ v5 minus 8-12k cw, about 80-85% of v5's cost-weighted, with 1 fewer tool call (median 2-4).
- C1 cost-weighted: v5b ~37-50% of no-skill: predicted PASS. in+out (almost all output; on round 1 even v4 was 74-84% of no-skill's output): v5 ~75-100% of no-skill, v5b ~60-85%: predicted FAIL for both. in+out+cache_read: v5b ~50-70% of no-skill: borderline.
- C2 vs ponytail: cost-weighted v5b ~80-95% of ponytail, in+out ~100-130% (ponytail writes the least output): predicted FAIL for v5b, and FAIL for v5 (section 3). If this holds, neither candidate counts, and the report says so.
- Quality: Q1 and Q2 predicted PASS (look.py's text still shows errors, controls that do nothing and 375 px overflow). Blind: v5b ranks at or below v5 (no visual review), above no-skill on ~6-7 of 9 pages, so Q3 (>= 8 of 9) predicted FAIL for v5b; v5's Q3 borderline. Confidence: low to moderate; nothing backs these beyond round 1.
- Proven wrong if: v5b's median tool calls are not at least 1 below v5's; v5b's thinking (4.8) is not <= 60% of v5's on every app; or v5b's mean rank beats v5's (then the screenshot was not buying quality).

### 4.7 Order (binding)

Round 2 zip delivered to Naman first (root steers); then the new specs hash, the checker hash and the key hash, each milestoned; then builds only when the Kimo hold file is gone and df >= 3000 MiB.

### 4.8 How thinking is measured (A2, defined before any v5 or v5b session)

Source file: the raw stream-json stdout of each session, kept by `benchmark/runner.py` at `<out>/logs/<tag>.agent.stdout` (launch() -> run_logged() writes `log_path + ".stdout"`; any phase-2 driver that calls launch() keeps the same file). Event: the session's final event with `"type": "result"`.
Field: **`usage.output_tokens_details.thinking_tokens`** (integer), cross-checked against `modelUsage["claude-opus-5-5"].thinkingTokens` in the same event; the two must be equal (they are equal in all 9 round-1 builds), and a build where they differ is reported "thinking: field mismatch" and counts as unmeasured.
Why this field and not another: the result event's `usage` is the session total over all API calls, so T(build) = that value is already "summed per session" (if a session ever emits more than one result event, T = the sum over them). Per-call `assistant` events are NOT used: their `usage.output_tokens` is a streaming partial (round-1 units/v4: per-event 2, 16, 4, 7 against a session total of 4,263), and their `thinking` blocks carry only a signature and no text (block text length 0), so neither "output minus visible text" nor block lengths can measure thinking. Thinking tokens are already inside `output_tokens` (every round-1 row has thinking <= output), so nothing is added to or removed from the token metrics.
Formula: per arm per app, M(arm, app) = median of T over its 3 scored builds (warm-ups excluded). ratio(app) = M(v5b, app) / M(v5, app).
Rule: **the v5b thinking instruction "bit" iff ratio(app) <= 0.60 on EVERY one of the 3 apps.** The pooled ratio (median of v5b's 9 builds / median of v5's 9) is reported, not gating. If M(v5, app) = 0 on an app, that app reads "not testable" and the rule fails. If the field is absent in any v5 or v5b scored build, the result is "thinking: unmeasured" (no fallback to the retired estimator, no other field chosen afterwards).
Round-1 values of this field, for scale (n = 1 each): todo no-skill 46 / ponytail 139 / v4 143; notes 638 / 639 / 592; units 601 / 523 / 344; that is 1.0-14.9% of output (median 8.1%).

### 4.9 look.py tokens: reported two ways (A2, Naman m:fe05342f)

v5 and v5b pay for their look.py runs inside their own token counts. Every v5/v5b result is reported two ways: **(a) look.py tokens included** (the plain measured numbers, exactly as for every other arm) and **(b) look.py tokens excluded**. **The PASS/FAIL verdict (C1, C2, C3, the ceiling line, FLOOR) uses (a), the included number. (b) is reported only to size the confound** and never changes a verdict.
Identification, from the same `<tag>.agent.stdout` stream-json:
- L-calls = every `tool_use` block in an `assistant` event with `name == "Bash"` whose `input.command` contains `look.py`; plus, v5 only, every `tool_use` with `name == "Read"` whose `input.file_path` ends in `.png` (the screenshot read).
- L-results = every `tool_result` block (in `user` events) whose `tool_use_id` is an L-call's `id`.
- Token counts by the counting endpoint (same model, after the run, no session; method of 4.2.1): o = for a Bash L-call, the tokens of the look.py part of the command only (from `python3` through the end of that pipeline, e.g. `python3 .claude/skills/tightloop/look.py . 2>&1 | tail -40`; the heredoc app code written in the same call is the build, not look.py), for a screenshot Read the tokens of its whole `input`; r_j = the tokens of L-result j's content (text; an image block counted from the block if the transcript holds it, else from the PNG at the path look.py printed, else width x height / 750); k_j = the number of API calls (distinct `assistant` `message.id`) whose first event comes after L-result j.
- Attributed to look.py: out_L = sum of o; cc_L = sum of r_j (each result enters the context once, as cache creation); cr_L = sum of r_j x k_j (re-read as cache on every later call).
- Excluded numbers: in+out(b) = in+out(a) - out_L; in+out+cache_read(b) = in+out+cache_read(a) - out_L - cr_L; cost-weighted(b) = cost-weighted(a) - 5*out_L - 1.25*cc_L - 0.1*cr_L.
- Bounds, stated: the whole tool_result of a Bash call that runs look.py is attributed to look.py, even if other commands in that call printed lines (upper side); the agent's thinking and text about the look.py output and any fix-round calls it triggered are NOT attributed (lower side). Wall time is not split. No-skill, ponytail and v4 have no look.py, so for them (a) = (b).

### 4.10 Warm-ups and reruns (A2, Naman m:fe05342f)

Warm-ups: the 9 warm-up sessions (one per block, no-skill, prompt "reply OK") sit outside the 45 scored sessions. **Warm-ups are EXCLUDED from every median, from the spreads, from the worst-run guard C3 and from the ceiling line. Their tokens still COUNT toward the total cost reported** (the report prints the 45 scored sessions, the 9 warm-ups, and the sum of both).
Reruns: **a failed or bad scored build is NOT rerun and is never replaced** (a crash, a timeout over 600 s, a checker failure, a cold cache, a high token count: all stay as they are and are scored by the rules above). **The only allowed rerun is a build VOIDED by an isolation hit**: a checker / key / repo-path hit in its transcript, or a sandbox probe hit before the session. The voided run is kept in the log, marked `void`, with the reason (the hit, the pattern and where it was found); its rerun takes the same (app, run, arm) slot in the same Latin-square position. A void is decided by those mechanical hits only, never by the result.

### 4.11 What the runner copies into an agent's workspace (A2, Naman m:ed447bea pt 5)

`benchmark/runner.py` at the commit that holds this file. The arm paths (lines 17-27; the three comment lines inside the dict omitted here):
```
ARMS = {
    "no-skill": None,
    "ponytail": None,  # pinned upstream SKILL.md, loaded by ponytail_skill()
    "tightloop-v3": os.path.join(ROOT, "arms", "tightloop-v3"),
    "tightloop-v4": os.path.join(ROOT, "..", ".claude", "skills", "tightloop"),
    "tightloop-v4a": os.path.join(ROOT, "arms", "tightloop-v4a"),
    "tightloop-v4b": os.path.join(ROOT, "arms", "tightloop-v4b"),
}
```
The copy code, `skill_folder()` (lines 166-185; docstring omitted), the only place an arm's files are collected:
```
    if arm == "no-skill":
        return {}
    if arm == "ponytail":
        return {".claude/skills/ponytail/SKILL.md": (ponytail_text.encode(), 0o644)}
    src = os.path.normpath(ARMS[arm])
    files = {}
    for dp, _, fns in os.walk(src):
        for fn in sorted(fns):
            if fn.endswith(".pyc"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, src).replace(os.sep, "/")
            with open(p, "rb") as fh:
                files[".claude/skills/tightloop/" + rel] = (fh.read(), os.stat(p).st_mode & 0o777)
    return files
```
`install_skill()` (lines 211-230) writes exactly those files into the fresh checkout and git-excludes them; `launch()` (lines 279-284) adds `--append-system-prompt <SKILL.md text>`; `prepare()` gives an app task an empty `git init` folder. The only other copy into the workspace is in `grade()` (`apps/<name>/tests/`), which runs AFTER the session ends. So what a session can see is exactly:
- no-skill: nothing.
- ponytail: one file, `.claude/skills/ponytail/SKILL.md` = the pinned upstream text from the cache (sha256 9badd22a32e1...a509), 3,496 B. `benchmark/arms/ponytail.md`, `ponytail.sh` and `no-skill.sh` are top-level provenance/install notes, not inside any copied folder (ponytail.md is read only as a labelled fallback if the pinned file cannot be fetched; it was not used in round 1).
- tightloop-v4 (`.claude/skills/tightloop/`): SKILL.md 1,984 B, gate.sh 3,608 B, phases/fail.md 970 B, phases/risky.md 901 B. Nothing else.
- tightloop-v5, once phase 2 adds `"tightloop-v5": os.path.join(ROOT, "arms", "tightloop-v5")` (`benchmark/arms/tightloop-v5/`): SKILL.md 2,994, gate.sh 3,608, look.py 5,330, phases/fail.md 970, phases/risky.md 901.
- tightloop-v5b, likewise (`benchmark/arms/tightloop-v5b/`): SKILL.md 3,161, gate.sh 3,608, look.py 5,207, phases/fail.md 970, phases/risky.md 901.
`benchmark/design/` (this file, the measurement script and its JSON) and `benchmark/blind/` (round-2 specs, checker, references, integrity file) are not an ARMS path and not under any ARMS path, so `skill_folder()` never reads them. A grep of every copied folder above (v4, v5, v5b) for predict, criteria, DESIGN.md, blind, ponytail, no-skill, KEY.json and check_app finds 0 lines; ponytail's single file is the pinned upstream text. No arm folder holds predictions, criteria, design docs, keys or checker code; look.py exists only in v5 and v5b, as their declared tool. Phase 2 re-checks this from the environment file's `skill_folders` listing before the first build.
Round-2 integrity file, linked for reference (round 2 is frozen; this amendment does not touch `benchmark/blind/`): `benchmark/blind/r2_INTEGRITY.md` as committed in e90af43fabc91e6fd17d5f7bcb281f1eeb4cc21c, blob sha256 443f108320f38443c7e1ad06442b5860758ebe02acd5a2b2d10ec5360a7eea0f (any later version of that file is in its own commit).

### 4.12 Dated prediction, standalone (A2, Naman m:ed447bea pt 6)

**PREDICTION, committed before any v5 or v5b session, key, spec or build exists: tightloop-v5 and tightloop-v5b both FAIL against ponytail on in+out (criterion C2 and the ceiling line): neither arm's in+out median comes out at or below 85% of ponytail's with a gap larger than the spreads.**
(From section 3 and 4.6: v5 ~110-140% of ponytail on cost-weighted on small apps; v5b in+out ~100-130% of ponytail.)

## 5. Amendment A1 (this commit, on top of eace66f; no v5 key, spec or build existed when it was written)

Requested by Naman on WhatsApp, m:eac698de (12:11 AM IST Oct 19) and m:a6fa9fc9 (12:15 AM IST Oct 19). Changes against eace66f:
1. n: 2 -> 3 runs per arm per app (4.1), with the C3 worst-run guard; Q3 threshold >= 8 of 9 pages (eace66f: >= 5 of 6); sessions 24 + 3 warm-ups -> 45 + 9 warm-ups.
2. Skill size: skill text counted in the measured tokens, how it is verified, and the size table (4.2).
3. v5b arm pre-registered (4.3, 4.6): `benchmark/arms/tightloop-v5b/`; thinking lowered by SKILL.md text only (an instruction, not a cap); no screenshot. 5 arms, 5 panels, letters A-E.
4. look.py made generic only, with the removals and grep evidence in 4.4 (v5's look.py changed; v5's SKILL.md is byte-identical to eace66f). "Only v5/v5b get a free verifier" stated as a confound.
5. The fixed ceiling line at the top of section 4.
6. This file moved out of the arm folder (see the note under Files).
eace66f is not amended, rebased or force-pushed; this is a new fast-forward commit.

## 6. Amendment A2 (on top of A1 and e90af43; no v5 key, spec, app or build existed when it was written; 0 sessions run for it)

Requested by Naman on WhatsApp, m:ed447bea (12:25 AM IST Oct 19) and m:fe05342f (12:27 AM IST Oct 19). Changes against A1 (0be26dc):
1. C3 (4.5) now applies to tightloop-v4, v5 and v5b only; no-skill and ponytail are the bars, never guarded. v4's C3 is reported, v5/v5b's gates.
2. Skill sizes (4.2, 4.2.1): v5 and v5b measured with the token-counting endpoint, no session (v5 1,172, v5b 1,216, v4c 433), validated by reproducing ponytail and v4's round-1 first-call deltas to a constant +9 offset; A1's "est." numbers replaced.
3. Thinking (4.8): the exact field `usage.output_tokens_details.thinking_tokens` of the result event, per session; per-app medians; the bite rule <= 60% of v5's on every app; missing field = unmeasured. The section-1 estimator is retired.
4. look.py tokens reported two ways (4.9): verdict on (a) included; (b) excluded only sizes the confound; identification and formula fixed.
5. Warm-ups and reruns (4.10): warm-ups out of medians, spreads, C3 and the ceiling, but in the reported total; no rerun or replacement of a failed or bad build; only an isolation VOID is rerun, kept in the log as void with its reason.
6. Runner copy code quoted and every arm's workspace files listed (4.11): benchmark/design/ and benchmark/blind/ are outside every copied folder; no arm folder holds predictions, criteria or design docs. r2_INTEGRITY.md linked with its committed sha.
7. The prediction "v5 and v5b FAIL vs ponytail on in+out" as a standalone dated line (4.12).

Disclosure, found while defining 4.8 (round-1 data only; no v5 data exists): section 1's finding that thinking is "an estimated 35-45% of output" is wrong. The exact field shows 46-639 thinking tokens per round-1 session, 1.0-14.9% of output (median 8.1%): e.g. v4 todo 143 (section 1 estimated ~1,436), no-skill notes 638 (estimated ~3,707). Why the estimator (output minus visible characters / 3.6) overcounted is not established here; the exact field replaces it. Sections 1-3 and 4.6 are NOT edited: their predictions stay pre-registered as written and are scored as written. What this means, stated now so it is dated before any run: thinking is a small bucket, so v5b's thinking instruction can save at most a few hundred output tokens per build (4.6 assumed 1-1.5k), the "next lever: cut thinking" in section 3 is much smaller than claimed, and v5b's predicted savings over v5 would come mostly from dropping the screenshot and its Read call.
