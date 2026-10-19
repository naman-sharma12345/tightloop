"""adapter B03 (invoice) - locators only."""
import re
async def _w(R,ms=250): await R.pg.wait_for_timeout(ms)
def _d(R): return R.pg.locator('dialog[open]')
async def close_dialog(R):
    for _ in range(2):
        if await R.pg.locator('dialog[open]').count(): await R.pg.keyboard.press('Escape'); await _w(R)
async def _goto(R,h):
    await R.pg.evaluate("(h)=>{location.hash=h}",h); await _w(R,400)
# ---------- settings ----------
async def settings_set(R,v):
    await R.pg.get_by_role('button',name='Business & data').click(); await _w(R); d=_d(R)
    await d.get_by_label('Business name').fill(v['name']); await d.get_by_label('Address').fill(v['address']); await d.get_by_label('Tax ID').fill(v['taxid'])
    await d.get_by_label('Default currency').select_option(value=v['currency']) if await d.get_by_label('Default currency').locator(f'option[value="{v["currency"]}"]').count() else await d.get_by_label('Default currency').select_option(label=re.compile(v['currency']))
    await d.get_by_label(re.compile('Default tax rate')).fill(v['taxrate'])
    await d.get_by_role('button',name='Save details').click(); await _w(R)
    st=await R.pg.locator('dialog[open]').count(); 
    if st: await close_dialog(R)
    return 'saved' if not st else 'dialog stayed open'
async def settings_read(R):
    await R.pg.get_by_role('button',name='Business & data').click(); await _w(R); d=_d(R)
    v={k: await d.get_by_label(l).input_value() for k,l in [('name','Business name'),('address','Address'),('taxid','Tax ID'),('currency','Default currency'),('taxrate',re.compile('Default tax rate'))]}
    await close_dialog(R); return v
# ---------- clients ----------
async def client_add(R,name,email):
    await _goto(R,'#/clients'); await R.pg.get_by_role('button',name='Add client').first.click(); await _w(R); d=_d(R)
    await d.get_by_label('Name').fill(name); await d.get_by_label('Email').fill(email)
    await d.get_by_role('button',name='Add client').click(); await _w(R)
    if await R.pg.locator('dialog[open]').count():
        e=await R.pg.evaluate("()=>[...document.querySelectorAll('dialog[open] [id$=-err]')].map(e=>e.innerText.trim()).filter(Boolean)")
        await close_dialog(R); return f'refused, inline errors {e}'
    return 'saved'
async def clients_list(R):
    await _goto(R,'#/clients'); return [t.strip().replace('\n',' ') for t in await R.pg.locator('main .client-list > li').all_inner_texts()]
async def client_edit(R,old,new):
    await _goto(R,'#/clients'); await R.pg.get_by_role('button',name=f'Edit {old}',exact=True).click(); await _w(R)
    d=_d(R); await d.get_by_label('Name').fill(new); await d.locator('button[type=submit], footer button.btn-primary').last.click(); await _w(R)
    st=await R.pg.locator('dialog[open]').count()
    if st: await close_dialog(R)
    return 'saved' if not st else 'not saved'
async def client_delete(R,name,accept):
    await _goto(R,'#/clients'); R.confirm_answer=accept; n0=len(R.log['dialogs'])
    await R.pg.get_by_role('button',name=f'Delete {name}',exact=True).click(); await _w(R,400); R.confirm_answer=False
    dl=R.log['dialogs'][n0:]
    msg=await R.pg.evaluate("()=>[...document.querySelectorAll('main [role=alert], main .banner, main .inline-error, main [id$=-err], .toast, [role=status]')].map(e=>e.innerText.trim()).filter(Boolean).join(' / ')")
    if await R.pg.locator('dialog[open]').count():
        msg+=' | dialog: '+(await _d(R).inner_text())[:200]; await close_dialog(R)
    return f'dialogs {dl}; message: {msg[:250]}'
# ---------- invoices ----------
async def inv_new(R):
    await _goto(R,'#/invoices'); await R.pg.get_by_role('button',name='New invoice').first.click(); await _w(R,500)
    return await inv_number(R)
