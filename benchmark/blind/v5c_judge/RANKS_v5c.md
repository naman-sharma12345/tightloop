# v5c blind ranks

Written 2026-10-18T23:06:05Z by the blind judge. Rubric: round-2 rubric from tightloop b8d4711, unchanged (RUBRIC_USED.md, committed ca2669e before the zip was opened).
Zip sha256 e6ead87f37745650cea98ee0b858a0f8c4b431bf908bc056e9d252589c23ddf9. Labels only; the judge does not know which version made which label.
Method: Playwright headless Chromium, 1280x800 and 375x812, every feature clicked (add, edit, delete with confirm dismissed AND accepted, filters/search, folders/columns, export/import, reload persistence, Escape/backdrop, drag), console/page errors and external requests captured (0 external requests on all 17), keyboard-focus styles read from computed style after Tab, every visible button clicked in a sweep, screenshots looked at (shots/ in the judge task dir). Ties share a rank per the rubric.

## bookmarks

| rank | label | score | reason |
|---|---|---|---|
| 1 | B | 99 | Clicked through add (inline URL error shown), search, tag chip + Clear all, edit, delete (confirm cancelled then accepted), folder create/rename/delete (bookmark moved to Unsorted), export JSON array, import 1 added 1 duplicate skipped, reload kept 4; 0 errors; focus rings visible on buttons and the new-folder input; 375 px stacks with no page scroll. |
| 1 | C | 99 | Same full click-through passed (invalid URL message, search, tag filter + clear, edit, delete confirm both ways, folders, export/import, reload); focus outline on buttons and ring on inputs; 0 errors; 375 px clean. |
| 3 | A | 98 | Full click-through passed incl. folders, export/import report and reload; 0 errors; focus ring on buttons but none rendered on the new-folder input when tabbed to (D4 -1). |
| 3 | D | 98 | Full click-through passed (inline URL error on submit, tag chips as #tags, folder flow, import report 'Skipped 1 duplicate URL', reload); 0 errors; new-folder input shows no focus ring when tabbed to (D4 -1). |
| 5 | E | 97 | Full click-through passed (inline URL error, folders, 'Import complete: 1 added, 1 duplicate skipped', reload); 0 errors; new-folder input has no focus ring (D4 -1) and the largest source at 45 KB (Q3 -1). |

## expenses

| rank | label | score | reason |
|---|---|---|---|
| 1 | E | 100 | Add with inline errors for empty/negative/non-numeric/zero, newest-first list with coloured tags, #total 842.50 only, 3 cards, category chart + 6-month trend svg, category filter to 1 row, month picker to previous month shows empty state, edit via #save-edit (850.00, total 862.50), delete cancel/accept, CSV header exact, reload kept rows; visible focus; 0 errors; 375 px clean. |
| 1 | F | 100 | Same full pass: inline errors sit under their fields, list/cards/charts update, filter and month picker work, edit saved, delete confirm both ways, CSV header exact, reload persists; focus ring + border on controls; 0 errors; 375 px clean. |
| 1 | G | 100 | Same full pass (also shows an average per expense); inline errors, cards, chart, 6-month trend, filter, month picker empty state, edit saved, delete both ways, CSV header exact, reload; focus outline visible; 0 errors; 375 px clean. |
| 4 | C | 99 | Full pass on every feature (edit saved desc, delete both ways, CSV header, reload, chart, trend, filter, month); 0 errors; but the month input shows no focus ring when tabbed to (D4 -1). |
| 4 | D | 99 | Full pass (6-month table instead of chart, allowed; edit 850 saved, total 862.50; CSV; reload); focus outline visible; 0 errors; row Edit/Delete buttons are 32 px tall (D3 -1). |
| 6 | B | 98 | Full pass (chart + 6-month table and svg, edit saved, delete both ways, CSV, reload); 0 errors; focus style on the month input is near-invisible (4% shadow) (D4 -1) and the largest expenses source at 36 KB (Q3 -1). |
| 7 | A | 71 | BROKEN LIST: after adding 3 expenses the total shows 842.50 and the cards update, but #expenses stays empty with the empty-state text, the category chart stays at $0.00, and Edit/Delete never appear; 8 page errors 'Cannot set property dataset'. Validation, month picker, CSV export and reload of totals work. F1 5, F2 0, F3 7, F4 4, F5 0. |

## kanban

| rank | label | score | reason |
|---|---|---|---|
| 1 | B | 100 | Add by Enter and by button, blank rejected, modal 560 px over dim backdrop with title/desc/due/labels saved, Bug chip and red overdue date, close by button/Escape/backdrop, delete cancel then accept, drag to In progress and reorder within To do, Bug filter shows 1 of 2, add column via typed name, rename column, counts per column, reload persists; all controls 36-40 px; focus outlines visible; 0 errors; 375 px clean with modal fitting. |
| 2 | C | 99 | Same full pass (prompt-based add/rename column, drag between and within, filter, modal closes 3 ways, delete confirm both ways, reload); focus outlines visible; 0 errors; column icon buttons are 32 px (D3 -1). |
| 2 | D | 99 | Same full pass (modal also offers a column select; drag, reorder, filter, add/rename column, counts, reload); focus outlines visible; 0 errors; icon buttons 32 px (D3 -1). |
| 2 | E | 99 | Same full pass (drag, reorder, filter, add/rename column, modal 3 close paths, delete both ways, reload); focus outlines visible; 0 errors; icon buttons 32 px (D3 -1). |
| 5 | A | 97 | Full pass on every feature (counts inline in headers, drag, reorder, filter, add/rename column, modal, delete, reload); 0 errors; but when tabbing to the filter select, Add column button and new-card input no focus ring was rendered despite a declared :focus-visible ring (D4 -1, Q2 -1), icon buttons 32 px (D3 -1), and the largest kanban source at 35 KB. |
