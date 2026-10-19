#!/usr/bin/env python3
"""arms_run.py - driver for the "arms" round (18 labels). Uses the FROZEN scorer (run_build.py, common.py, steps_*.py, serve.py)
unchanged from ../scorer/ (the frozen ../scorer next to this folder, or SCORER_DIR); only the label list, the spec source (each build's SPEC.txt) and the
adapter folder differ from run_all.py. usage: python3 arms_run.py <builds_dir> <out_dir> [B01 ...]"""
import sys, os, asyncio, importlib.util, time
HERE=os.path.dirname(os.path.abspath(__file__))
SCORER=os.environ.get('SCORER_DIR') or os.path.join(HERE,'..','scorer')
sys.dont_write_bytecode=True; sys.path.insert(0,os.path.abspath(SCORER))
import run_build
def load_adapter(lbl):
    sp=importlib.util.spec_from_file_location(f"adapter_{lbl}", os.path.join(HERE,'adapters',f'{lbl}.py')); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
async def main(builds,out,labels):
    from playwright.async_api import async_playwright
    os.makedirs(f'{out}/results',exist_ok=True)
    async with async_playwright() as pw:
        br=await pw.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
        for lbl in labels:
            spec=open(f'{builds}/{lbl}/SPEC.txt').read().strip(); t0=time.time()
            res=await run_build.run_build(br,lbl,spec,load_adapter(lbl),builds,out)
            print(f"{lbl} {spec} {time.time()-t0:.0f}s main_run_error={res.get('main_run_error')} probe_error={res.get('probe_error')}",flush=True)
        await br.close()
if __name__=='__main__':
    builds,out=sys.argv[1],sys.argv[2]
    labels=sys.argv[3:] or sorted(d for d in os.listdir(builds) if os.path.exists(f'{builds}/{d}/SPEC.txt'))
    asyncio.run(main(builds,out,labels))
