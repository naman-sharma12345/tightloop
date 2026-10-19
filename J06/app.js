/* Steady — habit tracker. Plain JS, no dependencies. */
(() => {
  'use strict';

  const STORAGE_KEY = 'steady-habit-tracker';
  const MAX_UNDO = 10;
  const NAME_MAX = 60;
  const WEEKS = 12;

  const COLORS = [
    { id: 'sage', name: 'Sage' },
    { id: 'ocean', name: 'Ocean' },
    { id: 'plum', name: 'Plum' },
    { id: 'amber', name: 'Amber' },
    { id: 'clay', name: 'Clay' },
    { id: 'slate', name: 'Slate' },
  ];
  const COLOR_IDS = COLORS.map((c) => c.id);
  const WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const WD_LONG = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const MON_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  const svg = (paths, cls = 'icon') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${paths}</svg>`;
  const ICONS = {
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    flame: '<path d="M12 21c3.9 0 6.5-2.6 6.5-6.3 0-3.2-2-5.6-3.6-7.3-.4 1.9-1.4 3-2.6 3.3.3-3-1-5.6-3.3-7.2.2 3-1.6 4.9-3 6.6A8.3 8.3 0 0 0 5.5 14.7C5.5 18.4 8.1 21 12 21Z"/>',
    trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0V4Z"/><path d="M16 5h3v1.5A3.5 3.5 0 0 1 15.6 10M8 5H5v1.5A3.5 3.5 0 0 0 8.4 10"/><path d="M12 13v4M8.5 20h7M9.5 17h5"/>',
    pencil: '<path d="M4 20h4L18.5 9.5a2.1 2.1 0 0 0-4-4L4 16v4Z"/><path d="m13.5 6.5 4 4"/>',
    archive: '<rect x="3" y="4" width="18" height="4.5" rx="1.2"/><path d="M5 8.5V18a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5"/><path d="M10 12.5h4"/>',
    restore: '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4.5h4.5"/>',
    trash: '<path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>',
    calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    repeat: '<path d="M17 3l3 3-3 3"/><path d="M4 11V9a3 3 0 0 1 3-3h13"/><path d="M7 21l-3-3 3-3"/><path d="M20 13v2a3 3 0 0 1-3 3H4"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/>',
    close: '<path d="M6 6l12 12M18 6 6 18"/>',
    undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    sparkle: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.3 6.3l2.5 2.5M15.2 15.2l2.5 2.5M6.3 17.7l2.5-2.5M15.2 8.8l2.5-2.5"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
  };
  const icon = (name, cls) => svg(ICONS[name], cls);

  const EMPTY_ART = `<svg viewBox="0 0 56 56" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
    <rect x="8" y="10" width="40" height="38" rx="8" fill="#e4ece8" stroke="none"/>
    <rect x="8" y="10" width="40" height="38" rx="8"/>
    <path d="M8 20h40M19 6v8M37 6v8"/>
    <rect x="15" y="26" width="6" height="6" rx="1.5" fill="currentColor" stroke="none"/>
    <rect x="25" y="26" width="6" height="6" rx="1.5" fill="currentColor" stroke="none" opacity=".55"/>
    <rect x="35" y="26" width="6" height="6" rx="1.5"/>
    <rect x="15" y="36" width="6" height="6" rx="1.5" fill="currentColor" stroke="none" opacity=".55"/>
    <rect x="25" y="36" width="6" height="6" rx="1.5"/>
    <rect x="35" y="36" width="6" height="6" rx="1.5"/>
  </svg>`;

  /* ---------- Dates (always local time) ---------- */
  const pad = (n) => String(n).padStart(2, '0');
  const keyOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const parseKey = (k) => {
    const [y, m, d] = k.split('-').map(Number);
    return new Date(y, m - 1, d, 12); // noon: immune to DST edges
  };
  const todayKey = () => keyOf(new Date());
  const addDays = (k, n) => {
    const d = parseKey(k);
    d.setDate(d.getDate() + n);
    return keyOf(d);
  };
  const dow = (k) => (parseKey(k).getDay() + 6) % 7; // 0 = Monday
  const weekStart = (k) => addDays(k, -dow(k));
  const isValidKey = (k) => {
    if (typeof k !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(k)) return false;
    const y = Number(k.slice(0, 4));
    return y >= 1970 && y <= 9999 && keyOf(parseKey(k)) === k;
  };
  const shortLabel = (k) => {
    const d = parseKey(k);
    return `${WD[dow(k)]} ${d.getDate()} ${MON[d.getMonth()]}`;
  };
  const longLabel = (k) => {
    const d = parseKey(k);
    return `${WD_LONG[dow(k)]} ${d.getDate()} ${MON_LONG[d.getMonth()]}`;
  };

  /* ---------- Helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const uid = () => {
    try { if (crypto.randomUUID) return crypto.randomUUID(); } catch (e) { /* insecure context */ }
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  };
  const normName = (s) => s.trim().toLocaleLowerCase();
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  const quote = (s) => `“${s}”`;

  /* ---------- Schedules ---------- */
  function parseSchedule(s) {
    if (!s || typeof s !== 'object') return null;
    if (s.type === 'daily') return { type: 'daily' };
    if (s.type === 'days') {
      if (!Array.isArray(s.days)) return null;
      const days = [...new Set(s.days)].filter((d) => Number.isInteger(d) && d >= 0 && d <= 6).sort();
      if (!days.length || days.length !== new Set(s.days).size) return null;
      return { type: 'days', days };
    }
    if (s.type === 'weekly') {
      if (!Number.isInteger(s.times) || s.times < 1 || s.times > 7) return null;
      return { type: 'weekly', times: s.times };
    }
    return null;
  }

  function scheduleText(s) {
    if (s.type === 'daily') return 'Every day';
    if (s.type === 'weekly') return s.times === 1 ? 'Once a week' : `${s.times} times a week`;
    const d = s.days.join(',');
    if (d === '0,1,2,3,4,5,6') return 'Every day';
    if (d === '0,1,2,3,4') return 'Weekdays';
    if (d === '5,6') return 'Weekends';
    return s.days.map((i) => WD[i]).join(', ');
  }

  const isScheduledDay = (h, k) => h.schedule.type === 'daily' || h.schedule.type === 'weekly' || h.schedule.days.includes(dow(k));

  function weekCount(h, k) {
    const ws = weekStart(k);
    let c = 0;
    for (let i = 0; i < 7; i++) if (h.checks.includes(addDays(ws, i))) c++;
    return c;
  }

  function isDueToday(h, today) {
    if (h.schedule.type === 'weekly') return h.checks.includes(today) || weekCount(h, today) < h.schedule.times;
    return isScheduledDay(h, today);
  }

  /* Streaks: consecutive scheduled periods completed up to today. The current period
     (today / this week) extends a streak once done but never breaks it while still open. */
  function streaks(h, today) {
    const set = new Set(h.checks);
    const past = h.checks.filter((k) => k <= today);
    if (!past.length) return { current: 0, best: 0 };
    const first = past[0]; // checks are kept sorted
    let run = 0;
    let best = 0;
    if (h.schedule.type === 'weekly') {
      const thisWeek = weekStart(today);
      for (let ws = weekStart(first); ws <= thisWeek; ws = addDays(ws, 7)) {
        let c = 0;
        for (let i = 0; i < 7; i++) if (set.has(addDays(ws, i))) c++;
        if (c >= h.schedule.times) best = Math.max(best, ++run);
        else if (ws !== thisWeek) run = 0;
      }
    } else {
      for (let k = first; k <= today; k = addDays(k, 1)) {
        if (!isScheduledDay(h, k)) continue;
        if (set.has(k)) best = Math.max(best, ++run);
        else if (k !== today) run = 0;
      }
    }
    return { current: run, best };
  }

  const streakUnit = (h, n) => (h.schedule.type === 'weekly' ? (n === 1 ? 'week' : 'weeks') : (n === 1 ? 'day' : 'days'));

  /* ---------- Validation (storage + import share it) ---------- */
  function validateData(data, { keepIds = false } = {}) {
    const list = Array.isArray(data) ? data : data && typeof data === 'object' && Array.isArray(data.habits) ? data.habits : null;
    if (!list) return { error: 'it doesn’t contain a list of habits.' };
    const out = [];
    const byName = new Map();
    const ids = new Set();
    for (let i = 0; i < list.length; i++) {
      const h = list[i];
      const where = `habit ${i + 1}`;
      if (!h || typeof h !== 'object' || Array.isArray(h)) return { error: `${where} isn’t a habit.` };
      if (typeof h.name !== 'string' || !h.name.trim()) return { error: `${where} has no name.` };
      const name = h.name.trim();
      if (name.length > NAME_MAX) return { error: `the name of ${where} is longer than ${NAME_MAX} characters.` };
      const color = h.color === undefined ? 'sage' : h.color;
      if (!COLOR_IDS.includes(color)) return { error: `${quote(name)} has an unknown colour.` };
      const schedule = h.schedule === undefined ? { type: 'daily' } : parseSchedule(h.schedule);
      if (!schedule) return { error: `${quote(name)} has a schedule we don’t understand.` };
      const rawChecks = h.checks === undefined ? [] : h.checks;
      if (!Array.isArray(rawChecks)) return { error: `the check-ins of ${quote(name)} aren’t a list.` };
      for (const c of rawChecks) {
        if (!isValidKey(c)) return { error: `${quote(name)} has a check-in that isn’t a date (YYYY-MM-DD).` };
      }
      if (h.archived !== undefined && typeof h.archived !== 'boolean') return { error: `${quote(name)} has an invalid archived flag.` };
      const checks = [...new Set(rawChecks)].sort();

      const existing = byName.get(normName(name));
      if (existing) { // duplicate inside the same data: merge it
        existing.checks = [...new Set([...existing.checks, ...checks])].sort();
        continue;
      }
      let id = keepIds && typeof h.id === 'string' && h.id ? h.id : uid();
      if (ids.has(id)) id = uid();
      ids.add(id);
      const habit = {
        id,
        name,
        color,
        schedule,
        archived: !!h.archived,
        createdAt: isValidKey(h.createdAt) ? h.createdAt : checks[0] || todayKey(),
        checks,
      };
      byName.set(normName(name), habit);
      out.push(habit);
    }
    return { habits: out };
  }

  /* ---------- State & persistence ---------- */
  let habits = [];
  let notice = null;
  const undoStack = [];
  let currentDay = todayKey();
  const heatFocus = new Map(); // habit id -> date key holding the roving tab stop

  function load() {
    let raw;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      notice = { title: 'Saving is turned off in this browser.', text: 'You can still use the tracker, but changes won’t be kept after you close the page.' };
      return;
    }
    if (raw === null) return; // first visit: friendly empty state handles it
    try {
      const res = validateData(JSON.parse(raw), { keepIds: true });
      if (res.error) throw new Error(res.error);
      habits = res.habits;
    } catch (e) {
      habits = [];
      notice = { title: 'We couldn’t read your saved habits, so Steady started empty.', text: 'If you have an exported backup, import it below to bring everything back.' };
    }
  }

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, habits }));
    } catch (e) {
      if (!notice) {
        notice = { title: 'Your latest change couldn’t be saved.', text: 'Browser storage may be full or disabled. Export a backup to be safe.' };
        renderNotice();
      }
    }
  }

  const findHabit = (id) => habits.find((h) => h.id === id);

  function commit(label, mutate) {
    undoStack.push({ label, snapshot: JSON.stringify(habits) });
    if (undoStack.length > MAX_UNDO) undoStack.shift();
    mutate();
    save();
    render();
  }

  function undo() {
    const entry = undoStack.pop();
    if (!entry) {
      toast('Nothing to undo', 'undo');
      return;
    }
    habits = JSON.parse(entry.snapshot);
    save();
    render();
    toast(`Undone: ${entry.label}`, 'undo');
  }

  function toggleCheck(id, date) {
    const h = findHabit(id);
    if (!h || date > todayKey()) return;
    const done = h.checks.includes(date);
    const label = `${done ? 'unchecked' : 'checked'} ${quote(h.name)} on ${shortLabel(date)}`;
    commit(label, () => {
      h.checks = done ? h.checks.filter((k) => k !== date) : [...h.checks, date].sort();
    });
  }

  /* ---------- Rendering ---------- */
  const els = {
    todayDate: $('#today-date'),
    todaySummary: $('#today-summary'),
    todayProgress: $('#today-progress'),
    todayDue: $('#today-due'),
    todayOther: $('#today-other'),
    habitList: $('#habit-list'),
    habitsMeta: $('#habits-meta'),
    archivedList: $('#archived-list'),
    archivedMeta: $('#archived-meta'),
    undoBtn: $('#undo-btn'),
    addBtn: $('#add-btn'),
    notice: $('#notice-region'),
    toasts: $('#toast-region'),
    importError: $('#import-error'),
    importFile: $('#import-file'),
  };

  function render() {
    const active = document.activeElement;
    const focusKey = active && active.dataset ? active.dataset.key : null;
    const today = todayKey();
    currentDay = today;

    renderToday(today);
    renderHabits(today);
    renderArchived();
    renderNotice();

    els.undoBtn.disabled = undoStack.length === 0;
    els.undoBtn.title = undoStack.length ? `Undo ${undoStack[undoStack.length - 1].label}` : 'Nothing to undo';

    if (focusKey && active && !document.contains(active)) {
      const next = document.querySelector(`[data-key="${CSS.escape(focusKey)}"]`);
      if (next) next.focus({ preventScroll: true });
    }
  }

  function todayRow(h, today, quiet) {
    const done = h.checks.includes(today);
    const { current } = streaks(h, today);
    const meta = h.schedule.type === 'weekly'
      ? `${Math.min(weekCount(h, today), 99)} of ${h.schedule.times} this week`
      : scheduleText(h.schedule);
    return `<li>
      <button type="button" class="today-row${done ? ' is-done' : ''}${quiet ? ' today-row--quiet' : ''}"
        style="--c: var(--c-${h.color})" data-action="toggle-today" data-id="${h.id}" data-key="row-${h.id}"
        aria-pressed="${done}">
        <span class="check">${icon('check')}</span>
        <span class="tr-text">
          <span class="tr-name">${esc(h.name)}</span>
          <span class="tr-meta"><span class="tr-swatch" aria-hidden="true"></span><span>${esc(meta)}</span></span>
        </span>
        <span class="tr-status">
          ${current > 0 ? `<span class="streak-pill">${icon('flame')}${current}<span class="visually-hidden"> ${streakUnit(h, current)} streak,</span></span>` : ''}
          <span class="${done ? '' : 'visually-hidden'}">${done ? 'Done' : 'Not done'}</span>
        </span>
      </button>
    </li>`;
  }

  function renderToday(today) {
    const active = habits.filter((h) => !h.archived);
    const due = active.filter((h) => isDueToday(h, today));
    const other = active.filter((h) => !isDueToday(h, today));
    const doneCount = due.filter((h) => h.checks.includes(today)).length;

    els.todayDate.textContent = longLabel(today);

    // Progress ring
    const pct = due.length ? doneCount / due.length : 0;
    const C = 2 * Math.PI * 26;
    els.todayProgress.innerHTML = active.length ? `
      <svg viewBox="0 0 64 64"><circle class="progress__track" cx="32" cy="32" r="26"/>
      <circle class="progress__bar" cx="32" cy="32" r="26" stroke-dasharray="${C.toFixed(2)}" stroke-dashoffset="${(C * (1 - pct)).toFixed(2)}"/></svg>
      <span class="progress__label">${doneCount}/${due.length}</span>` : '';

    if (!active.length) {
      els.todaySummary.textContent = habits.length ? 'All your habits are archived.' : 'Nothing to track yet.';
    } else if (!due.length) {
      els.todaySummary.textContent = 'Nothing due today.';
    } else {
      els.todaySummary.textContent = `${doneCount} of ${plural(due.length, 'habit', 'habits')} done`;
    }

    if (!active.length) {
      els.todayDue.innerHTML = `<div class="empty">
        <div class="empty__art">${EMPTY_ART}</div>
        <p class="empty__title">${habits.length ? 'Everything is resting' : 'Your day is a blank page'}</p>
        <p class="empty__text">${habits.length
          ? 'Restore an archived habit or add a new one, and it will show up here on the days it’s due.'
          : 'Add a habit and it will appear here each day it’s due. Tap it to check it off.'}</p>
        <button type="button" class="btn btn--primary" data-action="add" data-key="today-empty-add">${icon('plus')}<span>Add a habit</span></button>
      </div>`;
    } else if (!due.length) {
      els.todayDue.innerHTML = `<div class="empty empty--compact">
        <p class="empty__title">Nothing due today</p>
        <p class="empty__text">Enjoy the breather. You can still check off anything below if you get to it.</p>
      </div>`;
    } else {
      els.todayDue.innerHTML = `
        <h3 class="group-label" id="due-label">Due today</h3>
        <ul class="today-list" aria-labelledby="due-label">${due.map((h) => todayRow(h, today, false)).join('')}</ul>
        ${doneCount === due.length ? `<p class="all-done">${icon('sparkle')}All done for today. Nicely kept.</p>` : ''}`;
    }

    els.todayOther.innerHTML = other.length ? `
      <h3 class="group-label" id="other-label">Not due today</h3>
      <ul class="today-list" aria-labelledby="other-label">${other.map((h) => todayRow(h, today, true)).join('')}</ul>` : '';
  }

  function heatmapHTML(h, today) {
    const set = new Set(h.checks);
    const thisWeek = weekStart(today);
    const start = addDays(thisWeek, -7 * (WEEKS - 1));
    let focusDate = heatFocus.get(h.id);
    if (!focusDate || focusDate < start || focusDate > today) focusDate = today;

    const months = [];
    for (let w = 0; w < WEEKS; w++) {
      const ws = addDays(start, w * 7);
      let label = '';
      for (let i = 0; i < 7; i++) {
        const d = parseKey(addDays(ws, i));
        if (d.getDate() === 1) label = MON[d.getMonth()];
      }
      if (w === 0 && !label && parseKey(ws).getDate() <= 21) label = MON[parseKey(ws).getMonth()];
      months.push(`<span>${label}</span>`);
    }
    // Avoid two labels crowding the first columns.
    if (months[0] !== '<span></span>' && months[1] !== '<span></span>') months[0] = '<span></span>';

    const days = WD.map((d, i) => `<span class="${i % 2 ? 'd-skip' : ''}"><span class="d-long">${d}</span><span class="d-short">${d[0]}</span></span>`).join('');

    let cells = '';
    for (let i = 0; i < WEEKS * 7; i++) {
      const k = addDays(start, i);
      const future = k > today;
      const done = set.has(k);
      const sched = isScheduledDay(h, k);
      const cls = ['cell'];
      let state;
      if (future) { cls.push('cell--future'); state = 'upcoming'; }
      else if (done) { cls.push('cell--done'); state = 'done'; }
      else if (!sched) { cls.push('cell--off'); state = 'not done (not scheduled)'; }
      else state = 'not done';
      if (k === today) cls.push('cell--today');
      const label = `${shortLabel(k)}: ${state}${k === today ? ' (today)' : ''}`;
      cells += `<button type="button" class="${cls.join(' ')}" data-action="toggle-day" data-id="${h.id}" data-date="${k}"
        data-key="cell-${h.id}-${k}" aria-label="${label}" title="${label}"${future ? ' disabled' : ''} tabindex="${k === focusDate ? 0 : -1}"></button>`;
    }

    return `<div class="heatmap">
      <div class="hm-months" aria-hidden="true">${months.join('')}</div>
      <div class="hm-days" aria-hidden="true">${days}</div>
      <div class="hm-grid" role="group" aria-label="${esc(h.name)}: last ${WEEKS} weeks. Use arrow keys to move, Space to toggle a day." data-heatmap="${h.id}">${cells}</div>
      <div class="hm-legend" aria-hidden="true">
        <span><span class="cell cell--done"></span>Done</span>
        <span><span class="cell"></span>Not done</span>
        ${h.schedule.type === 'days' ? '<span><span class="cell cell--off"></span>Not scheduled</span>' : ''}
      </div>
    </div>`;
  }

  function renderHabits(today) {
    const active = habits.filter((h) => !h.archived);
    els.habitsMeta.textContent = active.length ? plural(active.length, 'habit', 'habits') : '';
    if (!active.length) {
      els.habitList.innerHTML = `<div class="empty">
        <p class="empty__title">No habits yet</p>
        <p class="empty__text">Start with something small you can do in two minutes. Your streaks and a 12-week history will show up here.</p>
        <button type="button" class="btn btn--secondary" data-action="add" data-key="list-empty-add">${icon('plus')}<span>Create a habit</span></button>
      </div>`;
      return;
    }
    els.habitList.innerHTML = active.map((h) => {
      const { current, best } = streaks(h, today);
      const recent = h.checks.filter((k) => k >= addDays(weekStart(today), -7 * (WEEKS - 1)) && k <= today).length;
      return `<article class="habit-card" style="--c: var(--c-${h.color})" aria-labelledby="name-${h.id}">
        <div class="hc-head">
          <div class="hc-title">
            <h3 class="hc-name" id="name-${h.id}">${esc(h.name)}</h3>
            <p class="hc-sched">${icon(h.schedule.type === 'weekly' ? 'repeat' : 'calendar')}<span>${esc(scheduleText(h.schedule))}</span><span class="visually-hidden">, colour ${COLORS.find((c) => c.id === h.color).name}</span></p>
          </div>
          <div class="hc-actions">
            <button type="button" class="icon-btn" data-action="edit" data-id="${h.id}" data-key="edit-${h.id}" aria-label="Edit ${esc(h.name)}" title="Edit">${icon('pencil')}</button>
            <button type="button" class="icon-btn" data-action="archive" data-id="${h.id}" data-key="archive-${h.id}" aria-label="Archive ${esc(h.name)}" title="Archive">${icon('archive')}</button>
            <button type="button" class="icon-btn icon-btn--danger" data-action="delete" data-id="${h.id}" data-key="delete-${h.id}" aria-label="Delete ${esc(h.name)}" title="Delete">${icon('trash')}</button>
          </div>
        </div>
        <div class="hc-body">
          <dl class="hc-stats">
            <div class="stat"><dt>Current streak</dt><dd><span class="stat__icon">${icon('flame')}</span><span class="stat__num">${current}</span>${streakUnit(h, current)}</dd></div>
            <div class="stat"><dt>Best streak</dt><dd><span class="stat__icon">${icon('trophy')}</span><span class="stat__num">${best}</span>${streakUnit(h, best)}</dd></div>
            <div class="stat"><dt>12 weeks</dt><dd><span class="stat__num">${recent}</span>${recent === 1 ? 'check-in' : 'check-ins'}</dd></div>
          </dl>
          ${heatmapHTML(h, today)}
        </div>
      </article>`;
    }).join('');
  }

  function renderArchived() {
    const archived = habits.filter((h) => h.archived);
    els.archivedMeta.textContent = archived.length ? plural(archived.length, 'habit', 'habits') : '';
    if (!archived.length) {
      els.archivedList.innerHTML = `<div class="empty empty--compact">
        <p class="empty__title">Nothing archived</p>
        <p class="empty__text">Pausing a habit? Archive it from its card. It leaves Today but keeps its full history, ready to restore.</p>
      </div>`;
      return;
    }
    els.archivedList.innerHTML = `<ul class="archived-list">${archived.map((h) => {
      const { best } = streaks(h, todayKey());
      return `<li class="archived-row" style="--c: var(--c-${h.color})">
        <span class="tr-text">
          <span class="tr-name">${esc(h.name)}</span>
          <span class="tr-meta"><span class="tr-swatch" aria-hidden="true"></span><span>${esc(scheduleText(h.schedule))} · best ${best} ${streakUnit(h, best)} · ${plural(h.checks.length, 'check-in', 'check-ins')}</span></span>
        </span>
        <button type="button" class="btn btn--secondary" data-action="restore" data-id="${h.id}" data-key="restore-${h.id}" aria-label="Restore ${esc(h.name)}">${icon('restore', 'icon icon--sm')}<span>Restore</span></button>
        <button type="button" class="icon-btn icon-btn--danger" data-action="delete" data-id="${h.id}" data-key="delete-${h.id}" aria-label="Delete ${esc(h.name)}" title="Delete">${icon('trash')}</button>
      </li>`;
    }).join('')}</ul>`;
  }

  function renderNotice() {
    els.notice.innerHTML = notice ? `<div class="notice" role="status">
      ${icon('alert')}
      <p class="notice__text"><strong>${esc(notice.title)}</strong>${esc(notice.text)}</p>
      <button type="button" class="icon-btn" data-action="dismiss-notice" aria-label="Dismiss message">${icon('close')}</button>
    </div>` : '';
  }

  function toast(message, kind = 'ok') {
    const t = document.createElement('div');
    t.className = `toast${kind === 'error' ? ' toast--error' : ''}`;
    t.innerHTML = `${icon(kind === 'undo' ? 'undo' : kind === 'error' ? 'alert' : 'check')}<span>${esc(message)}</span>`;
    els.toasts.appendChild(t);
    while (els.toasts.children.length > 3) els.toasts.firstElementChild.remove();
    setTimeout(() => {
      t.classList.add('is-leaving');
      setTimeout(() => t.remove(), 220);
    }, 3200);
  }

  /* ---------- Habit dialog ---------- */
  const dlg = $('#habit-dialog');
  const form = $('#habit-form');
  const f = {
    title: $('#dialog-title'),
    submit: $('#dialog-submit'),
    name: $('#f-name'),
    nameCount: $('#f-name-count'),
    nameError: $('#f-name-error'),
    colors: $('#f-colors'),
    days: $('#f-days'),
    daysError: $('#f-days-error'),
    times: $('#f-times'),
    timesError: $('#f-times-error'),
    panelDays: $('#panel-days'),
    panelWeekly: $('#panel-weekly'),
  };
  let editingId = null;
  let opener = null;
  let openerKey = null;

  f.colors.innerHTML = COLORS.map((c, i) => `<label class="swatch" style="--c: var(--c-${c.id})">
    <input type="radio" name="color" value="${c.id}"${i === 0 ? ' checked' : ''}>
    <span class="swatch__dot">${icon('check')}</span>
    <span class="swatch__name">${c.name}</span>
  </label>`).join('');
  f.days.innerHTML = WD.map((d, i) => `<label class="chip"><input type="checkbox" name="day" value="${i}" aria-label="${WD_LONG[i]}"><span>${d}</span></label>`).join('');

  const scheduleType = () => form.querySelector('input[name="stype"]:checked').value;

  function syncSchedulePanels() {
    const t = scheduleType();
    f.panelDays.hidden = t !== 'days';
    f.panelWeekly.hidden = t !== 'weekly';
  }

  function updateCount() {
    const len = f.name.value.trim().length;
    f.nameCount.textContent = `${len}/${NAME_MAX}`;
    f.nameCount.classList.toggle('is-over', len > NAME_MAX);
  }

  function setError(input, errEl, msg) {
    errEl.hidden = !msg;
    errEl.innerHTML = msg ? `${icon('alert')}<span>${esc(msg)}</span>` : '';
    if (input) {
      if (msg) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
    }
  }

  function clearErrors() {
    setError(f.name, f.nameError, '');
    setError(null, f.daysError, '');
    setError(f.times, f.timesError, '');
  }

  function openHabitDialog(h) {
    editingId = h ? h.id : null;
    opener = document.activeElement;
    openerKey = opener && opener.dataset ? opener.dataset.key || null : null;
    form.reset();
    clearErrors();
    f.title.textContent = h ? 'Edit habit' : 'New habit';
    f.submit.textContent = h ? 'Save changes' : 'Add habit';
    f.name.value = h ? h.name : '';
    form.querySelector(`input[name="color"][value="${h ? h.color : 'sage'}"]`).checked = true;
    const s = h ? h.schedule : { type: 'daily' };
    form.querySelector(`input[name="stype"][value="${s.type}"]`).checked = true;
    const days = s.type === 'days' ? s.days : [0, 1, 2, 3, 4];
    f.days.querySelectorAll('input').forEach((cb) => { cb.checked = days.includes(Number(cb.value)); });
    f.times.value = s.type === 'weekly' ? s.times : 3;
    syncSchedulePanels();
    updateCount();
    dlg.showModal();
    f.name.focus();
    if (h) f.name.select();
  }

  function closeHabitDialog() {
    if (dlg.open) dlg.close();
  }

  dlg.addEventListener('close', () => {
    const target = (openerKey && document.querySelector(`[data-key="${CSS.escape(openerKey)}"]`))
      || (opener && document.contains(opener) ? opener : null)
      || els.addBtn;
    target.focus();
    opener = null;
    openerKey = null;
  });

  dlg.addEventListener('click', (e) => {
    if (e.target === dlg) closeHabitDialog(); // backdrop click
  });

  dlg.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const items = [...dlg.querySelectorAll('button, input, [tabindex]:not([tabindex="-1"])')]
      .filter((el) => !el.disabled && el.offsetParent !== null && !(el.type === 'radio' && !el.checked));
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  form.addEventListener('change', (e) => {
    if (e.target.name === 'stype') { syncSchedulePanels(); setError(null, f.daysError, ''); setError(f.times, f.timesError, ''); }
    if (e.target.name === 'day') setError(null, f.daysError, '');
  });
  f.name.addEventListener('input', () => { updateCount(); setError(f.name, f.nameError, ''); });
  f.times.addEventListener('input', () => setError(f.times, f.timesError, ''));
  form.addEventListener('click', (e) => {
    const step = e.target.closest('[data-step]');
    if (!step) return;
    const n = parseInt(f.times.value, 10);
    const next = Math.min(7, Math.max(1, (Number.isNaN(n) ? 3 : n) + Number(step.dataset.step)));
    f.times.value = next;
    setError(f.times, f.timesError, '');
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearErrors();
    const name = f.name.value.trim();
    const type = scheduleType();
    let firstBad = null;

    let nameMsg = '';
    if (!name) nameMsg = 'Give your habit a name.';
    else if (name.length > NAME_MAX) nameMsg = `Keep the name to ${NAME_MAX} characters or fewer (it’s ${name.length} now).`;
    else {
      const clash = habits.find((h) => h.id !== editingId && normName(h.name) === normName(name));
      if (clash) nameMsg = `You already have a habit called ${quote(clash.name)}${clash.archived ? ' in Archived' : ''}. Try a different name.`;
    }
    if (nameMsg) { setError(f.name, f.nameError, nameMsg); firstBad = firstBad || f.name; }

    let schedule = { type: 'daily' };
    if (type === 'days') {
      const days = [...f.days.querySelectorAll('input:checked')].map((cb) => Number(cb.value));
      if (!days.length) { setError(null, f.daysError, 'Pick at least one day.'); firstBad = firstBad || f.days.querySelector('input'); }
      schedule = { type: 'days', days };
    } else if (type === 'weekly') {
      const raw = f.times.value.trim();
      const n = Number(raw);
      if (!raw || !Number.isInteger(n) || n < 1 || n > 7) { setError(f.times, f.timesError, 'Choose a number from 1 to 7.'); firstBad = firstBad || f.times; }
      schedule = { type: 'weekly', times: n };
    }
    if (firstBad) { firstBad.focus(); return; }

    const color = form.querySelector('input[name="color"]:checked').value;
    if (editingId) {
      const h = findHabit(editingId);
      if (h) {
        commit(`edit of ${quote(name)}`, () => { Object.assign(h, { name, color, schedule }); });
        toast(`Saved ${quote(name)}`);
      }
    } else {
      const h = { id: uid(), name, color, schedule, archived: false, createdAt: todayKey(), checks: [] };
      commit(`adding ${quote(name)}`, () => { habits.push(h); });
      openerKey = `row-${h.id}`;
      toast(`Added ${quote(name)}`);
    }
    closeHabitDialog();
  });

  /* ---------- Import / export ---------- */
  function exportData() {
    const data = {
      app: 'steady-habit-tracker',
      version: 1,
      exportedAt: new Date().toISOString(),
      habits: habits.map(({ id, ...rest }) => rest),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `steady-habits-${todayKey()}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Exported ${plural(habits.length, 'habit', 'habits')}`);
  }

  function showImportError(msg) {
    setError(null, els.importError, msg);
  }

  async function importFile(file) {
    showImportError('');
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) return showImportError('That file is too large to be a Steady backup (over 5 MB). Nothing was changed.');
    let text;
    try { text = await file.text(); } catch (e) { return showImportError('That file couldn’t be read. Nothing was changed.'); }
    let data;
    try { data = JSON.parse(text); } catch (e) { return showImportError(`${quote(file.name)} isn’t valid JSON. Nothing was changed.`); }
    const res = validateData(data);
    if (res.error) return showImportError(`Couldn’t import ${quote(file.name)}: ${res.error} Nothing was changed.`);
    if (!res.habits.length) return showImportError(`${quote(file.name)} has no habits in it. Nothing was changed.`);

    let added = 0;
    let merged = 0;
    commit('import', () => {
      for (const inc of res.habits) {
        const existing = habits.find((h) => normName(h.name) === normName(inc.name));
        if (existing) {
          existing.checks = [...new Set([...existing.checks, ...inc.checks])].sort();
          merged++;
        } else {
          habits.push(inc);
          added++;
        }
      }
    });
    const parts = [];
    if (added) parts.push(`${added} added`);
    if (merged) parts.push(`${merged} merged`);
    toast(`Imported ${plural(res.habits.length, 'habit', 'habits')} (${parts.join(', ')})`);
  }

  els.importFile.addEventListener('change', () => {
    const file = els.importFile.files[0];
    els.importFile.value = '';
    importFile(file);
  });

  /* ---------- Events ---------- */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn || btn.disabled) return;
    const { action, id } = btn.dataset;
    const h = id ? findHabit(id) : null;
    switch (action) {
      case 'add': openHabitDialog(null); break;
      case 'undo': undo(); break;
      case 'close-dialog': closeHabitDialog(); break;
      case 'export': exportData(); break;
      case 'import': els.importFile.click(); break;
      case 'dismiss-notice': notice = null; renderNotice(); els.addBtn.focus(); break;
      case 'toggle-today': if (h) toggleCheck(h.id, todayKey()); break;
      case 'toggle-day':
        if (h) { heatFocus.set(h.id, btn.dataset.date); toggleCheck(h.id, btn.dataset.date); }
        break;
      case 'edit': if (h) openHabitDialog(h); break;
      case 'archive':
        if (h) {
          const card = btn.closest('.habit-card');
          const sibling = card && (card.nextElementSibling || card.previousElementSibling);
          const nextKey = sibling ? sibling.querySelector('[data-action="archive"]').dataset.key : `restore-${h.id}`;
          commit(`archive of ${quote(h.name)}`, () => { h.archived = true; });
          toast(`Archived ${quote(h.name)}`);
          document.querySelector(`[data-key="${CSS.escape(nextKey)}"]`)?.focus();
        }
        break;
      case 'restore':
        if (h) {
          commit(`restore of ${quote(h.name)}`, () => { h.archived = false; });
          toast(`Restored ${quote(h.name)}`);
          $(`[data-key="edit-${h.id}"]`)?.focus();
        }
        break;
      case 'delete':
        if (h) {
          // eslint-disable-next-line no-alert
          if (!window.confirm(`Delete ${quote(h.name)} and all of its history?`)) return;
          commit(`deletion of ${quote(h.name)}`, () => { habits = habits.filter((x) => x.id !== h.id); });
          toast(`Deleted ${quote(h.name)}`);
          els.addBtn.focus();
        }
        break;
      default: break;
    }
  });

  document.addEventListener('focusin', (e) => {
    const cell = e.target.closest && e.target.closest('.cell[data-date]');
    if (!cell) return;
    const grid = cell.parentElement;
    grid.querySelectorAll('.cell[tabindex="0"]').forEach((c) => { if (c !== cell) c.tabIndex = -1; });
    cell.tabIndex = 0;
    heatFocus.set(cell.dataset.id, cell.dataset.date);
  });

  const isTyping = (el) => el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable);
  const calendarLayout = window.matchMedia('(max-width: 640px)');

  document.addEventListener('keydown', (e) => {
    const t = e.target;
    const mod = e.ctrlKey || e.metaKey;

    if (dlg.open) return; // the dialog manages its own keys (Esc, Tab trap)

    if (mod && !e.altKey && !e.shiftKey && e.key.toLowerCase() === 'z' && !isTyping(t)) {
      e.preventDefault();
      undo();
      return;
    }
    if (!mod && !e.altKey && (e.key === 'n' || e.key === 'N') && !isTyping(t)) {
      e.preventDefault();
      openHabitDialog(null);
      return;
    }
    if (mod || e.altKey) return;

    // Today rows: arrows move, Space toggles (native button behaviour).
    if (t.classList && t.classList.contains('today-row')) {
      const rows = [...document.querySelectorAll('.today-row')];
      const i = rows.indexOf(t);
      let next = null;
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') next = rows[Math.min(rows.length - 1, i + 1)];
      else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') next = rows[Math.max(0, i - 1)];
      else if (e.key === 'Home') next = rows[0];
      else if (e.key === 'End') next = rows[rows.length - 1];
      if (next) { e.preventDefault(); next.focus(); }
      return;
    }

    // Heatmap cells: roving focus in a 2-D grid.
    if (t.classList && t.classList.contains('cell') && t.dataset.date) {
      const cells = [...t.parentElement.querySelectorAll('.cell')];
      const i = cells.indexOf(t);
      const cal = calendarLayout.matches; // weeks are rows on small screens
      const moves = cal
        ? { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 7, ArrowUp: -7 }
        : { ArrowRight: 7, ArrowLeft: -7, ArrowDown: 1, ArrowUp: -1 };
      let j = null;
      if (e.key in moves) j = i + moves[e.key];
      else if (e.key === 'Home') j = 0;
      else if (e.key === 'End') j = cells.findIndex((c) => c.classList.contains('cell--today'));
      if (j === null) return;
      e.preventDefault();
      if (j < 0 || j >= cells.length || cells[j].disabled) return;
      cells[j].focus();
    }
  });

  /* ---------- Midnight rollover ---------- */
  function tick() {
    if (todayKey() !== currentDay) render();
  }
  setInterval(tick, 20000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) tick(); });
  window.addEventListener('focus', tick);

  // Keep tabs in sync if the data changes in another window.
  window.addEventListener('storage', (e) => {
    if (e.key !== STORAGE_KEY) return;
    load();
    render();
  });

  /* ---------- Boot ---------- */
  const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  $('#undo-kbd').textContent = isMac ? '⌘Z' : 'Ctrl Z';
  load();
  render();
})();
