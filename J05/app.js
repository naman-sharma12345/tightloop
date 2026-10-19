(() => {
  'use strict';

  const STORAGE_KEY = 'tend.habit-tracker.v1';
  const UNDO_LIMIT = 10;
  const NAME_MAX = 60;
  const WEEKS = 12;

  const COLORS = [
    { id: 'sage', name: 'Sage' },
    { id: 'ocean', name: 'Ocean' },
    { id: 'amber', name: 'Amber' },
    { id: 'rose', name: 'Rose' },
    { id: 'violet', name: 'Violet' },
    { id: 'slate', name: 'Slate' },
  ];
  const COLOR_IDS = COLORS.map((c) => c.id);
  const DOW_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const DOW_LONG = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const WEEK_ORDER = [1, 2, 3, 4, 5, 6, 0]; // Monday first

  /* ---------- Icons ---------- */
  const ICONS = {
    check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
    plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
    edit: '<path d="M4 20h4L18.5 9.5a2.12 2.12 0 0 0-3-3L5 17v3z"/><path d="m13.5 6.5 3 3"/>',
    archive: '<rect x="3" y="4" width="18" height="4.5" rx="1.2"/><path d="M5 8.5V19a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8.5"/><path d="M10 12.5h4"/>',
    restore: '<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1"/><path d="M3.5 4v5h5"/>',
    trash: '<path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M6 7l1 12.2a1 1 0 0 0 1 .8h8a1 1 0 0 0 1-.8L18 7"/><path d="M9 7V4.5h6V7"/>',
    flame: '<path d="M12 3c.6 3 3.5 4.8 3.5 8.8a3.5 3.5 0 1 1-7 0c0-1.5.6-2.6 1.6-3.5.1 1.4.8 2.3 1.9 2.7-.4-2.8-.6-5.3 0-8z"/><path d="M6.5 14.5A5.5 5.5 0 0 0 12 21a5.5 5.5 0 0 0 5.5-6.5"/>',
    trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5.5a2.5 2.5 0 0 0 2.6 3.6"/><path d="M16 6h2.5a2.5 2.5 0 0 1-2.6 3.6"/><path d="M12 13v4"/><path d="M8.5 20h7"/><path d="M10 17h4v3h-4z"/>',
    calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17"/><path d="M8 3v4"/><path d="M16 3v4"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5"/><path d="M12 16.5h.01"/>',
    close: '<path d="M6 6l12 12"/><path d="M18 6 6 18"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    sprout: '<path d="M12 21v-9"/><path d="M12 12c0-4.4 3-7.5 8-7.5 0 5-3.2 8-8 7.5z"/><path d="M12 15c0-3.3-2.3-5.5-6.5-5.5 0 3.5 2.4 5.7 6.5 5.5z"/>',
    box: '<path d="M3.5 8 12 3.5 20.5 8v8L12 20.5 3.5 16z"/><path d="M3.5 8 12 12.5 20.5 8"/><path d="M12 12.5v8"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/><path d="M12 7.5h.01"/>',
  };
  const icon = (name, cls = 'icon') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[name]}</svg>`;

  /* ---------- Dates (always local time) ---------- */
  const pad = (n) => String(n).padStart(2, '0');
  const keyOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const fromKey = (k) => { const [y, m, d] = k.split('-').map(Number); return new Date(y, m - 1, d); };
  const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
  const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const weekStart = (d) => addDays(startOfDay(d), -((d.getDay() + 6) % 7));
  const shortLabel = (d) => `${DOW_SHORT[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  const isValidKey = (k) => typeof k === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(k) && keyOf(fromKey(k)) === k;

  /* ---------- Helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const uid = () => 'h' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const clone = (o) => JSON.parse(JSON.stringify(o));
  const normName = (s) => s.trim().toLocaleLowerCase();
  const plural = (n, one, many = one + 's') => (n === 1 ? one : many);
  const quoted = (s) => `“${s}”`;

  /* ---------- State ---------- */
  let habits = [];
  let undoStack = [];
  let todayKey = keyOf(new Date());
  let notice = null;
  const heatFocus = {}; // habit id -> date key holding the roving tab stop
  const setCache = new WeakMap();

  const checkSet = (h) => {
    let s = setCache.get(h.checks);
    if (!s) { s = new Set(h.checks); setCache.set(h.checks, s); }
    return s;
  };

  /* ---------- Validation (shared by storage + import) ---------- */
  function validateName(raw, ignoreId) {
    const name = typeof raw === 'string' ? raw.trim() : '';
    if (!name) return { error: 'Give your habit a name.' };
    if (name.length > NAME_MAX) return { error: `Keep the name to ${NAME_MAX} characters or fewer (it’s ${name.length} now).` };
    const clash = habits.find((h) => h.id !== ignoreId && normName(h.name) === normName(name));
    if (clash) return { error: `You already have a habit called ${quoted(clash.name)}${clash.archived ? ' (it’s archived)' : ''}. Pick a different name.` };
    return { name };
  }

  function normSchedule(s) {
    if (!s || typeof s !== 'object') return null;
    if (s.type === 'daily') return { type: 'daily' };
    if (s.type === 'weekdays') {
      if (!Array.isArray(s.days)) return null;
      const days = [...new Set(s.days)];
      if (!days.length || !days.every((d) => Number.isInteger(d) && d >= 0 && d <= 6)) return null;
      return { type: 'weekdays', days: days.sort((a, b) => a - b) };
    }
    if (s.type === 'weekly') {
      if (!Number.isInteger(s.times) || s.times < 1 || s.times > 7) return null;
      return { type: 'weekly', times: s.times };
    }
    return null;
  }

  function parseData(data) {
    const list = Array.isArray(data) ? data : data && typeof data === 'object' ? data.habits : null;
    if (!Array.isArray(list)) return { error: 'It doesn’t contain a list of habits.' };
    const out = [];
    for (let i = 0; i < list.length; i++) {
      const h = list[i];
      const where = `Habit ${i + 1}`;
      if (!h || typeof h !== 'object') return { error: `${where} isn’t a valid habit.` };
      const name = typeof h.name === 'string' ? h.name.trim() : '';
      if (!name || name.length > NAME_MAX) return { error: `${where} needs a name of 1–${NAME_MAX} characters.` };
      const label = `${where} (${quoted(name)})`;
      if (!COLOR_IDS.includes(h.color)) return { error: `${label} has an unknown colour.` };
      const schedule = normSchedule(h.schedule);
      if (!schedule) return { error: `${label} has an invalid schedule.` };
      const checks = h.checks == null ? [] : h.checks;
      if (!Array.isArray(checks) || !checks.every(isValidKey)) return { error: `${label} has check-in dates that aren’t valid.` };
      if (h.archived != null && typeof h.archived !== 'boolean') return { error: `${label} has an invalid archived flag.` };
      out.push({
        id: typeof h.id === 'string' && h.id ? h.id : null,
        name,
        color: h.color,
        schedule,
        checks: [...new Set(checks)].sort(),
        archived: !!h.archived,
        createdAt: typeof h.createdAt === 'string' ? h.createdAt : new Date().toISOString(),
      });
    }
    return { habits: out };
  }

  /* ---------- Persistence ---------- */
  function load() {
    let raw = null;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      notice = { kind: 'warn', text: 'This browser is blocking local storage, so changes will be lost when you close the tab.' };
      return;
    }
    if (raw == null) return;
    try {
      const res = parseData(JSON.parse(raw));
      if (res.error) throw new Error(res.error);
      const seen = new Set();
      habits = res.habits.map((h) => {
        let id = h.id;
        if (!id || seen.has(id)) id = uid();
        seen.add(id);
        return { ...h, id };
      });
    } catch (e) {
      habits = [];
      notice = { kind: 'warn', text: '<strong>We couldn’t read your saved habits</strong>, so Tend started with an empty list. Anything you add now will be saved normally.' };
    }
  }

  function serialise() {
    return habits.map((h) => ({
      id: h.id, name: h.name, color: h.color, schedule: h.schedule,
      checks: [...h.checks].sort(), archived: h.archived, createdAt: h.createdAt,
    }));
  }

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ app: 'tend', version: 1, habits: serialise() }));
    } catch (e) {
      toast('Couldn’t save to this browser. Try exporting your data.');
    }
  }

  /* ---------- Schedule + streak logic ---------- */
  const isScheduled = (h, d) => (h.schedule.type === 'weekdays' ? h.schedule.days.includes(d.getDay()) : true);
  const isWeekly = (h) => h.schedule.type === 'weekly';

  function weekCount(h, d) {
    const set = checkSet(h);
    const start = weekStart(d);
    let n = 0;
    for (let i = 0; i < 7; i++) if (set.has(keyOf(addDays(start, i)))) n++;
    return n;
  }

  function isDueToday(h) {
    const today = fromKey(todayKey);
    if (isWeekly(h)) return checkSet(h).has(todayKey) || weekCount(h, today) < h.schedule.times;
    return isScheduled(h, today);
  }

  function streaks(h) {
    const set = checkSet(h);
    if (!set.size) return { current: 0, best: 0 };
    const today = fromKey(todayKey);
    const earliest = fromKey([...set].sort()[0]);
    let current = 0;
    let best = 0;

    if (isWeekly(h)) {
      const need = h.schedule.times;
      const thisWeek = weekStart(today);
      const firstWeek = weekStart(earliest);
      // Current: walk back week by week; an unmet current week is still in progress.
      for (let w = thisWeek; w >= firstWeek; w = addDays(w, -7)) {
        const met = weekCount(h, w) >= need;
        if (met) current++;
        else if (w.getTime() !== thisWeek.getTime()) break;
      }
      let run = 0;
      for (let w = firstWeek; w <= thisWeek; w = addDays(w, 7)) {
        if (weekCount(h, w) >= need) { run++; best = Math.max(best, run); }
        else if (w.getTime() !== thisWeek.getTime()) run = 0;
      }
    } else {
      // Day-based: only scheduled days count; an unchecked today is still in progress.
      for (let d = today; d >= earliest; d = addDays(d, -1)) {
        if (!isScheduled(h, d)) continue;
        if (set.has(keyOf(d))) current++;
        else if (keyOf(d) !== todayKey) break;
      }
      let run = 0;
      for (let d = earliest; d <= today; d = addDays(d, 1)) {
        if (!isScheduled(h, d)) continue;
        if (set.has(keyOf(d))) { run++; best = Math.max(best, run); }
        else if (keyOf(d) !== todayKey) run = 0;
      }
    }
    return { current, best: Math.max(best, current) };
  }

  function scheduleText(s) {
    if (s.type === 'daily') return 'Every day';
    if (s.type === 'weekly') return s.times === 1 ? 'Once a week' : s.times === 2 ? 'Twice a week' : `${s.times} times a week`;
    const days = [...s.days].sort((a, b) => a - b).join(',');
    if (days === '0,1,2,3,4,5,6') return 'Every day';
    if (days === '1,2,3,4,5') return 'Weekdays';
    if (days === '0,6') return 'Weekends';
    return WEEK_ORDER.filter((d) => s.days.includes(d)).map((d) => DOW_SHORT[d]).join(', ');
  }
  const unit = (h, n) => (isWeekly(h) ? plural(n, 'week') : plural(n, 'day'));

  /* ---------- Undo ---------- */
  function record(label, id) {
    const index = habits.findIndex((h) => h.id === id);
    undoStack.push({ label, id, index, before: index >= 0 ? clone(habits[index]) : null });
    if (undoStack.length > UNDO_LIMIT) undoStack.shift();
  }

  function undo() {
    const entry = undoStack.pop();
    if (!entry) { toast('Nothing to undo.'); return; }
    const idx = habits.findIndex((h) => h.id === entry.id);
    if (!entry.before) {
      if (idx >= 0) habits.splice(idx, 1);
    } else if (idx >= 0) {
      habits[idx] = entry.before;
    } else {
      habits.splice(Math.min(Math.max(entry.index, 0), habits.length), 0, entry.before);
    }
    save();
    render();
    toast(`Undid: ${entry.label}`, { icon: 'undo' });
  }

  /* ---------- Actions ---------- */
  const findHabit = (id) => habits.find((h) => h.id === id);

  function toggleCheck(id, key) {
    rollover();
    if (key == null) key = todayKey;
    const h = findHabit(id);
    if (!h || !isValidKey(key) || key > todayKey) return;
    const done = checkSet(h).has(key);
    const when = key === todayKey ? 'today' : shortLabel(fromKey(key));
    record(`${done ? 'unchecked' : 'checked'} ${quoted(h.name)} for ${when}`, id);
    h.checks = done ? h.checks.filter((k) => k !== key) : [...h.checks, key].sort();
    save();
    render();
    return !done;
  }

  function addHabit(data) {
    const h = { id: uid(), name: data.name, color: data.color, schedule: data.schedule, checks: [], archived: false, createdAt: new Date().toISOString() };
    record(`added ${quoted(h.name)}`, h.id);
    habits.push(h);
    save();
    render();
    toast(`Added ${quoted(h.name)}.`, { icon: 'check' });
  }

  function editHabit(id, data) {
    const h = findHabit(id);
    if (!h) return;
    const changed = h.name !== data.name || h.color !== data.color || JSON.stringify(h.schedule) !== JSON.stringify(data.schedule);
    if (!changed) return;
    record(`edited ${quoted(h.name)}`, id);
    Object.assign(h, { name: data.name, color: data.color, schedule: data.schedule });
    save();
    render();
    toast(`Saved changes to ${quoted(h.name)}.`, { icon: 'check' });
  }

  function setArchived(id, archived) {
    const h = findHabit(id);
    if (!h) return;
    record(`${archived ? 'archived' : 'restored'} ${quoted(h.name)}`, id);
    h.archived = archived;
    save();
    render(archived ? `restore-${id}` : `archive-${id}`);
    toast(`${archived ? 'Archived' : 'Restored'} ${quoted(h.name)}.`, { icon: archived ? 'archive' : 'restore', undo: true });
  }

  function deleteHabit(id) {
    const h = findHabit(id);
    if (!h) return;
    const n = h.checks.length;
    const ok = window.confirm(`Delete ${quoted(h.name)}? This removes it and its ${n} ${plural(n, 'check-in')}.`);
    if (!ok) return;
    record(`deleted ${quoted(h.name)}`, id);
    habits = habits.filter((x) => x.id !== id);
    save();
    render();
    if (!document.activeElement || document.activeElement === document.body) $('#habits-title').focus();
    toast(`Deleted ${quoted(h.name)}.`, { icon: 'trash', undo: true });
  }

  /* ---------- Import / export ---------- */
  function exportData() {
    const payload = { app: 'tend', version: 1, exportedAt: new Date().toISOString(), habits: serialise() };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tend-habits-${todayKey}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Exported ${habits.length} ${plural(habits.length, 'habit')}.`, { icon: 'check' });
  }

  function showDataError(text) {
    const box = $('#data-msg');
    box.innerHTML = text ? `<div class="banner banner-error">${icon('alert')}<p>${text}</p>
      <button type="button" class="icon-btn" data-action="dismiss-data" aria-label="Dismiss error">${icon('close')}</button></div>` : '';
  }

  async function importFile(file) {
    let text;
    try { text = await file.text(); } catch (e) { showDataError('<strong>Import failed.</strong> That file couldn’t be read.'); return; }
    let data;
    try { data = JSON.parse(text); } catch (e) {
      showDataError(`<strong>Import failed: nothing was changed.</strong> ${esc(file.name)} isn’t valid JSON. Choose a file exported from Tend.`);
      return;
    }
    const res = parseData(data);
    if (res.error) {
      showDataError(`<strong>Import failed: nothing was changed.</strong> ${esc(res.error)}`);
      return;
    }
    let added = 0;
    let merged = 0;
    for (const inc of res.habits) {
      const existing = habits.find((h) => normName(h.name) === normName(inc.name));
      if (existing) {
        existing.checks = [...new Set([...existing.checks, ...inc.checks])].sort();
        merged++;
      } else {
        const id = inc.id && !findHabit(inc.id) ? inc.id : uid();
        habits.push({ ...inc, id });
        added++;
      }
    }
    undoStack = []; // earlier per-habit snapshots would discard imported check-ins
    showDataError('');
    save();
    render();
    const parts = [];
    if (added) parts.push(`${added} new`);
    if (merged) parts.push(`${merged} merged`);
    toast(res.habits.length ? `Imported ${res.habits.length} ${plural(res.habits.length, 'habit')} (${parts.join(', ')}).` : 'That file had no habits in it.', { icon: 'check' });
  }

  /* ---------- Toasts ---------- */
  function toast(msg, opts = {}) {
    const wrap = $('#toasts');
    while (wrap.children.length >= 3) wrap.firstElementChild.remove();
    const el = document.createElement('div');
    el.className = 'toast';
    el.innerHTML = `${icon(opts.icon || 'info')}<span class="toast-msg"></span>${opts.undo ? '<button type="button" class="toast-btn">Undo</button>' : ''}`;
    el.querySelector('.toast-msg').textContent = msg;
    let timer;
    const dismiss = () => {
      clearTimeout(timer);
      el.classList.add('leaving');
      setTimeout(() => el.remove(), 200);
    };
    if (opts.undo) el.querySelector('.toast-btn').addEventListener('click', () => { dismiss(); undo(); });
    el.addEventListener('mouseenter', () => clearTimeout(timer));
    el.addEventListener('mouseleave', () => { timer = setTimeout(dismiss, 2500); });
    wrap.appendChild(el);
    timer = setTimeout(dismiss, opts.undo ? 6000 : 3500);
  }

  /* ---------- Rendering ---------- */
  function render(fallbackFocus) {
    const active = document.activeElement;
    const focusKey = active && active.dataset ? active.dataset.focus : null;

    const now = new Date();
    $('#today-date').textContent = `${DOW_LONG[now.getDay()]}, ${now.getDate()} ${MONTHS_LONG[now.getMonth()]}`;
    const undoBtn = $('#undo-btn');
    undoBtn.disabled = undoStack.length === 0;
    const last = undoStack[undoStack.length - 1];
    undoBtn.title = last ? `Undo: ${last.label} (Ctrl+Z)` : 'Nothing to undo';
    undoBtn.setAttribute('aria-label', last ? `Undo: ${last.label}` : 'Undo');
    $('#export-btn').disabled = habits.length === 0;
    $('#export-btn').title = habits.length ? 'Download all habits as JSON' : 'Add a habit first to export';

    renderNotice();
    renderToday();
    renderHabits();
    renderArchived();

    const target = (focusKey && document.querySelector(`[data-focus="${CSS.escape(focusKey)}"]`)) ||
      (fallbackFocus && document.querySelector(`[data-focus="${CSS.escape(fallbackFocus)}"]`));
    if (target && !target.disabled) target.focus({ preventScroll: true });
  }

  function renderNotice() {
    $('#notice').innerHTML = notice ? `<div class="banner banner-warn">${icon('alert')}<p>${notice.text}</p>
      <button type="button" class="icon-btn" data-action="dismiss-notice" aria-label="Dismiss message">${icon('close')}</button></div>` : '';
  }

  function streakChip(h, st) {
    const n = st.current;
    return `<span class="streak-chip${n ? '' : ' zero'}">${icon('flame')}${n}<span class="sr-only"> ${unit(h, n)} streak</span></span>`;
  }

  function todayRow(h) {
    const done = checkSet(h).has(todayKey);
    const st = streaks(h);
    let meta = esc(scheduleText(h.schedule));
    if (isWeekly(h)) meta = `${weekCount(h, fromKey(todayKey))} of ${h.schedule.times} this week`;
    return `<li><button type="button" class="today-row${done ? ' is-done' : ''}" style="--hc: var(--h-${h.color})"
        data-action="toggle-today" data-id="${h.id}" data-focus="today-${h.id}" aria-pressed="${done}">
        <span class="tick">${icon('check')}</span>
        <span class="row-text"><span class="row-name">${esc(h.name)}</span>
          <span class="row-meta"><span class="row-state">${done ? 'Done' : 'To do'}</span> · ${meta}</span></span>
        ${streakChip(h, st)}
      </button></li>`;
  }

  function renderToday() {
    const el = $('#today');
    const active = habits.filter((h) => !h.archived);
    const due = active.filter(isDueToday);
    const rest = active.filter((h) => !isDueToday(h));
    const doneCount = due.filter((h) => checkSet(h).has(todayKey)).length;
    const pct = due.length ? doneCount / due.length : 0;
    const C = 2 * Math.PI * 24;

    const head = `<div class="today-head">
        <div class="ring" aria-hidden="true"><svg viewBox="0 0 56 56"><circle class="ring-track" cx="28" cy="28" r="24" fill="none" stroke-width="5"/>
          <circle class="ring-fill" cx="28" cy="28" r="24" fill="none" stroke-width="5" stroke-linecap="round"
            stroke-dasharray="${C.toFixed(2)}" stroke-dashoffset="${(C * (1 - pct)).toFixed(2)}"${pct === 0 ? ' opacity="0"' : ''}/></svg>
          <span class="ring-label">${due.length ? Math.round(pct * 100) + '%' : '–'}</span></div>
        <div><h2 id="today-title">Today</h2>
          <p>${due.length ? `${doneCount} of ${due.length} done` : active.length ? 'Nothing scheduled' : 'No habits yet'}</p></div>
      </div>`;

    if (!habits.length) {
      el.innerHTML = head + `<div class="empty">
          <span class="empty-art">${icon('sprout')}</span>
          <h3>Start with one small habit</h3>
          <p>Add something you’d like to do regularly. It’ll show up here each day it’s due.</p>
          <button type="button" class="btn btn-primary" data-action="new">${icon('plus')}<span>Add your first habit</span></button>
        </div>`;
      return;
    }
    if (!active.length) {
      el.innerHTML = head + `<div class="empty">
          <span class="empty-art">${icon('archive')}</span>
          <h3>All habits are archived</h3>
          <p>Restore one from the Archived section, or add a new habit to track.</p>
          <button type="button" class="btn btn-primary" data-action="new">${icon('plus')}<span>New habit</span></button>
        </div>`;
      return;
    }

    const dueHtml = due.length
      ? `<ul class="today-list">${due.map(todayRow).join('')}</ul>`
      : `<div class="empty empty-sm"><h3>Nothing due today</h3><p>Enjoy the breather, or tick off something extra below.</p></div>`;
    const restHtml = rest.length
      ? `<ul class="today-list">${rest.map(todayRow).join('')}</ul>`
      : `<div class="empty empty-sm"><p>Every active habit is due today, so they’re all listed above.</p></div>`;
    const allDone = due.length && doneCount === due.length;

    el.innerHTML = head + `
      <div class="group" role="group" aria-labelledby="due-label">
        <h3 class="group-label" id="due-label">Due today</h3>${dueHtml}
        ${allDone ? `<p class="done-note">${icon('check')}All done for today. Nicely kept.</p>` : ''}
      </div>
      <div class="group" role="group" aria-labelledby="rest-label">
        <h3 class="group-label" id="rest-label">Not due today</h3>${restHtml}
      </div>`;
  }

  function heatmap(h) {
    const set = checkSet(h);
    const today = fromKey(todayKey);
    const start = addDays(weekStart(today), -(WEEKS - 1) * 7);
    const end = addDays(weekStart(today), 6);
    const firstVisible = keyOf(start);
    let focusKey = heatFocus[h.id];
    if (!focusKey || focusKey > todayKey || focusKey < firstVisible) focusKey = todayKey;

    const months = [];
    for (let w = 0; w < WEEKS; w++) {
      let label = '';
      for (let i = 0; i < 7; i++) {
        const d = addDays(start, w * 7 + i);
        if (d.getDate() === 1 || (w === 0 && i === 0)) { label = MONTHS[d.getMonth()]; break; }
      }
      months.push(`<span>${label}</span>`);
    }

    const cells = [];
    let total = 0;
    for (let d = start; d <= end; d = addDays(d, 1)) {
      const k = keyOf(d);
      const future = k > todayKey;
      const done = set.has(k);
      if (done && !future) total++;
      const sched = isScheduled(h, d);
      const state = future ? 'upcoming' : done ? 'done' : sched ? 'not done' : 'not done (rest day)';
      const label = `${shortLabel(d)}${k === todayKey ? ' (today)' : ''}: ${state}`;
      const cls = ['cell', done && !future ? 'done' : '', !sched && !done ? 'rest' : '', k === todayKey ? 'today' : ''].filter(Boolean).join(' ');
      cells.push(`<button type="button" class="${cls}" data-action="toggle-cell" data-id="${h.id}" data-date="${k}"
        data-focus="cell-${h.id}-${k}" tabindex="${k === focusKey ? 0 : -1}" aria-label="${label}" title="${label}"${future ? ' disabled' : ''}>${done && !future ? icon('check') : ''}</button>`);
    }

    const dayLabels = WEEK_ORDER.map((d) => `<span><span class="wk-full">${DOW_SHORT[d]}</span><span class="wk-mini">${DOW_SHORT[d][0]}</span></span>`).join('');
    return {
      total,
      html: `<div class="heat">
        <div class="heat-months" aria-hidden="true">${months.join('')}</div>
        <div class="heat-body">
          <div class="heat-days" aria-hidden="true">${dayLabels}</div>
          <div class="heat-grid" role="group" aria-label="${esc(h.name)}: last ${WEEKS} weeks. Use arrow keys to move between days.">${cells.join('')}</div>
        </div>
        <div class="legend" aria-hidden="true"><span><i class="l-done">${icon('check')}</i>Done</span><span><i></i>Missed or open</span>${h.schedule.type === 'weekdays' ? '<span><i class="l-rest"></i>Rest day</span>' : ''}</div>
      </div>`,
    };
  }

  function renderHabits() {
    const el = $('#habits');
    const active = habits.filter((h) => !h.archived);
    if (!active.length) {
      el.innerHTML = `<div class="empty">
          <span class="empty-art">${icon('calendar')}</span>
          <h3>${habits.length ? 'No active habits' : 'Your history will live here'}</h3>
          <p>${habits.length ? 'Restore an archived habit or add a new one to see its 12-week calendar.' : 'Each habit gets a 12-week calendar with its current and best streak. Press N to add one.'}</p>
        </div>`;
      return;
    }
    el.innerHTML = `<div class="habit-list">${active.map((h) => {
      const st = streaks(h);
      const hm = heatmap(h);
      return `<article class="habit-card" style="--hc: var(--h-${h.color})" aria-labelledby="name-${h.id}">
        <header class="card-head">
          <span class="dot" aria-hidden="true"></span>
          <div class="card-title"><h3 id="name-${h.id}">${esc(h.name)}</h3><p>${esc(scheduleText(h.schedule))} · ${COLORS.find((c) => c.id === h.color).name}</p></div>
          <div class="card-actions">
            <button type="button" class="icon-btn" data-action="edit" data-id="${h.id}" data-focus="edit-${h.id}" aria-label="Edit ${esc(h.name)}" title="Edit">${icon('edit')}</button>
            <button type="button" class="icon-btn" data-action="archive" data-id="${h.id}" data-focus="archive-${h.id}" aria-label="Archive ${esc(h.name)}" title="Archive">${icon('archive')}</button>
            <button type="button" class="icon-btn danger" data-action="delete" data-id="${h.id}" data-focus="delete-${h.id}" aria-label="Delete ${esc(h.name)}" title="Delete">${icon('trash')}</button>
          </div>
        </header>
        <div class="card-body">
          ${hm.html}
          <dl class="stats">
            <div><dt>${icon('flame')}Current streak</dt><dd>${st.current}<span>${unit(h, st.current)}</span></dd></div>
            <div><dt>${icon('trophy')}Best streak</dt><dd>${st.best}<span>${unit(h, st.best)}</span></dd></div>
            <div><dt>${icon('calendar')}12 weeks</dt><dd>${hm.total}<span>${plural(hm.total, 'check-in')}</span></dd></div>
          </dl>
        </div>
      </article>`;
    }).join('')}</div>`;
  }

  function renderArchived() {
    const el = $('#archived');
    const list = habits.filter((h) => h.archived);
    if (!list.length) {
      el.innerHTML = `<div class="empty empty-sm"><h3>Nothing archived</h3><p>Archive a habit to pause it. It leaves Today but keeps its full history, ready to restore.</p></div>`;
      return;
    }
    el.innerHTML = `<ul class="arch-list">${list.map((h) => {
      const st = streaks(h);
      return `<li class="arch-row" style="--hc: var(--h-${h.color})">
        <span class="dot" aria-hidden="true"></span>
        <span class="arch-name"><strong>${esc(h.name)}</strong><span>${esc(scheduleText(h.schedule))} · best streak ${st.best} ${unit(h, st.best)}</span></span>
        <span class="arch-actions">
          <button type="button" class="btn btn-ghost" data-action="restore" data-id="${h.id}" data-focus="restore-${h.id}" aria-label="Restore ${esc(h.name)}">${icon('restore')}<span>Restore</span></button>
          <button type="button" class="icon-btn danger" data-action="delete" data-id="${h.id}" data-focus="delete-${h.id}" aria-label="Delete ${esc(h.name)}" title="Delete">${icon('trash')}</button>
        </span>
      </li>`;
    }).join('')}</ul>`;
  }

  function pulse(selector) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.classList.remove('pulse');
    void el.offsetWidth;
    el.classList.add('pulse');
  }

  /* ---------- Dialog ---------- */
  const dialog = $('#habit-dialog');
  const form = $('#habit-form');
  const nameInput = $('#f-name');
  let editingId = null;
  let returnFocus = null;
  let returnFocusKey = null;

  $('#swatches').innerHTML = COLORS.map((c, i) => `<label class="swatch" style="--hc: var(--h-${c.id})">
      <input type="radio" name="color" value="${c.id}"${i === 0 ? ' checked' : ''}>
      <span class="swatch-dot">${icon('check')}</span><span class="swatch-name">${c.name}</span></label>`).join('');
  $('#days').innerHTML = WEEK_ORDER.map((d) => `<label class="day"><input type="checkbox" name="days" value="${d}">
      <span aria-hidden="true">${DOW_SHORT[d].slice(0, 2)}</span><span class="sr-only">${DOW_LONG[d]}</span></label>`).join('');

  function setFieldError(input, errEl, msg) {
    if (msg) {
      errEl.innerHTML = `${icon('alert')}<span>${esc(msg)}</span>`;
      errEl.hidden = false;
      if (input) input.setAttribute('aria-invalid', 'true');
    } else {
      errEl.hidden = true;
      errEl.textContent = '';
      if (input) input.removeAttribute('aria-invalid');
    }
  }

  function updateCount() {
    const n = nameInput.value.trim().length;
    const c = $('#name-count');
    c.textContent = `${n}/${NAME_MAX}`;
    c.classList.toggle('over', n > NAME_MAX);
  }

  function syncSchedulePanels() {
    const type = form.querySelector('input[name="stype"]:checked').value;
    $('#days-panel').hidden = type !== 'weekdays';
    $('#times-panel').hidden = type !== 'weekly';
  }

  function openDialog(id = null) {
    if (dialog.open) return;
    editingId = id;
    returnFocus = document.activeElement;
    returnFocusKey = returnFocus && returnFocus.dataset ? returnFocus.dataset.focus : null;
    const h = id ? findHabit(id) : null;
    form.reset();
    $('#dialog-title').textContent = h ? 'Edit habit' : 'New habit';
    $('#dialog-submit').textContent = h ? 'Save changes' : 'Add habit';
    nameInput.value = h ? h.name : '';
    const used = new Set(habits.map((x) => x.color));
    const color = h ? h.color : COLOR_IDS.find((c) => !used.has(c)) || COLOR_IDS[habits.length % COLOR_IDS.length];
    form.querySelector(`input[name="color"][value="${color}"]`).checked = true;
    const s = h ? h.schedule : { type: 'daily' };
    form.querySelector(`input[name="stype"][value="${s.type}"]`).checked = true;
    const days = s.type === 'weekdays' ? s.days : [1, 2, 3, 4, 5];
    form.querySelectorAll('input[name="days"]').forEach((cb) => { cb.checked = days.includes(Number(cb.value)); });
    $('#f-times').value = String(s.type === 'weekly' ? s.times : 3);
    setFieldError(nameInput, $('#name-err'), '');
    setFieldError(null, $('#days-err'), '');
    updateCount();
    syncSchedulePanels();
    dialog.showModal();
    nameInput.focus();
    if (h) nameInput.select();
  }

  function closeDialog() {
    if (dialog.open) dialog.close();
  }

  dialog.addEventListener('close', () => {
    const byKey = returnFocusKey && document.querySelector(`[data-focus="${CSS.escape(returnFocusKey)}"]`);
    const target = byKey || (returnFocus && document.contains(returnFocus) && returnFocus !== document.body ? returnFocus : $('#new-btn'));
    editingId = null;
    returnFocus = null;
    // Focus after the dialog has fully closed so the browser doesn't override it.
    setTimeout(() => target.focus(), 0);
  });

  dialog.addEventListener('click', (e) => {
    if (e.target.closest('[data-close]')) { closeDialog(); return; }
    if (e.target === dialog) {
      const r = dialog.getBoundingClientRect();
      const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
      if (!inside) closeDialog();
    }
  });

  dialog.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const items = [...dialog.querySelectorAll('button, input, select, [tabindex]:not([tabindex="-1"])')]
      .filter((el) => !el.disabled && el.offsetParent !== null && !(el.type === 'radio' && !el.checked));
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  nameInput.addEventListener('input', () => {
    updateCount();
    if (nameInput.getAttribute('aria-invalid')) setFieldError(nameInput, $('#name-err'), '');
  });
  form.addEventListener('change', (e) => {
    if (e.target.name === 'stype') syncSchedulePanels();
    if (e.target.name === 'days' || e.target.name === 'stype') setFieldError(null, $('#days-err'), '');
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const nameRes = validateName(nameInput.value, editingId);
    setFieldError(nameInput, $('#name-err'), nameRes.error);
    const type = form.querySelector('input[name="stype"]:checked').value;
    let schedule;
    let daysError = '';
    if (type === 'daily') schedule = { type: 'daily' };
    else if (type === 'weekly') schedule = { type: 'weekly', times: Number($('#f-times').value) };
    else {
      const days = [...form.querySelectorAll('input[name="days"]:checked')].map((cb) => Number(cb.value)).sort((a, b) => a - b);
      if (!days.length) daysError = 'Pick at least one day.';
      schedule = { type: 'weekdays', days };
    }
    setFieldError(null, $('#days-err'), daysError);
    if (nameRes.error) { nameInput.focus(); return; }
    if (daysError) { form.querySelector('input[name="days"]').focus(); return; }
    const data = { name: nameRes.name, color: form.querySelector('input[name="color"]:checked').value, schedule };
    const id = editingId;
    closeDialog();
    if (id) editHabit(id, data);
    else addHabit(data);
  });

  /* ---------- Events ---------- */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn || btn.disabled || dialog.contains(btn)) return;
    const id = btn.dataset.id;
    switch (btn.dataset.action) {
      case 'new': openDialog(); break;
      case 'undo': undo(); break;
      case 'export': exportData(); break;
      case 'import': $('#import-file').click(); break;
      case 'edit': openDialog(id); break;
      case 'archive': setArchived(id, true); break;
      case 'restore': setArchived(id, false); break;
      case 'delete': deleteHabit(id); break;
      case 'dismiss-notice': notice = null; renderNotice(); $('#main').focus(); break;
      case 'dismiss-data': showDataError(''); $('#import-btn').focus(); break;
      case 'toggle-today':
        if (toggleCheck(id, null)) pulse(`[data-focus="today-${CSS.escape(id)}"]`);
        break;
      case 'toggle-cell': {
        heatFocus[id] = btn.dataset.date;
        const key = btn.dataset.date;
        if (toggleCheck(id, key)) pulse(`[data-focus="cell-${CSS.escape(id)}-${key}"]`);
        break;
      }
      default: break;
    }
  });

  $('#import-file').addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (file) importFile(file);
  });

  const isTyping = (el) => el && (el.matches('input, textarea, select') || el.isContentEditable);

  function moveToday(current, key) {
    const rows = [...document.querySelectorAll('.today-row')];
    const i = rows.indexOf(current);
    let next = i;
    if (key === 'ArrowDown' || key === 'ArrowRight') next = Math.min(rows.length - 1, i + 1);
    else if (key === 'ArrowUp' || key === 'ArrowLeft') next = Math.max(0, i - 1);
    else if (key === 'Home') next = 0;
    else if (key === 'End') next = rows.length - 1;
    else return false;
    rows[next].focus();
    return true;
  }

  function moveCell(cell, key) {
    const calendarLayout = window.matchMedia('(max-width: 640px)').matches;
    const steps = calendarLayout
      ? { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }
      : { ArrowUp: -1, ArrowDown: 1, ArrowLeft: -7, ArrowRight: 7 };
    const grid = cell.parentElement;
    let targetKey;
    if (key in steps) targetKey = keyOf(addDays(fromKey(cell.dataset.date), steps[key]));
    else if (key === 'Home') targetKey = grid.firstElementChild.dataset.date;
    else if (key === 'End') targetKey = todayKey;
    else return false;
    const target = grid.querySelector(`[data-date="${targetKey}"]`);
    if (target && !target.disabled) {
      grid.querySelectorAll('.cell[tabindex="0"]').forEach((c) => { c.tabIndex = -1; });
      target.tabIndex = 0;
      target.focus();
      heatFocus[cell.dataset.id] = targetKey;
    }
    return true;
  }

  document.addEventListener('keydown', (e) => {
    if (dialog.open) return;
    const t = e.target;
    const mod = e.ctrlKey || e.metaKey;
    if (mod && !e.altKey && !e.shiftKey && e.key.toLowerCase() === 'z') {
      if (isTyping(t)) return;
      e.preventDefault();
      undo();
      return;
    }
    if (mod || e.altKey || isTyping(t)) return;
    if (e.key === 'n' || e.key === 'N') {
      e.preventDefault();
      openDialog();
      return;
    }
    if (t.classList && t.classList.contains('today-row')) {
      if (moveToday(t, e.key)) e.preventDefault();
    } else if (t.classList && t.classList.contains('cell')) {
      if (moveCell(t, e.key)) e.preventDefault();
    }
  });

  /* ---------- Midnight rollover ---------- */
  function rollover() {
    const k = keyOf(new Date());
    if (k === todayKey) return false;
    todayKey = k;
    Object.keys(heatFocus).forEach((id) => delete heatFocus[id]);
    render();
    return true;
  }
  setInterval(rollover, 20000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) rollover(); });
  window.addEventListener('focus', rollover);

  /* ---------- Boot ---------- */
  load();
  render();
})();
