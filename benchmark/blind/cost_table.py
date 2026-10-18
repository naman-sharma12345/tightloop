#!/usr/bin/env python3
"""Blind round cost file: cost_table.py <rows.jsonl> <out_prefix>
Writes <out_prefix>.json and <out_prefix>.md: per app and per version, the build's real tokens (input, output, cache_read,
cache_creation, in+out, cost-weighted = in + 5*out + 0.1*cache_read + 1.25*cache_creation), tool calls, turns and wall time,
with tightloop-v4c on the line right after tightloop-v4 and its difference to v4 (v4c minus v4, and v4c / v4).
Keyed by VERSION, never by blind label. It lives OUTSIDE the viewer folder; the viewer never reads or shows it."""
import json, sys
rows_p, out = sys.argv[1], sys.argv[2]
ORDER = ["no-skill", "ponytail", "tightloop-v4", "tightloop-v4c"]
F = ["input", "output", "cache_read", "cache_creation", "in_out", "cost_weighted", "tool_calls", "turns", "wall_seconds"]
rows = [json.loads(l) for l in open(rows_p) if l.strip()]
num = lambda v: v if isinstance(v, (int, float)) else None
res = {"apps": {}, "fields": F, "note": "keyed by version, not by blind label; never read by the viewer"}
md = ["# Blind round cost file (by version; not shown in the viewer)", ""]
for app in sorted({r["app"] for r in rows}):
    by = {r["arm"]: r for r in rows if r["app"] == app}
    a = {}
    md += [f"## {app}", "", "| version | " + " | ".join(F) + " |", "|---|" + "---|" * len(F)]
    for arm in ORDER + sorted(set(by) - set(ORDER)):
        if arm not in by: continue
        a[arm] = {k: by[arm].get(k) for k in F}
        md.append(f"| {arm} | " + " | ".join("" if a[arm][k] is None else str(a[arm][k]) for k in F) + " |")
    if "tightloop-v4" in a and "tightloop-v4c" in a:
        d = {k: (round(a["tightloop-v4c"][k] - a["tightloop-v4"][k], 2) if num(a["tightloop-v4c"][k]) is not None and num(a["tightloop-v4"][k]) is not None else None) for k in F}
        q = {k: (round(a["tightloop-v4c"][k] / a["tightloop-v4"][k], 3) if num(a["tightloop-v4c"][k]) is not None and num(a["tightloop-v4"][k]) else None) for k in F}
        a["v4c_minus_v4"] = d; a["v4c_over_v4"] = q
        md.append("| v4c - v4 | " + " | ".join("" if d[k] is None else str(d[k]) for k in F) + " |")
        md.append("| v4c / v4 | " + " | ".join("" if q[k] is None else str(q[k]) for k in F) + " |")
    res["apps"][app] = a; md.append("")
json.dump(res, open(out + ".json", "w"), indent=1)
open(out + ".md", "w").write("\n".join(md) + "\n")
print(out + ".json", out + ".md")
