# ERRATA r11 (checklist 4c3b8e79 is frozen; these notes say how two items were scored against the spec)

The checklist file was not edited. Where its wording conflicts with the spec it was written from, the spec wins, and the same rule was applied to every build of that spec.

## H15 (habits) - expected numbers
- Checklist says: with the H11 data, after toggling D-3 on, current 9 and best 9.
- The H11 data checks D-9..D-4 and D-2..today, so adding D-3 makes D-9..today 10 days in a row: current 10, best 10.
- Scored as: pass = correct recompute (10/10 after the first click, back to 3/6 after the second click).

## I15 (invoice) - duplicate invoice number
- Checklist says: pass needs "the duplicate is not saved".
- Spec: "Leaving the editor with an invalid field keeps the draft and marks the field", so a duplicate number may be kept as a marked, invalid draft.
- Scored as: pass if the duplicate is refused OR clearly marked invalid with a message (kept as a flagged draft is allowed); fail only if it is accepted silently.
