"""adapter B02 (habits) - locators only."""
import re, json
DAYS={'Mon':'Monday','Tue':'Tuesday','Wed':'Wednesday','Thu':'Thursday','Fri':'Friday','Sat':'Saturday','Sun':'Sunday'}
async def _w(R,ms=250): await R.pg.wait_for_timeout(ms)
def _dlg(R): return R.pg.locator('dialog[open]')
async def open_add(R):
    await R.pg.locator('header').get_by_role('button',name='New habit').click(); await _w(R)
async def add_form_open(R):
    return await R.pg.locator('dialog[open]').count()>0
async def fill_add(R,name=None,colour_index=None,schedule=None):
    d=_dlg(R)
    if name is not None: await d.get_by_label('Name').fill(name)
    if colour_index is not None: await d.get_by_role('group',name='Colour').get_by_role('radio').nth(colour_index).check(force=True)
    if schedule is not None:
        if schedule=='daily': await d.get_by_role('radio',name='Every day').check(force=True)
        elif schedule[0]=='days':
            await d.get_by_role('radio',name='Some days').check(force=True); await _w(R,150)
            g=d.get_by_role('group',name='Repeat on')
            for k,full in DAYS.items():
                cb=g.get_by_role('checkbox',name=re.compile(full))
                if k in schedule[1]: await cb.check(force=True)
                else: await cb.uncheck(force=True)
        elif schedule[0]=='weekly':
            await d.get_by_role('radio',name='Times a week').check(force=True); await _w(R,150)
            sb=d.get_by_role('spinbutton',name='Times per week'); await sb.fill(str(schedule[1]))
            return f'spin value now {await sb.input_value()}'
    return 'filled'
async def name_value(R):
    return await _dlg(R).get_by_label('Name').input_value()
async def colour_count(R):
    return await _dlg(R).get_by_role('group',name='Colour').get_by_role('radio').count()
async def submit_add(R):
    d=_dlg(R); await d.get_by_role('button',name=re.compile('^(Add habit|Save)')).click(); await _w(R,300)
async def form_errors(R):
    return await R.pg.evaluate("()=>[...document.querySelectorAll('dialog[open] [id$=error]:not([hidden]), dialog[open] .field__error:not([hidden]), dialog[open] [role=alert], dialog[open] .error:not([hidden])')].map(e=>e.innerText.trim()).filter(Boolean)")
async def close_dialog(R):
    for _ in range(2):
        if await R.pg.locator('dialog[open]').count():
            await R.pg.keyboard.press('Escape'); await _w(R)
async def add_habit(R,name,colour_index,schedule):
    await open_add(R); v=await fill_add(R,name=name,colour_index=colour_index,schedule=schedule); await submit_add(R)
    e=await form_errors(R); still=await add_form_open(R)
    if still: await close_dialog(R)
    return f'{name.strip()}: {"NOT saved "+str(e) if still else "saved"} {v if v!="filled" else ""}'
async def habit_names(R):
    return [t.strip() for t in await R.pg.locator('#habits-body article h3').all_inner_texts()] + [t.strip() for t in await R.pg.locator('.arch-row__name').all_inner_texts()]
async def due_names(R):
    return [t.strip() for t in await R.pg.locator('ul[aria-labelledby=due-label] .row__name').all_inner_texts()]
async def notdue_names(R):
    return [t.strip() for t in await R.pg.locator('ul[aria-labelledby=other-label] .row__name').all_inner_texts()]
def _row(R,name): return R.pg.locator('.today-row', has=R.pg.locator('.row__name', has_text=re.compile('^'+re.escape(name)+'$')))
async def toggle_today(R,name):
    r=_row(R,name)
    if await r.count()==0: return 'no row'
    await r.first.click(); await _w(R,200); return 'clicked'
async def today_done(R,name):
    r=_row(R,name)
    if await r.count()==0: return None
    return (await r.first.get_attribute('aria-pressed'))=='true'
def _card(R,name): return R.pg.locator('article', has=R.pg.locator('h3', has_text=re.compile('^'+re.escape(name)+'$'))).first
async def streaks(R,name):
    c=_card(R,name)
    if await c.count()==0: return None
    return (await c.locator('dl').first.inner_text()).replace('\n',' ')
async def habit_colour(R,name):
    c=_card(R,name); return (await c.locator('p').first.inner_text()).strip() if await c.count() else None
async def habit_schedule_text(R,name): return await habit_colour(R,name)
async def heat_cells(R,name):
    c=_card(R,name)
    return await c.locator('[role=group] button').evaluate_all("bs=>bs.map(b=>[b.getAttribute('aria-label'),b.disabled||b.getAttribute('aria-disabled')==='true',/: done/.test(b.getAttribute('aria-label')||'')])")
