# Gate failed: what to do

Fix only the line the gate names; rerun the same gate command. Two fails for the same reason: stop, report what you saw and your best hypothesis.

- PROVE FAIL (test passes without your change): the test misses the bug. Rebuild it from the exact input or call in the task, and assert the exact output the task expects. Do not weaken the fix to fit the test.
- PROVE UNKNOWN: the test lives in a file you listed as source, or the filter matched nothing. Check the filter matches your test name; if the test shares a file with the fix, prove it by hand once (revert the fix lines, run, restore).
- TEST FAIL: read only the first error. Compile error: fix that line. Wrong value: recheck your root-cause guess against the code, not the test. Never edit an existing test to make it pass unless the task changes that behaviour.
- FORMAT / WHITESPACE: run the formatter on that file only.
- debug? lines: remove them unless they are real behaviour.
