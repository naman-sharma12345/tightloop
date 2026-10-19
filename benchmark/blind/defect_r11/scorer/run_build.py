"""run_build.py - runs one build: spec steps (steps_<spec>.py) + GENERAL probes. Writes results/<label>.json and evidence screenshots.
usage (async, from a driver): await run_build(browser, label, spec, adapter_module, builds_dir, out_dir)"""
import os, json, asyncio, importlib, tempfile
import common
async def _fresh(browser, url, **kw):
    log=common.newlog(); R=await common.Run().start(browser,url,log,**kw); return R,log
async def run_build(browser, label, spec, A, builds_dir, out_dir):
    steps=importlib.import_module(f'steps_{spec}')
    ev=f'{out_dir}/evidence/{label}'; os.makedirs(ev,exist_ok=True)
    srv=common.Srv(f'{builds_dir}/{label}'); out={'label':label,'spec':spec}; items={}
    try:
        # ---- main run at 1280x800 ----
        R,log=await _fresh(browser,srv.url)
        try:
            await asyncio.wait_for(steps.run(R,A,out,ev),timeout=420)
        except Exception as e:
            out['main_run_error']=repr(e)[:500]
        items.update(out.get('items',{}))
        pg=R.pg
        # GENERAL probes on the filled app
        try:
            items['G04']={'auto':None,'ev':'localStorage keys: '+json.dumps(await pg.evaluate("()=>Object.keys(localStorage)"))}
            out['storage_keys']=await pg.evaluate("()=>Object.keys(localStorage)")
            await pg.evaluate("()=>window.scrollTo(0,0)")
            p1280=await common.general_probe(R,'1280 filled'); out['probe1280']=p1280
            await R.shot(f'{ev}/g07_1280_main.png')
            await R.pg.screenshot(path=f'{ev}/g07_1280_full.png', full_page=True)
            css=await pg.evaluate(common.JS_CSS); out['css']=css
            items['G15']={'auto':bool(css['reduced']) or not css['anim'],'ev':f"reduced-motion rule {css['reduced']}, has transitions/animations {css['anim']}"}
            items['G18']={'auto':css['vars']>=5 and css['svg']>0 and css['hover'] and css['active'] and css['disabled'] and css['focus'],'ev':json.dumps({k:css[k] for k in ['vars','svg','hover','active','disabled','focus','imgs']})}
            items['G16']={'auto':p1280['n_low']==0,'ev':f"low-contrast texts at 1280: {p1280['n_low']} {p1280['low_contrast'][:12]}"}
            items['G13']={'auto':len(p1280['unlabelled'])==0,'ev':f"unlabelled inputs (main view): {p1280['unlabelled'][:10]}"}
            walk=await common.tab_walk(pg,250); out['tabwalk']=walk
            items['G11']={'auto':None,'ev':f'{len(walk)} tab stops: '+' ; '.join(walk[:80])}
            n,bad=await common.focus_ring_check(pg,15)
            items['G12']={'auto':len(bad)==0 and n>0,'ev':f'checked {n} focused controls; without visible change: {bad}'}
            # dialog probes (main dialog chosen by adapter)
            try:
                dp=await A.dialog_probe(R)
                items['G14']={'auto':None,'ev':str(dp)[:600]}
                await R.shot(f'{ev}/g07_1280_dialog.png')
                pdlg=await common.general_probe(R,'1280 dialog'); out['probe1280_dialog']=pdlg
                items['G13']['ev']+=f" | in dialog: {pdlg['unlabelled'][:10]}"
                if pdlg['unlabelled']: items['G13']['auto']=False
                await A.close_dialog(R)
            except Exception as e:
                items['G14']={'auto':None,'ev':'dialog probe error '+repr(e)[:300]}
        except Exception as e:
            out['probe_error']=repr(e)[:400]
        # accept-delete + export path for fresh import
        try:
            if hasattr(steps,'run_delete_accept'): items[f'{spec[0].upper()}_delete_accept']=await steps.run_delete_accept(R,A)
        except Exception as e: items[f'{spec[0].upper()}_delete_accept']={'auto':None,'ev':'error '+repr(e)[:200]}
        keys=out.get('storage_keys',[])
        main_log=dict(log); await R.close()
        # ---- import into a fresh profile ----
        if out.get('json_export') and hasattr(steps,'run_import_fresh'):
            R,log2=await _fresh(browser,srv.url)
            try: items['IMPORT_FRESH']=await asyncio.wait_for(steps.run_import_fresh(R,A,out['json_export']),timeout=60)
            except Exception as e: items['IMPORT_FRESH']={'auto':None,'ev':'error '+repr(e)[:300]}
            for k in log2: main_log[k]=main_log[k]+log2[k]
            await R.close()
        # ---- 375x812 run (G08-G10, G09 usability flow) ----
        R,log3=await _fresh(browser,srv.url,w=375,h=812)
        try:
            await R.shot(f'{ev}/g08_375_empty.png')
            fl=await asyncio.wait_for(steps.flow375(R,A,ev),timeout=120)
            items['G09']={'auto':None,'ev':str(fl)[:600]}
        except Exception as e:
            items['G09']={'auto':None,'ev':'375 flow error '+repr(e)[:300]}
        try:
            await R.pg.evaluate("()=>window.scrollTo(0,0)")
            p375=await common.general_probe(R,'375 filled'); out['probe375']=p375
            await R.shot(f'{ev}/g08_375_main.png'); await R.pg.screenshot(path=f'{ev}/g08_375_full.png', full_page=True)
            items['G08']={'auto':None,'ev':f"375 overflow {p375['overflow']} (pass needs scrollWidth<=376); see screenshots"}
            items['G10']={'auto':p375['n_small']==0,'ev':f"{p375['n_small']} controls under 40px at 375: {p375['small_targets'][:12]}"}
            try:
                await A.dialog_probe(R); await R.shot(f'{ev}/g08_375_dialog.png')
                pd=await common.general_probe(R,'375 dialog'); out['probe375_dialog']=pd
                items['G10']['ev']+=f" | dialog: {pd['n_small']} {pd['small_targets'][:8]}"
                if pd['n_small']: items['G10']['auto']=False
                items['G08']['ev']+=f" | dialog overflow {pd['overflow']}"
                await A.close_dialog(R)
            except Exception as e: items['G08']['ev']+=' dialog error '+repr(e)[:200]
        except Exception as e:
            out['probe375_error']=repr(e)[:300]
        for k in log3: main_log[k]=main_log[k]+log3[k]
        await R.close()
        # ---- G05 corrupt storage ----
        if keys:
            R,log5=await _fresh(browser,srv.url,init_storage={k:'{not json' for k in keys})
            t=await R.text(); await R.shot(f'{ev}/g05_corrupt.png')
            items['G05']={'auto':None,'ev':f'pageerrors {log5["pageerror"]}; console {log5["console"][:3]}; text: '+t[:400].replace(chr(10),' | ')}
            await R.close()
        else:
            items['G05']={'auto':None,'ev':'no storage key found after the run'}
        # ---- logs ----
        items['G01']={'auto':not main_log['pageerror'] and not main_log['console'],'ev':f"pageerrors {main_log['pageerror'][:5]}; console errors {main_log['console'][:5]}"}
        items['G02']={'auto':not main_log['outside'],'ev':f"outside requests {main_log['outside'][:5]}"}
        items['G03']={'auto':not main_log['http'],'ev':f"HTTP>=400 {main_log['http'][:5]}"}
        out['dialogs']=main_log['dialogs']
    finally:
        srv.close()
    out['items']=items
    json.dump(out,open(f'{out_dir}/results/{label}.json','w'),indent=1)
    return out
