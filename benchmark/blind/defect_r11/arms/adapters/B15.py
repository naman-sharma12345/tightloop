"""adapter B15 (trip, arms round) - locators only (from the B01 adapter, parameterised)."""
import re
C={'trip_dlg': '#tripDialog', 'act_dlg': '#activityDialog', 'trip_count_js': "()=>document.querySelector('#tripView').hidden?0:document.querySelectorAll('#tripSelect option').length", 'new_trip': '#newTripBtn', 't_name': '#tName', 't_start': '#tStart', 't_end': '#tEnd', 'trav_lbl': 'Traveller {} name', 'add_trav': 'Add traveller', 't_submit': '#tripSave', 'errors': 'dialog[open] .err, dialog[open] [role=alert]', 'close_sel': 'button[aria-label="Close dialog"]', 'del_trip': '#deleteTripBtn', 'travellers': '#tripHeadMain ul.travellers li', 'days': '#board section.day', 'card': 'li.card', 'card_title': '.card-title', 'tray': '#tray', 'a_title': '#fTitle', 'a_day': '#fDay', 'a_start': '#fStart', 'dur_kind': 'select', 'a_dur': '#fDuration', 'a_place': '#fPlace', 'a_cost': '#fCost', 'a_paid': '#fPaidBy', 'a_split': '#splitGroup', 'a_notes': '#fNotes', 'a_submit': '#actSave', 'a_delete': '#actDelete', 'a_cats': '#catGroup', 'day_add': 'button.add-day', 'conflict': '.conflict-note', 'card_open': 'button.card-title', 'move_lbl': 'Move {} to another day', 'time': '.time', 'budget': '#budget', 'search': '#searchInput', 'board': '#board', 'search_status': '#searchStatus', 'ics_btn': '#icsBtn', 'json_btn': '#jsonBtn', 'import_file': '#importFile', 'import_msg': '#toast, #notice:not([hidden]), [role=alert]:not([hidden])', 'undo': '#undoBtn', 'redo': '#redoBtn', 'edit_trip': '#editTripBtn', 'dates_info': '#tDatesHint, #tripDialog .warn, #tripDialog .notice, #eTEnd', 'after_edit': '#toast, #notice, #tray'}
async def _w(R,ms=250): await R.pg.wait_for_timeout(ms)
def _td(R): return R.pg.locator(C['trip_dlg'])
def _ad(R): return R.pg.locator(C['act_dlg'])
async def trip_count(R):
    return await R.pg.evaluate(C['trip_count_js'])
async def open_new_trip(R):
    await R.pg.locator(C['new_trip']).first.click(); await _w(R)
async def fill_trip(R,name,start,end,travellers):
    pg=R.pg; d=_td(R)
    await d.locator(C['t_name']).fill(name)
    await d.locator(C['t_start']).fill(start); await d.locator(C['t_end']).fill(end)
    added=0
    if C.get('trav_mode')=='chips':
        while await d.locator(C['chip_x']).count(): await d.locator(C['chip_x']).first.click(); await _w(R,80)
        for i,n in enumerate(travellers):
            k=await d.locator(C['chips']).count()
            ab=d.locator(C['add_trav_btn'])
            if not await ab.is_visible() or await ab.is_disabled() or not await d.locator(C['trav_input']).is_editable(): return f'add button gone/disabled at #{i+1}'
            await d.locator(C['trav_input']).fill(n); await ab.click(); await _w(R,100)
            if await d.locator(C['chips']).count()==k: return f'add refused at #{i+1}: {await form_errors(R)}'
            added+=1
        return f'filled {added}'
    for i,n in enumerate(travellers):
        box=d.get_by_label(C['trav_lbl'].format(i+1),exact=True)
        if await box.count()==0:
            btn=d.get_by_role('button',name=C['add_trav'])
            if await btn.count()==0 or not await btn.is_visible() or await btn.is_disabled(): return f'add button gone/disabled at #{i+1}'
            await btn.click(); await _w(R,100)
            if await box.count()==0: return f'no box #{i+1}'
        await box.fill(n); added+=1
    if not travellers:
        await d.get_by_label(C['trav_lbl'].format(1),exact=True).fill('')
    return f'filled {added}'
async def submit_trip(R):
    await _td(R).locator(C['t_submit']).click(); await _w(R,400)
async def form_errors(R):
    return await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden&&e.offsetParent!==null).map(e=>e.innerText.trim()).filter(Boolean)",C['errors'])
