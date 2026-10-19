"""steps_trip.py - checklist items T01-T31 (+ shared G items run by run_build.py).
Same steps, same data, same order for every trip build. Only the adapter (adapters/Bxx.py) knows locators.
Each item returns {'auto': True/False/None, 'ev': str}. None = needs the scorer's look (screenshot/text), decided in verdicts/Bxx.json."""
import json, os, re, asyncio
TRIP=dict(name='Lisbon', start='2026-11-01', end='2026-11-04', travellers=['Ana','Ben','Cy'])
def res(auto,ev): return {'auto':auto,'ev':str(ev)[:600]}
async def safe(fn,*a,**k):
    try: return await fn(*a,**k)
    except Exception as e: return ('ERR',repr(e)[:300])
async def run(R, A, out, evdir):
    pg=R.pg; r={}
    # T31 empty state
    t=await R.text(); r['T31']=res(None,'first load text: '+t[:300].replace('\n',' | '))
    await R.shot(f'{evdir}/t31_empty.png')
    # T02 date rules (in the create form)
    ev=[]
    for (s,e,label) in [('2026-11-04','2026-11-01','end<start'),('2026-11-01','2026-12-01','31 days')]:
        n0=await A.trip_count(R)
        await A.open_new_trip(R); await A.fill_trip(R,'DateTest',s,e,['Ana']); await A.submit_trip(R)
        n1=await A.trip_count(R); err=await A.form_errors(R)
        ev.append(f'{label}: trips {n0}->{n1}, errors={err}'); await A.close_dialog(R)
        if n1>n0: await A.delete_current_trip(R, accept=True)
    n0=await A.trip_count(R)
    await A.open_new_trip(R); await A.fill_trip(R,'OneDay','2026-11-10','2026-11-10',['Ana']); await A.submit_trip(R)
    n1=await A.trip_count(R); ev.append(f'1-day: trips {n0}->{n1}'); await A.close_dialog(R)
    ok1 = 'trips 0->0' in ev[0] or re.search(r'trips (\d+)->\1,',ev[0]) is not None
    ok2 = re.search(r'trips (\d+)->\1,',ev[1]) is not None
    ok3 = n1==n0+1
    r['T02']=res(ok1 and ok2 and ok3 and None, '; '.join(ev))
    if n1>n0: await A.delete_current_trip(R, accept=True)
    # T03 travellers
    ev=[]
    n0=await A.trip_count(R)
    await A.open_new_trip(R); await A.fill_trip(R,'TravTest0','2026-11-01','2026-11-02',[]); await A.submit_trip(R)
    n1=await A.trip_count(R); ev.append(f'0 travellers: trips {n0}->{n1} err={await A.form_errors(R)}'); await A.close_dialog(R)
    if n1>n0: await A.delete_current_trip(R, accept=True)
    await A.open_new_trip(R); n9=await A.fill_trip(R,'TravTest9','2026-11-01','2026-11-02',['A1','A2','A3','A4','A5','A6','A7','A8','A9']); 
    ev.append(f'9th traveller: fill reported {n9}'); n0=await A.trip_count(R); await A.submit_trip(R); n1=await A.trip_count(R)
    tv = await A.current_travellers(R) if n1>n0 else None
    ev.append(f'9 travellers submit: trips {n0}->{n1}, travellers={tv}'); await A.close_dialog(R)
    if n1>n0: await A.delete_current_trip(R, accept=True)
    n0=await A.trip_count(R)
    await A.open_new_trip(R); await A.fill_trip(R,'TravDup','2026-11-01','2026-11-02',['Ana','Ana']); await A.submit_trip(R)
    n1=await A.trip_count(R); ev.append(f'dup Ana: trips {n0}->{n1} err={await A.form_errors(R)}'); await A.close_dialog(R)
    if n1>n0: await A.delete_current_trip(R, accept=True)
    r['T03']=res(None,'; '.join(ev))
    # T01 create
    n0=await A.trip_count(R)
    await A.open_new_trip(R); await A.fill_trip(R,TRIP['name'],TRIP['start'],TRIP['end'],TRIP['travellers']); await A.submit_trip(R)
    n1=await A.trip_count(R); nd=await A.ndays(R)
    r['T01']=res(n1==n0+1 and nd==4, f'trips {n0}->{n1}, days shown {nd}, travellers={await A.current_travellers(R)}')
    await R.shot(f'{evdir}/t01_trip.png')
    # T07 add activity
    await A.add_activity(R,1,'Lunch','12:30',60,'Time Out Market','Food',cost='45')
    d1=await A.day_titles(R,1)
    r['T07']=res('Lunch' in ' '.join(d1), f'day1 titles {d1}')
    # T08 title required
    await A.add_activity(R,1,'','10:00',60,'x','Other',submit=True)
    err=await A.form_errors(R); d1b=await A.day_titles(R,1); await A.close_dialog(R)
    r['T08']=res(len(d1b)==len(d1) and bool(err), f'errors={err}; day1 {d1}->{d1b}')
    # T09 durations
    opts=await A.duration_probe(R)
    r['T09']=res(None, f'duration control: {opts}')
    # T11 cost optional + T13 overlaps
    await A.add_activity(R,1,'Museum','13:00',90,'MNAA','Sight')
    await A.add_activity(R,1,'Coffee','11:30',60,'Cafe','Food')
    d1=await A.day_titles(R,1)
    r['T11']=res('Museum' in ' '.join(d1), f'Museum (no cost) saved: day1 {d1}')
    cf=await A.conflict_texts(R,1)
    r['T13']=res(None, f'conflict texts day1: {cf}')
    await R.shot(f'{evdir}/t13_conflicts.png')
    # T12 sorting
    for ti,tm in [('Walk','15:00'),('Tram','09:00'),('Tile shop','12:00')]:
        await A.add_activity(R,2,ti,tm,30,'Baixa','Other')
    o1=await A.day_titles(R,2)
    await A.edit_activity(R,'Tram',start='16:00')
    o2=await A.day_titles(R,2)
    r['T12']=res(None, f'day2 order after adds {o1}; after Tram->16:00 {o2}')
    # T10 categories/icons
    r['T10']=res(None, f'category control + icons: {await A.category_icons(R)}')
    # T18 detail dialog edits every field + notes
    ok18=await A.edit_activity(R,'Walk',title='Walk Alfama',start='17:00',duration=45,place='Alfama',category='Sight',cost='12.50',notes='line 1\nline 2')
    det=await A.read_activity(R,'Walk Alfama')
    r['T18']=res(None, f'edit result {ok18}; reopened: {det}')
    # T19 paid by / split
    ev19=await A.split_probe(R,'Lunch')
    r['T19']=res(None, f'{ev19}')
    # T20 dialog close: button, Escape, backdrop
    r['T20']=res(None, f'{await A.close_probe(R,"Lunch")}')
    # T14 drag Museum day1 -> day3 ; T16 conflicts re-check
    before=await A.day_titles(R,3)
    await A.drag(R,'Museum',3)
    d1=await A.day_titles(R,1); d3=await A.day_titles(R,3)
    r['T14']=res(any('Museum' in x for x in d3), f'day3 before {before}; after drag day1 {d1} day3 {d3}')
    cf1=await A.conflict_texts(R,1); cf3=await A.conflict_texts(R,3)
    # T15 move via keyboard menu: Coffee day1 -> day2
    mv=await A.move_menu(R,'Coffee',2)
    d1=await A.day_titles(R,1); d2=await A.day_titles(R,2)
    r['T15']=res(any('Coffee' in x for x in d2), f'menu result {mv}; day1 {d1}; day2 {d2}')
    # move Lunch into day 3 where Museum 13:00-14:30 sits -> new overlap
    mv2=await A.move_menu(R,'Lunch',3) if any('Coffee' in x for x in d2) else await A.drag(R,'Lunch',3)
    cf3b=await A.conflict_texts(R,3); t3=await A.activity_time(R,'Lunch')
    r['T16']=res(None, f'after Museum leaves day1: day1 conflicts {cf1}; day3 conflicts {cf3}; Lunch moved to day3 -> day3 conflicts {cf3b}; Lunch time text {t3}')
    await R.shot(f'{evdir}/t16_moved.png')
    # T22 budget: put Lunch (45, Food) back on day 1 as the checklist's setup states; add Transport 30 day2, Food 25 day2
    if any('Lunch' in x for x in await A.day_titles(R,3)): await A.move_menu(R,'Lunch',1)
    await A.add_activity(R,2,'Train','08:00',30,'Station','Transport',cost='30')
    await A.add_activity(R,2,'Snack','20:00',15,'Kiosk','Food',cost='25')
    # Walk Alfama has 12.50 from T18 -> remove cost to keep the fixed data
    await A.edit_activity(R,'Walk Alfama',cost='')
    b=await A.budget_text(R)
    r['T22']=res(None, f'budget (Lunch 45 Food day1, Train 30 Transport day2, Snack 25 Food day2; expected total 100, Food 70, Transport 30, day1 45, day2 55): {b}')
    await R.shot(f'{evdir}/t22_budget.png')
    # T23 settle-up: only 100 paid Ana split all; 30 paid Ben split Ben+Cy
    await A.edit_activity(R,'Lunch',cost='100',paid='Ana',split=['Ana','Ben','Cy'])
    await A.edit_activity(R,'Train',cost='30',paid='Ben',split=['Ben','Cy'])
    await A.edit_activity(R,'Snack',cost='')
    b=await A.budget_text(R)
    r['T23']=res(None, f'settle text: {b}')
    await R.shot(f'{evdir}/t23_settle.png')
    # T27 search
    s1=await A.search(R,'market'); s2=await A.search(R,'museum'); await A.search(R,'')
    r['T27']=res(None, f'search market: {s1}; search museum: {s2}')
    # T28 ics
    sched={}
    for d in range(1,(await A.ndays(R))+1):
        for ti in await A.day_titles(R,d): sched[ti]=d
    p=await A.export_ics(R); ics=open(p,encoding='utf-8',errors='replace').read() if p else None
    if ics: open(f'{evdir}/export.ics','w').write(ics)
    rows=[]
    if ics:
        for e in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT',ics.replace('\r',''),re.S):
            g=lambda k: (re.search(k+r'[^:\n]*:(.*)',e) or [None,None])[1]
            rows.append((g('SUMMARY'),g('DTSTART'),g('DTEND'),g('DURATION')))
    r['T28']=res(None, f'scheduled activities by day {sched}; ics file {os.path.basename(p) if p else None}: {len(rows)} VEVENTs {rows}; header ok {bool(ics and ics.lstrip().startswith("BEGIN:VCALENDAR"))}')
    # T29 json export
    pj=await A.export_json(R); out['json_export']=pj
    r['T29_export']=res(bool(pj), f'json export {pj and open(pj).read()[:300]}')
    # T24/T25 undo redo
    n_before=await A.day_titles(R,4)
    await A.add_activity(R,4,'UndoMe','10:00',30,'X','Other')
    a1=await A.day_titles(R,4); await A.undo(R); a2=await A.day_titles(R,4); await A.redo(R); a3=await A.day_titles(R,4)
    r['T24']=res(any('UndoMe' in x for x in a1) and not any('UndoMe' in x for x in a2) and any('UndoMe' in x for x in a3), f'day4 add {a1}; undo {a2}; redo {a3}')
    await pg.locator('body').click(position={'x':5,'y':5}) if False else None
    await A.focus_page(R)
    await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(300); k1=await A.day_titles(R,4)
    await A.focus_page(R)
    await pg.keyboard.press('Control+Shift+z'); await pg.wait_for_timeout(300); k2=await A.day_titles(R,4)
    r['T25']=res(not any('UndoMe' in x for x in k1) and any('UndoMe' in x for x in k2), f'Ctrl+Z -> {k1}; Shift+Ctrl+Z -> {k2}')
    # T26 undo depth 20: 21 adds on day 4, then 20 undos
    base=await A.day_titles(R,4)
    for i in range(1,22): await A.add_activity(R,4,f'U{i:02d}','06:00' if i<10 else '07:00',15,'','Other')
    full=await A.day_titles(R,4)
    for i in range(20): await A.undo(R)
    left=await A.day_titles(R,4)
    extra=await A.undo(R)
    left2=await A.day_titles(R,4)
    r['T26']=res(None, f'base {base}; after 21 adds {len(full)} items; after 20 undos {left}; 21st undo -> {left2}')
    # restore to a clean state: redo nothing; remove U01 if present
    # T17 shorten trip: activity on day 4 (UndoMe or U01) -> end 2026-11-02
    d4=await A.day_titles(R,4)
    msg=await A.edit_trip(R,end='2026-11-02')
    t=await R.text()
    unsched=await A.unscheduled_titles(R)
    r['T17']=res(None, f'day4 before {d4}; day3 had Lunch/Museum; after end->11-02 message: {msg}; unscheduled: {unsched}; days now {await A.ndays(R)}')
    await R.shot(f'{evdir}/t17_shorten.png')
    await A.edit_trip(R,end='2026-11-04')
    # T04 rename
    await A.edit_trip(R,name='Lisbon & Porto')
    await pg.reload(); await pg.wait_for_timeout(800)
    t=await R.text(); r['T04']=res('Lisbon & Porto' in t, 'after rename+reload name present: '+str('Lisbon & Porto' in t))
    # G06 reload persistence evidence
    r['G06']=res(None, 'after reload text: '+t[:400].replace('\n',' | '))
    # T21 delete in dialog
    r['T21']=res(None, f'{await A.delete_in_dialog(R,"Museum")}')
    # T06 columns + 10-day trip board scroll
    r['T06']=res(None, f'{await A.board_probe(R)}')
    # T30 bad import
    bad1=os.path.join(R.dl_dir,'bad.json'); open(bad1,'w').write('this is not json')
    bad2=os.path.join(R.dl_dir,'bad2.json'); open(bad2,'w').write('{"foo":1}')
    before=await R.text()
    e1=await A.import_json(R,bad1); mid=await R.text(); e2=await A.import_json(R,bad2); after=await R.text()
    r['T30']=res(None, f'bad text import msg={e1}; shape import msg={e2}; data unchanged={("Lisbon & Porto" in after) and (before.count("Lunch")==after.count("Lunch"))}')
    # T05 delete trip confirm
    n0=await A.trip_count(R); R.confirm_answer=False; await A.delete_current_trip(R, accept=False); n1=await A.trip_count(R)
    dl=[d for d in R.log['dialogs'] if d[0]=='confirm']
    r['T05_dismiss']=res(n1==n0 and len(dl)>0, f'dismiss: trips {n0}->{n1}, confirm dialogs so far {len(dl)}')
    out['items']=r
    return r
async def run_import_fresh(R, A, path):
    """T29 import into a fresh profile"""
    m=await A.import_json(R,path); await R.pg.wait_for_timeout(500); t=await R.text()
    return res(('Lisbon' in t) and ('Lunch' in t) and ('Ana' in t), f'import msg {m}; text after: '+t[:500].replace('\n',' | '))
async def run_delete_accept(R,A):
    n0=await A.trip_count(R); await A.delete_current_trip(R, accept=True); n1=await A.trip_count(R)
    return res(n1==n0-1, f'accept delete: trips {n0}->{n1}')

async def flow375(R,A,evdir):
    ev=[]
    await A.open_new_trip(R); await R.shot(f'{evdir}/g09_375_form.png'); await A.fill_trip(R,'Lisbon','2026-11-01','2026-11-04',['Ana','Ben']); await A.submit_trip(R)
    ev.append(f'trip created: {await A.trip_count(R)}')
    await A.add_activity(R,1,'Lunch','12:30',60,'Market','Food',cost='45')
    await A.add_activity(R,1,'Museum','13:00',90,'MNAA','Sight')
    ev.append(f'day1 {await A.day_titles(R,1)}')
    ev.append(f'budget visible text: {(await A.budget_text(R))[:120]}')
    return ev
