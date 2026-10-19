"""steps_invoice.py - checklist items I01-I40. Same steps/data/order for every invoice build; adapter holds locators."""
import json, os, re, csv, io
def res(auto,ev): return {'auto':auto,'ev':str(ev)[:800]}
LINES24=[('Design','0.5','2.01','0','0'),('Hosting','3','19.99','10','20'),('Support','2','12.50','0','5')]
async def run(R,A,out,evdir):
    pg=R.pg; r={}
    await R.shot(f'{evdir}/i_empty.png'); out['first_text']=(await R.text())[:400]
    # I01 settings
    s1=await A.settings_set(R,dict(name='Northwind Studio',address='1 Harbour St, Leeds',taxid='GB123',currency='EUR',taxrate='20'))
    await pg.reload(); await pg.wait_for_timeout(800)
    s2=await A.settings_read(R)
    r['I01']=res(None, f'save -> {s1}; after reload settings read {s2}')
    # I03-I05 clients
    c=[]
    c.append(await A.client_add(R,'Acme, Inc.','billing@acme.test'))
    c.append(await A.client_add(R,'','x@y.test'))
    c.append(await A.client_add(R,'BadMail','bad@'))
    c.append(await A.client_add(R,'Beta LLC',''))
    c.append(await A.client_add(R,'Gamma Co','gamma@g.test'))
    cl=await A.clients_list(R)
    r['I03']=res(any('Acme' in x for x in cl), f'add Acme -> {c[0]}; clients {cl}')
    r['I04']=res(None, f'empty name -> {c[1]}')
    r['I05']=res(None, f'bad@ -> {c[2]}; no email (Beta LLC) -> {c[3]}; clients {cl}')
    await R.shot(f'{evdir}/i03_clients.png')
    # I02 defaults on a new invoice (invoice #1)
    n1=await A.inv_new(R)
    d=await A.inv_read(R); await A.line_add_if_none(R); lt=await A.line_tax(R,0)
    bn=await A.business_name_visible(R)
    r['I02']=res(None, f'new invoice {n1}: fields {d}; new line tax {lt}; business name shown {bn}')
    # I24 exact math on invoice #1 in USD
    await A.inv_set(R,client='Acme, Inc.',currency='USD')
    await A.lines_fill(R,LINES24)
    tt=await A.totals_text(R); ll=await A.line_amounts(R)
    r['I24']=res(None, f'lines {LINES24}; line amounts {ll}; totals {tt}')
    r['I25']=res(None, f'totals block {tt}')
    await R.shot(f'{evdir}/i24_totals.png')
    # I28 currency switch
    await A.inv_set(R,currency='EUR'); te=await A.totals_text(R); le=await A.line_amounts(R)
    await A.inv_set(R,currency='GBP'); tg=await A.totals_text(R)
    await A.inv_set(R,currency='USD'); tu=await A.totals_text(R)
    r['I28']=res(None, f'EUR totals {te} lines {le}; GBP totals {tg}; back to USD {tu}')
    r['I17']=res(None, f'currency options {await A.currency_options(R)}')
    num1=await A.inv_number(R)
    # I14 numbering, I15 unique, I16 due>=issue on invoice #2 (scratch)
    n2=await A.inv_new(R); num2=await A.inv_number(R)
    r['I14']=res(None, f'first {num1}, second {num2}')
    e15=await A.inv_set(R,number=num1); er15=await A.editor_errors(R); await A.inv_back(R); rows=await A.list_rows(R)
    r['I15']=res(None, f'set #2 number to {num1} -> {e15}; errors {er15}; list rows after leaving {rows}')
    await A.open_inv(R, num2) or await A.open_inv_index(R,1)
    await A.inv_set(R,number=num2)
    e16=await A.inv_set(R,issue='2026-10-22',due='2026-10-20'); er16=await A.editor_errors(R)
    r['I16']=res(None, f'issue 22 Oct, due 20 Oct -> {e16}; errors {er16}')
    await A.inv_set(R,due='2026-11-05')
    # I18-I23 on invoice #2
    await A.inv_set(R,client='Gamma Co',currency='USD')
    await A.lines_fill(R,[('X','1','10','0','0'),('Y','1','20','0','0'),('Z','1','30','0','0')])
    l0=await A.line_descs(R); t0=await A.totals_text(R)
    await A.line_remove(R,1); l1=await A.line_descs(R); t1=await A.totals_text(R)
    r['I18']=res(None, f'lines {l0} totals {t0}; remove middle -> {l1} totals {t1}')
    await A.line_set(R,0,desc=''); e19=await A.line_invalid(R,0); await A.line_set(R,0,desc='X')
    r['I19']=res(None, f'empty description -> marked {e19}')
    e20=[]
    for q in ['0','-1','1.234']:
        await A.line_set(R,0,qty=q); e20.append((q, await A.line_invalid(R,0), await A.line_amounts(R)))
    await A.line_set(R,0,qty='1')
    r['I20']=res(None, f'qty tests {e20}')
    e21=[]
    for k,v in [('price','-5'),('disc','101'),('disc','-1')]:
        await A.line_set(R,0,**{k:v}); e21.append((k,v, await A.line_invalid(R,0), await A.line_amounts(R)))
        await A.line_set(R,0,price='10',disc='0')
    r['I21']=res(None, f'tests {e21}')
    await A.lines_fill(R,[('X','1','10','0','0'),('Z','1','30','0','0'),('W','1','40','0','0')])
    b=await A.line_descs(R); a1=await A.line_alt(R,1,'Up'); f1=await A.line_descs(R); a2=await A.line_alt(R,0,'Down'); f2=await A.line_descs(R)
    r['I22']=res(None, f'{b} -Alt+Up on line 2-> {f1} ({a1}) -Alt+Down on line 1-> {f2} ({a2})')
    dr=await A.line_drag(R,2,0); f3=await A.line_descs(R)
    r['I23']=res(None, f'drag line 3 above line 1 ({dr}) -> {f3}')
    # I27 grouping, INR
    await A.lines_fill(R,[('Big','1','1234567.5','0','0')]); g=await A.line_amounts(R); gt=await A.totals_text(R)
    await A.inv_set(R,currency='INR'); gi=await A.totals_text(R); await A.inv_set(R,currency='USD')
    r['I27']=res(None, f'USD 1x1234567.5 -> lines {g}, totals {gt}; INR totals {gi}')
    # I26 JPY invoice #3
    n3=await A.inv_new(R); await A.inv_set(R,client='Beta LLC',currency='JPY'); await A.lines_fill(R,[('Yen job','3','1234','0','10')])
    tj=await A.totals_text(R); lj=await A.line_amounts(R)
    r['I26']=res(None, f'JPY 3x1234 tax10 -> lines {lj}; totals {tj}')
    num3=await A.inv_number(R)
    # I35/I36 autosave + Saved indicator
    await A.line_set(R,0,desc='Yen job autosave'); await pg.wait_for_timeout(2000)
    si=await A.saved_indicator(R)
    await pg.reload(); await pg.wait_for_timeout(900)
    await A.open_inv(R,num3)
    ds=await A.line_descs(R)
    r['I35']=res(any('autosave' in x for x in ds), f'after typing + reload (no save click): lines {ds}')
    r['I36']=res(None, f'saved indicator text "{si}"')
    # I37 leave with invalid field
    await A.line_set(R,0,desc=''); await A.inv_back(R); rows=await A.list_rows(R); await A.open_inv(R,num3)
    ds=await A.line_descs(R); inv=await A.line_invalid(R,0); jt=await A.totals_text(R)
    r['I37']=res(None, f'cleared desc, left editor; list rows {rows}; reopened: lines {ds}, field marked {inv}, totals {jt}')
    await A.line_set(R,0,desc='Yen job')
    # I10 setup: A = invoice #1 Sent due 15 Oct; B = invoice #2 Draft due 15 Oct; C = new invoice #4 Sent due 30 Oct
    await A.open_inv(R,num1); await A.inv_set(R,issue='2026-10-01',due='2026-10-15'); s_a=await A.mark_sent(R)
    await A.open_inv(R,num2); await A.inv_set(R,issue='2026-10-01',due='2026-10-15')
    n4=await A.inv_new(R); await A.inv_set(R,client='Acme, Inc.',currency='USD',issue='2026-10-20',due='2026-10-30'); await A.lines_fill(R,[('Retainer','1','500','0','0')]); s_c=await A.mark_sent(R)
    num4=await A.inv_number(R)
    await A.inv_back(R); rows=await A.list_rows(R)
    out['nums']=[num1,num2,num3,num4]
    r['I10']=res(None, f'A={num1} sent ({s_a}) due 15 Oct, B={num2} draft due 15 Oct, C={num4} sent ({s_c}) due 30 Oct, JPY={num3} draft; list rows {rows}')
    r['I09']=res(None, f'list rows (columns) {rows}')
    await R.shot(f'{evdir}/i09_list.png')
    f={}
    for stt in ['Draft','Sent','Paid','Overdue']:
        f[stt]=await A.list_filter(R,stt)
    await A.list_filter(R,'All')
    r['I11']=res(None, f'filters {f}')
    s1=await A.list_search(R,'acme'); s2=await A.list_search(R,num4); await A.list_search(R,'')
    r['I12']=res(None, f'search acme -> {s1}; search {num4} -> {s2}')
    so=await A.list_sort(R)
    r['I13']=res(None, f'sorts {so}')
    # I06 edit client Beta LLC -> Beta Ltd (used on JPY invoice)
    e6=await A.client_edit(R,'Beta LLC','Beta Ltd'); cl=await A.clients_list(R); rows=await A.list_rows(R)
    r['I06']=res(None, f'edit -> {e6}; clients {cl}; invoice rows {rows}')
    # I07/I08 client delete
    d7=await A.client_delete(R,'Acme, Inc.',accept=True); cl7=await A.clients_list(R)
    R.confirm_answer=False; d8a=await A.client_delete(R,'BadMail' if any('BadMail' in x for x in cl7) else 'Gamma Co',accept=False)
    # Gamma Co is used by invoice #2; make an unused client for the confirm test
    await A.client_add(R,'Delta Unused','')
    d8b=await A.client_delete(R,'Delta Unused',accept=False); cl8b=await A.clients_list(R)
    d8c=await A.client_delete(R,'Delta Unused',accept=True); cl8c=await A.clients_list(R)
    cf=[x for x in R.log['dialogs'] if x[0]=='confirm']
    r['I07']=res(None, f'delete Acme (used) -> {d7}; clients after {cl7}')
    r['I08']=res(None, f'unused Delta: dismiss -> {d8b}, present {any("Delta" in x for x in cl8b)}; accept -> {d8c}, present {any("Delta" in x for x in cl8c)}; confirm dialogs so far {len(cf)}')
    # I29-I33 status actions on invoice #4 (C)
    await A.open_inv(R,num4); st0=await A.status(R)
    r['I29']=res(None, f'invoice C marked sent earlier: status now {st0}; A {s_a}')
    p=await A.mark_paid(R,'2026-10-21'); st1=await A.status(R)
    r['I30']=res(None, f'mark paid -> {p}; status {st1}')
    ro=await A.readonly_probe(R)
    r['I31']=res(None, f'{ro}')
    dpl=await A.duplicate(R); dd=await A.inv_read(R); dl=await A.line_descs(R); ds=await A.status(R)
    r['I32']=res(None, f'duplicate -> {dpl}; new fields {dd}; lines {dl}; status {ds}')
    numd=await A.inv_number(R)
    R.confirm_answer=False; await A.delete_inv(R); still=await A.inv_number(R); await A.inv_back(R); rows1=await A.list_rows(R)
    await A.open_inv(R,numd); R.confirm_answer=True; await A.delete_inv(R); R.confirm_answer=False; await A.inv_back(R); rows2=await A.list_rows(R)
    r['I33']=res(None, f'dismiss -> rows {len(rows1)} (dup {numd} present {any(numd in x for x in rows1)}); accept -> rows {len(rows2)} present {any(numd in x for x in rows2)}')
    # I34 print
    await A.open_inv(R,num1); pr=await A.print_probe(R,evdir)
    r['I34']=res(None, f'{pr}')
    bn2=await A.business_name_visible(R)
    r['I02']['ev']+=f' | on invoice #1 after setup, business name shown {bn2}'
    # I38 CSV
    await A.inv_back(R)
    p=await A.export_csv(R); txt=open(p,encoding='utf-8-sig',errors='replace').read() if p else None
    if txt: open(f'{evdir}/export.csv','w').write(txt)
    parsed=list(csv.reader(io.StringIO(txt))) if txt else None
    r['I38']=res(None, f'file {p and os.path.basename(p)}; first line {txt.splitlines()[0] if txt else None!r}; rows {parsed}')
    # I39 JSON export
    pj=await A.export_json(R); out['json_export']=pj
    r['I39']=res(None, f'export {pj and os.path.basename(pj)}: {open(pj).read()[:200] if pj else None}')
    # I40 bad import
    bad1=os.path.join(R.dl_dir,'bad.json'); open(bad1,'w').write('this is not json')
    bad2=os.path.join(R.dl_dir,'bad2.json'); open(bad2,'w').write('{"foo":1}')
    rows0=await A.list_rows(R); m1=await A.import_json(R,bad1); m2=await A.import_json(R,bad2); await A.inv_back(R); rows1=await A.list_rows(R)
    r['I40']=res(None, f'bad text -> {m1}; wrong shape -> {m2}; rows unchanged {rows0==rows1}')
    # G06 reload
    await pg.reload(); await pg.wait_for_timeout(800); rows2=await A.list_rows(R)
    r['G06']=res(sorted(rows2)==sorted(rows1), f'rows before {len(rows1)} after reload {len(rows2)}; same row set {sorted(rows2)==sorted(rows1)}; same order {rows2==rows1} (order may reset with the sort control; only data counts)'+('' if sorted(rows2)==sorted(rows1) else f'; differing rows before {[x for x in rows1 if x not in rows2]} after {[x for x in rows2 if x not in rows1]}'))
    out['items']=r
    return r
async def run_import_fresh(R,A,path):
    R.confirm_answer=True  # a 'replace data?' confirm on import is answered yes
    m=await A.import_json(R,path); await A.inv_back(R); rows=await A.list_rows(R); cl=await A.clients_list(R); s=await A.settings_read(R)
    return res(None, f'fresh import -> {m}; rows {rows}; clients {cl}; settings {s}')
async def flow375(R,A,evdir):
    ev=[]
    ev.append(await A.client_add(R,'Acme, Inc.','billing@acme.test'))
    n=await A.inv_new(R); await R.shot(f'{evdir}/g09_375_editor.png')
    await A.inv_set(R,client='Acme, Inc.'); await A.lines_fill(R,[('Design','1','100','0','0')]); ev.append(f'totals {await A.totals_text(R)}')
    ev.append(f'mark sent {await A.mark_sent(R)}')
    await A.inv_back(R); ev.append(f'rows {await A.list_rows(R)}')
    return ev
