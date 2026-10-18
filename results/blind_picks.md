# Blind app bake-off: Naman's picks and the reveal

Status: all picks in (2026-10-18, 23:20 to 23:27 IST). n = 1 build per arm per app, 3 apps, one judge: no significance or quality claim beyond Naman's own words. **See the caveat at the end: the way the builds were served may have shown Naman a cached copy of an earlier build, so these picks may not be valid.**

## Setup

- 3 small web apps, specs in `benchmark/blind/specs/` (todo, markdown notes, unit converter). The spec text is the whole prompt, identical for every arm. Commit 759f7c7.
- Arms: **no-skill**, **ponytail** (pinned 09c434ab), **tightloop-v4** (`.claude/skills/tightloop` at fd48849). No v4c existed in the repo when the builds started (17:15Z).
- One fresh `claude -p` session per build (Claude Code 2.1.302, same model), skill delivered exactly as `benchmark/runner.py` does it, sessions one at a time under `nice -n 15`. Order rotated per app. Every build was tagged `clean` (no pass-3 session overlapped).
- Blinding: labels A/B/C were shuffled per app with `random.Random(1412807045).sample(arms, 3)`. Stripped: `.claude/` skill folders (6 builds), one test file (`convert.test.js`, units/C, not loaded by the page) and a trailing 7-line `console.assert` self-check block (units/A, no UI effect). File dates were normalised.
- Sealed before Naman saw anything: KEY.json sha256 `2597e7e6401a598ad61f50183dbb4f9dc54685de8fa6d86ebca9e5b9cd851e5d` (commit 65f5453) and METRICS.json sha256 `6b61c4eb47d80b634632d4b17ea4935988d357bfc1f28d8c466daf2482d07572` (commit 2239f9e). Both are committed verbatim here as `results/blind_key.json` and `results/blind_metrics.json` and hash to those values.

## Naman's picks (verbatim, WhatsApp via Pally)

- todo, 23:20 IST (m:bac0e220): "Todo: A,B,C is 99.9% similar nothing better nothing worse". Recorded as a TIE.
- notes, 23:24 IST (m:43ab1a37): "markdown editor: A>B>C B was better visually but the help guide was worse than A and C had worse design and no guide". Recorded as A > B > C.
- units, 23:27 IST (m:4fc3b58f): "Unit converter: A>B>C A was better visually B was better than C as C did not even function.". Recorded as A > B > C.

## Key

| app | A | B | C |
|---|---|---|---|
| todo | ponytail | no-skill | tightloop-v4 |
| notes | no-skill | tightloop-v4 | ponytail |
| units | ponytail | no-skill | tightloop-v4 |

## Per build (cost-weighted is the headline)

cost-weighted = in + 5*out + 0.1*cache_read + 1.25*cache_creation. Hidden smoke = `benchmark/blind/checks/check_app.py` (todo 7, notes 5, units 10 checks). Basic = one scripted task per app on the served path.

| app | label | arm | Naman's place | **cost-weighted** | in+out | in+out+cache_read | in | out | cache_read | cache_creation | wall s | turns | tool calls | hidden smoke | basic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| todo | A | ponytail | tie (1st=) | **72835.3** | 3234 | 133512 | 10 | 3224 | 130278 | 34942 | 31.22 | 5 | 4 | 7/7 | PASS |
| todo | B | no-skill | tie (1st=) | **87340.75** | 4698 | 199303 | 14 | 4684 | 194605 | 35557 | 47.77 | 9 | 8 | 7/7 | PASS |
| todo | C | tightloop-v4 | tie (1st=) | **46076.1** | 3932 | 122163 | 8 | 3924 | 118231 | 11700 | 39.87 | 4 | 3 | 7/7 | PASS |
| notes | A | no-skill | 1st | **95598.6** | 8571 | 323102 | 18 | 8553 | 314531 | 17090 | 75.3 | 12 | 11 | 5/5 | PASS |
| notes | B | tightloop-v4 | 2nd | **66276.45** | 6533 | 162910 | 10 | 6523 | 156377 | 14411 | 59.52 | 5 | 4 | 5/5 | PASS |
| notes | C | ponytail | 3rd | **40789.8** | 4284 | 58592 | 4 | 4280 | 54308 | 11164 | 41.87 | 2 | 1 | 5/5 | PASS |
| units | A | ponytail | 1st | **43788.2** | 4173 | 91995 | 6 | 4167 | 87822 | 11332 | 37.05 | 3 | 2 | 10/10 | PASS |
| units | B | no-skill | 2nd | **55114.4** | 5736 | 122875 | 8 | 5728 | 117139 | 11802 | 52.08 | 4 | 3 | 10/10 | PASS |
| units | C | tightloop-v4 | 3rd | **46290.35** | 4271 | 122207 | 8 | 4263 | 117936 | 10539 | 37.71 | 4 | 3 | 10/10 | PASS |

## Per arm

| arm | todo | notes | units | cost-weighted (sum of 3) | in+out (sum) | in+out+cache_read (sum) | wall s (sum) | hidden smoke |
|---|---|---|---|---|---|---|---|---|
| no-skill | tie (1st=) | 1st | 2nd | 238053.75 | 19005 | 645280 | 175.1 | 22/22 |
| ponytail | tie (1st=) | 3rd | 1st | 157413.3 | 11691 | 284099 | 110.1 | 22/22 |
| tightloop-v4 | tie (1st=) | 2nd | 3rd | 158642.9 | 14736 | 407280 | 137.1 | 22/22 |

