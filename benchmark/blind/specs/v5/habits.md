# V5-1 Habit tracker (small website)

Build a single-page habit tracker. The user adds a habit with a name and a colour; empty or whitespace-only names are not
added. Habits are listed as rows; each row shows the name, a week grid of 7 day cells (oldest on the left, the last cell is
today) and a streak count. Clicking a day cell toggles that day done or not done; days after today cannot be checked.
Previous/next week buttons move the grid back and forward by 7 days (never past the week that ends today), so past days can be
checked too. The streak is the number of consecutive done days ending today, or ending yesterday when today is not done yet;
it counts across weeks and updates at once. A habit can be renamed and deleted. Everything survives a page reload. Every
destructive action asks first with the browser's native `confirm()` (not a custom dialog) and does nothing if the user
cancels. Element ids the checker uses: inputs `#habit-name` and `select#habit-color` inside `form#habit-form` (colour option
values exactly teal, amber, rose, sky, lime, violet); each habit row has class `habit` and `data-color` set to its colour
value, its name is in `.habit-name`, and its edit and delete buttons carry the classes `edit` and `delete`; clicking `.edit`
shows an input with class `rename` inside the row, saved with Enter; each day cell is a `button` with class `day` and
`data-date` (YYYY-MM-DD, local date), with class `done` and `aria-pressed="true"` when done; `.streak` contains ONLY the
streak number; the week buttons are `#prev-week` and `#next-week`.

Design instructions:
- Layout: a centred single column (max 880 px): a header with the title and the week range, the add form as one inline row, then one card per habit with the name on the left, the 7 round day cells in the middle and the streak on the right; day initials above the grid.
- Palette: background #f5f7fb, surfaces #ffffff, text #1e293b, muted #64748b, borders #e2e8f0, one accent #7c3aed (violet); habit colours: teal #14b8a6, amber #f59e0b, rose #f43f5e, sky #0ea5e9, lime #84cc16, violet #8b5cf6, used to fill done cells. Use the accent only for primary actions, the active state and focus rings.
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
