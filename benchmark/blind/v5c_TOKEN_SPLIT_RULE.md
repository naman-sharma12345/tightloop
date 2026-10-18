# v5c TOKEN SPLIT RULE (written 2026-10-18T22:25:05Z, Naman m:ecfa8839)

Applied by `benchmark/blind/v5c_run/token_why_v5c.py` to ALL 10 v5c-round builds (9 tightloop-v5c + the ponytail expenses rerun),
read only from each build's stream-json log. Output: files/tl_blind/v5c/TOKEN_WHY.tsv (and results/blind_v5c_TOKEN_WHY.tsv).

## Disclosure
A first TOKEN_WHY.tsv was made before this rule was written down (22:12-22:23Z, 9 v5c builds only), in three generations:
(1) visible tokens counted on the JSON-escaped tool input (which overcounted, so the unattributed rest came out negative);
(2) counted on the raw input values;
(3) generation 2 plus a fix: app files written by absolute workspace path (/tmp/tlb-*/name) were not recognised, which put all of
bookmarks-1's calls into first pass. Whether any number changed between generation 3 and the output of this rule is stated in
v5c_RESULTS.md, build by build.

## Units
- Output total and thinking tokens: the harness result event (`usage.output_tokens`, `usage.output_tokens_details.thinking_tokens`).
  Thinking is its own column: the stream does not say which step it belongs to.
- Every assistant content block in the log (text or tool_use), de-duplicated, is one unit. Its visible output = tokens of its content as
  counted by the token-counting endpoint (no model run): for text, the text; for a tool_use, its input values joined by newlines;
  minus the endpoint's fixed overhead for a one-character message.
- visible_unattributed = output_total - thinking - sum of the units (rounding of the count, JSON framing of tool calls).

## App file
A file in the build's workspace root (a bare or relative name, or /tmp/tlb-<id>/<name>) with extension .html .htm .css .js .mjs .json .svg,
whose name does not contain test, spec, check, shot, probe or "kt.". A tool call WRITES an app file if it is Write/Edit/MultiEdit/NotebookEdit
on it, or a Bash command with `cat > F <<`, `cat >> F <<`, `tee F <<`, `sed -i ... F`, `open('F','w'|'a')`, `Path('F').write_text`, or `> F` / `>> F`.

## Verification pattern (click test / server / browser hunt / test assertions)
A tool call matches if its input contains any of: http.server, SimpleHTTPRequestHandler, `serve`, playwright, puppeteer, selenium, chromium,
chrome, headless, ms-playwright, `playwright install`, jsdom, assert, `node --check`, `node --test`, pytest, curl localhost/127.0.0.1,
or it runs a script file that was written earlier in the same build containing one of those words.

## Classes (each unit gets exactly one)
1. FIRST-PASS WRITE: every unit from the start of the session up to and including the end of the initial run of calls that create app files.
   The first pass ends at the first tool call that, after at least one app file exists, creates no NEW app file. A call inside the first
   pass that also runs checks stays first-pass and is counted in the column first_pass_calls_with_checks.
2. After the first pass, a tool call that writes or edits an app file: REWRITE-EDIT (if it also matches the verification pattern it stays
   REWRITE-EDIT and is counted in mixed_calls).
3. After the first pass, a tool call that matches the verification pattern: CLICK-TEST / VERIFICATION.
4. After the first pass, any other tool call (ls, cat, pkill, ...): OTHER TOOL.
5. Text blocks: before the first pass ends -> FIRST-PASS WRITE; after -> FINAL REPLY (this includes interim narration).

## Click-test facts per build
- clicktest_script: yes if any call runs a browser-automation script (playwright/puppeteer/selenium/chromium inline, or a script file
  written in the build containing one of them).
- browser_launched: for each such call, its tool result is read. "no" if the result contains "Executable doesn't exist",
  "BrowserType.launch", "Failed to launch", "ModuleNotFoundError", "Traceback" or "Error:" from the browser launch; the first error line is
  quoted. "yes" if at least one such call returned without those markers.
- features_clicked: the selectors / text targets in every `.click(`, `.dblclick(`, `.fill(`, `.check(`, `.drag_to(`, `.press(`,
  `.select_option(` call in the build's browser scripts (unique, in order). They count as clicked only where browser_launched is yes;
  otherwise the column shows what the script would have clicked.
- app files written or edited more than once; tool calls; first-pass tool calls.
