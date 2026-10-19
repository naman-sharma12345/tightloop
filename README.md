# r11 no-skill calibration: blind judge input
9 builds in J01-J09 (labels shuffled; build order and run number hidden). Each folder: index.html, styles.css, app.js, SPEC.txt (which spec it built).
Specs: specs/ (sha256 pinned in rubric/PREREG_v11.md section 3). Rubric: rubric/PREREG_v11.md section 3 (file sha256 34949297c91f09c07c27e673187a7dde2cdbaa46a7a573292a26cf8b47b7e2bb, from v6/v11 2809200).
Judge each build alone, every feature clicked in a real browser, served locally with no network. 5 axes 0-10 with a one-line reason each; build score = mean of 5.
Output: judge/SCORES_r11_ns.jsonl, one line per label: label, spec, design, look, function, polish, code, 5 reasons, build_score, console_page_errors. Commit fast-forward to this branch, post commit hash + file sha256, then stop.
The key is held by Tab and not in this repo.
