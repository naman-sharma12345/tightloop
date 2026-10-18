# R2-3 Kanban board (small website)

Build a single-page kanban board with columns To do, In progress and Done (the user can also add and rename columns). The user
adds a card by typing a title and pressing Enter or an Add button; empty or whitespace-only titles are not added. Cards are
dragged between columns and reordered within a column (mouse drag and drop, with a visible drop indicator). Clicking a card
opens a detail modal where the user edits the title and a longer description, sets a due date, and toggles labels from a fixed
set (Bug, Feature, Design, Urgent, each with its own colour); the modal closes with a Close button, the Escape key or a click on
the backdrop, and has a Delete button. Cards show their labels as small coloured bars or chips and the due date (overdue dates in
red). Each column header shows its card count. A filter shows only cards with a chosen label. The board survives a page reload.
Element ids the checker uses: the new-card title input is `#new-card`; each column is an element with class `column` and
`data-col` set to `todo`, `doing` or `done` for the three default columns; each card is an element with class `card` inside its
column; the detail modal has id `card-modal` and is visible only while open.

Design instructions:
- Layout: a slim top bar (board title, label filter, add column) above horizontally arranged columns of equal width (280-320 px) that scroll horizontally inside the board when they do not fit; the modal is centred, 560 px wide, over a dimmed backdrop.
- Palette: background #eef1f5, column surfaces #f8fafc, cards #ffffff, text #0f172a, muted #64748b, borders #e2e8f0, one accent #2563eb (blue); labels: Bug #ef4444, Feature #22c55e, Design #a855f7, Urgent #f97316. Use the accent only for primary actions, the active state and focus rings.
- Type: the system font stack (-apple-system, Segoe UI, Roboto, sans-serif); page title 24 px semibold, section headings
  16 px semibold, body 14-15 px, secondary text muted grey; numbers right-aligned with tabular figures where they line up.
- Spacing: an 8 px scale (8/16/24/32); cards and panels have 12 px radius, a 1 px border and a soft shadow; controls are 36-40 px tall.
- States: visible hover and keyboard-focus styles on everything interactive; every list or board area that can be empty shows
  a short friendly empty-state message with a hint of what to do; destructive actions ask for confirmation.
- Responsive: it must look polished at 1280x800 and remain fully usable at 375 px wide (stack panels vertically, no
  horizontal page scroll except inside the board where noted).

Files: plain HTML, CSS and JavaScript in the current directory, `index.html` as the entry point, relative paths only
(the app is served from a sub-folder). No build step, no npm packages, no CDN, web fonts or other network requests; it must
work when served by any static file server. All data persists in localStorage. No console errors.
