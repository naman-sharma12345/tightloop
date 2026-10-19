# v9 blind judge: rubric used

Written 2026-10-19T01:50:49Z (UTC), BEFORE opening the zip. The judge (task a9268fde) has verified only the sha256 of
/home/user/tab/files/tl_blind/v9/viewer.zip = d45c7a0374de730aabf99f214acf98f0ce6c38f433101fe30e6e807d51672b26
and has not copied, listed or opened it, nor any build, key, results or log file.

Scope: 21 labelled builds, bookmarks A-G, kanban A-G, expenses A-G. The judge does not know which version made which.
Rubric = tightloop commit b8d4711 benchmark/blind/r2_JUDGE_RUBRIC.md, unchanged, reproduced verbatim below (same as the v8 judge's RUBRIC.md).
Scoring only from a Playwright click-through of every feature at 1280x800 and 375 px (start screens are not evidence), one-line reason per label.
Ties share a rank (same practice as the v8 judge). This zip keeps any shipped test files: every test file present in each label's folder
(test.js, tests/, *.test.*, *.spec.*, spec files) is listed with its path and counted; an unused test file costs 1 point on Q3 (same as the v8 judge).

---

# Round 2 blind judge: rubric

Written 2026-10-18T21:03:00Z (UTC), written before opening the zip. The judge has not copied, listed or opened viewer.zip
or any build, key, results or log file at this time.

Scope: 3 apps (bookmarks, expenses, kanban) x 4 builds labelled A, B, C, D. Each build is scored out of 100
against its spec in benchmark/blind/specs/r2/<app>.md. Ranks 1-4 within each app by total score.
Tie-break: higher FUNCTION score wins; if still tied, higher DESIGN; if still tied, the builds share the rank.
Overall order: mean rank across the 3 apps (lower is better); tie on mean rank -> higher mean total score.

Method per build: Playwright (headless chromium) at 1280x800 and 375x812; screenshots looked at; every spec
feature clicked through (add, edit, delete with confirm accepted AND dismissed, filters, drag where asked,
reload persistence); console errors, page errors and external requests captured; source read.
Every rubric line gets a score and a one-line reason. No model is asked to judge the apps.

## FUNCTION: 40 points (all apps)

| line | pts | full marks when |
|---|---|---|
| F1 core create | 8 | adding works through the spec's ids; invalid input rejected with an inline message (bookmarks: non-http(s) URL; expenses: empty desc / non-positive / non-numeric amount; kanban: empty/whitespace title) |
| F2 edit + delete | 8 | edit saves correctly; delete removes; native confirm(): accept deletes, dismiss leaves it |
| F3 app-specific features | 12 | bookmarks: folders create/rename/delete (bookmarks move to Unsorted), search by title/URL/tag, tag-chip filter + clear, counter, export JSON + import merge skipping duplicates. expenses: month picker (default current), category filter, 3 summary cards (total in #total only, count, largest category), chart updates, 6-month chart/table, CSV export with the exact header. kanban: drag between and within columns with a drop indicator, add/rename column, detail modal (title, desc, due date, labels; close by button/Escape/backdrop; delete), labels and overdue shown, column counts, label filter |
| F4 persistence | 6 | everything survives a reload (localStorage) |
| F5 clean runtime | 6 | 0 console errors, 0 page errors, 0 external network requests; no dead buttons |

## DESIGN: 35 points (all apps)

| line | pts | full marks when |
|---|---|---|
| D1 layout | 10 | follows the spec's layout (bookmarks: 240 px left sidebar + top bar + 3-4 col card grid; expenses: header, 3 summary cards, 60/40 two columns; kanban: slim top bar, equal 280-320 px columns scrolling inside the board, centred 560 px modal over a dim backdrop) |
| D2 palette + type | 10 | the spec's exact colours (background, surfaces, text, muted, borders, single accent used only for primary/active/focus, category/label colours); system font stack; 24 px semibold title, 16 px headings, 14-15 px body; tabular numbers where they line up |
| D3 spacing + surfaces | 5 | 8 px scale, 12 px radius, 1 px border, soft shadow, controls 36-40 px tall |
| D4 states | 5 | visible hover and keyboard-focus styles; friendly empty states with a hint on every list/board area that can be empty |
| D5 polish | 5 | looks finished at 1280x800: alignment, hierarchy, nothing broken or crowded (judged from the screenshot) |

## QUALITY: 25 points (all apps)

| line | pts | full marks when |
|---|---|---|
| Q1 375 px | 10 | fully usable at 375 px: panels stack, no horizontal page scroll (except inside the kanban board), controls reachable, nothing clipped |
| Q2 accessibility basics | 8 | labelled inputs, real buttons/links, modal/dialog semantics, focusable controls, sensible headings, adequate contrast |
| Q3 code clarity / size sanity | 7 | readable structure, no dead or debug code, reasonable size for the scope, plain HTML/CSS/JS, relative paths, no build step/CDN |

## Deductions within a line

Partial credit is proportional to how much of the line works. A spec feature that is missing scores 0 on its share
of the line. A build that fails to load scores 0 on FUNCTION and is marked FAILED TO LOAD in the ranks.
