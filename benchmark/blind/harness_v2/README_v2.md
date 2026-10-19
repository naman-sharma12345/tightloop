# APP HARNESS v2 (benchmark/blind/harness_v2/)

Binding: Pally m:de7a935c. The frozen app-round harness stays frozen (byte-identical, sha256 list below). The two fixes live
here, in a separate versioned copy. Comparisons use crash-free tokens only.

## The two v1 faults
1. prompt() (checker fault, not an app fault). checks/check_app.py line 37 answers every native dialog with dlg.accept() and
   no text, so window.prompt() returns "" and an app that skips an empty name does nothing. The check "every visible button
   changes page state" then fails. r2 kanban-C: 9/10, dead buttons ['+ Add column','✎','✎','✎'] (app.js:162
   prompt('Rename column', col.name), app.js:178 prompt('New column name')). Logged since 00:09Z Oct 19 in
   files/tl_blind/notes/KNOWN_CHECKER_BUG_prompt.md (v6c, v7, v4c-n3, v8, v9 kanban runs hit it too).
2. browser (build-sandbox fault). r2_run/sandbox_r2.py mounts an empty tmpfs on /home/user and binds back only
   tl-npm, go-dist, .cargo, .rustup. Playwright's browser is in /home/user/.cache/ms-playwright, so the building agent's
   own self-test crashed: "Executable doesn't exist at /home/user/.cache/ms-playwright/chromium_headless_shell-1243/..."
   Tool results with that crash: r2 kanban-A 1, kanban-B 1, kanban-C 2, bookmarks-A 1, bookmarks-C 2, expenses-A 1,
   expenses-C 2 (7 of 12 builds); v4c-n3 kanban-2 1, bookmarks-2 1, expenses-2 1, expenses-3 2 (4 of 6); v8 1 of 9; v9 4 of 9.
   The checker is not affected (it runs on the host); the agent's tokens are (retries, installs).

## The fixes (one each)
- check_app_v2.py = check_app.py + dialogs answered the way a real user would and logged in out.json ("dialogs",
  "dialog_counts", "dialogs_total"; each entry: type, message, default, answer, check in progress).
  prompt: OK with typed text (a number for amount/price/count, a URL for url/link, today for date, else the default
  edited as default + " 2", else "Test item"). Why not the bare default: on r2 kanban-C a variant that accepts the bare
  default still scores 9/10 with the 3 rename buttons dead (renaming "To do" to "To do" changes nothing), see
  selftest/SELFTEST_v2.txt. confirm: OK, except Cancel where a check asks for it (the delete-cancel checks, as in v1).
  alert: dismissed (one button; closes the same way). Nothing else in the checks changed.
- sandbox_v2.py = sandbox_r2 with prefix patched in the importing process only: one extra
  `--ro-bind /home/user/.cache/ms-playwright /home/user/.cache/ms-playwright` (read-only; browser binaries only, no keys).
  The hardened probe (run_probe) calls prefix too, so every isolation check before a build runs with the same bind.
- blind_driver_v2.py = v9_run/blind_driver_v9.py with the v2 sandbox and checker, one arm per run (no-skill,
  tightloop-v4c, tightloop-v11), the plan from ORDER_v2.json, no cutoff, its own hold ("appv2"), and two new row columns:
  browser_crash_events (tool results with a browser-launch failure; expected 0) and harness.
- rescore_v2.py: runs check_app_v2.py over SAVED outputs and writes v1 and v2 scores side by side (for v4c, v8, v9).
- orders/ORDER_v2.<n>.json: the committed rerun queue (not run). The driver uses the highest n; a pushed ORDER file is never
  edited. Each build pins its spec by path + sha256; the driver refuses a placeholder ("TBD") or a changed spec.

## Self-test (no builds, no model calls), on ONE r2 build output: work/tl_blind_out/r2/kanban/C
See selftest/SELFTEST_v2.txt for the full output. Summary:
- checker v1 (frozen) re-run: 9/10, dead ['+ Add column','✎','✎','✎'] (same as the saved r2 row).
- checker v2: 10/10, dead [], 9 dialogs logged: prompt OK x4 ('Test item', 'To do 2', 'In progress 2', 'Done 2'),
  confirm OK x4, confirm Cancel x1 (the delete-cancel check, which still passes).
- browser inside the sandbox, same app: v1 prefix launch FAILED "Executable doesn't exist ..."; v2 prefix launch ok,
  title "Kanban board", 15 buttons, 0 page errors, browser bind not writable. SELFTEST PASS.
- no-regression pass: check_app_v2.py over all 12 r2 outputs vs their saved v1 scores (selftest/SELFTEST_v2.txt).

## Running it later (root's GO only)
1. git archive the v6/app-harness-v2 commit into /home/user/tab/work/tl_blind_appv2 and write its .snap_commit.
2. root writes /home/user/tab/files/tl_blind/appv2/START_OK and the hold /home/user/tab/work/tl_appv2_state/hold ("appv2").
3. orders/ORDER_v2.1.json already pins the 3 new specs habits/invoice/trip (copied byte for byte from v6/v11 2809200 to
   benchmark/blind/specs/r11/, path + commit + sha256). The baseline is no-skill on these, not on kanban/bookmarks/expenses.
4. python3 /home/user/tab/work/tl_blind_appv2/benchmark/blind/harness_v2/blind_driver_v2.py no-skill   (9 builds)
   then tightloop-v4c (9 builds), then tightloop-v11 once its arm folder is committed on top of this branch.