def _cell(R,name,daymon):
    d,m=daymon.split(); return _card(R,name).locator(f'[role=group] button[aria-label*=" {d} {m}:"]').first
async def heat_click(R,name,daymon):
    if ':' in daymon: daymon=daymon.split(':')[0].split(' ',1)[1]
    b=_cell(R,name,daymon)
    if await b.count()==0: return 'no cell'
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150); return 'clicked'
async def heat_label(R,name,daymon):
    b=_cell(R,name,daymon); return await b.get_attribute('aria-label') if await b.count() else None
async def edit(R,name,new_name=None,colour_index=None,schedule=None):
    name_new=new_name
    await R.pg.get_by_role('button',name=f'Edit {name}',exact=True).click(); await _w(R)
    await fill_add(R,name=name_new,colour_index=colour_index,schedule=schedule)
    await submit_add(R); still=await add_form_open(R); e=await form_errors(R)
    if still: await close_dialog(R); return f'not saved {e}'
    return 'saved'
async def archive(R,name):
    await R.pg.get_by_role('button',name=f'Archive {name}',exact=True).click(); await _w(R)
async def restore(R,name):
    await R.pg.get_by_role('button',name=f'Restore {name}',exact=True).click(); await _w(R)
async def archived_names(R):
    return [t.strip() for t in await R.pg.locator('.arch-row__name').all_inner_texts()]
async def delete(R,name):
    await R.pg.get_by_role('button',name=f'Delete {name}',exact=True).click(); await _w(R,300)
async def undo(R):
    b=R.pg.locator('header button[aria-label^="Undo"]').first
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150)
async def toast(R):
    return (await R.pg.locator('#toast-region').inner_text()).strip().replace('\n',' ')
async def focus_page(R):
    await R.pg.evaluate("()=>{document.activeElement&&document.activeElement.blur()}")
async def keyboard_rows(R):
    pg=R.pg; rows=pg.locator('.today-row'); n=await rows.count()
    await rows.first.focus(); a=await pg.evaluate("()=>document.activeElement.innerText.split('\\n')[0]")
    await pg.keyboard.press('ArrowDown'); b=await pg.evaluate("()=>document.activeElement.innerText.split('\\n')[0]")
    await pg.keyboard.press('ArrowDown'); c=await pg.evaluate("()=>document.activeElement.innerText.split('\\n')[0]")
    await pg.keyboard.press('ArrowUp'); d=await pg.evaluate("()=>document.activeElement.innerText.split('\\n')[0]")
    return f'{n} rows; focus {a} -ArrowDown-> {b} -ArrowDown-> {c} -ArrowUp-> {d}'
async def keyboard_space(R):
    pg=R.pg; rows=pg.locator('.today-row'); await rows.first.focus(); await pg.keyboard.press('ArrowDown')
    nm=await pg.evaluate("()=>document.activeElement.querySelector('.row__name')?.innerText")
    a=await today_done(R,nm); await pg.keyboard.press('Space'); await _w(R,250); b=await today_done(R,nm)
    await pg.keyboard.press('Space'); await _w(R,250); c=await today_done(R,nm)
    return f'focused {nm}: done {a} -Space-> {b} -Space-> {c}'
async def export_json(R):
    return await R.download(lambda: R.pg.get_by_role('button',name='Export JSON').click())
def make_import(data):
    d=json.loads(json.dumps(data)); hs=d['habits'] if isinstance(d,dict) and 'habits' in d else d
    gym=[h for h in hs if h.get('name')=='Gym'][0]
    key=[k for k in gym if isinstance(gym[k],(list,dict)) and k not in ('days','weekdays','schedule')]
    ck=[k for k in gym if k.lower().startswith('check') or k in('done','dates','log','history')][0]
    if isinstance(gym[ck],list): gym[ck].append('2026-10-02')
    else: gym[ck]['2026-10-02']=True
    import copy; y=copy.deepcopy([h for h in hs if h.get('name')=='Stretch'][0]); y['name']='Yoga'; y['id']='yoga-import-1'
    y[ck]=['2026-10-21'] if isinstance(gym[ck],list) else {'2026-10-21':True}
    hs.append(y); return d
async def import_json(R,path):
    await R.pg.evaluate("()=>{const t=document.querySelector('#toast-region'); if(t) t.innerHTML=''}")
    await R.pg.locator('#import-file').set_input_files(path); await _w(R,600)
    err=await R.pg.locator('#import-error').inner_text() if await R.pg.locator('#import-error').count() else ''
    return 'toast: '+await toast(R) + ' / error: ' + err.strip()
async def today_header(R):
    return (await R.pg.locator('#today-title').inner_text()).strip()
async def dialog_probe(R):
    pg=R.pg; b=pg.locator('header').get_by_role('button',name='New habit'); await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
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
    return f'focus outside dialog on {outside}/30 tab presses; after Escape focus on {back} (opener New habit)'
