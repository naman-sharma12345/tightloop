"""adapter B08 (habits, arms round) - locators only."""
import re, json, copy
DAYS={'Mon':'Monday','Tue':'Tuesday','Wed':'Wednesday','Thu':'Thursday','Fri':'Friday','Sat':'Saturday','Sun':'Sunday'}
C={'dialog': 'dialog[open]', 'add_btn': '#add-btn', 'name': '#f-name', 'colours': '#habit-form .swatches input[type=radio]', 'r_daily': 'Every day', 'r_days': 'Specific days', 'r_weekly': 'Times a week', 'times': '#f-times', 'submit': '#habit-form button[type=submit]', 'errors': 'dialog[open] .field-error', 'card_names': '#cards article h3', 'arch_names': '#archived .row-name', 'due_names': 'ul[aria-labelledby=due-h] .row-name', 'notdue_names': 'ul[aria-labelledby=other-h] .row-name', 'row': 'li.row', 'row_name': '.row-name', 'row_click': 'button.check', 'row_focus': '#today-body li.row button.check', 'done_js': "e=>e.querySelector('button.check').getAttribute('aria-pressed')==='true'", 'card': '#cards article', 'card_name': 'h3', 'streaks': 'dl.stats', 'colour_js': "c=>{const s=c.querySelector('.badge');return (s?getComputedStyle(s).backgroundColor:'')+' '+(c.querySelector('p.meta')||{}).innerText}", 'sched': 'p.meta', 'cells': '.heat-grid button', 'edit_lbl': 'Edit {}', 'archive_lbl': 'Archive {}', 'restore_lbl': 'Restore {}', 'delete_lbl': 'Delete {}', 'undo': '#undo-btn', 'toast': '#toast', 'export': 'button[data-action=export]', 'import_file': '#import-file', 'import_msg': '#io-error, #notice, #toast', 'header': '#today-date'}
async def _w(R,ms=250): await R.pg.wait_for_timeout(ms)
def _dlg(R): return R.pg.locator(C['dialog'])
async def open_add(R):
    await R.pg.locator(C['add_btn']).first.click(); await _w(R)
async def add_form_open(R):
    return await R.pg.locator(C['dialog']).count()>0
async def fill_add(R,name=None,colour_index=None,schedule=None):
    d=_dlg(R)
    if name is not None: await d.locator(C['name']).fill(name)
    if colour_index is not None: await d.locator(C['colours']).nth(colour_index).check(force=True)
    if schedule is not None:
        if schedule=='daily': await d.get_by_role('radio',name=C['r_daily']).check(force=True)
        elif schedule[0]=='days':
            await d.get_by_role('radio',name=C['r_days']).check(force=True); await _w(R,150)
            for k,full in DAYS.items():
                cb=d.get_by_role('checkbox',name=re.compile('^'+k))
                if k in schedule[1]: await cb.check(force=True)
                else: await cb.uncheck(force=True)
        elif schedule[0]=='weekly':
            await d.get_by_role('radio',name=C['r_weekly']).check(force=True); await _w(R,150)
            sb=d.locator(C['times'])
            try: await sb.fill(str(schedule[1]))
            except Exception as e:
                try: await sb.select_option(str(schedule[1]))
                except Exception as e2: return f'cannot set {schedule[1]}: {str(e2)[:80]}'
            return f'times value now {await sb.input_value()}'
    return 'filled'
async def name_value(R):
    return await _dlg(R).locator(C['name']).input_value()
async def colour_count(R):
    return await _dlg(R).locator(C['colours']).count()
async def submit_add(R):
    await _dlg(R).locator(C['submit']).click(); await _w(R,300)
async def form_errors(R):
    return await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden&&e.offsetParent!==null).map(e=>e.innerText.trim()).filter(Boolean)", C['errors'])
async def close_dialog(R):
    for _ in range(2):
        if await R.pg.locator(C['dialog']).count():
            await R.pg.keyboard.press('Escape'); await _w(R)
