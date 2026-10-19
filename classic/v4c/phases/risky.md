# Risky change: extra checks before and after editing

Before editing, in one Bash call: `rg -n "<function or type you change>"` for every caller, and the tests that cover them.
- Every caller must still be correct. Callers outside the task that change behaviour mean a smaller fix exists; look for it.
- Keep error handling and validation of any code you move.
- Concurrency: name the shared state and who locks it. No new lock without a test that would deadlock or race without it.
- Public API, CLI flag, file format, error text: keep it unless the task asks; if it must change, say so in the report.
- Data loss or security: the error path needs its own test.

After the gate passes, run the package's tests once, capped: `go test ./<pkg>/... 2>&1 | tail -20`, `cargo test -q 2>&1 | tail -20`, `pytest -q <dir> 2>&1 | tail -20`. Report failures you did not cause as pre-existing; do not fix them.
