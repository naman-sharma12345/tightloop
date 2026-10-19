"""adapter B05 (invoice, arms round) - locators only."""
import re, os
C={'settings_open': 'header [data-act=open-settings]', 's_name': '#s-name', 's_address': '#s-address', 's_taxid': '#s-taxId', 's_currency': '#s-currency', 's_taxrate': '#s-taxRate', 's_save': '#dlg-settings button[type=submit]', 'clients_hash': '#/clients', 'client_add_btn': 'main .page-head button:has-text("Add client")', 'c_name': '#c-name', 'c_email': '#c-email', 'c_submit': '#dlg-client button[type=submit]', 'c_errors': 'dialog[open] .field-error', 'client_items': 'main ul.client-grid > li', 'edit_lbl': 'Edit {}', 'del_lbl': 'Delete {}', 'notice_sel': '#notice-region, main [role=alert], main .field-error, main .inline-error, #toast', 'inv_hash': '#/invoices', 'new_inv_btn': 'main .page-head button:has-text("New invoice")', 'f_number': '#f-number', 'f_client': '#f-clientId', 'f_issue': '#f-issueDate', 'f_due': '#f-dueDate', 'f_currency': '#f-currency', 'editor_err': 'main .field-error, main [role=alert], main .err', 'row_link': 'main table tbody a.row-link', 'rows': 'main table tbody tr', 'filter_group': 'Filter by status', 'search': '#q', 'sort': '#sort', 'sorts': ['Newest first', 'Oldest first', 'Highest total', 'Lowest total'], 'lines': '#lines > li', 'fk': {'Description': '.lf-description input', 'Qty': '.lf-quantity input', 'Unit price': '.lf-unitPrice input', 'Discount %': '.lf-discount input', 'Tax %': '.lf-taxRate input'}, 'add_line': '#add-line', 'line_rm': 'button[aria-label^="Remove line"]', 'amount': '.lf-amount output', 'totals': '#totals', 'handle': '.handle', 'saved': '#saved', 'status_js': "()=>document.querySelector('#inv-badge').innerText+' | '+document.querySelector('#saved').innerText+' | '+(document.querySelector('#actions')||{}).innerText", 'actions': '#actions', 'sent_name': 'Mark as sent', 'paid_name': 'Mark as paid', 'paid_date': '#p-date', 'paid_submit': '#dlg-paid button[type=submit]', 'reopen_re': 'Reopen|Back to|unpaid|Edit', 'dup_name': 'Duplicate', 'del_name': 'Delete', 'csv_btn': 'main .page-head button:has-text("Export CSV")', 'json_where': 'list', 'json_btn': 'main .page-head button:has-text("Export JSON")', 'import_file': '#import-file', 'import_msg': '#notice-region, #toast, main [role=alert]', 'probe_opener': 'header [data-act=open-settings]'}
async def _w(R,ms=250): await R.pg.wait_for_timeout(ms)
def _d(R): return R.pg.locator('dialog[open]')
async def close_dialog(R):
    for _ in range(2):
        if await R.pg.locator('dialog[open]').count(): await R.pg.keyboard.press('Escape'); await _w(R)
async def _goto(R,h):
    await R.pg.evaluate("(h)=>{location.hash=h}",h); await _w(R,400)
async def _open_settings(R):
    if C.get('settings_hash'): await _goto(R,C['settings_hash'])
    await R.pg.locator(C['settings_open']).first.click(); await _w(R)
async def settings_set(R,v):
    await _open_settings(R); pg=R.pg
    await pg.locator(C['s_name']).fill(v['name']); await pg.locator(C['s_address']).fill(v['address']); await pg.locator(C['s_taxid']).fill(v['taxid'])
    await pg.locator(C['s_currency']).select_option(value=v['currency'])
    await pg.locator(C['s_taxrate']).fill(v['taxrate'])
    await pg.locator(C['s_save']).first.click(); await _w(R)
    st=await R.pg.locator('dialog[open]').count()
    if st: await close_dialog(R)
    return 'saved' if not st else 'dialog stayed open'
