# Bookmarks manager (small website)

Build a single-page bookmarks manager. The user adds a bookmark with a title, a URL and comma-separated tags; a URL that is
not a valid http(s) address is rejected with a clear inline message. Bookmarks are shown as cards with the title, the
site's domain, a letter avatar and the tags as chips; the title opens the URL in a new tab. A search box filters the cards
live by title, URL or tag (case-insensitive); clicking a tag chip filters by that tag, and the active filter is visible and
can be cleared. Bookmarks can be edited and deleted, and a counter shows how many are visible. Data survives a page reload.
Element ids the checker uses: inputs `#title`, `#url` and `#tags` inside a `form#bookmark-form`; the search input is `#search`;
each bookmark card has class `bookmark`.

Design brief: it should look like a polished, modern product, not a demo. Use one cohesive visual style: a calm neutral
background, one accent colour used sparingly, a consistent spacing scale, the system font stack with a clear type hierarchy
(page title, section headings, body, muted secondary text), rounded corners and soft shadows on cards, and visible hover and
keyboard-focus states on everything interactive. Empty states get a short helpful message instead of a blank area. Controls are
labelled and have readable contrast. It must look good at 1280x800 and still work at 375 px wide.

Files: plain HTML, CSS and JavaScript in the current directory, `index.html` as the entry point, relative paths only
(the app may be served from a sub-folder). No build step, no npm packages, no CDN, fonts or other network requests; it must work
when served by any static file server. Data persists in localStorage. No console errors.
