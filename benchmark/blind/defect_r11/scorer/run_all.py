#!/usr/bin/env python3
"""run_all.py - reproduce the r11 defect-count evidence for every build with real browser clicks.
usage: python3 run_all.py <builds_dir> <out_dir> [B01 B02 ...]
needs: Python 3.11, playwright==1.63 (async API) with its chromium headless shell installed.
writes <out_dir>/results/<label>.json (per-item evidence, auto flags) and <out_dir>/evidence/<label>/ (screenshots, exports)."""
import sys, os, json, asyncio, importlib.util, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import run_build
SPEC={'B01':'trip','B08':'trip','B09':'trip','B02':'habits','B04':'habits','B05':'habits','B03':'invoice','B06':'invoice','B07':'invoice'}
def load_adapter(lbl):
    sp=importlib.util.spec_from_file_location(f"adapter_{lbl}", os.path.join(HERE,'adapters',f'{lbl}.py')); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
async def main(builds, out, labels):
    from playwright.async_api import async_playwright
    os.makedirs(f'{out}/results',exist_ok=True)
    async with async_playwright() as pw:
        br=await pw.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
        for lbl in labels:
            t0=time.time()
            res=await run_build.run_build(br,lbl,SPEC[lbl],load_adapter(lbl),builds,out)
            print(f"{lbl} {SPEC[lbl]} {time.time()-t0:.0f}s main_run_error={res.get('main_run_error')} probe_error={res.get('probe_error')}",flush=True)
        await br.close()
if __name__=='__main__':
    builds,out=sys.argv[1],sys.argv[2]; labels=sys.argv[3:] or sorted(SPEC)
    asyncio.run(main(builds,out,labels))