async def settings_read(R):
    await _open_settings(R); pg=R.pg
    v={k: await pg.locator(s).input_value() for k,s in [('name',C['s_name']),('address',C['s_address']),('taxid',C['s_taxid']),('currency',C['s_currency']),('taxrate',C['s_taxrate'])]}
    await close_dialog(R); return v
async def client_add(R,name,email):
    await _goto(R,C['clients_hash']); await R.pg.locator(C['client_add_btn']).first.click(); await _w(R); pg=R.pg
    await pg.locator(C['c_name']).fill(name); await pg.locator(C['c_email']).fill(email)
    await pg.locator(C['c_submit']).click(); await _w(R)
    if await R.pg.locator('dialog[open]').count():
        e=await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden&&e.offsetParent!==null).map(e=>e.innerText.trim()).filter(Boolean)",C['c_errors'])
        await close_dialog(R); return f'refused, inline errors {e}'
    return 'saved'
async def clients_list(R):
    await _goto(R,C['clients_hash']); return [t.strip().replace('\n',' ') for t in await R.pg.locator(C['client_items']).all_inner_texts()]
async def client_edit(R,old,new):
    await _goto(R,C['clients_hash']); await R.pg.get_by_role('button',name=C['edit_lbl'].format(old),exact=True).click(); await _w(R)
    await R.pg.locator(C['c_name']).fill(new); await R.pg.locator(C['c_submit']).click(); await _w(R)
    st=await R.pg.locator('dialog[open]').count()
    if st: await close_dialog(R)
    return 'saved' if not st else 'not saved'
async def client_delete(R,name,accept):
    await _goto(R,C['clients_hash']); R.confirm_answer=accept; n0=len(R.log['dialogs'])
    await R.pg.get_by_role('button',name=C['del_lbl'].format(name),exact=True).click(); await _w(R,400); R.confirm_answer=False
    dl=R.log['dialogs'][n0:]
    msg=await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].map(e=>e.innerText.trim()).filter(Boolean).join(' / ')",C['notice_sel'])
    if await R.pg.locator('dialog[open]').count():
        msg+=' | dialog: '+(await _d(R).inner_text())[:200]; await close_dialog(R)
    return f'dialogs {dl}; message: {msg[:250]}'
async def inv_new(R):
    await _goto(R,C['inv_hash']); await R.pg.locator(C['new_inv_btn']).first.click(); await _w(R,500)
    return await inv_number(R)
async def inv_number(R):
    l=R.pg.locator(C['f_number'])
    return await l.input_value() if await l.count() else None
async def inv_read(R):
    pg=R.pg
    return {k: await pg.locator(s).input_value() for k,s in [('number',C['f_number']),('issue',C['f_issue']),('due',C['f_due']),('currency',C['f_currency'])]}
async def inv_set(R,number=None,client=None,issue=None,due=None,currency=None):
    pg=R.pg
    if number is not None: await pg.locator(C['f_number']).fill(number); await pg.locator(C['f_number']).blur()
    if client is not None: await pg.locator(C['f_client']).select_option(label=client)
    if issue is not None: await pg.locator(C['f_issue']).fill(issue); await pg.locator(C['f_issue']).blur()
    if due is not None: await pg.locator(C['f_due']).fill(due); await pg.locator(C['f_due']).blur()
    if currency is not None: await pg.locator(C['f_currency']).select_option(value=currency)
    await _w(R,250); return 'set'
async def editor_errors(R):
    return await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden&&e.offsetParent!==null).map(e=>e.innerText.trim()).filter(Boolean)",C['editor_err'])
async def inv_back(R): await _goto(R,C['inv_hash'])
async def open_inv(R,num):
    await _goto(R,C['inv_hash']); l=R.pg.locator(C['row_link'],has_text=re.compile('^\\s*'+re.escape(num)+'\\s*$'))
    if await l.count()==0: return False
    await l.first.click(); await _w(R,400); return True