async def close_dialog(R):
    pg=R.pg
    if await pg.locator('dialog[open]').count():
        await pg.keyboard.press('Escape'); await _w(R)
    if await pg.locator('dialog[open]').count():
        await pg.locator('dialog[open] '+C['close_sel']).first.click(); await _w(R)
    if await pg.get_by_role('menu').count():
        await pg.keyboard.press('Escape'); await _w(R)
async def delete_current_trip(R,accept=True):
    R.confirm_answer=accept
    await R.pg.locator(C['del_trip']).first.click(); await _w(R,400)
    if C.get('del_trip_confirm') and await R.pg.locator('dialog[open]').count():
        if accept: await R.pg.locator(C['del_trip_confirm']).first.click()
        else: await close_dialog(R)
        await _w(R,300)
    R.confirm_answer=False
async def current_travellers(R):
    return await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].map(e=>e.innerText.replace(/\\n/g,' ').trim())",C['travellers'])
def _days(R): return R.pg.locator(C['days'])
async def ndays(R):
    return await _days(R).count()
def _day(R,day): return _days(R).nth(day-1)
JS_T="es=>es.map(e=>{const c=e.cloneNode(true);c.querySelectorAll('.sr-only,.visually-hidden,.vh').forEach(x=>x.remove());return c.textContent.replace(/\\s+/g,' ').trim()})"
async def day_titles(R,day):
    return await _day(R,day).locator(C['card']+' '+C['card_title']).evaluate_all(JS_T)
async def unscheduled_titles(R):
    return await R.pg.locator(C['tray']+' '+C['card']+' '+C['card_title']).evaluate_all(JS_T)
