# v6c blind ranks

Written 2026-10-18T23:24:43Z (UTC) by the blind judge (task bc73217b). Rubric: tightloop b8d4711 r2_JUDGE_RUBRIC.md unchanged (RUBRIC_USED.md, committed f2ff3f8 before the zip was opened). Zip sha256 1730d050ede737a6e0746b1bff52a568f6c1822b1630430a3292969bcd524d4a. Labels only; the judge read no key, results, token or log file.

Method: Playwright Chromium, 1280x800 and 375x812, every feature clicked on every label (add + invalid input, edit, delete with confirm dismissed AND accepted, search/filters, folders/columns, export/import, reload, Escape/backdrop, drag), console/page errors and external requests captured (0 / 0 / 0 on all 15), focus styles read after Tab, every visible button clicked in a sweep, screenshots kept in the judge task dir. Ties share a rank.


## bookmarks

| rank | label | score | reason |
|---|---|---|---|
| 1 | B | 100 | Full click-through pass: invalid URL rejected inline, add 2, search, tag-chip filter + Clear all, edit via form, delete confirm dismissed then accepted, folder Work created/renamed/deleted (bookmark moved to Unsorted), export JSON, import added 1 skipped 1 duplicate, reload kept 3; focus rings on buttons and the new-folder input; 0 errors; 375 stacks with no horizontal scroll. |
| 1 | C | 100 | Same full pass (invalid URL message, add/search/tag filter+clear, edit, delete both ways, folder create/rename/delete->Unsorted, export, import 1+1 dup, reload); focus ring on new-folder input; controls 36-38 px; 0 errors; 375 clean. |
| 1 | D | 100 | Same full pass on every feature; focus ring visible on the new-folder input; 0 errors; 375 clean. |
| 4 | A | 99 | Full pass on every feature (incl. folder rename/delete->Unsorted, import 1 added 1 dup, reload); the new-folder input shows no focus ring when tabbed (outline none, no shadow) (D4 -1); 0 errors; 375 clean. |
| 4 | E | 99 | Full pass on every feature (invalid URL inline message, edit, delete both ways, folders, export/import, reload); new-folder input has no focus ring when tabbed (D4 -1); largest source of the five (26 KB); 0 errors; 375 clean. |

## expenses

| rank | label | score | reason |
|---|---|---|---|
| 1 | D | 100 | Full pass: empty/negative/non-numeric/zero amounts each rejected inline, 3 added, #total 842.50 number only, 3 cards, category chart + 6-month trend, category filter, month switch to Sept shows empty-state text and 0.00, edit saved, delete dismissed then accepted, CSV header date,description,category,amount, reload kept rows; focus ring on desc and month inputs; 0 errors; 375 clean. |
| 2 | A | 99 | Full pass on every feature (validation x4, cards, charts, filter, month picker -> empty state, edit, delete both ways, CSV header exact, reload); desc and month inputs show no focus ring when tabbed (D4 -1); 0 errors; 375 clean. |
| 2 | C | 99 | Full pass (amount is a number input so non-numeric is blocked by the field; zero/negative/empty rejected inline; cards, charts, filter, month -> empty state, edit, delete both ways, CSV exact, reload); row Edit/Delete buttons 32 px (D3 -1); 0 errors; 375 clean. |
| 2 | E | 99 | Full pass on every feature incl. month-switch empty state and CSV header; focus rings visible; ships an unused test.js (node assert script) in the build, dead code (Q3 -1); 0 errors; 375 clean. |
| 5 | B | 98 | Full pass (validation x4, cards, charts, 6-month table with working month links, filter, month -> empty state, edit, delete both ways, CSV exact, reload); desc and month inputs show no focus ring (D4 -1); ships an unused test.js in the build (Q3 -1); 0 errors; 375 clean. |

## kanban

| rank | label | score | reason |
|---|---|---|---|
| 1 | A | 99 | Full pass: Enter + button add, blank rejected, 560 px modal over dim backdrop with title/desc/due/labels, Bug chip + red overdue, close by button/Escape/backdrop, delete dismissed then accepted, drag to In progress + reorder, Bug filter shows 1 (0/2 counts), add column, inline rename persists after reload, column delete cancel/accept, reload; focus rings visible; column icon buttons 32 px (D3 -1); 0 errors; 375 modal fits (343 px). |
| 1 | D | 99 | Same full pass (add, modal, labels, overdue red, close x3, delete both ways, drag between/within, filter, add/rename/delete column, reload); focus rings visible; icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 1 | E | 99 | Same full pass; rename via prompt works and persists; focus rings visible; icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 4 | C | 97 | Full pass on every feature (add, modal, Bug label, 'Oct 17 · overdue', close x3, delete both ways, drag, filter 1/2, add/rename/delete column, reload); no focus ring renders on the filter select, Add column button or new-card input when tabbed (D4 -1, Q2 -1); icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 5 | B | 96 | Full pass on every feature at 1280 and all controls 36-38 px with focus rings; but at 375 px the card modal stays 560 px wide (right edge at 576 px): the Close button and part of the Urgent chip are off-screen, only Escape/backdrop closes it (Q1 -4); 0 errors. |