async def open_inv_index(R,i):
    await _goto(R,C['inv_hash']); await R.pg.locator(C['row_link']).nth(i).click(); await _w(R,400); return True
async def list_rows(R):
    await _goto(R,C['inv_hash'])
    return [t.replace('\t',' | ').replace('\n',' ') for t in await R.pg.locator(C['rows']).all_inner_texts()]
async def list_filter(R,st):
    await _goto(R,C['inv_hash']); await R.pg.get_by_role('group',name=C['filter_group']).get_by_role('button',name=re.compile('^'+st)).click(); await _w(R)
    return [t.split('\t')[0].split('\n')[0]+':'+t.split('\t')[-1] for t in await R.pg.locator(C['rows']).all_inner_texts()]
async def list_search(R,q):
    await R.pg.locator(C['search']).fill(q); await _w(R,400)
    return [t.split('\t')[0].split('\n')[0] for t in await R.pg.locator(C['rows']).all_inner_texts()]
async def list_sort(R):
    out={}
    for lab in C['sorts']:
        await R.pg.locator(C['sort']).select_option(label=lab); await _w(R,200)
        out[lab]=[(t.split('\t')[0].split('\n')[0], t.split('\t')[2] if len(t.split('\t'))>2 else '', t.split('\t')[4] if len(t.split('\t'))>4 else '') for t in await R.pg.locator(C['rows']).all_inner_texts()]
    return out
def _li(R): return R.pg.locator(C['lines'])
async def line_add_if_none(R):
    if await _li(R).count()==0: await R.pg.locator(C['add_line']).click(); await _w(R)
def _f(R,l,i): return _li(R).nth(i).locator(C['fk'][l])
async def line_tax(R,i): return await _f(R,'Tax %',i).input_value()
async def line_set(R,i,desc=None,qty=None,price=None,disc=None,tax=None):
    for v,l in [(desc,'Description'),(qty,'Qty'),(price,'Unit price'),(disc,'Discount %'),(tax,'Tax %')]:
        if v is not None:
            f=_f(R,l,i); await f.fill(v); await f.blur()
    await _w(R,150)
async def line_remove(R,i):
    await _li(R).nth(i).locator(C['line_rm']).click(); await _w(R)
async def lines_fill(R,lines):
    while await _li(R).count()<len(lines): await R.pg.locator(C['add_line']).click(); await _w(R,150)
    while await _li(R).count()>len(lines): await line_remove(R,await _li(R).count()-1)
    for i,(d,q,p,di,t) in enumerate(lines): await line_set(R,i,d,q,p,di,t)
async def line_descs(R):
    n=await _li(R).count(); return [await _f(R,'Description',i).input_value() for i in range(n)]
async def line_amounts(R):
    return [(await x.locator(C['amount']).first.inner_text()).strip() for x in await _li(R).all()]
async def line_invalid(R,i):
    li=_li(R).nth(i)
    inv=await li.locator('[aria-invalid=true]').count(); msg=await li.evaluate("e=>[...e.querySelectorAll('.err, .field-error, [class*=error], [role=alert]')].filter(x=>!x.hidden&&x.offsetParent!==null).map(x=>x.innerText.trim()).filter(Boolean)")
    return f'aria-invalid fields {inv}, messages {msg}'
async def totals_text(R):
    return (await R.pg.locator(C['totals']).first.inner_text()).replace('\n',' ')
async def currency_options(R):
    return await R.pg.locator(C['f_currency']+' option').all_inner_texts()
async def business_name_visible(R):
    t=await R.pg.evaluate("()=>document.querySelector('main').innerText"); return 'Northwind Studio' in t
