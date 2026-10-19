# ERRATA r11, round "arms" (new file; ERRATA_r11.md and the checklist are unchanged)

The existing errata H15 and I15 from ERRATA_r11.md were applied as written. ERRATA_r11.md has entries for H15 and I15 only. The round prompt mentions I28, but no I28 entry exists there; it is added below as a NEW entry for this round.

Where the checklist wording conflicts with the spec it was written from, the spec wins. The same rule was applied to every build of that spec.

## I28 (invoice) - how the switched currency must read
- Checklist says: after USD -> EUR -> GBP the grand total "reads €92.02 then £92.02".
- Spec (invoice.md): "format every amount with the currency's own symbol and digit grouping (Intl.NumberFormat). Changing the currency reformats everything without changing the numbers." The spec does not fix a locale, so a locale form of the same amount such as "92,02 €" is the currency's own symbol and grouping from Intl.NumberFormat.
- Scored as: pass if every amount keeps the same number (92.02, line values unchanged) and is shown with the new currency's own symbol through Intl formatting, whether the symbol leads or trails and whichever decimal mark the locale uses; fail if a number changes, the old symbol stays, or no symbol is shown.
- First met on: B02 (EUR shown as "92,02 €", GBP "£92.02"). Applied the same way to every invoice build.
- Builds it decided: B02, B05, B06, B11, B12 and B16 all show EUR as "92,02 €" (lines "1,01 €", "53,97 €", "25,00 €") and GBP as "£92.02", with the numbers unchanged. All pass under this erratum. No other item was affected.

No other new erratum was found in the final rerun, the frozen-probe print runs or the no-skill print recheck.
