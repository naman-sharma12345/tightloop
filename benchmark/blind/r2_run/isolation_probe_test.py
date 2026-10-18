
import sys, types, re, subprocess, os, json, tempfile
src=open("/home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3/blind_driver_r2.py").read()
start=src.index("CUR = {"); end=src.index("APPS = [")
ns={"os":os,"re":re,"subprocess":subprocess,"sys":sys,"json":json,"TD":"/home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3"}
exec("_rl=None\n"+src[start:end].replace("R.run_logged = _nice_rl",""), ns)
wt=tempfile.mkdtemp(prefix="tlb-"); subprocess.run(["git","init","-q"],cwd=wt); os.makedirs(wt+"/.claude/skills/tightloop"); open(wt+"/.claude/skills/tightloop/SKILL.md","w").write("x")
import time; t=time.time(); r=ns["isolation_check"](wt); print(round(time.time()-t,1), json.dumps(r))
open(wt+"/leak.txt","w").write("see check_app.py"); print("planted check_app text -> grep hits", json.dumps(ns["isolation_check"](wt)["grep_hits"]))
os.remove(wt+"/leak.txt"); open(wt+"/KEY_v2.json","w").write("{}"); r2=ns["isolation_check"](wt); print("planted KEY_v2.json file -> visible_in_sandbox", json.dumps(r2["visible_in_sandbox"]), "ok", r2["ok"])
import shutil; shutil.rmtree(wt)
