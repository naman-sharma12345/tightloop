/* Wayfare — multi-day trip planner. Plain JS, no dependencies. */
(function () {
  'use strict';

  const STORAGE_KEY = 'wayfare.tripPlanner';
  const MAX_HISTORY = 20;
  const MAX_DAYS = 30;
  const MAX_TRAVELLERS = 8;
  const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK'];

  const ICONS = {
    food: '<path d="M4 3v7a3 3 0 0 0 3 3v8"/><path d="M10 3v7a3 3 0 0 1-3 3"/><path d="M7 3v6"/><path d="M19 21V3c-2.2 0-4 2.5-4 6.5 0 2.5 1 3.5 2 3.5h2"/>',
    sight: '<path d="M14.5 4h-5L7.5 7H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2.5z"/><circle cx="12" cy="13" r="3.5"/>',
    transport: '<rect x="5" y="3" width="14" height="14" rx="3"/><path d="M5 11h14"/><path d="M9 7h6"/><path d="m8 21 1.5-4M16 21l-1.5-4"/><path d="M8.5 14h.01M15.5 14h.01"/>',
    stay: '<path d="M3 5v15"/><path d="M3 9h15a3 3 0 0 1 3 3v8"/><path d="M3 16h18"/><path d="M7 9v7"/>',
    other: '<path d="m12 3 2.6 5.6 6.1.7-4.5 4.2 1.2 6.1L12 16.6l-5.4 3 1.2-6.1-4.5-4.2 6.1-.7z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pin: '<path d="M12 21s-7-6.1-7-11.5a7 7 0 0 1 14 0C19 14.9 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    move: '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
    alert: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>',
    calendar: '<rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/>',
    download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>',
    wallet: '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3"/><path d="M3 7h16a2 2 0 0 1 2 2v3h-4a2 2 0 0 0 0 4h4"/>',
    inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'
  };

  const CATEGORIES = [
    { id: 'food', label: 'Food' },
    { id: 'sight', label: 'Sight' },
    { id: 'transport', label: 'Transport' },
    { id: 'stay', label: 'Stay' },
    { id: 'other', label: 'Other' }
  ];
  const CAT = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));
  const AVATAR_TINTS = ['#F4DCC4', '#D9E8E3', '#E2DBF3', '#D7E4F5', '#F3D8DC', '#E8E2C8', '#D3E9DA', '#E9DCCF'];

  /* ---------- Small helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const icon = (name, cls = '') => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[name] || ''}</svg>`;
  const uid = () => Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-5);
  const pad = n => String(n).padStart(2, '0');
  const plural = (n, one, many = one + 's') => `${n} ${n === 1 ? one : many}`;

  /* ---------- Dates & times ---------- */
  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

  function parseDate(s) {
    if (typeof s !== 'string' || !DATE_RE.test(s)) return null;
    const [y, m, d] = s.split('-').map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d));
    return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d ? dt : null;
  }
  const isoOf = dt => dt.toISOString().slice(0, 10);
  function addDays(s, n) { const d = parseDate(s); d.setUTCDate(d.getUTCDate() + n); return isoOf(d); }
  const diffDays = (a, b) => Math.round((parseDate(b) - parseDate(a)) / 86400000);
  const tripDays = t => Array.from({ length: diffDays(t.start, t.end) + 1 }, (_, i) => addDays(t.start, i));
  function todayISO() { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }

  const dfDay = new Intl.DateTimeFormat(undefined, { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' });
  const dfDayYear = new Intl.DateTimeFormat(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  const fmtDay = s => dfDay.format(parseDate(s));
  const fmtDayYear = s => dfDayYear.format(parseDate(s));

  const toMin = t => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };
  const clock = m => `${pad(Math.floor(m / 60) % 24)}:${pad(m % 60)}`;
  const endMin = a => toMin(a.start) + a.duration;
  const timeRange = a => `${a.start}-${clock(endMin(a))}${endMin(a) >= 1440 ? ' (+1 day)' : ''}`;
  function durLabel(m) {
    const h = Math.floor(m / 60), mm = m % 60;
    return [h ? `${h} h` : '', mm ? `${mm} min` : ''].filter(Boolean).join(' ');
  }

  /* ---------- Money ---------- */
  const moneyFmts = {};
  function money(cents, cur) {
    if (!moneyFmts[cur]) {
      try {
        moneyFmts[cur] = new Intl.NumberFormat(undefined, { style: 'currency', currency: cur, minimumFractionDigits: 2, maximumFractionDigits: 2 });
      } catch (e) {
        moneyFmts[cur] = { format: v => `${v.toFixed(2)} ${cur}` };
      }
    }
    return moneyFmts[cur].format(cents / 100);
  }
  function parseCost(str) {
    const s = String(str).trim().replace(/\s/g, '').replace(',', '.');
    if (!s) return { value: null };
    if (!/^\d{1,7}(\.\d{1,2})?$/.test(s)) return { error: 'Enter an amount like 12 or 12.50 (up to 2 decimals).' };
    const [i, f = ''] = s.split('.');
    return { value: Number(i) * 100 + Number((f + '00').slice(0, 2)) };
  }
  const centsToInput = c => (c == null ? '' : (c / 100).toFixed(2));

  /* ---------- State ---------- */
  let state = { trips: [], currentId: null };
  let past = [];
  let future = [];
  const ui = { query: '', storageNotice: '', storageOk: true };

  const cur = () => state.trips.find(t => t.id === state.currentId) || null;
  const dayIndex = (trip, date) => tripDays(trip).indexOf(date);
  const dayName = (trip, date) => (date == null ? 'Unscheduled' : `Day ${dayIndex(trip, date) + 1} · ${fmtDay(date)}`);

  /* Validates and normalises a trip object (used for storage and imports). Throws a readable message. */
  function normalizeTrip(t) {
    const fail = m => { throw new Error(m); };
    if (!t || typeof t !== 'object' || Array.isArray(t)) fail('it does not contain a trip.');
    const name = typeof t.name === 'string' ? t.name.trim() : '';
    if (!name) fail('the trip has no name.');
    if (!parseDate(t.start) || !parseDate(t.end)) fail('the trip dates are missing or not real dates.');
    const len = diffDays(t.start, t.end) + 1;
    if (len < 1) fail('the end date is before the start date.');
    if (len > MAX_DAYS) fail(`the trip is longer than ${MAX_DAYS} days.`);
    if (!Array.isArray(t.travellers) || t.travellers.length < 1 || t.travellers.length > MAX_TRAVELLERS) fail('a trip needs 1 to 8 travellers.');
    const seenNames = new Set(), seenIds = new Set();
    const travellers = t.travellers.map(p => {
      const nm = typeof p === 'string' ? p.trim() : (p && typeof p.name === 'string' ? p.name.trim() : '');
      if (!nm) fail('one of the travellers has no name.');
      if (seenNames.has(nm.toLowerCase())) fail(`the traveller “${nm}” is listed twice.`);
      seenNames.add(nm.toLowerCase());
      let id = p && typeof p.id === 'string' && p.id ? p.id : uid();
      if (seenIds.has(id)) id = uid();
      seenIds.add(id);
      return { id, name: nm.slice(0, 40) };
    });
    const tids = travellers.map(p => p.id);
    if (t.activities != null && !Array.isArray(t.activities)) fail('the activity list is not a list.');
    const days = new Set(tripDays(t));
    const actIds = new Set();
    const activities = (t.activities || []).map((a, i) => {
      if (!a || typeof a !== 'object') fail(`activity ${i + 1} is not valid.`);
      const title = typeof a.title === 'string' ? a.title.trim() : '';
      if (!title) fail(`activity ${i + 1} has no title.`);
      if (typeof a.start !== 'string' || !TIME_RE.test(a.start)) fail(`“${title}” has an invalid start time.`);
      const d = Number(a.duration);
      if (!Number.isInteger(d) || d < 15 || d > 720 || d % 15) fail(`“${title}” has an invalid duration.`);
      if (!CAT[a.category]) fail(`“${title}” has an unknown category.`);
      const cost = a.cost == null ? null : Number(a.cost);
      if (cost != null && (!Number.isInteger(cost) || cost < 0 || cost > 999999999)) fail(`“${title}” has an invalid cost.`);
      if (a.date != null && !parseDate(a.date)) fail(`“${title}” has an invalid date.`);
      let id = typeof a.id === 'string' && a.id ? a.id : uid();
      if (actIds.has(id)) id = uid();
      actIds.add(id);
      let split = Array.isArray(a.split) ? tids.filter(x => a.split.includes(x)) : [];
      if (!split.length) split = tids.slice();
      return {
        id, title: title.slice(0, 100),
        date: a.date && days.has(a.date) ? a.date : null,
        start: a.start, duration: d,
        place: typeof a.place === 'string' ? a.place.slice(0, 120) : '',
        category: a.category, cost,
        notes: typeof a.notes === 'string' ? a.notes.slice(0, 4000) : '',
        paidBy: tids.includes(a.paidBy) ? a.paidBy : tids[0],
        split
      };
    });
    return {
      id: typeof t.id === 'string' && t.id ? t.id : uid(),
      name: name.slice(0, 80), start: t.start, end: t.end,
      currency: CURRENCIES.includes(t.currency) ? t.currency : 'EUR',
      travellers, activities
    };
  }

  function load() {
    let raw = null;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      ui.storageOk = false;
      ui.storageNotice = 'This browser is blocking local storage, so trips will only last until you close the page.';
      return;
    }
    if (raw == null) return;
    try {
      const data = JSON.parse(raw);
      if (!data || typeof data !== 'object' || !Array.isArray(data.trips)) throw new Error('bad shape');
      let skipped = 0;
      const trips = [];
      for (const t of data.trips) {
        try { trips.push(normalizeTrip(t)); } catch (e) { skipped++; }
      }
      state.trips = trips;
      state.currentId = trips.some(t => t.id === data.currentId) ? data.currentId : (trips[0] ? trips[0].id : null);
      if (skipped) ui.storageNotice = `${plural(skipped, 'saved trip')} could not be read and ${skipped === 1 ? 'was' : 'were'} left out. Everything else loaded normally.`;
    } catch (e) {
      state = { trips: [], currentId: null };
      ui.storageNotice = 'Your saved trips could not be read because the stored data is damaged, so the planner started empty. Create a new trip or import a trip file to continue.';
    }
  }

  function save() {
    if (!ui.storageOk) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, trips: state.trips, currentId: state.currentId }));
    } catch (e) {
      toast('Your change could not be saved to this browser’s storage (it may be full).', { kind: 'error' });
    }
  }

  /* ---------- History ---------- */
  const snapshot = () => JSON.stringify(state);

  function commit(label, fn) {
    const before = snapshot();
    const result = fn();
    if (result === false) return false;
    past.push({ snap: before, label });
    if (past.length > MAX_HISTORY) past.shift();
    future = [];
    save();
    render();
    return result;
  }
  function undo() {
    if (!past.length) return;
    closeMoveMenu();
    const entry = past.pop();
    future.push({ snap: snapshot(), label: entry.label });
    state = JSON.parse(entry.snap);
    save();
    render();
    toast(`Undid: ${entry.label}`);
  }
  function redo() {
    if (!future.length) return;
    closeMoveMenu();
    const entry = future.pop();
    past.push({ snap: snapshot(), label: entry.label });
    state = JSON.parse(entry.snap);
    save();
    render();
    toast(`Redid: ${entry.label}`);
  }

  /* ---------- Domain ---------- */
  const sortActs = list => list.slice().sort((a, b) => toMin(a.start) - toMin(b.start) || a.duration - b.duration || a.title.localeCompare(b.title));

  function conflictsFor(sorted) {
    const map = new Map(sorted.map(a => [a.id, []]));
    for (let i = 0; i < sorted.length; i++) {
      for (let j = i + 1; j < sorted.length; j++) {
        const a = sorted[i], b = sorted[j];
        if (toMin(b.start) >= endMin(a)) continue;
        if (toMin(a.start) < endMin(b)) { map.get(a.id).push(b); map.get(b.id).push(a); }
      }
    }
    return map;
  }

  const matches = (a, q) => !q || a.title.toLowerCase().includes(q) || (a.place || '').toLowerCase().includes(q);

  function highlight(text, q) {
    if (!q) return esc(text);
    const lower = text.toLowerCase();
    let out = '', i = 0, idx;
    while ((idx = lower.indexOf(q, i)) !== -1) {
      out += esc(text.slice(i, idx)) + '<mark>' + esc(text.slice(idx, idx + q.length)) + '</mark>';
      i = idx + q.length;
    }
    return out + esc(text.slice(i));
  }

  function computeBudget(trip) {
    const tids = trip.travellers.map(p => p.id);
    const byCat = Object.fromEntries(CATEGORIES.map(c => [c.id, 0]));
    const byDay = new Map(tripDays(trip).map(d => [d, 0]));
    let unscheduled = 0, total = 0, costed = 0;
    const paid = Object.fromEntries(tids.map(id => [id, 0]));
    const share = Object.fromEntries(tids.map(id => [id, 0]));
    for (const a of trip.activities) {
      if (!a.cost) continue;
      costed++;
      total += a.cost;
      byCat[a.category] += a.cost;
      if (a.date && byDay.has(a.date)) byDay.set(a.date, byDay.get(a.date) + a.cost); else unscheduled += a.cost;
      const payer = tids.includes(a.paidBy) ? a.paidBy : tids[0];
      paid[payer] += a.cost;
      let split = tids.filter(id => a.split.includes(id));
      if (!split.length) split = tids;
      // Whole cents only; leftover cents go to successive people, rotating per activity so no one always pays them.
      const base = Math.floor(a.cost / split.length);
      const rem = a.cost - base * split.length;
      split.forEach((id, k) => { share[id] += base + (((k - costed) % split.length + split.length) % split.length < rem ? 1 : 0); });
    }
    const balances = tids.map(id => ({ id, amt: paid[id] - share[id] }));
    return { total, costed, byCat, byDay, unscheduled, paid, share, balances, transfers: settleTransfers(balances) };
  }

  /* Fewest transfers: maximise the number of zero-sum groups (exact for ≤ 8 people), then settle each group greedily. */
  function settleTransfers(balances) {
    const b = balances.filter(x => x.amt !== 0);
    const n = b.length;
    if (!n) return [];
    const N = 1 << n;
    const sum = new Array(N).fill(0), dp = new Array(N).fill(0);
    for (let m = 1; m < N; m++) { const i = 31 - Math.clz32(m & -m); sum[m] = sum[m & (m - 1)] + b[i].amt; }
    for (let m = 1; m < N; m++) {
      let best = 0;
      for (let i = 0; i < n; i++) if (m & (1 << i)) best = Math.max(best, dp[m ^ (1 << i)]);
      dp[m] = best + (sum[m] === 0 ? 1 : 0);
    }
    const groups = [];
    let m = N - 1, last = N - 1;
    while (m) {
      const target = dp[m] - (sum[m] === 0 ? 1 : 0);
      let next = 0;
      for (let i = 0; i < n; i++) if ((m & (1 << i)) && dp[m ^ (1 << i)] === target) { next = m ^ (1 << i); break; }
      m = next;
      if (sum[m] === 0) { groups.push(last ^ m); last = m; }
    }
    const transfers = [];
    for (const g of groups) {
      const members = b.filter((_, i) => g & (1 << i)).map(x => ({ ...x }));
      const debtors = members.filter(x => x.amt < 0).sort((x, y) => x.amt - y.amt);
      const creditors = members.filter(x => x.amt > 0).sort((x, y) => y.amt - x.amt);
      let i = 0, j = 0;
      while (i < debtors.length && j < creditors.length) {
        const amt = Math.min(-debtors[i].amt, creditors[j].amt);
        transfers.push({ from: debtors[i].id, to: creditors[j].id, amt });
        debtors[i].amt += amt; creditors[j].amt -= amt;
        if (debtors[i].amt === 0) i++;
        if (creditors[j].amt === 0) j++;
      }
    }
    return transfers.sort((x, y) => y.amt - x.amt);
  }

  /* ---------- Rendering ---------- */
  function render() {
    const active = document.activeElement;
    const fk = active && active.dataset ? active.dataset.fk : null;

    if (state.currentId && !cur()) state.currentId = state.trips[0] ? state.trips[0].id : null;
    const trip = cur();
    renderTopbar(trip);
    renderNotices();
    $('#emptyApp').hidden = !!trip;
    $('#tripView').hidden = !trip;
    if (trip) {
      renderHead(trip);
      renderItinerary(trip);
      renderBudget(trip);
    }
    if (fk && (!active.isConnected || active !== document.activeElement)) {
      const el = document.querySelector(`[data-fk="${CSS.escape(fk)}"]`);
      if (el) el.focus();
    }
  }

  function renderTopbar(trip) {
    const sel = $('#tripSelect');
    $('#tripSwitch').hidden = !state.trips.length;
    sel.innerHTML = state.trips.map(t => `<option value="${esc(t.id)}"${trip && t.id === trip.id ? ' selected' : ''}>${esc(t.name)}</option>`).join('');
    const u = $('#undoBtn'), r = $('#redoBtn');
    u.disabled = !past.length;
    r.disabled = !future.length;
    const mod = /Mac|iPhone|iPad/.test(navigator.platform || '') ? '⌘' : 'Ctrl+';
    u.title = past.length ? `Undo: ${past[past.length - 1].label} (${mod}Z)` : 'Nothing to undo';
    r.title = future.length ? `Redo: ${future[future.length - 1].label} (Shift+${mod}Z)` : 'Nothing to redo';
    u.setAttribute('aria-label', past.length ? `Undo: ${past[past.length - 1].label}` : 'Undo');
    r.setAttribute('aria-label', future.length ? `Redo: ${future[future.length - 1].label}` : 'Redo');
  }

  function renderNotices() {
    const n = $('#storageNotice');
    if (ui.storageNotice) {
      n.innerHTML = `${icon('info')}<p>${esc(ui.storageNotice)}</p><button type="button" class="icon-btn" data-action="dismiss-notice" aria-label="Dismiss message">${icon('x')}</button>`;
      n.hidden = false;
    } else n.hidden = true;
  }

  function showImportError(msg) {
    const n = $('#importError');
    if (!msg) { n.hidden = true; n.innerHTML = ''; return; }
    n.innerHTML = `${icon('alert')}<p><strong>Import failed.</strong> ${esc(msg)} Nothing was changed.</p><button type="button" class="icon-btn" data-action="dismiss-import" aria-label="Dismiss import error">${icon('x')}</button>`;
    n.hidden = false;
  }

  function avatar(p, i) {
    const initials = p.name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
    return `<span class="avatar" style="background:${AVATAR_TINTS[i % AVATAR_TINTS.length]}" aria-hidden="true">${esc(initials)}</span>`;
  }

  function renderHead(trip) {
    const n = tripDays(trip).length;
    $('#tripHead').innerHTML = `
      <div class="trip-meta">
        <p class="eyebrow">${icon('calendar')}<span>${esc(fmtDay(trip.start))} – ${esc(fmtDayYear(trip.end))}</span><span aria-hidden="true">·</span><span>${plural(n, 'day')}</span></p>
        <h1 class="trip-title" id="tripTitle">${esc(trip.name)}</h1>
        <ul class="people" aria-label="Travellers">
          ${trip.travellers.map((p, i) => `<li class="person">${avatar(p, i)}${esc(p.name)}</li>`).join('')}
        </ul>
      </div>
      <div class="trip-actions">
        <button type="button" class="btn" data-action="edit-trip" data-fk="edit-trip">${icon('edit')}Edit trip</button>
        <button type="button" class="btn" data-action="export-ics" data-fk="export-ics">${icon('calendar')}Export .ics</button>
        <button type="button" class="btn" data-action="export-json" data-fk="export-json">${icon('download')}Export JSON</button>
        <button type="button" class="btn danger-ghost" data-action="delete-trip" data-fk="delete-trip">${icon('trash')}Delete trip</button>
      </div>`;
  }

  function cardHTML(a, trip, conflicts, q) {
    const c = CAT[a.category];
    const isMatch = q && matches(a, q);
    const cls = ['card', `cat-${a.category}`, conflicts && conflicts.length ? 'has-conflict' : '', q ? (isMatch ? 'is-match' : 'is-dim') : ''].join(' ');
    const conflictHTML = conflicts && conflicts.length
      ? `<div class="conflict" id="cf-${esc(a.id)}">${icon('alert')}<div><strong>Time conflict</strong>${conflicts.map(b => `<span>overlaps ${esc(b.title)} ${esc(b.start)}-${esc(clock(endMin(b)))}</span>`).join('')}</div></div>`
      : '';
    return `<li class="${cls}" draggable="true" data-id="${esc(a.id)}">
      <div class="card-row">
        <span class="cat-chip">${icon(a.category)}${c.label}</span>
        <span class="card-time">${icon('clock')}<span>${esc(timeRange(a))}</span></span>
      </div>
      <h4 class="card-title"><button type="button" class="card-open" data-action="open-activity" data-id="${esc(a.id)}" data-fk="open-${esc(a.id)}"${conflicts && conflicts.length ? ' aria-describedby="cf-' + esc(a.id) + '"' : ''}>${highlight(a.title, q)}</button></h4>
      ${a.place ? `<p class="card-place">${icon('pin')}<span><span class="sr-only">Place: </span>${highlight(a.place, q)}</span></p>` : ''}
      <div class="card-foot">
        <span class="card-meta">${esc(durLabel(a.duration))}${a.cost != null ? ` · <span class="cost">${esc(money(a.cost, trip.currency))}</span>` : ''}</span>
        <button type="button" class="move-btn" data-action="move-menu" data-id="${esc(a.id)}" data-fk="move-${esc(a.id)}" aria-haspopup="menu" aria-expanded="false">${icon('move')}<span>Move to…</span><span class="sr-only"> (${esc(a.title)})</span></button>
      </div>
      ${conflictHTML}
    </li>`;
  }

  function renderItinerary(trip) {
    const q = ui.query.trim().toLowerCase();
    const days = tripDays(trip);
    let matchCount = 0;
    const matchDays = new Set();

    // Unscheduled tray
    const un = sortActs(trip.activities.filter(a => a.date == null));
    un.forEach(a => { if (q && matches(a, q)) { matchCount++; matchDays.add('un'); } });
    const tray = $('#tray');
    tray.innerHTML = `<section class="tray${un.length ? ' has-items' : ''}" data-drop="unscheduled" aria-labelledby="trayTitle">
      <div class="tray-head">
        <h3 id="trayTitle">${icon('inbox')}Unscheduled <span class="count" aria-label="${plural(un.length, 'activity', 'activities')}">${un.length}</span></h3>
        <p class="hint">${un.length ? 'Drag these onto a day, or use “Move to…” to schedule them.' : 'Nothing waiting here. Activities from days you remove land here, so nothing gets lost.'}</p>
      </div>
      ${un.length ? `<ol class="tray-list">${un.map(a => cardHTML(a, trip, null, q)).join('')}</ol>` : ''}
    </section>`;

    // Day columns
    $('#board').innerHTML = days.map((d, i) => {
      const list = sortActs(trip.activities.filter(a => a.date === d));
      const conf = conflictsFor(list);
      const nConf = list.filter(a => conf.get(a.id).length).length;
      const dayMatches = q ? list.filter(a => matches(a, q)).length : 0;
      if (dayMatches) { matchCount += dayMatches; matchDays.add(d); }
      const collapsed = q && !dayMatches;
      const cost = list.reduce((s, a) => s + (a.cost || 0), 0);
      const sub = [plural(list.length, 'activity', 'activities')];
      if (cost) sub.push(money(cost, trip.currency));
      const headId = `day-${i}`;
      return `<section class="day${collapsed ? ' collapsed' : ''}" data-drop="${d}" aria-labelledby="${headId}">
        <header class="day-head">
          <h3 id="${headId}"><span class="day-num">Day ${i + 1}</span><span class="day-date">${esc(fmtDay(d))}</span></h3>
          <p class="day-sub"><span>${esc(sub.join(' · '))}</span>${nConf && !collapsed ? `<span class="badge-warn">${icon('alert')}${plural(nConf, 'conflict')}</span>` : ''}</p>
        </header>
        ${collapsed
          ? `<p class="collapsed-note">No matches on this day</p>`
          : `${list.length
              ? `<ol class="day-list">${list.map(a => cardHTML(a, trip, conf.get(a.id), q)).join('')}</ol>`
              : `<div class="day-empty">${icon('sun')}<strong>A free day</strong>Add an activity, or drag one here.</div><div class="day-list" aria-hidden="true"></div>`}
            <button type="button" class="btn add-btn" data-action="add-activity" data-date="${d}" data-fk="add-${d}">${icon('plus')}Add activity<span class="sr-only"> to Day ${i + 1}</span></button>`}
      </section>`;
    }).join('');

    const status = $('#searchStatus');
    if (!q) status.textContent = '';
    else if (!matchCount) status.innerHTML = `No activities match “<strong>${esc(ui.query.trim())}</strong>”. Try another word, or clear the search.`;
    else {
      const dayCount = [...matchDays].filter(d => d !== 'un').length;
      status.innerHTML = `<strong>${plural(matchCount, 'match', 'matches')}</strong> across ${plural(dayCount, 'day')}${matchDays.has('un') ? ' and Unscheduled' : ''}. Days without matches are collapsed.`;
    }
  }

  function renderBudget(trip) {
    const B = computeBudget(trip);
    const cur$ = c => esc(money(c, trip.currency));
    const el = $('#budget');
    const head = `<div class="budget-head">${icon('wallet')}<h2 class="section-title" id="budgetTitle">Budget</h2></div>`;
    if (!B.costed) {
      el.innerHTML = `${head}<div class="panel-empty">${icon('wallet')}<strong>No costs yet</strong>Open an activity and enter a cost. Totals per category and day, and who owes whom, will appear here.</div>`;
      return;
    }
    const maxCat = Math.max(...Object.values(B.byCat), 1);
    const dayVals = [...B.byDay.values(), B.unscheduled];
    const maxDay = Math.max(...dayVals, 1);
    const pct = (v, max) => `${Math.round((v / max) * 1000) / 10}%`;
    const days = tripDays(trip);
    const nameOf = id => (trip.travellers.find(p => p.id === id) || { name: '?' }).name;
    const perPerson = trip.travellers.length > 1 ? `<span class="total-sub">${cur$(Math.round(B.total / trip.travellers.length))} per person on average</span>` : '';

    const catRows = CATEGORIES.map(c => `
      <li class="bar-row cat-${c.id}${B.byCat[c.id] ? '' : ' zero'}">
        <span class="bar-label">${icon(c.id)}${c.label}</span>
        <span class="bar-value">${cur$(B.byCat[c.id])}</span>
        <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${pct(B.byCat[c.id], maxCat)}"></span></span>
      </li>`).join('');

    const dayRows = days.map((d, i) => `
      <li class="bar-row${B.byDay.get(d) ? '' : ' zero'}">
        <span class="bar-label">Day ${i + 1} <small>${esc(fmtDay(d))}</small></span>
        <span class="bar-value">${cur$(B.byDay.get(d))}</span>
        <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${pct(B.byDay.get(d), maxDay)}"></span></span>
      </li>`).join('') + (B.unscheduled ? `
      <li class="bar-row">
        <span class="bar-label">Unscheduled</span>
        <span class="bar-value">${cur$(B.unscheduled)}</span>
        <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${pct(B.unscheduled, maxDay)}; --c: var(--warn)"></span></span>
      </li>` : '');

    const rows = trip.travellers.map((p, i) => {
      const bal = B.paid[p.id] - B.share[p.id];
      const balHTML = bal > 0 ? `<span class="bal pos">+${cur$(bal)}<small>gets back</small></span>`
        : bal < 0 ? `<span class="bal neg">−${cur$(-bal)}<small>owes</small></span>`
        : `<span class="bal">${cur$(0)}<small>settled</small></span>`;
      return `<tr><th scope="row">${esc(p.name)}</th><td>${cur$(B.paid[p.id])}</td><td>${cur$(B.share[p.id])}</td><td>${balHTML}</td></tr>`;
    }).join('');

    const transfers = trip.travellers.length < 2
      ? `<p class="settled">${icon('check')}Only one traveller, so there is nothing to settle.</p>`
      : B.transfers.length
        ? `<ol class="transfers">${B.transfers.map(t => `<li class="transfer"><span class="who">${esc(nameOf(t.from))}</span><span class="verb">pays</span>${icon('arrow')}<span class="who">${esc(nameOf(t.to))}</span><span class="amt">${cur$(t.amt)}</span></li>`).join('')}</ol>`
        : `<p class="settled">${icon('check')}Everyone is square — no transfers needed.</p>`;

    el.innerHTML = `${head}
      <div class="total"><span class="total-label">Total trip cost</span><strong class="total-value">${cur$(B.total)}</strong>${perPerson}</div>
      <h3>By category</h3><ul class="bars">${catRows}</ul>
      <h3>By day</h3><ul class="bars">${dayRows}</ul>
      <h3>Settle up</h3>
      <table class="settle-table">
        <caption class="sr-only">What each traveller paid, their share and their balance</caption>
        <thead><tr><th scope="col">Traveller</th><th scope="col">Paid</th><th scope="col">Share</th><th scope="col">Balance</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <h3>${B.transfers.length ? `Transfers (${B.transfers.length})` : 'Transfers'}</h3>
      ${transfers}`;
  }

  /* ---------- Toasts ---------- */
  function toast(msg, opts = {}) {
    const el = document.createElement('div');
    el.className = 'toast' + (opts.kind ? ` toast-${opts.kind}` : '');
    el.innerHTML = `${icon(opts.kind === 'error' ? 'alert' : 'check')}<p>${esc(msg)}</p>`;
    let timer;
    const remove = () => { clearTimeout(timer); el.remove(); };
    if (opts.action) {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'btn'; b.textContent = opts.action.label;
      b.addEventListener('click', () => { remove(); opts.action.run(); });
      el.append(b);
    }
    const x = document.createElement('button');
    x.type = 'button'; x.className = 'icon-btn'; x.setAttribute('aria-label', 'Dismiss notification');
    x.innerHTML = icon('x');
    x.addEventListener('click', remove);
    el.append(x);
    const box = $('#toasts');
    while (box.children.length >= 3) box.firstElementChild.remove();
    box.append(el);
    const arm = () => { clearTimeout(timer); timer = setTimeout(remove, opts.action ? 8000 : 5000); };
    el.addEventListener('mouseenter', () => clearTimeout(timer));
    el.addEventListener('mouseleave', arm);
    el.addEventListener('focusin', () => clearTimeout(timer));
    el.addEventListener('focusout', arm);
    arm();
  }

  /* ---------- Dialog plumbing ---------- */
  function focusables(root) {
    return $$('a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])', root)
      .filter(el => el.offsetParent !== null || el === document.activeElement);
  }

  function setupDialog(dlg) {
    dlg.addEventListener('cancel', e => { e.preventDefault(); closeDialog(dlg); });
    let downOnBackdrop = false;
    dlg.addEventListener('mousedown', e => { downOnBackdrop = e.target === dlg; });
    dlg.addEventListener('click', e => {
      if (e.target === dlg && downOnBackdrop) closeDialog(dlg);
      downOnBackdrop = false;
      if (e.target.closest('[data-close]')) closeDialog(dlg);
    });
    dlg.addEventListener('keydown', e => {
      if (e.key !== 'Tab') return;
      const f = focusables(dlg);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === first || !dlg.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  function openDialog(dlg, opener, initialFocus) {
    closeMoveMenu();
    dlg._returnFk = opener && opener.dataset ? opener.dataset.fk : null;
    dlg._opener = opener || null;
    dlg.showModal();
    (initialFocus || focusables(dlg)[0]).focus();
  }

  function closeDialog(dlg, returnFk) {
    if (!dlg.open) return;
    dlg.close();
    const fk = returnFk !== undefined ? returnFk : dlg._returnFk;
    let target = fk ? document.querySelector(`[data-fk="${CSS.escape(fk)}"]`) : null;
    if (!target && dlg._opener && dlg._opener.isConnected) target = dlg._opener;
    if (!target) target = $('#main');
    target.focus();
  }

  function setError(id, msg) {
    const err = $(`#${id}-err`);
    const input = $(`#${id}`);
    if (msg) { err.textContent = msg; err.hidden = false; } else { err.textContent = ''; err.hidden = true; }
    if (input) input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }

  /* ---------- Trip dialog ---------- */
  let tripDraft = null;

  function openTripDialog(trip, opener) {
    const isNew = !trip;
    const today = todayISO();
    tripDraft = {
      id: trip ? trip.id : null,
      travellers: trip ? trip.travellers.map(p => ({ ...p })) : [{ id: uid(), name: '' }]
    };
    $('#tripDialogTitle').textContent = isNew ? 'New trip' : 'Edit trip';
    $('#tripSubmit').textContent = isNew ? 'Create trip' : 'Save changes';
    $('#tripName').value = trip ? trip.name : '';
    $('#tripStart').value = trip ? trip.start : today;
    $('#tripEnd').value = trip ? trip.end : addDays(today, 2);
    $('#tripCurrency').innerHTML = CURRENCIES.map(c => `<option value="${c}"${(trip ? trip.currency : 'EUR') === c ? ' selected' : ''}>${c}</option>`).join('');
    ['tripName', 'tripStart', 'tripEnd'].forEach(id => setError(id, ''));
    $('#travellers-err').hidden = true;
    renderTravellerInputs();
    updateTripLength();
    openDialog($('#tripDialog'), opener, $('#tripName'));
  }

  function renderTravellerInputs(focusIndex) {
    const list = $('#travellerList');
    const n = tripDraft.travellers.length;
    list.innerHTML = tripDraft.travellers.map((p, i) => `
      <li>
        ${avatar({ name: p.name || '?' }, i)}
        <label class="sr-only" for="trav-${i}">Traveller ${i + 1} name</label>
        <input id="trav-${i}" class="input" data-trav="${i}" maxlength="40" autocomplete="off" placeholder="Name" value="${esc(p.name)}" aria-describedby="travellers-err">
        <button type="button" class="icon-btn" data-remove-trav="${i}" aria-label="Remove traveller ${i + 1}${p.name ? ` (${esc(p.name)})` : ''}" ${n <= 1 ? 'disabled' : ''}>${icon('trash')}</button>
      </li>`).join('');
    const add = $('#addTraveller');
    add.disabled = n >= MAX_TRAVELLERS;
    add.title = n >= MAX_TRAVELLERS ? 'A trip can have up to 8 travellers' : '';
    if (focusIndex != null) {
      const el = $(`#trav-${Math.min(focusIndex, n - 1)}`);
      if (el) el.focus();
    }
  }

  function updateTripLength() {
    const s = $('#tripStart').value, e = $('#tripEnd').value;
    const el = $('#tripLength');
    if (parseDate(s) && parseDate(e) && diffDays(s, e) >= 0) {
      const n = diffDays(s, e) + 1;
      el.textContent = n > MAX_DAYS ? `That is ${n} days — trips can be at most ${MAX_DAYS} days.` : `${plural(n, 'day')} · ${fmtDay(s)} to ${fmtDay(e)}`;
    } else el.textContent = 'Trips can be 1 to 30 days long.';
  }

  function submitTrip() {
    const name = $('#tripName').value.trim();
    const start = $('#tripStart').value, end = $('#tripEnd').value;
    let firstBad = null;
    const bad = el => { if (!firstBad) firstBad = el; };

    setError('tripName', name ? '' : 'Give the trip a name.');
    if (!name) bad($('#tripName'));

    let startErr = '', endErr = '';
    if (!parseDate(start)) startErr = 'Choose a start date.';
    if (!parseDate(end)) endErr = 'Choose an end date.';
    else if (!startErr && diffDays(start, end) < 0) endErr = 'The end date can’t be before the start date.';
    else if (!startErr && diffDays(start, end) + 1 > MAX_DAYS) endErr = `Trips can be at most ${MAX_DAYS} days. Pick an end date on or before ${fmtDay(addDays(start, MAX_DAYS - 1))}.`;
    setError('tripStart', startErr); if (startErr) bad($('#tripStart'));
    setError('tripEnd', endErr); if (endErr) bad($('#tripEnd'));

    const travs = tripDraft.travellers.map(p => ({ ...p, name: p.name.trim() }));
    const inputs = $$('#travellerList input');
    inputs.forEach(i => i.setAttribute('aria-invalid', 'false'));
    let tErr = '';
    const seen = new Map();
    travs.forEach((p, i) => {
      if (!p.name) { tErr = tErr || 'Every traveller needs a name — fill it in or remove the empty row.'; inputs[i].setAttribute('aria-invalid', 'true'); bad(inputs[i]); return; }
      const k = p.name.toLowerCase();
      if (seen.has(k)) { tErr = tErr || `“${p.name}” is listed twice. Each traveller needs a different name.`; inputs[i].setAttribute('aria-invalid', 'true'); bad(inputs[i]); }
      seen.set(k, i);
    });
    if (!travs.length) tErr = 'Add at least one traveller.';
    const te = $('#travellers-err');
    te.textContent = tErr; te.hidden = !tErr;

    if (firstBad) { firstBad.focus(); return; }

    const currency = $('#tripCurrency').value;
    const dlg = $('#tripDialog');
    if (!tripDraft.id) {
      const trip = { id: uid(), name, start, end, currency, travellers: travs, activities: [] };
      commit(`Create trip “${name}”`, () => { state.trips.push(trip); state.currentId = trip.id; });
      ui.query = ''; $('#search').value = ''; $('#searchClear').hidden = true;
      render();
      closeDialog(dlg, 'edit-trip');
      toast(`Trip “${name}” created. Add your first activity to a day.`);
      return;
    }
    let moved = 0;
    commit(`Edit trip “${name}”`, () => {
      const t = state.trips.find(x => x.id === tripDraft.id);
      const oldLen = diffDays(t.start, t.end) + 1, newLen = diffDays(start, end) + 1;
      const offset = diffDays(t.start, start);
      // Shifting the whole trip (same length) keeps every activity on its day number;
      // otherwise activities stay on their calendar date and anything outside the new range is unscheduled.
      const shift = offset !== 0 && oldLen === newLen;
      t.name = name; t.currency = currency;
      for (const a of t.activities) {
        if (a.date == null) continue;
        if (shift) a.date = addDays(a.date, offset);
        else if (diffDays(start, a.date) < 0 || diffDays(a.date, end) < 0) { a.date = null; moved++; }
      }
      t.start = start; t.end = end;
      t.travellers = travs;
      const ids = travs.map(p => p.id);
      for (const a of t.activities) {
        if (!ids.includes(a.paidBy)) a.paidBy = ids[0];
        a.split = ids.filter(id => a.split.includes(id));
        if (!a.split.length) a.split = ids.slice();
      }
    });
    closeDialog(dlg);
    if (moved) toast(`${plural(moved, 'activity', 'activities')} moved to Unscheduled because ${moved === 1 ? 'its day is' : 'their days are'} no longer part of the trip.`, { action: { label: 'Undo', run: undo } });
    else toast('Trip details saved.');
  }

  /* ---------- Activity dialog ---------- */
  let actDraft = null;

  function openActivityDialog(trip, { id, date }, opener) {
    const a = id ? trip.activities.find(x => x.id === id) : null;
    if (id && !a) return;
    actDraft = { id: a ? a.id : null };
    const days = tripDays(trip);
    const d = a ? a.date : date;
    const tids = trip.travellers.map(p => p.id);

    $('#actDialogTitle').textContent = a ? a.title : 'New activity';
    $('#actEyebrow').textContent = a ? `Activity · ${dayName(trip, a.date)}` : `New activity · ${dayName(trip, d)}`;
    $('#actSubmit').textContent = a ? 'Save changes' : 'Add activity';
    $('#actDelete').hidden = !a;
    $('#actTitle').value = a ? a.title : '';
    $('#actPlace').value = a ? a.place : '';
    $('#actNotes').value = a ? a.notes : '';
    $('#actStart').value = a ? a.start : suggestStart(trip, d);
    $('#actCost').value = a ? centsToInput(a.cost) : '';
    $('#actCurrency').textContent = trip.currency;

    $('#actDay').innerHTML = days.map((x, i) => `<option value="${x}"${x === d ? ' selected' : ''}>Day ${i + 1} · ${esc(fmtDay(x))}</option>`).join('')
      + `<option value=""${d == null ? ' selected' : ''}>Unscheduled</option>`;

    const durOpts = [];
    for (let m = 15; m <= 720; m += 15) durOpts.push(`<option value="${m}"${m === (a ? a.duration : 60) ? ' selected' : ''}>${durLabel(m)}</option>`);
    $('#actDuration').innerHTML = durOpts.join('');

    const catSel = a ? a.category : 'sight';
    $('#actCategories').innerHTML = CATEGORIES.map(c => `
      <label class="seg cat-${c.id}"><input type="radio" name="category" value="${c.id}"${c.id === catSel ? ' checked' : ''}><span>${icon(c.id)}${c.label}</span></label>`).join('');

    $('#actPaidBy').innerHTML = trip.travellers.map(p => `<option value="${esc(p.id)}"${(a ? a.paidBy : tids[0]) === p.id ? ' selected' : ''}>${esc(p.name)}</option>`).join('');
    const split = a ? a.split : tids;
    $('#actSplit').innerHTML = trip.travellers.map(p => `
      <label class="check"><input type="checkbox" value="${esc(p.id)}"${split.includes(p.id) ? ' checked' : ''} aria-describedby="actSplit-err"><span><span class="box"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg></span>${esc(p.name)}</span></label>`).join('');

    ['actTitle', 'actStart', 'actCost'].forEach(x => setError(x, ''));
    $('#actSplit-err').hidden = true;
    updateSplitHint();
    openDialog($('#actDialog'), opener, $('#actTitle'));
  }

  function suggestStart(trip, date) {
    if (date == null) return '09:00';
    const list = sortActs(trip.activities.filter(a => a.date === date));
    if (!list.length) return '09:00';
    const end = Math.max(...list.map(endMin));
    const rounded = Math.ceil(end / 15) * 15;
    return rounded < 1440 ? clock(rounded) : '09:00';
  }

  function updateSplitHint() {
    const trip = cur();
    if (!trip) return;
    const n = $$('#actSplit input:checked').length;
    const c = parseCost($('#actCost').value);
    const hint = $('#splitHint');
    if (!n) hint.textContent = '';
    else if (c.value) hint.textContent = `· about ${money(Math.floor(c.value / n), trip.currency)} each`;
    else hint.textContent = `· ${plural(n, 'person', 'people')}`;
  }

  function submitActivity() {
    const trip = cur();
    if (!trip) return;
    const title = $('#actTitle').value.trim();
    const start = $('#actStart').value;
    const cost = parseCost($('#actCost').value);
    const split = $$('#actSplit input:checked').map(i => i.value);
    let firstBad = null;
    const bad = el => { if (!firstBad) firstBad = el; };

    setError('actTitle', title ? '' : 'Give the activity a title.');
    if (!title) bad($('#actTitle'));
    const startOk = TIME_RE.test(start);
    setError('actStart', startOk ? '' : 'Choose a start time, like 09:30.');
    if (!startOk) bad($('#actStart'));
    setError('actCost', cost.error || '');
    if (cost.error) bad($('#actCost'));
    const se = $('#actSplit-err');
    se.textContent = split.length ? '' : 'Choose at least one person to split the cost with.';
    se.hidden = !!split.length;
    if (!split.length) bad($('#actSplit input'));
    if (firstBad) { firstBad.focus(); return; }

    const data = {
      title, start,
      date: $('#actDay').value || null,
      duration: Number($('#actDuration').value),
      place: $('#actPlace').value.trim(),
      category: ($('#actCategories input:checked') || { value: 'other' }).value,
      cost: cost.value,
      notes: $('#actNotes').value.replace(/\s+$/, ''),
      paidBy: $('#actPaidBy').value,
      split
    };
    const dlg = $('#actDialog');
    if (!actDraft.id) {
      const id = uid();
      commit(`Add “${title}”`, () => { trip.activities.push({ id, ...data }); });
      closeDialog(dlg, `open-${id}`);
      toast(`Added “${title}” to ${dayName(trip, data.date)}.`);
    } else {
      commit(`Edit “${title}”`, () => { Object.assign(trip.activities.find(a => a.id === actDraft.id), data); });
      closeDialog(dlg, `open-${actDraft.id}`);
      toast(`Saved “${title}”.`);
    }
  }

  function deleteActivityFromDialog() {
    const trip = cur();
    const a = trip && trip.activities.find(x => x.id === actDraft.id);
    if (!a) return;
    if (!window.confirm(`Delete “${a.title}”? You can undo this afterwards.`)) return;
    const fk = a.date ? `add-${a.date}` : 'edit-trip';
    commit(`Delete “${a.title}”`, () => { trip.activities = trip.activities.filter(x => x.id !== a.id); });
    closeDialog($('#actDialog'), fk);
    toast(`Deleted “${a.title}”.`, { action: { label: 'Undo', run: undo } });
  }

  /* ---------- Moving ---------- */
  function moveActivity(id, date) {
    const trip = cur();
    const a = trip && trip.activities.find(x => x.id === id);
    if (!a || a.date === date) return false;
    commit(`Move “${a.title}”`, () => { a.date = date; });
    const t2 = cur();
    let extra = '';
    if (date) {
      const list = sortActs(t2.activities.filter(x => x.date === date));
      const c = conflictsFor(list).get(id) || [];
      if (c.length) extra = ` It overlaps ${c.map(b => `${b.title} ${b.start}-${clock(endMin(b))}`).join(', ')}.`;
    }
    toast(`Moved “${a.title}” to ${dayName(t2, date)}.${extra}`, { kind: extra ? 'error' : undefined });
    return true;
  }

  let menu = null;
  function openMoveMenu(btn) {
    closeMoveMenu();
    const trip = cur();
    const id = btn.dataset.id;
    const a = trip.activities.find(x => x.id === id);
    if (!a) return;
    const el = document.createElement('div');
    el.className = 'menu';
    el.setAttribute('role', 'menu');
    el.id = 'moveMenu';
    el.setAttribute('aria-label', `Move ${a.title} to`);
    const opts = tripDays(trip).map((d, i) => ({ value: d, label: `Day ${i + 1}`, sub: fmtDay(d) }));
    opts.push({ value: '', label: 'Unscheduled', sub: 'Decide later' });
    el.innerHTML = `<p class="menu-title" aria-hidden="true">Move to…</p>` + opts.map((o, i) => {
      const current = (o.value || null) === a.date;
      return `${i === opts.length - 1 ? '<div class="menu-sep" role="separator"></div>' : ''}<button type="button" role="menuitem" class="menu-item" tabindex="-1" data-value="${o.value}"${current ? ' aria-disabled="true"' : ''}><span>${o.label}${current ? ' <span class="sr-only">(current)</span>' : ''}</span><span class="menu-sub">${current ? 'Current · ' : ''}${esc(o.sub)}</span></button>`;
    }).join('');
    document.body.append(el);
    btn.setAttribute('aria-expanded', 'true');
    btn.setAttribute('aria-controls', 'moveMenu');
    menu = { el, btn, id };
    positionMenu();
    const items = $$('.menu-item', el);
    (items.find(i => !i.hasAttribute('aria-disabled')) || items[0]).focus();

    el.addEventListener('keydown', e => {
      const list = $$('.menu-item', el);
      const idx = list.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); list[(idx + 1) % list.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); list[(idx - 1 + list.length) % list.length].focus(); }
      else if (e.key === 'Home') { e.preventDefault(); list[0].focus(); }
      else if (e.key === 'End') { e.preventDefault(); list[list.length - 1].focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeMoveMenu(true); }
      else if (e.key === 'Tab') { e.preventDefault(); closeMoveMenu(true); }
    });
    el.addEventListener('click', e => {
      const item = e.target.closest('.menu-item');
      if (!item || item.getAttribute('aria-disabled') === 'true') return;
      const value = item.dataset.value || null;
      closeMoveMenu(false);
      moveActivity(id, value);
      const target = document.querySelector(`[data-fk="move-${CSS.escape(id)}"]`);
      if (target) { target.focus(); target.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
    });
  }
  /* Keeps the menu anchored to its button (the board may scroll or snap while it is open). */
  function positionMenu() {
    if (!menu) return;
    const { el, btn } = menu;
    const r = btn.getBoundingClientRect();
    if (!btn.isConnected || r.bottom < 0 || r.top > window.innerHeight) { closeMoveMenu(false); return; }
    const w = el.offsetWidth, h = el.offsetHeight;
    let top = r.bottom + 6;
    if (top + h > window.innerHeight - 8) top = Math.max(8, r.top - h - 6);
    const left = Math.max(8, Math.min(r.right - w, window.innerWidth - w - 8));
    el.style.top = `${top}px`;
    el.style.left = `${left}px`;
  }

  function closeMoveMenu(refocus) {
    if (!menu) return;
    const { el, btn } = menu;
    menu = null;
    el.remove();
    if (btn.isConnected) {
      btn.setAttribute('aria-expanded', 'false');
      btn.removeAttribute('aria-controls');
      if (refocus) btn.focus();
    }
  }

  /* ---------- Export / import ---------- */
  function download(filename, text, type) {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const slug = s => s.toLowerCase().normalize('NFKD').replace(/[^\w\s-]/g, '').trim().replace(/[\s_]+/g, '-').slice(0, 50) || 'trip';

  const icsEscape = s => String(s).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
  function icsFold(line) {
    const enc = new TextEncoder();
    const parts = [];
    let current = '', len = 0, limit = 75;
    for (const ch of line) {
      const l = enc.encode(ch).length;
      if (len + l > limit) { parts.push(current); current = ''; len = 0; limit = 74; }
      current += ch; len += l;
    }
    parts.push(current);
    return parts.join('\r\n ');
  }
  function icsDateTime(date, minutes) {
    const d = addDays(date, Math.floor(minutes / 1440));
    const m = minutes % 1440;
    return `${d.replace(/-/g, '')}T${pad(Math.floor(m / 60))}${pad(m % 60)}00`;
  }

  function exportICS(trip) {
    const scheduled = sortActs(trip.activities.filter(a => a.date)).sort((a, b) => a.date.localeCompare(b.date) || toMin(a.start) - toMin(b.start));
    if (!scheduled.length) {
      toast('There are no scheduled activities to export yet. Add activities to a day first.', { kind: 'error' });
      return;
    }
    const now = new Date();
    const stamp = `${now.getUTCFullYear()}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}T${pad(now.getUTCHours())}${pad(now.getUTCMinutes())}${pad(now.getUTCSeconds())}Z`;
    const nameOf = id => (trip.travellers.find(p => p.id === id) || {}).name || '';
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Wayfare//Trip Planner//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', `X-WR-CALNAME:${icsEscape(trip.name)}`];
    for (const a of scheduled) {
      const desc = [a.notes, a.cost != null ? `Cost: ${money(a.cost, trip.currency)} (paid by ${nameOf(a.paidBy)})` : ''].filter(Boolean).join('\n\n');
      lines.push('BEGIN:VEVENT',
        `UID:${a.id}@wayfare.trip-${trip.id}`,
        `DTSTAMP:${stamp}`,
        `DTSTART:${icsDateTime(a.date, toMin(a.start))}`,
        `DTEND:${icsDateTime(a.date, endMin(a))}`,
        `SUMMARY:${icsEscape(a.title)}`);
      if (a.place) lines.push(`LOCATION:${icsEscape(a.place)}`);
      if (desc) lines.push(`DESCRIPTION:${icsEscape(desc)}`);
      lines.push(`CATEGORIES:${CAT[a.category].label.toUpperCase()}`, 'END:VEVENT');
    }
    lines.push('END:VCALENDAR');
    download(`${slug(trip.name)}.ics`, lines.map(icsFold).join('\r\n') + '\r\n', 'text/calendar;charset=utf-8');
    const skipped = trip.activities.length - scheduled.length;
    toast(`Exported ${plural(scheduled.length, 'event')} to ${slug(trip.name)}.ics${skipped ? ` (${skipped} unscheduled left out)` : ''}.`);
  }

  function exportJSON(trip) {
    const data = { app: 'wayfare', kind: 'trip', version: 1, exportedAt: new Date().toISOString(), trip };
    download(`${slug(trip.name)}.json`, JSON.stringify(data, null, 2), 'application/json');
    toast(`Exported “${trip.name}” as ${slug(trip.name)}.json.`);
  }

  function importFile(file) {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { showImportError('The file is larger than 2 MB, which is too big for a trip export.'); return; }
    const reader = new FileReader();
    reader.onerror = () => showImportError('The file could not be read.');
    reader.onload = () => {
      let data;
      try { data = JSON.parse(String(reader.result)); } catch (e) { showImportError(`“${file.name}” isn’t valid JSON.`); return; }
      let trip;
      try {
        const raw = data && typeof data === 'object' && data.trip && typeof data.trip === 'object' ? data.trip : data;
        trip = normalizeTrip(raw);
      } catch (e) {
        showImportError(`“${file.name}” doesn’t look like a Wayfare trip: ${e.message}`);
        return;
      }
      if (state.trips.some(t => t.id === trip.id)) trip.id = uid();
      showImportError('');
      commit(`Import “${trip.name}”`, () => { state.trips.push(trip); state.currentId = trip.id; });
      toast(`Imported “${trip.name}” with ${plural(trip.activities.length, 'activity', 'activities')}.`);
      const h = $('#tripTitle');
      if (h) { h.tabIndex = -1; h.focus(); }
    };
    reader.readAsText(file);
  }

  /* ---------- Events ---------- */
  function onClick(e) {
    const btn = e.target.closest('[data-action]');
    if (!btn || btn.disabled) return;
    const trip = cur();
    switch (btn.dataset.action) {
      case 'undo': undo(); break;
      case 'redo': redo(); break;
      case 'new-trip': openTripDialog(null, btn); break;
      case 'import': $('#importFile').value = ''; $('#importFile').click(); break;
      case 'edit-trip': if (trip) openTripDialog(trip, btn); break;
      case 'delete-trip': {
        if (!trip) break;
        const n = trip.activities.length;
        if (!window.confirm(`Delete the trip “${trip.name}”${n ? ` and its ${plural(n, 'activity', 'activities')}` : ''}?`)) break;
        commit(`Delete trip “${trip.name}”`, () => {
          state.trips = state.trips.filter(t => t.id !== trip.id);
          state.currentId = state.trips[0] ? state.trips[0].id : null;
        });
        toast(`Deleted “${trip.name}”.`, { action: { label: 'Undo', run: undo } });
        $('#main').focus();
        break;
      }
      case 'export-ics': if (trip) exportICS(trip); break;
      case 'export-json': if (trip) exportJSON(trip); break;
      case 'add-activity': if (trip) openActivityDialog(trip, { date: btn.dataset.date }, btn); break;
      case 'open-activity': if (trip) openActivityDialog(trip, { id: btn.dataset.id }, btn); break;
      case 'move-menu':
        if (menu && menu.btn === btn) closeMoveMenu(true); else openMoveMenu(btn);
        break;
      case 'dismiss-notice': ui.storageNotice = ''; renderNotices(); $('#main').focus(); break;
      case 'dismiss-import': showImportError(''); $('#main').focus(); break;
    }
  }

  function onKeydown(e) {
    const mod = e.ctrlKey || e.metaKey;
    if (!mod || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k !== 'z' && k !== 'y') return;
    if (document.querySelector('dialog[open]')) return;
    const t = e.target;
    // Let text fields keep their own native undo while they hold text.
    if (t && t.matches && t.matches('textarea, input:not([type=checkbox]):not([type=radio]):not([type=button])') && t.value) return;
    e.preventDefault();
    if (k === 'y' || e.shiftKey) redo(); else undo();
  }

  let dragId = null;
  function setupDnD() {
    document.addEventListener('dragstart', e => {
      const card = e.target.closest && e.target.closest('.card[draggable="true"]');
      if (!card) return;
      closeMoveMenu();
      dragId = card.dataset.id;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', dragId);
      requestAnimationFrame(() => card.classList.add('dragging'));
    });
    document.addEventListener('dragend', () => {
      dragId = null;
      $$('.dragging').forEach(x => x.classList.remove('dragging'));
      $$('.drop-over').forEach(x => x.classList.remove('drop-over'));
    });
    document.addEventListener('dragover', e => {
      if (!dragId) return;
      const zone = e.target.closest && e.target.closest('[data-drop]');
      $$('.drop-over').forEach(x => { if (x !== zone) x.classList.remove('drop-over'); });
      if (!zone) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      zone.classList.add('drop-over');
    });
    document.addEventListener('drop', e => {
      if (!dragId) return;
      const zone = e.target.closest && e.target.closest('[data-drop]');
      if (!zone) return;
      e.preventDefault();
      const id = dragId;
      dragId = null;
      $$('.drop-over').forEach(x => x.classList.remove('drop-over'));
      moveActivity(id, zone.dataset.drop === 'unscheduled' ? null : zone.dataset.drop);
    });
  }

  function init() {
    load();
    ['#tripDialog', '#actDialog'].forEach(s => setupDialog($(s)));

    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKeydown);
    document.addEventListener('pointerdown', e => {
      if (menu && !menu.el.contains(e.target) && !menu.btn.contains(e.target)) closeMoveMenu(false);
    });
    window.addEventListener('resize', positionMenu);
    window.addEventListener('scroll', positionMenu, { passive: true });
    $('#board').addEventListener('scroll', positionMenu, { passive: true });
    setupDnD();

    $('#tripSelect').addEventListener('change', e => {
      state.currentId = e.target.value;
      ui.query = ''; $('#search').value = ''; $('#searchClear').hidden = true;
      save();
      render();
    });

    const search = $('#search');
    search.addEventListener('input', () => {
      ui.query = search.value;
      $('#searchClear').hidden = !search.value;
      const trip = cur();
      if (trip) renderItinerary(trip);
    });
    search.addEventListener('keydown', e => {
      if (e.key === 'Escape' && search.value) { e.preventDefault(); search.value = ''; search.dispatchEvent(new Event('input')); }
    });
    $('#searchClear').addEventListener('click', () => { search.value = ''; search.dispatchEvent(new Event('input')); search.focus(); });

    $('#importFile').addEventListener('change', e => importFile(e.target.files[0]));

    // Trip dialog
    $('#tripForm').addEventListener('submit', e => { e.preventDefault(); submitTrip(); });
    $('#tripStart').addEventListener('change', updateTripLength);
    $('#tripEnd').addEventListener('change', updateTripLength);
    $('#tripStart').addEventListener('input', updateTripLength);
    $('#tripEnd').addEventListener('input', updateTripLength);
    $('#travellerList').addEventListener('input', e => {
      const i = e.target.dataset.trav;
      if (i != null) tripDraft.travellers[Number(i)].name = e.target.value;
    });
    $('#travellerList').addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.target.dataset.trav != null) {
        e.preventDefault();
        if (tripDraft.travellers.length < MAX_TRAVELLERS && Number(e.target.dataset.trav) === tripDraft.travellers.length - 1 && e.target.value.trim()) $('#addTraveller').click();
      }
    });
    $('#travellerList').addEventListener('click', e => {
      const b = e.target.closest('[data-remove-trav]');
      if (!b || b.disabled) return;
      const i = Number(b.dataset.removeTrav);
      tripDraft.travellers.splice(i, 1);
      renderTravellerInputs(i);
    });
    $('#addTraveller').addEventListener('click', () => {
      if (tripDraft.travellers.length >= MAX_TRAVELLERS) return;
      tripDraft.travellers.push({ id: uid(), name: '' });
      renderTravellerInputs(tripDraft.travellers.length - 1);
    });

    // Activity dialog
    $('#actForm').addEventListener('submit', e => { e.preventDefault(); submitActivity(); });
    $('#actDelete').addEventListener('click', deleteActivityFromDialog);
    $('#actSplit').addEventListener('change', updateSplitHint);
    $('#actCost').addEventListener('input', updateSplitHint);

    render();
  }

  init();
})();