async def _fill_act(R,title=None,start=None,duration=None,place=None,category=None,cost=None,paid=None,split=None,notes=None,day=None):
    d=_ad(R)
    if title is not None: await d.locator(C['a_title']).fill(title)
    if day is not None: await d.locator(C['a_day']).select_option(index=day-1)
    if start is not None: await d.locator(C['a_start']).fill(start)
    if duration is not None:
        if C['dur_kind']=='select': await d.locator(C['a_dur']).select_option(str(duration))
        elif C['dur_kind']=='hm':
            await d.locator(C['a_dur_h']).fill(str(int(duration)//60)); await d.locator(C['a_dur_m']).fill(str(int(duration)%60))
        else: await d.locator(C['a_dur']).fill(str(duration))
    if category is not None: await d.get_by_role('radio',name=category).check(force=True)
    if place is not None: await d.locator(C['a_place']).fill(place)
    if cost is not None: await d.locator(C['a_cost']).fill(cost)
    if paid is not None: await d.locator(C['a_paid']).select_option(label=paid)
    if split is not None:
        for n in ['Ana','Ben','Cy']:
            cb=d.locator(C['a_split']).get_by_role('checkbox',name=n)
            if await cb.count():
                if n in split: await cb.check(force=True)
                else: await cb.uncheck(force=True)
    if notes is not None: await d.locator(C['a_notes']).fill(notes)
async def _add_btn(R,day): return _day(R,day).locator(C['day_add']).first
async def add_activity(R,day,title,start,dur,place,cat,cost=None,submit=True,**kw):
    pg=R.pg
    await (await _add_btn(R,day)).click(); await _w(R)
    await _fill_act(R,title=title,start=start,duration=dur,place=place,category=cat,cost=cost,**kw)
    if submit:
        await _ad(R).locator(C['a_submit']).click(); await _w(R,300)
        if title and await pg.locator(C['act_dlg']+'[open]').count(): await close_dialog(R)
async def duration_probe(R):
    pg=R.pg
    await (await _add_btn(R,1)).click(); await _w(R)
    if C['dur_kind']=='select':
        opts=await _ad(R).locator(C['a_dur']+' option').all_inner_texts(); await close_dialog(R)
        return f'select with {len(opts)} options: first {opts[:2]} last {opts[-2:]} (values not offerable outside the list)'
    ev=[]
    for v in C.get('dur_bad',['0','721']):
        await _ad(R).locator(C['a_title']).fill('DurProbe'); await _ad(R).locator(C['a_dur']).fill(v); await _ad(R).locator(C['a_submit']).click(); await _w(R)
        ev.append((v, await pg.locator(C['act_dlg']+'[open]').count(), await form_errors(R)))
        if not await pg.locator(C['act_dlg']+'[open]').count(): await (await _add_btn(R,1)).click(); await _w(R)
    await close_dialog(R); return f'number field probe {ev}'
async def conflict_texts(R,day):
    return [t.strip().replace('\n',' ') for t in await _day(R,day).locator(C['card']+' '+C['conflict']).all_inner_texts()]
def _card(R,title): return R.pg.locator(C['card'], has=R.pg.locator(C['card_title'], has_text=title)).first
async def _open(R,title):
    await _card(R,title).locator(C['card_open']).first.click(); await _w(R)
async def edit_activity(R,which,**kw):
    await _open(R,which); await _fill_act(R,**kw)
    await _ad(R).locator(C['a_submit']).click(); await _w(R,300)
    err=await form_errors(R)
    if await R.pg.locator(C['act_dlg']+'[open]').count(): await close_dialog(R); return f'not saved, errors {err}'
    return 'saved'
async def read_activity(R,title):
    await _open(R,title); d=_ad(R)
    v={}
    for k in ['title','start','place','cost','notes']: v[k]=await d.locator(C['a_'+k]).input_value()
    if C['dur_kind']=='hm': v['duration']=str(int(await d.locator(C['a_dur_h']).input_value() or 0)*60+int(await d.locator(C['a_dur_m']).input_value() or 0))
    else: v['duration']=await d.locator(C['a_dur']).input_value()
    c=d.locator(C['a_cats']+' input:checked'); v['category']=await c.get_attribute('value') if await c.count() else None
    await close_dialog(R); return v
async def category_icons(R):
    await (await _add_btn(R,1)).click(); await _w(R)
    m=await R.pg.evaluate("(s)=>[...document.querySelectorAll(s+' label')].map(l=>l.innerText.trim()+':'+((l.querySelector('svg')||{}).innerHTML||'NOSVG').slice(0,40))",C['a_cats'])
    await close_dialog(R)
    cards=await R.pg.evaluate("([c,t])=>[...document.querySelectorAll(c)].slice(0,6).map(e=>(e.querySelector(t)||{}).innerText+':'+((e.querySelector('svg')||{}).outerHTML||'NOSVG').slice(0,60)+':'+((e.querySelector('.cat-tag,.cat-badge,.cat')||{}).innerText||''))",[C['card'],C['card_title']])
    return f'picker {m}; cards {cards}'
async def split_probe(R,title):
    d=_ad(R); ev=[]; o=C['act_dlg']+'[open]'
    await _open(R,title); await d.locator(C['a_paid']).select_option(label='Ana')
    for n in ['Ana','Ben','Cy']: await d.locator(C['a_split']).get_by_role('checkbox',name=n).uncheck(force=True)
    await d.locator(C['a_submit']).click(); await _w(R)
    ev.append(f'split none -> dialog open {await R.pg.locator(o).count()} errors {await form_errors(R)}')
    if not await R.pg.locator(o).count(): await _open(R,title)
    await d.locator(C['a_split']).get_by_role('checkbox',name='Ana').check(force=True); await d.locator(C['a_split']).get_by_role('checkbox',name='Ben').check(force=True)
    await d.locator(C['a_submit']).click(); await _w(R)
    ev.append(f'Ana+Ben -> dialog open {await R.pg.locator(o).count()}')
    if await R.pg.locator(o).count(): await close_dialog(R)
    await _open(R,title); pb=await d.locator(C['a_paid']).input_value()
    sp=await d.locator(C['a_split']+' input:checked').count(); await close_dialog(R)
    ev.append(f'reopen paid-by value {pb}, split checked {sp}')
    return ev
async def close_probe(R,title):
    pg=R.pg; ev=[]; o=C['act_dlg']+'[open]'
    await _open(R,title); await pg.locator(o+' '+C['close_sel']).first.click(); await _w(R); ev.append(f'button: open={await pg.locator(o).count()}')
    await close_dialog(R)
    await _open(R,title); await pg.keyboard.press('Escape'); await _w(R); ev.append(f'Escape: open={await pg.locator(o).count()}')
    await close_dialog(R)
    await _open(R,title); await pg.mouse.click(5,400); await _w(R); ev.append(f'backdrop: open={await pg.locator(o).count()}')
    await close_dialog(R); return ev
async def drag(R,title,day):
    pg=R.pg; src=_card(R,title); dst=_day(R,day)
    vh=pg.viewport_size['height']; vw=pg.viewport_size['width']
    await dst.scroll_into_view_if_needed(); await src.scroll_into_view_if_needed(); await _w(R,150)
    a=await src.bounding_box(); b=await dst.bounding_box()
    if a and b and a['y']>=0 and a['y']+20<=vh and b['y']<vh-30 and b['y']+b['height']>30 and 0<=b['x']+b['width']/2<=vw:
        y0=a['y']+min(a['height']/2,30); ty=(max(b['y'],0)+min(b['y']+b['height'],vh))/2  # middle of the visible part of the day column
        await pg.mouse.move(a['x']+a['width']/2,y0); await pg.mouse.down(); await pg.mouse.move(a['x']+a['width']/2+6,y0+4,steps=3); await _w(R,150)  # human-paced: let the drag start settle
        await pg.mouse.move(b['x']+b['width']/2,ty,steps=15); await _w(R,100); await pg.mouse.up(); await _w(R,400)
        if title in ' '.join(await day_titles(R,day)): return 'manual mouse (both in view)'
    await _card(R,title).drag_to(dst); await _w(R,400)
    return f'drag_to (src box {a}, day box {b}, viewport {vw}x{vh})'
async def move_menu(R,title,day):
    pg=R.pg
    b=pg.get_by_role('button',name=C['move_lbl'].format(title)).first; await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
    items=await pg.get_by_role(C.get('menu_role','menuitem')).all_inner_texts()
    target=[i for i,t in enumerate(items) if t.strip().startswith(f'Day {day}')]
    if not target: return f'menu items {items}'
    hit=False
    for _ in range(10):
        f=await pg.evaluate("()=>document.activeElement.innerText")
        if f.strip().startswith(f'Day {day}'): hit=True; break
        await pg.keyboard.press('ArrowDown')
    if not hit:
        await pg.keyboard.press('Escape'); await _w(R); return f'Day {day} not reachable by arrow keys (current day?); items {items}'
    await pg.keyboard.press('Enter'); await _w(R,300)
    return f'keyboard menu items {[t.strip().replace(chr(10)," ")[:20] for t in items]}'
async def activity_time(R,title):
    return (await _card(R,title).locator(C['time']).first.inner_text()).replace('\n',' ')
async def budget_text(R):
    return (await R.pg.locator(C['budget']).inner_text()).replace('\n',' | ')
async def search(R,q):
    pg=R.pg; await pg.locator(C['search']).fill(q); await _w(R,400)
    if not q: return ''
    marks=await pg.locator(C['board']+' mark').count()
    st=await pg.evaluate("(s)=>[...document.querySelectorAll(s)].map(e=>e.innerText.trim()).join(' / ')",C['search_status'])
    cols=await pg.evaluate("([d,t,c])=>[...document.querySelectorAll(d+', '+t)].map(x=>x.className+':'+Math.round(x.getBoundingClientRect().width)+':cards'+[...x.querySelectorAll(c)].filter(e=>e.offsetParent&&getComputedStyle(e).opacity!=='0').length)",[C['days'],C['tray'],C['card']])
    vis=await pg.evaluate("([c,t])=>[...document.querySelectorAll(c)].filter(e=>e.offsetParent).map(e=>(e.querySelector(t)||{}).innerText+(e.className.match(/dim|match|hit|fade|mute/)?'('+e.className+')':''))",[C['card'],C['card_title']])
    return f'marks {marks}, status "{st}", columns {cols}, visible cards {vis}'
async def export_ics(R): return await R.download(lambda: R.pg.locator(C['ics_btn']).first.click())
async def export_json(R): return await R.download(lambda: R.pg.locator(C['json_btn']).first.click())
async def import_json(R,path):
    pg=R.pg
    await pg.evaluate("(s)=>{for(const e of document.querySelectorAll(s)) if(/toast/.test(e.id+e.className)) e.textContent=''}",C['import_msg'])
    await pg.locator(C['import_file']).set_input_files(path); await _w(R,600)
    t=await pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden).map(e=>e.innerText.trim()).filter(Boolean).join(' / ')",C['import_msg'])
    if await pg.locator('dialog[open]').count():
        btn=pg.locator('dialog[open]').get_by_role('button',name=re.compile('^(Replace|Import|Yes|Continue|Add)',re.I))
        if await btn.count(): await btn.last.click(); await _w(R,500); t+=' / '+await pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden).map(e=>e.innerText.trim()).filter(Boolean).join(' / ')",C['import_msg'])
    return t[:200]