async def inv_number(R):
    l=R.pg.get_by_label('Invoice number')
    return await l.input_value() if await l.count() else None
async def inv_read(R):
    pg=R.pg
    return {k: await pg.get_by_label(l,exact=True).input_value() for k,l in [('number','Invoice number'),('issue','Issue date'),('due','Due date'),('currency','Currency')]}
async def inv_set(R,number=None,client=None,issue=None,due=None,currency=None):
    pg=R.pg
    if number is not None: await pg.get_by_label('Invoice number').fill(number); await pg.get_by_label('Invoice number').blur()
    if client is not None: await pg.get_by_label('Client',exact=True).select_option(label=client)
    if issue is not None: await pg.get_by_label('Issue date').fill(issue)
    if due is not None: await pg.get_by_label('Due date').fill(due); await pg.get_by_label('Due date').blur()
    if currency is not None: await pg.get_by_label('Currency',exact=True).select_option(value=currency)
    await _w(R,250); return 'set'
async def editor_errors(R):
    return await R.pg.evaluate("()=>[...document.querySelectorAll('main [id$=-err]:not([hidden]), main .field-error:not([hidden]), main [role=alert]')].map(e=>e.innerText.trim()).filter(Boolean)")
async def inv_back(R): await _goto(R,'#/invoices')
async def open_inv(R,num):
    await _goto(R,'#/invoices'); l=R.pg.get_by_role('link',name=num,exact=True)
    if await l.count()==0: return False
    await l.first.click(); await _w(R,400); return True
async def open_inv_index(R,i):
    await _goto(R,'#/invoices'); await R.pg.locator('table tbody a').nth(i).click(); await _w(R,400); return True
async def list_rows(R):
    await _goto(R,'#/invoices')
    return [t.replace('\t',' | ').replace('\n',' ') for t in await R.pg.locator('table tbody tr').all_inner_texts()]
async def list_filter(R,st):
    await _goto(R,'#/invoices'); await R.pg.get_by_role('group',name='Filter by status').get_by_role('button',name=re.compile('^'+st)).click(); await _w(R)
    return [t.split('\t')[0].split('\n')[0]+':'+t.split('\t')[-1] for t in await R.pg.locator('table tbody tr').all_inner_texts()]
async def list_search(R,q):
    await R.pg.get_by_label('Search by client or number').fill(q); await _w(R,300)
    return [t.split('\t')[0].split('\n')[0] for t in await R.pg.locator('table tbody tr').all_inner_texts()]
async def list_sort(R):
    out={}
    for lab in ['Newest first','Oldest first','Highest total','Lowest total']:
        await R.pg.get_by_label('Sort invoices').select_option(label=lab); await _w(R,200)
        out[lab]=[(t.split('\t')[0].split('\n')[0], t.split('\t')[2] if len(t.split('\t'))>2 else '', t.split('\t')[4] if len(t.split('\t'))>4 else '') for t in await R.pg.locator('table tbody tr').all_inner_texts()]
    return out
# ---------- lines ----------
def _li(R): return R.pg.get_by_role('list',name='Line items').get_by_role('listitem')
async def line_add_if_none(R):
    if await _li(R).count()==0: await R.pg.get_by_role('button',name='Add line').click(); await _w(R)
def _f(R,l,i): return R.pg.get_by_role('textbox',name=f'{l} , line {i+1}',exact=True)
async def line_tax(R,i): return await _f(R,'Tax %',i).input_value()
async def line_set(R,i,desc=None,qty=None,price=None,disc=None,tax=None):
    pg=R.pg
    for v,l in [(desc,'Description'),(qty,'Qty'),(price,'Unit price'),(disc,'Discount %'),(tax,'Tax %')]:
        if v is not None:
            f=_f(R,l,i); await f.fill(v); await f.blur()
    await _w(R,150)
