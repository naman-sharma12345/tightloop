# same-port browser cache simulation (expects every zip unzipped into /tmp/tlb_inv2/<app>/A,B,C)

import sys, json, subprocess, time
from playwright.sync_api import sync_playwright
FB="/home/user/tab/files/tl_blind"; R={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for app in ["todo","notes","units"]:
      for how in ["goto","reload"]:
        ctx=b.new_context(viewport={"width":1280,"height":800}); pg=ctx.new_page(); pg.set_default_timeout(3000)
        errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        for lab in "ABC":
            srv=subprocess.Popen([sys.executable,"-m","http.server","8000"],cwd=f"/tmp/tlb_inv2/{app}/{lab}",stdout=open("/tmp/tlb_srv.log","w"),stderr=subprocess.STDOUT); time.sleep(0.8)
            errs.clear()
            if lab=="A" or how=="goto": pg.goto("http://localhost:8000")
            else: pg.reload()
            pg.wait_for_timeout(600)
            srv.terminate(); srv.wait(); time.sleep(0.3)
            hits=[l.split('"')[1].split()[1] for l in open("/tmp/tlb_srv.log") if '"GET' in l]
            R[f"{app}/{lab}/{how}"]={"fetched_from_server":hits,"page_errors":list(errs)}
            pg.screenshot(path=f"/home/user/tab/tasks/2a4ce3c5-0127-47bb-ac69-2a2747594489/logs/sim_{app}_{lab}_{how}.png")
        ctx.close()
    b.close()
print(json.dumps(R))
