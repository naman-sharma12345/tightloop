#!/usr/bin/env python3
"""Token-sink mining over the stream-json transcripts of every pass-2/pass-3 row that has a log
(superseded rows included: this is a cost anatomy, not a median). Writes results/token_sinks.md.
Estimates: chars/3.6 per token for visible text; a tool result or visible output added before API call k
is re-read (as cache_read) by every later call, so its cost = tokens x (calls after it).
The fixed prefix = first call's input+cache_read+cache_creation (CLI system prompt, tool schemas,
appended SKILL.md, task prompt), re-read by every call. Output split uses the row's exact output total;
hidden thinking = row output minus visible output estimate."""
import json, re, os, collections, statistics, sys
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CH=3.6
def classify(name, inp):
    if name=="Bash":
        c=inp.get("command","")
        if "gate.sh" in c: return "gate.sh run output"
        if re.search(r"\b(cargo test|go test|cargo build|go build|go vet|cargo check)\b",c): return "test/build run output"
        if re.search(r"(<<|git apply|perl -0?pi|sed -i|python3? -)",c) and "sed -n" not in c: return "scripted-edit output"
        if re.search(r"\b(sed -n|cat |head|tail|nl )",c): return "file views (sed -n/cat ranges)"
        if re.search(r"\b(rg|grep|find|ls|git grep)\b",c): return "search output (rg/grep/ls)"
        if "git diff" in c or "git status" in c: return "git diff/status output"
        return "other bash output"
    if name=="Read": return "Read ranged" if ("limit" in inp or "offset" in inp) else "Read whole file"
    if name in ("Edit","MultiEdit"): return "Edit tool result"
    if name=="Write": return "Write (scratch/contract file)" if not re.search(r"\.(rs|go|py|ts|js)$",inp.get("file_path","")) else "Write source"
    return "tool:"+name
def mine(path):
    calls=[]; seen={}; events=[]; pending={}; reads=collections.Counter()
    for l in open(path):
        if not l.strip().startswith("{"): continue
        o=json.loads(l)
        if o.get("type")=="assistant":
            m=o["message"]; mid=m["id"]
            if mid not in seen: seen[mid]=len(calls); calls.append({"usage":m.get("usage",{}),"text":0,"tool":0})
            ci=seen[mid]
            for c in m["content"]:
                if c["type"]=="text": calls[ci]["text"]+=len(c["text"])
                elif c["type"]=="tool_use":
                    calls[ci]["tool"]+=len(json.dumps(c["input"])); cat=classify(c["name"],c["input"]); pending[c["id"]]=(cat,ci); reads[cat]+=1
        elif o.get("type")=="user" and isinstance(o["message"].get("content"),list):
            for c in o["message"]["content"]:
                if c.get("type")=="tool_result":
                    cc=c.get("content"); s=cc if isinstance(cc,str) else json.dumps(cc)
                    cat,ci=pending.get(c.get("tool_use_id"),("?",len(calls)-1)); events.append((ci+1,cat,len(s)))
    return calls,events,reads