async def lines_fill(R,lines):
    while await _li(R).count()<len(lines): await R.pg.get_by_role('button',name='Add line').click(); await _w(R,150)
    while await _li(R).count()>len(lines): await line_remove(R,await _li(R).count()-1)
    for i,(d,q,p,di,t) in enumerate(lines): await line_set(R,i,d,q,p,di,t)
async def line_remove(R,i):
    await R.pg.get_by_role('button',name=f'Remove line {i+1}',exact=True).click(); await _w(R)
async def line_descs(R):
    n=await _li(R).count(); return [await _f(R,'Description',i).input_value() for i in range(n)]
async def line_amounts(R):
    return [ (await x.inner_text()).split('\n')[-2] if False else (await x.locator('.line-amount, .line-total, [class*=amount]').first.inner_text() if await x.locator('.line-amount, .line-total, [class*=amount]').count() else (await x.inner_text()).replace('\n',' ')[-40:]) for x in await _li(R).all()]
async def line_invalid(R,i):
    li=_li(R).nth(i)
    inv=await li.locator('[aria-invalid=true]').count(); msg=await li.evaluate("e=>[...e.querySelectorAll('[id$=-err], .field-error, .err')].map(x=>x.innerText.trim()).filter(Boolean)")
    return f'aria-invalid fields {inv}, messages {msg}'
async def totals_text(R):
    return (await R.pg.locator('main dl').last.inner_text()).replace('\n',' ')
async def currency_options(R):
    return await R.pg.get_by_label('Currency',exact=True).locator('option').all_inner_texts()
async def business_name_visible(R):
    t=await R.pg.evaluate("()=>document.body.innerText"); return 'Northwind Studio' in t
async def line_alt(R,i,direction):
    f=_f(R,'Description',i); await f.focus(); await R.pg.keyboard.press(f'Alt+Arrow{direction}'); await _w(R)
    return await R.pg.evaluate("()=>document.activeElement.getAttribute('aria-label')")
async def line_drag(R,src,dst):
    pg=R.pg; before=await line_descs(R)
    s=_li(R).nth(src).get_by_role('button').first; t=_li(R).nth(dst)
    await s.drag_to(t, target_position={'x':20,'y':5}); await _w(R,300)
    if await line_descs(R)!=before: return 'drag_to handle'
    a=await s.bounding_box(); b=await t.bounding_box()
    await pg.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2); await pg.mouse.down()
    for k in range(1,11): await pg.mouse.move(a['x']+a['width']/2, a['y']+(b['y']+3-a['y'])*k/10); await _w(R,30)
    await pg.mouse.up(); await _w(R,300)
    return 'manual mouse drag (drag_to changed nothing)'
async def saved_indicator(R):
    return await R.pg.evaluate("()=>{const e=[...document.querySelectorAll('main *')].find(x=>/^Saved/.test(x.innerText||'')&&x.children.length<3);return e?e.innerText:''}")
async def status(R):
    return await R.pg.evaluate("()=>{const h=document.querySelector('main h1'); const s=h&&h.parentElement? h.parentElement.innerText:''; return s.replace(/\\n/g,' ').slice(0,120)}")
async def mark_sent(R):
    b=R.pg.get_by_role('button',name='Mark as sent')
    if await b.count()==0: return 'no button'
    await b.click(); await _w(R); return 'clicked'
async def mark_paid(R,date):
    b=R.pg.get_by_role('button',name='Mark as paid')
    if await b.count()==0: return 'no button'
    await b.click(); await _w(R)
    if await R.pg.locator('dialog[open]').count():
        await R.pg.locator('#paid-date').fill(date); await _d(R).locator('button[type=submit]').click(); await _w(R)
        return 'paid dialog with date'
    return 'no date dialog'
