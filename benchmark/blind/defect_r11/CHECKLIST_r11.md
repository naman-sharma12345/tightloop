# CHECKLIST r11 - weighted defect count (written from the 3 specs only, before any build was opened)

Specs (sha256 checked before writing):
- habits.md  cff54483ed0314d5b6dcd9d7fd0d8a3b15eb08465451352475bce863de5b608d
- invoice.md 7b6d1ac8ecdba5de250ddcabd1c7d31ea5bbc5569a466637331687a4ed37331b
- trip.md    4158176e37737a6bcb14d219383c25e479d3a22aafd3ad3fc997269adb2b395d

## Weights (fixed by root, not changed here)
- blocker = 10: a spec feature missing, not reachable, or broken; data loss; a crash or uncaught error that stops use.
- major = 3: the feature works but a spec-stated rule or edge case is wrong; a wrong number or format; a console error that does not stop use.
- minor = 1: cosmetic or polish: overflow, clipping or overlap at 375 or 1280; misaligned or unclear UI; missing feedback the spec does not demand.

## Scoring rule
1. Every item below is run on every build of its spec, plus the GENERAL list on every build.
2. An item passes or fails. A failed item is ONE defect. Its weight is the item's default severity, with one fixed escalation and one fixed step-down:
   - escalate to blocker when the feature the item tests is absent, cannot be reached, or does nothing at all, or when the failure loses data (something deleted or overwritten that the user did not ask to lose);
   - an item marked [F] (a whole feature) is blocker when it fails; it may only be scored major if the feature works but one stated sub-rule of the item fails.
