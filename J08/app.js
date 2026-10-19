(() => {
  'use strict';

  const STORE_KEY = 'r11-trip-planner';
  const HISTORY_LIMIT = 20;
  const MAX_DAYS = 30;
  const MAX_TRAVELLERS = 8;
  const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
  const CATEGORIES = [
    { id: 'food', label: 'Food' },
    { id: 'sight', label: 'Sight' },
    { id: 'transport', label: 'Transport' },
    { id: 'stay', label: 'Stay' },
    { id: 'other', label: 'Other' },
  ];
  const CAT_IDS = CATEGORIES.map(c => c.id);
  const catLabel = id => (CATEGORIES.find(c => c.id === id) || CATEGORIES[4]).label;
  const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CAD', 'AUD', 'SEK', 'NOK', 'DKK'];

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const els = {
    tripSwitch: $('#tripSwitch'), tripSelect: $('#tripSelect'),
    undo: $('#undoBtn'), redo: $('#redoBtn'),
    banner: $('#banner'), importError: $('#importError'), importFile: $('#importFile'),
    emptyApp: $('#emptyApp'), tripView: $('#tripView'), tripHead: $('#tripHead'),
    search: $('#search'), searchClear: $('.search-clear'), searchStatus: $('#searchStatus'),
    tray: $('#tray'), board: $('#board'), budget: $('#budget'),
    toasts: $('#toasts'), menu: $('#moveMenu'),
    tripDialog: $('#tripDialog'), actDialog: $('#activityDialog'),
  };

  let data = { trips: [], currentTripId: null };
  let past = [];
  let future = [];
  const ui = { search: '', banner: '', importError: '' };

  /* ---------- Small helpers ---------- */
  const pad = n => String(n).padStart(2, '0');
  const uid = () => Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const icon = (name, cls = '') => `<svg class="icon ${cls}" aria-hidden="true" focusable="false"><use href="#i-${name}"></use></svg>`;
  const count = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  const initials = name => name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('') || '?';
  const byKey = key => key ? document.querySelector(`[data-key="${CSS.escape(key)}"]`) : null;

  /* ---------- Dates & times (dates are YYYY-MM-DD, handled in UTC to avoid DST drift) ---------- */
  function parseISO(s) {
    if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
    const [y, m, d] = s.split('-').map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d));
    return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d ? dt : null;
  }
  const toISO = dt => dt.toISOString().slice(0, 10);
  function addDays(s, n) { const d = parseISO(s); d.setUTCDate(d.getUTCDate() + n); return toISO(d); }
  const dayDiff = (a, b) => Math.round((parseISO(b) - parseISO(a)) / 864e5);
  const dayCount = (start, end) => dayDiff(start, end) + 1;
  const tripDays = t => Array.from({ length: Math.max(0, dayCount(t.start, t.end)) }, (_, i) => addDays(t.start, i));
  const fmtDay = s => parseISO(s).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' });
  function fmtRange(t) {
    const year = s => parseISO(s).getUTCFullYear();
    if (t.start === t.end) return `${fmtDay(t.start)} ${year(t.end)}`;
    const left = fmtDay(t.start) + (year(t.start) !== year(t.end) ? ` ${year(t.start)}` : '');
    return `${left} – ${fmtDay(t.end)} ${year(t.end)}`;
  }
  function todayISO() { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
  const toMin = hhmm => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };
  const fmtMin = min => { const m = ((min % 1440) + 1440) % 1440; return `${pad(Math.floor(m / 60))}:${pad(m % 60)}`; };
  const endOf = a => toMin(a.start) + a.duration;
  const timeRange = a => `${a.start}-${fmtMin(endOf(a))}`;
  function fmtDuration(min) {
    const h = Math.floor(min / 60), m = min % 60;
    return h && m ? `${h} h ${m} min` : h ? `${h} h` : `${m} min`;
  }

  /* ---------- Money (stored as integer cents) ---------- */
  const fmtCache = {};
  function money(cents, currency = 'EUR') {
    try {
      fmtCache[currency] ||= new Intl.NumberFormat('en-GB', { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 });
      return fmtCache[currency].format((cents || 0) / 100);
    } catch { return ((cents || 0) / 100).toFixed(2); }
  }
  function currencySymbol(currency) {
    try { return new Intl.NumberFormat('en-GB', { style: 'currency', currency }).formatToParts(0).find(p => p.type === 'currency').value; }
    catch { return currency; }
  }

  /* ---------- Trip helpers ---------- */
  const currentTrip = () => data.trips.find(t => t.id === data.currentTripId) || null;
  const findAct = (trip, id) => trip.activities.find(a => a.id === id);
  const travName = (trip, id) => (trip.travellers.find(t => t.id === id) || {}).name || 'Unknown';
  function dayLabel(trip, date) {
    if (!date) return 'Unscheduled';
    return `Day ${tripDays(trip).indexOf(date) + 1} (${fmtDay(date)})`;
  }
  function sortActs(list) {
    return list.slice().sort((a, b) => toMin(a.start) - toMin(b.start) || a.duration - b.duration || a.title.localeCompare(b.title));
  }
  function conflictsFor(sorted) {
    const map = new Map(sorted.map(a => [a.id, []]));
    for (let i = 0; i < sorted.length; i++) {
      for (let j = i + 1; j < sorted.length; j++) {
        const a = sorted[i], b = sorted[j];
        if (toMin(b.start) >= endOf(a)) continue;
        if (toMin(a.start) < endOf(b) && toMin(b.start) < endOf(a)) {
          map.get(a.id).push(b);
          map.get(b.id).push(a);
        }
      }
    }
    return map;
  }
  const actsOn = (trip, date) => sortActs(trip.activities.filter(a => (a.date || null) === (date || null)));
  function nextFreeStart(trip, date) {
    const acts = date ? actsOn(trip, date) : [];
    if (!acts.length) return '09:00';
    const end = Math.max(...acts.map(endOf));
    const rounded = Math.ceil(end / 15) * 15;
    return rounded <= 22 * 60 ? fmtMin(rounded) : '09:00';
  }

  /* ---------- Budget & settle-up ---------- */
  function computeBudget(trip) {
    const ids = trip.travellers.map(t => t.id);
    const paid = Object.fromEntries(ids.map(id => [id, 0]));
    const share = Object.fromEntries(ids.map(id => [id, 0]));
    const byCat = Object.fromEntries(CAT_IDS.map(c => [c, 0]));
    const byDay = {};
    let total = 0;
    trip.activities.forEach((a, n) => {
      const c = a.costCents;
      if (!c) return;
      total += c;
      byCat[a.category] += c;
      byDay[a.date || ''] = (byDay[a.date || ''] || 0) + c;
      const payer = ids.includes(a.paidBy) ? a.paidBy : ids[0];
      let split = ids.filter(id => (a.splitBetween || []).includes(id));
      if (!split.length) split = ids.slice();
      paid[payer] += c;
      const base = Math.floor(c / split.length);
      const rest = c - base * split.length;
      // leftover cents rotate between people so nobody always absorbs them
      split.forEach((id, k) => { share[id] += base + ((k - n % split.length + split.length) % split.length < rest ? 1 : 0); });
    });
    const rows = trip.travellers.map(t => ({ id: t.id, name: t.name, paid: paid[t.id], share: share[t.id], net: paid[t.id] - share[t.id] }));
    return { total, byCat, byDay, rows, transfers: minTransfers(rows) };
  }

  // Fewest transfers: split people into the largest number of zero-sum groups (bitmask DP, n <= 8);
  // each group of k people then settles with k-1 transfers.
  function minTransfers(rows) {
    const people = rows.filter(r => r.net !== 0);
    const n = people.length;
    if (!n) return [];
    const N = 1 << n;
    const sum = new Array(N).fill(0);
    for (let m = 1; m < N; m++) {
      const low = m & -m;
      sum[m] = sum[m ^ low] + people[31 - Math.clz32(low)].net;
    }
    const dp = new Array(N).fill(0);
    const pick = new Array(N).fill(-1);
    for (let m = 1; m < N; m++) {
      let best = -1;
      for (let i = 0; i < n; i++) {
        if (m >> i & 1 && dp[m ^ (1 << i)] > best) { best = dp[m ^ (1 << i)]; pick[m] = i; }
      }
      dp[m] = best + (sum[m] === 0 ? 1 : 0);
    }
    const groups = [];
    let cur = [];
    for (let m = N - 1; m;) {
      const i = pick[m];
      cur.push(people[i]);
      m ^= 1 << i;
      if (sum[m] === 0) { groups.push(cur); cur = []; }
    }
    const transfers = [];
    groups.forEach(g => {
      const debtors = g.filter(p => p.net < 0).map(p => ({ ...p, left: -p.net })).sort((a, b) => b.left - a.left);
      const creditors = g.filter(p => p.net > 0).map(p => ({ ...p, left: p.net })).sort((a, b) => b.left - a.left);
      let i = 0, j = 0;
      while (i < debtors.length && j < creditors.length) {
        const amt = Math.min(debtors[i].left, creditors[j].left);
        transfers.push({ from: debtors[i].name, to: creditors[j].name, cents: amt });
        debtors[i].left -= amt;
        creditors[j].left -= amt;
        if (!debtors[i].left) i++;
        if (!creditors[j].left) j++;
      }
    });
    return transfers.sort((a, b) => b.cents - a.cents);
  }

  /* ---------- Validation / normalisation (used for storage and imports) ---------- */
  function validateTrip(t, keepTripId) {
    const fail = msg => { throw new Error(msg); };
    if (!t || typeof t !== 'object' || Array.isArray(t) || !['name', 'start', 'end', 'travellers'].some(k => k in t)) {
      fail('It doesn’t look like a trip exported from this planner.');
    }
    const name = typeof t.name === 'string' ? t.name.trim() : '';
    if (!name) fail('The trip has no name.');
    if (!parseISO(t.start) || !parseISO(t.end)) fail('The trip dates are missing or aren’t real dates.');
    const len = dayCount(t.start, t.end);
    if (len < 1) fail('The trip ends before it starts.');
    if (len > MAX_DAYS) fail(`The trip is longer than ${MAX_DAYS} days.`);
    if (!Array.isArray(t.travellers) || t.travellers.length < 1 || t.travellers.length > MAX_TRAVELLERS) {
      fail(`A trip needs between 1 and ${MAX_TRAVELLERS} travellers.`);
    }
    const idMap = new Map();
    const nameMap = new Map();
    const travellers = t.travellers.map(tr => {
      const raw = typeof tr === 'string' ? tr : (tr && typeof tr.name === 'string' ? tr.name : '');
      const clean = raw.trim().slice(0, 40);
      if (!clean) fail('Every traveller needs a name.');
      if (nameMap.has(clean.toLowerCase())) fail(`The traveller “${clean}” appears twice.`);
      const id = uid();
      nameMap.set(clean.toLowerCase(), id);
      if (tr && typeof tr === 'object' && tr.id != null) idMap.set(String(tr.id), id);
      return { id, name: clean };
    });
    const allIds = travellers.map(x => x.id);
    const mapT = v => (v == null ? null : idMap.get(String(v)) || nameMap.get(String(v).toLowerCase()) || null);
    const days = new Set(tripDays(t));
    const acts = t.activities == null ? [] : t.activities;
    if (!Array.isArray(acts)) fail('The list of activities isn’t valid.');
    if (acts.length > 3000) fail('It has too many activities.');
    const activities = acts.map((a, i) => {
      if (!a || typeof a !== 'object') fail(`Activity ${i + 1} isn’t valid.`);
      const title = typeof a.title === 'string' ? a.title.trim().slice(0, 120) : '';
      if (!title) fail(`Activity ${i + 1} has no title.`);
      const date = a.date == null || a.date === '' ? null : a.date;
      if (date !== null && !days.has(date)) fail(`“${title}” is dated outside the trip.`);
      if (typeof a.start !== 'string' || !TIME_RE.test(a.start)) fail(`“${title}” has an invalid start time.`);
      const d = a.duration;
      if (!Number.isInteger(d) || d < 15 || d > 720 || d % 15) fail(`“${title}” has an invalid duration.`);
      if (!CAT_IDS.includes(a.category)) fail(`“${title}” has an unknown category.`);
      const cost = a.costCents == null ? null : a.costCents;
      if (cost !== null && (!Number.isInteger(cost) || cost < 0 || cost > 1e10)) fail(`“${title}” has an invalid cost.`);
      const split = Array.isArray(a.splitBetween) ? a.splitBetween.map(mapT).filter(Boolean) : [];
      return {
        id: uid(), title, date, start: a.start, duration: d,
        place: typeof a.place === 'string' ? a.place.trim().slice(0, 160) : '',
        category: a.category, costCents: cost,
        notes: typeof a.notes === 'string' ? a.notes.slice(0, 5000) : '',
        paidBy: mapT(a.paidBy) || allIds[0],
        splitBetween: split.length ? allIds.filter(id => split.includes(id)) : allIds.slice(),
      };
    });
    return {
      id: keepTripId && typeof t.id === 'string' && t.id ? t.id : uid(),
      name: name.slice(0, 80), start: t.start, end: t.end,
      currency: CURRENCIES.includes(t.currency) ? t.currency : 'EUR',
      travellers, activities,
    };
  }

  /* ---------- Persistence ---------- */
  function load() {
    let raw;
    try { raw = localStorage.getItem(STORE_KEY); } catch {
      ui.banner = 'This browser is blocking storage, so changes will only last until you close the tab.';
      return;
    }
    if (raw == null) return;
    try {
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.trips)) throw new Error('bad shape');
      const trips = [];
      parsed.trips.forEach(t => { try { trips.push(validateTrip(t, true)); } catch { /* skipped below */ } });
      data = { trips, currentTripId: trips.some(t => t.id === parsed.currentTripId) ? parsed.currentTripId : (trips[0] || {}).id || null };
      if (trips.length < parsed.trips.length) {
        ui.banner = `${count(parsed.trips.length - trips.length, 'saved trip', 'saved trips')} couldn’t be read and ${parsed.trips.length - trips.length === 1 ? 'was' : 'were'} skipped.`;
      }
    } catch {
      data = { trips: [], currentTripId: null };
      ui.banner = 'Your saved trips couldn’t be read, so the planner started empty. Create a trip or import one from a JSON file.';
    }
  }
  function persist() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify({ version: 1, ...data })); }
    catch { toast('Couldn’t save in this browser. Export your trip as JSON to keep it.', 'alert'); }
  }

  /* ---------- History ---------- */
  const snapshot = () => JSON.stringify(data);
  function commit(label, mutate) {
    past.push({ label, state: snapshot() });
    if (past.length > HISTORY_LIMIT) past.shift();
    future = [];
    mutate();
    persist();
    render();
  }
  function travel(from, to, verb) {
    if (!from.length) return;
    closeMenu(false);
    const entry = from.pop();
    to.push({ label: entry.label, state: snapshot() });
    data = JSON.parse(entry.state);
    persist();
    render();
    toast(`${verb}: ${entry.label}`, verb === 'Undid' ? 'undo' : 'redo');
  }
  const undo = () => travel(past, future, 'Undid');
  const redo = () => travel(future, past, 'Redid');

  /* ---------- Rendering ---------- */
  function render() {
    const active = document.activeElement;
    const keyBefore = active && active.dataset ? active.dataset.key : null;
    const inOverlay = active && active.closest && active.closest('dialog, .menu');
    renderChrome();
    const trip = currentTrip();
    els.emptyApp.hidden = !!trip;
    els.tripView.hidden = !trip;
    if (trip) {
      renderTripHead(trip);
      renderTray(trip);
      renderBoard(trip);
      renderBudget(trip);
      renderSearchStatus(trip);
    }
    if (keyBefore && !inOverlay && !active.isConnected) {
      const el = byKey(keyBefore);
      if (el) el.focus({ preventScroll: true });
    }
  }

  function renderChrome() {
    els.tripSwitch.hidden = !data.trips.length;
    els.tripSelect.innerHTML = data.trips
      .map(t => `<option value="${esc(t.id)}"${t.id === data.currentTripId ? ' selected' : ''}>${esc(t.name)}</option>`).join('');
    const u = past[past.length - 1], r = future[future.length - 1];
    els.undo.disabled = !u;
    els.redo.disabled = !r;
    els.undo.title = u ? `Undo “${u.label}” (Ctrl+Z)` : 'Nothing to undo';
    els.redo.title = r ? `Redo “${r.label}” (Shift+Ctrl+Z)` : 'Nothing to redo';
    els.undo.setAttribute('aria-label', u ? `Undo ${u.label}` : 'Undo');
    els.redo.setAttribute('aria-label', r ? `Redo ${r.label}` : 'Redo');
    els.banner.hidden = !ui.banner;
    $('.banner-text', els.banner).textContent = ui.banner;
    els.importError.hidden = !ui.importError;
    $('.banner-text', els.importError).textContent = ui.importError;
  }

  function renderTripHead(trip) {
    const n = dayCount(trip.start, trip.end);
    els.tripHead.innerHTML = `
      <div class="trip-title">
        <p class="eyebrow">${icon('calendar')}<span>${esc(fmtRange(trip))}</span><span aria-hidden="true">·</span><span>${count(n, 'day', 'days')}</span></p>
        <h1 id="tripName" tabindex="-1" data-key="trip-name">${esc(trip.name)}</h1>
        <ul class="travellers" aria-label="Travellers">
          ${trip.travellers.map((t, i) => `<li class="person"><span class="avatar av-${i % 8}" aria-hidden="true">${esc(initials(t.name))}</span>${esc(t.name)}</li>`).join('')}
        </ul>
      </div>
      <div class="trip-actions">
        <button type="button" class="btn btn-secondary" data-action="edit-trip" data-key="edit-trip" title="Rename the trip, change dates or travellers">${icon('edit')}<span>Rename &amp; edit</span></button>
        <button type="button" class="btn btn-secondary" data-action="export-ics" data-key="export-ics">${icon('calendar')}<span>Export .ics</span></button>
        <button type="button" class="btn btn-secondary" data-action="export-json" data-key="export-json">${icon('download')}<span>Export JSON</span></button>
        <button type="button" class="btn btn-danger-quiet" data-action="delete-trip" data-key="delete-trip">${icon('trash')}<span>Delete trip</span></button>
      </div>`;
  }

  const norm = s => s.trim().toLowerCase();
  const isMatch = (a, q) => a.title.toLowerCase().includes(q) || a.place.toLowerCase().includes(q);
  function hl(text, q) {
    if (!q) return esc(text);
    const lower = text.toLowerCase();
    let out = '', i = 0, k;
    while ((k = lower.indexOf(q, i)) !== -1) {
      out += esc(text.slice(i, k)) + `<mark>${esc(text.slice(k, k + q.length))}</mark>`;
      i = k + q.length;
    }
    return out + esc(text.slice(i));
  }

  function cardHTML(trip, a, conflicts, q) {
    const match = q && isMatch(a, q);
    const end = endOf(a);
    const endLabel = fmtMin(end) + (end >= 1440 ? ' (+1 day)' : '');
    const conflictText = conflicts.map(c => `overlaps ${esc(c.title)} <span class="nowrap">${timeRange(c)}</span>`).join('; ');
    const foot = [
      a.place ? `<span>${icon('pin')}<span>${hl(a.place, q)}</span></span>` : '',
      a.costCents != null ? `<span>${icon('wallet')}<span>${money(a.costCents, trip.currency)}</span></span>` : '',
    ].filter(Boolean).join('');
    return `
      <li class="card cat-${a.category}${conflicts.length ? ' has-conflict' : ''}${match ? ' is-match' : ''}" draggable="true" data-id="${a.id}">
        <div class="card-row">
          <span class="cat-chip" aria-hidden="true">${icon(a.category)}</span>
          <div class="card-main">
            <h4 class="card-title"><button type="button" class="card-open" id="t-${a.id}" data-action="open" data-id="${a.id}" data-key="open-${a.id}">${hl(a.title, q)}${match ? '<span class="sr-only"> (matches search)</span>' : ''}</button></h4>
            <p class="card-meta"><span class="time">${a.start}–${endLabel}</span><span aria-hidden="true">·</span><span>${catLabel(a.category)}</span><span class="sr-only">, ${fmtDuration(a.duration)}</span></p>
          </div>
          <button type="button" class="btn btn-icon btn-quiet card-move" data-action="move" data-id="${a.id}" data-key="move-${a.id}"
            aria-haspopup="menu" aria-expanded="false" aria-label="Move to…" aria-describedby="t-${a.id}" title="Move to…">${icon('move')}</button>
        </div>
        ${foot ? `<p class="card-foot">${foot}</p>` : ''}
        ${conflicts.length ? `<p class="conflict">${icon('alert')}<span><span class="sr-only">Time conflict: </span>${conflictText}</span></p>` : ''}
      </li>`;
  }

  function renderTray(trip) {
    const q = norm(ui.search);
    const acts = actsOn(trip, null);
    const shown = q ? acts.filter(a => isMatch(a, q)) : acts;
    let body;
    if (!acts.length) body = '<p class="empty-inline">Nothing waiting here. If you shorten the trip, activities from removed days land in this tray.</p>';
    else if (!shown.length) body = '<p class="empty-inline">No matches in the tray.</p>';
    else body = `<ul class="tray-list">${shown.map(a => cardHTML(trip, a, [], q)).join('')}</ul>`;
    els.tray.innerHTML = `
      <div class="tray-head">
        <h2 id="trayTitle" class="section-title">${icon('inbox')}Unscheduled <span class="count" aria-label="${count(acts.length, 'activity', 'activities')}">${acts.length}</span></h2>
        ${acts.length ? '<p class="tray-hint">Drag onto a day, or use “Move to…” on the card.</p>' : ''}
      </div>
      ${body}`;
  }

  function renderBoard(trip) {
    const q = norm(ui.search);
    els.board.innerHTML = tripDays(trip).map((date, i) => {
      const acts = actsOn(trip, date);
      const conf = conflictsFor(acts);
      const collapsed = q && !acts.some(a => isMatch(a, q));
      const cost = acts.reduce((s, a) => s + (a.costCents || 0), 0);
      const clashes = acts.filter(a => conf.get(a.id).length).length;
      const meta = collapsed ? ['No matches'] : [
        count(acts.length, 'activity', 'activities'),
        cost ? money(cost, trip.currency) : '',
        clashes ? `<span class="clash">${icon('alert')}${count(clashes, 'clash', 'clashes')}</span>` : '',
      ].filter(Boolean);
      let body = '';
      if (!collapsed) {
        body = acts.length
          ? `<ol class="day-list" aria-label="Activities on day ${i + 1}">${acts.map(a => cardHTML(trip, a, conf.get(a.id), q)).join('')}</ol>`
          : '<div class="day-empty"><p><strong>Free day</strong></p><p>Add an activity below, or drag one here.</p></div>';
        body += `<button type="button" class="btn btn-add" data-action="add" data-date="${date}" data-key="add-${date}">${icon('plus')}<span>Add activity<span class="sr-only"> to day ${i + 1}</span></span></button>`;
      }
      return `
        <section class="day${collapsed ? ' is-collapsed' : ''}" data-drop="${date}" aria-labelledby="dh-${date}">
          <header class="day-head">
            <h3 class="day-title" id="dh-${date}"><span class="day-num">Day ${i + 1}</span><span class="day-date">${fmtDay(date)}</span></h3>
            <p class="day-meta">${meta.join('<span aria-hidden="true">·</span>')}</p>
          </header>
          ${body}
        </section>`;
    }).join('');
  }

  function renderSearchStatus(trip) {
    const q = norm(ui.search);
    els.searchClear.hidden = !ui.search;
    if (!q) { els.searchStatus.textContent = ''; return; }
    const hits = trip.activities.filter(a => isMatch(a, q));
    const days = new Set(hits.filter(a => a.date).map(a => a.date)).size;
    const inTray = hits.some(a => !a.date);
    els.searchStatus.textContent = hits.length
      ? `${count(hits.length, 'match', 'matches')} on ${count(days, 'day', 'days')}${inTray ? ' and in Unscheduled' : ''}. Other days are collapsed.`
      : `No activities match “${ui.search.trim()}”. Try another title or place.`;
  }

  function renderBudget(trip) {
    const b = computeBudget(trip);
    const cur = trip.currency;
    const title = `<h2 id="budgetTitle" class="section-title">${icon('wallet')}Budget</h2>`;
    if (!b.total) {
      els.budget.innerHTML = `${title}
        <div class="empty-panel">${icon('wallet', 'empty-icon')}<p><strong>No costs yet</strong></p>
        <p>Add a cost to any activity and you’ll see the total, spend per day and who owes whom.</p></div>`;
      return;
    }
    const maxCat = Math.max(...Object.values(b.byCat));
    const days = tripDays(trip);
    const dayRows = days.map((d, i) => ({ label: `Day ${i + 1} · ${fmtDay(d)}`, v: b.byDay[d] || 0 }));
    if (b.byDay['']) dayRows.push({ label: 'Unscheduled', v: b.byDay[''] });
    const maxDay = Math.max(...dayRows.map(r => r.v));
    const bar = (label, v, max, extra = '') => `
      <li class="bar-row${v ? '' : ' is-zero'}${extra}">
        <span class="bar-label">${label}</span><span class="bar-value">${v ? money(v, cur) : '—'}</span>
        <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${max ? (v / max * 100).toFixed(1) : 0}%"></span></span>
      </li>`;
    const multi = trip.travellers.length > 1;
    els.budget.innerHTML = `${title}
      <div class="budget-total">
        <span class="label">Total</span>
        <strong>${money(b.total, cur)}</strong>
        ${multi ? `<span class="sub">about ${money(Math.round(b.total / trip.travellers.length), cur)} per traveller</span>` : ''}
      </div>
      <section class="budget-section" aria-labelledby="bcat">
        <h3 id="bcat">By category</h3>
        <ul class="bars">${CATEGORIES.map(c => bar(`${icon(c.id)}${c.label}`, b.byCat[c.id], maxCat, ` cat-${c.id}`)).join('')}</ul>
      </section>
      <section class="budget-section" aria-labelledby="bday">
        <h3 id="bday">By day</h3>
        <ul class="bars">${dayRows.map(r => bar(esc(r.label), r.v, maxDay)).join('')}</ul>
      </section>
      <section class="budget-section" aria-labelledby="bsettle">
        <h3 id="bsettle">Settle up</h3>
        <table class="settle">
          <caption class="sr-only">What each traveller paid, their share and their balance</caption>
          <thead><tr><th scope="col">Traveller</th><th scope="col" class="num">Paid</th><th scope="col" class="num">Share</th><th scope="col" class="num">Balance</th></tr></thead>
          <tbody>${b.rows.map(r => `
            <tr><th scope="row">${esc(r.name)}</th><td class="num">${money(r.paid, cur)}</td><td class="num">${money(r.share, cur)}</td>
            <td class="num bal ${r.net > 0 ? 'pos' : r.net < 0 ? 'neg' : ''}">${r.net > 0 ? '+' : r.net < 0 ? '−' : ''}${money(Math.abs(r.net), cur)}<span class="bal-word">${r.net > 0 ? 'gets back' : r.net < 0 ? 'owes' : 'even'}</span></td></tr>`).join('')}
          </tbody>
        </table>
        ${b.transfers.length ? `
          <h3 id="btransfers">${count(b.transfers.length, 'transfer settles', 'transfers settle')} everything</h3>
          <ol class="transfers" aria-labelledby="btransfers">${b.transfers.map(t => `
            <li class="transfer"><span class="who">${esc(t.from)}</span><span class="pays">pays</span>${icon('arrow-right')}<span class="who">${esc(t.to)}</span><strong>${money(t.cents, cur)}</strong></li>`).join('')}
          </ol>` : `<p class="square">${icon('check')}${multi ? 'Everyone is square. No transfers needed.' : 'Solo trip, nothing to settle.'}</p>`}
      </section>`;
  }

  /* ---------- Toasts ---------- */
  function toast(msg, ico = 'check') {
    const el = document.createElement('div');
    el.className = 'toast';
    el.innerHTML = `${icon(ico)}<span></span>`;
    el.lastElementChild.textContent = msg;
    els.toasts.appendChild(el);
    while (els.toasts.children.length > 2) els.toasts.firstElementChild.remove();
    setTimeout(() => { el.classList.add('is-leaving'); setTimeout(() => el.remove(), 250); }, 4500);
  }

  /* ---------- Move ---------- */
  function moveActivity(id, date) {
    const trip = currentTrip();
    const a = trip && findAct(trip, id);
    date = date || null;
    if (!a || (a.date || null) === date) return false;
    commit('Move activity', () => { a.date = date; });
    const t = currentTrip();
    const clash = date ? (conflictsFor(actsOn(t, date)).get(id) || []) : [];
    toast(`Moved “${a.title}” to ${dayLabel(t, date)}${clash.length ? `. It overlaps ${clash.map(c => c.title).join(', ')}` : ''}.`, clash.length ? 'alert' : 'check');
    return true;
  }

  let menuState = null;
  function openMenu(btn) {
    const trip = currentTrip();
    const a = trip && findAct(trip, btn.dataset.id);
    if (!a) return;
    if (menuState && menuState.id === a.id) { closeMenu(true); return; }
    closeMenu(false);
    const items = tripDays(trip).map((d, i) => ({ date: d, label: `Day ${i + 1}`, sub: fmtDay(d) }));
    const item = it => {
      const isCur = (a.date || '') === it.date;
      return `<button type="button" role="menuitem" tabindex="-1" class="menu-item" data-date="${it.date}"${isCur ? ' aria-disabled="true"' : ''}>
        <span class="mi-label">${it.label}</span><span class="mi-sub">${it.sub}</span>${isCur ? `<span class="mi-current">${icon('check')}Current</span>` : ''}</button>`;
    };
    els.menu.innerHTML = `<p class="menu-title" id="menuTitle">Move “${esc(a.title)}” to</p>
      <div role="menu" aria-labelledby="menuTitle">${items.map(item).join('')}<div class="menu-sep" role="separator"></div>${item({ date: '', label: 'Unscheduled', sub: '' })}</div>`;
    els.menu.hidden = false;
    const r = btn.getBoundingClientRect();
    const w = els.menu.offsetWidth, h = els.menu.offsetHeight;
    const left = Math.max(8, Math.min(r.right - w, window.innerWidth - w - 8));
    let top = r.bottom + 6;
    if (top + h > window.innerHeight - 8) top = Math.max(8, r.top - h - 6);
    Object.assign(els.menu.style, { left: `${left}px`, top: `${top}px` });
    btn.setAttribute('aria-expanded', 'true');
    menuState = { id: a.id, btn, key: btn.dataset.key, openedAt: performance.now() };
    const items$ = $$('.menu-item', els.menu);
    (items$.find(b => !b.hasAttribute('aria-disabled')) || items$[0]).focus();
  }
  function closeMenu(returnFocus) {
    if (!menuState) return;
    const { btn, key } = menuState;
    if (els.menu.contains(document.activeElement)) returnFocus = true;
    menuState = null;
    els.menu.hidden = true;
    els.menu.innerHTML = '';
    if (btn.isConnected) btn.setAttribute('aria-expanded', 'false');
    if (returnFocus) (btn.isConnected ? btn : byKey(key) || els.board).focus();
  }
  els.menu.addEventListener('keydown', e => {
    const items = $$('.menu-item', els.menu);
    const i = items.indexOf(document.activeElement);
    const go = n => { e.preventDefault(); items[(n + items.length) % items.length].focus(); };
    if (e.key === 'ArrowDown') go(i + 1);
    else if (e.key === 'ArrowUp') go(i - 1);
    else if (e.key === 'Home') go(0);
    else if (e.key === 'End') go(items.length - 1);
    else if (e.key === 'Escape' || e.key === 'Tab') { e.preventDefault(); closeMenu(true); }
  });
  els.menu.addEventListener('click', e => {
    const it = e.target.closest('.menu-item');
    if (!it || it.getAttribute('aria-disabled') === 'true' || !menuState) return;
    const { id } = menuState;
    closeMenu(false);
    moveActivity(id, it.dataset.date);
    const back = byKey(`move-${id}`);
    if (back) { back.focus(); back.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
  });
  document.addEventListener('pointerdown', e => {
    if (menuState && !els.menu.contains(e.target) && !e.target.closest('.card-move')) closeMenu(false);
  });
  window.addEventListener('resize', () => closeMenu(false));
  document.addEventListener('scroll', e => {
    if (!menuState || performance.now() - menuState.openedAt < 400) return;
    if (!(e.target instanceof Node && els.menu.contains(e.target))) closeMenu(false);
  }, true);

  /* ---------- Dialog plumbing ---------- */
  const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  function focusables(root) {
    return $$(FOCUSABLE, root).filter(el => !el.disabled && el.getClientRects().length && !(el.type === 'radio' && !el.checked && $$(`input[name="${el.name}"]:checked`, root).length));
  }
  function setupDialog(dlg) {
    let downOnBackdrop = false;
    dlg.addEventListener('mousedown', e => { downOnBackdrop = e.target === dlg; });
    dlg.addEventListener('click', e => {
      if (e.target === dlg && downOnBackdrop) dlg.close();
      else if (e.target.closest('[data-close]')) dlg.close();
      downOnBackdrop = false;
    });
    dlg.addEventListener('keydown', e => {
      if (e.key !== 'Tab') return;
      const f = focusables(dlg);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (!dlg.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
      else if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    dlg.addEventListener('close', () => {
      const r = dlg._return || {};
      const target = (r.el && r.el.isConnected ? r.el : null) || byKey(r.key) || byKey(r.fallback)
        || (currentTrip() ? byKey('trip-name') : byKey('empty-title'));
      if (target) target.focus();
      dlg.innerHTML = '';
    });
  }
  function openDialog(dlg, opener, fallback) {
    dlg._return = { el: opener || null, key: opener && opener.dataset ? opener.dataset.key : null, fallback };
    dlg.showModal();
  }
  function setError(input, msg) {
    const err = document.getElementById(input.getAttribute('aria-describedby').split(' ').find(id => id.startsWith('err-')));
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    if (!err) return;
    err.hidden = !msg;
    err.innerHTML = msg ? `${icon('alert')}<span>${esc(msg)}</span>` : '';
  }
  function clearErrorOnInput(form) {
    form.addEventListener('input', e => {
      if (e.target.getAttribute && e.target.getAttribute('aria-invalid') === 'true') setError(e.target, '');
    });
  }

  /* ---------- Trip dialog ---------- */
  const travRowHTML = (t, i) => `
    <div class="trav-row" data-tid="${esc(t.id)}">
      <div class="trav-input">
        <span class="avatar av-${i % 8}" aria-hidden="true">${esc(initials(t.name || '?'))}</span>
        <input class="input" type="text" maxlength="40" autocomplete="off" value="${esc(t.name)}" placeholder="Name" aria-label="Traveller ${i + 1} name" aria-describedby="err-trav-${esc(t.id)}">
        <button type="button" class="btn btn-icon btn-quiet" data-remove aria-label="Remove traveller ${i + 1}">${icon('x')}</button>
      </div>
      <p class="field-error" id="err-trav-${esc(t.id)}" hidden></p>
    </div>`;

  function openTripDialog(mode, opener) {
    const trip = mode === 'edit' ? currentTrip() : null;
    const today = todayISO();
    const t = trip || { name: '', start: today, end: addDays(today, 2), currency: 'EUR', travellers: [{ id: uid(), name: '' }] };
    const dlg = els.tripDialog;
    dlg.innerHTML = `
      <form class="dlg" novalidate>
        <header class="dlg-head">
          <div><p class="eyebrow">${trip ? 'Trip settings' : 'Plan something new'}</p><h2 id="tripDlgTitle">${trip ? 'Edit trip' : 'New trip'}</h2></div>
          <button type="button" class="btn btn-icon btn-quiet" data-close aria-label="Close">${icon('x')}</button>
        </header>
        <div class="dlg-body">
          <div class="field">
            <label for="tf-name">Trip name <span class="req" aria-hidden="true">*</span></label>
            <input class="input" id="tf-name" type="text" maxlength="80" autocomplete="off" required value="${esc(t.name)}" placeholder="e.g. Lisbon long weekend" aria-describedby="err-tf-name">
            <p class="field-error" id="err-tf-name" hidden></p>
          </div>
          <div class="grid-2">
            <div class="field">
              <label for="tf-start">Start date</label>
              <input class="input" id="tf-start" type="date" required value="${t.start}" aria-describedby="err-tf-start">
              <p class="field-error" id="err-tf-start" hidden></p>
            </div>
            <div class="field">
              <label for="tf-end">End date</label>
              <input class="input" id="tf-end" type="date" required value="${t.end}" aria-describedby="err-tf-end tf-length">
              <p class="field-error" id="err-tf-end" hidden></p>
            </div>
          </div>
          <p class="hint" id="tf-length"></p>
          ${trip ? `<label class="check" id="tf-shift-wrap" hidden><input type="checkbox" id="tf-shift"> Shift activities along with the new start date</label>
          <p class="notice" id="tf-impact" role="status" hidden></p>` : ''}
          <div class="field">
            <label for="tf-currency">Currency</label>
            <select class="select" id="tf-currency">${CURRENCIES.map(c => `<option value="${c}"${c === t.currency ? ' selected' : ''}>${c} (${esc(currencySymbol(c))})</option>`).join('')}</select>
          </div>
          <fieldset class="field">
            <legend>Travellers <span class="hint-inline" id="tf-trav-count"></span></legend>
            <div class="trav-list" id="tf-travs">${t.travellers.map(travRowHTML).join('')}</div>
            <div><button type="button" class="btn btn-secondary btn-sm" id="tf-add-trav">${icon('plus')}Add traveller</button></div>
          </fieldset>
        </div>
        <footer class="dlg-foot">
          <span class="spacer"></span>
          <button type="button" class="btn btn-secondary" data-close>Cancel</button>
          <button type="submit" class="btn btn-primary">${trip ? 'Save changes' : 'Create trip'}</button>
        </footer>
      </form>`;
    const form = $('form', dlg);
    const list = $('#tf-travs', form);
    const syncTravs = () => {
      const rows = $$('.trav-row', list);
      rows.forEach((r, i) => {
        $('input', r).setAttribute('aria-label', `Traveller ${i + 1} name`);
        const rm = $('[data-remove]', r);
        rm.disabled = rows.length <= 1;
        rm.setAttribute('aria-label', `Remove traveller ${i + 1}${$('input', r).value.trim() ? ` (${$('input', r).value.trim()})` : ''}`);
        $('.avatar', r).textContent = initials($('input', r).value || '?');
      });
      $('#tf-add-trav', form).disabled = rows.length >= MAX_TRAVELLERS;
      $('#tf-trav-count', form).textContent = rows.length >= MAX_TRAVELLERS ? `${rows.length} of ${MAX_TRAVELLERS}, that’s the maximum` : `${rows.length} of up to ${MAX_TRAVELLERS}, each name once`;
    };
    const syncDates = () => {
      const start = $('#tf-start', form).value, end = $('#tf-end', form).value;
      const len = $('#tf-length', form);
      const ok = parseISO(start) && parseISO(end);
      const n = ok ? dayCount(start, end) : 0;
      len.textContent = !ok ? '' : n < 1 ? 'The end date is before the start date.' : n > MAX_DAYS ? `That’s ${n} days. Trips can be up to ${MAX_DAYS} days.` : `${count(n, 'day', 'days')} in total.`;
      len.classList.toggle('is-bad', ok && (n < 1 || n > MAX_DAYS));
      if (!trip) return;
      const delta = parseISO(start) ? dayDiff(trip.start, start) : 0;
      const wrap = $('#tf-shift-wrap', form);
      wrap.hidden = !delta;
      const shift = delta && $('#tf-shift', form).checked ? delta : 0;
      const impact = $('#tf-impact', form);
      const moved = ok && n >= 1 && n <= MAX_DAYS ? displaced(trip, start, end, shift) : 0;
      impact.hidden = !moved;
      impact.innerHTML = moved ? `${icon('info')}<span>${moved === 1 ? '1 activity falls' : `${moved} activities fall`} outside the new dates and will move to Unscheduled. Nothing is deleted.</span>` : '';
    };
    form.addEventListener('input', e => {
      if (e.target.matches('#tf-start, #tf-end, #tf-shift')) syncDates();
      if (e.target.closest('.trav-row')) syncTravs();
    });
    form.addEventListener('change', e => { if (e.target.matches('#tf-shift, #tf-start, #tf-end')) syncDates(); });
    clearErrorOnInput(form);
    $('#tf-add-trav', form).addEventListener('click', () => {
      const n = $$('.trav-row', list).length;
      if (n >= MAX_TRAVELLERS) return;
      list.insertAdjacentHTML('beforeend', travRowHTML({ id: uid(), name: '' }, n));
      syncTravs();
      $('input', list.lastElementChild).focus();
    });
    list.addEventListener('click', e => {
      const rm = e.target.closest('[data-remove]');
      if (!rm || rm.disabled) return;
      const row = rm.closest('.trav-row');
      const next = row.nextElementSibling || row.previousElementSibling;
      row.remove();
      syncTravs();
      if (next) $('input', next).focus();
    });
    form.addEventListener('submit', e => { e.preventDefault(); saveTrip(form, trip); });
    syncTravs();
    syncDates();
    openDialog(dlg, opener);
    $('#tf-name', form).focus();
  }

  function displaced(trip, start, end, shift) {
    const days = new Set(tripDays({ start, end }));
    return trip.activities.filter(a => a.date && !days.has(shift ? addDays(a.date, shift) : a.date)).length;
  }

  function saveTrip(form, trip) {
    const nameEl = $('#tf-name', form), startEl = $('#tf-start', form), endEl = $('#tf-end', form);
    [nameEl, startEl, endEl].forEach(el => setError(el, ''));
    let firstBad = null;
    const bad = (el, msg) => { setError(el, msg); firstBad = firstBad || el; };
    const name = nameEl.value.trim();
    const start = startEl.value, end = endEl.value;
    if (!name) bad(nameEl, 'Give the trip a name.');
    if (!parseISO(start)) bad(startEl, 'Pick the first day of the trip.');
    if (!parseISO(end)) bad(endEl, 'Pick the last day of the trip.');
    else if (parseISO(start)) {
      const n = dayCount(start, end);
      if (n < 1) bad(endEl, 'The end date can’t be before the start date.');
      else if (n > MAX_DAYS) bad(endEl, `Trips can be up to ${MAX_DAYS} days. This one would be ${n}.`);
    }
    const seen = new Set();
    const travellers = $$('.trav-row', form).map(r => {
      const input = $('input', r);
      const value = input.value.trim();
      setError(input, '');
      if (!value) bad(input, 'Type a name, or remove this row.');
      else if (seen.has(value.toLowerCase())) bad(input, `“${value}” is already on the list. Use a different name.`);
      seen.add(value.toLowerCase());
      return { id: r.dataset.tid, name: value };
    });
    if (firstBad) { firstBad.focus(); return; }
    const currency = $('#tf-currency', form).value;
    const dlg = els.tripDialog;

    if (!trip) {
      const t = { id: uid(), name, start, end, currency, travellers, activities: [] };
      commit('Create trip', () => { data.trips.push(t); data.currentTripId = t.id; });
      dlg._return = { key: 'trip-name' };
      dlg.close();
      toast(`Created “${name}”. Add your first activity to any day.`);
      return;
    }
    const shiftBox = $('#tf-shift', form);
    const shift = shiftBox && !$('#tf-shift-wrap', form).hidden && shiftBox.checked ? dayDiff(trip.start, start) : 0;
    const datesChanged = start !== trip.start || end !== trip.end;
    let moved = 0;
    commit(!datesChanged && name !== trip.name ? 'Rename trip' : 'Edit trip', () => {
      const ids = travellers.map(x => x.id);
      const days = new Set(tripDays({ start, end }));
      trip.activities.forEach(a => {
        if (a.date) {
          const d = shift ? addDays(a.date, shift) : a.date;
          if (days.has(d)) a.date = d; else { a.date = null; moved++; }
        }
        if (!ids.includes(a.paidBy)) a.paidBy = ids[0];
        a.splitBetween = ids.filter(id => a.splitBetween.includes(id));
        if (!a.splitBetween.length) a.splitBetween = ids.slice();
      });
      Object.assign(trip, { name, start, end, currency, travellers });
    });
    dlg.close();
    toast(moved
      ? `Trip updated. ${moved === 1 ? '1 activity' : `${moved} activities`} moved to Unscheduled.`
      : 'Trip updated.', moved ? 'inbox' : 'check');
  }

  /* ---------- Activity dialog ---------- */
  function openActivityDialog(id, date, opener) {
    const trip = currentTrip();
    if (!trip) return;
    const days = tripDays(trip);
    const existing = id ? findAct(trip, id) : null;
    if (id && !existing) return;
    const day = date !== undefined ? date : days[0];
    const a = existing || {
      title: '', date: day, start: nextFreeStart(trip, day), duration: 60, place: '', category: 'sight',
      costCents: null, notes: '', paidBy: trip.travellers[0].id, splitBetween: trip.travellers.map(t => t.id),
    };
    const durations = [];
    for (let m = 15; m <= 720; m += 15) durations.push(m);
    const sym = currencySymbol(trip.currency);
    const dlg = els.actDialog;
    dlg.innerHTML = `
      <form class="dlg" novalidate>
        <header class="dlg-head">
          <div><p class="eyebrow">${existing ? esc(dayLabel(trip, a.date)) : 'New activity'}</p><h2 id="actDlgTitle">${existing ? esc(a.title) : 'Add activity'}</h2></div>
          <button type="button" class="btn btn-icon btn-quiet" data-close aria-label="Close">${icon('x')}</button>
        </header>
        <div class="dlg-body">
          <div class="field">
            <label for="af-title">Title <span class="req" aria-hidden="true">*</span></label>
            <input class="input" id="af-title" type="text" maxlength="120" autocomplete="off" required value="${esc(a.title)}" placeholder="e.g. Lunch at Time Out Market" aria-describedby="err-af-title">
            <p class="field-error" id="err-af-title" hidden></p>
          </div>
          <div class="grid-3">
            <div class="field">
              <label for="af-date">Day</label>
              <select class="select" id="af-date">
                ${days.map((d, i) => `<option value="${d}"${d === a.date ? ' selected' : ''}>Day ${i + 1} · ${fmtDay(d)}</option>`).join('')}
                <option value=""${!a.date ? ' selected' : ''}>Unscheduled</option>
              </select>
            </div>
            <div class="field">
              <label for="af-start">Start time</label>
              <input class="input" id="af-start" type="time" required value="${a.start}" aria-describedby="err-af-start">
              <p class="field-error" id="err-af-start" hidden></p>
            </div>
            <div class="field">
              <label for="af-duration">Duration</label>
              <select class="select" id="af-duration">${durations.map(m => `<option value="${m}"${m === a.duration ? ' selected' : ''}>${fmtDuration(m)}</option>`).join('')}</select>
            </div>
          </div>
          <fieldset class="field">
            <legend>Category</legend>
            <div class="cat-picker">${CATEGORIES.map(c => `
              <div class="cat-option cat-${c.id}">
                <input type="radio" name="af-cat" id="af-cat-${c.id}" value="${c.id}"${c.id === a.category ? ' checked' : ''}>
                <label for="af-cat-${c.id}">${icon(c.id)}${c.label}</label>
              </div>`).join('')}
            </div>
          </fieldset>
          <div class="grid-2">
            <div class="field">
              <label for="af-place">Place</label>
              <input class="input" id="af-place" type="text" maxlength="160" autocomplete="off" value="${esc(a.place)}" placeholder="Address or venue">
            </div>
            <div class="field">
              <label for="af-cost">Cost <span class="hint-inline">optional</span></label>
              <div class="input-affix"><span class="affix" aria-hidden="true">${esc(sym)}</span>
                <input class="input" id="af-cost" type="text" inputmode="decimal" autocomplete="off" value="${a.costCents != null ? (a.costCents / 100).toFixed(2) : ''}" placeholder="0.00" aria-describedby="err-af-cost">
              </div>
              <p class="field-error" id="err-af-cost" hidden></p>
            </div>
          </div>
          <div class="field">
            <label for="af-paid">Paid by</label>
            <select class="select" id="af-paid">${trip.travellers.map(t => `<option value="${esc(t.id)}"${t.id === a.paidBy ? ' selected' : ''}>${esc(t.name)}</option>`).join('')}</select>
          </div>
          <fieldset class="field" id="af-split" aria-describedby="err-af-split">
            <legend>Split between <span class="hint-inline">at least one person</span></legend>
            <div class="chips">${trip.travellers.map(t => `
              <div class="chip">
                <input type="checkbox" id="af-split-${esc(t.id)}" value="${esc(t.id)}"${a.splitBetween.includes(t.id) ? ' checked' : ''}>
                <label for="af-split-${esc(t.id)}">${icon('check')}${esc(t.name)}</label>
              </div>`).join('')}
            </div>
            <p class="field-error" id="err-af-split" hidden></p>
          </fieldset>
          <div class="field">
            <label for="af-notes">Notes</label>
            <textarea class="textarea" id="af-notes" rows="4" maxlength="5000" placeholder="Booking reference, opening hours, what to bring…">${esc(a.notes)}</textarea>
          </div>
        </div>
        <footer class="dlg-foot">
          ${existing ? `<button type="button" class="btn btn-danger-quiet" id="af-delete">${icon('trash')}Delete</button>` : ''}
          <span class="spacer"></span>
          <button type="button" class="btn btn-secondary" data-close>Cancel</button>
          <button type="submit" class="btn btn-primary">${existing ? 'Save changes' : 'Add activity'}</button>
        </footer>
      </form>`;
    const form = $('form', dlg);
    clearErrorOnInput(form);
    $('#af-split', form).addEventListener('change', () => {
      const fs = $('#af-split', form);
      if (fs.getAttribute('aria-invalid') === 'true' && $$('input:checked', fs).length) setError(fs, '');
    });
    form.addEventListener('submit', e => { e.preventDefault(); saveActivity(form, existing); });
    const del = $('#af-delete', form);
    if (del) {
      del.addEventListener('click', () => {
        if (!window.confirm(`Delete “${existing.title}”? You can undo this afterwards.`)) return;
        const fallback = existing.date ? `add-${existing.date}` : 'add-toolbar';
        commit('Delete activity', () => { trip.activities = trip.activities.filter(x => x.id !== existing.id); });
        dlg._return = { key: fallback };
        dlg.close();
        toast(`Deleted “${existing.title}”.`, 'trash');
      });
    }
    openDialog(dlg, opener, day ? `add-${day}` : 'add-toolbar');
    $('#af-title', form).focus();
  }

  function saveActivity(form, existing) {
    const trip = currentTrip();
    const titleEl = $('#af-title', form), startEl = $('#af-start', form), costEl = $('#af-cost', form), splitEl = $('#af-split', form);
    let firstBad = null;
    const bad = (el, msg, focusEl) => { setError(el, msg); firstBad = firstBad || focusEl || el; };
    [titleEl, startEl, costEl, splitEl].forEach(el => setError(el, ''));
    const title = titleEl.value.trim();
    if (!title) bad(titleEl, 'Give the activity a title.');
    const start = startEl.value.slice(0, 5);
    if (!TIME_RE.test(start)) bad(startEl, 'Enter a start time, like 09:30.');
    let costCents = null;
    const rawCost = costEl.value.trim().replace(/\s/g, '').replace(',', '.');
    if (rawCost) {
      const v = Number(rawCost);
      if (!/^\d+(\.\d{0,2})?$/.test(rawCost) || !Number.isFinite(v)) bad(costEl, 'Enter an amount like 12.50, or leave it empty.');
      else if (v > 10000000) bad(costEl, 'That amount is too large.');
      else costCents = Math.round(v * 100);
    }
    const split = $$('input:checked', splitEl).map(c => c.value);
    if (!split.length) bad(splitEl, 'Choose at least one person to split the cost with.', $('input', splitEl));
    if (firstBad) { firstBad.focus(); return; }
    const values = {
      title, start, costCents,
      date: $('#af-date', form).value || null,
      duration: Number($('#af-duration', form).value),
      category: ($('input[name="af-cat"]:checked', form) || {}).value || 'other',
      place: $('#af-place', form).value.trim(),
      notes: $('#af-notes', form).value,
      paidBy: $('#af-paid', form).value,
      splitBetween: trip.travellers.map(t => t.id).filter(id => split.includes(id)),
    };
    let id;
    if (existing) {
      id = existing.id;
      commit('Edit activity', () => Object.assign(existing, values));
    } else {
      id = uid();
      commit('Add activity', () => trip.activities.push({ id, ...values }));
    }
    els.actDialog.close();
    const clash = values.date ? conflictsFor(actsOn(trip, values.date)).get(id) || [] : [];
    const where = dayLabel(trip, values.date);
    toast(clash.length
      ? `${existing ? 'Saved' : 'Added'} “${title}”. Heads up: it overlaps ${clash.map(c => c.title).join(', ')}.`
      : `${existing ? 'Saved' : `Added to ${where}:`} “${title}”.`, clash.length ? 'alert' : 'check');
  }

  /* ---------- Import / export ---------- */
  const slug = s => s.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'trip';
  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }
  function exportJSON(trip) {
    download(`${slug(trip.name)}.json`, JSON.stringify({ app: STORE_KEY, version: 1, exportedAt: new Date().toISOString(), trip }, null, 2), 'application/json');
    toast(`Exported “${trip.name}” as JSON.`, 'download');
  }
  const icsText = s => String(s).replace(/\\/g, '\\\\').replace(/\r?\n/g, '\\n').replace(/([,;])/g, '\\$1');
  function fold(line) {
    const enc = new TextEncoder();
    const out = [];
    let cur = '', bytes = 0;
    for (const ch of line) {
      const b = enc.encode(ch).length;
      if (bytes + b > 75) { out.push(cur); cur = ' '; bytes = 1; }
      cur += ch;
      bytes += b;
    }
    out.push(cur);
    return out.join('\r\n');
  }
  function exportICS(trip) {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
    const local = (date, min) => `${addDays(date, Math.floor(min / 1440)).replace(/-/g, '')}T${fmtMin(min).replace(':', '')}00`;
    const scheduled = sortActs(trip.activities.filter(a => a.date)).sort((a, b) => a.date.localeCompare(b.date));
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Wayfare//Trip planner//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', `X-WR-CALNAME:${icsText(trip.name)}`];
    scheduled.forEach(a => {
      const desc = [`Category: ${catLabel(a.category)}`];
      if (a.costCents != null) desc.push(`Cost: ${money(a.costCents, trip.currency)} (paid by ${travName(trip, a.paidBy)})`);
      if (a.notes) desc.push('', a.notes);
      lines.push('BEGIN:VEVENT', `UID:${a.id}@wayfare.trip`, `DTSTAMP:${stamp}`,
        `DTSTART:${local(a.date, toMin(a.start))}`, `DTEND:${local(a.date, endOf(a))}`,
        `SUMMARY:${icsText(a.title)}`);
      if (a.place) lines.push(`LOCATION:${icsText(a.place)}`);
      lines.push(`DESCRIPTION:${icsText(desc.join('\n'))}`, `CATEGORIES:${icsText(catLabel(a.category))}`, 'END:VEVENT');
    });
    lines.push('END:VCALENDAR');
    download(`${slug(trip.name)}.ics`, lines.map(fold).join('\r\n') + '\r\n', 'text/calendar');
    const left = trip.activities.length - scheduled.length;
    toast(`Exported ${count(scheduled.length, 'event', 'events')} to a calendar file${left ? ` (${left} unscheduled left out)` : ''}.`, 'calendar');
  }
  async function importFile(file) {
    const fail = msg => {
      ui.importError = `Couldn’t import “${file.name}”: ${msg} Nothing was changed.`;
      renderChrome();
    };
    if (file.size > 5 * 1024 * 1024) return fail('The file is larger than 5 MB.');
    let text;
    try { text = await file.text(); } catch { return fail('The file couldn’t be read.'); }
    let parsed;
    try { parsed = JSON.parse(text); } catch { return fail('It isn’t a valid JSON file.'); }
    let trip;
    try { trip = validateTrip(parsed && typeof parsed === 'object' && 'trip' in parsed ? parsed.trip : parsed, false); }
    catch (err) { return fail(err.message); }
    ui.importError = '';
    commit('Import trip', () => { data.trips.push(trip); data.currentTripId = trip.id; });
    byKey('trip-name').focus();
    toast(`Imported “${trip.name}” with ${count(trip.activities.length, 'activity', 'activities')}.`, 'upload');
  }

  /* ---------- Events ---------- */
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-action]');
    if (!btn || btn.disabled) return;
    const trip = currentTrip();
    switch (btn.dataset.action) {
      case 'undo': undo(); break;
      case 'redo': redo(); break;
      case 'new-trip': openTripDialog('new', btn); break;
      case 'edit-trip': if (trip) openTripDialog('edit', btn); break;
      case 'delete-trip': {
        if (!trip) break;
        const n = trip.activities.length;
        if (!window.confirm(`Delete “${trip.name}”${n ? ` and its ${count(n, 'activity', 'activities')}` : ''}? You can undo this afterwards.`)) break;
        commit('Delete trip', () => {
          data.trips = data.trips.filter(t => t.id !== trip.id);
          data.currentTripId = (data.trips[0] || {}).id || null;
        });
        (byKey('trip-name') || byKey('empty-title')).focus();
        toast(`Deleted “${trip.name}”.`, 'trash');
        break;
      }
      case 'export-ics': if (trip) exportICS(trip); break;
      case 'export-json': if (trip) exportJSON(trip); break;
      case 'import': els.importFile.value = ''; els.importFile.click(); break;
      case 'add': if (trip) openActivityDialog(null, btn.dataset.date, btn); break;
      case 'open': openActivityDialog(btn.dataset.id, undefined, btn); break;
      case 'move': openMenu(btn); break;
      case 'clear-search': setSearch(''); els.search.focus(); break;
      case 'dismiss-banner': ui.banner = ''; renderChrome(); break;
      case 'dismiss-import-error': ui.importError = ''; renderChrome(); break;
    }
  });

  els.importFile.addEventListener('change', () => {
    const file = els.importFile.files && els.importFile.files[0];
    if (file) importFile(file);
  });
  els.tripSelect.addEventListener('change', () => {
    data.currentTripId = els.tripSelect.value;
    persist();
    render();
  });

  function setSearch(v) {
    ui.search = v;
    if (els.search.value !== v) els.search.value = v;
    const trip = currentTrip();
    if (!trip) return;
    renderTray(trip);
    renderBoard(trip);
    renderSearchStatus(trip);
  }
  els.search.addEventListener('input', () => setSearch(els.search.value));
  els.search.addEventListener('keydown', e => {
    if (e.key === 'Escape' && els.search.value) { e.preventDefault(); setSearch(''); }
  });

  const isTextField = el => el && (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && !['checkbox', 'radio', 'button', 'submit', 'file'].includes(el.type)));
  document.addEventListener('keydown', e => {
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k !== 'z' && k !== 'y') return;
    if (document.querySelector('dialog[open]')) return;
    if (isTextField(e.target) && e.target.value) return; // let the field undo its own typing
    e.preventDefault();
    if (k === 'y' || e.shiftKey) redo(); else undo();
  });

  // Drag and drop between days and the tray
  let dragId = null;
  const clearDrag = () => {
    $$('.is-dragging, .is-drop-target').forEach(el => el.classList.remove('is-dragging', 'is-drop-target'));
    dragId = null;
  };
  document.addEventListener('dragstart', e => {
    const card = e.target instanceof Element && e.target.closest('.card[data-id]');
    if (!card) return;
    closeMenu(false);
    dragId = card.dataset.id;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragId);
    requestAnimationFrame(() => card.classList.add('is-dragging'));
  });
  document.addEventListener('dragover', e => {
    const zone = e.target instanceof Element && e.target.closest('[data-drop]');
    if (!zone) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    $$('.is-drop-target').forEach(z => z !== zone && z.classList.remove('is-drop-target'));
    zone.classList.add('is-drop-target');
  });
  document.addEventListener('dragleave', e => {
    const zone = e.target instanceof Element && e.target.closest('[data-drop]');
    if (zone && !(e.relatedTarget instanceof Node && zone.contains(e.relatedTarget))) zone.classList.remove('is-drop-target');
  });
  document.addEventListener('drop', e => {
    const zone = e.target instanceof Element && e.target.closest('[data-drop]');
    if (!zone) return;
    e.preventDefault();
    const id = dragId || e.dataTransfer.getData('text/plain');
    clearDrag();
    if (id) moveActivity(id, zone.dataset.drop);
  });
  document.addEventListener('dragend', clearDrag);

  /* ---------- Boot ---------- */
  setupDialog(els.tripDialog);
  setupDialog(els.actDialog);
  load();
  render();
})();