async def undo(R):
    b=R.pg.locator(C['undo']).first
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150)
async def redo(R):
    b=R.pg.locator(C['redo']).first
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150)
async def focus_page(R):
    await R.pg.evaluate("()=>{document.activeElement&&document.activeElement.blur()}")
async def edit_trip(R,name=None,start=None,end=None):
    pg=R.pg; await pg.locator(C['edit_trip']).first.click(); await _w(R)
    d=_td(R)
    if name is not None: await d.locator(C['t_name']).fill(name)
    if start is not None: await d.locator(C['t_start']).fill(start)
    if end is not None: await d.locator(C['t_end']).fill(end)
    await d.locator(C['t_end']).dispatch_event('change'); await _w(R,200)
    warn=await pg.evaluate("(s)=>[...document.querySelectorAll(s)].map(e=>e.innerText.trim()).join(' ')",C['dates_info'])+' '+' '.join(await form_errors(R))
    await d.locator(C['t_submit']).click(); await _w(R,500)
    if await pg.locator('dialog[open]').count():
        cb=pg.locator('dialog[open]').get_by_role('button',name=re.compile(C.get('shrink_confirm','^(Save|Move|Yes|Continue|Shorten|Apply)'),re.I))
        if await cb.count(): await cb.last.click(); await _w(R,500)
    t=await pg.evaluate("(s)=>[...document.querySelectorAll(s)].map(e=>e.innerText.trim()).join(' / ')",C['after_edit'])
    if await pg.locator(C['trip_dlg']+'[open]').count(): await close_dialog(R)
    return f'form warning "{warn}"; after: {t[:300]} … {t[-300:]}'
