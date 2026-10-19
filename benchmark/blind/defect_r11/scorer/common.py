"""common.py - shared harness for the r11 defect hunt (async Playwright).
Serves one build alone, fresh context per run, fixed clock/time zone/locale, blocks outside network,
logs console errors, page errors, HTTP>=400, native dialogs. Also the GENERAL (G) automated probes."""
import subprocess, time, shutil, os, json, tempfile, socket, asyncio, re
SERVE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"serve.py")  # no-cache static server, copied alongside
CLOCK='2026-10-22T10:00:00+05:30'
def free_port():
    s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p
class Srv:
    """copy build to <tmp>/app (SPEC.txt dropped) and serve <tmp> on 127.0.0.1"""
    def __init__(self,build_dir):
        self.tmp=tempfile.mkdtemp(prefix='dr11_'); shutil.copytree(build_dir,f"{self.tmp}/app")
        if os.path.exists(f"{self.tmp}/app/SPEC.txt"): os.remove(f"{self.tmp}/app/SPEC.txt")
        self.port=free_port()
        self.p=subprocess.Popen(['python3',SERVE,self.tmp,str(self.port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        time.sleep(0.6); self.url=f"http://127.0.0.1:{self.port}/app/"
    def close(self):
        self.p.kill(); self.p.wait(timeout=5); shutil.rmtree(self.tmp,ignore_errors=True)
def newlog(): return {'outside':[],'console':[],'pageerror':[],'http':[],'dialogs':[]}
class Run:
    async def start(self,browser,url,log,w=1280,h=800,clock=CLOCK,init_storage=None,reduced=False,dl_dir=None):
        self.log=log; self.confirm_answer=False; self.prompt_value=''; self.url=url; self.dl_dir=dl_dir or tempfile.mkdtemp(prefix='dr11dl_')
        self.c=await browser.new_context(viewport={'width':w,'height':h},timezone_id='Asia/Kolkata',locale='en-US',accept_downloads=True,reduced_motion='reduce' if reduced else 'no-preference')
        async def route(r):
            u=r.request.url
            if u.startswith('http://127.0.0.1') or u.startswith('data:') or u.startswith('blob:'): await r.continue_()
            else: log['outside'].append(u); await r.abort()
        await self.c.route('**/*',route)
        if init_storage is not None:
            await self.c.add_init_script("(()=>{if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');const s=%s;for(const k in s)localStorage.setItem(k,s[k]);}})()"%json.dumps(init_storage))
        self.pg=await self.c.new_page(); pg=self.pg; pg.set_default_timeout(4000)
        if clock: await pg.clock.install(time=clock)
        pg.on('console',lambda m: log['console'].append(m.text[:300]) if m.type=='error' else None)
        pg.on('pageerror',lambda e: log['pageerror'].append(str(e)[:300]))
        pg.on('response',lambda r: log['http'].append((r.status,r.url)) if r.status>=400 else None)
        async def dlg(d):
            log['dialogs'].append((d.type,d.message[:120]))
            if d.type=='confirm': await (d.accept() if self.confirm_answer else d.dismiss())
            elif d.type=='prompt': await d.accept(self.prompt_value)
            else: await d.accept()
        pg.on('dialog',lambda d: asyncio.ensure_future(dlg(d)))
        await pg.goto(url); await pg.wait_for_timeout(800)
        return self
    async def text(self): return await self.pg.evaluate("()=>document.body.innerText")
    async def shot(self,path): await self.pg.screenshot(path=path)
    async def download(self,click_coro_fn,timeout=5000):
        """run click; return saved path of the download or None"""
        try:
            async with self.pg.expect_download(timeout=timeout) as di:
                await click_coro_fn()
            d=await di.value; p=os.path.join(self.dl_dir,d.suggested_filename or 'download'); await d.save_as(p); return p
        except Exception as e:
            return None
    async def set_file(self,path,input_sel='input[type=file]'):
        await self.pg.locator(input_sel).first.set_input_files(path)
    async def close(self): await self.c.close()

# ---------- GENERAL automated probes (evidence; verdicts recorded per checklist) ----------
JS_OVERFLOW = "()=>{const x0=scrollX; scrollTo(99999,scrollY); const sx=scrollX; scrollTo(x0,scrollY); return {sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth, bw:document.body.scrollWidth, page_scrollable_x:sx}}"
JS_TARGETS = r"""()=>{const out=[];for(const e of document.querySelectorAll('button,input:not([type=hidden]),select,textarea,a[href],[role=button],[tabindex]:not([tabindex="-1"])')){
 const r=e.getBoundingClientRect(); const cs=getComputedStyle(e);
 if(r.width<=2||r.height<=2||cs.visibility==='hidden'||cs.display==='none') continue;
 if(e.closest('dialog:not([open])')) continue;
 if(e.tagName==='A' && cs.display==='inline' && e.closest('p,li')) continue;
 if(r.right<0||r.bottom<0||r.left>innerWidth) continue;
 let tw=r.width,th=r.height; if(e.tagName==='INPUT'&&(e.type==='checkbox'||e.type==='radio')){const l=e.closest('label')||(e.id&&document.querySelector('label[for="'+e.id+'"]')); if(l){const lr=l.getBoundingClientRect(); tw=Math.max(tw,lr.width); th=Math.max(th,lr.height);} }
 if(cs.opacity==='0' && !(e.tagName==='INPUT')) continue;
 {const a=getComputedStyle(e,'::after'), b=getComputedStyle(e,'::before'); for(const g of [a,b]){ if(g.content&&g.content!=='none'&&g.position==='absolute'){ let p=e.parentElement; while(p&&getComputedStyle(p).position==='static') p=p.parentElement; if(p){const pr=p.getBoundingClientRect(); tw=Math.max(tw,pr.width); th=Math.max(th,pr.height);} } } }
 if(tw<40||th<40) out.push((e.getAttribute('aria-label')||e.innerText||e.name||e.id||e.tagName).slice(0,30)+' '+Math.round(tw)+'x'+Math.round(th));}
 return out;}"""
JS_UNLABELLED = r"""()=>{const out=[];for(const e of document.querySelectorAll('input:not([type=hidden]),select,textarea')){
 const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); if(e.closest('dialog:not([open])')) continue;
 if(e.type==='file') continue;
 if((r.width===0||r.height===0) && !(e.type==='checkbox'||e.type==='radio')) continue;
 if(cs.display==='none') continue;
 const lab=(e.labels&&e.labels.length)||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.getAttribute('title');
 if(!lab) out.push(e.tagName+'#'+e.id+'.'+e.className+' type='+e.type+' ph='+(e.placeholder||''));}
 return out;}"""
JS_CONTRAST = r"""()=>{
 function parse(c){const m=c.match(/rgba?\(([^)]+)\)/); if(!m) return null; const p=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0],p[1],p[2],p.length>3?p[3]:1];}
 function lum(c){const a=c.slice(0,3).map(v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)});return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2];}
 function bg(e){let layers=[];while(e){const cs=getComputedStyle(e); if(cs.backgroundImage&&cs.backgroundImage!=='none') return null; const c=parse(cs.backgroundColor); if(c&&c[3]>0){layers.push(c); if(c[3]>=1) break;} e=e.parentElement;}
  let r=[255,255,255]; for(let i=layers.length-1;i>=0;i--){const c=layers[i];r=[0,1,2].map(k=>c[k]*c[3]+r[k]*(1-c[3]));} return r;}
 const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n; const seen=new Set();
 while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const e=n.parentElement; if(!e||seen.has(e)) continue; seen.add(e);
  const cs=getComputedStyle(e); const r=e.getBoundingClientRect(); if(r.width===0||r.height===0||cs.visibility==='hidden'||parseFloat(cs.opacity)===0) continue;
  if(e.closest('dialog:not([open]),[hidden],[aria-hidden=true],.sr-only,.visually-hidden')) continue;
  if(e.closest('button:disabled,[aria-disabled=true],input:disabled')) continue;
  if(r.bottom<0||r.top>innerHeight*3) continue;
  const fg=parse(cs.color); const b=bg(e); if(!fg||!b) continue;
  const f=[0,1,2].map(k=>fg[k]*fg[3]+b[k]*(1-fg[3]));
  const L1=lum(f),L2=lum(b); const cr=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
  if(cr<4.5) out.push(n.textContent.trim().slice(0,30)+' '+cr.toFixed(2));}
 return out;}"""
JS_CSS = r"""()=>{let txt='';for(const s of document.styleSheets){try{for(const r of s.cssRules) txt+=r.cssText+'\n';}catch(e){}} 
 return {reduced:/prefers-reduced-motion/.test(txt), anim:/(transition|animation)\s*:/.test(txt), vars:(txt.match(/--[a-zA-Z0-9-]+\s*:/g)||[]).length,
 hover:/:hover/.test(txt), active:/:active/.test(txt), disabled:/:disabled|\[disabled\]|aria-disabled/.test(txt), focus:/:focus-visible|:focus/.test(txt),
 print:/@media print/.test(txt), svg:document.querySelectorAll('svg').length, imgs:[...document.images].map(i=>i.src).slice(0,5)};}"""
async def tab_walk(pg, n=250):
    """press Tab n times from the top; return list of focused element descriptions"""
    await pg.evaluate("()=>{document.activeElement&&document.activeElement.blur(); window.scrollTo(0,0)}")
    out=[]
    for i in range(n):
        await pg.keyboard.press('Tab')
        d=await pg.evaluate("()=>{const e=document.activeElement; if(!e||e===document.body) return null; return (e.tagName+'|'+(e.getAttribute('aria-label')||e.innerText||e.value||e.placeholder||e.id||'').trim().slice(0,40)).replace(/\\n/g,' ')}")
        if d is None:
            if out and out[-1]=='<none>': break
            out.append('<none>'); continue
        if out and d==[x for x in out if x!='<none>'][0] and i>5: break
        out.append(d)
    return out
JS_FOCUS_VISIBLE = r"""async()=>{}"""
async def focus_ring_check(pg, max_n=12):
    """Tab through controls; for each focused control compare outline/box-shadow/border vs blurred (a ring drawn on the control's own ::before/::after counts). returns (checked, without_ring list)"""
    await pg.evaluate("()=>{document.activeElement&&document.activeElement.blur(); window.scrollTo(0,0)}")
    bad=[]; n=0
    for i in range(max_n*3):
        await pg.keyboard.press('Tab')
        r=await pg.evaluate(r"""()=>{const e=document.activeElement; if(!e||e===document.body) return null;
          const f=getComputedStyle(e); const fs=[f.outlineStyle,f.outlineWidth,f.outlineColor,f.boxShadow,f.borderColor,f.backgroundColor,f.textDecorationLine].join('|');
          const ps=['::before','::after'].map(p=>getComputedStyle(e,p)).filter(g=>g.content&&g.content!=='none');
          const pr=ps.some(g=>(g.outlineStyle!=='none'&&parseFloat(g.outlineWidth)>0)||g.boxShadow!=='none');
          return {d:(e.tagName+'|'+(e.getAttribute('aria-label')||e.innerText||e.id||'').trim().slice(0,30)), fs:fs, ow:(f.outlineStyle!=='none'&&parseFloat(f.outlineWidth)>0)||pr, bs:f.boxShadow!=='none'}}""")
        if r is None: break
        n+=1
        if not (r['ow'] or r['bs']):
            # compare to unfocused style
            same=await pg.evaluate(r"""(fs)=>{const e=document.activeElement; const c=e.cloneNode(true); e.parentNode.insertBefore(c,e.nextSibling); const g=getComputedStyle(c);
               const s=[g.outlineStyle,g.outlineWidth,g.outlineColor,g.boxShadow,g.borderColor,g.backgroundColor,g.textDecorationLine].join('|'); c.remove(); return s===fs}""", r['fs'])
            if same: bad.append(r['d'])
        if n>=max_n: break
    return n,bad
async def general_probe(R, tag):
    pg=R.pg
    o=await pg.evaluate(JS_OVERFLOW); t=await pg.evaluate(JS_TARGETS); u=await pg.evaluate(JS_UNLABELLED); c=await pg.evaluate(JS_CONTRAST)
    return {'tag':tag,'overflow':o,'small_targets':t[:40],'n_small':len(t),'unlabelled':u,'low_contrast':c[:40],'n_low':len(c)}