Losses, plainly (as judged): tightloop-v4 placed last on units (the build Naman said "did not even function") and 2nd on notes. Ponytail placed last on notes. No-skill placed 2nd on units and was the most expensive arm on every app. Todo: no arm won or lost.
Tokens: on cost-weighted, ponytail was cheapest on notes and units, and tightloop-v4 was cheapest on todo. No-skill was the most expensive on all three. Over the 3 apps, ponytail (157413.3) and tightloop-v4 (158642.9) are within 1% of each other, both about two thirds of no-skill (238053.75). n = 1 each, so no spread is measurable and no token gain is claimed from this study.

## units/C: "did not even function" vs. the scripted checks (investigated read-only, nothing rebuilt or rerun)

- The exact `units/C.zip` that was sent was unzipped into a fresh folder and served with the exact run line (`python3 -m http.server 8000`), then driven in headless Chrome by script. Results: every from/to pair in all 3 categories gave the correct value for 12.5 (Length 49, Weight 16, Temperature 9; 74/74). Swap worked (km/mi -> mi/km). "abc" and "1,5" showed "Invalid number — please enter a numeric value.", empty input showed "Please enter a value to convert.", and -40 / 1e3 / 0.1 converted. 0 console errors. The same held when `index.html` was opened directly as `file://`. units/A and units/B gave identical results (74/74, swap OK, clear messages, 0 errors, both over http and file://). With JavaScript disabled, all three show empty unit lists, so a no-JS preview cannot tell them apart either.
- So in a clean browser units/C works, and the checker was not too weak for this build: what it checks (3 conversions, empty input, swap) all work by hand too.
- **What can make C look broken: browser caching from my run instructions (my mistake).** All 9 builds were given the same run line on the same port (`localhost:8000`) and share file names (`index.html`, `app.js`, `style.css`). I also set every file date to the same time when blinding. Python's server sends no cache headers, so Chrome keeps the files from the first build it opened, and on revalidation the server answers 304 Not Modified, because the dates match. In a scripted session opening A, then B, then C on `localhost:8000` (one server at a time, the same browser), the server received **zero** requests for B and C, and the page still showed A. This happened in all 3 apps, both on a plain visit and on a normal reload. A mixed state (C's page with A's cached `app.js`) throws `Cannot set properties of null (setting 'textContent')` and shows wrong output.
- What this means: what Naman saw for B and C may have been a cached copy of an earlier build, or a mix of files. The todo verdict "A, B, C 99.9% similar" fits seeing the same build three times. The picks above are recorded as given, but they may not be valid judgements of the builds. A clean re-view needs no rebuild: serve each label on its own port (8001 / 8002 / 8003) or in a fresh private window, or open `index.html` directly. Whether to re-view is Naman's call.
- Evidence scripts: `benchmark/blind/checks/units_investigate.py` (by-hand drive, http + file:// + no-JS) and `benchmark/blind/checks/cache_sim.py` (sequential same-port session).

Files Naman judged: 1280x800 screenshots plus zips in Tab's files/tl_blind/<app>/ (not committed). Every screenshot was taken in a fresh browser on its own port, so the screenshots show the right build.

## Addendum (18:10Z, Pally m:1455239a): was units/C broken, and did the checker miss it?

Round 1 stays as sealed above. Nothing was rebuilt or rerun, and no round-1 number changed.

- Pally's guess was that the check loaded the page but never typed a value. That is not what happened. The round-1 `check_app.py` units checks were: the five elements exist (`select#category`, `select#from`, `select#to`, `input#value`, `#result`); then **"10 km -> 6.2137 mi"**, **"100 C -> 212 F"** and **"1 lb -> 0.4536 kg"** (each picks the category by label, selects from/to, fills `#value`, which fires `input`, and requires the number in `#result`); "empty input shows no NaN/undefined"; and "swap exchanges units". units/C passed all 10. A converter with dead handlers fails three of them (see `reference/units_dead` below).
- **(a) What is broken in units/C: nothing I can find in a clean browser.** There is no console error and no dead handler. `app.js` wires `input` on `#value`, `change` on all three selects, and `click` on `#swap` (app.js lines 34-43). Driven by hand, all 74 unit pairs are correct, both over http and over file://.
- **(b) The likely real cause is the delivery, not the code:** the same-port cache effect described above. One gap is real: the round-1 checker recorded console errors but did not fail on them.
- New harness steps (in `benchmark/blind/checks/check_app.py`, for the next round): (1) units: type a value by keyboard, fire `change` too, and require the result to CHANGE to the expected number (3 m -> 9.8425 ft); (2) every app: any console error or uncaught page error fails the build.
  Validation on the hand-written references in `benchmark/blind/checks/reference/`: todo 8/8, notes 6/6, units 12/12 (pass). Negative controls: `units_dead` (handlers never wired) 8/12, failing the 3 conversions and the new typed-change step; `todo_err` (uncaught error after load) 7/8, failing the new error step.
  On the round-1 units builds (read-only): A 12/12, B 12/12, **C 12/12**. **The new step does NOT fail units/C**, because units/C works in a clean browser. It would not have caught what Naman saw.
- Delivery fix for the next round (benchmark/blind/README.md): every label gets its own port (no two builds share an origin), file dates are not set equal, and the run line says to open a fresh private window.

## Re-judge after the cache finding (Pally m:14b11f24)

The round-1 picks above stay exactly as given. Naman re-judged one app in a private (incognito) window, so nothing was cached:

- units: **C ≈ B** (incognito, Naman, 11:42 PM IST Oct 18). His original verdict was A > B > C, with C "did not even function". In a clean window he finds C roughly equal to B.
- todo: not re-judged yet (Naman decides).
- notes: not re-judged yet (Naman decides).

Key, for reading the re-judge: units B = no-skill, units C = tightloop-v4.
