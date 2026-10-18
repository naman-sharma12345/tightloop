# Expense tracker (small website)

Build a single-page expense tracker. The user adds an expense with a description, an amount, a category (Food, Transport,
Housing, Fun, Other) and a date (today by default); invalid input (empty description, non-positive or non-numeric amount)
shows a clear inline message and adds nothing. Expenses are listed newest first with their category shown as a coloured tag,
and each can be deleted. A filter limits the list to one category or All. The page shows the total of the visible expenses,
formatted as money with two decimals, and a chart of spending by category (a bar or donut chart drawn with SVG or canvas,
no chart library) that updates whenever expenses change. Data survives a page reload. Element ids the checker uses: inputs
`#desc`, `#amount`, `select#category` (option values exactly as the category names above) and `#date`, inside a `form#expense-form`;
each listed expense is an `li` or `tr` inside `#expenses`; `#total` contains the total; the chart is `#chart` (an `svg` or `canvas`).

Design brief: it should look like a polished, modern product, not a demo. Use one cohesive visual style: a calm neutral
background, one accent colour used sparingly, a consistent spacing scale, the system font stack with a clear type hierarchy
(page title, section headings, body, muted secondary text), rounded corners and soft shadows on cards, and visible hover and
keyboard-focus states on everything interactive. Empty states get a short helpful message instead of a blank area. Controls are
labelled and have readable contrast. It must look good at 1280x800 and still work at 375 px wide.

Files: plain HTML, CSS and JavaScript in the current directory, `index.html` as the entry point, relative paths only
(the app may be served from a sub-folder). No build step, no npm packages, no CDN, fonts or other network requests; it must work
when served by any static file server. Data persists in localStorage. No console errors.
