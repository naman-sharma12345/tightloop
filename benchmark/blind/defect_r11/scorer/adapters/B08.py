"""adapter B08 (trip) - locators only."""
import re
async def _w(R,ms=250): await R.pg.wait_for_timeout(ms)
async def trip_count(R):
    pg=R.pg
    if await pg.locator('#tripView').is_hidden(): return 0
    return await pg.locator('#tripSelect option').count()
async def open_new_trip(R):
    await R.pg.locator('header').get_by_role('button',name='New trip').click(); await _w(R)
async def fill_trip(R,name,start,end,travellers):
    pg=R.pg; d=pg.locator('#tripDialog')
    await d.get_by_label('Trip name').fill(name)
    await d.get_by_label('Start date').fill(start); await d.get_by_label('End date').fill(end)
    added=0
    for i,n in enumerate(travellers):
        box=d.get_by_label(f'Traveller {i+1} name')
        if await box.count()==0:
            btn=d.get_by_role('button',name='Add traveller')
            if await btn.count()==0 or not await btn.is_visible() or await btn.is_disabled(): return f'add button gone/disabled at #{i+1}'
            await btn.click(); await _w(R,100)
            if await box.count()==0: return f'no box #{i+1}'
        await box.fill(n); added+=1
    if not travellers:
        await d.get_by_label('Traveller 1 name').fill('')
    return f'filled {added}'
async def submit_trip(R):
    await R.pg.locator('#tripSubmit').click(); await _w(R,400)
async def form_errors(R):
    pg=R.pg
    return await pg.evaluate("()=>[...document.querySelectorAll('dialog[open] [id$=-err]:not([hidden]), dialog[open] .field-error:not([hidden]), dialog[open] [role=alert]')].map(e=>e.innerText.trim()).filter(Boolean)")
async def close_dialog(R):
    pg=R.pg
    if await pg.locator('dialog[open]').count():
        await pg.keyboard.press('Escape'); await _w(R)
    if await pg.locator('dialog[open]').count():
        await pg.locator('dialog[open] [data-close]').first.click(); await _w(R)
async def delete_current_trip(R,accept=True):
    R.confirm_answer=accept
    await R.pg.get_by_role('button',name='Delete trip',exact=True).click(); await _w(R,400)
    R.confirm_answer=False
async def current_travellers(R):
    return await R.pg.evaluate("()=>[...document.querySelectorAll('#tripHead li')].map(e=>e.innerText.trim())")
async def ndays(R):
    return await R.pg.locator('#board section[aria-label^="Day "], #board [role=region][aria-label^="Day "]').count() or await R.pg.locator('#board > *').count()
def _day(R,day): return R.pg.locator('#board > *').nth(day-1)
async def day_titles(R,day):
    return [t.strip() for t in await _day(R,day).locator('.card .card-title').all_inner_texts()]
async def unscheduled_titles(R):
    return [t.strip() for t in await R.pg.locator('#tray .card .card-title').all_inner_texts()]
async def _fill_act(R,title=None,start=None,duration=None,place=None,category=None,cost=None,paid=None,split=None,notes=None,day=None):
    d=R.pg.locator('#actDialog')
    if title is not None: await d.get_by_label('Title').fill(title)
    if day is not None: await d.get_by_label('Day').select_option(index=day-1)
    if start is not None: await d.get_by_label('Start time').fill(start)
    if duration is not None:
        h,m=divmod(duration,60); lab=(f'{h} h' if h else '')+(' ' if h and m else '')+(f'{m} min' if m else '')
        await d.get_by_label('Duration').select_option(label=lab)
    if category is not None:
        r_=d.get_by_role('radio',name=category,exact=True)
        if not await r_.is_checked():
            lab=r_.locator('xpath=ancestor::label[1]')
            await (lab.click() if await lab.count() else r_.check(force=True))
    if place is not None: await d.get_by_label('Place').fill(place)
    if cost is not None: await d.get_by_label('Cost').fill(cost)
    if paid is not None: await d.get_by_label('Paid by').select_option(label=paid)
    if split is not None:
        for n in ['Ana','Ben','Cy']:
            cb=d.locator('#actSplit').get_by_role('checkbox',name=n,exact=True)
            if await cb.count():
                if n in split: await cb.check(force=True)
                else: await cb.uncheck(force=True)
    if notes is not None: await d.get_by_label('Notes').fill(notes)
async def add_activity(R,day,title,start,dur,place,cat,cost=None,submit=True,**kw):
    pg=R.pg
    await pg.get_by_role('button',name=f'Add activity to Day {day}').click(); await _w(R)
    await _fill_act(R,title=title,start=start,duration=dur,place=place,category=cat,cost=cost,**kw)
    if submit:
        await pg.locator('#actSubmit').click(); await _w(R,300)
        if title and await pg.locator('#actDialog[open]').count(): await close_dialog(R)
async def duration_probe(R):
    pg=R.pg
    await pg.get_by_role('button',name='Add activity to Day 1').click(); await _w(R)
    opts=await pg.locator('#actDuration option').all_inner_texts(); await close_dialog(R)
    return f'select with {len(opts)} options: first {opts[:2]} last {opts[-2:]} (values not offerable outside the list)'
