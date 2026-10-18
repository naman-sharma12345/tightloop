# Round 2 blind judge: ranks

Written 2026-10-18T21:21:30Z (UTC) by the separate blind judge, against the rubric committed in b8d4711 (benchmark/blind/r2_JUDGE_RUBRIC.md, written before opening the zip).
Judged zip: viewer.zip sha256 6d033cc74dad2f3b4610663ddbc0add214ad472faa18399a6307bb56b9b96764. I worked from my own copy, and both copies' sha256 matched. Every build loaded (0 failed to load).
Evidence: every score comes from a Playwright click-through (headless chromium, 1280x800 plus 375 px) of every spec feature: add, invalid input, edit, delete with confirm dismissed and accepted, filters and search, drag (kanban), import and export, reload persistence. I captured console and page errors and external requests, and read the source. Screenshots were used only for the design lines, and always of the state after the click-through. Labels only; I know nothing about which setup made which build.
Integrity note: while I was judging, the box's own process-census facts pasted other tasks' command lines into my context. These were pass-3 token runs on a tokio task, and their skill texts were among them. They carried no round-2 label information, and I did not use them.

## bookmarks

| label | function /40 | design /35 | quality /25 | total /100 | rank |
|---|---|---|---|---|---|
| A | 40 | 35 | 24 | 99 | 1 |
| B | 40 | 34 | 23 | 97 | 2 |
| C | 40 | 33 | 23 | 96 | 3 |
| D | 40 | 31 | 25 | 96 | 4 |

Rank order: A > B > C > D

- bookmarks rank 1 = A: every feature worked in the click-through, and it has the most polished design (icons, brand mark, hinted empty states everywhere), 99.
- bookmarks rank 2 = B: every feature worked; clean but plainer visuals and dense CSS, 97.
- bookmarks rank 3 = C: every feature worked; no folder-list empty state, and creating a folder silently switches the view; wins the tie with D on design, 96.
- bookmarks rank 4 = D: every feature worked, but a literal "null" shows in the empty state and the folder list has no empty state, 96 (loses the design tie-break).

Why: Every build passed the full click-through: invalid URLs rejected, add, search, tag chips, folder filter, edit, delete with confirm dismiss and accept, folder rename and delete to Unsorted, export, import with duplicate skip, reload. 0 console errors. So the ranks come down to design and quality. A is the most finished: a brand mark, SVG icons, and empty states with hints everywhere. B is clean and complete but plainer. C loses a point on the folder-list empty state, and creating a folder silently moves the view into it. D has a visible bug: a literal "null" line in its empty state on first load, and no folder-list empty state. C and D tie on 96; the function tie-break leaves them tied, so design decides.

Per-line scores (points, reason):

