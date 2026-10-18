# V5-3 Pomodoro timer (small website)

Build a single-page pomodoro timer with three modes: Focus, Short break and Long break. Durations are set in whole minutes
(defaults 25, 5 and 15) and a long break comes after every 4th focus session; changing a duration while the timer is not
running updates the display at once. Start, Pause and Reset control the timer; Reset returns the current mode to its full
duration and stops it. When a session reaches 00:00 the app adds it to the history and advances automatically to the next mode
(Focus to Short break, or Long break after every 4th focus; any break back to Focus) and keeps running. The user keeps a task
list: add a task (empty names are not added), click a task to make it the active one, delete a task. Each finished Focus
session adds 1 to the active task's completed count. Settings, tasks, the active task, counts and the history survive a page
reload (the running timer does not have to). The timer must be driven by setInterval/setTimeout and Date.now(), never by
requestAnimationFrame alone. Every destructive action asks first with the
browser's native `confirm()` (not a custom dialog) and does nothing if the user cancels. Element ids the checker uses: the
time display `#time` shows ONLY mm:ss; `#mode` has `data-mode` set to `focus`, `short` or `long`; the buttons are `#start`,
`#pause` and `#reset`; the number inputs are `#focus-min`, `#short-min` and `#long-min`; inputs `#task-input` inside
`form#task-form`; each task is an element with class `task` (class `active` when active), its name in `.task-name`, its count
in `.count` holding ONLY the number, and its delete button carries the class `delete`; the history is `#history`, one `li`
per finished session with `data-mode` set to its mode; `#clear-history` clears the history.

Design instructions:
- Layout: a large timer card (mode tabs, a big mm:ss, the three buttons, then the settings) with the task list on its right (360 px) and the session history in a strip beneath both.
- Palette: dark theme: background #1c1a26, surfaces #26233a, text #f4f4f5, muted #a1a1aa, borders #3f3b56, one accent #f43f5e (tomato); breaks use #22d3ee for Short and #a3e635 for Long. Use the accent only for primary actions, the active state and focus rings.
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