async def conflict_texts(R,day):
    return [t.strip().replace('\n',' ') for t in await _day(R,day).locator('.conflict').all_inner_texts()]
async def _open(R,title):
    await R.pg.locator('.card', has=R.pg.locator('.card-title', has_text=title)).first.locator('.card-open').click(); await _w(R)
async def edit_activity(R,which,**kw):
    await _open(R,which); await _fill_act(R,**kw)
    await R.pg.locator('#actSubmit').click(); await _w(R,300)
    err=await form_errors(R)
    if await R.pg.locator('#actDialog[open]').count(): await close_dialog(R); return f'not saved, errors {err}'
    return 'saved'
async def read_activity(R,title):
    await _open(R,title); d=R.pg.locator('#actDialog')
    v={k: await d.get_by_label(lab).input_value() for k,lab in [('title','Title'),('start','Start time'),('duration','Duration'),('place','Place'),('cost','Cost'),('notes','Notes')]}
    v['category']=await d.locator('#actCategories input:checked').get_attribute('value')
    await close_dialog(R); return v
async def category_icons(R):
    await R.pg.get_by_role('button',name='Add activity to Day 1').click(); await _w(R)
    m=await R.pg.evaluate("()=>[...document.querySelectorAll('#actCategories label')].map(l=>l.innerText.trim()+':'+((l.querySelector('svg')||{}).innerHTML||'NOSVG').slice(0,40))")
    await close_dialog(R); return m
async def split_probe(R,title):
    d=R.pg.locator('#actDialog'); ev=[]
    await _open(R,title); await d.get_by_label('Paid by').select_option(label='Ana')
    for n in ['Ana','Ben','Cy']: await d.locator('#actSplit').get_by_role('checkbox',name=n).uncheck(force=True)
    await R.pg.locator('#actSubmit').click(); await _w(R)
    ev.append(f'split none -> dialog open {await R.pg.locator("#actDialog[open]").count()} errors {await form_errors(R)}')
    await d.locator('#actSplit').get_by_role('checkbox',name='Ana').check(force=True); await d.locator('#actSplit').get_by_role('checkbox',name='Ben').check(force=True)
    await R.pg.locator('#actSubmit').click(); await _w(R)
    ev.append(f'Ana+Ben -> dialog open {await R.pg.locator("#actDialog[open]").count()}')
    await _open(R,title); pb=await d.get_by_label('Paid by').input_value()
    sp=await d.locator('#actSplit input:checked').count(); await close_dialog(R)
    ev.append(f'reopen paid-by value {pb}, split checked {sp}')
    return ev
async def close_probe(R,title):
    pg=R.pg; ev=[]
    await _open(R,title); await pg.locator('#actDialog [data-close]').first.click(); await _w(R); ev.append(f'button: open={await pg.locator("#actDialog[open]").count()}')
    await _open(R,title); await pg.keyboard.press('Escape'); await _w(R); ev.append(f'Escape: open={await pg.locator("#actDialog[open]").count()}')
    await _open(R,title); await pg.mouse.click(5,400); await _w(R); ev.append(f'backdrop: open={await pg.locator("#actDialog[open]").count()}')
    await close_dialog(R); return ev
async def drag(R,title,day):
    pg=R.pg; src=pg.locator('.card', has=pg.locator('.card-title', has_text=title)).first; dst=_day(R,day)
    await src.drag_to(dst); await _w(R,400)
    return 'drag_to'
async def move_menu(R,title,day):
    pg=R.pg
    b=pg.get_by_role('button',name=f'Move to… ({title})'); await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
    items=await pg.get_by_role('menuitem').all_inner_texts()
    # keyboard: arrow to the target day item, Enter
    target=[i for i,t in enumerate(items) if t.strip().startswith(f'Day {day}')]
    if not target: return f'menu items {items}'
    for _ in range(10):
        f=await pg.evaluate("()=>document.activeElement.innerText")
        if f.strip().startswith(f'Day {day}'): break
        await pg.keyboard.press('ArrowDown')
    await pg.keyboard.press('Enter'); await _w(R,300)
    return f'keyboard menu items {[t.strip()[:20] for t in items]}'
async def activity_time(R,title):
    return await R.pg.locator('.card', has=R.pg.locator('.card-title', has_text=title)).first.locator('.card-time').inner_text()
async def budget_text(R):
    return (await R.pg.locator('#budget').inner_text()).replace('\n',' | ')
async def search(R,q):
    pg=R.pg; await pg.locator('#search').fill(q); await _w(R,400)
    if not q: return ''
    marks=await pg.locator('#board mark').count(); 
    st=await pg.locator('#searchStatus').inner_text()
    cols=await pg.evaluate("()=>[...document.querySelectorAll('#board > *')].map(d=>d.className+':'+Math.round(d.getBoundingClientRect().width))")
    return f'marks {marks}, status "{st}", columns {cols}'
