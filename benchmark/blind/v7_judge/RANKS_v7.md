# v7 blind ranks

Written 2026-10-19T00:06:55Z (UTC) by the blind judge (task 86a3da26). Rubric: tightloop b8d4711 r2_JUDGE_RUBRIC.md unchanged (benchmark/blind/v7_judge/RUBRIC.md, committed dbdfa44 before the zip was opened). Zip sha256 d736e41105fbb16575e9f517987444f3a4b9f2432cd21a05ea02fba35c81575b. Labels only; the judge read no key, results, token or log file.

Method (same as the v6c judge): Playwright Chromium, 1280x800 and 375x812, every feature clicked on every label (add + invalid input, edit, delete with confirm dismissed AND accepted, search/filters, folders/columns incl. "+ Add column" and every column rename/edit button, export/import, reload, Escape/backdrop, drag), console/page errors and external requests captured (0 / 0 / 0 on all 15), focus styles read after Tab (read after CSS transitions settle), every visible button clicked in a sweep, screenshots kept in the judge task dir. Prompts were answered the way a person would (typed a name, OK). Ties share a rank.


## bookmarks

| rank | label | score | reason |
|---|---|---|---|
| 1 | B | 100 | Full click-through pass: add form open on load, Title box typed into directly (the top-bar Add also focuses it); invalid 'notaurl' and ftp:// each rejected inline; add 3, card link opens in a new tab with domain, avatar, chips; counter; search by title/URL/tag; tag chip filter shown + cleared; edit; delete dismissed then accepted; folder Work create/filter/rename/delete (cancel keeps, accept moves bookmarks to Unsorted); export JSON array; import 1 added 1 duplicate skipped with message; reload; focus rings everywhere; 0 errors; 375 stacks, add works. Largest source (45 KB total), not deducted. |
| 1 | D | 100 | Full pass on every feature. The add form is HIDDEN until "+ Add bookmark" is clicked (typing into Title before that times out); clicking it opens the form and focuses Title, and Title takes typing normally; invalid URL inline, search/tag filter+clear, edit, delete both ways, folders create/rename/delete -> Unsorted, export, import 1+1 dup, reload; focus rings everywhere; 0 errors; 375 add works. |
| 1 | E | 100 | Full pass: add form open on load, Title typed into directly ('+ Add' focuses it); invalid URL inline, search, tag filter + Clear all, edit, delete both ways, folders create/rename/delete -> Unsorted, export, import 1 added 1 dup, reload; focus rings everywhere; 0 errors; 375 clean. |
| 4 | A | 99 | Full pass: add form open on load, Title typed into directly; invalid URL inline, search, tag filter + Clear all, edit, delete both ways, folders -> Unsorted, export, import 1+1 dup, reload; focus rings everywhere; ships an unused test.js in the build (Q3 -1); 0 errors; 375 clean. |
| 4 | C | 99 | Full pass: add form open on load, Title typed into directly; invalid URL inline, '#tag' chip filter + Clear all, edit, delete both ways, folders -> Unsorted, export, import 1+1 dup, reload; focus rings everywhere; ships an unused test.js in the build (Q3 -1); 0 errors; 375 clean. |

## expenses

| rank | label | score | reason |
|---|---|---|---|
| 1 | B | 100 | Full pass: month and date default to current; empty/negative/non-numeric/zero each rejected inline; 3 added newest first; #total '842.50' number only; 3 cards (total, count, Housing); category chart updates; 6-month table; category filter; previous month -> empty state + 0.00; edit in dialog saved with #save-edit (850.00); delete dismissed then accepted; CSV header exact; reload; focus rings; 0 errors; 375 clean. |
| 1 | D | 100 | Full pass on every feature (validation x4 inline, newest first, #total number only, 3 cards, chart + 6-month chart, filter, month -> empty state, dialog edit via #save-edit, delete both ways, CSV exact, reload); focus rings; 0 errors; 375 clean. |
| 3 | C | 99 | Full pass on every feature (validation x4 inline, #total number only, cards, chart + 6-month chart, filter, month -> empty state, in-place edit via #save-edit, delete both ways, CSV exact, reload); focus rings; ships an unused test.js in the build (Q3 -1); 0 errors; 375 clean. |
| 4 | A | 98 | Full pass on every feature ('$842.50' in #total, clickable 6-month bars, dialog edit via #save-edit, delete both ways, CSV exact, reload); focus rings; row Edit/Delete buttons 32 px (D3 -1); ships an unused test.js (Q3 -1); 0 errors; 375 clean. |
| 4 | E | 98 | Full pass on every feature (validation x4, cards, chart + 6-month table, filter, month -> empty state, dialog edit via #save-edit, delete both ways, CSV exact, reload); focus rings; row Edit/Delete buttons 32 px (D3 -1); ships an unused test.js (Q3 -1); 0 errors; 375 clean. |

## kanban

| rank | label | score | reason |
|---|---|---|---|
| 1 | A | 99 | Full click-through pass at 1280: whitespace title rejected with a hint, add by Enter and by button, 560 px dialog over dim backdrop (title/desc/due/Bug label), Bug chip + red 'Overdue', close by button/Escape/backdrop, card delete dismissed then accepted, drag To do -> In progress with drop indicator + reorder within To do, Bug filter shows 1, "+ Add column" WORKS (Add column form, 'Review' added), column rename/edit (pencil) buttons WORK on all 3 columns (inline input, persists after reload), column delete cancel/accept, reload; focus rings visible; column icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 1 | B | 99 | Same full pass: "+ Add column" WORKS (opens a prompt; named 'Review', column added), all 3 column Rename buttons WORK (prompt, persists after reload), column delete cancel/accept, add/modal/close x3/delete both ways/drag between+within/Bug filter/reload all pass; focus rings visible; column icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 1 | C | 99 | Same full pass: "+ Add column" WORKS (adds 'New column' at once with its name field focused; renamed 'Review'), all 3 column rename (pencil) buttons WORK (inline input, persists after reload; while another column's name field is open the first pencil click only closes that field), drag/filter/modal/delete/reload pass; focus rings visible after Tab; column icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 1 | D | 99 | Same full pass: "+ Add column" WORKS (adds 'New column' with an inline name field; renamed 'Review'), all 3 column edit (pencil) buttons WORK (inline input, persists after reload; same first-click-closes-open-field behaviour as C), drag/filter/modal/delete/reload pass; focus rings visible; column icon buttons 32 px (D3 -1); 0 errors; 375 modal fits. |
| 5 | E | 98 | Same full pass: "+ Add column" WORKS (prompt; 'Review' added), all 3 column edit (pencil) buttons WORK (prompt, persists after reload), drag/filter/modal/delete/reload pass; focus rings visible; column icon buttons 28 px (D3 -1); ships an unused test.js (node assert script) in the build (Q3 -1); 0 errors; 375 modal fits. |

## Runtime log per label

console errors / page errors / outside requests: 0 / 0 / 0 on every label (bookmarks A-E, expenses A-E, kanban A-E).