async def line_alt(R,i,direction):
    f=_f(R,'Description',i); await f.focus(); await R.pg.keyboard.press(f'Alt+Arrow{direction}'); await _w(R)
    return await R.pg.evaluate("()=>document.activeElement.id+'|'+(document.activeElement.value||document.activeElement.getAttribute('aria-label')||'')")
async def line_drag(R,src,dst):
    pg=R.pg; before=await line_descs(R)
    s=_li(R).nth(src).locator(C['handle']).first; t=_li(R).nth(dst)
    await s.drag_to(t, target_position={'x':20,'y':5}); await _w(R,300)
    if await line_descs(R)!=before: return 'drag_to handle'
    a=await s.bounding_box(); b=await t.bounding_box()
    await pg.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2); await pg.mouse.down()
    for k in range(1,11): await pg.mouse.move(a['x']+a['width']/2, a['y']+(b['y']+3-a['y'])*k/10); await _w(R,30)
    await pg.mouse.up(); await _w(R,300)
    return 'manual mouse drag (drag_to changed nothing)'
async def saved_indicator(R):
    l=R.pg.locator(C['saved']); return (await l.first.inner_text()).replace('\n',' ') if await l.count() else ''
async def status(R):
    return (await R.pg.evaluate(C['status_js'])).replace('\n',' ')[:160]
async def _act(R,name): return R.pg.locator(C['actions']).get_by_role('button',name=name,exact=True)
async def mark_sent(R):
    b=await _act(R,C['sent_name'])
    if await b.count()==0: return 'no button'
    await b.click(); await _w(R); return 'clicked'
async def mark_paid(R,date):
    b=await _act(R,C['paid_name'])
    if await b.count()==0: return 'no button'
    await b.click(); await _w(R)
    if await R.pg.locator('dialog[open]').count():
        await R.pg.locator(C['paid_date']).fill(date); await R.pg.locator(C['paid_submit']).click(); await _w(R)
        return 'paid dialog with date'
    return 'no date dialog'
async def readonly_probe(R):
    pg=R.pg; f=_f(R,'Description',0)
    ro=await f.evaluate("e=>e.readOnly||e.disabled||!!e.closest('fieldset:disabled')") if await f.count() else 'no field'
    cl=await pg.locator(C['f_client']).evaluate("e=>e.disabled||e.readOnly||!!e.closest('fieldset:disabled')") if await pg.locator(C['f_client']).count() else 'no client field'
    try: await f.fill('HACK',timeout=1500); after=await f.input_value()
    except Exception as e: after='fill refused'
    acts=await pg.locator(C['actions']+' button').all_inner_texts()
    rb=pg.locator(C['actions']).get_by_role('button',name=re.compile(C['reopen_re'],re.I)); has=await rb.count()
    if has: await rb.first.click(); await _w(R)
    if await pg.locator('dialog[open]').count(): await close_dialog(R)
    ro2=await f.evaluate("e=>e.readOnly||e.disabled||!!e.closest('fieldset:disabled')") if await f.count() else None
    await line_set(R,0,desc='Retainer')
    return f'paid: line field readonly {ro}, client disabled {cl}, fill attempt -> {after}; actions {[a.strip() for a in acts]}; reopen button {has}; after reopen readonly {ro2}'
async def duplicate(R):
    await (await _act(R,C['dup_name'])).click(); await _w(R,500); return 'clicked'
async def delete_inv(R):
    await (await _act(R,C['del_name'])).click(); await _w(R,400)
