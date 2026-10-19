#!/usr/bin/env python3
"""make_scores.py - turn the per-build verdict files (verdicts/Bxx.json, written by the scorer after reading
the evidence in results/Bxx.json + screenshots) into DEFECTS_r11_ns.jsonl and SCORES_r11_ns.jsonl.
usage: python3 make_scores.py   (run inside benchmark/blind/defect_r11/)"""
import json, os, statistics
HERE=os.path.dirname(os.path.abspath(__file__)); VD=os.path.join(HERE,'verdicts')
W={'blocker':10,'major':3,'minor':1}
labels=sorted(f[:-5] for f in os.listdir(VD) if f.endswith('.json'))
defects=[]; scores=[]
for lbl in labels:
    v=json.load(open(os.path.join(VD,f'{lbl}.json'))); items=v['items']
    cnt={'blocker':0,'major':0,'minor':0}; score=0
    for k in sorted(items):
        x=items[k]
        if x['result']=='fail':
            assert W[x['severity']]==x['weight'], (lbl,k)
            cnt[x['severity']]+=1; score+=x['weight']
            defects.append({'label':lbl,'spec':v['spec'],'item':k,'severity':x['severity'],'weight':x['weight'],'evidence':x['evidence']})
        elif x['result']=='fail-shared-cause':
            defects.append({'label':lbl,'spec':v['spec'],'item':k,'severity':'shared-cause','weight':0,'evidence':f"counted once on {x['counted_on']}: "+x['evidence']})
    un=0
    for u in v.get('unlisted',[]):
        un+=u['weight']; defects.append({'label':lbl,'spec':v['spec'],'item':'unlisted','severity':u['severity'],'weight':u['weight'],'evidence':u['evidence']})
    passed=sum(1 for x in items.values() if x['result']=='pass')
    scores.append({'label':lbl,'spec':v['spec'],'items_tested':len(items),'items_passed':passed,'blocker':cnt['blocker'],'major':cnt['major'],'minor':cnt['minor'],'weighted_score':score,'unlisted_score':un})
with open(os.path.join(HERE,'DEFECTS_r11_ns.jsonl'),'w') as f:
    for d in defects: f.write(json.dumps(d,ensure_ascii=False)+'\n')
with open(os.path.join(HERE,'SCORES_r11_ns.jsonl'),'w') as f:
    for s in scores: f.write(json.dumps(s,ensure_ascii=False)+'\n')
for sp in sorted({s['spec'] for s in scores}):
    xs=[s['weighted_score'] for s in scores if s['spec']==sp]
    print(f"{sp}: median {statistics.median(xs)} mean {statistics.mean(xs):.2f} over {len(xs)} builds")
