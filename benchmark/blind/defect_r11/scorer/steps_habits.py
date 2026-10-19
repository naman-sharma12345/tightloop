"""steps_habits.py - checklist items H01-H35. Same steps/data/order for every habits build; adapter holds locators.
Clock: installed at Thu 22 Oct 2026 10:00 Asia/Kolkata. History is made through the app's own UI by moving the clock (set_system_time + reload)."""
import json, os, re
def res(auto,ev): return {'auto':auto,'ev':str(ev)[:700]}
TZ='+05:30'
async def goto_day(R,iso,hm='10:00:00'):
    await R.pg.clock.set_system_time(f'{iso}T{hm}{TZ}'); await R.pg.reload(); await R.pg.wait_for_timeout(700)
async def run(R,A,out,evdir):
    pg=R.pg; r={}
    t=await R.text(); r['H35']=res(None,'first load: '+t[:300].replace('\n',' | ')); await R.shot(f'{evdir}/h35_empty.png')
    # ---------- history setup through the UI (clock moved back) ----------
    await goto_day(R,'2026-10-06')
    setup=[]
    setup.append(await A.add_habit(R,'Swim',None,('weekly',2)))
    setup.append(await A.add_habit(R,'Gym',None,('days',['Mon','Wed','Fri'])))
    setup.append(await A.add_habit(R,'Stretch',None,'daily'))
    setup.append(await A.add_habit(R,'Floss',None,'daily'))
    plan={'2026-10-06':['Swim'],'2026-10-07':['Swim'],'2026-10-13':['Swim','Stretch'],'2026-10-14':['Swim','Stretch'],'2026-10-15':['Stretch'],
          '2026-10-16':['Gym','Stretch'],'2026-10-17':['Stretch'],'2026-10-18':['Stretch'],'2026-10-19':['Gym'],'2026-10-20':['Swim','Stretch','Floss'],'2026-10-21':['Gym','Stretch','Swim']}
    swim_before_w=None; swim_after_w=None
    for day,names in plan.items():
        await goto_day(R,day)
        if day=='2026-10-21': swim_before_w=await A.streaks(R,'Swim')
        for n in names:
            ok=await A.toggle_today(R,n); setup.append(f'{day} {n} {ok}')
        if day=='2026-10-21': swim_after_w=await A.streaks(R,'Swim')
    await goto_day(R,'2026-10-22')
    for n in ['Stretch','Floss']: setup.append(f'22 {n} {await A.toggle_today(R,n)}')
    out['setup']=setup
    st=await A.streaks(R,'Stretch'); gy=await A.streaks(R,'Gym'); sw=await A.streaks(R,'Swim')
    r['H11']=res(None,f'Stretch (daily; 13-18, 20-22 Oct checked) streaks {st}; expected current 3 best 6')
    r['H12']=res(None,f'Gym (Mon/Wed/Fri; Fri16 Mon19 Wed21) streaks {gy}; expected current 3')
    r['H13']=res(None,f'Swim (2/week; 6+7, 13+14, 20 Oct): on Wed 21 before check {swim_before_w}; after check Wed 21 {swim_after_w}; on Thu 22 {sw}; expected 2 then 3 (weeks)')
    await R.shot(f'{evdir}/h11_streaks.png')
    # ---------- add-form rules ----------
    n0=await A.habit_names(R)
    e=[]
    for nm in ['','   ']:
        await A.open_add(R); await A.fill_add(R,name=nm); await A.submit_add(R); e.append((repr(nm),await A.form_errors(R))); await A.close_dialog(R)
    n1=await A.habit_names(R)
    r['H03']=res(len(n1)==len(n0) and all(x[1] for x in e), f'habits {n0}->{n1}; errors {e}')
    r['H01']=res(None,'')
    res1=await A.add_habit(R,'Read',None,'daily'); due=await A.due_names(R)
    r['H01']=res('Read' in due, f'add Read daily -> {res1}; due today {due}')
    await A.open_add(R); cc=await A.colour_count(R); await A.close_dialog(R)
    r2=await A.add_habit(R,'  Walk  ',1,'daily'); names=await A.habit_names(R)
    col=await A.habit_colour(R,'Walk')
    r['H05']=res(None, f'colour choices {cc}; Walk added with 2nd colour -> shown colour {col}')
    a60='A'*60; a61='B'*61
    r60=await A.add_habit(R,a60,None,'daily')
    await A.open_add(R); await A.fill_add(R,name=a61); v61=await A.name_value(R); await A.submit_add(R); e61=await A.form_errors(R); await A.close_dialog(R)
    names=await A.habit_names(R)
    r['H02']=res(None, f'"  Walk  " saved as {[n for n in names if "Walk" in n]}; 60-char present {a60 in names}; 61-char field value len {len(v61) if v61 else v61}, errors {e61}, 61-char saved {any(n.startswith("B"*61) for n in names)}')
    e=[]
    for nm in ['read',' READ ']:
        await A.open_add(R); await A.fill_add(R,name=nm); await A.submit_add(R); e.append((nm,await A.form_errors(R))); await A.close_dialog(R)
    names2=await A.habit_names(R)
    r['H04']=res(len(names2)==len(names) and all(x[1] for x in e), f'habits {len(names)}->{len(names2)}; errors {e}')
    # weekdays none / N out of range
    await A.open_add(R); await A.fill_add(R,name='NoDays',schedule=('days',[])); await A.submit_add(R); e0=await A.form_errors(R); await A.close_dialog(R)
    nd=await A.habit_names(R)
    due=await A.due_names(R); notdue=await A.notdue_names(R)
    r['H06']=res(None, f'zero weekdays: errors {e0}, NoDays saved {"NoDays" in nd}; Gym in due {"Gym" in due}, in not-due {"Gym" in notdue}; due {due}; not due {notdue}')
    e=[]
    for n in [0,8]:
        await A.open_add(R); v=await A.fill_add(R,name=f'N{n}',schedule=('weekly',n)); await A.submit_add(R); e.append((n,v,await A.form_errors(R))); await A.close_dialog(R)
    nd=await A.habit_names(R)
    r['H07']=res(None, f'N=0/8 attempts {e}; saved N0 {"N0" in nd} N8 {"N8" in nd}; Swim 2/week was saved in setup ({"Swim" in nd})')
    # ---------- today check/uncheck ----------
    await A.toggle_today(R,'Read'); d1=await A.today_done(R,'Read')
    await R.shot(f'{evdir}/h08_checked.png')
    await A.toggle_today(R,'Read'); d2=await A.today_done(R,'Read')
    r['H08']=res(d1 is True, f'after check Read done={d1}')
    r['H09']=res(d1 is True and d2 is False, f'after second click done={d2}')
    g0=await A.today_done(R,'Gym'); await A.toggle_today(R,'Gym'); g1=await A.today_done(R,'Gym'); await A.toggle_today(R,'Gym')
    r['H10']=res(None, f'Gym (not due Thu) listed in not-due {"Gym" in notdue}; check registered {g0}->{g1}')
    # ---------- heatmap ----------
    cells=await A.heat_cells(R,'Read')
    en=[c for c in cells if not c[1]]
    r['H14']=res(None, f'{len(cells)} cells, {len(en)} enabled; first {cells[:1]}, last enabled {en[-1:]}, after {[c for c in cells if c[1]][:3]}')
    fut=[c for c in cells if c[1]]
    fres=None
    if fut:
        fres=await A.heat_click(R,'Read',fut[0][0]); 
    r['H16']=res(None, f'future cells {[c[0] for c in fut]}; click on first future -> {fres}; cells after {[(c[0]) for c in (await A.heat_cells(R,"Read")) if "Oct 23" in c[0] or "23 Oct" in c[0]]}')
    b=await A.streaks(R,'Stretch')
    c1=await A.heat_click(R,'Stretch','19 Oct'); s1=await A.streaks(R,'Stretch'); lab1=await A.heat_label(R,'Stretch','19 Oct')
    c2=await A.heat_click(R,'Stretch','19 Oct'); s2=await A.streaks(R,'Stretch'); lab2=await A.heat_label(R,'Stretch','19 Oct')
    r['H15']=res(None, f'Stretch before {b}; click Mon 19 Oct -> {c1}, streaks {s1}, label {lab1}; click again -> {c2}, streaks {s2}, label {lab2}; expected 10/10 then 3/6')
    r['H17']=res(None, f'labels: done cell {await A.heat_label(R,"Stretch","20 Oct")}; not-done cell {lab2}; toggled {lab1}')
    # ---------- edit + schedule recompute ----------
    f0=await A.streaks(R,'Floss')
    e19=await A.edit(R,'Floss',schedule=('days',['Tue','Thu'])); f1=await A.streaks(R,'Floss')
    r['H19']=res(None, f'Floss daily (20,22 Oct) {f0}; after edit to Tue+Thu ({e19}) {f1}; expected 1 then 2')
    e18=await A.edit(R,'Read',new_name='Read more',colour_index=3,schedule=('days',['Mon','Tue','Wed','Thu','Fri']))
    names=await A.habit_names(R); col=await A.habit_colour(R,'Read more'); sch=await A.habit_schedule_text(R,'Read more')
    r['H18']=res(None, f'edit -> {e18}; names {names}; colour {col}; schedule text {sch}')
    await R.shot(f'{evdir}/h18_edit.png')
    # ---------- archive / restore ----------
    await A.archive(R,'Walk'); due=await A.due_names(R); arch=await A.archived_names(R)
    await R.shot(f'{evdir}/h20_archived.png')
    await A.restore(R,'Walk'); due2=await A.due_names(R); arch2=await A.archived_names(R)
    r['H20']=res('Walk' not in due and 'Walk' in ' '.join(arch) and 'Walk' in due2, f'archived: due {due}, archived {arch}; restored: due {due2}, archived {arch2}')
    # ---------- undo (5 action types) ----------
    u=[]
    await A.toggle_today(R,'Walk'); a=await A.today_done(R,'Walk'); await A.undo(R); t1=await A.toast(R); b_=await A.today_done(R,'Walk'); u.append(f'check: {a}->undo {b_} toast "{t1}"')
    await A.toggle_today(R,'Walk'); await A.toggle_today(R,'Walk'); a=await A.today_done(R,'Walk'); await A.undo(R); t2=await A.toast(R); b_=await A.today_done(R,'Walk'); u.append(f'uncheck: {a}->undo {b_} toast "{t2}"')
    if b_: await A.toggle_today(R,'Walk')
    await A.edit(R,'Walk',new_name='Walk2'); n1=await A.habit_names(R); await A.undo(R); t3=await A.toast(R); n2=await A.habit_names(R); u.append(f'edit: {"Walk2" in n1}->undo Walk back {"Walk" in n2 and "Walk2" not in n2} toast "{t3}"')
    if 'Walk2' in n2: await A.edit(R,'Walk2',new_name='Walk')
    await A.archive(R,'Walk'); ar=await A.archived_names(R); await A.undo(R); t4=await A.toast(R); ar2=await A.archived_names(R); due=await A.due_names(R); u.append(f'archive: {ar}->undo archived {ar2}, due has Walk {"Walk" in due} toast "{t4}"')
    if 'Walk' not in due: await A.restore(R,'Walk')
    R.confirm_answer=True; await A.delete(R,'Walk'); R.confirm_answer=False; n1=await A.habit_names(R); await A.undo(R); t5=await A.toast(R); n2=await A.habit_names(R); u.append(f'delete: present after delete {"Walk" in n1} -> undo present {"Walk" in n2} toast "{t5}"')
    r['H22']=res(None,'; '.join(u)); r['H25']=res(None,f'toasts: {[t1,t2,t3,t4,t5]}')
    # Ctrl+Z
    await A.toggle_today(R,'Walk'); a=await A.today_done(R,'Walk'); await A.focus_page(R); await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(300); b_=await A.today_done(R,'Walk')
    r['H23']=res(a is True and b_ is False, f'check Walk {a}; Ctrl+Z -> done {b_}')
    # depth 10 via 11 heatmap toggles on Walk (1..11 Oct)
    days=[f'{d} Oct' for d in range(1,12)]
    for dd in days: await A.heat_click(R,'Walk',dd)
    done_before=sum(1 for c in await A.heat_cells(R,'Walk') if c[2])
    for i in range(10): await A.undo(R)
    done_after=sum(1 for c in await A.heat_cells(R,'Walk') if c[2])
    await A.undo(R); done_after11=sum(1 for c in await A.heat_cells(R,'Walk') if c[2])
    r['H24']=res(done_before==11 and done_after==1, f'done cells after 11 toggles {done_before}; after 10 undos {done_after}; after 11th undo {done_after11}')
    # ---------- keyboard ----------
    k=await A.keyboard_rows(R)
    r['H26']=res(None, f'{k}')
    sp=await A.keyboard_space(R)
    r['H27']=res(None, f'{sp}')
    await A.close_dialog(R); await A.focus_page(R)
    await pg.keyboard.press('n'); await pg.wait_for_timeout(300); o1=await A.add_form_open(R); await A.close_dialog(R)
    await A.focus_page(R); await pg.keyboard.press('N'); await pg.wait_for_timeout(300); o2=await A.add_form_open(R)
    inside=None
    if o2:
        await A.fill_add(R,name=''); await pg.keyboard.type('nnn'); inside=await A.name_value(R)
    await A.close_dialog(R)
    r['H28']=res(o1 or o2, f'"n" opens add form {o1}; "N" opens {o2}; typing nnn in name field gives "{inside}"')
    # ---------- delete with confirm ----------
    R.confirm_answer=False; await A.delete(R,'Walk'); n1=await A.habit_names(R)
    R.confirm_answer=True; await A.delete(R,'Walk'); R.confirm_answer=False; n2=await A.habit_names(R)
    cf=[d for d in R.log['dialogs'] if d[0]=='confirm']
    r['H21']=res('Walk' in n1 and 'Walk' not in n2 and len(cf)>=3, f'dismiss -> Walk present {"Walk" in n1}; accept -> present {"Walk" in n2}; confirm dialogs total {len(cf)}')
    # ---------- export / import ----------
    p=await A.export_json(R); data=None
    try: data=json.load(open(p))
    except Exception as e: data=None
    if p: open(f'{evdir}/export.json','w').write(open(p).read())
    r['H29']=res(bool(data) and ('Stretch' in json.dumps(data)) and ('2026-10-13' in json.dumps(data) or '20261013' in json.dumps(data)), f'export file {p and os.path.basename(p)}; parsed {bool(data)}; snippet {json.dumps(data)[:300] if data else None}')
    out['export_path']=p
    # import: add check-in 2026-10-02 to Gym and a new habit "Yoga" by editing the exported structure generically
    imp=None
    if data:
        txt=json.dumps(data)
        mod=A.make_import(data)   # adapter knows the file shape: returns modified dict (Gym +2026-10-02, new habit Yoga daily with 2026-10-21)
        ip=os.path.join(R.dl_dir,'import_mod.json'); json.dump(mod,open(ip,'w'))
        n0=await A.habit_names(R); m=await A.import_json(R,ip); n1=await A.habit_names(R)
        gc=await A.heat_label(R,'Gym','2 Oct'); yc=await A.heat_label(R,'Yoga','21 Oct') if 'Yoga' in n1 else None; gy2=await A.heat_label(R,'Gym','16 Oct')
        imp=f'import msg {m}; habits {n0} -> {n1}; Gym 2 Oct label {gc}; Gym 16 Oct label {gy2}; Yoga 21 Oct {yc}; Gym count {sum(1 for x in n1 if x=="Gym")}'
    r['H30']=res(None, imp or 'no export to modify')
    bad1=os.path.join(R.dl_dir,'bad.json'); open(bad1,'w').write('this is not json')
    bad2=os.path.join(R.dl_dir,'bad2.json'); open(bad2,'w').write('{"foo":1}')
    n0=await A.habit_names(R); m1=await A.import_json(R,bad1); m2=await A.import_json(R,bad2); n1=await A.habit_names(R)
    r['H31']=res(None, f'bad text -> "{m1}"; wrong shape -> "{m2}"; habits unchanged {n0==n1}')
    # ---------- reload persistence ----------
    await pg.reload(); await pg.wait_for_timeout(700); n2=await A.habit_names(R); st2=await A.streaks(R,'Stretch')
    r['G06']=res(None, f'before reload {n1}; after {n2}; Stretch {st2}')
    # ---------- midnight ----------
    await goto_day(R,'2026-10-22','23:59:00')
    if 'Read more' in await A.habit_names(R):
        rd='Read more'
    else: rd=(await A.due_names(R) or ['Stretch'])[0]
    if await A.today_done(R,rd): await A.toggle_today(R,rd)
    await pg.clock.run_for(30000); await A.toggle_today(R,rd); dn=await A.today_done(R,rd)
    hdr0=await A.today_header(R)
    await pg.clock.run_for(100000); await pg.wait_for_timeout(500)
    hdr1=await A.today_header(R); dn1=await A.today_done(R,rd); due_fri=await A.due_names(R)
    await R.shot(f'{evdir}/h33_after_midnight.png')
    r['H33']=res(None, f'at 23:59 header "{hdr0}"; after running clock to 00:01:10 without reload header "{hdr1}", {rd} done={dn1}')
    r['H34']=res(None, f'due list after rollover (Fri): {due_fri}; Gym due {"Gym" in due_fri}')
    await pg.reload(); await pg.wait_for_timeout(700)
    l22=await A.heat_label(R,rd,'22 Oct'); l23=await A.heat_label(R,rd,'23 Oct')
    r['H32']=res(None, f'checked {rd} at 23:59:30 (done={dn}); after midnight+reload: 22 Oct label {l22}; 23 Oct label {l23}')
    out['items']=r
    return r
async def run_import_fresh(R,A,path):
    R.confirm_answer=True  # a 'replace data?' confirm on import is answered yes
    m=await A.import_json(R,path); n=await A.habit_names(R)
    return res(None, f'fresh-profile import of own export: {m}; habits {n}')
async def flow375(R,A,evdir):
    ev=[]
    await A.open_add(R); await R.shot(f'{evdir}/g09_375_form.png'); await A.close_dialog(R)
    ev.append(await A.add_habit(R,'Read',None,'daily')); ev.append(await A.add_habit(R,'Gym',None,('days',['Mon','Wed','Fri'])))
    await A.toggle_today(R,'Read'); ev.append(f'Read done {await A.today_done(R,"Read")}')
    ev.append(f'edit -> {await A.edit(R,"Gym",new_name="Gym 2")}')
    ev.append(f'heat click -> {await A.heat_click(R,"Read","20 Oct")}')
    return ev