async def print_probe(R,evdir):
    pg=R.pg
    if os.environ.get('ARMS_PRINT_MODE','beforeprint')!='frozen': await pg.evaluate("()=>window.dispatchEvent(new Event('beforeprint'))")  # what a real print fires first (deviation; ARMS_PRINT_MODE=frozen skips it)
    await pg.emulate_media(media='print'); await _w(R,300)
    await pg.screenshot(path=f'{evdir}/i34_print.png', full_page=True)
    vis=await pg.evaluate("()=>[...document.querySelectorAll('button, nav, header')].filter(e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}).map(e=>e.tagName+':'+(e.innerText||'').trim().slice(0,20))")
    css=await pg.evaluate("()=>{let t='';for(const s of document.styleSheets){try{for(const r of s.cssRules){if(r.media&&/print/.test(r.media.mediaText)) t+=r.cssText}}catch(e){}} return t}")
    tot=await pg.evaluate("()=>[...document.querySelectorAll('[class*=total],[id*=total]')].filter(e=>e.getBoundingClientRect().height>0).map(e=>(e.id||e.className).toString().slice(0,30)+':'+getComputedStyle(e).breakInside).slice(0,8)")
    txt=(await pg.evaluate("()=>document.body.innerText"))[:300].replace('\n',' | ')
    await pg.emulate_media(media='screen')
    if os.environ.get('ARMS_PRINT_MODE','beforeprint')!='frozen': await pg.evaluate("()=>window.dispatchEvent(new Event('afterprint'))")
    avoid=re.findall(r'([^{}]*)\{[^}]*(?:break-inside|page-break-inside)\s*:\s*avoid',css)
    return f'visible buttons/nav/header in print: {vis[:10]}; print CSS rules with break-inside avoid on: {[a.strip()[-60:] for a in avoid][:8]}; print css length {len(css)}; computed break-inside of visible total blocks in print: {tot}; print text {txt}'
async def export_csv(R):
    await _goto(R,C['inv_hash']); return await R.download(lambda: R.pg.locator(C['csv_btn']).first.click())
async def export_json(R):
    if C['json_where']=='settings':
        await _open_settings(R); p=await R.download(lambda: R.pg.locator(C['json_btn']).first.click()); await close_dialog(R); return p
    await _goto(R,C['inv_hash']); return await R.download(lambda: R.pg.locator(C['json_btn']).first.click())
async def import_json(R,path):
    pg=R.pg
    if C['json_where']=='settings': await _open_settings(R)
    else: await _goto(R,C['inv_hash'])
    await pg.evaluate("(s)=>{for(const e of document.querySelectorAll(s)) if(e.id==='toast'||/toast/.test(e.className)) e.textContent=''}",C['import_msg'])
    await pg.locator(C['import_file']).set_input_files(path); await _w(R,700)
    msg=await pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden).map(e=>e.innerText.trim()).filter(Boolean).join(' / ')",C['import_msg'])
    if await pg.locator('dialog[open]').count():
        btn=_d(R).get_by_role('button',name=re.compile('^(Replace|Import|Yes|Continue)',re.I))
        if await btn.count():
            t=await btn.last.inner_text()
            if 'JSON' not in t: await btn.last.click(); await _w(R,500); msg+=' | clicked '+t.strip()
    await close_dialog(R); return msg[:300]
async def focus_page(R): await R.pg.evaluate("()=>document.activeElement&&document.activeElement.blur()")
async def dialog_probe(R):
    pg=R.pg
    if C.get('settings_hash'): await _goto(R,C['settings_hash'])
    b=pg.locator(C['probe_opener']).first; await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
    outside=0
    for i in range(25):
        await pg.keyboard.press('Tab')
        if not await pg.evaluate("()=>!!document.activeElement.closest('dialog[open],[role=dialog]')"): outside+=1
    for i in range(5):
        await pg.keyboard.press('Shift+Tab')
        if not await pg.evaluate("()=>!!document.activeElement.closest('dialog[open],[role=dialog]')"): outside+=1
    await pg.keyboard.press('Escape'); await _w(R)
    back=await pg.evaluate("()=>{const e=document.activeElement;return e.tagName+'|'+(e.getAttribute('aria-label')||e.innerText||e.id).slice(0,40)}")
    await b.click(); await _w(R)
    return f'focus outside dialog on {outside}/30 tab presses; after Escape focus on {back} (opener {C["probe_opener"]})'
