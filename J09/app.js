/* Wayfare: multi-day trip planner. Plain JS, no dependencies. */
(function () {
  'use strict';

  const STORAGE_KEY = 'r11-trip-planner';
  const HISTORY_LIMIT = 20;
  const MAX_DAYS = 30;
  const MAX_TRAVELLERS = 8;

  const CATEGORIES = [
    { id: 'food', label: 'Food' },
    { id: 'sight', label: 'Sight' },
    { id: 'transport', label: 'Transport' },
    { id: 'stay', label: 'Stay' },
    { id: 'other', label: 'Other' },
  ];
  const CURRENCIES = [
    { code: 'EUR', sym: '€', label: 'Euro (€)' },
    { code: 'USD', sym: '$', label: 'US dollar ($)' },
    { code: 'GBP', sym: '£', label: 'British pound (£)' },
    { code: 'CHF', sym: 'CHF ', label: 'Swiss franc (CHF)' },
    { code: 'JPY', sym: '¥', label: 'Japanese yen (¥)' },
    { code: 'AUD', sym: 'A$', label: 'Australian dollar (A$)' },
    { code: 'CAD', sym: 'C$', label: 'Canadian dollar (C$)' },
    { code: 'SEK', sym: 'kr ', label: 'Swedish krona (kr)' },
  ];

  /* ---------- Icons (inline SVG) ---------- */
  const ICONS = {
    plus: '<path d="M12 5v14M5 12h14"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    redo: '<path d="m15 14 5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    upload: '<path d="M12 15V3"/><path d="m7 8 5-5 5 5"/><path d="M5 21h14"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m6 6 1 14a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-14"/><path d="M10 11v6M14 11v6"/>',
    pencil: '<path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/>',
    move: '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
    alert: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    wallet: '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pin: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    arrowRight: '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    compass: '<circle cx="12" cy="12" r="9.25"/><path d="m15.9 8.1-2.2 5.6-5.6 2.2 2.2-5.6z"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    eyeOff: '<path d="M9.9 4.2A10 10 0 0 1 12 4c7 0 10 8 10 8a17 17 0 0 1-2.2 3.4M6.6 6.6C3.6 8.6 2 12 2 12s3 8 10 8a9.7 9.7 0 0 0 5.4-1.6"/><path d="M14.1 14.1a3 3 0 0 1-4.2-4.2"/><path d="m2 2 20 20"/>',
    food: '<path d="M3 2v7a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6a2 2 0 0 0 2 2h3Zm0 0v7"/>',
    sight: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3z"/><circle cx="12" cy="13" r="3"/>',
    transport: '<rect x="4" y="3" width="16" height="15" rx="3"/><path d="M4 11h16M12 3v8"/><path d="m8 18-2 4M16 18l2 4"/><path d="M8.5 14.5h.01M15.5 14.5h.01"/>',
    stay: '<path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/>',
    other: '<path d="m12 3 1.9 5.8H20l-4.9 3.6 1.9 5.8-5-3.6-5 3.6 1.9-5.8L4 8.8h6.1Z"/>',
  };
  function icon(name, cls) {
    return '<svg class="icon' + (cls ? ' ' + cls : '') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + ICONS[name] + '</svg>';
  }

  /* ---------- Small helpers ---------- */
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ESC[c]);
  const uid = () => Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);
  const pad = (n) => String(n).padStart(2, '0');
  const plural = (n, one, many) => n + ' ' + (n === 1 ? one : (many || one + 's'));
  const catById = (id) => CATEGORIES.find((c) => c.id === id) || CATEGORIES[4];
  const currency = (trip) => CURRENCIES.find((c) => c.code === (trip && trip.currency)) || CURRENCIES[0];

  // Dates are handled as UTC midnight so DST never shifts a day.
  function parseISO(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || ''));
    if (!m) return null;
    const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
    return d.getUTCMonth() === +m[2] - 1 && d.getUTCDate() === +m[3] ? d : null;
  }
  const toISO = (d) => d.toISOString().slice(0, 10);
  function addDays(iso, n) { const d = parseISO(iso); d.setUTCDate(d.getUTCDate() + n); return toISO(d); }
  const diffDays = (a, b) => Math.round((parseISO(b) - parseISO(a)) / 86400000);
  const WD = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const MO = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmtDay(iso) { const d = parseISO(iso); return WD[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MO[d.getUTCMonth()]; }
  function fmtRange(a, b) {
    const da = parseISO(a), db = parseISO(b);
    if (a === b) return fmtDay(a) + ' ' + da.getUTCFullYear();
    const sameYear = da.getUTCFullYear() === db.getUTCFullYear();
    return fmtDay(a) + (sameYear ? '' : ' ' + da.getUTCFullYear()) + ' – ' + fmtDay(b) + ' ' + db.getUTCFullYear();
  }
  function todayISO() { const n = new Date(); return n.getFullYear() + '-' + pad(n.getMonth() + 1) + '-' + pad(n.getDate()); }

  const toMin = (t) => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };
  function fmtMin(m) { const mm = ((m % 1440) + 1440) % 1440; return pad(Math.floor(mm / 60)) + ':' + pad(mm % 60); }
  function fmtEnd(start, end) { return fmtMin(end) + (end >= 1440 ? ' (+1)' : ''); }
  function fmtDur(m) {
    const h = Math.floor(m / 60), r = m % 60;
    return (h ? h + ' h' : '') + (h && r ? ' ' : '') + (r ? r + ' min' : '');
  }
  const isTime = (t) => /^([01]\d|2[0-3]):[0-5]\d$/.test(String(t || ''));

  const toCents = (v) => (typeof v === 'number' && isFinite(v) && v > 0 ? Math.round(v * 100) : 0);
  function fmtMoney(cents, trip) {
    const sym = currency(trip).sym;
    const sign = cents < 0 ? '−' : '';
    return sign + sym + (Math.abs(cents) / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  const initials = (name) => name.trim().split(/\s+/).slice(0, 2).map((p) => p[0]).join('').toUpperCase();

  /* ---------- State, persistence, history ---------- */
  let state = { trips: [], currentId: null };
  let undoStack = [];
  let redoStack = [];
  const ui = { search: '', banner: null, trayNotice: null };

  function normalizeTrip(t) {
    if (!t || typeof t !== 'object' || Array.isArray(t)) throw new Error('the file does not contain a trip.');
    const name = typeof t.name === 'string' ? t.name.trim() : '';
    if (!name) throw new Error('the trip has no name.');
    if (!parseISO(t.start) || !parseISO(t.end)) throw new Error('the trip dates are missing or not valid.');
    if (t.end < t.start) throw new Error('the trip ends before it starts.');
    if (diffDays(t.start, t.end) + 1 > MAX_DAYS) throw new Error('the trip is longer than ' + MAX_DAYS + ' days.');
    if (!Array.isArray(t.travellers) || t.travellers.length < 1 || t.travellers.length > MAX_TRAVELLERS) {
      throw new Error('a trip needs between 1 and ' + MAX_TRAVELLERS + ' travellers.');
    }
    const seenNames = new Set();
    const seenIds = new Set();
    const travellers = t.travellers.map((p) => {
      const tr = typeof p === 'string' ? { name: p } : p;
      const pname = tr && typeof tr.name === 'string' ? tr.name.trim() : '';
      if (!pname) throw new Error('a traveller has no name.');
      if (seenNames.has(pname.toLowerCase())) throw new Error('two travellers share the name "' + pname + '".');
      seenNames.add(pname.toLowerCase());
      let id = tr && typeof tr.id === 'string' && tr.id ? tr.id : uid();
      if (seenIds.has(id)) id = uid();
      seenIds.add(id);
      return { id, name: pname.slice(0, 40) };
    });
    const ids = travellers.map((p) => p.id);
    if (t.activities != null && !Array.isArray(t.activities)) throw new Error('the activity list is not valid.');
    const actIds = new Set();
    const activities = (t.activities || []).map((a, i) => {
      if (!a || typeof a !== 'object') throw new Error('activity ' + (i + 1) + ' is not valid.');
      const title = typeof a.title === 'string' ? a.title.trim() : '';
      if (!title) throw new Error('activity ' + (i + 1) + ' has no title.');
      if (!isTime(a.start)) throw new Error('"' + title + '" has no valid start time.');
      const duration = Number(a.duration);
      if (!Number.isInteger(duration) || duration < 15 || duration > 720 || duration % 15) {
        throw new Error('"' + title + '" has a duration that is not 15 min to 12 h in 15-minute steps.');
      }
      const category = CATEGORIES.some((c) => c.id === a.category) ? a.category : null;
      if (!category) throw new Error('"' + title + '" has an unknown category.');
      let cost = null;
      if (a.cost != null && a.cost !== '') {
        cost = Number(a.cost);
        if (!isFinite(cost) || cost < 0) throw new Error('"' + title + '" has a cost that is not a positive number.');
        cost = Math.round(cost * 100) / 100;
      }
      let day = a.day == null || a.day === '' ? null : a.day;
      if (day !== null && !parseISO(day)) throw new Error('"' + title + '" has an invalid day.');
      if (day !== null && (day < t.start || day > t.end)) day = null;
      let id = typeof a.id === 'string' && a.id ? a.id : uid();
      if (actIds.has(id)) id = uid();
      actIds.add(id);
      const split = Array.isArray(a.split) ? ids.filter((x) => a.split.includes(x)) : [];
      return {
        id, title: title.slice(0, 120), day, start: a.start, duration,
        place: typeof a.place === 'string' ? a.place.slice(0, 160) : '',
        category, cost,
        notes: typeof a.notes === 'string' ? a.notes : '',
        paidBy: ids.includes(a.paidBy) ? a.paidBy : ids[0],
        split: split.length ? split : ids.slice(),
      };
    });
    return {
      id: typeof t.id === 'string' && t.id ? t.id : uid(),
      name: name.slice(0, 80), start: t.start, end: t.end,
      currency: CURRENCIES.some((c) => c.code === t.currency) ? t.currency : 'EUR',
      travellers, activities,
    };
  }

  function load() {
    let raw = null;
    try { raw = localStorage.getItem(STORAGE_KEY); } catch (e) {
      ui.banner = { kind: 'warn', title: 'Storage is unavailable', text: 'Your browser is blocking local storage, so changes will not be kept after you close this tab.' };
      return;
    }
    if (raw == null) return;
    try {
      const data = JSON.parse(raw);
      if (!data || !Array.isArray(data.trips)) throw new Error('bad shape');
      const trips = data.trips.map(normalizeTrip);
      const tripIds = new Set();
      trips.forEach((t) => { if (tripIds.has(t.id)) t.id = uid(); tripIds.add(t.id); });
      state = { trips, currentId: trips.some((t) => t.id === data.currentId) ? data.currentId : (trips[0] ? trips[0].id : null) };
    } catch (e) {
      state = { trips: [], currentId: null };
      ui.banner = { kind: 'warn', title: 'We could not read your saved trips', text: 'The saved data was damaged, so the planner started empty. Create a new trip or import a trip file to carry on.' };
    }
  }

  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, trips: state.trips, currentId: state.currentId })); }
    catch (e) { toast('Could not save your changes in this browser.', { icon: 'alert' }); }
  }

  function commit(mutate) {
    const before = JSON.stringify(state);
    mutate();
    undoStack.push(before);
    if (undoStack.length > HISTORY_LIMIT) undoStack.shift();
    redoStack = [];
    save();
    render();
  }
  function undo() {
    if (!undoStack.length) return;
    redoStack.push(JSON.stringify(state));
    state = JSON.parse(undoStack.pop());
    afterHistory('Undone');
  }
  function redo() {
    if (!redoStack.length) return;
    undoStack.push(JSON.stringify(state));
    state = JSON.parse(redoStack.pop());
    afterHistory('Redone');
  }
  function afterHistory(msg) {
    ui.trayNotice = null;
    save();
    render();
    toast(msg, { icon: msg === 'Undone' ? 'undo' : 'redo' });
  }

  const getTrip = () => state.trips.find((t) => t.id === state.currentId) || null;
  function tripDays(trip) {
    const n = diffDays(trip.start, trip.end) + 1;
    const out = [];
    for (let i = 0; i < n; i++) { const iso = addDays(trip.start, i); out.push({ iso, index: i, num: 'Day ' + (i + 1), date: fmtDay(iso) }); }
    return out;
  }
  function dayLabel(trip, iso) {
    if (!iso) return 'Unscheduled';
    return 'Day ' + (diffDays(trip.start, iso) + 1) + ' · ' + fmtDay(iso);
  }
  const sortActs = (list) => list.slice().sort((a, b) => toMin(a.start) - toMin(b.start) || a.duration - b.duration || a.title.localeCompare(b.title) || (a.id < b.id ? -1 : 1));

  function conflictsFor(list) {
    const map = new Map();
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i], b = list[j];
        const as = toMin(a.start), ae = as + a.duration, bs = toMin(b.start), be = bs + b.duration;
        if (as < be && bs < ae) {
          if (!map.has(a.id)) map.set(a.id, []);
          if (!map.has(b.id)) map.set(b.id, []);
          map.get(a.id).push(b);
          map.get(b.id).push(a);
        }
      }
    }
    return map;
  }
  function overlapText(others) {
    return others.map((o) => { const s = toMin(o.start); return 'overlaps ' + o.title + ' ' + fmtMin(s) + '-' + fmtMin(s + o.duration); }).join('; ');
  }

  /* ---------- Budget ---------- */
  function computeBudget(trip) {
    const ids = trip.travellers.map((p) => p.id);
    const paid = {}, share = {};
    ids.forEach((id) => { paid[id] = 0; share[id] = 0; });
    const byCat = {}, byDay = {};
    let total = 0, costed = 0;
    trip.activities.forEach((a, idx) => {
      const c = toCents(a.cost);
      if (!c) return;
      total += c; costed++;
      byCat[a.category] = (byCat[a.category] || 0) + c;
      const dk = a.day || '';
      byDay[dk] = (byDay[dk] || 0) + c;
      const payer = ids.includes(a.paidBy) ? a.paidBy : ids[0];
      paid[payer] += c;
      let split = ids.filter((id) => a.split.includes(id));
      if (!split.length) split = ids.slice();
      const base = Math.floor(c / split.length);
      const rem = c - base * split.length;
      split.forEach((id) => { share[id] += base; });
      // Leftover cents rotate across activities so nobody always pays them.
      for (let k = 0; k < rem; k++) share[split[(idx + k) % split.length]] += 1;
    });
    const people = trip.travellers.map((p) => ({ id: p.id, name: p.name, paid: paid[p.id], share: share[p.id], bal: paid[p.id] - share[p.id] }));
    return { total, costed, byCat, byDay, people, transfers: settle(people) };
  }

  // Minimum transfers: split the non-zero balances into as many zero-sum groups as
  // possible (each group of k people needs k-1 transfers), then settle each greedily.
  function settle(people) {
    const items = people.filter((p) => p.bal !== 0);
    const n = items.length;
    if (!n) return [];
    const N = 1 << n;
    const sum = new Array(N).fill(0);
    for (let m = 1; m < N; m++) {
      const low = m & -m;
      sum[m] = sum[m ^ low] + items[31 - Math.clz32(low)].bal;
    }
    const best = new Array(N).fill(-1);
    const pick = new Array(N).fill(0);
    best[0] = 0;
    for (let m = 1; m < N; m++) {
      if (sum[m] !== 0) continue;
      const low = m & -m, rest = m ^ low;
      for (let s = rest; ; s = (s - 1) & rest) {
        const g = s | low;
        if (sum[g] === 0 && best[m ^ g] >= 0 && best[m ^ g] + 1 > best[m]) { best[m] = best[m ^ g] + 1; pick[m] = g; }
        if (s === 0) break;
      }
    }
    const transfers = [];
    let m = N - 1;
    while (m) {
      const g = pick[m];
      const group = items.filter((_, i) => g & (1 << i)).map((p) => ({ p, left: p.bal }));
      for (;;) {
        const debtors = group.filter((x) => x.left < 0).sort((a, b) => a.left - b.left);
        const creditors = group.filter((x) => x.left > 0).sort((a, b) => b.left - a.left);
        if (!debtors.length || !creditors.length) break;
        const d = debtors[0], c = creditors[0];
        const amt = Math.min(-d.left, c.left);
        transfers.push({ from: d.p, to: c.p, amount: amt });
        d.left += amt; c.left -= amt;
      }
      m ^= g;
    }
    return transfers.sort((a, b) => b.amount - a.amount);
  }

  /* ---------- DOM refs ---------- */
  const el = {
    tripSelect: $('#tripSelect'), tripSwitch: $('#tripSwitch'),
    undo: $('#undoBtn'), redo: $('#redoBtn'), importBtn: $('#importBtn'), newTrip: $('#newTripBtn'), importFile: $('#importFile'),
    banner: $('#banner'), emptyApp: $('#emptyApp'), workspace: $('#workspace'),
    tripHead: $('#tripHead'), tray: $('#tray'), board: $('#board'), budget: $('#budget'),
    search: $('#searchInput'), searchClear: $('#searchClear'), searchStatus: $('#searchStatus'), addActivity: $('#addActivityBtn'),
    toasts: $('#toasts'),
    actDialog: $('#actDialog'), actForm: $('#actForm'), tripDialog: $('#tripDialog'), tripForm: $('#tripForm'),
  };

  function setupStaticIcons() {
    el.undo.innerHTML = icon('undo');
    el.redo.innerHTML = icon('redo');
    el.importBtn.innerHTML = icon('upload') + '<span class="btn-label">Import</span>';
    el.newTrip.innerHTML = icon('plus') + '<span class="btn-label">New trip</span>';
    $('#searchIcon').innerHTML = icon('search');
    el.searchClear.innerHTML = icon('x', 'icon-sm');
    el.addActivity.innerHTML = icon('plus') + '<span>Add activity</span>';
    $$('.dialog-head [data-close]').forEach((b) => { b.innerHTML = icon('x'); });
    $('#actDelete').innerHTML = icon('trash') + '<span>Delete</span>';
    $('#tAddTraveller').innerHTML = icon('plus') + '<span>Add traveller</span>';
    $('#fCats').innerHTML = CATEGORIES.map((c) =>
      '<label class="seg-opt cat-' + c.id + '"><input type="radio" name="category" value="' + c.id + '"><span>' + icon(c.id) + c.label + '</span></label>').join('');
    const dur = [];
    for (let m = 15; m <= 720; m += 15) dur.push('<option value="' + m + '">' + fmtDur(m) + '</option>');
    $('#fDuration').innerHTML = dur.join('');
    $('#tCurrency').innerHTML = CURRENCIES.map((c) => '<option value="' + c.code + '">' + esc(c.label) + '</option>').join('');
  }

  /* ---------- Rendering ---------- */
  let pendingFocus = null;

  function focusFid(fid) {
    if (!fid) return false;
    const target = document.querySelector('[data-fid="' + CSS.escape(fid) + '"]');
    if (target && !target.disabled && target.offsetParent !== null) { target.focus(); return true; }
    return false;
  }

  function render() {
    const active = document.activeElement;
    const prevFid = active && active.dataset ? active.dataset.fid : null;
    const trip = getTrip();

    renderTopbar(trip);
    renderBanner();
    if (!trip) {
      el.workspace.hidden = true;
      el.emptyApp.hidden = false;
      renderEmptyApp();
    } else {
      el.emptyApp.hidden = true;
      el.workspace.hidden = false;
      renderTripHead(trip);
      renderItinerary(trip);
      renderBudget(trip);
    }

    if (pendingFocus) { const f = pendingFocus; pendingFocus = null; focusFid(f); }
    else if (prevFid && (document.activeElement === document.body || !document.activeElement)) focusFid(prevFid);
  }

  function renderTopbar(trip) {
    el.undo.disabled = !undoStack.length;
    el.redo.disabled = !redoStack.length;
    el.tripSwitch.hidden = !state.trips.length;
    el.tripSelect.innerHTML = state.trips.map((t) =>
      '<option value="' + esc(t.id) + '"' + (trip && t.id === trip.id ? ' selected' : '') + '>' + esc(t.name) + '</option>').join('');
  }

  function renderBanner() {
    const b = ui.banner;
    if (!b) { el.banner.innerHTML = ''; return; }
    el.banner.innerHTML =
      '<div class="banner' + (b.kind === 'error' ? ' is-error' : '') + '" role="' + (b.kind === 'error' ? 'alert' : 'status') + '">' +
      icon(b.kind === 'error' ? 'alert' : 'info') +
      '<p class="banner-text"><strong>' + esc(b.title) + '</strong>' + esc(b.text) + '</p>' +
      '<button type="button" class="btn btn-ghost icon-btn" data-action="dismiss-banner" aria-label="Dismiss message">' + icon('x') + '</button></div>';
  }

  function renderEmptyApp() {
    el.emptyApp.innerHTML =
      '<section class="hero" aria-labelledby="heroTitle">' +
      '<div class="hero-art">' + icon('compass') + '</div>' +
      '<h1 id="heroTitle">No trips yet</h1>' +
      '<p>Create your first trip to start planning day by day: set the dates, add who is coming, then fill each day with things to do.</p>' +
      '<div class="hero-actions">' +
      '<button type="button" class="btn btn-primary" data-action="new-trip" data-fid="hero-new">' + icon('plus') + 'Create a trip</button>' +
      '<button type="button" class="btn" data-action="import" data-fid="hero-import">' + icon('upload') + 'Import a trip file</button>' +
      '</div>' +
      '<ol class="hero-steps">' +
      '<li><strong>1. Set the dates</strong>Up to 30 days, one column per day.</li>' +
      '<li><strong>2. Add activities</strong>Times, places and costs, with clashes flagged.</li>' +
      '<li><strong>3. Settle up</strong>See who paid what and who owes whom.</li>' +
      '</ol></section>';
  }

  function renderTripHead(trip) {
    const n = diffDays(trip.start, trip.end) + 1;
    el.tripHead.innerHTML =
      '<div class="trip-head-main">' +
      '<p class="eyebrow">Trip itinerary</p>' +
      '<h1 class="trip-title">' + esc(trip.name) + '</h1>' +
      '<div class="trip-meta">' +
      '<span class="meta-item">' + icon('calendar') + esc(fmtRange(trip.start, trip.end)) + '</span>' +
      '<span class="meta-sep" aria-hidden="true"></span>' +
      '<span class="meta-item">' + plural(n, 'day') + '</span>' +
      '<span class="meta-sep" aria-hidden="true"></span>' +
      '<span class="meta-item">' + icon('users') + '<span class="sr-only">Travellers:</span></span>' +
      '<ul class="people">' + trip.travellers.map((p) => '<li class="person"><span class="avatar" aria-hidden="true">' + esc(initials(p.name)) + '</span>' + esc(p.name) + '</li>').join('') + '</ul>' +
      '</div></div>' +
      '<div class="trip-actions">' +
      '<button type="button" class="btn" data-action="edit-trip" data-fid="edit-trip">' + icon('pencil') + 'Edit trip</button>' +
      '<button type="button" class="btn" data-action="export-menu" data-fid="export-menu" aria-haspopup="menu" aria-expanded="false">' + icon('download') + 'Export</button>' +
      '<button type="button" class="btn btn-danger" data-action="delete-trip" data-fid="delete-trip">' + icon('trash') + 'Delete trip</button>' +
      '</div>';
  }

  function matches(a, q) {
    return a.title.toLowerCase().includes(q) || (a.place || '').toLowerCase().includes(q);
  }
  function highlight(text, q) {
    if (!q) return esc(text);
    const lower = text.toLowerCase();
    let out = '', i = 0;
    for (;;) {
      const j = lower.indexOf(q, i);
      if (j < 0) break;
      out += esc(text.slice(i, j)) + '<mark>' + esc(text.slice(j, j + q.length)) + '</mark>';
      i = j + q.length;
    }
    return out + esc(text.slice(i));
  }

  function cardHTML(trip, a, conflicts, q) {
    const cat = catById(a.category);
    const s = toMin(a.start), e = s + a.duration;
    const isMatch = q && matches(a, q);
    const conflict = conflicts && conflicts.get(a.id);
    const payer = trip.travellers.find((p) => p.id === a.paidBy);
    const cost = toCents(a.cost);
    const cid = 'cf-' + a.id;
    return '<li class="card cat-' + cat.id + (conflict ? ' is-conflict' : '') + (isMatch ? ' is-match' : '') + '" draggable="true" data-id="' + esc(a.id) + '">' +
      '<button type="button" class="card-main" data-action="open" data-id="' + esc(a.id) + '" data-fid="open-' + esc(a.id) + '"' +
      (conflict ? ' aria-describedby="' + esc(cid) + '"' : '') + '>' +
      '<span class="card-top"><span class="cat-chip">' + icon(cat.id) + cat.label + '</span>' +
      '<span class="card-time"><span class="sr-only">from </span>' + fmtMin(s) + '<span aria-hidden="true">–</span><span class="sr-only"> to </span>' + fmtEnd(s, e) + '</span>' +
      '</span>' +
      '<span class="card-title">' + highlight(a.title, q) + '</span>' +
      (a.place ? '<span class="card-place">' + icon('pin') + '<span>' + highlight(a.place, q) + '</span></span>' : '') +
      '<span class="card-meta"><span>' + icon('clock') + fmtDur(a.duration) + '</span>' +
      (cost ? '<span class="card-cost">' + icon('wallet') + fmtMoney(cost, trip) + (payer && trip.travellers.length > 1 ? ' · ' + esc(payer.name) : '') + '</span>' : '') +
      (a.notes ? '<span>' + icon('file') + '<span class="sr-only">Has notes</span></span>' : '') +
      (isMatch ? '<span class="match-badge">' + icon('search') + 'Match</span>' : '') + '</span>' +
      '</button>' +
      (conflict ? '<p class="card-conflict" id="' + esc(cid) + '">' + icon('alert') + '<span><span class="sr-only">Time conflict: </span>' + esc(overlapText(conflict)) + '</span></p>' : '') +
      '<button type="button" class="btn btn-ghost icon-btn card-move" data-action="move" data-id="' + esc(a.id) + '" data-fid="move-' + esc(a.id) + '" aria-haspopup="menu" aria-expanded="false" aria-label="Move ' + esc(a.title) + ' to…" title="Move to…">' + icon('move') + '</button>' +
      '</li>';
  }

  function renderItinerary(trip) {
    const q = ui.search.trim().toLowerCase();
    const days = tripDays(trip);
    let matchCount = 0, matchDays = 0;

    // Unscheduled tray
    const loose = sortActs(trip.activities.filter((a) => !a.day));
    const looseMatches = q ? loose.filter((a) => matches(a, q)).length : 0;
    if (q && looseMatches) { matchCount += looseMatches; matchDays++; }
    const trayCollapsed = q && !looseMatches;
    el.tray.className = 'tray' + (loose.length ? ' has-items' : '');
    let trayBody;
    if (trayCollapsed) {
      trayBody = '<p class="tray-empty">' + (loose.length ? 'No matches here' : 'Empty') + '</p></div>';
    } else if (!loose.length) {
      trayBody = '<p class="tray-empty">Nothing waiting. Drag an activity here to park it without a day.</p></div>';
    } else {
      trayBody = '</div><ol class="tray-list">' + loose.map((a) => cardHTML(trip, a, null, q)).join('') + '</ol>';
    }
    el.tray.innerHTML =
      '<div class="tray-head"><h2 id="trayTitle" tabindex="-1" data-fid="tray-title">' + icon('inbox') + 'Unscheduled <span class="count">' + loose.length + '</span></h2>' +
      trayBody +
      (ui.trayNotice ? '<p class="inline-warn tray-notice" role="status">' + icon('info') + '<span>' + esc(ui.trayNotice) + '</span>' +
        '</p>' : '');
    el.tray.dataset.drop = '';
    el.tray.dataset.day = '';

    // Day columns
    el.board.innerHTML = days.map((d) => {
      const acts = sortActs(trip.activities.filter((a) => a.day === d.iso));
      const conflicts = conflictsFor(acts);
      const dayCost = acts.reduce((s, a) => s + toCents(a.cost), 0);
      const nMatch = q ? acts.filter((a) => matches(a, q)).length : 0;
      if (q && nMatch) { matchCount += nMatch; matchDays++; }
      const collapsed = q && !nMatch;
      const head = '<header class="day-head"><h3 id="dh-' + d.iso + '"><span class="day-num">' + d.num + '</span><span class="day-date">' + d.date + '</span></h3>' +
        (collapsed ? '' : '<span class="day-sum">' + plural(acts.length, 'activity', 'activities') + (dayCost ? '<br>' + fmtMoney(dayCost, trip) : '') +
          (conflicts.size ? '<br><span class="sr-only">Has time conflicts</span>' : '') + '</span>') + '</header>';
      if (collapsed) {
        return '<section class="day is-collapsed" aria-labelledby="dh-' + d.iso + '" data-drop data-day="' + d.iso + '">' + head +
          '<p class="collapsed-note">' + icon('eyeOff', 'icon-sm') + ' No matches</p></section>';
      }
      const list = acts.length
        ? acts.map((a) => cardHTML(trip, a, conflicts, q)).join('')
        : '<li class="empty">' + icon('sun') + '<strong>A free day</strong>Add an activity, or drag one here from another day.</li>';
      return '<section class="day" aria-labelledby="dh-' + d.iso + '">' + head +
        '<ol class="day-list" data-drop data-day="' + d.iso + '">' + list + '</ol>' +
        '<button type="button" class="btn btn-ghost day-add" data-action="add" data-day="' + d.iso + '" data-fid="add-' + d.iso + '">' + icon('plus') + 'Add activity<span class="sr-only"> to ' + d.num + '</span></button>' +
        '</section>';
    }).join('');

    // Search status
    el.searchClear.hidden = !ui.search;
    if (!q) {
      const total = trip.activities.length;
      el.searchStatus.innerHTML = total ? plural(total, 'activity', 'activities') + ' planned' : 'No activities yet. Add one to get started.';
    } else if (!matchCount) {
      el.searchStatus.innerHTML = 'Nothing matches <strong>“' + esc(ui.search.trim()) + '”</strong>. Try a different title or place.';
    } else {
      el.searchStatus.innerHTML = '<strong>' + plural(matchCount, 'match', 'matches') + '</strong> in ' + plural(matchDays, 'day') + (looseMatches ? ' (incl. Unscheduled)' : '');
    }
  }

  function renderBudget(trip) {
    const b = computeBudget(trip);
    const head = '<div class="budget-head"><h2 id="budgetTitle">' + icon('wallet') + 'Budget</h2></div>';
    if (!b.total) {
      el.budget.innerHTML = head +
        '<div class="empty">' + icon('wallet') + '<strong>No costs yet</strong>Open an activity and add a cost. Totals, daily spend and who owes whom will appear here.</div>';
      return;
    }
    const catRows = CATEGORIES.filter((c) => b.byCat[c.id]).map((c) => {
      const v = b.byCat[c.id];
      const pct = Math.round((v / b.total) * 100);
      return '<li class="row cat-' + c.id + '"><span class="row-label">' + icon(c.id) + c.label + ' <span class="hint">' + pct + '%</span></span><span class="row-value">' + fmtMoney(v, trip) + '</span>' +
        '<span class="bar" aria-hidden="true"><span style="width:' + Math.max(pct, 2) + '%"></span></span></li>';
    }).join('');
    const dayRows = tripDays(trip).map((d) => {
      const v = b.byDay[d.iso] || 0;
      return '<li class="row' + (v ? '' : ' row-muted') + '"><span class="row-label">' + d.num + ' · ' + d.date + '</span><span class="row-value">' + fmtMoney(v, trip) + '</span></li>';
    }).join('') + (b.byDay[''] ? '<li class="row"><span class="row-label">Unscheduled</span><span class="row-value">' + fmtMoney(b.byDay[''], trip) + '</span></li>' : '');

    let settleHTML;
    if (trip.travellers.length < 2) {
      settleHTML = '<p class="hint">Only one traveller, so there is nothing to settle. Add travellers in Edit trip to split costs.</p>';
    } else {
      settleHTML = '<table class="settle-table"><caption class="sr-only">What each traveller paid and owes</caption><thead><tr><th scope="col">Traveller</th><th scope="col">Paid</th><th scope="col">Share</th><th scope="col">Balance</th></tr></thead><tbody>' +
        b.people.map((p) => '<tr><td>' + esc(p.name) + '</td><td>' + fmtMoney(p.paid, trip) + '</td><td>' + fmtMoney(p.share, trip) + '</td><td class="' + (p.bal > 0 ? 'bal-pos' : p.bal < 0 ? 'bal-neg' : '') + '">' +
          (p.bal > 0 ? '+' + fmtMoney(p.bal, trip) + ' <span class="sr-only">is owed</span>' : p.bal < 0 ? fmtMoney(p.bal, trip) + ' <span class="sr-only">owes</span>' : fmtMoney(0, trip)) + '</td></tr>').join('') +
        '</tbody></table>' +
        (b.transfers.length
          ? '<h3 class="sr-only">Transfers to settle up</h3><ol class="transfers" aria-label="Transfers to settle up">' + b.transfers.map((t) =>
            '<li class="transfer"><span class="transfer-who"><strong>' + esc(t.from.name) + '</strong> pays <strong>' + esc(t.to.name) + '</strong></span>' + icon('arrowRight') + '<span class="transfer-amt">' + fmtMoney(t.amount, trip) + '</span></li>').join('') + '</ol>'
          : '<p class="square">' + icon('check') + 'Everyone is square. No transfers needed.</p>');
    }

    el.budget.innerHTML = head +
      '<div class="total"><p class="total-label">Total</p><p class="total-value">' + fmtMoney(b.total, trip) + '</p>' +
      '<p class="total-sub">' + plural(b.costed, 'activity', 'activities') + ' with a cost' + (trip.travellers.length > 1 ? ' · ' + fmtMoney(Math.round(b.total / trip.travellers.length), trip) + ' per person on average' : '') + '</p></div>' +
      '<section class="budget-section"><h3>By category</h3><ul class="rows">' + catRows + '</ul></section>' +
      '<section class="budget-section"><h3>By day</h3><ul class="rows">' + dayRows + '</ul></section>' +
      '<section class="budget-section"><h3>Settle up</h3>' + settleHTML + '</section>';
  }

  /* ---------- Toasts & banner ---------- */
  function toast(text, opts) {
    opts = opts || {};
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = icon(opts.icon || 'check') + '<span class="toast-text">' + esc(text) + '</span>' +
      (opts.action ? '<button type="button" class="btn btn-ghost btn-sm toast-action">' + esc(opts.action.label) + '</button>' : '') +
      '<button type="button" class="btn btn-ghost icon-btn" aria-label="Dismiss notification">' + icon('x', 'icon-sm') + '</button>';
    const remove = () => {
      if (!t.isConnected) return;
      t.classList.add('is-leaving');
      setTimeout(() => t.remove(), 220);
    };
    if (opts.action) t.querySelector('.toast-action').addEventListener('click', () => { opts.action.run(); remove(); });
    t.lastElementChild.addEventListener('click', remove);
    el.toasts.appendChild(t);
    while (el.toasts.children.length > 2) el.toasts.firstElementChild.remove();
    let timer = setTimeout(remove, opts.long ? 9000 : 5000);
    t.addEventListener('mouseenter', () => clearTimeout(timer));
    t.addEventListener('focusin', () => clearTimeout(timer));
    t.addEventListener('mouseleave', () => { timer = setTimeout(remove, 3000); });
  }
  const undoAction = { label: 'Undo', run: undo };

  /* ---------- Dialog helpers (focus trap + return) ---------- */
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function openDialog(dlg, returnFid, fallbackFid) {
    const active = document.activeElement;
    dlg._returnEl = active;
    dlg._returnFid = returnFid || (active && active.dataset && active.dataset.fid) || null;
    dlg._fallbackFid = fallbackFid || null;
    closeMenu(false);
    dlg.showModal();
    const first = dlg.querySelector('[autofocus]') || dlg.querySelector('.dialog-body ' + FOCUSABLE.split(', ').join(', .dialog-body '));
    if (first) first.focus();
  }

  function wireDialog(dlg) {
    let downOnBackdrop = false;
    dlg.addEventListener('mousedown', (e) => { downOnBackdrop = e.target === dlg; });
    dlg.addEventListener('click', (e) => {
      if (e.target === dlg && downOnBackdrop) dlg.close();
      downOnBackdrop = false;
    });
    dlg.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) dlg.close(); });
    dlg.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;
      const items = $$(FOCUSABLE, dlg).filter((n) => n.offsetParent !== null || n === document.activeElement);
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    dlg.addEventListener('close', () => {
      if (focusFid(dlg._returnFid)) return;
      if (dlg._returnEl && dlg._returnEl.isConnected && dlg._returnEl.offsetParent !== null) { dlg._returnEl.focus(); return; }
      if (focusFid(dlg._fallbackFid)) return;
      $('#main').focus();
    });
  }

  function setError(input, errEl, msg) {
    if (msg) {
      errEl.innerHTML = icon('alert') + '<span>' + esc(msg) + '</span>';
      errEl.hidden = false;
      if (input) input.setAttribute('aria-invalid', 'true');
    } else {
      errEl.hidden = true;
      errEl.innerHTML = '';
      if (input) input.removeAttribute('aria-invalid');
    }
  }

  /* ---------- Activity dialog ---------- */
  let editingId = null;
  const af = {
    title: $('#fTitle'), day: $('#fDay'), start: $('#fStart'), duration: $('#fDuration'), place: $('#fPlace'),
    cost: $('#fCost'), paidBy: $('#fPaidBy'), split: $('#fSplit'), notes: $('#fNotes'),
    eTitle: $('#eTitle'), eStart: $('#eStart'), eCost: $('#eCost'), eSplit: $('#eSplit'),
  };

  function openActivityDialog(actId, defaultDay) {
    const trip = getTrip();
    if (!trip) return;
    const a = actId ? trip.activities.find((x) => x.id === actId) : null;
    if (actId && !a) return;
    editingId = a ? a.id : null;
    $('#actDialogTitle').textContent = a ? a.title : 'New activity';
    $('#actDialogEyebrow').textContent = a ? 'Activity details' : 'Add to your itinerary';
    $('#actSave').textContent = a ? 'Save changes' : 'Add activity';
    $('#actDelete').hidden = !a;
    $('#fCostSym').textContent = currency(trip).sym.trim();

    const day = a ? a.day : (defaultDay === undefined ? trip.start : defaultDay);
    af.day.innerHTML = tripDays(trip).map((d) => '<option value="' + d.iso + '">' + d.num + ' · ' + d.date + '</option>').join('') +
      '<option value="">Unscheduled</option>';
    af.day.value = day || '';
    af.title.value = a ? a.title : '';
    af.start.value = a ? a.start : '09:00';
    af.duration.value = String(a ? a.duration : 60);
    af.place.value = a ? a.place : '';
    af.cost.value = a && a.cost != null ? a.cost.toFixed(2) : '';
    af.notes.value = a ? a.notes : '';
    const cat = a ? a.category : 'sight';
    $$('input[name="category"]', el.actForm).forEach((r) => { r.checked = r.value === cat; });
    af.paidBy.innerHTML = trip.travellers.map((p) => '<option value="' + esc(p.id) + '">' + esc(p.name) + '</option>').join('');
    af.paidBy.value = a ? a.paidBy : trip.travellers[0].id;
    const split = a ? a.split : trip.travellers.map((p) => p.id);
    af.split.innerHTML = trip.travellers.map((p) =>
      '<label class="check"><input type="checkbox" name="split" value="' + esc(p.id) + '"' + (split.includes(p.id) ? ' checked' : '') + '>' +
      '<span><span class="box">' + icon('check') + '</span>' + esc(p.name) + '</span></label>').join('');
    [[af.title, af.eTitle], [af.start, af.eStart], [af.cost, af.eCost], [null, af.eSplit]].forEach(([i, e]) => setError(i, e, null));

    const fallback = a && a.day ? 'add-' + a.day : 'tray-title';
    openDialog(el.actDialog, a ? 'open-' + a.id : null, fallback);
    if (a) af.title.select();
  }

  function submitActivity(e) {
    e.preventDefault();
    const trip = getTrip();
    if (!trip) return;
    const title = af.title.value.trim();
    const start = af.start.value;
    const costRaw = af.cost.value.trim().replace(',', '.');
    const split = $$('input[name="split"]:checked', af.split).map((c) => c.value);
    const errs = [];
    setError(af.title, af.eTitle, title ? null : 'Give the activity a title.');
    if (!title) errs.push(af.title);
    setError(af.start, af.eStart, isTime(start) ? null : 'Pick a start time, for example 09:30.');
    if (!isTime(start)) errs.push(af.start);
    let cost = null;
    if (costRaw) {
      const num = Number(costRaw);
      const bad = !/^\d+(\.\d{1,2})?$/.test(costRaw) || !isFinite(num);
      setError(af.cost, af.eCost, bad ? 'Enter the cost as a number like 12.50, or leave it empty.' : null);
      if (bad) errs.push(af.cost); else cost = Math.round(num * 100) / 100;
    } else setError(af.cost, af.eCost, null);
    setError(null, af.eSplit, split.length ? null : 'Choose at least one person to split the cost with.');
    if (!split.length) errs.push(af.split.querySelector('input'));
    if (errs.length) { errs[0].focus(); return; }

    const data = {
      title, start, cost, split,
      day: af.day.value || null,
      duration: Number(af.duration.value),
      place: af.place.value.trim(),
      category: ($('input[name="category"]:checked', el.actForm) || {}).value || 'other',
      notes: af.notes.value.replace(/\s+$/, ''),
      paidBy: af.paidBy.value,
    };
    const isNew = !editingId;
    const id = editingId || uid();
    commit(() => {
      const t = getTrip();
      if (isNew) t.activities.push(Object.assign({ id }, data));
      else Object.assign(t.activities.find((x) => x.id === id), data);
    });
    if (isNew) el.actDialog._returnFid = 'open-' + id;
    el.actDialog.close();
    toast((isNew ? 'Added “' : 'Saved “') + title + '” · ' + dayLabel(getTrip(), data.day), { action: undoAction });
  }

  function deleteActivityFromDialog() {
    const trip = getTrip();
    const a = trip && trip.activities.find((x) => x.id === editingId);
    if (!a) return;
    if (!window.confirm('Delete “' + a.title + '”? You can undo this afterwards.')) return;
    const fallback = a.day ? 'add-' + a.day : 'tray-title';
    commit(() => { const t = getTrip(); t.activities = t.activities.filter((x) => x.id !== a.id); });
    el.actDialog._returnFid = fallback;
    el.actDialog.close();
    toast('Deleted “' + a.title + '”', { icon: 'trash', action: undoAction });
  }

  /* ---------- Trip dialog ---------- */
  let tripEditingId = null;
  let draftTravellers = [];
  const tf = {
    name: $('#tName'), start: $('#tStart'), end: $('#tEnd'), currency: $('#tCurrency'), list: $('#tTravellers'),
    add: $('#tAddTraveller'), hint: $('#tDaysHint'), warn: $('#tShrinkWarn'),
    eName: $('#eName'), eStart: $('#eStartDate'), eEnd: $('#eEndDate'), eTravellers: $('#eTravellers'),
  };

  function renderTravellerRows(focusIndex) {
    tf.list.innerHTML = draftTravellers.map((p, i) =>
      '<li class="traveller-row">' +
      '<span class="avatar" aria-hidden="true">' + esc(p.name.trim() ? initials(p.name) : String(i + 1)) + '</span>' +
      '<div class="field"><label class="sr-only" for="tp-' + i + '">Traveller ' + (i + 1) + ' name</label>' +
      '<input id="tp-' + i + '" class="input" data-traveller="' + i + '" maxlength="40" autocomplete="off" value="' + esc(p.name) + '" placeholder="Name" aria-describedby="tpe-' + i + '">' +
      '<p class="field-error" id="tpe-' + i + '" hidden></p></div>' +
      '<button type="button" class="btn btn-ghost icon-btn" data-remove-traveller="' + i + '" aria-label="Remove traveller ' + (i + 1) + (p.name.trim() ? ' (' + esc(p.name.trim()) + ')' : '') + '"' + (draftTravellers.length <= 1 ? ' disabled' : '') + '>' + icon('trash') + '</button>' +
      '</li>').join('');
    tf.add.disabled = draftTravellers.length >= MAX_TRAVELLERS;
    tf.add.querySelector('span').textContent = draftTravellers.length >= MAX_TRAVELLERS ? 'Maximum of 8 travellers' : 'Add traveller';
    if (focusIndex != null) { const inp = $('#tp-' + focusIndex); if (inp) inp.focus(); }
  }

  function updateTripHints() {
    const s = tf.start.value, e = tf.end.value;
    tf.warn.hidden = true;
    if (!parseISO(s) || !parseISO(e)) { tf.hint.textContent = ''; return; }
    if (e < s) { tf.hint.textContent = ''; return; }
    const n = diffDays(s, e) + 1;
    tf.hint.textContent = n > MAX_DAYS ? '' : plural(n, 'day') + ': ' + fmtRange(s, e);
    if (tripEditingId && n <= MAX_DAYS) {
      const trip = state.trips.find((t) => t.id === tripEditingId);
      const lost = planDateChange(trip, s, e).moved;
      if (lost) {
        tf.warn.innerHTML = icon('alert') + '<span>' + plural(lost, 'activity', 'activities') + (lost === 1 ? ' falls' : ' fall') + ' outside the new dates and will move to Unscheduled. Nothing is deleted.</span>';
        tf.warn.hidden = false;
      }
    }
  }

  // Returns how activities map onto new dates. A trip moved without changing its length
  // keeps every activity on the same day number; otherwise activities keep their date.
  function planDateChange(trip, start, end) {
    const sameLength = diffDays(start, end) === diffDays(trip.start, trip.end);
    const shift = sameLength ? diffDays(trip.start, start) : 0;
    let moved = 0;
    const map = {};
    trip.activities.forEach((a) => {
      if (!a.day) { map[a.id] = null; return; }
      const d = shift ? addDays(a.day, shift) : a.day;
      if (d < start || d > end) { moved++; map[a.id] = null; } else map[a.id] = d;
    });
    return { moved, map };
  }

  function openTripDialog(tripId) {
    const trip = tripId ? state.trips.find((t) => t.id === tripId) : null;
    tripEditingId = trip ? trip.id : null;
    $('#tripDialogTitle').textContent = trip ? 'Edit trip' : 'New trip';
    $('#tripSave').textContent = trip ? 'Save changes' : 'Create trip';
    tf.name.value = trip ? trip.name : '';
    const start = trip ? trip.start : todayISO();
    tf.start.value = start;
    tf.end.value = trip ? trip.end : addDays(start, 2);
    tf.currency.value = trip ? trip.currency : 'EUR';
    draftTravellers = trip ? trip.travellers.map((p) => ({ id: p.id, name: p.name })) : [{ id: uid(), name: '' }];
    [[tf.name, tf.eName], [tf.start, tf.eStart], [tf.end, tf.eEnd], [null, tf.eTravellers]].forEach(([i, e]) => setError(i, e, null));
    renderTravellerRows();
    updateTripHints();
    openDialog(el.tripDialog, null, trip ? 'edit-trip' : null);
  }

  function submitTrip(e) {
    e.preventDefault();
    const name = tf.name.value.trim();
    const start = tf.start.value, end = tf.end.value;
    const errs = [];
    setError(tf.name, tf.eName, name ? null : 'Give the trip a name.');
    if (!name) errs.push(tf.name);
    const okStart = !!parseISO(start), okEnd = !!parseISO(end);
    setError(tf.start, tf.eStart, okStart ? null : 'Pick the first day of the trip.');
    if (!okStart) errs.push(tf.start);
    let endMsg = null;
    if (!okEnd) endMsg = 'Pick the last day of the trip.';
    else if (okStart && end < start) endMsg = 'The end date can’t be before the start date.';
    else if (okStart && diffDays(start, end) + 1 > MAX_DAYS) endMsg = 'A trip can be at most 30 days. This one is ' + (diffDays(start, end) + 1) + '.';
    setError(tf.end, tf.eEnd, endMsg);
    if (endMsg) errs.push(tf.end);

    const seen = new Map();
    draftTravellers.forEach((p, i) => {
      const input = $('#tp-' + i), err = $('#tpe-' + i);
      const nm = p.name.trim();
      let msg = null;
      if (!nm) msg = 'Enter a name, or remove this row.';
      else if (seen.has(nm.toLowerCase())) msg = '“' + nm + '” is already on the list. Each traveller needs a different name.';
      if (nm) seen.set(nm.toLowerCase(), i);
      setError(input, err, msg);
      if (msg) errs.push(input);
    });
    setError(null, tf.eTravellers, draftTravellers.length ? null : 'Add at least one traveller.');
    if (errs.length) { errs[0].focus(); return; }

    const travellers = draftTravellers.map((p) => ({ id: p.id, name: p.name.trim() }));
    const curr = tf.currency.value;
    if (!tripEditingId) {
      const id = uid();
      ui.search = ''; el.search.value = ''; ui.trayNotice = null;
      el.board.scrollLeft = 0;
      commit(() => {
        state.trips.push({ id, name, start, end, currency: curr, travellers, activities: [] });
        state.currentId = id;
      });
      el.tripDialog._returnFid = 'toolbar-add';
      el.tripDialog.close();
      toast('Created “' + name + '”. Add your first activity.', { action: undoAction });
      return;
    }
    const trip = state.trips.find((t) => t.id === tripEditingId);
    const plan = planDateChange(trip, start, end);
    commit(() => {
      const t = state.trips.find((x) => x.id === tripEditingId);
      const ids = travellers.map((p) => p.id);
      t.name = name; t.start = start; t.end = end; t.currency = curr; t.travellers = travellers;
      t.activities.forEach((a) => {
        a.day = plan.map[a.id];
        if (!ids.includes(a.paidBy)) a.paidBy = ids[0];
        a.split = a.split.filter((x) => ids.includes(x));
        if (!a.split.length) a.split = ids.slice();
      });
      ui.trayNotice = plan.moved ? plural(plan.moved, 'activity', 'activities') + ' moved here because the trip got shorter. Use “Move to…” to give ' + (plan.moved === 1 ? 'it' : 'them') + ' a new day.' : null;
    });
    el.tripDialog.close();
    if (plan.moved) toast(plural(plan.moved, 'activity', 'activities') + ' moved to Unscheduled because the trip got shorter.', { icon: 'inbox', long: true, action: undoAction });
    else toast('Trip updated', { action: undoAction });
  }

  /* ---------- Menus (Move to…, Export) ---------- */
  let openMenuState = null;

  function openMenu(anchor, label, items) {
    closeMenu(false);
    const menu = document.createElement('div');
    menu.className = 'menu';
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', label);
    menu.innerHTML = '<p class="menu-label" aria-hidden="true">' + esc(label) + '</p>' + items.map((it, i) =>
      it.sep ? '<div class="menu-sep" role="separator"></div>'
        : '<button type="button" class="menu-item" role="menuitem" tabindex="-1" data-i="' + i + '"' + (it.disabled ? ' disabled aria-disabled="true"' : '') + '>' +
        (it.icon ? icon(it.icon) : '') + '<span>' + esc(it.label) + '</span>' + (it.note ? '<small>' + esc(it.note) + '</small>' : '') + '</button>').join('');
    document.body.appendChild(menu);
    anchor.setAttribute('aria-expanded', 'true');
    openMenuState = { menu, anchor, items };
    positionMenu();
    const enabled = () => $$('.menu-item:not([disabled])', menu);
    const first = enabled()[0];
    if (first) first.focus();

    menu.addEventListener('click', (e) => {
      const b = e.target.closest('.menu-item');
      if (!b || b.disabled) return;
      const it = items[+b.dataset.i];
      closeMenu(true);
      it.run();
    });
    menu.addEventListener('keydown', (e) => {
      const list = enabled();
      const idx = list.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); list[(idx + 1) % list.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); list[(idx - 1 + list.length) % list.length].focus(); }
      else if (e.key === 'Home') { e.preventDefault(); list[0].focus(); }
      else if (e.key === 'End') { e.preventDefault(); list[list.length - 1].focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeMenu(true); }
      else if (e.key === 'Tab') { e.preventDefault(); closeMenu(true); }
    });
  }

  function positionMenu() {
    if (!openMenuState) return;
    const { menu, anchor } = openMenuState;
    const r = anchor.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight || r.right < 0 || r.left > window.innerWidth) { closeMenu(false); return; }
    const mw = menu.offsetWidth, mh = menu.offsetHeight;
    let left = Math.min(r.right - mw, window.innerWidth - mw - 8);
    if (left < 8) left = 8;
    let top = r.bottom + 6;
    if (top + mh > window.innerHeight - 8) top = Math.max(8, r.top - mh - 6);
    menu.style.left = left + 'px';
    menu.style.top = top + 'px';
  }

  function closeMenu(returnFocus) {
    if (!openMenuState) return;
    const { menu, anchor } = openMenuState;
    openMenuState = null;
    menu.remove();
    anchor.setAttribute('aria-expanded', 'false');
    if (returnFocus && anchor.isConnected) anchor.focus();
  }

  function openMoveMenu(anchor, actId) {
    const trip = getTrip();
    const a = trip.activities.find((x) => x.id === actId);
    if (!a) return;
    const items = tripDays(trip).map((d) => ({
      label: d.num + ' · ' + d.date, icon: 'calendar', disabled: a.day === d.iso, note: a.day === d.iso ? 'Current' : '',
      run: () => moveActivity(actId, d.iso, true),
    }));
    items.push({ sep: true });
    items.push({ label: 'Unscheduled', icon: 'inbox', disabled: !a.day, note: !a.day ? 'Current' : '', run: () => moveActivity(actId, null, true) });
    openMenu(anchor, 'Move “' + a.title + '” to', items);
  }

  function moveActivity(id, day, keyboard) {
    const trip = getTrip();
    const a = trip && trip.activities.find((x) => x.id === id);
    if (!a || (a.day || null) === (day || null)) return;
    if (keyboard) pendingFocus = 'open-' + id;
    commit(() => { getTrip().activities.find((x) => x.id === id).day = day || null; });
    const t = getTrip();
    let msg = 'Moved “' + a.title + '” to ' + dayLabel(t, day);
    if (day) {
      const acts = sortActs(t.activities.filter((x) => x.day === day));
      const c = conflictsFor(acts).get(id);
      if (c) msg += '. It ' + overlapText(c) + '.';
    }
    toast(msg, { icon: 'move', action: undoAction });
  }

  function openExportMenu(anchor) {
    const trip = getTrip();
    const dated = trip.activities.filter((a) => a.day).length;
    openMenu(anchor, 'Export', [
      { label: 'Calendar file (.ics)', icon: 'calendar', note: dated ? plural(dated, 'event') : 'No events', disabled: !dated, run: exportICS },
      { label: 'Trip file (.json)', icon: 'file', run: exportJSON },
    ]);
  }

  /* ---------- Export / import ---------- */
  function slug(s) { return s.toLowerCase().normalize('NFKD').replace(/[^\w\s-]/g, '').trim().replace(/[\s_]+/g, '-').slice(0, 60) || 'trip'; }
  function download(name, text, type) {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name; a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1000);
  }
  function icsEscape(s) { return String(s).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n'); }
  function icsFold(line) {
    const enc = new TextEncoder();
    if (enc.encode(line).length <= 75) return line;
    const out = [];
    let cur = '', bytes = 0;
    for (const ch of line) {
      const b = enc.encode(ch).length;
      if (bytes + b > 75) { out.push(cur); cur = ' ' + ch; bytes = 1 + b; } else { cur += ch; bytes += b; }
    }
    out.push(cur);
    return out.join('\r\n');
  }
  function icsLocal(iso, minutes) {
    const d = addDays(iso, Math.floor(minutes / 1440));
    const m = minutes % 1440;
    return d.replace(/-/g, '') + 'T' + pad(Math.floor(m / 60)) + pad(m % 60) + '00';
  }

  function exportICS() {
    const trip = getTrip();
    const now = new Date();
    const stamp = now.getUTCFullYear() + pad(now.getUTCMonth() + 1) + pad(now.getUTCDate()) + 'T' + pad(now.getUTCHours()) + pad(now.getUTCMinutes()) + pad(now.getUTCSeconds()) + 'Z';
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Wayfare//Trip Planner//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:' + icsEscape(trip.name)];
    const dated = sortActs(trip.activities.filter((a) => a.day)).sort((a, b) => (a.day < b.day ? -1 : a.day > b.day ? 1 : 0));
    dated.forEach((a) => {
      const s = toMin(a.start);
      const desc = [catById(a.category).label];
      if (toCents(a.cost)) desc.push('Cost: ' + fmtMoney(toCents(a.cost), trip));
      if (a.notes) desc.push(a.notes);
      lines.push('BEGIN:VEVENT', 'UID:' + a.id + '-' + trip.id + '@wayfare.local', 'DTSTAMP:' + stamp,
        'DTSTART:' + icsLocal(a.day, s), 'DTEND:' + icsLocal(a.day, s + a.duration),
        'SUMMARY:' + icsEscape(a.title));
      if (a.place) lines.push('LOCATION:' + icsEscape(a.place));
      lines.push('DESCRIPTION:' + icsEscape(desc.join('\n')), 'CATEGORIES:' + icsEscape(catById(a.category).label.toUpperCase()), 'END:VEVENT');
    });
    lines.push('END:VCALENDAR');
    download(slug(trip.name) + '.ics', lines.map(icsFold).join('\r\n') + '\r\n', 'text/calendar;charset=utf-8');
    const skipped = trip.activities.length - dated.length;
    toast('Exported ' + plural(dated.length, 'event') + ' to a calendar file' + (skipped ? '. ' + plural(skipped, 'unscheduled activity', 'unscheduled activities') + ' left out (no day).' : '.'), { icon: 'download', long: !!skipped });
  }

  function exportJSON() {
    const trip = getTrip();
    download(slug(trip.name) + '.json', JSON.stringify({ app: 'wayfare', version: 1, exportedAt: new Date().toISOString(), trip }, null, 2), 'application/json');
    toast('Exported “' + trip.name + '” as a trip file', { icon: 'download' });
  }

  function importFile(file) {
    const reader = new FileReader();
    const fail = (why) => {
      ui.banner = { kind: 'error', title: 'Could not import “' + file.name + '”', text: 'This file can’t be used because ' + why + ' Nothing was changed.' };
      renderBanner();
      const btn = el.banner.querySelector('button');
      if (btn) btn.focus();
    };
    reader.onerror = () => fail('it could not be read.');
    reader.onload = () => {
      let data;
      try { data = JSON.parse(String(reader.result)); } catch (e) { fail('it is not a valid JSON file.'); return; }
      let trip;
      try { trip = normalizeTrip(data && typeof data === 'object' && data.trip ? data.trip : data); } catch (e) { fail(e.message); return; }
      trip.id = uid();
      ui.banner = null;
      ui.search = ''; el.search.value = '';
      commit(() => { state.trips.push(trip); state.currentId = trip.id; });
      toast('Imported “' + trip.name + '” with ' + plural(trip.activities.length, 'activity', 'activities'), { icon: 'upload', action: undoAction });
    };
    reader.readAsText(file);
  }

  /* ---------- Events ---------- */
  function onClick(e) {
    const t = e.target.closest('[data-action]');
    if (!t) return;
    const action = t.dataset.action;
    const trip = getTrip();
    if (openMenuState && openMenuState.anchor === t) { closeMenu(true); return; }
    switch (action) {
      case 'new-trip': openTripDialog(null); break;
      case 'import': el.importFile.click(); break;
      case 'dismiss-banner': ui.banner = null; renderBanner(); el.main.focus(); break;
      case 'edit-trip': openTripDialog(trip.id); break;
      case 'export-menu': openExportMenu(t); break;
      case 'delete-trip': {
        if (!window.confirm('Delete the trip “' + trip.name + '” and all of its activities?')) return;
        const name = trip.name;
        commit(() => {
          const i = state.trips.findIndex((x) => x.id === trip.id);
          state.trips.splice(i, 1);
          const next = state.trips[Math.min(i, state.trips.length - 1)];
          state.currentId = next ? next.id : null;
        });
        ui.trayNotice = null;
        pendingFocus = null;
        if (!focusFid('edit-trip')) focusFid('hero-new');
        toast('Deleted “' + name + '”', { icon: 'trash', action: undoAction });
        break;
      }
      case 'add': openActivityDialog(null, t.dataset.day); break;
      case 'open': openActivityDialog(t.dataset.id); break;
      case 'move': openMoveMenu(t, t.dataset.id); break;
    }
  }

  function wire() {
    el.main = $('#main');
    document.addEventListener('click', onClick);
    document.addEventListener('mousedown', (e) => {
      if (openMenuState && !openMenuState.menu.contains(e.target) && !openMenuState.anchor.contains(e.target)) closeMenu(false);
    });
    window.addEventListener('resize', positionMenu);
    document.addEventListener('scroll', (e) => { if (!openMenuState || !openMenuState.menu.contains(e.target)) positionMenu(); }, { passive: true, capture: true });

    el.newTrip.addEventListener('click', () => openTripDialog(null));
    el.importBtn.addEventListener('click', () => el.importFile.click());
    el.importFile.addEventListener('change', () => {
      const f = el.importFile.files && el.importFile.files[0];
      el.importFile.value = '';
      if (f) importFile(f);
    });
    el.undo.addEventListener('click', undo);
    el.redo.addEventListener('click', redo);
    el.tripSelect.addEventListener('change', () => {
      state.currentId = el.tripSelect.value;
      ui.search = ''; el.search.value = ''; ui.trayNotice = null;
      save();
      render();
      el.board.scrollLeft = 0;
    });
    el.addActivity.addEventListener('click', () => {
      const trip = getTrip();
      if (trip) openActivityDialog(null, trip.start);
    });

    el.search.addEventListener('input', () => { ui.search = el.search.value; const trip = getTrip(); if (trip) renderItinerary(trip); });
    el.search.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && el.search.value) { e.preventDefault(); el.search.value = ''; ui.search = ''; renderItinerary(getTrip()); }
    });
    el.searchClear.addEventListener('click', () => { el.search.value = ''; ui.search = ''; renderItinerary(getTrip()); el.search.focus(); });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      const mod = e.ctrlKey || e.metaKey;
      if (!mod || e.altKey) return;
      const k = e.key.toLowerCase();
      if (k !== 'z' && k !== 'y') return;
      if (el.actDialog.open || el.tripDialog.open) return;
      const tg = e.target;
      const textual = tg && (tg.tagName === 'TEXTAREA' || (tg.tagName === 'INPUT' && !/^(checkbox|radio|button|submit|file)$/i.test(tg.type)));
      if (textual && tg.value) return; // let the field undo its own typing
      e.preventDefault();
      if (k === 'y' || e.shiftKey) redo(); else undo();
    });

    // Dialogs
    wireDialog(el.actDialog);
    wireDialog(el.tripDialog);
    el.actForm.addEventListener('submit', submitActivity);
    $('#actDelete').addEventListener('click', deleteActivityFromDialog);
    af.title.addEventListener('input', () => { if (af.title.value.trim()) setError(af.title, af.eTitle, null); });
    af.split.addEventListener('change', () => { if ($$('input:checked', af.split).length) setError(null, af.eSplit, null); });

    el.tripForm.addEventListener('submit', submitTrip);
    tf.start.addEventListener('change', () => {
      if (parseISO(tf.start.value) && (!parseISO(tf.end.value) || tf.end.value < tf.start.value)) tf.end.value = tf.start.value;
      setError(tf.start, tf.eStart, null); updateTripHints();
    });
    tf.end.addEventListener('change', () => { setError(tf.end, tf.eEnd, null); updateTripHints(); });
    tf.start.addEventListener('input', updateTripHints);
    tf.end.addEventListener('input', updateTripHints);
    tf.name.addEventListener('input', () => { if (tf.name.value.trim()) setError(tf.name, tf.eName, null); });
    tf.list.addEventListener('input', (e) => {
      const i = e.target.dataset.traveller;
      if (i == null) return;
      draftTravellers[+i].name = e.target.value;
      const av = e.target.closest('.traveller-row').querySelector('.avatar');
      av.textContent = e.target.value.trim() ? initials(e.target.value) : String(+i + 1);
    });
    tf.list.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.dataset.traveller != null) {
        // Enter in the last name field adds a row instead of submitting
        const i = +e.target.dataset.traveller;
        if (i === draftTravellers.length - 1 && draftTravellers.length < MAX_TRAVELLERS && e.target.value.trim()) {
          e.preventDefault();
          draftTravellers.push({ id: uid(), name: '' });
          renderTravellerRows(draftTravellers.length - 1);
        }
      }
    });
    tf.list.addEventListener('click', (e) => {
      const b = e.target.closest('[data-remove-traveller]');
      if (!b || draftTravellers.length <= 1) return;
      const i = +b.dataset.removeTraveller;
      draftTravellers.splice(i, 1);
      renderTravellerRows(Math.min(i, draftTravellers.length - 1));
    });
    tf.add.addEventListener('click', () => {
      if (draftTravellers.length >= MAX_TRAVELLERS) return;
      draftTravellers.push({ id: uid(), name: '' });
      renderTravellerRows(draftTravellers.length - 1);
    });

    // Drag and drop
    let dragId = null;
    document.addEventListener('dragstart', (e) => {
      const card = e.target.closest && e.target.closest('.card[draggable="true"]');
      if (!card) return;
      dragId = card.dataset.id;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', dragId);
      closeMenu(false);
      requestAnimationFrame(() => card.classList.add('is-dragging'));
    });
    document.addEventListener('dragend', () => {
      dragId = null;
      $$('.is-dragging').forEach((n) => n.classList.remove('is-dragging'));
      $$('.drop-over').forEach((n) => n.classList.remove('drop-over'));
    });
    const zoneOf = (target) => (target.closest ? target.closest('[data-drop]') : null);
    document.addEventListener('dragover', (e) => {
      if (!dragId) return;
      const z = zoneOf(e.target);
      if (!z) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      $$('.drop-over').forEach((n) => { if (n !== z) n.classList.remove('drop-over'); });
      z.classList.add('drop-over');
    });
    document.addEventListener('dragleave', (e) => {
      const z = zoneOf(e.target);
      if (z && !z.contains(e.relatedTarget)) z.classList.remove('drop-over');
    });
    document.addEventListener('drop', (e) => {
      const z = zoneOf(e.target);
      if (!z || !dragId) return;
      e.preventDefault();
      const id = dragId;
      dragId = null;
      $$('.drop-over').forEach((n) => n.classList.remove('drop-over'));
      moveActivity(id, z.dataset.day || null, false);
    });
  }

  /* ---------- Boot ---------- */
  setupStaticIcons();
  load();
  wire();
  render();
})();
