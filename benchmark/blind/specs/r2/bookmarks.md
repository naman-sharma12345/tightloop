# R2-1 Bookmarks manager (small website)

Build a single-page bookmarks manager. The user adds a bookmark with a title, a URL, comma-separated tags and a folder; a URL
that is not a valid http(s) address is rejected with a clear inline message. Folders are listed in a sidebar ("All bookmarks"
plus user folders; the user can create, rename and delete a folder, and deleting a folder moves its bookmarks to "Unsorted").
Bookmarks show as cards with the title (opens in a new tab), the domain, a letter avatar and the tags as chips. A search box
filters live by title, URL or tag (case-insensitive); clicking a tag chip filters by that tag, and active filters are shown
and can be cleared. Bookmarks can be edited and deleted, and a counter shows how many are visible. Export downloads all data
as a JSON file; Import reads such a file and merges it, skipping duplicate URLs and reporting how many were added. Element ids
the checker uses: inputs `#title`, `#url`, `#tags` and `select#folder` inside `form#bookmark-form`; the search input is
`#search`; each bookmark card has class `bookmark`; the export and import controls are `#export` and `#import` (a file input or
a button that opens one).

Design instructions:
- Layout: a fixed left sidebar (folders, 240 px) and a main area with a top bar (search, add, import/export) above a responsive card grid (3-4 columns at 1280 px).
- Palette: background #f6f7f9, surfaces #ffffff, text #1f2328, muted #6b7280, borders #e5e7eb, one accent #4f46e5 (indigo); tag chips use soft tints of a few distinct hues. Use the accent only for primary actions, the active state and focus rings.
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
