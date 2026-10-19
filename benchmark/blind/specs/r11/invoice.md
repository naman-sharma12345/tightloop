# r11 spec: invoice builder

Build an invoice builder in the browser.

Function:
- Business profile (name, address, tax id, default currency, default tax rate) edited once in a settings dialog and used
  on every new invoice.
- Clients: add, edit and delete clients (name required, email validated if given). Deleting a client used by an invoice
  is refused with an inline explanation; otherwise it asks first with the native `confirm()` and does nothing when dismissed.
- Invoices list: number, client, issue date, due date, total and status (Draft, Sent, Paid, Overdue). Overdue is derived:
  Sent and past the due date. Filter by status, search by client or number, sort by date or total.
- Invoice editor: invoice number (auto-incremented per year, e.g. 2026-0007, editable but must stay unique), client,
  issue and due dates (due must not be before issue), currency (USD, EUR, GBP, INR, JPY) and line items. Each line item:
  description (required), quantity (positive, up to 2 decimals), unit price (non-negative), per-line discount percent
  (0-100) and a tax rate. Lines can be added, removed and reordered by keyboard (Alt+Up / Alt+Down) as well as by drag.
- Totals: subtotal, total discount, tax grouped per rate, and grand total. Money math is exact: use integer minor units
  (JPY has no minor unit), round each line half away from zero, and format every amount with the currency's own symbol and
  digit grouping (Intl.NumberFormat). Changing the currency reformats everything without changing the numbers.
- Status actions: Mark as sent, Mark as paid (with a paid date), Duplicate (new number, today's dates, Draft) and Delete
  (native `confirm()` first). A Paid invoice is read-only until reopened.
- Print view: a clean, single-column printable invoice via a print stylesheet (`@media print`): no buttons or navigation,
  the totals block never splits across pages.
- Autosave: edits save as you type; a small "Saved" indicator shows the last save time. Leaving the editor with an invalid
  field keeps the draft and marks the field.
- Export the invoices list as CSV with the header `number,client,issue_date,due_date,currency,total,status` (amounts in
  major units with a dot decimal separator), and export/import everything as JSON (bad files rejected, nothing changed).

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
