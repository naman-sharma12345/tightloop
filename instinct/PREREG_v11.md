# tightloop v11 pre-registration (written 2026-10-19T07:50:41Z, before any v11 build or run)

Owner: Naman (WhatsApp m:0371119f 1:03 PM IST, plus binding steers m:b5a24969 1:06, m:037936c8 1:11, m:b6bb09d4 1:13).
Branch v6/v11, from d826d5b (the v10 prereg commit). Nothing here is registered in runner.py and nothing has run.

PLAIN STATEMENT: v11 is a MULTI-CHANGE rewrite. It breaks the one-change-per-version rule, at Naman's request.
Every change is listed in section 2 so a loss can be traced back to it.

## 0. Base and bar
- Base and bar: tightloop-v4c (benchmark/arms/tightloop-v4c, the 3-call skill, 433 tokens).
- Bug-fix data used (step 1 of v10, 75 transcripts in tl_instinct_out/*/logs): every model call re-reads ~30-38k tokens,
  so cost ~= calls x 32k; 26% of v4c tuning tokens (510,197 of 1,934,531) went to gate fails whose reason was hidden.
- v10 (gate stops printing the diff) on tokio-02: v4c 5/5/6 calls, v10 4/4/4; the saved call came from the reason
  being visible. v10's SECOND gate in all 3 tokio-02 runs printed GATE FAIL while cargo said "10 passed; 0 failed":
  cause found (section 2, B2). v10 was not kept (11/12 passes vs v4c 12/12).
- App round (r2, n=1 per arm per app): no-skill 99/100/100, v4c 97/99/97 at 44/69/47% of no-skill cost-weighted.
  v5c, v6c, v7, v9 tied on quality (judge 96-100) and cost more tokens than v4c: their extra checks were extra calls.
  v4c's r2 point losses were all write-time items: text/emoji icons, fewer aria labels, dense one-line CSS.

## 1. Arm files (benchmark/arms/tightloop-v11/), installed by the runner at .claude/skills/tightloop/
- SKILL.md: one skill, two modes (bug fix, app). Measured size 297 tokens (raw delta 288 + 9 calibration), the same
  method that gives v4c 433 (raw 424 + 9): token-counting endpoint only, no model run
  (benchmark/design/tightloop-v11/measure_skill_tokens_v11.py, output skill_tokens_v11.json). Hard cap 300: met.
- gate.sh: the bug-fix gate (section 2B).
- agents/scout.md, agents/skeptic.md, AGENTS.md: see section 2C.
- phases/: removed (fail.md is replaced by the gate's last line; risky.md is dropped to fit the 300-token cap).

## 2. What changed vs v4c, and why

A. SKILL.md (433 -> 297 tokens)
 A1. Shorter text, both modes in one file. Why: the skill text rides on every call; v4c paid +433 per call
     (call-1 context v4c minus no-skill: 431-437 on all 6 tasks). Hard cap 300 (Naman).
 A2. Bug-fix steps kept from v4c, compressed: rg + sed 20-40 lines + nearest test; heredoc edits; root-cause fix and a test
     that fails without it; check empty, boundary and error inputs; gate; 3-line reply.
 A3. Dropped from v4c to fit the cap: the risky.md pointer (concurrency/security/data/public API), "No more tool calls",
     "no comments that restate code". Risk: a risky task loses its extra checklist. Said plainly.
 A4. "On GATE FAIL read fail.md" -> "fix what its last line names, rerun once". Why: v10 finding above (the extra call
     was cat fail.md plus a rerun, just to see the reason).
 A5. App mode, new: one write step (heredoc each file once, then `node --check` the JS, in the same call), then the reply.
     Four write-time rules aimed at the r2 point losses: SVG icons not emoji, aria-labels, empty-state hints,
     inline errors. No browser step, no review step, no extra call (the v5c/v6c/v7/v9 lesson).

B. gate.sh (bug fix)
 B1. Kept from v10: no diff is printed.
 B2. FIX of the hidden v4c/v10 fail: NOTESTS contained the unanchored pattern "0 passed; 0 failed", which also matches
     "10 passed; 0 failed". The gate then printed "TEST FAIL (exit 0)" followed by 30 lines of passing test output, so a
     `| tail -25` showed only the passing lines and GATE FAIL. Now anchored: (^|[^0-9])0 passed; 0 failed.
 B3. Verdict and reason on the LAST line ("GATE FAIL: <reason>" / "GATE PASS (<diff size>)"), output self-capped
     (~15 lines on a fail, 3-5 on a pass), so any tail the model adds keeps the reason.
 B4. Order: test WITH the change first, then prove WITHOUT. Why: in v4c/v10 "prove ok" printed when the command itself
     was broken (exit 127 "command not found" on fd-01; the cargo error on tokio-02), because a broken command also fails
     without the change. 0 skill tokens, can only remove calls.
 B5. A bare test name as the command (fd-01 r1 passed "test_and_pattern_with_forward_slash") or exit 127 gets a plain
     reason on the last line. 0 skill tokens, can only remove calls.
 B6. Format: gofmt / cargo fmt are run on the changed files and reported, instead of failing (v4c failed and cost a call;
     fd-01 had one). cargo fmt runs only if every unformatted file is one the model changed; otherwise FORMAT fails as
     before. 0 skill tokens, can only remove calls. Naman may veto (steer m:b6bb09d4 lists auto-format as drop-unless-0/0).
 B7. Test-only and config-only exemption (Naman m:037936c8 pt 3). The gate needs a test that fails without the change
     only when a CODE file changed. Detection, from git (changed + untracked files):
     - code file = extension in go rs py js jsx ts tsx mjs cjs java kt c h cc cpp hpp rb php swift cs scala sh,
       and not a test path; test path = *_test.go, *_test.py, test_*.py, any tests/ or test/ dir, *.test.* / *.spec.* js/ts.
     - test-only: no code file changed and a test file changed (or a test function added) -> "prove skipped: test-only
       change", can pass.
     - config/docs-only: no code file changed -> "prove skipped: no code file changed"; if the model lists config files
       they are reverted and tried, and a test that also passes without them is reported "not proven", not failed.
     - a separate "no test added" FAIL was drafted and then removed: it can only fire when an EXISTING test already proves
       the fix, which would force a redundant test and an extra call. The prove step already fails a code change that
       has no failing-without test (PROVE FAIL / PROVE UNKNOWN).
 B8. Files: test files listed by the model are never reverted; with no files listed, the changed code files from git
     are used. 0 skill tokens.
 B9. Debug leftovers: listed as "debug?" lines, not a failure (same as v4c).
 Dry check (no model, no go, no cargo; a throwaway python git repo plus simulated go/cargo outputs): 23 cases, each gave
 the expected verdict on its last line, including the "10 passed; 0 failed" case (now GATE PASS) and an interrupted-run
 restore.

C. Agents
 What "agents" is in this repo: .claude/agents/scout.md, .claude/agents/skeptic.md and AGENTS.md at the repo root.
 None reaches a benchmark run: the runner installs only the arm folder (at .claude/skills/tightloop/) and passes SKILL.md
 by --append-system-prompt; Codex gets AGENTS.md written from SKILL.md; every arm since v4c says "no subagents".
 v11 ships rewritten, shorter copies inside the arm folder (agents/scout.md 10-line map, read-only; agents/skeptic.md
 blind diff review in at most 2 tool calls, 8-line reply; AGENTS.md = SKILL.md body for Codex). They are inert in the
 benchmark (Claude Code loads subagents from .claude/agents/, not from the skill folder), so they change no measured
 number. Loading them would be a harness change and needs Naman's word. The repo-root files are not touched.

## 3. App round: new specs, rubric, judge (committed before any build)
 Specs (benchmark/blind/specs/r11/), harder than r2 on purpose: open design brief (no palette or layout given, so design
 can differ), and harder function (undo, keyboard paths, exact money math, date/time-zone edges, import validation,
 conflict detection, settle-up math, print/ICS export).
 - habits.md  sha256 cff54483ed0314d5b6dcd9d7fd0d8a3b15eb08465451352475bce863de5b608d
 - invoice.md sha256 7b6d1ac8ecdba5de250ddcabd1c7d31ea5bbc5569a466637331687a4ed37331b
 - trip.md    sha256 4158176e37737a6bcb14d219383c25e479d3a22aafd3ad3fc997269adb2b395d

 RUBRIC: 5 axes, 0-10 each, one-line reason per axis, per build.
 - DESIGN (0-10): a coherent visual system: palette, type scale, spacing, hierarchy, icons, layout fit for the task.
   10 = a product designer would ship it unchanged; 5 = clean but generic template look; 0 = unstyled or broken layout.
 - LOOK (0-10): what the screenshots show at 1280x800 and 375 px: alignment, density, contrast, empty and error states,
   no overflow. 10 = flawless at both sizes; 5 = fine on desktop, rough at 375 px or in empty/error states; 0 = broken.
 - FUNCTION (0-10): every spec feature clicked through in a real browser (start screens are not evidence), including
   bad input, delete with confirm accepted AND dismissed, keyboard paths, undo, import of a bad file, reload persistence.
   Score = 10 x features working / features in the spec, rounded down, minus 1 per console or page error (floor 0).
 - POLISH AND EDGE CASES (0-10): the spec's edge rules (dates, rounding, duplicates, empty, corrupt storage, conflicts),
   focus handling, toasts and saved states, reduced motion. 10 = every edge rule right; 5 = half; 0 = none.
 - CODE QUALITY (0-10): readable structure, no dead code or debug output, no duplicated logic, sensible size, no
   network requests. 10 = a reviewer approves as is; 5 = works but messy; 0 = unreadable.
 Build score = mean of the 5 axes. App score per arm = mean over its n=3 builds.

 JUDGE PROTOCOL: a separate blind judge worker; the rubric is fixed by this commit; the judge sees only shuffled labels
 (arm order shuffled per app, new sealed key), the same judge prompt and model for every arm, scores from click-through
 evidence, and commits its ranks file (with sha256) before any reveal. n=3 builds per arm per spec.

 CALIBRATION RULE (Naman m:037936c8, m:b6bb09d4):
 - Calibrate the specs on NO-SKILL ONLY (n=3 per spec) before v11 builds anything. Never tune a spec after seeing any
   v11 output.
 - No-skill must land 4-6 (app score, per spec). If a spec lands above 7, it is too easy: tighten it BEFORE v11 ever
   runs, then re-calibrate. After the no-skill baseline is seen, NO spec commit is allowed except under this tighten
   rule. If a spec lands in (6, 7] or below 4, root reports it and asks Naman before v11 runs.
 - PASS LINE ("halve the points lost"): if no-skill scores S, v11 needs at least S + (10 - S) / 2 (S = 6 -> 8).
   It holds only if S is 4-6. My reading, flagged for Naman: applied per spec, on the app score above.
 - Tokens: v11 at fewer tokens than no-skill on the same spec (steer m:b5a24969).

## 4. Predictions (written before any run)
 Bug fix (4 tuning tasks, n=3, same frozen harness): pass >= v4c's 12/12 minus task-title noise; median calls and tokens
 lower than v4c where v4c hit hidden gate fails (fd-01, tokio-02), tie on gin-01/gin-02 (already 3-4 calls); per call
 ~136 fewer skill tokens. gin-04-style tasks (3-call floor) stay a tie with no-skill. Risk named: dropping risky.md.
 App (r11 specs): tokens at or below r2 v4c's share of no-skill (44-69%), because the mode is still one write call.
 Quality: I predict v11 beats no-skill on LOOK and CODE QUALITY (icons, labels, states) and ties on FUNCTION; whether it
 clears the halve-the-points-lost line depends on DESIGN, which the skill barely steers. Honest odds: below even.

## 5. Keep rule
 TBD by Naman: quality measure. Proposed for his word: app side = the pass line in section 3 on at least 2 of 3 specs at
 fewer tokens than no-skill; bug-fix side = passes >= v4c and median tokens and cw below v4c on at least 3 of 4 tuning
 tasks, no task worse by separate ranges.

## 6. Not done (waits for root's GO)
 No runner.py registration, no ORDER file, no app driver for r11 specs, no calibration run, no build, no run.
