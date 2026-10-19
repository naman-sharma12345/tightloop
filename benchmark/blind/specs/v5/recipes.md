# V5-2 Recipe box (small website)

Build a single-page recipe box. The user adds a recipe with a title, a number of servings, comma-separated tags, an
ingredients list (one per line, e.g. "200 g flour", "1/2 cup milk", "2 eggs") and steps (one per line); a recipe without a
title or with servings that are not a positive whole number is rejected with a clear inline message. Recipes show as cards
with tag chips. Clicking a card opens a detail panel with the ingredients and numbered steps. In the detail
panel a servings scaler rescales every ingredient that starts with a number (whole, decimal or a fraction like 1/2):
new quantity = quantity x new servings / original servings, shown with at most 2 decimals and no trailing zeros (0.75, 1.5,
3); ingredients without a leading number are shown unchanged. A search box filters live by title or ingredient text
(case-insensitive) and a tag filter shows only recipes with that tag. Recipes can be edited (loaded back into the form,
saved over the same recipe) and deleted. Everything survives a page reload. Every destructive action asks first with the
browser's native `confirm()` (not a custom dialog) and does nothing if the user cancels. Element ids the checker uses: inputs
`#recipe-title`, `#recipe-servings`, `#recipe-tags`, textareas `#recipe-ingredients` and `#recipe-steps`, and the save button
`#save-recipe`, inside `form#recipe-form`; each card has class `recipe` inside `#recipes`, its title is in `.recipe-title`,
and its edit and delete buttons carry the classes `edit` and `delete`; the detail panel is `#recipe-detail`; each ingredient
is an `li` with class `ingredient` whose quantity is in a `.qty` element holding ONLY the number; the scaler is the number
input `#scale-servings` (it starts at the recipe's servings); the search input is `#search`; the tag filter is
`select#tag-filter` (first option value "" = all tags, then one option per tag, lower case).

Design instructions:
- Layout: a header with search and the tag filter, then three panes: the form (320 px) left, a 2-column card grid in the middle, the detail panel right.
- Palette: background #faf7f2, surfaces #ffffff, text #292524, muted #78716c, borders #e7e5e4, one accent #c2410c (terracotta); tag chips in soft tints of sage, sand and clay. Use the accent only for primary actions, the active state and focus rings.
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