async def add_habit(R,name,colour_index,schedule):
    await open_add(R); v=await fill_add(R,name=name,colour_index=colour_index,schedule=schedule); await submit_add(R)
    e=await form_errors(R); still=await add_form_open(R)
    if still: await close_dialog(R)
    return f'{name.strip()}: {"NOT saved "+str(e) if still else "saved"} {v if v!="filled" else ""}'
async def habit_names(R):
    return [t.strip() for t in await R.pg.locator(C['card_names']).all_inner_texts()] + [t.strip() for t in await R.pg.locator(C['arch_names']).all_inner_texts()]
async def due_names(R):
    return [t.strip() for t in await R.pg.locator(C['due_names']).all_inner_texts()]
async def notdue_names(R):
    return [t.strip() for t in await R.pg.locator(C['notdue_names']).all_inner_texts()]
def _row(R,name): return R.pg.locator(C['row'], has=R.pg.locator(C['row_name'], has_text=re.compile('^'+re.escape(name)+'$')))
async def toggle_today(R,name):
    r=_row(R,name)
    if await r.count()==0: return 'no row'
    await r.first.locator(C['row_click']).first.click() if C['row_click'] else await r.first.click()
    await _w(R,200); return 'clicked'
async def today_done(R,name):
    r=_row(R,name)
    if await r.count()==0: return None
    return await r.first.evaluate(C['done_js'])
def _card(R,name): return R.pg.locator(C['card'], has=R.pg.locator(C['card_name'], has_text=re.compile('^'+re.escape(name)+'$'))).first
async def streaks(R,name):
    c=_card(R,name)
    if await c.count()==0: return None
    return (await c.locator(C['streaks']).first.inner_text()).replace('\n',' ')
async def habit_colour(R,name):
    c=_card(R,name)
    if await c.count()==0: return None
    return await c.evaluate(C['colour_js'])
async def habit_schedule_text(R,name):
    c=_card(R,name); return (await c.locator(C['sched']).first.inner_text()).strip() if await c.count() else None
async def heat_cells(R,name):
    c=_card(R,name)
    return await c.locator(C['cells']).evaluate_all("bs=>bs.map(b=>[b.getAttribute('aria-label'),b.disabled||b.getAttribute('aria-disabled')==='true',/: done/i.test(b.getAttribute('aria-label')||'')])")
def _cell(R,name,daymon):
    d,m=daymon.split(); return _card(R,name).locator(C['cells']).and_(R.pg.locator(f'[aria-label*=" {d} {m}"]')).first
async def heat_click(R,name,daymon):
    if ':' in daymon: daymon=daymon.split(':')[0].split(' ',1)[1]
    b=_cell(R,name,daymon)
    if await b.count()==0: return 'no cell'
    if await b.is_disabled() or (await b.get_attribute('aria-disabled'))=='true': return 'disabled'
    await b.click(); await _w(R,150); return 'clicked'
async def heat_label(R,name,daymon):
    b=_cell(R,name,daymon); return await b.get_attribute('aria-label') if await b.count() else None
async def edit(R,name,new_name=None,colour_index=None,schedule=None):
    await R.pg.get_by_role('button',name=C['edit_lbl'].format(name),exact=True).first.click(); await _w(R)
    await fill_add(R,name=new_name,colour_index=colour_index,schedule=schedule)
    await submit_add(R); still=await add_form_open(R); e=await form_errors(R)
    if still: await close_dialog(R); return f'not saved {e}'
    return 'saved'
async def archive(R,name):
    await R.pg.get_by_role('button',name=C['archive_lbl'].format(name),exact=True).first.click(); await _w(R)
async def restore(R,name):
    await R.pg.get_by_role('button',name=C['restore_lbl'].format(name),exact=True).first.click(); await _w(R)
async def archived_names(R):
    return [t.strip() for t in await R.pg.locator(C['arch_names']).all_inner_texts()]
