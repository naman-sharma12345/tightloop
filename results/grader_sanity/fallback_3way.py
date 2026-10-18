#!/usr/bin/env python3
# Grader-fallback 3-way (no agent, no harness edit): fresh checkout at start_commit via runner.prepare,
# apply a REAL agent's test-file hunk (from a pass-3 row's saved diff) so the same rename/fallback path is exercised,
# plus one input (empty / upstream fix nontest / planted wrong), then runner.rename_colliding_tests + runner.grade, unchanged.
import os, sys, json, subprocess, shutil, time, datetime, re
B='/home/user/tab/work/tightloop_bench'
sys.path.insert(0,B+'/benchmark')
import runner
GS=B+'/results/grader_sanity'; cache='/home/user/tab/work/tl_tools/tl-cache'
TD='/home/user/tab/tasks/55470a11-e536-4597-955f-c2989d5151e4'
AGENT={'gin-01':('diffs/gin-01_no-skill_1_attempt4.diff','recovery_test.go'),
       'fd-01':('diffs/fd-01_no-skill_1_attempt6.diff','tests/tests.rs'),
       'gin-02':('diffs/gin-02_no-skill_1_attempt4.diff','response_writer_test.go')}
def file_part(diff, path):
    out=[]; keep=False
    for l in open(diff).read().splitlines(True):
        if l.startswith('diff --git '):
            keep = l.strip().endswith(' b/'+path)
        if keep: out.append(l)
    return ''.join(out)
res=[]
for tid in sys.argv[1].split(','):
    dpath, tfile = AGENT[tid]
    hunk = file_part(os.path.join(B,'results',dpath), tfile)
    hp = os.path.join(TD, f'{tid}_agent_testhunk.patch'); open(hp,'w').write(hunk)
    for inp,exp in (('empty','fail'),('upstream_fix_nontest','pass'),('wrong_plausible','fail')):
        task=runner.load_task(tid); wt=runner.prepare(task, cache)
        try:
            r=subprocess.run(['git','apply',hp],cwd=wt,capture_output=True,text=True); assert r.returncode==0,(tid,'agent hunk',r.stderr)
            if inp!='empty':
                pf=os.path.join(GS,f'{tid}_{inp}.patch')
                r=subprocess.run(['git','apply',pf],cwd=wt,capture_output=True,text=True); assert r.returncode==0,(tid,inp,r.stderr)
            nontest = subprocess.run(['git','diff','--name-only','HEAD'],cwd=wt,capture_output=True,text=True).stdout.split()
            renamed=runner.rename_colliding_tests(task, wt)
            t0=time.time(); log=os.path.join(TD,f'fb3_{tid}_{inp}.grade')
            reset=[]; result,stat=runner.grade(task, wt, 900, log, reset)
            # after grade: is the non-test change still in the tree?
            after = subprocess.run(['git','diff','--name-only','HEAD'],cwd=wt,capture_output=True,text=True).stdout.split()
            txt=open(log+'.stdout').read()+open(log+'.stderr').read()
            lines=[l.strip() for l in txt.splitlines() if re.match(r'^(test result:|ok\s|FAIL|--- FAIL|--- PASS|error\[|error:|panic)',l.strip())]
            rec={"task":tid,"input":inp,"agent_test_hunk":f"{dpath}::{tfile}","expected":exp,"result":result,"ok":result==exp,
                 "renamed":[x['to'] for x in renamed],"hidden_patch_fallback":"yes" if reset else "no","reset_files":reset,
                 "changed_before_grade":nontest,"changed_at_grade":after,"check_command":task['check_command'],
                 "result_lines":lines[:8],"seconds":round(time.time()-t0,1),"at":datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
        finally:
            shutil.rmtree(wt, ignore_errors=True)
        res.append(rec); print(json.dumps(rec), flush=True)
        json.dump(res, open(os.path.join(TD,'fallback_3way_'+sys.argv[1].replace(',','_')+'.json'),'w'), indent=2)
print('DONE', flush=True)
