# R2-2 Expense tracker (small website)

Build a single-page expense tracker. The user adds an expense with a description, an amount, a category (Food, Transport,
Housing, Fun, Other) and a date (today by default); invalid input (empty description, non-positive or non-numeric amount)
shows a clear inline message and adds nothing. Expenses are listed newest first, with the category as a coloured tag; each can
be edited in place or in a small dialog, and deleted. A month picker selects which month is shown (default: the current month)
and a category filter narrows the list. Summary cards show the month's total, the number of expenses and the largest category,
all formatted as money with two decimals. A chart of the month's spending by category (bars or a donut, drawn with SVG or
canvas, no chart library) updates whenever data changes, and a second small chart or table shows the total for each of the
last 6 months. Export CSV downloads the visible expenses (header row: date,description,category,amount). Every destructive
action asks first with the browser's native `confirm()` (not a custom dialog) and does nothing if the user cancels. Element
ids the checker uses: inputs `#desc`, `#amount`, `select#category` (option values exactly the category names above) and
`#date` inside `form#expense-form`; each listed expense is an `li` or `tr` inside `#expenses`, and its edit and delete buttons
carry the classes `edit` and `delete`; an edit (in place or in a dialog) is saved with a button `#save-edit`; `#total`
contains ONLY the month's total as a formatted number (no label or other words inside that element); the month picker is
`#month` and defaults to the current month; the chart is `#chart` (an `svg` or `canvas`); the CSV control is `#export-csv`.

Design instructions:
- Layout: a header with the month picker and Export CSV, a row of 3 summary cards, then two columns: the add form and the expense list on the left (60%), the charts on the right (40%).
- Palette: background #f7f8fa, surfaces #ffffff, text #111827, muted #6b7280, borders #e5e7eb, one accent #0f9d76 (green); category colours: Food #f59e0b, Transport #3b82f6, Housing #8b5cf6, Fun #ec4899, Other #64748b; negative or error text #dc2626. Use the accent only for primary actions, the active state and focus rings.
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
