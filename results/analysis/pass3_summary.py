#!/usr/bin/env python3
"""Pass-3 summary (analysis only). Rows: pass 3, not superseded, result pass/fail.
Metrics: in+out; in+out+cache_read; cost-weighted = in*1 + out*5 + cache_read*0.1 + cache_creation*1.25.
Per arm per task: median and spread (max - min) across repeats (spread pre-registered in RUN_LOG).
Decision (Pally, pre-registered): for v4a / v4b, per task, compare the arm's median ratio vs the same-pass
no-skill median with v4's pass-2 ratio vs pass-2 no-skill; the drop must exceed the arm's spread expressed
as a ratio (arm spread / pass-3 no-skill median), on BOTH cost-weighted and in+out. Kept only if that holds."""
import json, statistics, sys
R="results/rows.jsonl"; O="results/pass3_order.jsonl"
rows=[json.loads(l) for l in open(R)]
order={}
try:
    for l in open(O):
        o=json.loads(l); order[o["tag"]]=o
except FileNotFoundError: pass
def cw(t): return t["input"]*1+t["output"]*5+t["cache_read"]*0.1+t["cache_creation"]*1.25
def io(t): return t["input"]+t["output"]
def iocr(t): return io(t)+t["cache_read"]
M={"in+out":io,"in+out+cache_read":iocr,"cost-weighted":cw}
p3=[r for r in rows if r.get("pass")==3 and not str(r.get("status","")).startswith("superseded") and r.get("result") in ("pass","fail")]
p2=[r for r in rows if r.get("pass")==2 and not str(r.get("status","")).startswith("superseded") and r.get("result") in ("pass","fail")]
arms=["no-skill","ponytail","tightloop-v3","tightloop-v4a","tightloop-v4b"]
tasks=sorted({r["task"] for r in p3})
print("ROWS (pass 3; time overlapped, not comparable)")
for r in p3:
    t=r["tokens"]; tag=r.get("logs","").replace("logs/","").replace(".*",""); o=order.get(tag,{})
    print(f"{r['task']} r{o.get('repeat','?')} pos{o.get('position','?')} {r['arm']}: {r['result'].upper()} in+out {io(t)} | in+out+cache_read {iocr(t)} | cost-weighted {cw(t):.2f} | turns {r.get('turns')} | tools {r.get('tool_calls')} | gate_runs {r.get('gate_runs')} gate_bytes {r.get('gate_output_bytes')} | fail.md {r['phase_reads'].get('fail.md')} risky.md {r['phase_reads'].get('risky.md')} | rename {r.get('rename_applied')} fallback {r.get('hidden_patch_fallback')} | {r.get('overlap')}")
print()
S={}
print("PER ARM PER TASK: median [min-max] spread")
for task in tasks:
    for a in arms:
        rs=[r for r in p3 if r["task"]==task and r["arm"]==a]
        if not rs: continue
        line=f"{task} {a} (n={len(rs)}, pass {sum(r['result']=='pass' for r in rs)}/{len(rs)}):"
        for k,f in M.items():
            v=[f(r["tokens"]) for r in rs]; med=statistics.median(v); sp=max(v)-min(v)
            S[(task,a,k)]=(med,sp,min(v),max(v))
            line+=f" {k} {med:.2f} [{min(v):.2f}-{max(v):.2f}] spread {sp:.2f};"
        tr=[r.get("turns") for r in rs]; tc=[r.get("tool_calls") for r in rs]
        line+=f" turns {tr} tools {tc} fail.md {[r['phase_reads'].get('fail.md') for r in rs]} risky.md {[r['phase_reads'].get('risky.md') for r in rs]}"
        print(line)
print()
print("MEDIAN RATIO vs same-pass no-skill (median over tasks of per-task median ratios)")
for a in arms[1:]:
    for k in M:
        rat=[S[(t,a,k)][0]/S[(t,"no-skill",k)][0] for t in tasks if (t,a,k) in S and (t,"no-skill",k) in S]
        if rat: print(f"{a} {k}: per-task {[round(x,4) for x in rat]} median {statistics.median(rat)}")
print()
print("DECISION (pre-registered rule)")
v4={}
for t in tasks:
    ns=[r for r in p2 if r["task"]==t and r["arm"]=="no-skill"]; v=[r for r in p2 if r["task"]==t and r["arm"]=="tightloop-v4"]
    if ns and v:
        for k,f in M.items(): v4[(t,k)]=f(v[0]["tokens"])/f(ns[0]["tokens"])
for a in ["tightloop-v4a","tightloop-v4b"]:
    ok_all=True; det=[]
    for k in ["cost-weighted","in+out"]:
        for t in tasks:
            if (t,k) not in v4:
                det.append(f"{t} {k}: no v4 pass-2 baseline on this task (new 4th task) -> descriptive only, not in the decision"); continue
            if (t,a,k) not in S: ok_all=False; continue
            med,sp,_,_=S[(t,a,k)]; nsmed=S[(t,"no-skill",k)][0]
            r_a=med/nsmed; r_4=v4[(t,k)]; drop=r_4-r_a; need=sp/nsmed
            ok=drop>need; ok_all&=ok
            det.append(f"{t} {k}: v4 pass-2 ratio {r_4:.4f}, {a} pass-3 ratio {r_a:.4f}, drop {drop:.4f} vs spread-as-ratio {need:.4f} -> {'beats spread' if ok else 'within spread / no drop'}")
    if a.endswith("v4a"):
        print(a, "token drop beats the spread on both metrics" if ok_all else "no change, keep v4", "- tokens only, quality unmeasured; never promoted to default (skeptic step stays a v4 rule)")
    else:
        print(a, "KEEP v4b (beats the spread on both metrics)" if ok_all else "no change, keep v4")
    for d in det: print("   ", d)
