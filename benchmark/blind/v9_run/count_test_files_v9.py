#!/usr/bin/env python3
"""tightloop v9 P1 measure (v9_PREREG.md): shipped test files per build output folder, by the SAME TEST_RE as
blind_driver_v9.py (paths under .claude/ excluded: that is the harness-installed skill). Used for the base runs (v4c n=3 or v8 n=3)
and to re-check the v9 rows. Usage: count_test_files_v9.py <build output dir> [...] -> TSV: dir, n_test_files, files"""
import os, re, sys
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)tests?\.[A-Za-z0-9]+$|(^|/)tests?[_-][^/]*$|[._-](test|spec)\.[A-Za-z0-9]+$", re.I)
SKIP = {".git", "node_modules", "target"}
def test_files(d):
    out = []
    for dp, dns, fs in os.walk(d):
        dns[:] = [x for x in dns if x not in SKIP]
        for f in fs:
            p = os.path.relpath(os.path.join(dp, f), d)
            if not p.startswith(".claude/") and TEST_RE.search(p): out.append(p)
    return sorted(out)
if __name__ == "__main__":
    print("dir\tn_test_files\tfiles")
    for d in sys.argv[1:]:
        t = test_files(d); print(f"{d}\t{len(t)}\t{','.join(t)}")
