# r11 spec: habit tracker

Build a habit tracker in the browser.

Function:
- Add a habit with a name (1-60 characters after trimming; empty, whitespace-only and duplicate names, case-insensitive,
  are rejected with an inline message), a colour from a fixed set of 6, and a schedule: every day, or chosen weekdays
  (at least one), or N times per week (1-7).
- Today view: each habit due today as a row with a check button; checking marks today done, checking again unmarks.
  Habits not due today are listed separately and can still be checked.
- Streak per habit: consecutive scheduled periods completed up to today (for N times per week, a week counts when it has at
  least N check-ins; the current week counts only once it is met). Show current streak and best streak.
- A 12-week calendar heatmap per habit (one cell per day, today at the end); clicking a past cell toggles that day;
  future cells are disabled. Each cell has an accessible label like "Mon 3 Mar: done".
- Edit a habit (name, colour, schedule) in a dialog; changing the schedule recomputes streaks. Archive and restore a habit;
  archived habits are hidden from Today but kept in an Archived section. Delete asks first with the native `confirm()`,
  and does nothing when dismissed.
- Undo: the last 10 actions (check, uncheck, edit, archive, delete) can be undone with an Undo button and Ctrl/Cmd+Z;
  each undo shows a short toast naming what was undone.
- Keyboard: arrow keys move between habit rows on Today, Space toggles the focused habit, N opens the add form.
- Export all data as JSON; import a JSON file, validating it (a bad file shows an error and changes nothing), merging
  habits by name and keeping the union of check-ins.
- Dates use the user's local time zone; a check-in made just before midnight belongs to that day. The app must behave
  correctly when the page stays open across midnight (Today rolls over within a minute).

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