3. No double counting: if one root cause makes several items fail (e.g. the add form never submits, so later items cannot be set up), it is counted ONCE, on the first item it breaks. Later items that cannot be run because of it are marked "blocked-by <id>" and are not scored. The shared cause is noted.
4. Items whose setup needs another feature use a fallback setup where the spec allows one (e.g. data via the app's own UI on another day by moving the fixed clock). Only if no fallback exists is the item marked blocked-by.
5. Defects found that no item covers are recorded as "unlisted" with a severity by the same weights, reported in a separate column, NOT in the main score.
6. Build score = sum of weights of failed listed items (lower is better). Items tested, items passed, and blocker/major/minor counts are reported per build.
7. This checklist and PROTOCOL.md are fixed before any build is opened; they are not changed after.

Fixed test conditions for every build: browser clock fixed at Thu 22 Oct 2026 10:00 local (time runs from there; moved only where an item says so), time zone Asia/Kolkata, locale en-US, fresh browser profile and empty localStorage per build. "Today" below = Thu 22 Oct 2026. D-n = n days before today.
A "native confirm" means a window.confirm() dialog (seen by the browser's dialog event, type "confirm"). "Inline message" means visible text next to the field or form, not only an alert().

---------------------------------------------------------------------
## HABITS (habits.md) - 35 items

H01 [F] Add habit. Spec: "Add a habit with a name ..., a colour ..., and a schedule". Test: open the add form, name "Read", pick a colour, schedule every day, save. Pass: "Read" appears on Today with a check button. Default: blocker.
H02 Name trimmed and 1-60 chars. Test: add "  Walk  " -> saved/shown as "Walk"; add a 60-char name -> accepted; try a 61-char name -> rejected with an inline message, or the field cannot hold more than 60. Pass: all three. Default: major.
H03 Empty and whitespace-only names rejected inline. Test: submit "" and "   ". Pass: no habit added, inline message near the field both times. Default: major.
H04 Duplicate names rejected, case-insensitive. Test: with "Read" present, add "read" and " READ ". Pass: no habit added, inline message. Default: major.
H05 Colour from a fixed set of 6. Test: open the add form, count colour choices; pick a non-default colour and save. Pass: exactly 6 choices; the habit shows the chosen colour. Default: major (blocker if no colour choice at all).
H06 Schedule "chosen weekdays, at least one". Test: pick weekdays with none selected and save -> rejected; add "Gym" on Mon/Wed/Fri. Pass: zero weekdays rejected with a message; "Gym" saved and is NOT in the due-today list (today is Thursday). Default: major.
H07 Schedule "N times per week (1-7)". Test: try N = 0 and N = 8 -> rejected or impossible; add "Swim" 2 times per week. Pass: out-of-range blocked; 2/week saved. Default: major.
H08 [F] Today: due habits as rows with a check button; checking marks today done. Test: check "Read". Pass: row shows done state (not only by colour: icon, text or aria-pressed/checked). Default: blocker.
H09 Checking again unmarks. Test: click "Read"'s check again. Pass: back to not done. Default: major.
H10 Not-due habits listed separately and can still be checked. Test: find "Gym" (Mon/Wed/Fri) in a separate not-due group; check it. Pass: separate group exists and the check registers. Default: major.
H11 Daily streak: current and best. Setup (using the app's own UI with the clock moved, one reload per day): daily habit "Stretch" created on D-9; checked on D-9..D-4 (6 days), not D-3, checked D-2, D-1 and today. Pass: current streak 3, best streak 6, both shown. Default: major (blocker if no streak shown at all).
H12 Weekday-schedule streak. Setup: "Gym" (Mon/Wed/Fri) checked on Fri 16, Mon 19, Wed 21 Oct (scheduled days only). Pass: current streak 3 (unscheduled days do not break it). Default: major.
H13 N-per-week streak, current week counts only once met. Setup: "Swim" 2/week, checked Tue 6 + Wed 7 Oct and Tue 13 + Wed 14 Oct, then Tue 20 Oct only. Pass: current streak 2 (counted in weeks, not days); after also checking Wed 21 Oct (via heatmap or clock) it becomes 3. (Check-in days chosen so Mon-start and Sun-start weeks give the same answer.) Default: major.
H14 Heatmap: 12 weeks, one cell per day, today at the end. Test: count day cells for one habit and read the last cell's label. Pass: 78-91 day cells (12 weeks with a partial week allowed); the last enabled cell is today. Default: major (blocker if no heatmap).
H15 [F] Clicking a past heatmap cell toggles that day. Test: click the cell for D-3 on "Stretch", then click it again. Pass: the cell becomes done and the streak recomputes (with H11 data: current 9, best 9), then the second click makes it not done again (current 3, best 6). Default: blocker.
H16 Future cells disabled. Test: if any cells after today are shown, click one. Pass: no future cells, or they are disabled (disabled/aria-disabled) and clicking changes nothing. Default: major.
H17 Accessible cell label like "Mon 3 Mar: done". Test: read aria-label (or accessible name) of a done and a not-done cell. Pass: names weekday, day, month and state, and the state word changes on toggle. Default: major.
H18 [F] Edit dialog: name, colour, schedule. Test: open edit on "Read", change name to "Read more", colour, and schedule to weekdays Mon-Fri; save. Pass: all three changes shown. Default: blocker.
H19 Changing the schedule recomputes streaks. Setup: daily habit "Floss" checked D-2 (Tue 20) and today (Thu 22), not D-1. Read current streak (1 expected for daily). Edit schedule to weekdays Tue+Thu. Pass: current streak becomes 2 without reload. Default: major.
H20 [F] Archive and restore. Test: archive "Walk"; check Today and an Archived section; restore it. Pass: hidden from Today, listed in Archived, back on Today after restore, check-ins kept. Default: blocker.
H21 Delete asks with native confirm(); dismiss does nothing. Test: delete "Walk" and dismiss -> still there; delete again and accept -> gone. Pass: a native confirm both times, dismiss keeps it, accept removes it. Default: major (blocker if dismiss deletes).
H22 [F] Undo button covers check, uncheck, edit, archive, delete. Test: for each of the five actions in turn: do it, click Undo. Pass: each action is reversed exactly. Default: blocker if Undo never works; major if one or more of the five types is not undone.
H23 Ctrl+Z undoes (focus on the page, not in a text field). Test: check a habit, press Control+Z. Pass: check reversed. Default: major.
H24 Undo depth 10. Test: do 11 check/uncheck actions on the heatmap or Today, then press Undo 10 times. Pass: the 10 most recent actions are reversed in order, the 1st stays; an 11th Undo changes nothing and raises no error. Default: major.
H25 Undo toast names what was undone. Test: watch the page after each Undo in H22. Pass: a short toast appears naming the action (e.g. "Undid check-in 'Read'"). Default: major.
H26 Arrow keys move between habit rows on Today. Test: focus the first row, press ArrowDown, ArrowUp. Pass: focus moves to the next/previous habit row. Default: major.
H27 Space toggles the focused habit. Test: focus a row (via arrows), press Space. Pass: that habit's today state toggles (once, not twice). Default: major.
H28 N opens the add form. Test: focus body, press "n" (and "N"). Pass: add form opens with focus in it; typing "n" inside a text field does not open it. Default: major.
H29 [F] Export all data as JSON. Test: click export. Pass: a file downloads; it parses as JSON and contains every habit and its check-in dates. Default: blocker.
H30 [F] Import merges by name, union of check-ins. Test: edit the exported file: add a check-in date to an existing habit, add one new habit; import it. Pass: no duplicate habit; the existing habit has old+new check-ins; the new habit is added. Default: blocker if no import; major if the merge rule is wrong.
H31 Bad import shows an error and changes nothing. Test: import a non-JSON text file and a JSON file of the wrong shape ({"foo":1}). Pass: an error is shown both times and data are unchanged. Default: major (blocker if data are lost).
H32 Check-in just before midnight belongs to that day. Test: set clock to Thu 22 Oct 23:59:30, check "Read", then let the clock pass midnight and reload. Pass: Thu 22 Oct shows done in the heatmap/label; Fri 23 Oct starts not done. Default: major.
H33 Today rolls over across midnight within a minute with the page open. Test: open at 23:59:00 with "Read" checked; run the clock to 00:01:10 without reload. Pass: Today now shows Fri 23 Oct (Read not done). Default: major.
H34 Habits not due today are not mixed with due ones after rollover. Test: after H33 (now Friday), "Gym" (Mon/Wed/Fri) is in the due group. Pass: the due/not-due split follows the new day. Default: major.
H35 Empty state (habits). Test: first load with empty storage. Pass: Today shows a friendly empty state that says what to do next (e.g. "No habits yet - add one"). Default: major.

## INVOICE (invoice.md) - 40 items

I01 [F] Business profile in a settings dialog. Test: open settings, set name "Northwind Studio", address, tax id "GB123", default currency EUR, default tax rate 20, save, reload, reopen. Pass: all five fields kept. Default: blocker.
I02 Profile used on every new invoice. Test: create a new invoice after I01. Pass: currency defaults to EUR, a new line's tax defaults to 20, and the business name appears on the invoice (editor or print view). Default: major.
I03 [F] Add client. Test: add client "Acme, Inc." with email "billing@acme.test". Pass: listed. Default: blocker.
I04 Client name required. Test: save a client with an empty name. Pass: refused with an inline message. Default: major.
I05 Email validated if given. Test: email "bad@" -> refused inline; a client with no email -> accepted. Pass: both. Default: major.
I06 [F] Edit client. Test: rename a client "Beta LLC" to "Beta Ltd". Pass: new name shown in clients list and on its invoices. Default: blocker.
I07 Deleting a client used by an invoice is refused with an inline explanation. Test: delete "Acme, Inc." after an invoice uses it. Pass: not deleted, an explanation is shown inline (not only an alert, no confirm needed). Default: major (blocker if the client is deleted and its invoices lose their client).
I08 Deleting an unused client asks with native confirm(); dismiss does nothing. Test: delete an unused client, dismiss -> kept; again, accept -> removed. Default: major (blocker if dismiss deletes).
I09 [F] Invoices list columns. Test: with 2+ invoices, read the list. Pass: number, client, issue date, due date, total and status visible per invoice (at 1280). Default: blocker if no list; major if a column is missing.
I10 Overdue is derived. Setup: invoice A Sent, due 15 Oct 2026; invoice B Draft, due 15 Oct; invoice C Sent, due 30 Oct. Pass: A shows Overdue, B shows Draft, C shows Sent. Default: major.
I11 Filter by status. Test: filter Draft, Sent, Paid, Overdue in turn. Pass: each filter shows exactly the matching invoices (Overdue shows A; Sent shows C, and A only if the build treats Overdue as a kind of Sent). Default: major.
I12 Search by client or number. Test: search "acme" and the number of invoice C. Pass: only matching invoices shown each time. Default: major.
I13 Sort by date and by total. Test: sort by date, then by total (both directions where offered). Pass: list order matches the values. Default: major.
I14 Number auto-increments per year, format like 2026-0007. Test: create two invoices. Pass: numbers are 2026-NNNN with the second one 1 higher than the first. Default: major.
I15 Number editable but unique. Test: change invoice 2's number to invoice 1's number. Pass: refused or marked invalid with a message; the duplicate is not saved. Default: major.
I16 Due date not before issue date. Test: issue 22 Oct, due 20 Oct. Pass: refused or marked invalid with a message. Default: major.
I17 Currency choices: USD, EUR, GBP, INR, JPY. Test: open the currency control. Pass: all five offered. Default: major.
I18 [F] Line items can be added and removed. Test: add 3 lines, remove the middle one. Pass: the right line is gone and totals update. Default: blocker.
I19 Line description required. Test: clear a line's description. Pass: marked invalid with a message. Default: major.
I20 Quantity positive, up to 2 decimals. Test: qty 0, -1, 1.234. Pass: each refused or marked invalid (rounding 1.234 to 1.23 with a visible change also passes; silently keeping 3 decimals in the total fails). Default: major.
I21 Unit price non-negative; discount 0-100. Test: price -5; discount 101 and -1. Pass: each refused or marked invalid. Default: major.
I22 Reorder lines with Alt+Up / Alt+Down. Test: focus a field in line 2, press Alt+ArrowUp, then Alt+ArrowDown. Pass: the line moves up, then back down; focus stays with the moved line. Default: major.
I23 Reorder lines by drag. Test: drag line 3 above line 1 (Playwright drag, then manual mouse down/move/up if needed). Pass: the order changes. Default: major.
I24 Exact money math, half away from zero, per line. Setup in USD: line 1 "Design" qty 0.5 x 2.01, 0% discount, 0% tax; line 2 "Hosting" qty 3 x 19.99, 10% discount, 20% tax; line 3 "Support" qty 2 x 12.50, 0% discount, 5% tax. Pass: line 1 = $1.01 (not $1.00); total discount $6.00; tax 20% = $10.79; tax 5% = $1.25; subtotal $85.98 (before discount) or $79.98 (after discount); grand total $92.02. Default: major.
I25 Tax grouped per rate. Test: read the totals block of I24. Pass: separate rows for 20% and 5% (a 0% row is optional). Default: major.
I26 JPY has no minor unit. Setup: invoice in JPY, one line qty 3 x 1234, 0% discount, 10% tax. Pass: subtotal ¥3,702, tax ¥370, total ¥4,072, no decimals anywhere. Default: major.
I27 Intl formatting with symbol and grouping. Test: a USD line qty 1 x 1234567.5. Pass: shown as $1,234,567.50 (Intl.NumberFormat style); INR and GBP/EUR use their own symbols. Default: major.
I28 Changing currency reformats without changing numbers. Test: on the I24 invoice switch USD -> EUR -> GBP. Pass: grand total reads €92.02 then £92.02; line values unchanged. Default: major.
I29 [F] Mark as sent. Test: on a Draft, mark as sent. Pass: status Sent in editor and list. Default: blocker.
I30 [F] Mark as paid with a paid date. Test: mark invoice as paid. Pass: status Paid and a paid date is asked for or recorded and shown. Default: blocker if absent; major if no paid date.
I31 Paid is read-only until reopened. Test: after I30 try to edit a line and the client. Then reopen. Pass: edits blocked while Paid; a reopen action exists and editing works after it. Default: major.
I32 [F] Duplicate. Test: duplicate the paid invoice. Pass: new invoice with a new number, issue date 22 Oct 2026 (today; due date today or today + the original term), status Draft, same lines. Default: blocker if absent; major if a stated property is wrong.
I33 Delete invoice asks with native confirm(); dismiss does nothing. Test: dismiss -> kept; accept -> removed. Default: major (blocker if dismiss deletes).
I34 Print view. Test: emulate print media on an invoice with lines. Pass: buttons and navigation hidden, single column, the totals block has break-inside: avoid (or page-break-inside: avoid) in print CSS. Default: major (blocker if no @media print at all).
I35 [F] Autosave as you type. Test: type in a line description, wait 2 s, reload without any save click. Pass: the edit is kept. Default: blocker (data loss).
I36 "Saved" indicator with last save time. Test: after an edit. Pass: an indicator says saved with a time. Default: major.
I37 Leaving with an invalid field keeps the draft and marks the field. Test: clear a line description, go back to the list, reopen the invoice. Pass: the invoice still exists with its other edits, and the empty field is marked invalid. Default: major.
I38 CSV export. Test: export with invoices from I10/I24/I26 present. Pass: a file downloads; the first line is exactly number,client,issue_date,due_date,currency,total,status; one row per invoice; parses with a standard CSV parser to 7 fields per row (client "Acme, Inc." quoted); totals in major units with a dot (92.02; JPY 4072). Default: major (blocker if no CSV export).
I39 [F] JSON export and import. Test: export JSON, load it into a fresh profile with import. Pass: profile, clients and invoices restored. Default: blocker.
I40 Bad JSON import rejected, nothing changed. Test: import a non-JSON file and {"foo":1}. Pass: error shown, data unchanged. Default: major (blocker if data are lost).

## TRIP (trip.md) - 31 items

T01 [F] Create a trip. Test: name "Lisbon", start 1 Nov 2026, end 4 Nov 2026, travellers Ana, Ben, Cy. Pass: trip shown with 4 days. Default: blocker.
T02 Dates: end not before start; 1-30 days. Test: end before start; a 31-day range; a 1-day trip (start = end). Pass: first two refused with a message, third accepted. Default: major.
T03 Travellers 1-8, unique. Test: 0 travellers; a 9th traveller; a duplicate name ("ana" vs "Ana" counts as duplicate only if the build says so; exact duplicate "Ana" must be refused). Pass: 0 refused, 9th refused/prevented, exact duplicate refused. Default: major.
T04 [F] Rename a trip. Test: rename "Lisbon" to "Lisbon & Porto". Pass: new name shown and kept on reload. Default: blocker.
T05 Delete trip asks with native confirm(); dismiss does nothing. Test: dismiss -> kept; accept -> removed. Default: major (blocker if dismiss deletes).
T06 One column per day; horizontal scroll inside the board. Test: a 10-day trip at 1280 and the 4-day trip at 375. Pass: one column per day; when columns do not fit, the board scrolls horizontally while the page itself does not. Default: major.
T07 [F] Add an activity. Test: day 1: "Lunch", 12:30, 60 min, place "Time Out Market", Food, cost 45. Pass: shown in day 1 with its details and Food icon. Default: blocker.
T08 Title required. Test: save with empty title. Pass: refused with an inline message. Default: major.
T09 Duration 15-minute steps, 15 min to 12 h. Test: try 0, 10, 20 min and 12 h 15 min; then 15 min and 12 h. Pass: the first four refused or not offerable; 15 min and 12 h accepted. Default: major.
T10 Five categories, each with its own icon. Test: open the category control; add one activity per category. Pass: Food, Sight, Transport, Stay, Other offered; 5 different icons shown. Default: major.
T11 Cost is optional. Test: add an activity with no cost. Pass: accepted. Default: major.
T12 Sorted by start time. Test: in day 2 add 15:00, then 09:00, then 12:00; then edit 09:00 to 16:00. Pass: order 09,12,15 then 12,15,16. Default: major.
T13 [F] Overlaps flagged on both items with text. Test: day 1 "Lunch" 12:30 60 min, "Museum" 13:00 90 min, and "Coffee" 11:30 60 min (ends exactly when Lunch starts). Pass: Lunch and Museum both show a visible marker and text naming the other (e.g. "overlaps Museum 13:00-14:30"); Coffee (ends 12:30) is not flagged against Lunch. Default: blocker if no conflict detection; major if one side, the text, or the back-to-back case is wrong.
T14 [F] Move by drag and drop. Test: drag "Museum" from day 1 to day 3 (Playwright drag, then manual mouse steps if needed). Pass: it moves. Default: blocker.
T15 [F] Move without a mouse: "Move to..." menu. Test: by keyboard, open "Move to..." on an activity and pick day 2. Pass: it moves. Default: blocker.
T16 Moving keeps the start time and re-checks both days. Test: after T14/T15, read start time and conflict markers in both days; move an activity into a day where it overlaps. Pass: time unchanged; old day's conflict cleared; new overlap flagged. Default: major.
T17 Shortening the trip keeps activities. Setup: an activity on day 4. Change end to 2 Nov. Pass: it moves to an "Unscheduled" tray and a message says how many moved (1). Default: major (blocker if the activity is lost).
T18 [F] Detail dialog edits every field, with multi-line notes. Test: open an activity; change title, time, duration, place, category, cost; notes "line 1\nline 2"; save; reopen. Pass: all saved, notes keep the line break. Default: blocker if no dialog; major if a field cannot be edited.
T19 Paid by one traveller; Split between at least one. Test: set Paid by Ana; Split between none -> refused; Split between Ana+Ben -> saved. Pass: all. Default: major.
T20 Dialog closes by button, Escape and backdrop click. Test: each of the three. Pass: all three close it. Default: major.
T21 Delete inside the dialog with native confirm(). Test: dismiss -> kept; accept -> removed. Default: major (blocker if dismiss deletes).
T22 [F] Budget: total, per category, per day. Setup: costs 45 (Food, day 1), 30 (Transport, day 2), 25 (Food, day 2). Pass: total 100.00; Food 70, Transport 30; day 1 45, day 2 55. Default: blocker if no budget panel; major if a number is wrong.
T23 Settle-up table. Setup: travellers Ana, Ben, Cy; only these costs: 100.00 paid by Ana split Ana+Ben+Cy; 30.00 paid by Ben split Ben+Cy. Pass: paid Ana 100.00, Ben 30.00, Cy 0.00; shares sum to exactly 130.00, each within 0.01 of exact (Ana 33.33/33.34, Ben 48.33/48.34, Cy 48.33/48.34); 2 transfers (Ben -> Ana and Cy -> Ana) that settle everyone to exactly 0.00; amounts to 2 decimals. Default: major (blocker if no settle-up).
T24 [F] Undo and redo buttons. Test: add an activity, Undo (gone), Redo (back). Pass: both work. Default: blocker.
T25 Ctrl+Z and Shift+Ctrl+Z. Test: focus on the page, not a text field. Pass: both work. Default: major.
T26 Undo depth 20. Test: 21 changes (e.g. add 21 activities or edits), then Undo 20 times. Pass: the 20 most recent reversed, the 1st stays. Default: major.
T27 Search by title or place; highlight; non-matching days collapse. Test: search "market" (place) and "museum" (title). Pass: matches highlighted; days with no match collapse. Default: major.
T28 .ics export. Test: export with 3+ scheduled activities. Pass: file downloads; BEGIN:VCALENDAR; one VEVENT per scheduled activity; DTSTART clock time equals the activity start (floating local time or TZID; a UTC "Z" time that does not equal the same instant is a fail); end = start + duration. Default: major (blocker if no .ics export).
T29 [F] JSON export and import of the whole trip. Test: export, then import into a fresh profile. Pass: trip with days, activities, travellers restored. Default: blocker.
T30 Bad JSON import rejected with an error, nothing changed. Test: non-JSON file and {"foo":1}. Pass: error shown, data unchanged. Default: major (blocker if data lost).
T31 Empty state. Test: first load with empty storage. Pass: a friendly empty state saying what to do next (create a trip). Default: major.

---------------------------------------------------------------------
## GENERAL (applied to every build) - 18 items

G01 No uncaught errors or console errors during the whole run. Pass: zero pageerror and zero console "error" messages. Default: major per distinct root cause, blocker if an error stops use (then counted on the item it breaks, per rule 3).
G02 No outside network requests. Test: log every request not to 127.0.0.1. Pass: none. Default: major.
G03 Works from a sub-folder with relative paths. Test: served at http://127.0.0.1:<port>/app/. Pass: CSS and JS load (no 404s). Default: blocker if the app does not load; major if an asset 404s but the app works.
G04 Data in localStorage under one key. Test: after the full run, list localStorage keys. Pass: exactly one key written by the app. Default: major.
G05 Corrupt or missing storage does not break the page. Test: fresh profile with the app's key set to "{not json" before load. Pass: page loads, no uncaught error, starts empty and says so (visible message). Default: major (blocker if the page does not render).
G06 Reload persistence. Test: after creating data, reload. Pass: all data and states kept. Default: blocker (data loss).
G07 1280x800 layout. Test: screenshots of main view, a dialog, and a filled list. Pass: no horizontal page overflow, no clipped or overlapping text. Default: minor.
G08 375x812 layout. Test: same views at 375. Pass: no horizontal page scroll (document scrollWidth <= 376), no clipped or overlapping text. Default: minor.
G09 375 px fully usable. Test: at 375, do the spec's main create action and open each main panel/dialog. Pass: every main action reachable and usable. Default: blocker if a spec feature cannot be reached at 375; major if usable only with difficulty (e.g. a control off-screen inside a dialog that cannot scroll).
G10 Touch targets at least 40 px at 375. Test: measure bounding boxes of visible buttons, inputs, selects and links in the main view and one dialog. Pass: every one is >= 40 px in both directions (an inline text link inside a sentence is exempt). Default: minor.
G11 Keyboard reach. Test: Tab through the page (up to 250 stops) from the top, then into the main dialog. Pass: every main action of the spec is reachable and operable with Enter/Space. Default: major (blocker if a spec feature can only be used with a mouse; a spec-required mouse-only path like drag is exempt when its keyboard twin exists).
G12 Visible keyboard focus. Test: Tab to buttons and inputs; compare focused vs unfocused computed outline/box-shadow/border. Pass: a visible change on every focused control checked. Default: major.
G13 Labelled inputs. Test: every visible input/select/textarea has an accessible name (label, aria-label or aria-labelledby; placeholder alone does not count). Default: major.
G14 Dialogs trap focus and return it. Test: open the main dialog, Tab past the last control and Shift+Tab before the first; close it. Pass: focus stays inside; after close it returns to the opener. Default: major.
G15 prefers-reduced-motion respected. Test: CSS contains a prefers-reduced-motion rule that reduces motion, or the app has no animations/transitions. Default: major.
G16 Contrast at least 4.5:1. Test: compute contrast for visible text (not disabled, not placeholder) over its solid background in the main view at 1280. Pass: every sampled text >= 4.5:1. Default: major.
G17 Colour is never the only signal. Test: states such as done/not done, status, conflict, invalid field also carry text, icon or shape. Default: major.
G18 Design-system basics stated in the spec. Test: CSS custom properties define the palette; icons are inline SVG; CSS has :hover, :active, :disabled and :focus-visible (or :focus) styles for buttons. Pass: all present. Default: minor.

## Totals
Habits 35 items, Invoice 40 items, Trip 31 items, General 18 items (applied to every build).
Per build tested: habits 53, invoice 58, trip 49.
