#!/usr/bin/env python3
"""ns_print_recheck.py - steer of 2026-10-19: re-run the three no-skill invoice builds (NS_B03, NS_B06, NS_B07) through the FROZEN
scorer with their FROZEN adapters (scorer/adapters/B03.py, B06.py, B07.py), once as frozen ("frozen") and once with a wrapper that fires
window 'beforeprint' before the frozen print_probe and 'afterprint' after it ("beforeprint"). Nothing frozen is edited; the wrapper only
wraps print_probe. usage: python3 ns_print_recheck.py <noskill_dir> <out_dir> <mode: frozen|beforeprint>"""
import sys, os, asyncio, importlib.util, time
HERE=os.path.dirname(os.path.abspath(__file__))
SCORER=os.environ.get('SCORER_DIR') or os.path.join(HERE,'..','scorer')
sys.dont_write_bytecode=True; sys.path.insert(0,os.path.abspath(SCORER))
import run_build
def load(path,name):
    sp=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
async def main(nsdir,out,mode):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br=await pw.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
        for lbl in ['NS_B03','NS_B06','NS_B07']:
            A=load(os.path.join(SCORER,'adapters',lbl.replace('NS_','')+'.py'),f'ns_{lbl}_{mode}')
            if mode=='beforeprint':
                orig=A.print_probe
                async def pp(R,evdir,_o=orig):
                    await R.pg.evaluate("()=>window.dispatchEvent(new Event('beforeprint'))")
                    r=await _o(R,evdir)
                    await R.pg.evaluate("()=>window.dispatchEvent(new Event('afterprint'))")
                    return r
                A.print_probe=pp
            spec=open(f'{nsdir}/{lbl}/SPEC.txt').read().strip(); t0=time.time()
            res=await run_build.run_build(br,lbl,spec,A,nsdir,out)
            print(f"{lbl} {mode} {time.time()-t0:.0f}s main_run_error={res.get('main_run_error')} probe_error={res.get('probe_error')}",flush=True)
        await br.close()
if __name__=='__main__':
    asyncio.run(main(sys.argv[1],sys.argv[2],sys.argv[3]))