bookmarks A:
- F1 core create: 8/8: 3 bad URLs (notaurl, ftp, javascript:) rejected with an inline message; add via spec ids works
- F2 edit + delete: 8/8: edit prefills the form and saves; delete: confirm dismissed keeps the card, accepted removes it
- F3 app features: 12/12: folders create, inline rename and delete (confirm; bookmarks move to Unsorted); search by title, URL and tag; tag chip filter + Clear all; counter; export JSON in the spec shape; import merges 1 and skips 1 duplicate, with a message
- F4 persistence: 6/6: bookmarks and folders survive two reloads
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: 240 px sidebar, top bar, 3-column card grid at 1280
- D2 palette + type: 10/10: spec hexes (#f6f7f9 bg, #4f46e5 accent), system font, 24 px/600 title, tabular numbers
- D3 spacing + surfaces: 5/5: 12 px radius, 1 px border, soft shadow, controls 36-38 px
- D4 states: 5/5: hover styles, focus ring; empty states with hints for the grid, the folder list and no-results
- D5 polish: 5/5: the most finished of the four: brand mark, SVG icons, clear hierarchy
- Q1 375 px: 10/10: 375 px: no horizontal scroll, panels stack, folder actions reachable
- Q2 accessibility: 8/8: labelled inputs, aria labels on the icon buttons (33 aria attributes)
- Q3 code clarity/size: 6/7: readable but the largest build (~45 KB)

bookmarks B:
- F1 core create: 8/8: 3 bad URLs rejected inline; add works
- F2 edit + delete: 8/8: edit prefills and saves; confirm dismiss keeps, accept deletes
- F3 app features: 12/12: folder create, rename (prompt) and delete (confirm, moves to Unsorted); search title/URL/tag; tag chip + Clear all; counter; export shape OK; import 1 added, 1 skipped, message
- F4 persistence: 6/6: survives reloads
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: sidebar, top bar, 3-column grid
- D2 palette + type: 10/10: spec palette and type
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 36-38 px controls
- D4 states: 5/5: hover and focus outline; empty states with hints, including the folder list
- D5 polish: 4/5: clean but plainer than A (text glyph icons, emoji folder tags)
- Q1 375 px: 10/10: 375 px: no overflow, stacked
- Q2 accessibility: 7/8: labels present; fewer aria hints (12)
- Q3 code clarity/size: 6/7: compact (~29 KB) but the CSS is dense one-line rules

bookmarks C:
- F1 core create: 8/8: 3 bad URLs rejected inline; add works
- F2 edit + delete: 8/8: edit prefills and saves; confirm dismiss keeps, accept deletes
- F3 app features: 12/12: folder create, rename (prompt) and delete (confirm, moves to Unsorted); search; tag chip + Clear all; counter; export shape OK; import 1 added, 1 skipped, message
- F4 persistence: 6/6: survives reloads
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: sidebar, top bar, 3-column grid
- D2 palette + type: 10/10: spec palette and type
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 36-38 px controls
- D4 states: 4/5: hover and focus OK; no empty-state message for the folder list
- D5 polish: 4/5: plain; creating a folder silently switches the view into that folder, so bookmarks added elsewhere seem to vanish ("2 of 3 shown")
- Q1 375 px: 10/10: 375 px: no overflow, stacked
- Q2 accessibility: 7/8: labels present; few aria hints (12)
- Q3 code clarity/size: 6/7: smallest (~23 KB) but the CSS is dense one-line rules

bookmarks D:
- F1 core create: 8/8: 3 bad URLs rejected inline; add works
- F2 edit + delete: 8/8: edit prefills and saves; confirm dismiss keeps, accept deletes
- F3 app features: 12/12: folder create, rename (prompt) and delete (confirm, moves to Unsorted); search; tag chip + Clear all; counter; export shape OK; import merges 1, skips 1, reports "Imported 1 bookmark"
- F4 persistence: 6/6: survives reloads
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: sidebar, top bar, 3-column grid
- D2 palette + type: 10/10: spec palette and type
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 36-38 px controls
- D4 states: 3/5: no folder-list empty state, and the bookmark empty state prints a literal "null" line
- D5 polish: 3/5: the visible "null" in the empty state (replaceChildren with a null action) is a visible bug on first load
- Q1 375 px: 10/10: 375 px: no overflow; folder actions shown on touch via hover:none
- Q2 accessibility: 8/8: labels plus aria (27); reduced-motion support
- Q3 code clarity/size: 7/7: readable, reasonable size (~39 KB)

## expenses

| label | function /40 | design /35 | quality /25 | total /100 | rank |
|---|---|---|---|---|---|
| A | 40 | 35 | 25 | 100 | 1 |
| D | 40 | 34 | 25 | 99 | 2 |
| B | 40 | 34 | 22 | 96 | 3 |
| C | 10 | 28 | 18 | 56 | 4 |

Rank order: A > D > B > C

- expenses rank 1 = A: every feature worked (validation, dialog edit, confirm delete, month and category, charts, CSV, reload); the most polished, with a chart plus a table for 6 months, 100.
- expenses rank 2 = D: every feature worked, with per-field errors; slightly plainer list than A, 99.
- expenses rank 3 = B: every feature worked; a large blank gap at 375 px and denser code, 96.
- expenses rank 4 = C: broken. A render error on every expense means the list never shows, edit and delete are unreachable and the charts don't update (9 page errors), 56.

Why: A, B and D pass every feature: 4 invalid cases, add, newest first, cards, chart redraw, 6-month view, filter, month picker, dialog edit, delete with confirm, an exact CSV header, reload. A edges D on polish: icon actions, category dots, and a 6-month chart plus a table. B adds a big blank gap at 375 px and has denser code. C is broken: its element helper throws on every render that has an expense (9 page errors), so the list never shows and edit and delete cannot be reached.

Per-line scores (points, reason):

expenses A:
- F1 core create: 8/8: empty desc, 0, -5 and "abc" each rejected with an inline message, nothing added
- F2 edit + delete: 8/8: dialog edit prefilled, #save-edit updates the total (1,220.50 -> 1,228.00), an invalid edit is blocked; delete: dismiss keeps, accept removes
- F3 app features: 12/12: month defaults to 2026-10, picker shows Sep alone (15.00); category filter; #total holds only the number; count and largest-category cards right; chart redraws; 6-month chart plus table; CSV header exact
- F4 persistence: 6/6: list and total survive a reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: header, 3 cards, 60/40 columns
- D2 palette + type: 10/10: spec palette, category colours, system font, tabular numbers
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 36-38 px controls
- D4 states: 5/5: focus ring, empty states with hints for the list and the chart
- D5 polish: 5/5: polished: category dots, icon buttons, the 6-month chart plus a table
- Q1 375 px: 10/10: 375 px: no overflow, clean stack
- Q2 accessibility: 8/8: labels for every field, dialog semantics, aria
- Q3 code clarity/size: 7/7: readable, reasonable size (~36 KB)

expenses B:
- F1 core create: 8/8: all 4 invalid cases rejected inline
- F2 edit + delete: 8/8: dialog edit saves (1,228.00), invalid edit blocked; delete: dismiss keeps, accept removes
- F3 app features: 12/12: month default and picker, category filter, cards, chart redraws (checked by outerHTML diff), 6-month chart, CSV header exact; #total is "$1,220.50"
- F4 persistence: 6/6: survives reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: header, 3 cards, 60/40 columns
- D2 palette + type: 10/10: spec palette and type
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 38 px controls
- D4 states: 5/5: focus outline, empty states with hints
- D5 polish: 4/5: clean, plainer list rows (text Edit/Delete)
- Q1 375 px: 9/10: 375 px: no overflow, but a large blank gap between the list and the charts
- Q2 accessibility: 7/8: labels present; fewer aria hints
- Q3 code clarity/size: 6/7: compact; CSS denser

expenses C:
- F1 core create: 4/8: validation messages work, but an added expense never appears in the list
- F2 edit + delete: 0/8: no rows are ever rendered, so there is nothing to edit or delete
- F3 app features: 3/12: CSV export works with the exact header; month picker and filter act on an always-empty list; cards and chart stop updating mid-render (total stuck at a stale value, chart blank)
- F4 persistence: 3/6: data is written to localStorage (total and count after reload) but the list still renders empty
- F5 clean runtime: 0/6: 9 page errors: "Cannot set property dataset of HTMLElement" on every render with an expense
- D1 layout: 10/10: header, 3 cards, 60/40 columns
- D2 palette + type: 9/10: spec palette; total shown as "1220.50" without separator after reload
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 38 px controls
- D4 states: 3/5: shows the empty state permanently, even when expenses exist
- D5 polish: 1/5: looks broken: count 4 and a non-zero total beside an empty list and blank charts
- Q1 375 px: 9/10: 375 px: no overflow (but the content is broken)
- Q2 accessibility: 6/8: labels present, few aria hints
- Q3 code clarity/size: 3/7: small, but the el() helper does Object.assign(li, {dataset:...}), which throws: shipped untested

expenses D:
- F1 core create: 8/8: all 4 invalid cases rejected with per-field messages
- F2 edit + delete: 8/8: dialog edit saves (1,228.00), invalid edit blocked; delete: dismiss keeps, accept removes
- F3 app features: 12/12: month default and picker (adding an expense dated in another month jumps the view to that month), filter, cards (largest + share %), chart redraws, 6-month chart, CSV header exact
- F4 persistence: 6/6: survives reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: header, 3 cards, 60/40 columns
- D2 palette + type: 10/10: spec palette and type
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow, 38 px controls
- D4 states: 5/5: focus ring, empty states with hints
- D5 polish: 4/5: polished, a notch below A (text buttons, no table)
- Q1 375 px: 10/10: 375 px: no overflow, clean stack
- Q2 accessibility: 8/8: labels, per-field error elements, roles
- Q3 code clarity/size: 7/7: readable, smallest working build (~29 KB)

## kanban

| label | function /40 | design /35 | quality /25 | total /100 | rank |
|---|---|---|---|---|---|
| A | 40 | 35 | 25 | 100 | 1 |
| B | 40 | 34 | 25 | 99 | 2 |
| D | 40 | 34 | 23 | 97 | 3 |
| C | 40 | 33 | 23 | 96 | 4 |

Rank order: A > B > D > C

- kanban rank 1 = A: every feature worked (drag with indicator, modal with 3 ways to close, confirm delete, labels, overdue, filter, columns, reload); the most polished, 100.
- kanban rank 2 = B: every feature worked; overdue is shown by colour only, 99.
- kanban rank 3 = D: every feature worked; emoji header icons and dense CSS, 97.
- kanban rank 4 = C: every feature worked; 28 px icon controls, emoji icons, prompt() for columns, fewest labels, dense CSS, 96.

Why: All four pass every feature: add by Enter or button, blank rejected, mouse drag between and within columns with a drop indicator, the modal (title, description, due date, labels; closes by button, Escape and backdrop; delete with confirm dismiss and accept), red overdue dates, counts, label filter, add and rename column, reload, and keyboard-openable cards. A is the most polished, with SVG icons and the word "overdue". B is close, but shows overdue by colour only. D and C use emoji header icons and dense CSS. C also has 28 px icon controls, prompt() dialogs and fewer labels.

Per-line scores (points, reason):

kanban A:
- F1 core create: 8/8: Enter and the Add button both add; whitespace and empty titles ignored
- F2 edit + delete: 8/8: modal edits title, description, due date and labels and they persist; #card-delete: dismiss keeps, accept deletes and closes
- F3 app features: 12/12: mouse drag between columns and within a column, with a drop indicator; add and rename column (inline); modal closes by button, Escape and backdrop; labels shown, overdue in red with the word "overdue"; counts update; label filter
- F4 persistence: 6/6: cards, columns, labels and dates survive a reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: slim top bar, 300 px columns, centred 560 px modal over a dimmed backdrop
- D2 palette + type: 10/10: spec palette, label colours, system font
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow on cards and columns
- D4 states: 5/5: hover, focus ring, empty column states with hints
- D5 polish: 5/5: most polished: SVG icons, clear card meta
- Q1 375 px: 10/10: 375 px: columns stack, no page overflow
- Q2 accessibility: 8/8: cards are role=button with tabindex 0; Enter opens the modal and focuses the title; sr-only labels; aria-pressed toggles
- Q3 code clarity/size: 7/7: readable, reasonable size (~34 KB)

kanban B:
- F1 core create: 8/8: Enter and Add both add; blank titles ignored
- F2 edit + delete: 8/8: modal edits persist; delete: dismiss keeps, accept deletes
- F3 app features: 12/12: drag between and within columns, with a drop indicator; inline add-column form and inline rename; Close, Escape and backdrop all close; overdue date in red; counts; filter
- F4 persistence: 6/6: survives reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: top bar, 300 px columns, 560 px modal
- D2 palette + type: 10/10: spec palette and label colours
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow
- D4 states: 5/5: hover, focus, empty states with hints
- D5 polish: 4/5: polished; overdue is shown by colour only (no word)
- Q1 375 px: 10/10: 375 px: stacks, no overflow
- Q2 accessibility: 8/8: keyboard-openable cards, labelled fields, the most aria hints (24)
- Q3 code clarity/size: 7/7: readable, reasonable size (~33 KB)

kanban C:
- F1 core create: 8/8: Enter and Add both add; blank titles ignored
- F2 edit + delete: 8/8: modal edits persist; delete: dismiss keeps, accept deletes
- F3 app features: 12/12: drag between and within columns, with a drop indicator; add and rename column (prompt); Close, Escape and backdrop close; "Overdue" in red; counts; filter
- F4 persistence: 6/6: survives reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: top bar, 300 px columns, 560 px modal
- D2 palette + type: 10/10: spec palette and label colours
- D3 spacing + surfaces: 4/5: column icon buttons 28 px tall, under the spec controls; empty boxes 8 px radius
- D4 states: 5/5: hover, focus, empty states with hints
- D5 polish: 4/5: emoji icons (pencil, wastebasket) always visible on every column header
- Q1 375 px: 10/10: 375 px: stacks, no overflow
- Q2 accessibility: 7/8: keyboard-openable cards; fewer labels (4), prompt() dialogs
- Q3 code clarity/size: 6/7: smallest (~18 KB) but the CSS is dense one-line rules

kanban D:
- F1 core create: 8/8: Enter and Add both add; blank titles ignored
- F2 edit + delete: 8/8: modal edits persist; delete: dismiss keeps, accept deletes
- F3 app features: 12/12: drag between and within columns, with a drop indicator; add and rename column; Close, Escape and backdrop close; "Overdue" in red; counts; filter
- F4 persistence: 6/6: survives reload
- F5 clean runtime: 6/6: 0 console errors, 0 page errors, 0 external requests
- D1 layout: 10/10: top bar, 300 px columns, 560 px modal
- D2 palette + type: 10/10: spec palette and label colours
- D3 spacing + surfaces: 5/5: 12 px radius, border, shadow
- D4 states: 5/5: hover, focus, empty states with hints
- D5 polish: 4/5: emoji icons on column headers; otherwise tidy
- Q1 375 px: 10/10: 375 px: stacks, no overflow
- Q2 accessibility: 7/8: keyboard-openable cards; fewer labels and aria hints (12)
- Q3 code clarity/size: 6/7: reasonable size, but the CSS is dense one-line rules

## Overall (mean rank across the 3 apps; tie -> higher mean total)

| label | bookmarks | expenses | kanban | mean rank | mean total |
|---|---|---|---|---|---|
| A | 1 | 1 | 1 | 1.00 | 99.7 |
| B | 2 | 3 | 2 | 2.33 | 97.3 |
| D | 4 | 2 | 3 | 3.00 | 97.3 |
| C | 3 | 4 | 4 | 3.67 | 82.7 |

Overall order: A > B > D > C

Contact sheets (screenshots after the click-through, 1280x800 plus 375 px): benchmark/blind/r2_judge_sheets/{bookmarks,expenses,kanban}.png