rows=[json.loads(l) for l in open(os.path.join(W,"results/rows.jsonl"))]
per=collections.defaultdict(list)
for r in rows:
    if r.get("pass") not in (2,3) or r.get("result") not in ("pass","fail"): continue
    lp=os.path.join(W,"results",r["logs"].replace(".*",".agent.stdout"))
    if not os.path.exists(lp): continue
    calls,events,reads=mine(lp); n=len(calls)
    if not n: continue
    u0=calls[0]["usage"]; prefix=u0.get("cache_read_input_tokens",0)+u0.get("cache_creation_input_tokens",0)+u0.get("input_tokens",0)
    d=collections.defaultdict(float); d["_calls"]=n; d["_prefix"]=prefix
    d["fixed prefix x calls"]=prefix*n
    for ci,cat,ch in events: d["re-read: "+cat]+=ch/CH*(n-ci)
    vt=sum(c["tool"] for c in calls)/CH; vf=calls[-1]["text"]/CH; vm=sum(c["text"] for c in calls[:-1])/CH
    for i,c in enumerate(calls): d["re-read: own earlier output"]+=(c["tool"]+c["text"])/CH*(n-1-i)
    out=r["tokens"]["output"]
    d["out: hidden thinking"]=max(0,out-vt-vf-vm); d["out: tool inputs (commands, edit payloads)"]=vt; d["out: final report"]=vf; d["out: mid-run text/plan"]=vm
    d["_out"]=out; d["_cc"]=r["tokens"]["cache_creation"]; d["_cr"]=r["tokens"]["cache_read"]; d["_io"]=r["tokens"]["input"]+out
    for k,v in reads.items(): d["n: "+k]+=v
    per[r["arm"]].append((r["task"],r["pass"],d))
arms=["no-skill","ponytail","tightloop-v3","tightloop-v4","tightloop-v4a","tightloop-v4b"]
med=lambda xs: statistics.median(xs) if xs else 0
out=["# Token sinks per arm (mined from run transcripts)","",
"Source: every pass-2 and pass-3 row with a transcript (superseded rows included: this is cost anatomy, not a benchmark median). Script: results/analysis/token_sinks.py.",
"Method: visible text = chars/3.6 tokens (estimate). A tool result or visible output added before API call k is re-read by every later call (cache_read), so its cost = tokens x calls after it. Fixed prefix = first call's input+cache_read+cache_creation (CLI system prompt + tool schemas + appended SKILL.md + task prompt), re-read by every call. Output split uses each row's exact output total; hidden thinking = output minus visible estimate. Values are medians per run.",""]
out.append("## Per-arm shape (median per run)"); out.append("")
out.append("| arm | runs | API calls | fixed prefix/call | cache_read | in+out | output | hidden thinking | cache_creation |")
out.append("|---|---|---|---|---|---|---|---|---|")
for a in arms:
    v=[d for _,_,d in per[a]]
    if not v: continue
    out.append(f"| {a} | {len(v)} | {med([d['_calls'] for d in v])} | {med([d['_prefix'] for d in v]):.0f} | {med([d['_cr'] for d in v]):.0f} | {med([d['_io'] for d in v]):.0f} | {med([d['_out'] for d in v]):.0f} | {med([d['out: hidden thinking'] for d in v]):.0f} | {med([d['_cc'] for d in v]):.0f} |")
out.append("")
RULE={
 "fixed prefix x calls":("number of API calls; SKILL.md bytes are appended to the system prompt, so they ride every call","v4 steps 1-5 are 4-5 separate calls (look, edit, gate, sometimes skeptic rerun, report); the 1984 B SKILL.md is ~550 tokens on every call (v3's 12053 B ~3.3k)"),
 "re-read: file views (sed -n/cat ranges)":("step 1 'sed -n the ranges around the hits' (no size cap) + re-looks","ranges of 100-140 lines (e.g. sed -n 80,215p = 6.3 KB) re-read by every later call"),
 "re-read: own earlier output":("tool inputs/edit payloads stay in context","python heredoc edit scripts carry old+new text"),
 "out: hidden thinking":("deliberation per call; more calls = more thinking","not addressable by text directly; fewer decision points"),
 "out: tool inputs (commands, edit payloads)":("step 2 edit style (python heredoc rewriting blocks) and long commands","edit scripts restate surrounding code"),
 "re-read: gate.sh run output":("step 3 gate prints test tails + the full diff","diff re-printed after the agent already wrote it"),
 "out: final report":("step 5 'at most 4 lines'","~200-370 tokens"),
 "re-read: test/build run output":("no-skill/v3 run tests separately before/after","v4 folds it into the gate"),
 "re-read: scripted-edit output":("edit scripts that print diffs","echoing the diff after editing"),
}
for a in ["tightloop-v4","tightloop-v4a","tightloop-v4b","no-skill"]:
    v=[d for _,_,d in per[a]]
    if not v: continue
    keys=sorted({k for d in v for k in d if not k.startswith(("_","n: "))}, key=lambda k:-med([d.get(k,0) for d in v]))
    tot=med([d['_cr']+d['_io'] for d in v])
    out.append(f"## Ranked sinks: {a} (median per run; in+out+cache_read median {tot:.0f})"); out.append("")
    out.append("| rank | sink | tokens/run | which rule causes it |"); out.append("|---|---|---|---|")
    for i,k in enumerate(keys,1):
        m=med([d.get(k,0) for d in v])
        if m<1: continue
        rr=RULE.get(k,("",""))
        out.append(f"| {i} | {k} | {m:.0f} | {rr[0]}{'; '+rr[1] if rr[1] else ''} |")
    cnt=collections.Counter()
    for d in v:
        for k in d:
            if k.startswith("n: "): cnt[k[3:]]+=d[k]
    out.append(""); out.append("Tool calls by kind (total over runs): "+", ".join(f"{k} {int(c)}" for k,c in cnt.most_common())); out.append("")
