#!/usr/bin/env python3
"""Cost-weighted token figure for pass-2 rows (analysis only; runner and score.py untouched).
Weights, relative to input = 1: input 1, output 5, cache_read 0.1, cache_creation 1.25.
cost_weighted = input*1 + output*5 + cache_read*0.1 + cache_creation*1.25
Ratios are raw (arm / no-skill and v4 / ponytail on the same task); headline = median of per-task ratios."""
import json, statistics, sys
rows=[json.loads(l) for l in open(sys.argv[1] if len(sys.argv)>1 else "results/rows.jsonl")]
rows=[r for r in rows if r.get("pass")==2 and r.get("result") in ("pass","fail") and not str(r.get("status","")).startswith("superseded")]
W={"input":1,"output":5,"cache_read":0.1,"cache_creation":1.25}
cw=lambda r: sum(r["tokens"][k]*w for k,w in W.items())
by={(r["task"],r["arm"]):r for r in rows}
tasks=sorted({r["task"] for r in rows}); arms=["no-skill","ponytail","tightloop-v3","tightloop-v4"]
rat={a:[] for a in arms[1:]}; v4p=[]
for t in tasks:
    ns=by[(t,"no-skill")]
    print(t+": "+", ".join(f"{a} {cw(by[(t,a)])}" for a in arms))
    for a in arms[1:]: rat[a].append(cw(by[(t,a)])/cw(ns))
    v4p.append(cw(by[(t,"tightloop-v4")])/cw(by[(t,"ponytail")]))
    print(f"  ratio vs no-skill: " + ", ".join(f"{a} {rat[a][-1]}" for a in arms[1:]) + f"; v4/ponytail {v4p[-1]}")
for a in arms[1:]: print(f"median cost-weighted ratio {a} / no-skill: {statistics.median(rat[a])} over {len(rat[a])} tasks")
print(f"median cost-weighted ratio tightloop-v4 / ponytail: {statistics.median(v4p)} over {len(v4p)} tasks")
