# Kanban board (small website)

Build a single-page kanban board with three columns: To do, In progress and Done. The user adds a card by typing a title
(and an optional short description) and pressing Enter or an Add button; the card appears in To do. Cards can be dragged
between columns and reordered within a column (mouse drag and drop); each card can be edited (title and description) and
deleted. Each column header shows its card count, and a card in Done looks visibly finished. Empty or whitespace-only titles
are not added. The board survives a page reload. Element ids the checker uses: the new-card title input is `#new-card`; each
column is an element with class `column` and `data-col` set to `todo`, `doing` or `done`; each card is an element with class
`card` inside its column.

Design brief: it should look like a polished, modern product, not a demo. Use one cohesive visual style: a calm neutral
background, one accent colour used sparingly, a consistent spacing scale, the system font stack with a clear type hierarchy
(page title, section headings, body, muted secondary text), rounded corners and soft shadows on cards, and visible hover and
keyboard-focus states on everything interactive. Empty states get a short helpful message instead of a blank area. Controls are
labelled and have readable contrast. It must look good at 1280x800 and still work at 375 px wide.

Files: plain HTML, CSS and JavaScript in the current directory, `index.html` as the entry point, relative paths only
(the app may be served from a sub-folder). No build step, no npm packages, no CDN, fonts or other network requests; it must work
when served by any static file server. Data persists in localStorage. No console errors.