async def readonly_probe(R):
    pg=R.pg; f=_f(R,'Description',0)
    ro=await f.evaluate("e=>e.readOnly||e.disabled") if await f.count() else 'no field'
    cl=await pg.get_by_label('Client',exact=True).evaluate("e=>e.disabled") if await pg.get_by_label('Client',exact=True).count() else 'no client field'
    try: await f.fill('HACK',timeout=1500); after=await f.input_value()
    except Exception as e: after='fill refused'
    rb=pg.get_by_role('button',name='Reopen'); has=await rb.count()
    if has: await rb.first.click(); await _w(R)
    ro2=await f.evaluate("e=>e.readOnly||e.disabled") if await f.count() else None
    await line_set(R,0,desc='Retainer')
    return f'paid: line field readonly {ro}, client disabled {cl}, fill attempt -> {after}; reopen button {has}; after reopen readonly {ro2}'
async def duplicate(R):
    await R.pg.get_by_role('button',name='Duplicate').click(); await _w(R,500); return 'clicked'
async def delete_inv(R):
    await R.pg.get_by_role('button',name='Delete',exact=True).click(); await _w(R,400)
async def print_probe(R,evdir):
    pg=R.pg; await pg.emulate_media(media='print'); await _w(R,300)
    await pg.screenshot(path=f'{evdir}/i34_print.png', full_page=True)
    vis=await pg.evaluate("()=>[...document.querySelectorAll('button, nav, header')].filter(e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}).map(e=>e.tagName+':'+(e.innerText||'').trim().slice(0,20))")
    css=await pg.evaluate("()=>{let t='';for(const s of document.styleSheets){try{for(const r of s.cssRules){if(r.media&&/print/.test(r.media.mediaText)) t+=r.cssText}}catch(e){}} return t}")
    await pg.emulate_media(media='screen')
    avoid=re.findall(r'([^{}]*)\{[^}]*(?:break-inside|page-break-inside)\s*:\s*avoid',css)
    return f'visible buttons/nav/header in print: {vis[:10]}; print CSS rules with break-inside avoid on: {[a.strip()[-60:] for a in avoid][:8]}; print css length {len(css)}'
async def export_csv(R):
    await _goto(R,'#/invoices'); return await R.download(lambda: R.pg.get_by_role('button',name='Export CSV').click())
async def export_json(R):
    await R.pg.get_by_role('button',name='Business & data').click(); await _w(R)
    p=await R.download(lambda: R.pg.locator('#export-json').click()); await close_dialog(R); return p
async def import_json(R,path):
    pg=R.pg; await pg.get_by_role('button',name='Business & data').click(); await _w(R)
    await pg.locator('#import-file').set_input_files(path); await _w(R,700)
    msg=await pg.evaluate("()=>[...document.querySelectorAll('dialog[open] [role=alert], dialog[open] [id$=-err], dialog[open] .banner, .toast, [role=status]')].map(e=>e.innerText.trim()).filter(Boolean).join(' / ')")
    if await pg.locator('dialog[open]').count(): 
        msg+=' | open dialog: '+(await _d(R).inner_text())[:200].replace('\n',' ')
        # a confirm-style import dialog: accept if it asks to replace
        btn=_d(R).get_by_role('button',name=re.compile('Replace|Import',re.I))
        if await btn.count(): await btn.last.click(); await _w(R,500); msg+=' | clicked replace'
    await close_dialog(R); return msg[:300]
async def focus_page(R): await R.pg.evaluate("()=>document.activeElement&&document.activeElement.blur()")
async def dialog_probe(R):
    pg=R.pg; b=pg.get_by_role('button',name='Business & data'); await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
    outside=0
    for i in range(25):
        await pg.keyboard.press('Tab')
        if not await pg.evaluate("()=>!!document.activeElement.closest('dialog[open]')"): outside+=1
    for i in range(5):
        await pg.keyboard.press('Shift+Tab')
        if not await pg.evaluate("()=>!!document.activeElement.closest('dialog[open]')"): outside+=1
    await pg.keyboard.press('Escape'); await _w(R)
    back=await pg.evaluate("()=>{const e=document.activeElement;return e.tagName+'|'+(e.getAttribute('aria-label')||e.innerText||e.id).slice(0,40)}")
    await b.click(); await _w(R)
    return f'focus outside dialog on {outside}/30 tab presses; after Escape focus on {back} (opener Business & data)'
