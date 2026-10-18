# read-only investigation of the units builds (expects the 3 zips unzipped into /tmp/tlb_inv/A,B,C)

import sys, json, socket, subprocess, time, itertools
from playwright.sync_api import sync_playwright
D="/tmp/tlb_inv"; R={}
EXP={"Length":{"mm":.001,"cm":.01,"m":1,"km":1000,"in":.0254,"ft":.3048,"mi":1609.344},"Weight":{"g":1,"kg":1000,"oz":28.349523125,"lb":453.59237}}
def tc(v,u): return v if u=="C" else (v-32)*5/9 if u=="F" else v-273.15
def fc(c,u): return c if u=="C" else c*9/5+32 if u=="F" else c+273.15
def nums(t):
    import re; return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", t.replace(",",""))]
with sync_playwright() as p:
    b=p.chromium.launch()
    for lab in "ABC":
        out={"console":[], "pageerrors":[]}
        s=socket.socket(); s.bind(("127.0.0.1",0)); port=s.getsockname()[1]; s.close()
        srv=subprocess.Popen([sys.executable,"-m","http.server",str(port)],cwd=f"{D}/{lab}",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.8)
        for mode,url,js in [("http",f"http://localhost:{port}/",True),("file",f"file://{D}/{lab}/index.html",True),("nojs",f"http://localhost:{port}/",False)]:
            ctx=b.new_context(java_script_enabled=js, viewport={"width":1280,"height":800}); pg=ctx.new_page(); pg.set_default_timeout(3000)
            errs=[]; pg.on("console",lambda m: m.type in("error","warning") and errs.append(m.text[:150])); pg.on("pageerror",lambda e: errs.append("PAGEERROR "+str(e)[:150]))
            pg.goto(url); pg.wait_for_timeout(500)
            pg.screenshot(path=f"/home/user/tab/tasks/2a4ce3c5-0127-47bb-ac69-2a2747594489/logs/inv_units_{lab}_{mode}.png")
            m={"errors":errs,"from_options":pg.locator("#from option").count(),"result_text":pg.inner_text("#result")[:60] if pg.locator("#result").count() else None}
            if js:
                bad=[]; total=0
                for cat in ["Length","Weight","Temperature"]:
                    pg.select_option("#category",label=cat); pg.wait_for_timeout(100)
                    units=[o.get_attribute("value") for o in pg.locator("#from option").all()]
                    for f_,t_ in itertools.product(units,units):
                        pg.select_option("#from",value=f_); pg.select_option("#to",value=t_)
                        pg.click("#value", click_count=3); pg.keyboard.type("12.5"); pg.wait_for_timeout(40)
                        txt=pg.inner_text("#result"); total+=1
                        exp=fc(tc(12.5,f_),t_) if cat=="Temperature" else 12.5*EXP[cat][f_]/EXP[cat][t_]
                        if not any(abs(n-round(exp,4))<=max(1e-4,abs(exp)*1e-6) for n in nums(txt)): bad.append((cat,f_,t_,txt[:50],round(exp,4)))
                m["pairs_checked"]=total; m["pairs_wrong"]=bad[:8]; m["n_wrong"]=len(bad)
                # swap
                pg.select_option("#category",label="Length"); pg.select_option("#from",value="km"); pg.select_option("#to",value="mi")
                sw=pg.locator("#swap, button[aria-label*=wap i], button[title*=wap i]").first
                if sw.count()==0: sw=pg.locator("button").first
                sw.click(); pg.wait_for_timeout(100); m["swap"]=(pg.input_value("#from"),pg.input_value("#to"))
                # invalid / edge inputs
                ed={}
                for v in ["abc","","-40","1e3","0.1","1,5"]:
                    pg.click("#value", click_count=3); pg.keyboard.press("Backspace"); pg.keyboard.type(v); pg.wait_for_timeout(60)
                    ed[v]=(pg.input_value("#value"), pg.inner_text("#result")[:60])
                m["edge"]=ed
            out[mode]=m; ctx.close()
        srv.terminate(); srv.wait(); R[lab]=out
    b.close()
print(json.dumps(R,indent=1))
