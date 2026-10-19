(() => {
  'use strict';

  const STORAGE_KEY = 'kept-habit-tracker';
  const UNDO_LIMIT = 10;
  const NAME_MAX = 60;

  const COLORS = [
    { id: 'evergreen', name: 'Evergreen', value: '#2f6b55' },
    { id: 'ocean', name: 'Ocean', value: '#24648a' },
    { id: 'iris', name: 'Iris', value: '#5450c4' },
    { id: 'plum', name: 'Plum', value: '#8a4479' },
    { id: 'clay', name: 'Clay', value: '#ad4a2f' },
    { id: 'ochre', name: 'Ochre', value: '#8a5f0c' },
  ];
  const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const DOW_LONG = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const WEEK_ORDER = [1, 2, 3, 4, 5, 6, 0]; // Monday first

  /* ---------- Icons ---------- */
  const ICONS = {
    check: '<path d="M5 12.5l4.2 4.2L19 7"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    undo: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 010 11H11"/>',
    pencil: '<path d="M4 20h4L18.5 9.5a2.1 2.1 0 00-3-3L5 17v3z"/><path d="M13.5 7.5l3 3"/>',
    archive: '<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8"/><path d="M10 12h4"/>',
    restore: '<path d="M3 12a9 9 0 109-9 9.7 9.7 0 00-6.7 2.7L3 8"/><path d="M3 3v5h5"/>',
    trash: '<path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12"/><path d="M9 7V4h6v3"/>',
    download: '<path d="M12 4v12"/><path d="M7 11l5 5 5-5"/><path d="M5 20h14"/>',
    upload: '<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M5 20h14"/>',
    flame: '<path d="M12 3c.8 3.2 5 5.4 5 10.2A5 5 0 017 13.4c0-2.3 1.1-3.8 2.4-4.9.2 1.7 1 2.8 2.1 2.8C11.4 8.6 11 6 12 3z"/>',
    trophy: '<path d="M8 4h8v5a4 4 0 01-8 0V4z"/><path d="M8 6H5.5a2.5 2.5 0 002.8 3.9M16 6h2.5a2.5 2.5 0 01-2.8 3.9"/><path d="M12 13v4M8.5 20.5h7M10 17h4"/>',
    calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5V13M12 16.5h.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/>',
  };
  const icon = (name, cls = '') =>
    `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`;

  const EMPTY_ART = `<svg class="empty__art" viewBox="0 0 88 64" aria-hidden="true" focusable="false">
    <g fill="#e2ece7">${[0, 1, 2, 3, 4].map(c => [0, 1, 2].map(r => `<rect x="${4 + c * 17}" y="${6 + r * 18}" width="13" height="13" rx="4"/>`).join('')).join('')}</g>
    <rect x="55" y="24" width="13" height="13" rx="4" fill="#2d5b4e"/>
    <path d="M58.5 30.7l2.2 2.2 4.2-4.6" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`;

  /* ---------- Helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pad = n => String(n).padStart(2, '0');
  const keyOf = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const parseKey = k => { const [y, m, d] = k.split('-').map(Number); return new Date(y, m - 1, d); };
  const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
  const startOfToday = () => { const n = new Date(); return new Date(n.getFullYear(), n.getMonth(), n.getDate()); };
  const mondayOf = d => addDays(d, -((d.getDay() + 6) % 7));
  const isValidKey = k => typeof k === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(k) && keyOf(parseKey(k)) === k;
  const fmtShort = d => `${DOW[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  const fmtLong = d => `${DOW_LONG[d.getDay()]}, ${d.getDate()} ${MONTHS_LONG[d.getMonth()]}`;
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
  const colorOf = id => (COLORS.find(c => c.id === id) || COLORS[0]).value;
  const uid = () => 'h' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const sameName = (a, b) => a.trim().toLowerCase() === b.trim().toLowerCase();
  const clone = o => JSON.parse(JSON.stringify(o));

  /* ---------- Validation (shared by storage + import) ---------- */
  function validateSchedule(s) {
    if (!s || typeof s !== 'object') return null;
    if (s.type === 'daily') return { type: 'daily' };
    if (s.type === 'weekdays') {
      if (!Array.isArray(s.days)) return null;
      const days = [...new Set(s.days)].filter(d => Number.isInteger(d) && d >= 0 && d <= 6);
      if (!days.length || days.length !== s.days.length) return null;
      return { type: 'weekdays', days: days.sort((a, b) => a - b) };
    }
    if (s.type === 'weekly') {
      if (!Number.isInteger(s.times) || s.times < 1 || s.times > 7) return null;
      return { type: 'weekly', times: s.times };
    }
    return null;
  }

  function validateHabits(raw) {
    const list = Array.isArray(raw) ? raw : (raw && typeof raw === 'object' && Array.isArray(raw.habits) ? raw.habits : null);
    if (!list) return { error: 'The file doesn’t contain a list of habits.' };
    const out = [];
    const ids = new Set();
    for (let i = 0; i < list.length; i++) {
      const h = list[i];
      const n = i + 1;
      if (!h || typeof h !== 'object' || Array.isArray(h)) return { error: `Habit ${n} isn’t in the expected format.` };
      const name = typeof h.name === 'string' ? h.name.trim() : '';
      if (!name) return { error: `Habit ${n} has no name.` };
      if (name.length > NAME_MAX) return { error: `Habit ${n} has a name longer than ${NAME_MAX} characters.` };
      if (!COLORS.some(c => c.id === h.color)) return { error: `“${name}” has a colour this app doesn’t know.` };
      const schedule = validateSchedule(h.schedule);
      if (!schedule) return { error: `“${name}” has a schedule this app can’t read.` };
      const checks = h.checks === undefined ? [] : h.checks;
      if (!Array.isArray(checks)) return { error: `“${name}” has check-ins in the wrong format.` };
      const bad = checks.find(k => !isValidKey(k));
      if (bad !== undefined) return { error: `“${name}” has a check-in that isn’t a valid date (${String(bad).slice(0, 20)}).` };
      let id = typeof h.id === 'string' && h.id ? h.id : uid();
      if (ids.has(id)) id = uid();
      ids.add(id);
      out.push({
        id, name, color: h.color, schedule,
        archived: h.archived === true,
        createdAt: isValidKey(h.createdAt) ? h.createdAt : keyOf(startOfToday()),
        checks: [...new Set(checks)].sort(),
      });
    }
    return { habits: out };
  }

  /* ---------- State & storage ---------- */
  let habits = [];
  let undoStack = [];
  let today = startOfToday();
  let todayKey = keyOf(today);
  let justToggled = null;
  let newHabitId = null;
  const roving = new Map(); // habit id -> focused heatmap date
  let storageOk = true;

  function load() {
    let raw;
    try { raw = localStorage.getItem(STORAGE_KEY); }
    catch { storageOk = false; showNotice('Your browser is blocking storage, so changes won’t be saved after you close this page.'); return; }
    if (raw === null) return;
    try {
      const res = validateHabits(JSON.parse(raw));
      if (res.error) throw new Error(res.error);
      habits = res.habits;
    } catch {
      habits = [];
      showNotice('Your saved habits couldn’t be read, so Kept started with an empty list. If you have a backup, import it below.');
    }
  }

  function save() {
    if (!storageOk) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, habits }));
    } catch {
      toast('Couldn’t save your changes. Storage may be full or blocked.');
    }
  }

  function showNotice(text) {
    const el = $('#notice');
    el.innerHTML = `${icon('info')}<p></p><button type="button" class="icon-btn" aria-label="Dismiss message">${icon('x')}</button>`;
    $('p', el).textContent = text;
    $('button', el).addEventListener('click', () => { el.hidden = true; $('#today-title').focus(); });
    el.hidden = false;
  }

  /* ---------- Domain ---------- */
  function scheduleText(s) {
    if (s.type === 'daily') return 'Every day';
    if (s.type === 'weekly') return `${s.times} ${s.times === 1 ? 'time' : 'times'} a week`;
    const d = s.days;
    if (d.length === 7) return 'Every day';
    if (d.length === 5 && [1, 2, 3, 4, 5].every(x => d.includes(x))) return 'Weekdays';
    if (d.length === 2 && d.includes(0) && d.includes(6)) return 'Weekends';
    return WEEK_ORDER.filter(x => d.includes(x)).map(x => DOW[x]).join(', ');
  }

  const isScheduledOn = (h, d) => h.schedule.type !== 'weekdays' || h.schedule.days.includes(d.getDay());

  function weekCount(h, day) {
    const from = keyOf(mondayOf(day));
    const to = keyOf(addDays(mondayOf(day), 6));
    return h.checks.filter(k => k >= from && k <= to).length;
  }

  function isDueToday(h) {
    if (h.schedule.type === 'daily') return true;
    if (h.schedule.type === 'weekdays') return h.schedule.days.includes(today.getDay());
    return h.checks.includes(todayKey) || weekCount(h, today) < h.schedule.times;
  }

  function computeStreaks(h) {
    const unit = h.schedule.type === 'weekly' ? 'week' : 'day';
    const past = h.checks.filter(k => k <= todayKey);
    if (!past.length) return { current: 0, best: 0, unit };
    const first = parseKey(past[0]);
    const done = new Set(past);

    if (h.schedule.type === 'weekly') {
      const need = h.schedule.times;
      const counts = new Map();
      for (const k of past) {
        const w = keyOf(mondayOf(parseKey(k)));
        counts.set(w, (counts.get(w) || 0) + 1);
      }
      const met = w => (counts.get(keyOf(w)) || 0) >= need;
      const thisWeek = mondayOf(today);
      const firstWeek = mondayOf(first);
      // Current week only counts once met; an unmet current week doesn't break the streak.
      let current = met(thisWeek) ? 1 : 0;
      for (let w = addDays(thisWeek, -7); w >= firstWeek && met(w); w = addDays(w, -7)) current++;
      let best = 0, run = 0;
      for (let w = firstWeek; w <= thisWeek; w = addDays(w, 7)) {
        if (met(w)) { run++; best = Math.max(best, run); } else if (w < thisWeek) run = 0;
      }
      return { current, best: Math.max(best, current), unit };
    }

    // Daily / chosen weekdays: count consecutive scheduled days; today still pending doesn't break it.
    let current = 0;
    for (let d = today; d >= first; d = addDays(d, -1)) {
      if (!isScheduledOn(h, d)) continue;
      const k = keyOf(d);
      if (done.has(k)) current++;
      else if (k === todayKey) continue;
      else break;
    }
    let best = 0, run = 0;
    for (let d = first; d <= today; d = addDays(d, 1)) {
      if (!isScheduledOn(h, d)) continue;
      const k = keyOf(d);
      if (done.has(k)) { run++; best = Math.max(best, run); } else if (k !== todayKey) run = 0;
    }
    return { current, best: Math.max(best, current), unit };
  }

  const findHabit = id => habits.find(h => h.id === id);

  /* ---------- Undo ---------- */
  function pushUndo(entry) {
    undoStack.push(entry);
    if (undoStack.length > UNDO_LIMIT) undoStack.shift();
    updateUndoButton();
  }

  function updateUndoButton() {
    const btn = $('#undo-btn');
    const last = undoStack[undoStack.length - 1];
    if (!last && document.activeElement === btn) $('#today-title').focus();
    btn.disabled = !last;
    btn.title = last ? `Undo: ${last.label} (Ctrl/Cmd+Z)` : 'Nothing to undo';
    btn.setAttribute('aria-label', last ? `Undo: ${last.label}` : 'Undo, nothing to undo');
  }

  function undo() {
    const entry = undoStack.pop();
    if (!entry) { toast('Nothing to undo.'); return; }
    if (entry.kind === 'delete') {
      habits.splice(Math.min(entry.index, habits.length), 0, entry.before);
    } else {
      const i = habits.findIndex(h => h.id === entry.before.id);
      if (i >= 0) habits[i] = entry.before; else habits.push(entry.before);
    }
    save();
    updateUndoButton();
    render();
    toast(`Undone: ${entry.label}`);
  }

  /* ---------- Actions ---------- */
  function toggleCheck(id, key) {
    const h = findHabit(id);
    if (!h || key > todayKey) return;
    const before = clone(h);
    const wasDone = h.checks.includes(key);
    h.checks = wasDone ? h.checks.filter(k => k !== key) : [...h.checks, key].sort();
    const when = key === todayKey ? 'today' : fmtShort(parseKey(key));
    pushUndo({ kind: 'update', before, label: `${wasDone ? 'Unchecked' : 'Checked'} “${h.name}” for ${when}` });
    justToggled = wasDone ? null : `${id}:${key}`;
    save();
    render();
  }

  function archiveHabit(id) {
    const h = findHabit(id);
    if (!h) return;
    const before = clone(h);
    h.archived = true;
    const label = `Archived “${h.name}”`;
    pushUndo({ kind: 'update', before, label });
    save();
    render({ focus: `restore:${id}` });
    toast(label, true);
  }

  function restoreHabit(id) {
    const h = findHabit(id);
    if (!h) return;
    const before = clone(h);
    h.archived = false;
    pushUndo({ kind: 'update', before, label: `Restored “${h.name}”` });
    save();
    render({ focus: `archive:${id}` });
    toast(`Restored “${h.name}”`);
  }

  function deleteHabit(id) {
    const index = habits.findIndex(h => h.id === id);
    if (index < 0) return;
    const h = habits[index];
    if (!window.confirm(`Delete “${h.name}” and all of its check-ins?`)) return;
    habits.splice(index, 1);
    const label = `Deleted “${h.name}”`;
    pushUndo({ kind: 'delete', before: h, index, label });
    roving.delete(id);
    save();
    render({ focus: h.archived ? 'archived-title' : 'habits-title' });
    toast(label, true);
  }

  /* ---------- Rendering ---------- */
  function render(opts = {}) {
    // Remember focus and heatmap scroll so a re-render feels seamless.
    const active = document.activeElement;
    const focusKey = opts.focus || (active && active.dataset && active.dataset.fk);
    const scrolls = new Map($$('.heatmap-scroll').map(el => [el.dataset.scroll, el.scrollLeft]));

    const active_ = habits.filter(h => !h.archived);
    renderToday(active_);
    renderHabits(active_);
    renderArchived(habits.filter(h => h.archived));

    $$('.heatmap-scroll').forEach(el => {
      el.scrollLeft = scrolls.has(el.dataset.scroll) ? scrolls.get(el.dataset.scroll) : el.scrollWidth;
    });

    if (focusKey) {
      const target = document.querySelector(`[data-fk="${CSS.escape(focusKey)}"]`) || document.getElementById(focusKey);
      if (target && target !== document.activeElement) target.focus({ preventScroll: !opts.focus });
    }
    justToggled = null;
    newHabitId = null;
  }

  function renderToday(list) {
    $('#today-title').textContent = fmtLong(today);
    const body = $('#today-body');
    const due = list.filter(isDueToday);
    const other = list.filter(h => !isDueToday(h));

    const doneCount = due.filter(h => h.checks.includes(todayKey)).length;
    const progress = $('#today-progress');
    if (due.length) {
      const c = 2 * Math.PI * 18;
      const frac = doneCount / due.length;
      progress.innerHTML = `
        <div class="progress__text"><strong>${doneCount}/${due.length}</strong>done</div>
        <svg class="progress__ring" viewBox="0 0 44 44" aria-hidden="true" focusable="false">
          <circle class="progress__track" cx="22" cy="22" r="18" fill="none" stroke-width="5"/>
          <circle class="progress__bar" cx="22" cy="22" r="18" fill="none" stroke-width="5" stroke-linecap="round"
            stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - frac)}"${frac === 0 ? ' stroke-opacity="0"' : ''}/>
        </svg>`;
      progress.setAttribute('aria-label', `${doneCount} of ${due.length} habits due today are done`);
      progress.setAttribute('role', 'img');
    } else {
      progress.innerHTML = '';
      progress.removeAttribute('role');
      progress.removeAttribute('aria-label');
    }

    if (!list.length) {
      const anyArchived = habits.some(h => h.archived);
      body.innerHTML = `
        <div class="empty">
          ${EMPTY_ART}
          <p class="empty__title">${anyArchived ? 'No active habits' : 'No habits yet'}</p>
          <p class="empty__text">${anyArchived
            ? 'Everything is archived. Restore a habit from the Archived list, or start a new one.'
            : 'Start with something small you’d like to do regularly. It will show up here each day it’s due.'}</p>
          <button type="button" class="btn btn--primary" data-action="add" data-fk="empty-add">${icon('plus')}<span>Add your first habit</span></button>
        </div>`;
      return;
    }

    const row = (h, off) => {
      const done = h.checks.includes(todayKey);
      const st = computeStreaks(h);
      let meta = scheduleText(h.schedule);
      if (h.schedule.type === 'weekly') meta += ` · ${weekCount(h, today)} of ${h.schedule.times} this week`;
      const cls = ['today-row', off ? 'today-row--off' : '', justToggled === `${h.id}:${todayKey}` ? 'just-toggled' : ''].join(' ');
      return `
        <li>
          <button type="button" class="${cls}" style="--habit:${colorOf(h.color)}" data-action="toggle-today" data-id="${h.id}"
            data-fk="today:${h.id}" aria-pressed="${done}">
            <span class="check" aria-hidden="true">${icon('check')}</span>
            <span class="row__main">
              <span class="row__name">${esc(h.name)}</span>
              <span class="row__meta">${done ? '<span class="row__state">Done</span> · ' : ''}${esc(meta)}</span>
            </span>
            <span class="streak-chip${st.current >= 3 ? ' streak-chip--hot' : ''}">${icon('flame', 'icon--sm')}${st.current}<span class="sr-only"> ${st.unit} streak</span></span>
          </button>
        </li>`;
    };

    let html = '<h2 class="group-label" id="due-label">Due today</h2>';
    html += due.length
      ? `<ul class="today-list" aria-labelledby="due-label">${due.map(h => row(h, false)).join('')}</ul>`
      : `<div class="empty empty--compact"><p class="empty__title">Nothing due today</p><p class="empty__text">Enjoy the breather. You can still check off any habit below.</p></div>`;
    html += '<h2 class="group-label" id="other-label">Not due today</h2>';
    html += other.length
      ? `<ul class="today-list" aria-labelledby="other-label">${other.map(h => row(h, true)).join('')}</ul>`
      : `<p class="inline-note">Every active habit is on today’s list.</p>`;
    body.innerHTML = html;
  }

  function renderHabits(list) {
    $('#habits-count').textContent = list.length ? String(list.length) : '';
    const body = $('#habits-body');
    if (!list.length) {
      body.innerHTML = `
        <div class="empty">
          ${icon('calendar')}
          <p class="empty__title">Your streaks and history live here</p>
          <p class="empty__text">Add a habit to see its current and best streak and a 12-week calendar you can fill in.</p>
          <button type="button" class="btn btn--secondary" data-action="add" data-fk="habits-add">${icon('plus')}<span>New habit</span></button>
        </div>`;
      return;
    }
    body.innerHTML = `<div class="cards">${list.map(card).join('')}</div>`;
  }

  function card(h) {
    const st = computeStreaks(h);
    const start = addDays(mondayOf(today), -77);
    const rangeFrom = keyOf(start);
    const in12 = h.checks.filter(k => k >= rangeFrom && k <= todayKey).length;
    const nameId = `hn-${h.id}`;
    const color = COLORS.find(c => c.id === h.color) || COLORS[0];
    return `
      <article class="card${h.id === newHabitId ? ' card--new' : ''}" style="--habit:${color.value}" aria-labelledby="${nameId}">
        <div class="card__head">
          <div class="card__titles">
            <h3 class="card__title" id="${nameId}">${esc(h.name)}</h3>
            <p class="card__meta"><span class="colour-tag"><span class="dot" aria-hidden="true"></span>${color.name}</span><span aria-hidden="true">·</span><span>${esc(scheduleText(h.schedule))}</span></p>
          </div>
          <div class="card__actions">
            <button type="button" class="icon-btn" data-action="edit" data-id="${h.id}" data-fk="edit:${h.id}" aria-label="Edit ${esc(h.name)}" title="Edit">${icon('pencil')}</button>
            <button type="button" class="icon-btn" data-action="archive" data-id="${h.id}" data-fk="archive:${h.id}" aria-label="Archive ${esc(h.name)}" title="Archive">${icon('archive')}</button>
            <button type="button" class="icon-btn icon-btn--danger" data-action="delete" data-id="${h.id}" data-fk="delete:${h.id}" aria-label="Delete ${esc(h.name)}" title="Delete">${icon('trash')}</button>
          </div>
        </div>
        <div class="card__body">
          <dl class="stats">
            <div class="stat"><dt>${icon('flame')}Current streak</dt><dd><strong>${st.current}</strong> ${st.unit}${st.current === 1 ? '' : 's'}</dd></div>
            <div class="stat stat--small"><dt>${icon('trophy')}Best streak</dt><dd><strong>${st.best}</strong> ${st.unit}${st.best === 1 ? '' : 's'}</dd></div>
            <div class="stat stat--small"><dt>${icon('check')}12 weeks</dt><dd><strong>${in12}</strong> ${in12 === 1 ? 'check-in' : 'check-ins'}</dd></div>
          </dl>
          <div>
            ${heatmap(h, start)}
            <div class="legend" aria-hidden="true">
              <span><i class="lg-done"></i>Done</span><span><i></i>Not done</span>
              ${h.schedule.type === 'weekdays' ? '<span><i class="lg-off"></i>Not scheduled</span>' : ''}
              <span><i class="lg-future"></i>Upcoming</span>
            </div>
          </div>
        </div>
      </article>`;
  }

  function heatmap(h, start) {
    const done = new Set(h.checks);
    let focusDate = roving.get(h.id);
    if (!focusDate || focusDate > todayKey || focusDate < keyOf(start)) focusDate = todayKey;

    let months = '';
    let prevMonth = -1;
    for (let c = 0; c < 12; c++) {
      const sunday = addDays(start, c * 7 + 6);
      const m = sunday.getMonth();
      months += `<span>${m !== prevMonth ? MONTHS[m] : ''}</span>`;
      prevMonth = m;
    }

    let cells = '';
    for (let i = 0; i < 84; i++) {
      const d = addDays(start, i);
      const k = keyOf(d);
      const future = k > todayKey;
      const isDone = done.has(k);
      const off = !isScheduledOn(h, d);
      const cls = ['cell', isDone ? 'cell--done' : '', off ? 'cell--off' : '', k === todayKey ? 'cell--today' : ''].join(' ');
      const state = future ? 'upcoming' : isDone ? 'done' : 'not done';
      cells += `<button type="button" class="${cls}" data-action="cell" data-id="${h.id}" data-date="${k}" data-fk="cell:${h.id}:${k}"
        aria-label="${fmtShort(d)}: ${state}"${k === todayKey ? ' aria-current="date"' : ''}${future ? ' disabled' : ''}
        tabindex="${k === focusDate ? 0 : -1}"><span class="cell__sq">${isDone ? icon('check') : ''}</span></button>`;
    }

    return `
      <div class="heatmap-scroll" data-scroll="${h.id}">
        <div class="heatmap">
          <div class="hm-months" aria-hidden="true">${months}</div>
          <div class="hm-days" aria-hidden="true"><span>Mon</span><span></span><span>Wed</span><span></span><span>Fri</span><span></span><span>Sun</span></div>
          <div class="hm-grid" role="group" aria-label="${esc(h.name)}: last 12 weeks. Use arrow keys to move between days, Enter or Space to toggle.">${cells}</div>
        </div>
      </div>`;
  }

  function renderArchived(list) {
    $('#archived-count').textContent = list.length ? String(list.length) : '';
    const body = $('#archived-body');
    if (!list.length) {
      body.innerHTML = `
        <div class="empty empty--compact">
          ${icon('archive')}
          <p class="empty__title">Nothing archived</p>
          <p class="empty__text">Archive a habit to pause it. Its history stays safe here, and you can restore it any time.</p>
        </div>`;
      return;
    }
    body.innerHTML = `<ul class="arch-list">${list.map(h => `
      <li class="arch-row" style="--habit:${colorOf(h.color)}">
        <span class="dot" aria-hidden="true"></span>
        <div class="arch-row__main">
          <p class="arch-row__name">${esc(h.name)}</p>
          <p class="arch-row__meta">${esc(scheduleText(h.schedule))} · ${plural(h.checks.length, 'check-in')}</p>
        </div>
        <div class="arch-row__actions">
          <button type="button" class="btn btn--secondary btn--sm" data-action="restore" data-id="${h.id}" data-fk="restore:${h.id}" aria-label="Restore ${esc(h.name)}">${icon('restore', 'icon--sm')}<span>Restore</span></button>
          <button type="button" class="icon-btn icon-btn--danger" data-action="delete" data-id="${h.id}" data-fk="delete:${h.id}" aria-label="Delete ${esc(h.name)}" title="Delete">${icon('trash')}</button>
        </div>
      </li>`).join('')}</ul>`;
  }

  /* ---------- Toast ---------- */
  let toastTimer = null;
  function toast(message, withUndo = false) {
    const region = $('#toast-region');
    clearTimeout(toastTimer);
    region.innerHTML = '';
    const el = document.createElement('div');
    el.className = 'toast' + (withUndo ? '' : ' toast--plain');
    el.innerHTML = `${icon('check')}<span class="toast__msg"></span>`;
    $('.toast__msg', el).textContent = message;
    if (withUndo) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'toast__btn';
      b.textContent = 'Undo';
      b.addEventListener('click', () => { region.innerHTML = ''; undo(); });
      el.appendChild(b);
    }
    region.appendChild(el);
    let remaining = withUndo ? 6000 : 3500;
    const arm = () => { toastTimer = setTimeout(() => { if (el.contains(document.activeElement)) $('#today-title').focus(); el.remove(); }, remaining); };
    el.addEventListener('mouseenter', () => clearTimeout(toastTimer));
    el.addEventListener('mouseleave', arm);
    el.addEventListener('focusin', () => clearTimeout(toastTimer));
    el.addEventListener('focusout', arm);
    arm();
  }

  /* ---------- Dialog ---------- */
  const dialog = $('#habit-dialog');
  const form = $('#habit-form');
  const nameInput = $('#f-name');
  const timesInput = $('#f-times');
  let editingId = null;
  let dialogOpener = null;

  function buildDialogControls() {
    $('#swatches').innerHTML = COLORS.map(c => `
      <label class="swatch-wrap">
        <input type="radio" name="color" value="${c.id}" class="overlay-input">
        <span class="swatch" style="--c:${c.value}"><span class="swatch__chip">${icon('check')}</span>${c.name}</span>
      </label>`).join('');
    $('#days').innerHTML = WEEK_ORDER.map(d => `
      <label class="day-chip"><input type="checkbox" name="days" value="${d}" class="overlay-input"><span><span class="sr-only">${DOW_LONG[d]}</span><span aria-hidden="true">${DOW[d]}</span></span></label>`).join('');
  }

  function setError(id, msg, input) {
    const el = $('#' + id);
    if (msg) {
      el.innerHTML = `${icon('alert')}<span></span>`;
      $('span', el).textContent = msg;
      el.hidden = false;
    } else {
      el.hidden = true;
      el.textContent = '';
    }
    if (input) input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }

  function syncSchedulePanels() {
    const type = form.elements.stype.value;
    $('#days-panel').hidden = type !== 'weekdays';
    $('#times-panel').hidden = type !== 'weekly';
    syncStepper();
  }

  function syncStepper() {
    const v = Number(timesInput.value);
    $('#times-dec').disabled = !(v > 1);
    $('#times-inc').disabled = !(v < 7) && Number.isFinite(v);
  }

  function updateNameCount() {
    const len = nameInput.value.trim().length;
    const el = $('#name-count');
    el.textContent = `${len}/${NAME_MAX}`;
    el.classList.toggle('field__count--over', len > NAME_MAX);
  }

  function openDialog(habit, opener) {
    if (dialog.open) return;
    editingId = habit ? habit.id : null;
    dialogOpener = opener || document.activeElement;
    $('#dialog-title').textContent = habit ? 'Edit habit' : 'New habit';
    $('#dialog-submit').textContent = habit ? 'Save changes' : 'Add habit';
    form.reset();
    nameInput.value = habit ? habit.name : '';
    const color = habit ? habit.color : COLORS[habits.length % COLORS.length].id;
    form.querySelector(`input[name="color"][value="${color}"]`).checked = true;
    const s = habit ? habit.schedule : { type: 'daily' };
    form.querySelector(`input[name="stype"][value="${s.type}"]`).checked = true;
    const days = s.type === 'weekdays' ? s.days : [1, 2, 3, 4, 5];
    $$('input[name="days"]', form).forEach(cb => { cb.checked = days.includes(Number(cb.value)); });
    timesInput.value = s.type === 'weekly' ? s.times : 3;
    setError('name-error', '', nameInput);
    setError('days-error', '');
    setError('times-error', '', timesInput);
    updateNameCount();
    syncSchedulePanels();
    dialog.showModal();
    nameInput.focus();
    if (habit) nameInput.select();
  }

  function closeDialog() {
    if (dialog.open) dialog.close();
  }

  dialog.addEventListener('close', () => {
    const fk = dialogOpener && dialogOpener.dataset ? dialogOpener.dataset.fk : null;
    let target = dialogOpener && document.contains(dialogOpener) ? dialogOpener : null;
    if (!target && fk) target = document.querySelector(`[data-fk="${CSS.escape(fk)}"]`);
    if (!target) target = $('#add-btn');
    target.focus();
    dialogOpener = null;
    editingId = null;
  });

  // Keep Tab inside the dialog.
  dialog.addEventListener('keydown', e => {
    if (e.key !== 'Tab') return;
    // Unchecked radios are skipped by the browser's own tab order (arrow keys move within a group).
    const list = $$('button:not(:disabled), input:not(:disabled)', dialog)
      .filter(el => !(el.type === 'radio' && !el.checked) && !el.closest('[hidden]'));
    if (!list.length) return;
    const first = list[0], last = list[list.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  dialog.addEventListener('click', e => {
    if (e.target === dialog) closeDialog();
    if (e.target.closest('[data-close]')) closeDialog();
  });

  nameInput.addEventListener('input', () => {
    updateNameCount();
    if (nameInput.getAttribute('aria-invalid') === 'true') setError('name-error', '', nameInput);
  });
  form.addEventListener('change', e => {
    if (e.target.name === 'stype') syncSchedulePanels();
    if (e.target.name === 'days' && $$('input[name="days"]:checked', form).length) setError('days-error', '');
  });
  timesInput.addEventListener('input', () => { syncStepper(); setError('times-error', '', timesInput); });
  const step = delta => {
    const v = Number(timesInput.value);
    const next = Math.min(7, Math.max(1, (Number.isInteger(v) ? v : 3) + delta));
    timesInput.value = next;
    setError('times-error', '', timesInput);
    syncStepper();
    if ((delta < 0 && next === 1) || (delta > 0 && next === 7)) timesInput.focus();
  };
  $('#times-dec').addEventListener('click', () => step(-1));
  $('#times-inc').addEventListener('click', () => step(1));

  form.addEventListener('submit', e => {
    e.preventDefault();
    const name = nameInput.value.trim();
    let nameErr = '';
    if (!name) nameErr = 'Give your habit a name.';
    else if (name.length > NAME_MAX) nameErr = `Keep the name to ${NAME_MAX} characters or fewer (it’s ${name.length} now).`;
    else {
      const dup = habits.find(h => h.id !== editingId && sameName(h.name, name));
      if (dup) nameErr = `You already have a habit called “${dup.name}”${dup.archived ? ' (in Archived)' : ''}. Try a different name.`;
    }
    setError('name-error', nameErr, nameInput);

    const type = form.elements.stype.value;
    let schedule = { type: 'daily' };
    let daysErr = '', timesErr = '';
    if (type === 'weekdays') {
      const days = $$('input[name="days"]:checked', form).map(cb => Number(cb.value)).sort((a, b) => a - b);
      if (!days.length) daysErr = 'Pick at least one day.';
      schedule = { type, days };
    } else if (type === 'weekly') {
      const raw = timesInput.value.trim();
      const n = Number(raw);
      if (!raw || !Number.isInteger(n) || n < 1 || n > 7) timesErr = 'Choose a whole number from 1 to 7.';
      schedule = { type, times: n };
    }
    setError('days-error', daysErr);
    setError('times-error', timesErr, timesInput);

    if (nameErr) { nameInput.focus(); return; }
    if (daysErr) { $('input[name="days"]', form).focus(); return; }
    if (timesErr) { timesInput.focus(); return; }

    const color = form.elements.color.value;
    if (editingId) {
      const h = findHabit(editingId);
      if (h) {
        const before = clone(h);
        const changed = h.name !== name || h.color !== color || JSON.stringify(h.schedule) !== JSON.stringify(schedule);
        if (changed) {
          Object.assign(h, { name, color, schedule });
          pushUndo({ kind: 'update', before, label: `Edited “${before.name}”` });
          save();
          render();
          toast(`Saved changes to “${name}”`);
        }
      }
      closeDialog();
    } else {
      const h = { id: uid(), name, color, schedule, archived: false, createdAt: todayKey, checks: [] };
      habits.push(h);
      newHabitId = h.id;
      save();
      render();
      closeDialog();
      toast(`Added “${name}”`);
    }
  });

  /* ---------- Import / export ---------- */
  function exportData() {
    const data = { app: 'kept', version: 1, exportedAt: new Date().toISOString(), habits };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kept-habits-${todayKey}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    toast(habits.length ? `Exported ${plural(habits.length, 'habit')}` : 'Exported an empty backup');
  }

  async function importFile(file) {
    const errEl = 'import-error';
    setError(errEl, '');
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { setError(errEl, 'That file is too large to be a Kept backup. Nothing was imported.'); return; }
    let parsed;
    try {
      parsed = JSON.parse(await file.text());
    } catch {
      setError(errEl, 'That file isn’t valid JSON, so nothing was imported.');
      return;
    }
    const res = validateHabits(parsed);
    if (res.error) { setError(errEl, `Nothing was imported. ${res.error}`); return; }

    let added = 0, merged = 0;
    const ids = new Set(habits.map(h => h.id));
    for (const h of res.habits) {
      const existing = habits.find(x => sameName(x.name, h.name));
      if (existing) {
        existing.checks = [...new Set([...existing.checks, ...h.checks])].sort();
        merged++;
      } else {
        if (ids.has(h.id)) h.id = uid();
        ids.add(h.id);
        habits.push(h);
        added++;
      }
    }
    // Snapshots taken before a merge would silently drop imported check-ins, so start a fresh undo history.
    undoStack = [];
    updateUndoButton();
    save();
    render();
    toast(res.habits.length
      ? `Imported ${plural(res.habits.length, 'habit')}: ${added} new, ${merged} merged`
      : 'The file had no habits, so nothing changed');
  }

  /* ---------- Events ---------- */
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-action]');
    if (!btn || btn.disabled) return;
    const id = btn.dataset.id;
    switch (btn.dataset.action) {
      case 'toggle-today': toggleCheck(id, todayKey); break;
      case 'cell': roving.set(id, btn.dataset.date); toggleCheck(id, btn.dataset.date); break;
      case 'edit': openDialog(findHabit(id), btn); break;
      case 'archive': archiveHabit(id); break;
      case 'restore': restoreHabit(id); break;
      case 'delete': deleteHabit(id); break;
      case 'add': openDialog(null, btn); break;
    }
  });

  $('#add-btn').addEventListener('click', e => openDialog(null, e.currentTarget));
  $('#undo-btn').addEventListener('click', undo);
  $('#export-btn').addEventListener('click', exportData);
  $('#import-btn').addEventListener('click', () => $('#import-file').click());
  $('#import-file').addEventListener('change', async e => {
    const file = e.target.files && e.target.files[0];
    await importFile(file);
    e.target.value = '';
  });

  // Arrow keys move between rows on Today.
  $('#today-body').addEventListener('keydown', e => {
    const row = e.target.closest('.today-row');
    if (!row) return;
    const rows = $$('.today-row', $('#today-body'));
    const i = rows.indexOf(row);
    let next = null;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') next = rows[Math.min(rows.length - 1, i + 1)];
    else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') next = rows[Math.max(0, i - 1)];
    else if (e.key === 'Home') next = rows[0];
    else if (e.key === 'End') next = rows[rows.length - 1];
    if (next) { e.preventDefault(); next.focus(); }
  });

  // Roving focus inside each heatmap.
  $('#habits-body').addEventListener('keydown', e => {
    const cell = e.target.closest('.cell');
    if (!cell) return;
    const delta = { ArrowUp: -1, ArrowDown: 1, ArrowLeft: -7, ArrowRight: 7 }[e.key];
    let target;
    if (delta !== undefined) {
      const d = addDays(parseKey(cell.dataset.date), delta);
      let k = keyOf(d);
      if (k > todayKey) k = todayKey;
      target = cell.parentElement.querySelector(`[data-date="${k}"]`);
    } else if (e.key === 'Home') target = cell.parentElement.querySelector('.cell');
    else if (e.key === 'End') target = cell.parentElement.querySelector(`[data-date="${todayKey}"]`);
    if (!target) { if (delta !== undefined || e.key === 'Home' || e.key === 'End') e.preventDefault(); return; }
    e.preventDefault();
    $$('.cell', cell.parentElement).forEach(c => { c.tabIndex = -1; });
    target.tabIndex = 0;
    roving.set(cell.dataset.id, target.dataset.date);
    target.focus();
  });
  $('#habits-body').addEventListener('focusin', e => {
    const cell = e.target.closest('.cell');
    if (cell) roving.set(cell.dataset.id, cell.dataset.date);
  });

  // Global shortcuts.
  document.addEventListener('keydown', e => {
    if (dialog.open || e.defaultPrevented) return;
    const t = e.target;
    const editable = t instanceof Element && t.closest('input, textarea, select, [contenteditable=""], [contenteditable="true"]');
    if ((e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && e.key.toLowerCase() === 'z') {
      if (editable) return;
      e.preventDefault();
      undo();
      return;
    }
    if (!e.ctrlKey && !e.metaKey && !e.altKey && (e.key === 'n' || e.key === 'N') && !editable && !e.repeat) {
      e.preventDefault();
      openDialog(null, $('#add-btn'));
    }
  });

  /* ---------- Midnight rollover ---------- */
  function checkDay() {
    const now = startOfToday();
    const k = keyOf(now);
    if (k !== todayKey) {
      today = now;
      todayKey = k;
      render();
    }
  }
  setInterval(checkDay, 15000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) checkDay(); });
  window.addEventListener('focus', checkDay);
  window.addEventListener('storage', e => {
    if (e.key !== STORAGE_KEY) return;
    try {
      const res = validateHabits(JSON.parse(e.newValue));
      if (!res.error) { habits = res.habits; undoStack = []; updateUndoButton(); render(); }
    } catch { /* ignore foreign writes we can't read */ }
  });

  /* ---------- Init ---------- */
  $$('[data-icon]').forEach(el => { el.outerHTML = icon(el.dataset.icon); });
  buildDialogControls();
  load();
  updateUndoButton();
  render();
})();