async def delete(R,name):
    await R.pg.get_by_role('button',name=C['delete_lbl'].format(name),exact=True).first.click(); await _w(R,300)
async def undo(R):
    b=R.pg.locator(C['undo']).first
    if await b.is_disabled(): return 'disabled'
    await b.click(); await _w(R,150)
async def toast(R):
    return (await R.pg.locator(C['toast']).first.inner_text()).strip().replace('\n',' ')
async def focus_page(R):
    await R.pg.evaluate("()=>{document.activeElement&&document.activeElement.blur()}")
async def _fname(R):
    return await R.pg.evaluate("([rs,s])=>{const e=document.activeElement; if(!e) return null; const r=e.closest(rs)||e; const n=r.querySelector(s); return n?n.innerText.trim():e.innerText.split('\\n')[0]}", [C['row'],C['row_name']])
async def keyboard_rows(R):
    pg=R.pg; rows=pg.locator(C['row_focus']); n=await rows.count()
    await rows.first.focus(); a=await _fname(R)
    await pg.keyboard.press('ArrowDown'); b=await _fname(R)
    await pg.keyboard.press('ArrowDown'); c=await _fname(R)
    await pg.keyboard.press('ArrowUp'); d=await _fname(R)
    return f'{n} rows; focus {a} -ArrowDown-> {b} -ArrowDown-> {c} -ArrowUp-> {d}'
async def keyboard_space(R):
    pg=R.pg; rows=pg.locator(C['row_focus']); await rows.first.focus(); await pg.keyboard.press('ArrowDown')
    nm=await _fname(R)
    a=await today_done(R,nm); await pg.keyboard.press('Space'); await _w(R,250); b=await today_done(R,nm)
    await pg.keyboard.press('Space'); await _w(R,250); c=await today_done(R,nm)
    return f'focused {nm}: done {a} -Space-> {b} -Space-> {c}'
async def export_json(R):
    return await R.download(lambda: R.pg.locator(C['export']).first.click())
def make_import(data):
    d=json.loads(json.dumps(data)); hs=d['habits'] if isinstance(d,dict) and 'habits' in d else d
    gym=[h for h in hs if h.get('name')=='Gym'][0]
    ck=[k for k in gym if k.lower().startswith('check') or k in('done','dates','log','history','completions')][0]
    if isinstance(gym[ck],list): gym[ck].append('2026-10-02')
    else: gym[ck]['2026-10-02']=True
    y=copy.deepcopy([h for h in hs if h.get('name')=='Stretch'][0]); y['name']='Yoga'; y['id']='yoga-import-1'
    y[ck]=['2026-10-21'] if isinstance(gym[ck],list) else {'2026-10-21':True}
    hs.append(y); return d
async def import_json(R,path):
    await R.pg.evaluate("(s)=>{for(const e of document.querySelectorAll(s)) e.textContent=''}", C['toast'])
    await R.pg.locator(C['import_file']).set_input_files(path); await _w(R,600)
    if await R.pg.locator(C['dialog']).count():
        b=_dlg(R).get_by_role('button',name=re.compile('Replace|Import|Merge',re.I))
        if await b.count(): await b.first.click(); await _w(R,500)
    msg=await R.pg.evaluate("(s)=>[...document.querySelectorAll(s)].filter(e=>!e.hidden).map(e=>e.innerText.trim()).filter(Boolean).join(' / ')", C['import_msg'])
    return msg[:300]
async def today_header(R):
    return (await R.pg.locator(C['header']).first.inner_text()).strip().replace('\n',' ')
async def dialog_probe(R):
    pg=R.pg; b=pg.locator(C['add_btn']).first; await b.focus(); await pg.keyboard.press('Enter'); await _w(R)
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
    return f'focus outside dialog on {outside}/30 tab presses; after Escape focus on {back} (opener {C["add_btn"]})'
