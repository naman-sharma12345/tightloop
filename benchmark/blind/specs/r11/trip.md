# r11 spec: trip planner

Build a multi-day trip planner in the browser.

Function:
- Trips: create, rename and delete trips (native `confirm()` before delete, nothing happens when dismissed). A trip has a
  name, start and end date (end not before start; 1-30 days) and a list of travellers (1-8 names, unique).
- Itinerary: one column per day (horizontal scroll inside the board when the days do not fit). Add an activity to a day
  with a title (required), start time, duration (15-minute steps, 15 min to 12 h), place (free text), category (Food,
  Sight, Transport, Stay, Other, each with its own icon) and an optional cost.
- Activities within a day are always shown sorted by start time. Overlapping activities in the same day are flagged on
  both items with a visible conflict marker and a text explanation ("overlaps Lunch 12:30-13:30").
- Move an activity to another day by drag and drop, and also without a mouse: a "Move to..." menu on each activity.
  Moving keeps the start time and re-checks conflicts in both days.
- Changing the trip dates: shortening the trip must not silently lose activities; activities on removed days move to an
  "Unscheduled" tray, and the user is told how many moved.
- Activity detail dialog: edit every field, notes (multi-line), and "Paid by" (one traveller) with "Split between"
  (a subset of travellers, at least one). Close by button, Escape or backdrop click; delete inside with `confirm()`.
- Budget panel: total cost, cost per category, cost per day, and a settle-up table: what each traveller paid, their share,
  and the smallest list of transfers that settles all debts (amounts to 2 decimals; rounding cents assigned so the
  transfers sum exactly).
- Undo/redo the last 20 changes (buttons and Ctrl/Cmd+Z, Shift+Ctrl/Cmd+Z).
- Search activities across the trip by title or place; matching items are highlighted and non-matching days collapse.
- Export the itinerary as an .ics calendar file (one VEVENT per activity with the trip's local times) and export/import
  the whole trip as JSON (bad files rejected with an error, nothing changed).

Design brief (open on purpose: the look is yours to design and is judged):
- It should feel like a calm, premium product a designer shipped, not a template: a clear visual hierarchy, one coherent
  palette you choose (state it as CSS custom properties), consistent spacing and type scale, and real icons (inline SVG).
- Every interactive element has hover, active, disabled and keyboard-focus styles; every list or panel that can be empty
  shows a friendly empty state that says what to do next; errors are inline, next to the field, in plain words.
- Responsive: polished at 1280x800 and fully usable at 375 px wide (no horizontal page scroll, touch targets at least 40 px).
- Accessible: every control reachable and usable by keyboard alone in a sensible order, labelled inputs, visible focus,
  colour is never the only signal, text contrast at least 4.5:1, dialogs trap focus and return it when closed.
- Motion is subtle and respects prefers-reduced-motion.

Files: plain HTML, CSS and JavaScript in the current directory, `index.html` as the entry point, relative paths only
(the app is served from a sub-folder). No build step, no npm packages, no CDN, web fonts, images from the network or other
network requests; it must work when served by any static file server. All data persists in localStorage under one key
per app, and a corrupt or missing value must not break the page (start empty and say so). No console errors.
