/* Ledgerly — invoice builder. Plain JS, no dependencies. */
(() => {
  'use strict';

  /* ===================== Constants ===================== */
  const KEY = 'r11-invoice-builder';
  const CURRENCIES = {
    USD: { locale: 'en-US', digits: 2, name: 'Dollar' },
    EUR: { locale: 'de-DE', digits: 2, name: 'Euro' },
    GBP: { locale: 'en-GB', digits: 2, name: 'Pound' },
    INR: { locale: 'en-IN', digits: 2, name: 'Rupee' },
    JPY: { locale: 'ja-JP', digits: 0, name: 'Yen' },
  };
  const STATUS = {
    draft: { label: 'Draft', icon: 'draft' },
    sent: { label: 'Sent', icon: 'send' },
    overdue: { label: 'Overdue', icon: 'alert' },
    paid: { label: 'Paid', icon: 'checkCircle' },
  };
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  const ICONS = {
    logo: '<path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10A.5.5 0 0 1 7 20z" /><path d="M10 12h5M10 15.5h5M10 8.5h2"/>',
    file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M15.5 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',
    building: '<path d="M4 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16"/><path d="M15 9h3a2 2 0 0 1 2 2v10M2.5 21h19M8 7.5h3M8 11.5h3M8 15.5h3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    upload: '<path d="M12 16V5M7 10l5-5 5 5M5 20h14"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 .5.5V7"/>',
    edit: '<path d="M4 20h4L19 9a2.83 2.83 0 0 0-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
    grip: '<circle class="fill" cx="9" cy="6" r="1.5"/><circle class="fill" cx="15" cy="6" r="1.5"/><circle class="fill" cx="9" cy="12" r="1.5"/><circle class="fill" cx="15" cy="12" r="1.5"/><circle class="fill" cx="9" cy="18" r="1.5"/><circle class="fill" cx="15" cy="18" r="1.5"/>',
    up: '<path d="m6 15 6-6 6 6"/>',
    down: '<path d="m6 9 6 6 6-6"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    send: '<path d="M21 3 10 14"/><path d="M21 3l-6.5 18-4.5-7-7-4.5z"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    printer: '<path d="M7 9V3.5h10V9"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v6.5H7z"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.01"/>',
    draft: '<circle cx="12" cy="12" r="8.5" stroke-dasharray="3.2 2.6"/>',
    checkCircle: '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 3 3 5-6"/>',
    arrowLeft: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    unlock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.6-1.7"/>',
    lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    filter: '<path d="M4 5h16l-6 8v6l-4-2v-4z"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14.6-4.5L4 8M4 4v4h4M4 13a8 8 0 0 0 14.6 4.5L20 16M20 20v-4h-4"/>',
  };

  /* ===================== Small helpers ===================== */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const nl2br = s => esc(s).replace(/\n/g, '<br>');
  const icon = (n, cls = '') => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[n] || ''}</svg>`;
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const pad = n => String(n).padStart(2, '0');
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

  /* ===================== Dates ===================== */
  const toISO = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const todayISO = () => toISO(new Date());
  function parseISO(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
    if (!m) return null;
    const d = new Date(+m[1], +m[2] - 1, +m[3]);
    return d.getMonth() === +m[2] - 1 && d.getDate() === +m[3] ? d : null;
  }
  const isISO = s => !!parseISO(s);
  function addDays(s, n) { const d = parseISO(s) || new Date(); d.setDate(d.getDate() + n); return toISO(d); }
  const daysBetween = (a, b) => Math.round((parseISO(b) - parseISO(a)) / 86400000);
  const dateFmt = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const fmtDate = s => { const d = parseISO(s); return d ? dateFmt.format(d) : '—'; };
  const timeFmt = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', second: '2-digit' });

  /* ===================== Exact money math ===================== */
  // Decimal strings are parsed into BigInt values scaled by 10^scale — no floats involved.
  function parseNum(raw, scale) {
    const s = String(raw ?? '').trim();
    if (s === '') return { empty: true };
    if (s.startsWith('-')) return { negative: true };
    const m = /^(\d*)(?:\.(\d*))?$/.exec(s);
    if (!m || (!m[1] && !m[2])) return { bad: true };
    const frac = m[2] || '';
    if (frac.length > scale) return { precision: true };
    return { value: BigInt((m[1] || '0') + frac.padEnd(scale, '0')) };
  }
  // Integer division rounding half away from zero.
  function roundDiv(a, b) {
    const neg = a < 0n;
    const x = neg ? -a : a;
    const r = (x * 2n + b) / (2n * b);
    return neg ? -r : r;
  }
  function minorToMajor(minor, digits) {
    const neg = minor < 0n;
    let s = (neg ? -minor : minor).toString();
    if (digits > 0) {
      s = s.padStart(digits + 1, '0');
      s = s.slice(0, -digits) + '.' + s.slice(-digits);
    }
    return (neg ? '-' : '') + s;
  }
  const fmtCache = {};
  function formatter(cur) {
    if (!fmtCache[cur]) {
      const c = CURRENCIES[cur];
      fmtCache[cur] = new Intl.NumberFormat(c.locale, { style: 'currency', currency: cur, minimumFractionDigits: c.digits, maximumFractionDigits: c.digits });
    }
    return fmtCache[cur];
  }
  // Intl accepts exact decimal strings in modern engines; older ones coerce to Number (fine for display).
  const currencySymbol = cur => formatter(cur).formatToParts(0).find(x => x.type === 'currency')?.value || cur;
  const currencyLabel = cur => `${cur} · ${currencySymbol(cur)} ${CURRENCIES[cur].name}`;
  const fmtMoney = (minor, cur) => formatter(cur).format(minorToMajor(minor, CURRENCIES[cur].digits));
  const fmtMajorStr = (str, cur) => formatter(cur).format(String(str).trim() || '0');
  function fmtRate(hundredths) {
    const s = minorToMajor(hundredths, 2).replace(/\.?0+$/, '');
    return `${s}%`;
  }

  function percentError(p, label) {
    if (p.negative) return `${label} can't be negative.`;
    if (p.bad) return 'Use a percentage from 0 to 100.';
    if (p.precision) return 'Use at most 2 decimal places.';
    if (p.value > 10000n) return `${label} can't be more than 100%.`;
    return '';
  }

  // Analyse one line: validation errors plus exact amounts in minor units.
  function analyzeLine(item, cur) {
    const digits = CURRENCIES[cur].digits;
    const e = {};
    if (!String(item.description || '').trim()) e.description = "Describe what you're billing for.";
    const q = parseNum(item.quantity, 2);
    if (q.empty) e.quantity = 'Enter a quantity.';
    else if (q.negative) e.quantity = 'Quantity must be more than 0.';
    else if (q.bad) e.quantity = 'Use a number, like 2 or 1.5.';
    else if (q.precision) e.quantity = 'Use at most 2 decimal places.';
    else if (q.value === 0n) e.quantity = 'Quantity must be more than 0.';
    const p = parseNum(item.unitPrice, 2);
    if (p.empty) e.unitPrice = 'Enter a price (0 is fine).';
    else if (p.negative) e.unitPrice = "Price can't be negative.";
    else if (p.bad) e.unitPrice = 'Use a number, like 120 or 99.50.';
    else if (p.precision || (digits === 0 && p.value % 100n !== 0n)) {
      e.unitPrice = digits === 0 ? `${cur} has no minor unit, so use a whole number.` : 'Use at most 2 decimal places.';
    }
    const dRaw = String(item.discount ?? '').trim() === '' ? { value: 0n } : parseNum(item.discount, 2);
    const dErr = percentError(dRaw, 'Discount');
    if (dErr) e.discount = dErr;
    const tRaw = String(item.taxRate ?? '').trim() === '' ? { value: 0n } : parseNum(item.taxRate, 2);
    const tErr = percentError(tRaw, 'Tax rate');
    if (tErr) e.taxRate = tErr;

    let amounts = null;
    if (!e.quantity && !e.unitPrice && !e.discount && !e.taxRate) {
      // qty (×100) × price (×100) = major ×10^4  →  minor units
      const gross = roundDiv(q.value * p.value, 10n ** BigInt(4 - digits));
      const discount = roundDiv(gross * dRaw.value, 10000n);
      const net = gross - discount;
      const tax = roundDiv(net * tRaw.value, 10000n);
      amounts = { gross, discount, net, tax, rate: tRaw.value };
    }
    return { errors: e, amounts };
  }

  function computeTotals(inv) {
    let subtotal = 0n, discount = 0n, tax = 0n;
    const groups = new Map();
    const lines = {};
    for (const item of inv.items) {
      const a = analyzeLine(item, inv.currency);
      lines[item.id] = a;
      if (!a.amounts) continue;
      const { gross, discount: d, net, tax: t, rate } = a.amounts;
      subtotal += gross; discount += d; tax += t;
      const g = groups.get(rate) || { rate, base: 0n, tax: 0n };
      g.base += net; g.tax += t;
      groups.set(rate, g);
    }
    const taxGroups = [...groups.values()].sort((a, b) => (a.rate < b.rate ? -1 : a.rate > b.rate ? 1 : 0));
    return { lines, subtotal, discount, taxGroups, tax, total: subtotal - discount + tax };
  }

  /* ===================== State & persistence ===================== */
  const str = x => (typeof x === 'string' ? x : '');
  const numStr = (x, def) => (typeof x === 'number' && isFinite(x) ? String(x) : typeof x === 'string' ? x : def);
  const emptyState = () => ({ version: 1, profile: { name: '', address: '', taxId: '', currency: 'USD', taxRate: '0' }, clients: [], invoices: [] });

  // Validates and normalises a stored or imported blob. Throws an Error with a plain-words message.
  function normalizeData(d) {
    const fail = m => { throw new Error(m); };
    if (!d || typeof d !== 'object' || Array.isArray(d)) fail("it doesn't contain invoice data.");
    if (!Array.isArray(d.clients) || !Array.isArray(d.invoices)) fail('it is missing the clients or invoices list.');
    const p = d.profile && typeof d.profile === 'object' ? d.profile : {};
    const profile = {
      name: str(p.name), address: str(p.address), taxId: str(p.taxId),
      currency: CURRENCIES[p.currency] ? p.currency : 'USD',
      taxRate: numStr(p.taxRate, '0'),
    };
    const clientIds = new Set();
    const clients = d.clients.map((c, i) => {
      if (!c || typeof c !== 'object') fail(`client ${i + 1} isn't valid.`);
      if (typeof c.id !== 'string' || !c.id || clientIds.has(c.id)) fail(`client ${i + 1} has a missing or duplicate id.`);
      if (typeof c.name !== 'string' || !c.name.trim()) fail(`client ${i + 1} has no name.`);
      clientIds.add(c.id);
      return { id: c.id, name: c.name, email: str(c.email), address: str(c.address), taxId: str(c.taxId) };
    });
    const invIds = new Set();
    const numbers = new Set();
    const invoices = d.invoices.map((v, i) => {
      if (!v || typeof v !== 'object') fail(`invoice ${i + 1} isn't valid.`);
      const label = typeof v.number === 'string' && v.number ? v.number : `#${i + 1}`;
      if (typeof v.id !== 'string' || !v.id || invIds.has(v.id)) fail(`invoice ${label} has a missing or duplicate id.`);
      invIds.add(v.id);
      if (typeof v.number !== 'string') fail(`invoice ${label} has no number.`);
      const key = v.number.trim().toLowerCase();
      if (key) { if (numbers.has(key)) fail(`invoice number ${v.number} appears twice.`); numbers.add(key); }
      if (!['draft', 'sent', 'paid'].includes(v.status)) fail(`invoice ${label} has an unknown status.`);
      if (!CURRENCIES[v.currency]) fail(`invoice ${label} uses an unsupported currency.`);
      const clientId = str(v.clientId);
      if (clientId && !clientIds.has(clientId)) fail(`invoice ${label} refers to a client that isn't in the data.`);
      for (const f of ['issueDate', 'dueDate', 'paidDate']) {
        if (v[f] != null && v[f] !== '' && !(typeof v[f] === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v[f]))) fail(`invoice ${label} has an invalid ${f}.`);
      }
      if (!Array.isArray(v.items)) fail(`invoice ${label} has no line items list.`);
      const itemIds = new Set();
      const items = v.items.map((it, j) => {
        if (!it || typeof it !== 'object') fail(`line ${j + 1} of invoice ${label} isn't valid.`);
        let id = typeof it.id === 'string' && it.id && !itemIds.has(it.id) ? it.id : uid() + j;
        itemIds.add(id);
        return {
          id, description: str(it.description),
          quantity: numStr(it.quantity, ''), unitPrice: numStr(it.unitPrice, ''),
          discount: numStr(it.discount, '0'), taxRate: numStr(it.taxRate, '0'),
        };
      });
      const from = v.from && typeof v.from === 'object' ? v.from : {};
      return {
        id: v.id, number: v.number, clientId,
        issueDate: str(v.issueDate), dueDate: str(v.dueDate), paidDate: str(v.paidDate),
        currency: v.currency, status: v.status, notes: str(v.notes), items,
        from: { name: str(from.name), address: str(from.address), taxId: str(from.taxId) },
        flagged: v.flagged === true,
        createdAt: str(v.createdAt), updatedAt: str(v.updatedAt),
      };
    });
    return { version: 1, profile, clients, invoices };
  }

  let loadNotice = null;
  function load() {
    let raw;
    try { raw = localStorage.getItem(KEY); }
    catch (e) {
      loadNotice = { kind: 'warn', text: "<strong>Storage is blocked in this browser.</strong> You can still work, but nothing will be kept after you close this tab." };
      return emptyState();
    }
    if (raw == null) {
      loadNotice = { kind: 'info', text: '<strong>Welcome to Ledgerly.</strong> Nothing is saved yet, so you’re starting with an empty workspace. Everything you add is saved in this browser automatically.' };
      return emptyState();
    }
    try { return normalizeData(JSON.parse(raw)); }
    catch (e) {
      loadNotice = { kind: 'warn', text: '<strong>Your saved data couldn’t be read</strong>, so you’re starting with an empty workspace. If you have a JSON backup, import it from Business &amp; data.' };
      return emptyState();
    }
  }

  let state = load();
  let saveOk = true;
  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
      saveOk = true;
      if (loadNotice && loadNotice.kind === 'info') { loadNotice = null; renderNotice(); }
    } catch (e) {
      if (saveOk) toast("Couldn't save: this browser's storage is full or blocked.", 'error');
      saveOk = false;
    }
    return saveOk;
  }

  const getInv = id => state.invoices.find(i => i.id === id);
  const getClient = id => state.clients.find(c => c.id === id);
  const clientName = id => getClient(id)?.name || '';
  const effStatus = (inv, today = todayISO()) => (inv.status === 'sent' && isISO(inv.dueDate) && inv.dueDate < today ? 'overdue' : inv.status);
  const profileSnapshot = () => ({ name: state.profile.name, address: state.profile.address, taxId: state.profile.taxId });
  const numberTaken = (num, exceptId) => {
    const k = num.trim().toLowerCase();
    return !!k && state.invoices.some(i => i.id !== exceptId && i.number.trim().toLowerCase() === k);
  };
  function nextNumber(year) {
    let max = 0;
    for (const inv of state.invoices) {
      const m = /^(\d{4})-(\d+)$/.exec(inv.number.trim());
      if (m && m[1] === year) max = Math.max(max, parseInt(m[2], 10));
    }
    let n = max + 1, num;
    do { num = `${year}-${String(n).padStart(4, '0')}`; n++; } while (numberTaken(num));
    return num;
  }
  const newItem = () => ({ id: uid(), description: '', quantity: '1', unitPrice: '', discount: '0', taxRate: state.profile.taxRate || '0' });

  function validateInvoice(inv, totals = computeTotals(inv)) {
    const e = {};
    if (!inv.number.trim()) e.number = 'Enter an invoice number.';
    else if (numberTaken(inv.number, inv.id)) e.number = `Invoice ${inv.number.trim()} already exists. Pick another number.`;
    if (!inv.clientId || !getClient(inv.clientId)) e.clientId = 'Choose who this invoice is for.';
    if (!isISO(inv.issueDate)) e.issueDate = 'Enter the issue date.';
    if (!isISO(inv.dueDate)) e.dueDate = 'Enter the due date.';
    else if (isISO(inv.issueDate) && inv.dueDate < inv.issueDate) e.dueDate = "Due date can't be before the issue date.";
    if (!inv.items.length) e.items = 'Add at least one line item.';
    for (const item of inv.items) {
      const errs = totals.lines[item.id].errors;
      for (const k of Object.keys(errs)) e[`${item.id}:${k}`] = errs[k];
    }
    return e;
  }

  /* ===================== Feedback: toasts & announcements ===================== */
  function toast(msg, kind = 'success') {
    const region = $('#toasts');
    const el = document.createElement('div');
    el.className = `toast toast-${kind}`;
    el.innerHTML = icon(kind === 'success' ? 'checkCircle' : 'alert') + `<span>${esc(msg)}</span>`;
    region.appendChild(el);
    while (region.children.length > 3) region.firstElementChild.remove();
    setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 260); }, 4200);
  }
  function announce(msg) {
    const a = $('#announcer');
    a.textContent = '';
    setTimeout(() => { a.textContent = msg; }, 40);
  }
  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  /* ===================== Dialogs (focus trap + return) ===================== */
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([tabindex="-1"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  function openDialog(dlg, { returnSel, focus } = {}) {
    dlg._returnEl = document.activeElement;
    dlg._returnSel = returnSel || null;
    dlg.showModal();
    const target = focus || $$(FOCUSABLE, dlg).find(el => el.matches('input, select, textarea')) || $$(FOCUSABLE, dlg)[0];
    target?.focus();
  }
  function setupDialog(dlg) {
    dlg.addEventListener('keydown', e => {
      if (e.key !== 'Tab') return;
      const f = $$(FOCUSABLE, dlg).filter(el => el.offsetParent !== null);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === first || !dlg.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && (document.activeElement === last || !dlg.contains(document.activeElement))) { e.preventDefault(); first.focus(); }
    });
    dlg.addEventListener('mousedown', e => { if (e.target === dlg) dlg.close(); });
    $$('[data-close]', dlg).forEach(b => b.addEventListener('click', () => dlg.close()));
    dlg.addEventListener('close', () => {
      const el = (dlg._returnSel && $(dlg._returnSel)) || dlg._returnEl;
      if (el && el.isConnected && !el.disabled && el !== document.body) el.focus();
      else $('#view h1')?.focus();
    });
  }
  function setFieldError(input, errEl, msg) {
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    errEl.hidden = !msg;
    errEl.innerHTML = msg ? icon('alert') + `<span>${esc(msg)}</span>` : '';
  }

  /* ===================== Router ===================== */
  let current = { view: null, id: null };
  function parseHash() {
    const [view, id] = location.hash.replace(/^#\/?/, '').split('/');
    if (view === 'clients') return { view: 'clients', id: null };
    if (view === 'invoice' && id) return { view: 'invoice', id };
    return { view: 'invoices', id: null };
  }
  function route(initial = false) {
    const next = parseHash();
    const prev = current;
    current = next;
    if (prev.view === 'invoice' && (next.view !== 'invoice' || next.id !== prev.id)) leaveEditor(prev.id);
    if (next.view === 'invoices' && location.hash !== '#/invoices') history.replaceState(null, '', '#/invoices');
    render();
    $$('[data-nav]').forEach(a => {
      const on = a.dataset.nav === next.view || (a.dataset.nav === 'invoices' && next.view === 'invoice');
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    const view = $('#view');
    view.classList.remove('view-enter'); void view.offsetWidth; view.classList.add('view-enter');
    if (!initial) {
      window.scrollTo(0, 0);
      $('#view h1')?.focus({ preventScroll: true });
    }
  }
  function render() {
    document.body.classList.toggle('has-print-doc', current.view === 'invoice');
    if (current.view !== 'invoice') $('#print-doc').innerHTML = '';
    if (current.view === 'clients') renderClients();
    else if (current.view === 'invoice') renderEditor(current.id);
    else renderInvoices();
  }

  function renderNotice() {
    const region = $('#notice-region');
    if (!loadNotice) { region.innerHTML = ''; return; }
    region.innerHTML = `<div class="banner banner-${loadNotice.kind}">${icon(loadNotice.kind === 'warn' ? 'alert' : 'info')}
      <div class="banner-body">${loadNotice.text}</div>
      <div class="banner-actions"><button type="button" class="btn btn-ghost btn-icon" id="dismiss-notice" aria-label="Dismiss message">${icon('x')}</button></div></div>`;
    $('#dismiss-notice').addEventListener('click', () => { loadNotice = null; renderNotice(); $('#view h1')?.focus(); });
  }

  /* ===================== Invoices list ===================== */
  const listState = { filter: 'all', q: '', sort: 'date-desc' };

  function listRows() {
    const today = todayISO();
    return state.invoices.map(inv => ({ inv, status: effStatus(inv, today), client: clientName(inv.clientId), total: computeTotals(inv).total }));
  }
  function shownRows(all) {
    const q = listState.q.trim().toLowerCase();
    let rows = listState.filter === 'all' ? all.slice() : all.filter(r => r.status === listState.filter);
    if (q) rows = rows.filter(r => r.inv.number.toLowerCase().includes(q) || r.client.toLowerCase().includes(q));
    const major = r => Number(r.total) / 10 ** CURRENCIES[r.inv.currency].digits;
    const byDate = (a, b) => (a.inv.issueDate || '').localeCompare(b.inv.issueDate || '') || a.inv.number.localeCompare(b.inv.number);
    const sorters = {
      'date-desc': (a, b) => byDate(b, a),
      'date-asc': byDate,
      'total-desc': (a, b) => major(b) - major(a) || byDate(b, a),
      'total-asc': (a, b) => major(a) - major(b) || byDate(b, a),
    };
    return rows.sort(sorters[listState.sort] || sorters['date-desc']);
  }
  const badge = s => `<span class="badge badge-${s}">${icon(STATUS[s].icon)}${STATUS[s].label}</span>`;

  function renderInvoices() {
    document.title = 'Invoices · Ledgerly';
    const all = listRows();
    const counts = { all: all.length, draft: 0, sent: 0, overdue: 0, paid: 0 };
    all.forEach(r => counts[r.status]++);
    const outstanding = counts.sent + counts.overdue;
    const profileCallout = !state.profile.name.trim() ? `
      <div class="banner banner-info">${icon('building')}
        <div class="banner-body"><strong>Add your business details.</strong> Your name, address and tax ID will appear on every new invoice.</div>
        <div class="banner-actions"><button type="button" class="btn btn-secondary" data-action="open-settings">Set up profile</button></div>
      </div>` : '';
    const segs = ['all', 'draft', 'sent', 'overdue', 'paid'].map(f => `
      <button type="button" class="seg" data-filter="${f}" aria-pressed="${listState.filter === f}">${f === 'all' ? 'All' : STATUS[f].label}<span class="seg-count">${counts[f]}</span></button>`).join('');
    $('#view').innerHTML = `
      <div class="page">
        <div class="page-head">
          <div>
            <p class="eyebrow">Billing</p>
            <h1 tabindex="-1">Invoices</h1>
            <p class="page-sub">${all.length ? `${plural(all.length, 'invoice')} · ${outstanding} awaiting payment${counts.overdue ? `, ${counts.overdue} overdue` : ''}` : 'Create, send and track what you’re owed.'}</p>
          </div>
          <div class="page-actions">
            <button type="button" class="btn btn-secondary" id="export-csv">${icon('download')}<span>Export CSV</span></button>
            <button type="button" class="btn btn-primary" data-action="new-invoice">${icon('plus')}<span>New invoice</span></button>
          </div>
        </div>
        ${profileCallout}
        ${all.length ? `
        <div class="toolbar">
          <div class="segmented" role="group" aria-label="Filter by status">${segs}</div>
          <div class="toolbar-right">
            <div class="search">${icon('search')}<label class="sr-only" for="inv-search">Search by client or number</label>
              <input class="input" type="search" id="inv-search" placeholder="Search client or number" value="${esc(listState.q)}" autocomplete="off"></div>
            <div class="sort"><label class="sr-only" for="inv-sort">Sort invoices</label>
              <select class="input" id="inv-sort">
                <option value="date-desc">Newest first</option><option value="date-asc">Oldest first</option>
                <option value="total-desc">Highest total</option><option value="total-asc">Lowest total</option>
              </select></div>
          </div>
        </div>` : ''}
        <div id="inv-results"></div>
      </div>`;
    const sort = $('#inv-sort');
    if (sort) sort.value = listState.sort;
    renderInvoiceResults(all);

    const view = $('#view');
    $('#inv-search')?.addEventListener('input', e => { listState.q = e.target.value; renderInvoiceResults(); });
    sort?.addEventListener('change', e => { listState.sort = e.target.value; renderInvoiceResults(); });
    $$('.seg', view).forEach(b => b.addEventListener('click', () => {
      listState.filter = b.dataset.filter;
      $$('.seg', view).forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      renderInvoiceResults();
    }));
    $('#export-csv').addEventListener('click', exportCSV);
  }

  function renderInvoiceResults(all = listRows()) {
    const box = $('#inv-results');
    if (!box) return;
    const rows = shownRows(all);
    const exportBtn = $('#export-csv');
    if (exportBtn) {
      exportBtn.disabled = rows.length === 0;
      exportBtn.title = rows.length ? `Download ${plural(rows.length, 'invoice')} as CSV` : 'Nothing to export yet';
    }
    if (!all.length) {
      box.innerHTML = `<div class="card"><div class="empty">
        <div class="empty-art">${icon('file')}</div>
        <h2>No invoices yet</h2>
        <p>${state.clients.length ? 'Create your first invoice. It saves as you type, so you can stop and come back anytime.' : 'Create your first invoice. You can add the client right from the editor, and everything saves as you type.'}</p>
        <button type="button" class="btn btn-primary" data-action="new-invoice">${icon('plus')}<span>New invoice</span></button>
      </div></div>`;
      return;
    }
    if (!rows.length) {
      box.innerHTML = `<div class="card"><div class="empty">
        <div class="empty-art">${icon('filter')}</div>
        <h2>No invoices match</h2>
        <p>Nothing fits ${listState.q.trim() ? `“${esc(listState.q.trim())}”` : 'this filter'}${listState.filter !== 'all' ? ` in ${STATUS[listState.filter].label}` : ''}. Try another search or show all invoices.</p>
        <button type="button" class="btn btn-secondary" data-action="clear-filters">Clear filters</button>
      </div></div>`;
      return;
    }
    const today = todayISO();
    box.innerHTML = `<div class="card table-card"><table class="inv-table">
      <caption class="sr-only">Invoices, ${plural(rows.length, 'result')}</caption>
      <thead><tr><th scope="col">Number</th><th scope="col">Client</th><th scope="col">Issued</th><th scope="col">Due</th><th scope="col" class="num">Total</th><th scope="col">Status</th></tr></thead>
      <tbody>${rows.map(r => {
        const needs = r.inv.flagged && r.inv.status !== 'paid' && Object.keys(validateInvoice(r.inv)).length > 0;
        const dueSoon = r.status === 'overdue' ? ` <span class="sr-only">(${Math.abs(daysBetween(today, r.inv.dueDate))} days late)</span>` : '';
        return `<tr data-id="${esc(r.inv.id)}">
          <td class="c-num" data-label="Number"><a class="row-link" href="#/invoice/${encodeURIComponent(r.inv.id)}">${esc(r.inv.number.trim() || 'Untitled draft')}</a>${needs ? `<span class="attention">${icon('alert')}Needs attention</span>` : ''}</td>
          <td class="c-client" data-label="Client">${r.client ? esc(r.client) : '<span class="client-sub">No client yet</span>'}</td>
          <td class="c-issue" data-label="Issued">${fmtDate(r.inv.issueDate)}</td>
          <td class="c-due" data-label="Due">${fmtDate(r.inv.dueDate)}${dueSoon}</td>
          <td class="c-total num" data-label="Total">${fmtMoney(r.total, r.inv.currency)}</td>
          <td class="c-status" data-label="Status">${badge(r.status)}</td>
        </tr>`;
      }).join('')}</tbody></table></div>`;
    $('tbody', box).addEventListener('click', e => {
      if (e.target.closest('a')) return;
      const tr = e.target.closest('tr[data-id]');
      if (tr) location.hash = `#/invoice/${encodeURIComponent(tr.dataset.id)}`;
    });
  }

  const csvCell = v => (/[",\r\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
  function exportCSV() {
    const rows = shownRows(listRows());
    if (!rows.length) return;
    const lines = ['number,client,issue_date,due_date,currency,total,status'];
    for (const r of rows) {
      lines.push([r.inv.number, r.client, r.inv.issueDate, r.inv.dueDate, r.inv.currency,
        minorToMajor(r.total, CURRENCIES[r.inv.currency].digits), STATUS[r.status].label].map(v => csvCell(String(v))).join(','));
    }
    download(`invoices-${todayISO()}.csv`, lines.join('\r\n') + '\r\n', 'text/csv;charset=utf-8');
    toast(`Exported ${plural(rows.length, 'invoice')} as CSV.`);
  }

  function createInvoice() {
    const t = todayISO();
    const now = new Date().toISOString();
    const inv = {
      id: uid(), number: nextNumber(t.slice(0, 4)),
      clientId: state.clients.length === 1 ? state.clients[0].id : '',
      issueDate: t, dueDate: addDays(t, 14), paidDate: '',
      currency: state.profile.currency, status: 'draft', notes: '',
      items: [newItem()], from: profileSnapshot(), flagged: false, createdAt: now, updatedAt: now,
    };
    state.invoices.push(inv);
    save();
    location.hash = `#/invoice/${inv.id}`;
  }

  /* ===================== Clients ===================== */
  const initials = name => name.trim().split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase() || '?';

  function renderClients() {
    document.title = 'Clients · Ledgerly';
    const usage = id => state.invoices.filter(i => i.clientId === id);
    const sorted = state.clients.slice().sort((a, b) => a.name.localeCompare(b.name));
    $('#view').innerHTML = `
      <div class="page">
        <div class="page-head">
          <div>
            <p class="eyebrow">Directory</p>
            <h1 tabindex="-1">Clients</h1>
            <p class="page-sub">${state.clients.length ? `${plural(state.clients.length, 'client')}` : 'The people and companies you bill.'}</p>
          </div>
          <div class="page-actions">
            <button type="button" class="btn btn-primary" id="add-client">${icon('plus')}<span>Add client</span></button>
          </div>
        </div>
        ${sorted.length ? `<div class="card"><ul class="client-list">${sorted.map(c => {
          const n = usage(c.id).length;
          return `<li class="client" data-id="${esc(c.id)}">
            <span class="avatar" aria-hidden="true">${esc(initials(c.name))}</span>
            <div class="client-info">
              <div class="client-name">${esc(c.name)}</div>
              <div class="client-meta">
                ${c.email ? `<span>${icon('mail')}${esc(c.email)}</span>` : '<span>No email</span>'}
                <span>${icon('file')}${plural(n, 'invoice')}</span>
              </div>
            </div>
            <div class="client-actions">
              <button type="button" class="btn btn-ghost" data-edit-client="${esc(c.id)}">${icon('edit')}<span>Edit</span><span class="sr-only"> ${esc(c.name)}</span></button>
              <button type="button" class="btn btn-ghost btn-danger-ghost" data-delete-client="${esc(c.id)}">${icon('trash')}<span>Delete</span><span class="sr-only"> ${esc(c.name)}</span></button>
            </div>
            <div class="inline-error" id="client-err-${esc(c.id)}" role="alert" hidden></div>
          </li>`;
        }).join('')}</ul></div>` : `
        <div class="card"><div class="empty">
          <div class="empty-art">${icon('users')}</div>
          <h2>No clients yet</h2>
          <p>Add the people or companies you work with, then pick them when you create an invoice.</p>
          <button type="button" class="btn btn-primary" data-action="add-client">${icon('plus')}<span>Add your first client</span></button>
        </div></div>`}
      </div>`;
    const view = $('#view');
    $('#add-client').addEventListener('click', () => openClientDialog(null, { returnSel: '#add-client' }));
    $$('[data-edit-client]', view).forEach(b => b.addEventListener('click', () =>
      openClientDialog(getClient(b.dataset.editClient), { returnSel: `[data-edit-client="${b.dataset.editClient}"]` })));
    $$('[data-delete-client]', view).forEach(b => b.addEventListener('click', () => deleteClient(b.dataset.deleteClient, b)));
  }

  function deleteClient(id, btn) {
    const c = getClient(id);
    if (!c) return;
    $$('.client .inline-error').forEach(el => { el.hidden = true; el.innerHTML = ''; });
    const used = state.invoices.filter(i => i.clientId === id);
    if (used.length) {
      const nums = used.slice(0, 3).map(i => i.number || 'an untitled draft').join(', ') + (used.length > 3 ? ` and ${used.length - 3} more` : '');
      const err = $(`#client-err-${id}`);
      err.innerHTML = `${icon('alert')}<span><strong>${esc(c.name)} can’t be deleted</strong> because ${used.length === 1 ? 'an invoice uses' : `${used.length} invoices use`} them (${esc(nums)}). Delete those invoices or switch them to another client first.</span>`;
      err.hidden = false;
      btn.setAttribute('aria-describedby', err.id);
      return;
    }
    if (!window.confirm(`Delete client “${c.name}”? This can’t be undone.`)) return;
    state.clients = state.clients.filter(x => x.id !== id);
    save();
    renderClients();
    $('#add-client')?.focus();
    toast(`${c.name} deleted.`);
  }

  let clientCtx = {};
  function openClientDialog(client, ctx = {}) {
    clientCtx = { id: client?.id || null, ...ctx };
    $('#client-dialog-title').textContent = client ? 'Edit client' : 'New client';
    $('#client-submit').textContent = client ? 'Save changes' : 'Add client';
    $('#client-name').value = client?.name || '';
    $('#client-email').value = client?.email || '';
    $('#client-address').value = client?.address || '';
    $('#client-taxid').value = client?.taxId || '';
    setFieldError($('#client-name'), $('#client-name-err'), '');
    setFieldError($('#client-email'), $('#client-email-err'), '');
    openDialog($('#client-dialog'), { returnSel: ctx.returnSel });
  }
  const clientNameError = v => (v.trim() ? '' : "Enter the client's name.");
  const clientEmailError = v => (v.trim() && !EMAIL_RE.test(v.trim()) ? 'That email doesn’t look right. Check for a typo, like name@example.com.' : '');

  function setupClientForm() {
    const form = $('#client-form');
    form.addEventListener('input', e => {
      if (e.target.id === 'client-name' && e.target.getAttribute('aria-invalid') === 'true') setFieldError(e.target, $('#client-name-err'), clientNameError(e.target.value));
      if (e.target.id === 'client-email' && e.target.getAttribute('aria-invalid') === 'true') setFieldError(e.target, $('#client-email-err'), clientEmailError(e.target.value));
    });
    form.addEventListener('submit', e => {
      e.preventDefault();
      const name = $('#client-name').value, email = $('#client-email').value;
      const nErr = clientNameError(name), eErr = clientEmailError(email);
      setFieldError($('#client-name'), $('#client-name-err'), nErr);
      setFieldError($('#client-email'), $('#client-email-err'), eErr);
      if (nErr) { $('#client-name').focus(); return; }
      if (eErr) { $('#client-email').focus(); return; }
      const data = { name: name.trim(), email: email.trim(), address: $('#client-address').value.trim(), taxId: $('#client-taxid').value.trim() };
      let saved;
      if (clientCtx.id && getClient(clientCtx.id)) { saved = Object.assign(getClient(clientCtx.id), data); }
      else { saved = { id: uid(), ...data }; state.clients.push(saved); }
      if (clientCtx.onSaved) clientCtx.onSaved(saved);
      save();
      render();
      $('#client-dialog').close();
      toast(clientCtx.id ? 'Client updated.' : `${saved.name} added.`);
    });
  }

  /* ===================== Settings & data ===================== */
  function openSettings(returnSel) {
    const p = state.profile;
    $('#profile-name').value = p.name;
    $('#profile-address').value = p.address;
    $('#profile-taxid').value = p.taxId;
    $('#profile-currency').value = p.currency;
    $('#profile-taxrate').value = p.taxRate;
    setFieldError($('#profile-taxrate'), $('#profile-taxrate-err'), '');
    const ie = $('#import-error'); ie.hidden = true; ie.innerHTML = '';
    openDialog($('#settings-dialog'), { returnSel });
  }
  const taxRateError = v => {
    const p = String(v).trim() === '' ? { value: 0n } : parseNum(v, 2);
    return percentError(p, 'Tax rate');
  };

  function setupSettings() {
    $('#profile-currency').innerHTML = Object.keys(CURRENCIES).map(c => `<option value="${c}">${esc(currencyLabel(c))}</option>`).join('');
    $('#settings-btn').addEventListener('click', () => openSettings('#settings-btn'));
    $('#profile-taxrate').addEventListener('input', e => {
      if (e.target.getAttribute('aria-invalid') === 'true') setFieldError(e.target, $('#profile-taxrate-err'), taxRateError(e.target.value));
    });
    $('#settings-form').addEventListener('submit', e => {
      e.preventDefault();
      const rate = $('#profile-taxrate').value.trim();
      const err = taxRateError(rate);
      setFieldError($('#profile-taxrate'), $('#profile-taxrate-err'), err);
      if (err) { $('#profile-taxrate').focus(); return; }
      state.profile = {
        name: $('#profile-name').value.trim(), address: $('#profile-address').value.trim(),
        taxId: $('#profile-taxid').value.trim(), currency: $('#profile-currency').value, taxRate: rate || '0',
      };
      // Drafts that were created before the profile existed pick it up automatically.
      state.invoices.forEach(inv => { if (inv.status === 'draft' && !inv.from.name.trim()) inv.from = profileSnapshot(); });
      save();
      render();
      $('#settings-dialog').close();
      toast('Business details saved.');
    });
    $('#export-json').addEventListener('click', () => {
      const data = { app: 'ledgerly', version: 1, exportedAt: new Date().toISOString(), ...state };
      download(`ledgerly-backup-${todayISO()}.json`, JSON.stringify(data, null, 2), 'application/json');
      toast('Backup exported.');
    });
    $('#import-json-btn').addEventListener('click', () => $('#import-file').click());
    $('#import-file').addEventListener('change', async e => {
      const file = e.target.files[0];
      e.target.value = '';
      if (!file) return;
      const ie = $('#import-error');
      const showErr = msg => {
        ie.innerHTML = `${icon('alert')}<span><strong>Couldn’t import “${esc(file.name)}”:</strong> ${esc(msg)} Nothing was changed.</span>`;
        ie.hidden = false;
        $('#import-json-btn').focus();
      };
      let data;
      try {
        if (file.size > 20 * 1024 * 1024) throw new Error('the file is too large to be a backup.');
        const text = await file.text();
        let parsed;
        try { parsed = JSON.parse(text); } catch { throw new Error('it isn’t valid JSON.'); }
        data = normalizeData(parsed);
      } catch (err) { showErr(err.message.charAt(0).toUpperCase() + err.message.slice(1)); return; }
      ie.hidden = true;
      if (!window.confirm(`Replace all current data with “${file.name}”? It contains ${plural(data.clients.length, 'client')} and ${plural(data.invoices.length, 'invoice')}.`)) return;
      state = data;
      if (!save()) return;
      loadNotice = null;
      renderNotice();
      ed.id = null;
      if (current.view === 'invoice' && !getInv(current.id)) location.hash = '#/invoices';
      else render();
      $('#settings-dialog').close();
      toast(`Imported ${plural(data.clients.length, 'client')} and ${plural(data.invoices.length, 'invoice')}.`);
    });
  }

  /* ===================== Invoice editor ===================== */
  const ed = { id: null, touched: new Set(), showAll: false };

  function leaveEditor(id) {
    const inv = getInv(id);
    if (!inv || inv.status === 'paid') return;
    const n = Object.keys(validateInvoice(inv)).length;
    if (n) {
      if (!inv.flagged) { inv.flagged = true; save(); }
      toast(`Draft ${inv.number.trim() || ''} kept. ${plural(n, 'field')} still need${n === 1 ? 's' : ''} attention.`.replace('  ', ' '), 'warn');
    } else if (inv.flagged) { inv.flagged = false; save(); }
    ed.id = null;
  }

  function editorActions(inv) {
    const primary = inv.status === 'draft'
      ? `<button type="button" class="btn btn-primary" data-action="send">${icon('send')}<span>Mark as sent</span></button>`
      : inv.status === 'sent'
        ? `<button type="button" class="btn btn-primary" data-action="paid">${icon('check')}<span>Mark as paid</span></button>`
        : `<button type="button" class="btn btn-primary" data-action="reopen">${icon('unlock')}<span>Reopen</span></button>`;
    return `${primary}
      <button type="button" class="btn btn-secondary" data-action="duplicate">${icon('copy')}<span>Duplicate</span></button>
      <button type="button" class="btn btn-secondary" data-action="print">${icon('printer')}<span>Print</span></button>
      <button type="button" class="btn btn-danger" data-action="delete">${icon('trash')}<span>Delete</span></button>`;
  }

  function fieldHTML(key, id, label, control) {
    return `<div class="field" data-key="${key}"><label for="${id}">${label}</label>${control}<p class="field-error" id="${id}-err" hidden></p></div>`;
  }

  function renderEditor(id) {
    const inv = getInv(id);
    if (!inv) {
      $('#view').innerHTML = '';
      toast('That invoice doesn’t exist anymore.', 'warn');
      location.replace('#/invoices');
      return;
    }
    if (ed.id !== id) { ed.id = id; ed.touched = new Set(); ed.showAll = inv.flagged; }
    const ro = inv.status === 'paid';
    const dis = ro ? 'disabled' : '';
    const clientOpts = state.clients.length
      ? `<option value="">Choose a client…</option>` + state.clients.slice().sort((a, b) => a.name.localeCompare(b.name))
        .map(c => `<option value="${esc(c.id)}" ${c.id === inv.clientId ? 'selected' : ''}>${esc(c.name)}</option>`).join('')
      : `<option value="">No clients yet — add one</option>`;

    $('#view').innerHTML = `
      <div class="page editor">
        <a class="back-link" href="#/invoices">${icon('arrowLeft')}<span>All invoices</span></a>
        <div class="editor-head">
          <div class="editor-title">
            <h1 tabindex="-1">Invoice <span class="num-display"></span></h1>
            <div class="title-meta"><span id="ed-badge"></span><span class="save-state" id="save-state"></span></div>
          </div>
          <div class="editor-actions">${editorActions(inv)}</div>
        </div>
        ${ro ? `<div class="banner banner-success">${icon('lock')}<div class="banner-body"><strong>Paid on ${fmtDate(inv.paidDate)}.</strong> This invoice is read-only. Reopen it if you need to make changes.</div></div>` : ''}
        <section class="card" aria-labelledby="details-title">
          <div class="section">
            <div class="section-head"><h2 class="section-title" id="details-title">Details</h2><div class="from-block" id="from-block"></div></div>
            <div class="fields-grid">
              ${fieldHTML('number', 'f-number', 'Invoice number', `<input class="input" id="f-number" data-field="number" value="${esc(inv.number)}" autocomplete="off" spellcheck="false" aria-describedby="f-number-err" ${dis}>`)}
              ${fieldHTML('clientId', 'f-client', 'Client', `<div class="input-row"><select class="input" id="f-client" data-field="clientId" aria-describedby="f-client-err" ${dis}>${clientOpts}</select>${ro ? '' : `<button type="button" class="btn btn-secondary btn-icon" data-action="new-client" aria-label="Add a new client" title="Add a new client">${icon('plus')}</button>`}</div>`)}
              ${fieldHTML('issueDate', 'f-issue', 'Issue date', `<input class="input" type="date" id="f-issue" data-field="issueDate" value="${esc(inv.issueDate)}" aria-describedby="f-issue-err" ${dis}>`)}
              ${fieldHTML('dueDate', 'f-due', 'Due date', `<input class="input" type="date" id="f-due" data-field="dueDate" value="${esc(inv.dueDate)}" aria-describedby="f-due-err" ${dis}>`)}
              ${fieldHTML('currency', 'f-currency', 'Currency', `<select class="input" id="f-currency" data-field="currency" ${dis}>${Object.keys(CURRENCIES).map(c => `<option value="${c}" ${c === inv.currency ? 'selected' : ''}>${esc(currencyLabel(c))}</option>`).join('')}</select>`)}
            </div>
          </div>
          <div class="section">
            <div class="section-head">
              <h2 class="section-title" id="lines-title">Line items</h2>
              ${ro ? '' : '<p class="hint" id="lines-help">Drag the handle, or press Alt + ↑ / ↓ inside a line, to reorder.</p>'}
            </div>
            <div id="lines-wrap"></div>
            <div class="field items-error" data-key="items"><p class="field-error" id="items-err" hidden></p></div>
            ${ro ? '' : `<button type="button" class="btn btn-secondary add-line" data-action="add-line">${icon('plus')}<span>Add line</span></button>`}
            <div class="lines-foot">
              <div class="field notes-field">
                <label for="f-notes">Notes <span class="req">optional</span></label>
                <textarea class="input" id="f-notes" data-field="notes" rows="3" placeholder="Payment terms, bank details, a thank-you…" ${dis}>${esc(inv.notes)}</textarea>
              </div>
              <dl class="totals" id="totals" aria-label="Totals"></dl>
            </div>
          </div>
        </section>
      </div>`;
    renderLines(inv);
    bindEditor($('.editor'));
    updateEditor(inv);
    setSaveState(inv.updatedAt ? new Date(inv.updatedAt) : null);
  }

  function lineHTML(item, i, n, ro) {
    const id = esc(item.id);
    const dis = ro ? 'disabled' : '';
    const f = (field, label, cls, extra = '') => {
      const iid = `l-${id}-${field}`;
      return `<div class="field lf lf-${field}" data-key="${id}:${field}">
        <label class="line-label" for="${iid}">${label}<span class="sr-only">, line ${i + 1}</span></label>
        <input class="input ${cls}" id="${iid}" data-line-field="${field}" value="${esc(item[field])}" aria-describedby="${iid}-err" autocomplete="off" ${extra} ${dis}>
        <p class="field-error" id="${iid}-err" hidden></p></div>`;
    };
    return `<li class="line" data-id="${id}">
      ${ro ? '<span class="handle-spacer"></span>' : `<button type="button" class="drag-handle" data-act="handle" aria-label="Reorder line ${i + 1} of ${n}. Press Alt plus Up or Down arrow to move it." title="Drag to reorder">${icon('grip')}</button>`}
      ${f('description', 'Description', '', 'placeholder="What are you billing for?"')}
      ${f('quantity', 'Qty', 'num', 'inputmode="decimal"')}
      ${f('unitPrice', 'Unit price', 'num', 'inputmode="decimal" placeholder="0.00"')}
      ${f('discount', 'Discount %', 'num', 'inputmode="decimal"')}
      ${f('taxRate', 'Tax %', 'num', 'inputmode="decimal"')}
      <div class="line-amount"><span class="line-label" aria-hidden="true">Amount</span><span class="amt"></span><span class="line-disc"></span></div>
      <div class="line-actions">${ro ? '' : `
        <button type="button" class="btn btn-ghost btn-icon move-btn" data-act="up" aria-label="Move line ${i + 1} up" ${i === 0 ? 'disabled' : ''}>${icon('up')}</button>
        <button type="button" class="btn btn-ghost btn-icon move-btn" data-act="down" aria-label="Move line ${i + 1} down" ${i === n - 1 ? 'disabled' : ''}>${icon('down')}</button>
        <button type="button" class="btn btn-ghost btn-icon btn-danger-ghost" data-act="remove" aria-label="Remove line ${i + 1}" title="Remove line">${icon('trash')}</button>`}
      </div>
    </li>`;
  }

  function renderLines(inv) {
    const wrap = $('#lines-wrap');
    const ro = inv.status === 'paid';
    if (!inv.items.length) {
      wrap.innerHTML = `<div class="empty empty-sm">
        <div class="empty-art">${icon('file')}</div>
        <h3>No line items yet</h3>
        <p>${ro ? 'This invoice has no lines.' : 'Add the products or services you’re billing for with “Add line” below.'}</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <div class="lines-head" aria-hidden="true"><span></span><span>Description</span><span class="num">Qty</span><span class="num">Unit price</span><span class="num">Disc. %</span><span class="num">Tax %</span><span class="num">Amount</span><span class="${ro ? '' : 'actions-col'}"></span></div>
      <ol class="lines" id="lines" aria-labelledby="lines-title" ${ro ? '' : 'aria-describedby="lines-help"'}>
        ${inv.items.map((it, i) => lineHTML(it, i, inv.items.length, ro)).join('')}
      </ol>`;
  }

  function totalsHTML(inv, t) {
    const cur = inv.currency;
    const taxRows = t.taxGroups.filter(g => g.rate > 0n);
    return `
      <div><dt>Subtotal</dt><dd>${fmtMoney(t.subtotal, cur)}</dd></div>
      <div><dt>Discount</dt><dd>${t.discount > 0n ? '−' : ''}${fmtMoney(t.discount, cur)}</dd></div>
      ${taxRows.length ? taxRows.map(g => `<div><dt>Tax ${fmtRate(g.rate)}<span class="sub">on ${fmtMoney(g.base, cur)}</span></dt><dd>${fmtMoney(g.tax, cur)}</dd></div>`).join('')
        : `<div><dt>Tax</dt><dd>${fmtMoney(0n, cur)}</dd></div>`}
      <div class="grand"><dt>Total due</dt><dd>${fmtMoney(t.total, cur)}</dd></div>`;
  }

  function updateEditor(inv) {
    const root = $('.editor');
    if (!root) return;
    const t = computeTotals(inv);
    const errs = validateInvoice(inv, t);
    const ro = inv.status === 'paid';
    $$('[data-key]', root).forEach(w => {
      const key = w.dataset.key;
      const msg = ro ? '' : errs[key] || '';
      const show = msg && (ed.showAll || ed.touched.has(key)) ? msg : '';
      const err = w.querySelector('.field-error');
      const input = w.querySelector('input, select, textarea');
      if (input) input.setAttribute('aria-invalid', show ? 'true' : 'false');
      w.classList.toggle('has-error', !!show);
      if (err && err.dataset.msg !== show) {
        err.dataset.msg = show;
        err.hidden = !show;
        err.innerHTML = show ? icon('alert') + `<span>${esc(show)}</span>` : '';
      }
    });
    for (const item of inv.items) {
      const li = root.querySelector(`.line[data-id="${CSS.escape(item.id)}"]`);
      if (!li) continue;
      const a = t.lines[item.id].amounts;
      li.querySelector('.amt').textContent = a ? fmtMoney(a.net, inv.currency) : '—';
      li.querySelector('.line-disc').textContent = a && a.discount > 0n ? `${fmtMoney(a.discount, inv.currency)} off` : '';
    }
    $('#totals').innerHTML = totalsHTML(inv, t);
    const num = inv.number.trim() || 'Untitled';
    $('.num-display', root).textContent = num;
    document.title = `Invoice ${num} · Ledgerly`;
    $('#ed-badge').innerHTML = badge(effStatus(inv));
    renderFromBlock(inv);
    renderPrintDoc(inv, t);
  }

  function renderFromBlock(inv) {
    const box = $('#from-block');
    const p = state.profile;
    const ro = inv.status === 'paid';
    const differs = p.name !== inv.from.name || p.address !== inv.from.address || p.taxId !== inv.from.taxId;
    if (!inv.from.name.trim() && !p.name.trim()) {
      box.innerHTML = ro ? '' : `<button type="button" class="link-btn" data-action="open-settings">${icon('building')}Add your business details</button>`;
      return;
    }
    box.innerHTML = `<span class="from-label">From</span><strong>${esc(inv.from.name.trim() || 'No business name')}</strong>
      ${!ro && differs && p.name.trim() ? `<button type="button" class="link-btn" data-action="refresh-from">${icon('refresh')}Use current business details</button>` : ''}`;
  }

  function setSaveState(when, ok = true) {
    const el = $('#save-state');
    if (!el) return;
    el.classList.toggle('is-error', !ok);
    if (!ok) { el.innerHTML = `${icon('alert')}Not saved — storage unavailable`; return; }
    el.innerHTML = when ? `${icon('check')}Saved at ${timeFmt.format(when)}` : `${icon('check')}Saved`;
    el.classList.remove('pulse'); void el.offsetWidth; el.classList.add('pulse');
  }

  function commit(inv) {
    inv.updatedAt = new Date().toISOString();
    if (inv.flagged && !Object.keys(validateInvoice(inv)).length) { inv.flagged = false; ed.showAll = false; }
    const ok = save();
    updateEditor(inv);
    setSaveState(new Date(), ok);
  }

  function bindEditor(root) {
    const onInput = e => {
      const inv = getInv(ed.id);
      const t = e.target;
      if (!inv || inv.status === 'paid') return;
      if (t.dataset.field) {
        const f = t.dataset.field;
        if (inv[f] === t.value) return;
        inv[f] = t.value;
        if (['clientId', 'issueDate', 'dueDate', 'currency'].includes(f)) ed.touched.add(f);
        if (f === 'issueDate' || f === 'dueDate') { ed.touched.add('issueDate'); ed.touched.add('dueDate'); }
        if (f === 'currency') inv.items.forEach(it => ed.touched.add(`${it.id}:unitPrice`));
      } else if (t.dataset.lineField) {
        const item = inv.items.find(x => x.id === t.closest('.line').dataset.id);
        if (!item || item[t.dataset.lineField] === t.value) return;
        item[t.dataset.lineField] = t.value;
      } else return;
      commit(inv);
    };
    root.addEventListener('input', onInput);
    root.addEventListener('change', onInput);
    root.addEventListener('focusout', e => {
      const w = e.target.closest('[data-key]');
      if (!w || !e.target.matches('input, select, textarea')) return;
      ed.touched.add(w.dataset.key);
      const inv = getInv(ed.id);
      if (inv) updateEditor(inv);
    });
    root.addEventListener('click', onEditorClick);
    root.addEventListener('keydown', e => {
      if (!e.altKey || (e.key !== 'ArrowUp' && e.key !== 'ArrowDown')) return;
      const li = e.target.closest('.line');
      if (!li) return;
      e.preventDefault();
      moveLine(li.dataset.id, e.key === 'ArrowUp' ? -1 : 1, e.target);
    });
    bindDrag(root);
  }

  function focusKeyOf(el) {
    if (el?.dataset?.lineField) return `[data-line-field="${el.dataset.lineField}"]`;
    if (el?.dataset?.act) return `[data-act="${el.dataset.act}"]`;
    return '[data-act="handle"]';
  }

  function moveLine(id, delta, fromEl) {
    const inv = getInv(ed.id);
    if (!inv || inv.status === 'paid') return;
    const i = inv.items.findIndex(x => x.id === id);
    const j = i + delta;
    if (i < 0 || j < 0 || j >= inv.items.length) { announce(delta < 0 ? 'Already the first line.' : 'Already the last line.'); return; }
    const [item] = inv.items.splice(i, 1);
    inv.items.splice(j, 0, item);
    afterReorder(inv, id, focusKeyOf(fromEl));
    announce(`Line moved to position ${j + 1} of ${inv.items.length}.`);
  }

  function afterReorder(inv, id, focusSel) {
    renderLines(inv);
    commit(inv);
    const li = $(`.line[data-id="${CSS.escape(id)}"]`);
    if (!li) return;
    li.classList.add('moved');
    let target = focusSel ? li.querySelector(focusSel) : null;
    if (!target || target.disabled || target.offsetParent === null) target = li.querySelector('[data-act="handle"]');
    if (!target || target.offsetParent === null) target = li.querySelector('[data-line-field="description"]');
    target?.focus();
  }

  function bindDrag(root) {
    let dragId = null;
    const clear = () => $$('.line', root).forEach(l => l.classList.remove('drop-before', 'drop-after', 'dragging'));
    root.addEventListener('pointerdown', e => {
      const h = e.target.closest('.drag-handle');
      if (h) h.closest('.line').draggable = true;
    });
    root.addEventListener('pointerup', e => {
      const h = e.target.closest('.drag-handle');
      if (h) h.closest('.line').draggable = false;
    });
    root.addEventListener('dragstart', e => {
      const li = e.target.closest?.('.line');
      if (!li || !li.draggable) { e.preventDefault(); return; }
      dragId = li.dataset.id;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', dragId);
      requestAnimationFrame(() => li.classList.add('dragging'));
    });
    root.addEventListener('dragover', e => {
      if (!dragId) return;
      const li = e.target.closest('.line');
      if (!li) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      $$('.line', root).forEach(l => l.classList.remove('drop-before', 'drop-after'));
      if (li.dataset.id === dragId) return;
      const r = li.getBoundingClientRect();
      li.classList.add(e.clientY < r.top + r.height / 2 ? 'drop-before' : 'drop-after');
    });
    root.addEventListener('drop', e => {
      if (!dragId) return;
      e.preventDefault();
      const li = e.target.closest('.line');
      const inv = getInv(ed.id);
      const id = dragId;
      dragId = null;
      if (!li || !inv || li.dataset.id === id) { clear(); return; }
      const r = li.getBoundingClientRect();
      const after = e.clientY >= r.top + r.height / 2;
      const from = inv.items.findIndex(x => x.id === id);
      const [item] = inv.items.splice(from, 1);
      let to = inv.items.findIndex(x => x.id === li.dataset.id) + (after ? 1 : 0);
      inv.items.splice(to, 0, item);
      afterReorder(inv, id, '[data-act="handle"]');
      announce(`Line moved to position ${to + 1} of ${inv.items.length}.`);
    });
    root.addEventListener('dragend', e => {
      dragId = null;
      clear();
      const li = e.target.closest?.('.line');
      if (li) li.draggable = false;
    });
  }

  function requireValid(inv, verb) {
    const errs = validateInvoice(inv);
    const n = Object.keys(errs).length;
    if (!n) return true;
    ed.showAll = true;
    updateEditor(inv);
    const first = $('.editor .has-error input, .editor .has-error select, .editor .has-error textarea');
    if (first) first.focus();
    else $('[data-action="add-line"]')?.focus();
    toast(`Fix ${plural(n, 'field')} before ${verb}.`, 'warn');
    return false;
  }

  function onEditorClick(e) {
    const inv = getInv(ed.id);
    if (!inv) return;
    const act = e.target.closest('[data-act]');
    if (act && inv.status !== 'paid') {
      const li = act.closest('.line');
      if (act.dataset.act === 'up') moveLine(li.dataset.id, -1, act);
      else if (act.dataset.act === 'down') moveLine(li.dataset.id, 1, act);
      else if (act.dataset.act === 'remove') {
        const idx = inv.items.findIndex(x => x.id === li.dataset.id);
        inv.items.splice(idx, 1);
        renderLines(inv);
        commit(inv);
        const next = inv.items[Math.min(idx, inv.items.length - 1)];
        if (next) $(`.line[data-id="${CSS.escape(next.id)}"] [data-line-field="description"]`)?.focus();
        else $('[data-action="add-line"]')?.focus();
        announce(`Line removed. ${plural(inv.items.length, 'line')} left.`);
      }
      return;
    }
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    switch (btn.dataset.action) {
      case 'add-line': {
        const item = newItem();
        inv.items.push(item);
        renderLines(inv);
        commit(inv);
        $(`.line[data-id="${CSS.escape(item.id)}"] [data-line-field="description"]`)?.focus();
        break;
      }
      case 'new-client':
        openClientDialog(null, {
          returnSel: '#f-client',
          onSaved: c => { inv.clientId = c.id; ed.touched.add('clientId'); inv.updatedAt = new Date().toISOString(); },
        });
        break;
      case 'refresh-from':
        inv.from = profileSnapshot();
        commit(inv);
        $('#f-number')?.focus();
        toast('Business details updated on this invoice.');
        break;
      case 'send':
        if (!requireValid(inv, 'sending')) return;
        inv.status = 'sent';
        commit(inv);
        renderEditor(inv.id);
        $('.editor-actions .btn-primary')?.focus();
        toast(`Invoice ${inv.number} marked as sent.`);
        break;
      case 'paid':
        if (!requireValid(inv, 'marking it paid')) return;
        $('#paid-date').value = todayISO();
        setFieldError($('#paid-date'), $('#paid-date-err'), '');
        openDialog($('#paid-dialog'), { returnSel: '.editor-actions .btn-primary' });
        break;
      case 'reopen':
        inv.status = 'sent';
        inv.paidDate = '';
        commit(inv);
        renderEditor(inv.id);
        $('.editor-actions .btn-primary')?.focus();
        toast('Invoice reopened. You can edit it again.');
        break;
      case 'duplicate': {
        const t = todayISO();
        const term = isISO(inv.issueDate) && isISO(inv.dueDate) ? Math.max(0, daysBetween(inv.issueDate, inv.dueDate)) : 14;
        const now = new Date().toISOString();
        const copy = {
          ...inv, id: uid(), number: nextNumber(t.slice(0, 4)), issueDate: t, dueDate: addDays(t, term),
          status: 'draft', paidDate: '', flagged: false, from: profileSnapshot(), createdAt: now, updatedAt: now,
          items: inv.items.map(it => ({ ...it, id: uid() + Math.random().toString(36).slice(2, 5) })),
        };
        state.invoices.push(copy);
        save();
        toast(`Duplicated as ${copy.number}.`);
        location.hash = `#/invoice/${copy.id}`;
        break;
      }
      case 'print':
        window.print();
        break;
      case 'delete':
        if (!window.confirm(`Delete invoice ${inv.number.trim() || '(untitled draft)'}? This can’t be undone.`)) return;
        state.invoices = state.invoices.filter(x => x.id !== inv.id);
        save();
        ed.id = null;
        toast(`Invoice ${inv.number.trim() || ''} deleted.`.replace('  ', ' '));
        location.hash = '#/invoices';
        break;
    }
  }

  function setupPaidForm() {
    $('#paid-form').addEventListener('submit', e => {
      e.preventDefault();
      const inv = getInv(ed.id);
      if (!inv) { $('#paid-dialog').close(); return; }
      const v = $('#paid-date').value;
      const err = !isISO(v) ? 'Enter the date the payment arrived.'
        : isISO(inv.issueDate) && v < inv.issueDate ? `The paid date can’t be before the issue date (${fmtDate(inv.issueDate)}).` : '';
      setFieldError($('#paid-date'), $('#paid-date-err'), err);
      if (err) { $('#paid-date').focus(); return; }
      inv.status = 'paid';
      inv.paidDate = v;
      inv.flagged = false;
      commit(inv);
      renderEditor(inv.id);
      $('#paid-dialog').close();
      toast(`Invoice ${inv.number} marked as paid.`);
    });
  }

  /* ===================== Print document ===================== */
  function renderPrintDoc(inv, t) {
    const c = getClient(inv.clientId);
    const cur = inv.currency;
    const f = inv.from;
    const taxRows = t.taxGroups.filter(g => g.rate > 0n);
    $('#print-doc').innerHTML = `
      <header class="pd-head">
        <h1 class="pd-title">Invoice</h1>
        <div class="pd-number">No. ${esc(inv.number)}</div>
        ${inv.status === 'paid' ? `<div class="pd-paid">Paid ${fmtDate(inv.paidDate)}</div>` : ''}
      </header>
      <section class="pd-block">
        <p class="pd-label">From</p>
        <div class="pd-strong">${esc(f.name || '')}</div>
        ${f.address ? `<div>${nl2br(f.address)}</div>` : ''}
        ${f.taxId ? `<div>Tax ID: ${esc(f.taxId)}</div>` : ''}
      </section>
      <section class="pd-block">
        <p class="pd-label">Bill to</p>
        <div class="pd-strong">${esc(c?.name || '')}</div>
        ${c?.address ? `<div>${nl2br(c.address)}</div>` : ''}
        ${c?.email ? `<div>${esc(c.email)}</div>` : ''}
        ${c?.taxId ? `<div>Tax ID: ${esc(c.taxId)}</div>` : ''}
      </section>
      <dl class="pd-dates">
        <div><dt>Issue date</dt><dd>${fmtDate(inv.issueDate)}</dd></div>
        <div><dt>Due date</dt><dd>${fmtDate(inv.dueDate)}</dd></div>
        <div><dt>Currency</dt><dd>${cur}</dd></div>
      </dl>
      <table class="pd-items">
        <thead><tr><th>Description</th><th class="num">Qty</th><th class="num">Unit price</th><th class="num">Disc.</th><th class="num">Tax</th><th class="num">Amount</th></tr></thead>
        <tbody>${inv.items.map(it => {
          const a = t.lines[it.id].amounts;
          const priceOk = a && !t.lines[it.id].errors.unitPrice;
          return `<tr><td>${esc(it.description)}</td><td class="num">${esc(it.quantity)}</td>
            <td class="num">${priceOk ? fmtMajorStr(it.unitPrice, cur) : esc(it.unitPrice)}</td>
            <td class="num">${String(it.discount).trim() && Number(it.discount) ? esc(it.discount) + '%' : '—'}</td>
            <td class="num">${String(it.taxRate).trim() && Number(it.taxRate) ? esc(it.taxRate) + '%' : '—'}</td>
            <td class="num">${a ? fmtMoney(a.net, cur) : '—'}</td></tr>`;
        }).join('')}</tbody>
      </table>
      <dl class="pd-totals">
        <div><dt>Subtotal</dt><dd>${fmtMoney(t.subtotal, cur)}</dd></div>
        ${t.discount > 0n ? `<div><dt>Discount</dt><dd>−${fmtMoney(t.discount, cur)}</dd></div>` : ''}
        ${taxRows.map(g => `<div><dt>Tax ${fmtRate(g.rate)} on ${fmtMoney(g.base, cur)}</dt><dd>${fmtMoney(g.tax, cur)}</dd></div>`).join('')}
        <div class="grand"><dt>Total due</dt><dd>${fmtMoney(t.total, cur)}</dd></div>
      </dl>
      ${inv.notes.trim() ? `<section class="pd-notes"><p class="pd-label">Notes</p>${esc(inv.notes)}</section>` : ''}`;
  }

  /* ===================== Boot ===================== */
  function init() {
    $$('[data-icon]').forEach(el => { el.outerHTML = icon(el.dataset.icon); });
    $$('dialog').forEach(setupDialog);
    setupClientForm();
    setupSettings();
    setupPaidForm();
    $('#skip-link').addEventListener('click', e => { e.preventDefault(); ($('#view h1') || $('#main')).focus(); });
    // Global actions used across views.
    document.addEventListener('click', e => {
      const b = e.target.closest('[data-action]');
      if (!b) return;
      switch (b.dataset.action) {
        case 'new-invoice': createInvoice(); break;
        case 'open-settings': openSettings(); break;
        case 'add-client': openClientDialog(null, { returnSel: '#add-client' }); break;
        case 'clear-filters':
          listState.filter = 'all'; listState.q = '';
          renderInvoices();
          $('#inv-search')?.focus();
          break;
      }
    });
    window.addEventListener('hashchange', () => route());
    window.addEventListener('pagehide', () => {
      if (current.view !== 'invoice') return;
      const inv = getInv(current.id);
      if (inv && inv.status !== 'paid' && Object.keys(validateInvoice(inv)).length && !inv.flagged) { inv.flagged = true; save(); }
    });
    renderNotice();
    route(true);
  }

  init();
})();