async def delete_in_dialog(R,title):
    pg=R.pg; ev=[]; o=C['act_dlg']+'[open]'
    await _open(R,title); R.confirm_answer=False; await _ad(R).locator(C['a_delete']).click(); await _w(R,300)
    if await pg.locator(o).count(): await close_dialog(R)
    ev.append(f'dismiss -> still present {await pg.locator(C["card_title"], has_text=title).count()}')
    await _open(R,title); R.confirm_answer=True; await _ad(R).locator(C['a_delete']).click(); await _w(R,300); R.confirm_answer=False
    if await pg.locator(o).count(): await close_dialog(R)
    ev.append(f'accept -> present {await pg.locator(C["card_title"], has_text=title).count()}')
    ev.append(f'dialogs {[d for d in R.log["dialogs"] if d[0]=="confirm"][-2:]}')
    return ev
async def board_probe(R):
    pg=R.pg; ev=[]
    js="([b,d])=>{const x=document.querySelector(b);return {cols:x.querySelectorAll(d).length, sw:x.scrollWidth, cw:x.clientWidth, ox:getComputedStyle(x).overflowX, page_sw:document.documentElement.scrollWidth}}"
    ev.append(await pg.evaluate(js,[C['board'],C['days']]))
    await open_new_trip(R); await fill_trip(R,'TenDays','2026-12-01','2026-12-10',['Ana']); await submit_trip(R)
    ev.append(await pg.evaluate(js,[C['board'],C['days']]))
    await delete_current_trip(R,accept=True)
    return ev
async def dialog_probe(R):
    pg=R.pg
    if await trip_count(R)==0:
        b=pg.locator(C['new_trip']).first; opener=C['new_trip']
    else:
        b=await _add_btn(R,1); opener='Add activity to Day 1'
    await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
    dsel='dialog[open]'; outside=0
    for i in range(25):
        await pg.keyboard.press('Tab')
        if not await pg.evaluate("(s)=>!!document.activeElement.closest(s)",dsel): outside+=1
    for i in range(5):
        await pg.keyboard.press('Shift+Tab')
        if not await pg.evaluate("(s)=>!!document.activeElement.closest(s)",dsel): outside+=1
    await pg.keyboard.press('Escape'); await _w(R)
    back=await pg.evaluate("()=>{const e=document.activeElement;return e.tagName+'|'+(e.getAttribute('aria-label')||e.innerText||e.id).slice(0,40)}")
    await b.click(); await _w(R)
    return f'focus outside dialog on {outside}/30 tab presses; after Escape focus on {back} (opener {opener})'