ns=[d for _,_,d in per["no-skill"]]; pre=med([d["_prefix"] for d in ns])
out+=["## What this means for the 40% floor (arithmetic, not a measurement)","",
f"- in+out+cache_read is about API calls x the fixed prefix (no-skill prefix median {pre:.0f} tokens per call; the CLI system prompt and tool schemas are most of it and no skill text can remove them). Everything a skill controls inside a run (file views, gate output, edit payloads, report) is under 10% of it.",
f"- So 40% of no-skill on in+out+cache_read needs roughly 40% of no-skill's calls. Per task no-skill's call count is in the rows (fd-01 ~6-9, gin-01 ~4, gin-02 ~5). A fix needs at least 3 calls (look, edit+gate, report), which is about 40% only where no-skill uses 7+ calls (fd-01). On gin-01/gin-02 the floor implies 1.6-2 calls, below what any proven fix can take; I expect it to stay missed there and will report it as missed, not explain it away.",
"- in+out is mostly output: hidden thinking (~45-55%), tool inputs/edit payloads, final report. 40% of no-skill in+out is ~1000-1300 tokens, so v4c has to cut calls (fewer decisions = less thinking), edit payloads and the report together.",
"- SKILL.md is appended to the system prompt, so its bytes ride every call: v4 1984 B (~550 tokens x calls), v4c 978 B.","",
"## Rules removed or merged in v4c (benchmark/arms/tightloop-v4c/SKILL.md, 978 B; gate.sh and phases/ byte-identical to v4)","",
"| v4 rule | sink it drives | v4c |","|---|---|---|",
"| steps 2 and 3 are separate calls (edit, then gate) | +1 call = +~30k cache_read | edits and the gate run in ONE Bash call |",
"| step 4 skeptic pass, then rerun the gate | the only extra gate run seen (fd-01 v4, comment-only change) | no rerun; the boundary/error check happens before writing the edit |",
"| step 1 sed -n ranges with no size cap | rank-2 sink (file views re-read every call) | ranged reads only, 20-40 lines, no whole-file reads, no cat |",
"| step 5 report in at most 4 lines | 200-370 output tokens | 3 lines, no tool calls after the gate |",
"| 'aim to finish in about 5' | 4-6 calls observed | 'finish in 3 calls' with the per-call cost stated |",
"| contract/plan/notes files | none observed in v4 (rule already 'no plan, notes or todo files') | kept as one short line |",
"| risky.md read before editing (a separate step) | never read so far (0 reads) | read inside call 1 when it applies, so it adds no call |",""]
open(os.path.join(W,"results/token_sinks.md"),"w").write("\n".join(out)+"\n")
print("\n".join(out))