async def _export_menu(R,which):
    pg=R.pg
    async def click():
        await pg.get_by_role('button',name=re.compile('^Export '+which,re.I)).first.click()
    return await R.download(click)
async def export_ics(R): return await _export_menu(R,r'\.ics')
async def export_json(R): return await _export_menu(R,'json')
async def import_json(R,path):
    pg=R.pg
    await pg.locator('#importFile').set_input_files(path); await _w(R,600)
    t=await pg.evaluate("()=>[...document.querySelectorAll('#toasts, #storageNotice, #importError, [role=alert]')].filter(e=>!e.hidden).map(e=>e.innerText.trim()).join(' / ')")
    return t[:200]
async def undo(R): 
    b=R.pg.locator('#undoBtn')
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150)
async def redo(R): 
    b=R.pg.locator('#redoBtn')
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150)
async def focus_page(R):
    await R.pg.evaluate("()=>{document.activeElement&&document.activeElement.blur()}")
async def edit_trip(R,name=None,start=None,end=None):
    pg=R.pg; await pg.get_by_role('button',name='Edit trip',exact=True).click(); await _w(R)
    d=pg.locator('#tripDialog')
    if name is not None: await d.get_by_label('Trip name').fill(name)
    if start is not None: await d.get_by_label('Start date').fill(start)
    if end is not None: await d.get_by_label('End date').fill(end)
    await _w(R,200); warn=await pg.evaluate("()=>[...document.querySelectorAll('#tripDialog p, #tripDialog [role=status], #tripDialog .warn, #tripDialog .notice')].filter(e=>e.offsetParent&&/unscheduled|move|outside|remov/i.test(e.innerText)).map(e=>e.innerText.trim()).join(' / ')")
    await pg.locator('#tripSubmit').click(); await _w(R,500)
    t=await pg.evaluate("()=>[...document.querySelectorAll('#toasts, #storageNotice, #tray')].map(e=>e.innerText.trim()).join(' / ')")
    if await pg.locator('#tripDialog[open]').count(): await close_dialog(R)
    return f'form warning "{warn}"; after: {t[:300]} … {t[-300:]}'
async def delete_in_dialog(R,title):
    pg=R.pg; ev=[]
    await _open(R,title); R.confirm_answer=False; await pg.locator('#actDelete').click(); await _w(R,300)
    if await pg.locator('#actDialog[open]').count(): await close_dialog(R)
    ev.append(f'dismiss -> still present {await pg.locator(".card-title", has_text=title).count()}')
    await _open(R,title); R.confirm_answer=True; await pg.locator('#actDelete').click(); await _w(R,300); R.confirm_answer=False
    if await pg.locator('#actDialog[open]').count(): await close_dialog(R)
    ev.append(f'accept -> present {await pg.locator(".card-title", has_text=title).count()}')
    ev.append(f'dialogs {[d for d in R.log["dialogs"] if d[0]=="confirm"][-2:]}')
    return ev
async def board_probe(R):
    pg=R.pg; ev=[]
    ev.append(await pg.evaluate("()=>{const b=document.querySelector('#board');return {cols:b.children.length, sw:b.scrollWidth, cw:b.clientWidth, ox:getComputedStyle(b).overflowX, page_sw:document.documentElement.scrollWidth}}"))
    await open_new_trip(R); await fill_trip(R,'TenDays','2026-12-01','2026-12-10',['Ana']); await submit_trip(R)
    ev.append(await pg.evaluate("()=>{const b=document.querySelector('#board');return {cols:b.children.length, sw:b.scrollWidth, cw:b.clientWidth, ox:getComputedStyle(b).overflowX, page_sw:document.documentElement.scrollWidth}}"))
    await delete_current_trip(R,accept=True)
    return ev

async def dialog_probe(R):
    """open the activity dialog from its opener; Tab 25x and Shift+Tab 5x; record whether focus left the dialog; close; record where focus returns"""
    pg=R.pg
    if await trip_count(R)==0:
        await open_new_trip(R); opener='New trip'; dsel='dialog[open]'
    else:
        b=pg.get_by_role('button',name='Add activity to Day 1'); await b.focus(); await pg.keyboard.press('Enter'); await _w(R); opener='Add activity to Day 1'; dsel='dialog[open]'
    outside=0
    for i in range(25):
        await pg.keyboard.press('Tab')
        if not await pg.evaluate("(s)=>!!document.activeElement.closest(s)",dsel): outside+=1
    for i in range(5):
        await pg.keyboard.press('Shift+Tab')
        if not await pg.evaluate("(s)=>!!document.activeElement.closest(s)",dsel): outside+=1
    await pg.keyboard.press('Escape'); await _w(R)
    back=await pg.evaluate("()=>{const e=document.activeElement;return e.tagName+'|'+(e.getAttribute('aria-label')||e.innerText||e.id).slice(0,40)}")
    # reopen for screenshots
    if opener=='New trip': await open_new_trip(R)
    else: await pg.get_by_role('button',name='Add activity to Day 1').click(); await _w(R)
    return f'focus outside dialog on {outside}/30 tab presses; after Escape focus on {back} (opener {opener})'
