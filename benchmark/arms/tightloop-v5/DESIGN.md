# tightloop v5: design note, data, predictions, pre-registered test

Status: DESIGN ONLY. No agent session has run v5. Written 2026-10-18 for Naman's ask (WhatsApp m:81a05cc7): design, quality and functioning far better than no-skill, tokens and usage far below no-skill and ponytail. Binding rules from Naman m:c9c6e9cc are folded in (real-token targets, wall cap, quality checks, new apps, new sealed key, at most one screenshot, its cost counted).

Files: `SKILL.md` (2,994 bytes, the only text added to the system prompt), `look.py` (the browser self-check, run by the agent, never in the prompt), `gate.sh` and `phases/` (copied unchanged from v4c, used only for bug fixes). `.claude/skills` stays v4. v5 is not yet registered in `benchmark/runner.py`; that is a phase-2 step.

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

## 4. Pre-registered test (fixed before any v5 run; nothing below changes after the first build)

Arms: no-skill; ponytail (pinned 09c434ab); tightloop-v4 (`.claude/skills/tightloop` at the commit that holds this file); tightloop-v5 (this folder at the same commit). The v5 folder sha256s are recorded in the run's environment file; v5 is frozen from this commit.

Apps: 3 NEW specs, not round 1 (todo, notes, units) and not round 2 (bookmarks, expenses, kanban). They are written AFTER this commit, by a worker that has not read v5's files, in the round-2 template: feature paragraph, design instructions (layout, hex palette, type, spacing, states, responsive), file rules, checker ids and classes, native confirm() for destructive actions. Complexity at least round 2's. Specs committed (hash milestoned) before any build.

Checker: round 2's `check_app.py` method (one origin per build, no-store, served bytes = zip, console and page errors fail, every-button-changes-state, 375 px rule, confirm accept/dismiss), extended with each new app's feature checks. Self-tested before any build: a hand-written reference passes; a dead-handler, a no-confirm and an overflowing control each fail. Checker hash milestoned before any build, then frozen.

Key: a NEW seeded key. Letters A-D shuffled independently per (app, run) by `random.Random(seed)`, seed drawn from os.urandom and recorded only inside the key. sha256 of the key committed and milestoned before any build. Root and this worker never see the mapping before Naman's picks.

Runs: 2 per arm per app = 24 sessions. Same CLI version and model for all (logged). Fresh session each, skill delivered as `benchmark/runner.py` does (`--append-system-prompt` + skill folder). Arm order rotated (Latin square) per app and run. One session at a time, none overlapping a pass-3 or Kimo build (logged). Before each app block, one discarded warm-up session (no-skill, prompt "reply OK"), so no arm pays a cold system-prompt cache; any row whose first call still has cache_read 0 is flagged "cold" and reported. look.py's runs, its screenshot and its Read are inside v5's session and counted in v5's tokens and wall time; nothing is excluded.

Blind format: as round 2. One zip, one plain viewer, 4 panels per (app, run), letters shuffled, every build on its own port. Checker results and the cost file (tokens, tool calls, wall time per build) are never in the viewer. Naman ranks the 4 versions on each of the 6 pages (1 = best). Checker table shown only after the picks.

Metrics per build: in+out; in+out+cache_read; cost-weighted (headline); tool calls; turns; wall s; checker passed/total; console+page errors.
Spread per arm = the median over apps of (max - min across its 2 runs), per metric.

Pass criteria. v5 COUNTS only if every line holds:
- Q1 checker: on every app, v5's checks passed summed over its 2 runs >= no-skill's sum on that app.
- Q2 errors: console + page errors = 0 on all 6 v5 builds.
- Q3 blind rank: v5 ranked above no-skill on >= 5 of the 6 pages (a tie is not above), AND v5's mean rank is the best of the 4 arms.
- C1 vs no-skill, for EACH of cost-weighted, in+out, and in+out+cache_read: v5's median over its 6 builds <= 60% of no-skill's median.
- C2 vs ponytail, for EACH of the same 3 metrics: v5's median <= 85% of ponytail's median, AND (ponytail median - v5 median) > max(ponytail spread, v5 spread). Parity with ponytail (above 85%, or within the spread) is a FAIL.
- W wall time: no v5 build over 600 s (one over it counts as 0 checks and last rank on its page), and v5's median wall <= no-skill's median wall.
Reported, not gating: FLOOR (cost-weighted median <= 40% of no-skill; predicted not met); v5 vs v4 head-to-head on rank, checks and the 3 token metrics; every loss stated plainly. With n = 2 per cell and one judge, the result is a decision rule, not a statistical claim; no gain percentage is published beyond these rows.

Order (binding): round 2 zip delivered to Naman first (root steers); then specs hash, checker hash, key hash, each milestoned; then builds only when the Kimo hold file is gone and df >= 3000 MiB.
