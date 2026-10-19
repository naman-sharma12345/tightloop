/* Ledgerly — invoice builder. Plain JS, no dependencies. */
(function () {
  'use strict';

  const STORAGE_KEY = 'ledgerly-invoices.v1';
  const DATA_VERSION = 1;
  const DEFAULT_TERM_DAYS = 14;

  // Each currency is formatted with its own locale so the symbol and digit grouping
  // are native (e.g. INR uses lakh grouping: ₹14,75,000.00).
  const CURRENCIES = {
    USD: { locale: 'en-US', digits: 2, name: 'US dollar' },
    EUR: { locale: 'en-IE', digits: 2, name: 'Euro' },
    GBP: { locale: 'en-GB', digits: 2, name: 'British pound' },
    INR: { locale: 'en-IN', digits: 2, name: 'Indian rupee' },
    JPY: { locale: 'en-JP', digits: 0, name: 'Japanese yen' },
  };
  const STATUS_LABEL = { draft: 'Draft', sent: 'Sent', paid: 'Paid', overdue: 'Overdue' };
  const STATUS_ICON = { draft: 'i-draft', sent: 'i-send', paid: 'i-check-circle', overdue: 'i-alert' };

  /* ------------------------------------------------------------------ utils */

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const icon = (id, cls = '') => `<svg class="icon ${cls}" aria-hidden="true" focusable="false"><use href="#${id}"/></svg>`;
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const isObj = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

  const pad2 = (n) => String(n).padStart(2, '0');
  const toISO = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
  const todayISO = () => toISO(new Date());
  const isISODate = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(parseISO(s));
  function parseISO(s) {
    const [y, m, d] = s.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    return dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d ? dt : NaN;
  }
  function addDays(iso, n) { const d = parseISO(iso); d.setDate(d.getDate() + n); return toISO(d); }
  function diffDays(a, b) { return Math.round((parseISO(b) - parseISO(a)) / 86400000); }
  const dateFmt = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const fmtDate = (iso) => (isISODate(iso) ? dateFmt.format(parseISO(iso)) : '—');
  const timeFmt = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  /* ------------------------------------------------------------------ money
     All arithmetic is done on BigInt integers:
       quantity  -> hundredths  (q100)
       price     -> currency minor units (cents; yen for JPY)
       percents  -> hundredths of a percent (p100)
     Each line is rounded half away from zero. */

  function parseDecimal(raw, maxDec) {
    let s = String(raw == null ? '' : raw).trim().replace(/\s+/g, '');
    if (!s) return { error: 'empty' };
    if (!s.includes('.') && /^-?\d*,\d+$/.test(s)) s = s.replace(',', '.');
    let neg = false;
    if (s[0] === '-') { neg = true; s = s.slice(1); }
    else if (s[0] === '+') s = s.slice(1);
    if (!/^(\d+(\.\d*)?|\.\d+)$/.test(s)) return { error: 'nan' };
    let [int, frac = ''] = s.split('.');
    int = int.replace(/^0+(?=\d)/, '') || '0';
    if (int.length > 12) return { error: 'big' };
    const tooPrecise = frac.replace(/0+$/, '').length > maxDec;
    let v = BigInt(int + (frac + '0'.repeat(maxDec)).slice(0, maxDec));
    if (tooPrecise && Number(frac[maxDec]) >= 5) v += 1n;
    if (neg) v = -v;
    return { value: v, neg: neg && v !== 0n, tooPrecise };
  }

  function roundDiv(n, d) {
    const neg = n < 0n;
    const a = neg ? -n : n;
    const q = (a * 2n + d) / (2n * d);
    return neg ? -q : q;
  }

  function minorToDecimal(v, digits) {
    const neg = v < 0n;
    let s = (neg ? -v : v).toString();
    if (digits > 0) {
      s = s.padStart(digits + 1, '0');
      s = s.slice(0, -digits) + '.' + s.slice(-digits);
    }
    return (neg ? '-' : '') + s;
  }

  const fmtCache = {};
  function fmtMoney(minor, cur) {
    const c = CURRENCIES[cur] || CURRENCIES.USD;
    const key = cur;
    if (!fmtCache[key]) fmtCache[key] = new Intl.NumberFormat(c.locale, { style: 'currency', currency: cur, minimumFractionDigits: c.digits, maximumFractionDigits: c.digits });
    const str = minorToDecimal(minor, c.digits);
    try { return fmtCache[key].format(str); } catch (e) { return fmtCache[key].format(Number(str)); }
  }

  function fmtPercent(p100) {
    const s = minorToDecimal(p100, 2).replace(/\.?0+$/, '');
    return s + '%';
  }

  function lineAmounts(line, cur) {
    const digits = (CURRENCIES[cur] || CURRENCIES.USD).digits;
    const q = parseDecimal(line.quantity, 2);
    const p = parseDecimal(line.unitPrice, digits);
    const d = parseDecimal(line.discount === '' ? '0' : line.discount, 2);
    const t = parseDecimal(line.taxRate === '' ? '0' : line.taxRate, 2);
    const q100 = q.error || q.value <= 0n ? 0n : q.value;
    const price = p.error || p.value < 0n ? 0n : p.value;
    const disc = d.error || d.value < 0n || d.value > 10000n ? 0n : d.value;
    const rate = t.error || t.value < 0n || t.value > 10000n ? 0n : t.value;
    const exact = q100 * price; // in minor units * 100
    const gross = roundDiv(exact, 100n);
    const discount = roundDiv(exact * disc, 1000000n);
    const net = gross - discount;
    const tax = roundDiv(net * rate, 10000n);
    return { gross, discount, net, tax, rate, disc, total: net + tax };
  }

  function invoiceTotals(inv) {
    let subtotal = 0n, discount = 0n, taxTotal = 0n;
    const taxes = new Map();
    for (const line of inv.lines) {
      const a = lineAmounts(line, inv.currency);
      subtotal += a.gross;
      discount += a.discount;
      taxTotal += a.tax;
      const key = a.rate.toString();
      const g = taxes.get(key) || { rate: a.rate, base: 0n, tax: 0n };
      g.base += a.net; g.tax += a.tax;
      taxes.set(key, g);
    }
    const groups = Array.from(taxes.values()).filter((g) => g.rate > 0n).sort((a, b) => (a.rate < b.rate ? 1 : -1));
    return { subtotal, discount, taxes: groups, taxTotal, total: subtotal - discount + taxTotal };
  }

  /* ------------------------------------------------------------------ data */

  function emptyData() {
    return { version: DATA_VERSION, profile: { name: '', address: '', taxId: '', currency: 'USD', taxRate: '0' }, clients: [], invoices: [] };
  }

  const str = (v, max = 2000) => (typeof v === 'string' ? v.slice(0, max) : typeof v === 'number' && isFinite(v) ? String(v) : null);

  // Validates and normalises an imported/stored object. Returns {ok, data} or {ok:false, error}.
  function validateData(obj) {
    if (!isObj(obj)) return { ok: false, error: 'The file is not a Ledgerly backup (expected a JSON object).' };
    if (!isObj(obj.profile) || !Array.isArray(obj.clients) || !Array.isArray(obj.invoices)) {
      return { ok: false, error: 'The file is missing the profile, clients or invoices sections.' };
    }
    const out = emptyData();
    const p = obj.profile;
    for (const k of ['name', 'address', 'taxId']) {
      if (p[k] != null && str(p[k]) === null) return { ok: false, error: `Profile field “${k}” has the wrong type.` };
      out.profile[k] = str(p[k]) || '';
    }
    if (p.currency != null && !CURRENCIES[p.currency]) return { ok: false, error: `Unknown default currency “${String(p.currency)}”.` };
    out.profile.currency = p.currency || 'USD';
    out.profile.taxRate = str(p.taxRate) || '0';

    const clientIds = new Set();
    for (const [i, c] of obj.clients.entries()) {
      if (!isObj(c) || typeof c.id !== 'string' || !c.id || typeof c.name !== 'string' || !c.name.trim()) {
        return { ok: false, error: `Client #${i + 1} is missing an id or name.` };
      }
      if (clientIds.has(c.id)) return { ok: false, error: `Two clients share the id “${c.id}”.` };
      clientIds.add(c.id);
      out.clients.push({ id: c.id, name: c.name.slice(0, 120), email: str(c.email) || '', address: str(c.address) || '' });
    }

    const invIds = new Set();
    const numbers = new Set();
    for (const [i, v] of obj.invoices.entries()) {
      const where = `Invoice #${i + 1}`;
      if (!isObj(v) || typeof v.id !== 'string' || !v.id) return { ok: false, error: `${where} has no id.` };
      if (invIds.has(v.id)) return { ok: false, error: `Two invoices share the id “${v.id}”.` };
      invIds.add(v.id);
      if (typeof v.number !== 'string') return { ok: false, error: `${where} has no invoice number.` };
      const nk = v.number.trim().toLowerCase();
      if (nk && numbers.has(nk)) return { ok: false, error: `Invoice number “${v.number}” appears twice.` };
      numbers.add(nk);
      if (!['draft', 'sent', 'paid'].includes(v.status)) return { ok: false, error: `${where} has an unknown status “${String(v.status)}”.` };
      if (!CURRENCIES[v.currency]) return { ok: false, error: `${where} uses an unsupported currency.` };
      if (v.clientId && !clientIds.has(v.clientId)) return { ok: false, error: `${where} refers to a client that isn't in the file.` };
      if (!Array.isArray(v.lines)) return { ok: false, error: `${where} has no line items list.` };
      const lines = [];
      for (const l of v.lines) {
        if (!isObj(l)) return { ok: false, error: `${where} has a malformed line item.` };
        const line = { id: typeof l.id === 'string' && l.id ? l.id : uid() };
        for (const k of ['description', 'quantity', 'unitPrice', 'discount', 'taxRate']) {
          if (l[k] != null && str(l[k]) === null) return { ok: false, error: `${where} has a line with an invalid “${k}”.` };
          line[k] = str(l[k]) || '';
        }
        lines.push(line);
      }
      const from = isObj(v.from) ? { name: str(v.from.name) || '', address: str(v.from.address) || '', taxId: str(v.from.taxId) || '' } : { name: '', address: '', taxId: '' };
      out.invoices.push({
        id: v.id,
        number: v.number.slice(0, 40),
        clientId: v.clientId || '',
        issueDate: isISODate(v.issueDate) ? v.issueDate : '',
        dueDate: isISODate(v.dueDate) ? v.dueDate : '',
        currency: v.currency,
        status: v.status,
        paidDate: v.status === 'paid' && isISODate(v.paidDate) ? v.paidDate : '',
        notes: str(v.notes) || '',
        from,
        lines,
        flagged: !!v.flagged,
        createdAt: str(v.createdAt) || new Date().toISOString(),
        updatedAt: str(v.updatedAt) || new Date().toISOString(),
      });
    }
    return { ok: true, data: out };
  }

  let notice = null;
  function load() {
    let raw;
    try { raw = localStorage.getItem(STORAGE_KEY); }
    catch (e) {
      notice = { kind: 'warn', title: 'Storage is blocked', text: "This browser isn't allowing local storage, so changes won't be kept after you close the tab." };
      return emptyData();
    }
    if (raw == null) {
      notice = { kind: 'info', title: 'Welcome — nothing saved yet', text: 'You are starting with an empty workspace. Add your business details in Settings, then create a client and your first invoice.', action: 'open-settings', actionLabel: 'Open settings' };
      return emptyData();
    }
    try {
      const res = validateData(JSON.parse(raw));
      if (!res.ok) throw new Error(res.error);
      return res.data;
    } catch (e) {
      notice = { kind: 'warn', title: "Your saved data couldn't be read", text: 'It looks damaged, so the app started empty. If you have a JSON backup, import it from the Data menu. Saved data will be replaced as soon as you make a change.', action: 'import-json', actionLabel: 'Import backup' };
      return emptyData();
    }
  }

  let data = load();
  let lastSaved = null;
  let saveError = false;

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      lastSaved = new Date();
      saveError = false;
      if (notice && notice.kind === 'info' && (data.clients.length || data.invoices.length)) { notice = null; renderBanner(); }
    } catch (e) {
      saveError = true;
    }
    updateSaveState();
  }

  /* ------------------------------------------------------------------ domain helpers */

  const clientById = (id) => data.clients.find((c) => c.id === id);
  const invoiceById = (id) => data.invoices.find((v) => v.id === id);
  const clientName = (id) => (clientById(id) || {}).name || '';

  function effectiveStatus(inv) {
    if (inv.status === 'sent' && isISODate(inv.dueDate) && inv.dueDate < todayISO()) return 'overdue';
    return inv.status;
  }

  function nextNumber(year) {
    const re = new RegExp(`^${year}-(\\d+)$`);
    let max = 0;
    for (const v of data.invoices) {
      const m = re.exec(v.number.trim());
      if (m) max = Math.max(max, parseInt(m[1], 10));
    }
    let n = max + 1, num;
    do { num = `${year}-${String(n).padStart(4, '0')}`; n++; } while (numberTaken(num));
    return num;
  }
  function numberTaken(num, exceptId) {
    const k = num.trim().toLowerCase();
    return data.invoices.some((v) => v.id !== exceptId && v.number.trim().toLowerCase() === k);
  }

  function newLine(inv) {
    return { id: uid(), description: '', quantity: '1', unitPrice: '', discount: '0', taxRate: data.profile.taxRate || '0' };
  }

  function profileSnapshot() { return { name: data.profile.name, address: data.profile.address, taxId: data.profile.taxId }; }

  function createInvoice() {
    const today = todayISO();
    const inv = {
      id: uid(),
      number: nextNumber(today.slice(0, 4)),
      clientId: data.clients.length === 1 ? data.clients[0].id : '',
      issueDate: today,
      dueDate: addDays(today, DEFAULT_TERM_DAYS),
      currency: data.profile.currency || 'USD',
      status: 'draft',
      paidDate: '',
      notes: '',
      from: profileSnapshot(),
      lines: [],
      flagged: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    inv.lines.push(newLine(inv));
    data.invoices.push(inv);
    save();
    return inv;
  }

  function quantityError(raw) {
    const r = parseDecimal(raw, 2);
    if (r.error === 'empty') return 'Enter a quantity.';
    if (r.error === 'big') return 'That quantity is too large.';
    if (r.error) return 'Use a number, like 1 or 2.5.';
    if (r.neg || r.value <= 0n) return 'Quantity must be more than 0.';
    if (r.tooPrecise) return 'Use at most 2 decimal places.';
    return '';
  }
  function priceError(raw, cur) {
    const digits = CURRENCIES[cur].digits;
    const r = parseDecimal(raw, digits);
    if (r.error === 'empty') return 'Enter a price (0 is fine).';
    if (r.error === 'big') return 'That price is too large.';
    if (r.error) return 'Use a number, like 120 or 99.50.';
    if (r.neg) return "Price can't be negative.";
    if (r.tooPrecise) return digits === 0 ? 'Yen has no minor unit, so use a whole number.' : `Use at most ${digits} decimal places.`;
    return '';
  }
  function percentError(raw, what) {
    if (String(raw).trim() === '') return '';
    const r = parseDecimal(raw, 2);
    if (r.error) return `${what} must be a number from 0 to 100.`;
    if (r.neg || r.value > 10000n) return `${what} must be between 0 and 100%.`;
    if (r.tooPrecise) return 'Use at most 2 decimal places.';
    return '';
  }

  // Returns a map of field key -> message.
  function validateInvoice(inv) {
    const e = {};
    if (!inv.number.trim()) e.number = 'Enter an invoice number.';
    else if (numberTaken(inv.number, inv.id)) e.number = `${inv.number.trim()} is already used by another invoice. Pick a different number.`;
    if (!inv.clientId || !clientById(inv.clientId)) e.clientId = 'Choose who this invoice is for.';
    if (!isISODate(inv.issueDate)) e.issueDate = 'Enter the issue date.';
    if (!isISODate(inv.dueDate)) e.dueDate = 'Enter the due date.';
    else if (isISODate(inv.issueDate) && inv.dueDate < inv.issueDate) e.dueDate = "Due date can't be before the issue date.";
    if (!inv.lines.length) e.lines = 'Add at least one line item.';
    for (const l of inv.lines) {
      const k = `line:${l.id}:`;
      if (!l.description.trim()) e[k + 'description'] = 'Describe this item.';
      const q = quantityError(l.quantity); if (q) e[k + 'quantity'] = q;
      const p = priceError(l.unitPrice, inv.currency); if (p) e[k + 'unitPrice'] = p;
      const d = percentError(l.discount, 'Discount'); if (d) e[k + 'discount'] = d;
      const t = percentError(l.taxRate, 'Tax rate'); if (t) e[k + 'taxRate'] = t;
    }
    return e;
  }

  /* ------------------------------------------------------------------ UI: toasts, announcer, banner */

  function toast(message, opts = {}) {
    const host = $('#toasts');
    const el = document.createElement('div');
    el.className = 'toast' + (opts.error ? ' is-error' : '');
    el.innerHTML = `${icon(opts.error ? 'i-alert' : 'i-check-circle')}<span>${esc(message)}</span>`;
    if (opts.action) {
      const b = document.createElement('button');
      b.type = 'button';
      b.innerHTML = (opts.actionIcon ? icon(opts.actionIcon, 'icon-sm') : '') + esc(opts.action);
      b.addEventListener('click', () => { opts.onAction(); dismiss(); });
      el.appendChild(b);
    }
    const x = document.createElement('button');
    x.type = 'button'; x.className = 'toast-x'; x.setAttribute('aria-label', 'Dismiss notification');
    x.innerHTML = icon('i-x', 'icon-sm');
    x.addEventListener('click', () => dismiss());
    el.appendChild(x);
    host.appendChild(el);
    while (host.children.length > 3) host.firstChild.remove();
    let timer = setTimeout(dismiss, opts.action ? 9000 : 5000);
    el.addEventListener('mouseenter', () => clearTimeout(timer));
    el.addEventListener('focusin', () => clearTimeout(timer));
    el.addEventListener('mouseleave', () => { clearTimeout(timer); timer = setTimeout(dismiss, 3000); });
    function dismiss() {
      clearTimeout(timer);
      if (!el.isConnected) return;
      if (el.contains(document.activeElement)) { const m = $('#main'); m.focus({ preventScroll: true }); }
      el.remove();
    }
  }

  function announce(msg) {
    const a = $('#announcer');
    a.textContent = '';
    setTimeout(() => { a.textContent = msg; }, 30);
  }

  function renderBanner() {
    const slot = $('#banner-slot');
    if (!notice) { slot.innerHTML = ''; return; }
    slot.innerHTML = `<div class="banner banner-${notice.kind}" role="${notice.kind === 'warn' ? 'alert' : 'status'}">
      ${icon(notice.kind === 'warn' ? 'i-alert' : 'i-info')}
      <div><strong>${esc(notice.title)}</strong><p>${esc(notice.text)}</p></div>
      ${notice.action ? `<button type="button" class="btn btn-secondary btn-sm" data-action="${notice.action}">${esc(notice.actionLabel)}</button>` : ''}
      <button type="button" class="btn btn-ghost btn-icon" data-action="dismiss-banner" aria-label="Dismiss message">${icon('i-x')}</button>
    </div>`;
  }

  /* ------------------------------------------------------------------ routing */

  const ui = { filter: 'all', query: '', sort: 'date-desc', clientMsg: null };
  let current = { view: null, id: null };
  let editor = null; // { id, touched:Set, showAll:bool }
  let pendingFocus = null;

  function parseRoute() {
    const parts = location.hash.replace(/^#\/?/, '').split('/');
    if (parts[0] === 'clients') return { view: 'clients' };
    if (parts[0] === 'invoice' && parts[1]) return { view: 'editor', id: decodeURIComponent(parts[1]) };
    return { view: 'invoices' };
  }

  function onRoute() {
    const next = parseRoute();
    if (current.view === 'editor' && !(next.view === 'editor' && next.id === current.id)) leaveEditor();
    const prevView = current.view;
    current = next;
    closeMenu();
    $$('.main-nav a').forEach((a) => {
      const active = a.dataset.nav === (next.view === 'editor' ? 'invoices' : next.view);
      if (active) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    if (next.view === 'clients') { document.title = 'Clients — Ledgerly'; renderClients(); }
    else if (next.view === 'editor') {
      const inv = invoiceById(next.id);
      if (!inv) { toast("That invoice doesn't exist any more.", { error: true }); location.replace('#/invoices'); return; }
      openEditor(inv);
    } else { document.title = 'Invoices — Ledgerly'; renderList(); }
    if (pendingFocus === 'new' && next.view === 'editor') {
      pendingFocus = null;
      window.scrollTo(0, 0);
      const f = $('#f-client');
      const target = f && !f.value ? f : $('[data-line-field="description"]');
      if (target) target.focus();
    } else if (prevView !== null) {
      window.scrollTo(0, 0);
      const h1 = $('#app h1');
      if (h1) { h1.setAttribute('tabindex', '-1'); h1.focus({ preventScroll: true }); }
    }
  }

  function go(hash) { if (location.hash === hash) onRoute(); else location.hash = hash; }

  /* ------------------------------------------------------------------ list view */

  function statusBadge(st) {
    return `<span class="badge badge-${st}">${icon(STATUS_ICON[st])}${STATUS_LABEL[st]}</span>`;
  }

  function filteredInvoices() {
    const q = ui.query.trim().toLowerCase();
    let rows = data.invoices.map((inv) => ({ inv, st: effectiveStatus(inv), total: invoiceTotals(inv).total, client: clientName(inv.clientId) }));
    if (ui.filter !== 'all') rows = rows.filter((r) => r.st === ui.filter);
    if (q) rows = rows.filter((r) => r.inv.number.toLowerCase().includes(q) || r.client.toLowerCase().includes(q));
    const [key, dir] = ui.sort.split('-');
    const sign = dir === 'asc' ? 1 : -1;
    rows.sort((a, b) => {
      let c = 0;
      if (key === 'total') {
        const da = CURRENCIES[a.inv.currency].digits, db = CURRENCIES[b.inv.currency].digits;
        c = Number(minorToDecimal(a.total, da)) - Number(minorToDecimal(b.total, db));
      } else c = (a.inv.issueDate || '').localeCompare(b.inv.issueDate || '');
      if (c === 0) c = a.inv.number.localeCompare(b.inv.number, undefined, { numeric: true });
      return c * sign;
    });
    return rows;
  }

  function renderList() {
    const app = $('#app');
    const counts = { all: data.invoices.length, draft: 0, sent: 0, overdue: 0, paid: 0 };
    data.invoices.forEach((v) => counts[effectiveStatus(v)]++);
    const head = `<div class="page-head">
        <div><h1>Invoices</h1><p>${data.invoices.length ? `${counts.all} invoice${counts.all === 1 ? '' : 's'} · ${counts.overdue} overdue` : 'Create, send and track what you’re owed.'}</p></div>
        <button type="button" class="btn btn-primary" data-action="new-invoice">${icon('i-plus')}New invoice</button>
      </div>`;

    if (!data.invoices.length) {
      app.innerHTML = head + `<div class="card"><div class="empty">
        <div class="empty-art">${icon('i-file')}</div>
        <h2>No invoices yet</h2>
        <p>${data.clients.length ? 'Create your first invoice — it saves automatically as you type.' : 'Start by adding a client, then create your first invoice. It saves automatically as you type.'}</p>
        <div class="actions">
          <button type="button" class="btn btn-primary" data-action="new-invoice">${icon('i-plus')}Create an invoice</button>
          ${data.clients.length ? '' : `<button type="button" class="btn btn-secondary" data-action="new-client">${icon('i-users')}Add a client</button>`}
          ${data.profile.name ? '' : `<button type="button" class="btn btn-secondary" data-action="open-settings">${icon('i-building')}Business details</button>`}
        </div></div></div>`;
      return;
    }

    const chips = ['all', 'draft', 'sent', 'overdue', 'paid'].map((k) =>
      `<button type="button" class="chip" data-action="filter" data-filter="${k}" aria-pressed="${ui.filter === k}">${k === 'all' ? 'All' : STATUS_LABEL[k]}<span class="count" aria-label="${counts[k]} invoices">${counts[k]}</span></button>`).join('');

    app.innerHTML = head + `<div class="card">
      <div class="toolbar">
        <div class="chips" role="group" aria-label="Filter by status">${chips}</div>
        <div class="search">${icon('i-search')}<label class="visually-hidden" for="inv-search">Search by client or number</label>
          <input id="inv-search" type="search" placeholder="Search client or number" value="${esc(ui.query)}" autocomplete="off"></div>
        <div class="sort"><label for="inv-sort">Sort</label>
          <select id="inv-sort">
            <option value="date-desc">Issue date, newest first</option>
            <option value="date-asc">Issue date, oldest first</option>
            <option value="total-desc">Total, highest first</option>
            <option value="total-asc">Total, lowest first</option>
          </select></div>
      </div>
      <div id="list-body"></div>
    </div>`;
    $('#inv-sort').value = ui.sort;
    renderListBody();
  }

  function renderListBody() {
    const body = $('#list-body');
    if (!body) return;
    const rows = filteredInvoices();
    if (!rows.length) {
      body.innerHTML = `<div class="empty empty-sm">
        <div class="empty-art">${icon('i-search')}</div>
        <h2>No invoices match</h2>
        <p>Nothing ${ui.filter !== 'all' ? `is <strong>${STATUS_LABEL[ui.filter]}</strong>` : 'matches'}${ui.query ? ` for “${esc(ui.query.trim())}”` : ''}. Try another search or show all invoices.</p>
        <div class="actions"><button type="button" class="btn btn-secondary" data-action="clear-filters">Clear filters</button></div>
      </div>`;
      return;
    }
    const today = todayISO();
    body.innerHTML = `<table class="table">
      <caption class="visually-hidden">Invoices, ${rows.length} shown</caption>
      <thead><tr><th scope="col">Number</th><th scope="col">Client</th><th scope="col">Issued</th><th scope="col">Due</th><th scope="col" class="num">Total</th><th scope="col">Status</th></tr></thead>
      <tbody>${rows.map(({ inv, st, total, client }) => {
        const needs = inv.flagged && Object.keys(validateInvoice(inv)).length;
        let dueSub = '';
        if (st === 'overdue') { const n = diffDays(inv.dueDate, today); dueSub = `<span class="cell-sub is-overdue">${n} day${n === 1 ? '' : 's'} overdue</span>`; }
        else if (st === 'paid' && inv.paidDate) dueSub = `<span class="cell-sub">Paid ${fmtDate(inv.paidDate)}</span>`;
        return `<tr class="inv-row" data-id="${esc(inv.id)}">
          <td class="td-num"><a class="inv-num" href="#/invoice/${encodeURIComponent(inv.id)}">${esc(inv.number || 'Untitled')}</a>
            ${needs ? `<span class="attention">${icon('i-alert')}Needs attention</span>` : ''}</td>
          <td class="td-client">${client ? esc(client) : '<span class="muted">No client yet</span>'}</td>
          <td class="td-issue">${fmtDate(inv.issueDate)}</td>
          <td class="td-due">${fmtDate(inv.dueDate)}${dueSub}</td>
          <td class="td-total num"><span class="amount">${fmtMoney(total, inv.currency)}</span></td>
          <td class="td-status">${statusBadge(st)}</td>
        </tr>`;
      }).join('')}</tbody></table>
      <div class="list-foot">${rows.length} of ${data.invoices.length} shown</div>`;
  }

  /* ------------------------------------------------------------------ clients view */

  function initials(name) {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    return ((parts[0] || '?')[0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
  }

  function renderClients() {
    const app = $('#app');
    const head = `<div class="page-head">
      <div><h1>Clients</h1><p>${data.clients.length ? `${data.clients.length} client${data.clients.length === 1 ? '' : 's'}` : 'The people and companies you bill.'}</p></div>
      <button type="button" class="btn btn-primary" data-action="new-client">${icon('i-plus')}Add client</button>
    </div>`;
    if (!data.clients.length) {
      app.innerHTML = head + `<div class="card"><div class="empty">
        <div class="empty-art">${icon('i-users')}</div>
        <h2>No clients yet</h2>
        <p>Add a client with a name and, if you like, an email and billing address. You can then pick them on any invoice.</p>
        <div class="actions"><button type="button" class="btn btn-primary" data-action="new-client">${icon('i-plus')}Add your first client</button></div>
      </div></div>`;
      return;
    }
    const sorted = data.clients.slice().sort((a, b) => a.name.localeCompare(b.name));
    app.innerHTML = head + `<div class="card"><ul class="client-list">${sorted.map((c) => {
      const used = data.invoices.filter((v) => v.clientId === c.id);
      const msg = ui.clientMsg && ui.clientMsg.id === c.id;
      return `<li class="client" data-id="${esc(c.id)}">
        <span class="avatar" aria-hidden="true">${esc(initials(c.name))}</span>
        <div><div class="client-name">${esc(c.name)}</div>${c.email ? `<div class="client-meta">${esc(c.email)}</div>` : '<div class="client-meta">No email</div>'}</div>
        <div class="client-meta client-info2">${c.address ? esc(c.address.split('\n')[0]) : ''}</div>
        <div class="client-count">${used.length ? `${used.length} invoice${used.length === 1 ? '' : 's'}` : 'No invoices'}</div>
        <div class="client-actions">
          <button type="button" class="btn btn-ghost btn-icon" data-action="edit-client" data-id="${esc(c.id)}" aria-label="Edit ${esc(c.name)}">${icon('i-edit')}</button>
          <button type="button" class="btn btn-danger-ghost btn-icon" data-action="delete-client" data-id="${esc(c.id)}" aria-label="Delete ${esc(c.name)}" ${msg ? `aria-describedby="cmsg-${esc(c.id)}"` : ''}>${icon('i-trash')}</button>
        </div>
        ${msg ? `<div class="client-msg" id="cmsg-${esc(c.id)}" role="alert">${icon('i-alert')}<span>${ui.clientMsg.html}</span>
          <button type="button" class="btn btn-ghost btn-icon btn-sm" data-action="dismiss-client-msg" aria-label="Dismiss">${icon('i-x', 'icon-sm')}</button></div>` : ''}
      </li>`;
    }).join('')}</ul></div>`;
  }

  function deleteClient(id, trigger) {
    const c = clientById(id);
    if (!c) return;
    const used = data.invoices.filter((v) => v.clientId === id);
    if (used.length) {
      const list = used.slice(0, 3).map((v) => esc(v.number || 'Untitled')).join(', ') + (used.length > 3 ? ` and ${used.length - 3} more` : '');
      ui.clientMsg = { id, html: `Can’t delete ${esc(c.name)}: ${used.length === 1 ? 'invoice' : `${used.length} invoices`} ${list} ${used.length === 1 ? 'uses' : 'use'} this client. Delete or reassign ${used.length === 1 ? 'it' : 'them'} first.` };
      renderClients();
      const btn = $(`.client[data-id="${CSS.escape(id)}"] [data-action="delete-client"]`);
      if (btn) btn.focus();
      return;
    }
    if (!window.confirm(`Delete client “${c.name}”? This can’t be undone.`)) return;
    data.clients = data.clients.filter((x) => x.id !== id);
    ui.clientMsg = null;
    save();
    renderClients();
    const first = $('.client [data-action="edit-client"]') || $('[data-action="new-client"]');
    if (first) first.focus();
    toast(`Deleted ${c.name}.`);
  }

  /* ------------------------------------------------------------------ dialogs */

  function openDialog(dlg, opener) {
    dlg._opener = opener || document.activeElement;
    dlg.showModal();
    const first = dlg.querySelector('input:not([type=hidden]), select, textarea');
    if (first) first.focus();
  }
  function closeDialog(dlg) { if (dlg.open) dlg.close(); }

  $$('dialog').forEach((dlg) => {
    dlg.addEventListener('click', (e) => {
      if (e.target.closest('[data-close]')) closeDialog(dlg);
      else if (e.target === dlg) {
        // click on backdrop
        const r = dlg.getBoundingClientRect();
        if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) closeDialog(dlg);
      }
    });
    dlg.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;
      const f = $$('button:not([disabled]), input:not([disabled]):not([tabindex="-1"]), select:not([disabled]), textarea:not([disabled]), a[href]', dlg).filter((el) => el.getClientRects().length > 0);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    dlg.addEventListener('close', () => {
      const back = dlg._opener;
      dlg._opener = null;
      if (dlg._onClose) { const fn = dlg._onClose; dlg._onClose = null; fn(dlg.returnValue); }
      if (back && back.isConnected && back !== document.body) back.focus();
      else if (!document.activeElement || document.activeElement === document.body) {
        const h = $('#app h1'); if (h) { h.setAttribute('tabindex', '-1'); h.focus(); }
      }
    });
  });

  function setFieldError(input, errEl, msg) {
    if (msg) {
      errEl.innerHTML = icon('i-alert') + `<span>${esc(msg)}</span>`;
      errEl.hidden = false;
      input.setAttribute('aria-invalid', 'true');
    } else {
      errEl.hidden = true; errEl.innerHTML = '';
      input.removeAttribute('aria-invalid');
    }
  }

  // --- Settings
  const settingsDlg = $('#settings-dialog');
  const pCurrency = $('#p-currency');
  pCurrency.innerHTML = Object.entries(CURRENCIES).map(([k, c]) => `<option value="${k}">${k} — ${c.name}</option>`).join('');

  function openSettings(opener) {
    const f = $('#settings-form');
    f.name.value = data.profile.name;
    f.address.value = data.profile.address;
    f.taxId.value = data.profile.taxId;
    f.currency.value = data.profile.currency;
    f.taxRate.value = data.profile.taxRate;
    setFieldError(f.taxRate, $('#p-tax-err'), '');
    openDialog(settingsDlg, opener);
  }
  $('#settings-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = e.target;
    const taxMsg = percentError(f.taxRate.value.trim() || '0', 'Tax rate');
    setFieldError(f.taxRate, $('#p-tax-err'), taxMsg);
    if (taxMsg) { f.taxRate.focus(); return; }
    data.profile = {
      name: f.name.value.trim(), address: f.address.value.trim(), taxId: f.taxId.value.trim(),
      currency: f.currency.value, taxRate: f.taxRate.value.trim() || '0',
    };
    save();
    if (notice && notice.kind === 'info') { notice = null; renderBanner(); }
    closeDialog(settingsDlg);
    toast('Business profile saved. New invoices will use it.');
    rerenderCurrent();
  });
  $('#p-tax').addEventListener('input', (e) => { if (e.target.getAttribute('aria-invalid')) setFieldError(e.target, $('#p-tax-err'), percentError(e.target.value.trim() || '0', 'Tax rate')); });

  // --- Client
  const clientDlg = $('#client-dialog');
  let clientEditing = null;
  let clientDone = null;
  const EMAIL_RE = /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/;

  function openClient(id, opener, done) {
    const f = $('#client-form');
    const c = id ? clientById(id) : null;
    clientEditing = c ? c.id : null;
    clientDone = done || null;
    $('#client-title').textContent = c ? 'Edit client' : 'New client';
    $('#client-submit-label').textContent = c ? 'Save changes' : 'Add client';
    f.name.value = c ? c.name : '';
    f.email.value = c ? c.email : '';
    f.address.value = c ? c.address : '';
    setFieldError(f.name, $('#c-name-err'), '');
    setFieldError(f.email, $('#c-email-err'), '');
    clientDlg._onClose = () => { if (clientDone) { const fn = clientDone; clientDone = null; fn(null); } };
    openDialog(clientDlg, opener);
  }
  function clientErrors(f) {
    return {
      name: f.name.value.trim() ? '' : 'Enter the client’s name.',
      email: !f.email.value.trim() || EMAIL_RE.test(f.email.value.trim()) ? '' : 'That doesn’t look like an email address — check for a missing @ or dot.',
    };
  }
  $('#client-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = e.target;
    const errs = clientErrors(f);
    setFieldError(f.name, $('#c-name-err'), errs.name);
    setFieldError(f.email, $('#c-email-err'), errs.email);
    if (errs.name) { f.name.focus(); return; }
    if (errs.email) { f.email.focus(); return; }
    const vals = { name: f.name.value.trim(), email: f.email.value.trim(), address: f.address.value.trim() };
    let c;
    if (clientEditing) { c = clientById(clientEditing); Object.assign(c, vals); }
    else { c = { id: uid(), ...vals }; data.clients.push(c); }
    save();
    const done = clientDone; clientDone = null;
    closeDialog(clientDlg);
    toast(clientEditing ? `Saved ${c.name}.` : `Added ${c.name}.`);
    if (done) done(c);
    else rerenderCurrent();
  });
  ['name', 'email'].forEach((k) => {
    const input = $('#client-form')[k];
    input.addEventListener('input', () => { if (input.getAttribute('aria-invalid')) setFieldError(input, $(`#c-${k}-err`), clientErrors($('#client-form'))[k]); });
    input.addEventListener('blur', () => { if (input.value.trim()) setFieldError(input, $(`#c-${k}-err`), clientErrors($('#client-form'))[k]); });
  });

  // --- Paid
  const paidDlg = $('#paid-dialog');
  function openPaid(inv, opener) {
    const f = $('#paid-form');
    f.paidDate.value = todayISO();
    f.paidDate.min = inv.issueDate || '';
    $('#paid-sub').textContent = `Invoice ${inv.number} becomes read-only until you reopen it.`;
    setFieldError(f.paidDate, $('#paid-date-err'), '');
    openDialog(paidDlg, opener);
  }
  $('#paid-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = e.target;
    const inv = editor && invoiceById(editor.id);
    if (!inv) { closeDialog(paidDlg); return; }
    const v = f.paidDate.value;
    let msg = '';
    if (!isISODate(v)) msg = 'Enter the date you were paid.';
    else if (isISODate(inv.issueDate) && v < inv.issueDate) msg = 'The paid date can’t be before the issue date.';
    setFieldError(f.paidDate, $('#paid-date-err'), msg);
    if (msg) { f.paidDate.focus(); return; }
    inv.status = 'paid';
    inv.paidDate = v;
    touch(inv);
    closeDialog(paidDlg);
    renderEditor();
    toast(`Invoice ${inv.number} marked as paid.`);
    focusAction('reopen');
  });

  // --- Data menu
  const menuBtn = $('#data-menu-btn');
  const menu = $('#data-menu');
  function openMenu() {
    menu.hidden = false; menuBtn.setAttribute('aria-expanded', 'true');
    const first = menu.querySelector('.menu-item'); if (first) first.focus();
  }
  function closeMenu(returnFocus) {
    if (menu.hidden) return;
    menu.hidden = true; menuBtn.setAttribute('aria-expanded', 'false');
    if (returnFocus) menuBtn.focus();
  }
  menuBtn.addEventListener('click', () => (menu.hidden ? openMenu() : closeMenu(true)));
  menu.addEventListener('keydown', (e) => {
    const items = $$('.menu-item', menu);
    const i = items.indexOf(document.activeElement);
    if (e.key === 'Escape') { e.preventDefault(); closeMenu(true); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    else if (e.key === 'Home') { e.preventDefault(); items[0].focus(); }
    else if (e.key === 'End') { e.preventDefault(); items[items.length - 1].focus(); }
  });
  menu.addEventListener('focusout', (e) => { if (!menu.contains(e.relatedTarget) && e.relatedTarget !== menuBtn) closeMenu(false); });
  document.addEventListener('click', (e) => { if (!menu.hidden && !e.target.closest('.menu-wrap')) closeMenu(false); });

  /* ------------------------------------------------------------------ export / import */

  function download(name, text, type) {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function csvCell(v) {
    const s = String(v == null ? '' : v);
    return /[",\r\n]/.test(s) || /^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }

  function exportCSV() {
    const rows = filteredInvoices();
    const lines = ['number,client,issue_date,due_date,currency,total,status'];
    for (const { inv, st, total, client } of rows) {
      lines.push([inv.number, client, inv.issueDate, inv.dueDate, inv.currency, minorToDecimal(total, CURRENCIES[inv.currency].digits), STATUS_LABEL[st]].map(csvCell).join(','));
    }
    download(`invoices-${todayISO()}.csv`, lines.join('\r\n') + '\r\n', 'text/csv;charset=utf-8');
    toast(`Exported ${rows.length} invoice${rows.length === 1 ? '' : 's'} as CSV.`);
  }

  function exportJSON() {
    download(`ledgerly-backup-${todayISO()}.json`, JSON.stringify({ app: 'ledgerly', exportedAt: new Date().toISOString(), ...data }, null, 2), 'application/json');
    toast('Backup downloaded.');
  }

  const fileInput = $('#import-file');
  fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    fileInput.value = '';
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { toast('That file is too large to be a backup (over 5 MB). Nothing was changed.', { error: true }); return; }
    const reader = new FileReader();
    reader.onerror = () => toast('The file couldn’t be read. Nothing was changed.', { error: true });
    reader.onload = () => {
      let parsed;
      try { parsed = JSON.parse(String(reader.result)); }
      catch (e) { toast('That file isn’t valid JSON. Nothing was changed.', { error: true }); return; }
      const res = validateData(parsed);
      if (!res.ok) { toast(`Import rejected: ${res.error} Nothing was changed.`, { error: true }); return; }
      const previous = data;
      data = res.data;
      notice = null; renderBanner();
      save();
      if (current.view === 'editor') go('#/invoices'); else rerenderCurrent();
      toast(`Imported ${data.invoices.length} invoice${data.invoices.length === 1 ? '' : 's'} and ${data.clients.length} client${data.clients.length === 1 ? '' : 's'}.`, {
        action: 'Undo', actionIcon: 'i-undo',
        onAction: () => { data = previous; save(); if (current.view === 'editor') go('#/invoices'); else rerenderCurrent(); toast('Import undone.'); },
      });
    };
    reader.readAsText(file);
  });

  /* ------------------------------------------------------------------ editor */

  function openEditor(inv) {
    const errs = validateInvoice(inv);
    editor = { id: inv.id, touched: new Set(), showAll: inv.flagged && Object.keys(errs).length > 0 };
    document.title = `Invoice ${inv.number || ''} — Ledgerly`;
    renderEditor();
  }

  function leaveEditor() {
    if (!editor) return;
    const inv = invoiceById(editor.id);
    editor = null;
    $('#print-doc').innerHTML = '';
    if (!inv) return;
    const n = Object.keys(validateInvoice(inv)).length;
    inv.flagged = n > 0;
    save();
    if (n) toast(`Draft ${inv.number || ''} kept. ${n} field${n === 1 ? ' needs' : 's need'} attention — they’re marked when you reopen it.`);
  }

  function touch(inv) {
    inv.updatedAt = new Date().toISOString();
    save();
  }

  function updateSaveState() {
    const el = $('#save-state');
    if (!el) return;
    if (saveError) {
      el.className = 'save-state is-error';
      el.innerHTML = `${icon('i-alert')}<span>Couldn’t save — storage is full or blocked</span>`;
    } else if (lastSaved) {
      el.className = 'save-state';
      el.innerHTML = `${icon('i-check')}<span>Saved <time datetime="${lastSaved.toISOString()}">${timeFmt.format(lastSaved)}</time></span>`;
    } else {
      el.className = 'save-state';
      el.innerHTML = `${icon('i-check')}<span>All changes saved</span>`;
    }
  }

  function lineFieldHTML(inv, line, idx, key, label, opts) {
    const id = `l-${line.id}-${key}`;
    const ro = inv.status === 'paid';
    const val = line[key];
    const input = `<input id="${id}" type="text" ${opts.mode ? `inputmode="${opts.mode}"` : ''} value="${esc(val)}"
        data-key="line:${line.id}:${key}" data-line-field="${key}" aria-describedby="${id}-err" ${opts.placeholder ? `placeholder="${opts.placeholder}"` : ''}
        ${ro ? 'disabled' : ''} autocomplete="off" ${key === 'description' ? 'maxlength="300"' : 'maxlength="20"'}>`;
    return `<div class="lf lf-${opts.cls}">
      <label for="${id}" class="line-label-desktop-hidden">${label}<span class="visually-hidden">, line ${idx + 1}</span></label>
      ${opts.affix ? `<div class="input-affix">${input}<span class="affix" aria-hidden="true">${opts.affix}</span></div>` : input}
      <p class="field-error" id="${id}-err" data-err-for="line:${line.id}:${key}" hidden></p>
    </div>`;
  }

  function linesHTML(inv) {
    const ro = inv.status === 'paid';
    if (!inv.lines.length) {
      return `<div class="lines-empty">
        ${icon('i-file', 'icon-lg')}
        <strong>No line items yet</strong>
        <span>${ro ? 'This invoice has no line items.' : 'Add a line for each product or service you’re billing for.'}</span>
      </div>`;
    }
    return `<div class="lines-head" aria-hidden="true">
        <span></span><span>Description</span><span class="r">Qty</span><span class="r">Unit price</span><span class="r">Disc.</span><span class="r">Tax</span><span class="r">Amount</span><span></span>
      </div>
      <ol class="line-list" id="line-list">${inv.lines.map((l, i) => `<li class="line" data-line-id="${esc(l.id)}">
        <button type="button" class="drag-handle" data-line-handle ${ro ? 'disabled' : ''}
          aria-label="Line ${i + 1} of ${inv.lines.length}. Drag to reorder, or press Alt plus Up or Down arrow" aria-keyshortcuts="Alt+ArrowUp Alt+ArrowDown">
          ${icon('i-grip')}<span class="line-num" aria-hidden="true">Line ${i + 1}</span></button>
        ${lineFieldHTML(inv, l, i, 'description', 'Description', { cls: 'desc', placeholder: 'e.g. Brand workshop' })}
        ${lineFieldHTML(inv, l, i, 'quantity', 'Quantity', { cls: 'qty', mode: 'decimal' })}
        ${lineFieldHTML(inv, l, i, 'unitPrice', `Unit price (${inv.currency})`, { cls: 'price', mode: CURRENCIES[inv.currency].digits ? 'decimal' : 'numeric', placeholder: CURRENCIES[inv.currency].digits ? '0.00' : '0' })}
        ${lineFieldHTML(inv, l, i, 'discount', 'Discount', { cls: 'disc', mode: 'decimal', affix: '%' })}
        ${lineFieldHTML(inv, l, i, 'taxRate', 'Tax rate', { cls: 'tax', mode: 'decimal', affix: '%' })}
        <div class="lf lf-total"><span class="amount-label" aria-hidden="true">Amount</span><span><output id="l-${esc(l.id)}-total" aria-label="Amount, line ${i + 1}"></output><span class="disc-note" data-disc-note></span></span></div>
        <button type="button" class="btn btn-ghost btn-icon remove" data-action="remove-line" aria-label="Remove line ${i + 1}" ${ro ? 'disabled' : ''}>${icon('i-trash')}</button>
      </li>`).join('')}</ol>`;
  }

  function renderEditor() {
    const inv = invoiceById(editor.id);
    const app = $('#app');
    const ro = inv.status === 'paid';
    const st = effectiveStatus(inv);
    const dis = ro ? 'disabled' : '';
    const from = inv.from || { name: '', address: '', taxId: '' };
    const profileDiffers = !ro && (from.name !== data.profile.name || from.address !== data.profile.address || from.taxId !== data.profile.taxId) && (data.profile.name || data.profile.address || data.profile.taxId);
    const clientOptions = data.clients.slice().sort((a, b) => a.name.localeCompare(b.name))
      .map((c) => `<option value="${esc(c.id)}" ${c.id === inv.clientId ? 'selected' : ''}>${esc(c.name)}</option>`).join('');

    const fromHTML = from.name || from.address || from.taxId
      ? `<div class="from-name">${esc(from.name || 'Your business')}</div>
         ${from.address ? `<div class="from-lines">${esc(from.address)}</div>` : ''}
         ${from.taxId ? `<div class="from-lines">Tax ID: ${esc(from.taxId)}</div>` : ''}
         ${profileDiffers ? `<button type="button" class="link-btn" data-action="refresh-from">Use current business profile</button>` : ''}`
      : `<div class="from-empty">Your business details aren’t set yet.<br>
         ${profileDiffers ? `<button type="button" class="link-btn" data-action="refresh-from">Use current business profile</button>` : `<button type="button" class="link-btn" data-action="open-settings">Add them in Settings</button>`}</div>`;

    app.innerHTML = `<div class="editor">
      <div class="editor-top">
        <a class="btn btn-ghost back" href="#/invoices">${icon('i-chevron-left')}Invoices</a>
        <div class="editor-title"><h1 id="ed-title">Invoice ${esc(inv.number || 'Untitled')}</h1><span id="ed-badge">${statusBadge(st)}</span></div>
        <div class="save-state" id="save-state" role="status" aria-live="polite"></div>
      </div>
      ${ro ? `<div class="readonly-banner">${icon('i-lock')}<span>Paid on ${fmtDate(inv.paidDate)}. This invoice is read-only — reopen it to make changes.</span>
        <button type="button" class="btn btn-secondary btn-sm" data-action="reopen">${icon('i-unlock')}Reopen</button></div>` : ''}
      <div class="editor-grid">
        <section class="card doc" aria-labelledby="ed-title">
          <div class="doc-head">
            <div class="from"><span class="eyebrow">From</span>${fromHTML}</div>
            <div class="meta-grid">
              <div class="field">
                <label for="f-number">Invoice number</label>
                <input id="f-number" type="text" value="${esc(inv.number)}" data-key="number" aria-describedby="f-number-err" maxlength="40" autocomplete="off" ${dis}>
                <p class="field-error" id="f-number-err" data-err-for="number" hidden></p>
              </div>
              <div class="field">
                <label for="f-currency">Currency</label>
                <select id="f-currency" data-key="currency" ${dis}>${Object.entries(CURRENCIES).map(([k, c]) => `<option value="${k}" ${k === inv.currency ? 'selected' : ''}>${k} — ${c.name}</option>`).join('')}</select>
              </div>
              <div class="field span-2">
                <label for="f-client">Bill to</label>
                <div class="client-select-row">
                  <select id="f-client" data-key="clientId" aria-describedby="f-client-err" ${dis}>
                    <option value="">${data.clients.length ? 'Choose a client…' : 'No clients yet'}</option>
                    ${clientOptions}
                  </select>
                  <button type="button" class="btn btn-secondary btn-icon" data-action="new-client-inline" aria-label="Add a new client" title="Add a new client" ${dis}>${icon('i-plus')}</button>
                </div>
                <p class="field-error" id="f-client-err" data-err-for="clientId" hidden></p>
              </div>
              <div class="field">
                <label for="f-issue">Issue date</label>
                <input id="f-issue" type="date" value="${esc(inv.issueDate)}" data-key="issueDate" aria-describedby="f-issue-err" ${dis}>
                <p class="field-error" id="f-issue-err" data-err-for="issueDate" hidden></p>
              </div>
              <div class="field">
                <label for="f-due">Due date</label>
                <input id="f-due" type="date" value="${esc(inv.dueDate)}" data-key="dueDate" aria-describedby="f-due-err" ${inv.issueDate ? `min="${esc(inv.issueDate)}"` : ''} ${dis}>
                <p class="field-error" id="f-due-err" data-err-for="dueDate" hidden></p>
              </div>
            </div>
          </div>

          <div class="section-head">
            <h2 id="lines-title">Line items</h2>
            ${ro ? '' : `<span class="hint">Reorder by dragging ${icon('i-grip')} or with <kbd>Alt</kbd> + <kbd>↑</kbd>/<kbd>↓</kbd></span>`}
          </div>
          <div id="lines" role="group" aria-labelledby="lines-title">${linesHTML(inv)}</div>
          <p class="field-error lines-error" id="lines-err" data-err-for="lines" hidden></p>
          ${ro ? '' : `<button type="button" class="btn btn-secondary add-line" data-action="add-line">${icon('i-plus')}Add line</button>`}

          <div class="field notes">
            <label for="f-notes">Notes <span class="optional">optional — payment details, thanks, terms</span></label>
            <textarea id="f-notes" data-key="notes" rows="3" maxlength="2000" ${dis}>${esc(inv.notes)}</textarea>
          </div>
        </section>

        <aside class="side" aria-label="Invoice summary and actions">
          <section class="card panel totals" aria-labelledby="totals-title">
            <h2 id="totals-title">Summary</h2>
            <div id="totals"></div>
          </section>
          <section class="card panel" aria-labelledby="actions-title">
            <div class="status-line"><h2 id="actions-title" style="margin:0">Status</h2><span id="side-badge">${statusBadge(st)}</span></div>
            <div class="actions-list">
              ${inv.status === 'draft' ? `<button type="button" class="btn btn-primary btn-block" data-action="mark-sent">${icon('i-send')}Mark as sent</button>` : ''}
              ${inv.status === 'sent' ? `<button type="button" class="btn btn-success btn-block" data-action="mark-paid">${icon('i-check-circle')}Mark as paid…</button>
                <button type="button" class="btn btn-ghost btn-block" data-action="to-draft">${icon('i-rewind')}Move back to draft</button>` : ''}
              ${inv.status === 'paid' ? `<button type="button" class="btn btn-secondary btn-block" data-action="reopen">${icon('i-unlock')}Reopen invoice</button>` : ''}
              <div class="divider" role="presentation"></div>
              <button type="button" class="btn btn-ghost btn-block" data-action="print">${icon('i-printer')}Print or save PDF</button>
              <button type="button" class="btn btn-ghost btn-block" data-action="duplicate">${icon('i-copy')}Duplicate</button>
              <button type="button" class="btn btn-danger-ghost btn-block" data-action="delete-invoice">${icon('i-trash')}Delete invoice</button>
            </div>
          </section>
        </aside>
      </div>
    </div>`;
    updateSaveState();
    refreshEditor();
  }

  // Updates computed output (totals, line amounts, errors, print doc) without touching inputs.
  function refreshEditor() {
    const inv = invoiceById(editor.id);
    if (!inv) return;
    const cur = inv.currency;
    const errs = validateInvoice(inv);

    $$('[data-err-for]').forEach((p) => {
      const key = p.dataset.errFor;
      const show = editor.showAll || editor.touched.has(key);
      const msg = show ? errs[key] : '';
      const input = $(`[data-key="${CSS.escape(key)}"]`);
      if (msg) {
        if (p.hidden || p.dataset.msg !== msg) { p.innerHTML = icon('i-alert') + `<span>${esc(msg)}</span>`; p.dataset.msg = msg; }
        p.hidden = false;
        if (input) input.setAttribute('aria-invalid', 'true');
      } else {
        p.hidden = true; p.innerHTML = ''; p.dataset.msg = '';
        if (input) input.removeAttribute('aria-invalid');
      }
    });

    for (const l of inv.lines) {
      const out = document.getElementById(`l-${l.id}-total`);
      if (!out) continue;
      const a = lineAmounts(l, cur);
      out.textContent = fmtMoney(a.net, cur);
      const note = out.parentElement.querySelector('[data-disc-note]');
      note.textContent = a.discount > 0n ? ` (−${fmtPercent(a.disc)})` : '';
    }

    const t = invoiceTotals(inv);
    const taxRows = t.taxes.length
      ? t.taxes.map((g) => `<dt>Tax ${fmtPercent(g.rate)} <span class="visually-hidden">on ${fmtMoney(g.base, cur)}</span></dt><dd>${fmtMoney(g.tax, cur)}</dd>`).join('')
      : `<dt>Tax</dt><dd>${fmtMoney(0n, cur)}</dd>`;
    $('#totals').innerHTML = `<dl>
        <dt>Subtotal</dt><dd>${fmtMoney(t.subtotal, cur)}</dd>
        <dt>Discount</dt><dd>${t.discount > 0n ? '−' : ''}${fmtMoney(t.discount, cur)}</dd>
        ${taxRows}
        <dt class="grand-dt">Total ${esc(cur)}</dt><dd class="grand-dd" id="grand-total">${fmtMoney(t.total, cur)}</dd>
      </dl>
      ${inv.status === 'paid' ? `<p class="paid-note">${icon('i-check-circle')}Paid in full on ${fmtDate(inv.paidDate)}</p>` : ''}`;

    if (inv.flagged && !Object.keys(errs).length) { inv.flagged = false; save(); }
    renderPrint(inv, t);
  }

  function renderPrint(inv, t) {
    const cur = inv.currency;
    const c = clientById(inv.clientId);
    const from = inv.from || {};
    const st = effectiveStatus(inv);
    $('#print-doc').innerHTML = `
      <header class="pd-head">
        <div>
          <div class="pd-title">Invoice</div>
          <div class="pd-number">No. ${esc(inv.number)}</div>
          ${st === 'paid' ? `<div class="pd-stamp">Paid ${fmtDate(inv.paidDate)}</div>` : ''}
        </div>
        <div class="pd-from"><strong>${esc(from.name || '')}</strong>${esc(from.address || '')}${from.taxId ? `\nTax ID: ${esc(from.taxId)}` : ''}</div>
      </header>
      <section class="pd-parties">
        <div><div class="pd-label">Bill to</div><div class="pd-billto"><strong>${esc(c ? c.name : '—')}</strong>${c && c.address ? `\n${esc(c.address)}` : ''}${c && c.email ? `\n${esc(c.email)}` : ''}</div></div>
        <div><dl class="pd-dates"><dt>Issue date</dt><dd>${fmtDate(inv.issueDate)}</dd><dt>Due date</dt><dd>${fmtDate(inv.dueDate)}</dd><dt>Currency</dt><dd>${esc(cur)}</dd></dl></div>
      </section>
      <table class="pd-table">
        <thead><tr><th>Description</th><th class="r">Qty</th><th class="r">Unit price</th><th class="r">Discount</th><th class="r">Tax</th><th class="r">Amount</th></tr></thead>
        <tbody>${inv.lines.map((l) => {
          const a = lineAmounts(l, cur);
          const p = parseDecimal(l.unitPrice, CURRENCIES[cur].digits);
          return `<tr><td>${esc(l.description)}</td><td class="r">${esc(l.quantity)}</td><td class="r">${fmtMoney(p.error ? 0n : p.value, cur)}</td>
            <td class="r">${a.disc > 0n ? fmtPercent(a.disc) : '—'}</td><td class="r">${fmtPercent(a.rate)}</td><td class="r">${fmtMoney(a.net, cur)}</td></tr>`;
        }).join('')}</tbody>
      </table>
      <section class="pd-totals"><dl>
        <dt>Subtotal</dt><dd>${fmtMoney(t.subtotal, cur)}</dd>
        ${t.discount > 0n ? `<dt>Discount</dt><dd>−${fmtMoney(t.discount, cur)}</dd>` : ''}
        ${t.taxes.map((g) => `<dt>Tax ${fmtPercent(g.rate)}</dt><dd>${fmtMoney(g.tax, cur)}</dd>`).join('')}
        <dt class="grand">Total due</dt><dd class="grand">${fmtMoney(t.total, cur)}</dd>
      </dl></section>
      ${inv.notes ? `<section class="pd-notes"><div class="pd-label">Notes</div>${esc(inv.notes)}</section>` : ''}`;
  }

  function editorInvoice() { return editor ? invoiceById(editor.id) : null; }

  function focusAction(action) {
    const b = $(`#app [data-action="${action}"]`);
    if (b) b.focus();
  }

  function rerenderLines(focus) {
    const inv = editorInvoice();
    $('#lines').innerHTML = linesHTML(inv);
    refreshEditor();
    if (focus) {
      const el = focus.lineId ? $(`.line[data-line-id="${CSS.escape(focus.lineId)}"] ${focus.sel}`) : null;
      if (el) el.focus();
    }
  }

  function moveLine(lineId, delta, focusSel) {
    const inv = editorInvoice();
    const i = inv.lines.findIndex((l) => l.id === lineId);
    const j = i + delta;
    if (i < 0 || j < 0 || j >= inv.lines.length) { announce(delta < 0 ? 'Already the first line.' : 'Already the last line.'); return; }
    const [l] = inv.lines.splice(i, 1);
    inv.lines.splice(j, 0, l);
    touch(inv);
    rerenderLines({ lineId, sel: focusSel });
    const li = $(`.line[data-line-id="${CSS.escape(lineId)}"]`);
    if (li) li.classList.add('just-moved');
    announce(`Line moved to position ${j + 1} of ${inv.lines.length}.`);
  }

  function selectorFor(el) {
    if (el.matches('[data-line-handle]')) return '[data-line-handle]';
    if (el.dataset.lineField) return `[data-line-field="${el.dataset.lineField}"]`;
    if (el.matches('[data-action="remove-line"]')) return '[data-action="remove-line"]';
    return '[data-line-handle]';
  }

  // Editor input handling (autosave on every keystroke)
  function onEditorInput(e) {
    const inv = editorInvoice();
    if (!inv || inv.status === 'paid') return;
    const t = e.target;
    const key = t.dataset.key;
    if (!key) return;
    if (t.dataset.lineField) {
      const lineId = t.closest('.line').dataset.lineId;
      const line = inv.lines.find((l) => l.id === lineId);
      if (!line) return;
      line[t.dataset.lineField] = t.value;
    } else if (key === 'clientId') {
      inv.clientId = t.value;
      editor.touched.add('clientId');
    } else if (key === 'currency') {
      inv.currency = t.value;
      touch(inv);
      // placeholders/inputmode for price fields depend on the currency
      $$('[data-line-field="unitPrice"]').forEach((el) => {
        el.placeholder = CURRENCIES[inv.currency].digits ? '0.00' : '0';
        el.inputMode = CURRENCIES[inv.currency].digits ? 'decimal' : 'numeric';
        const lab = $(`label[for="${el.id}"]`);
        if (lab) lab.firstChild.textContent = `Unit price (${inv.currency})`;
      });
      refreshEditor();
      announce(`Currency changed to ${CURRENCIES[inv.currency].name}. Amounts reformatted.`);
      return;
    } else {
      inv[key] = t.value;
      if (key === 'number') $('#ed-title').textContent = `Invoice ${inv.number || 'Untitled'}`;
      if (key === 'issueDate') { const due = $('#f-due'); if (isISODate(inv.issueDate)) due.min = inv.issueDate; else due.removeAttribute('min'); editor.touched.add('dueDate'); }
      if (key === 'dueDate' || key === 'issueDate') editor.touched.add(key);
      if (key === 'dueDate') {
        const st = effectiveStatus(inv);
        $('#ed-badge').innerHTML = statusBadge(st); $('#side-badge').innerHTML = statusBadge(st);
      }
    }
    touch(inv);
    refreshEditor();
  }

  /* ------------------------------------------------------------------ drag to reorder (pointer events: mouse, pen, touch) */

  let drag = null;
  function onPointerDown(e) {
    const handle = e.target.closest('[data-line-handle]');
    if (!handle || handle.disabled || e.button !== 0) return;
    const li = handle.closest('.line');
    e.preventDefault();
    handle.focus({ preventScroll: true });
    handle.setPointerCapture(e.pointerId);
    drag = { handle, li, list: li.parentElement, startIndex: Array.prototype.indexOf.call(li.parentElement.children, li), pointerId: e.pointerId, moved: false, lastY: e.clientY, offset: 0 };
    li.classList.add('dragging');
  }
  function onPointerMove(e) {
    if (!drag || e.pointerId !== drag.pointerId) return;
    e.preventDefault();
    const { li, list } = drag;
    const y = e.clientY;
    // Move siblings rather than the dragged node so pointer capture is never lost.
    let prev = li.previousElementSibling, next = li.nextElementSibling;
    if (next) {
      const r = next.getBoundingClientRect();
      if (y > r.top + r.height / 2) { list.insertBefore(next, li); drag.moved = true; }
    }
    if (prev) {
      const r = prev.getBoundingClientRect();
      if (y < r.top + r.height / 2) { list.insertBefore(prev, li.nextElementSibling); drag.moved = true; }
    }
    // Auto-scroll near viewport edges
    if (y < 70) window.scrollBy(0, -12); else if (y > window.innerHeight - 50) window.scrollBy(0, 12);
  }
  function onPointerUp(e) {
    if (!drag || e.pointerId !== drag.pointerId) return;
    const { li, list, handle } = drag;
    li.classList.remove('dragging');
    try { handle.releasePointerCapture(e.pointerId); } catch (err) { /* already released */ }
    const inv = editorInvoice();
    const order = $$('.line', list).map((n) => n.dataset.lineId);
    const newIndex = order.indexOf(li.dataset.lineId);
    const changed = newIndex !== drag.startIndex;
    const lineId = li.dataset.lineId;
    drag = null;
    if (inv && changed) {
      inv.lines.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
      touch(inv);
      rerenderLines({ lineId, sel: '[data-line-handle]' });
      announce(`Line moved to position ${newIndex + 1} of ${inv.lines.length}.`);
    }
  }

  /* ------------------------------------------------------------------ global events */

  function rerenderCurrent() {
    if (current.view === 'clients') renderClients();
    else if (current.view === 'editor' && editor) renderEditor();
    else renderList();
  }

  function handleAction(action, btn, e) {
    const inv = editorInvoice();
    switch (action) {
      case 'dismiss-banner': notice = null; renderBanner(); $('#main').focus(); break;
      case 'open-settings': closeMenu(false); openSettings(btn); break;
      case 'export-csv': closeMenu(true); exportCSV(); break;
      case 'export-json': closeMenu(true); exportJSON(); break;
      case 'import-json': closeMenu(true); fileInput.click(); break;
      case 'new-invoice': { const v = createInvoice(); pendingFocus = 'new'; go(`#/invoice/${encodeURIComponent(v.id)}`); break; }
      case 'new-client': openClient(null, btn); break;
      case 'edit-client': ui.clientMsg = null; openClient(btn.dataset.id, btn); break;
      case 'delete-client': deleteClient(btn.dataset.id, btn); break;
      case 'dismiss-client-msg': { const id = ui.clientMsg && ui.clientMsg.id; ui.clientMsg = null; renderClients(); const b = id && $(`.client[data-id="${CSS.escape(id)}"] [data-action="delete-client"]`); if (b) b.focus(); break; }
      case 'filter': ui.filter = btn.dataset.filter; $$('.chip').forEach((c) => c.setAttribute('aria-pressed', String(c === btn))); renderListBody(); break;
      case 'clear-filters': ui.filter = 'all'; ui.query = ''; renderList(); { const s = $('#inv-search'); if (s) s.focus(); } break;

      case 'new-client-inline': {
        if (!inv) break;
        openClient(null, btn, (c) => {
          if (!c) return;
          inv.clientId = c.id; touch(inv);
          renderEditor();
          const sel = $('#f-client'); if (sel) sel.focus();
        });
        break;
      }
      case 'refresh-from': if (inv) { inv.from = profileSnapshot(); touch(inv); renderEditor(); focusAction('print'); toast('Business details updated on this invoice.'); } break;
      case 'add-line': {
        if (!inv || inv.status === 'paid') break;
        const l = newLine(inv);
        inv.lines.push(l);
        touch(inv);
        rerenderLines({ lineId: l.id, sel: '[data-line-field="description"]' });
        announce(`Line ${inv.lines.length} added.`);
        break;
      }
      case 'remove-line': {
        if (!inv || inv.status === 'paid') break;
        const li = btn.closest('.line');
        const idx = inv.lines.findIndex((l) => l.id === li.dataset.lineId);
        const [removed] = inv.lines.splice(idx, 1);
        touch(inv);
        const neighbour = inv.lines[Math.min(idx, inv.lines.length - 1)];
        rerenderLines(neighbour ? { lineId: neighbour.id, sel: '[data-action="remove-line"]' } : null);
        if (!neighbour) { const a = $('[data-action="add-line"]'); if (a) a.focus(); }
        toast(`Removed line${removed.description ? ` “${removed.description}”` : ''}.`, {
          action: 'Undo', actionIcon: 'i-undo',
          onAction: () => {
            const v = invoiceById(inv.id);
            if (!v || v.status === 'paid') return;
            v.lines.splice(Math.min(idx, v.lines.length), 0, removed); touch(v);
            if (editor && editor.id === v.id) rerenderLines({ lineId: removed.id, sel: '[data-line-field="description"]' });
          },
        });
        break;
      }
      case 'mark-sent': {
        if (!inv) break;
        const errs = validateInvoice(inv);
        if (Object.keys(errs).length) {
          editor.showAll = true;
          refreshEditor();
          const firstKey = Object.keys(errs)[0];
          const el = $(`[data-key="${CSS.escape(firstKey)}"]`) || $('[data-action="add-line"]');
          if (el) el.focus();
          const n = Object.keys(errs).length;
          toast(`Fix ${n} marked field${n === 1 ? '' : 's'} before sending.`, { error: true });
          break;
        }
        inv.status = 'sent'; inv.flagged = false; touch(inv);
        renderEditor();
        toast(`Invoice ${inv.number} marked as sent.`);
        focusAction('mark-paid');
        break;
      }
      case 'mark-paid': if (inv) openPaid(inv, btn); break;
      case 'to-draft': if (inv) { inv.status = 'draft'; touch(inv); renderEditor(); toast(`Invoice ${inv.number} is a draft again.`); focusAction('mark-sent'); } break;
      case 'reopen': if (inv) { inv.status = 'sent'; inv.paidDate = ''; touch(inv); renderEditor(); toast(`Invoice ${inv.number} reopened — you can edit it again.`); focusAction('mark-paid'); } break;
      case 'print': window.print(); break;
      case 'duplicate': {
        if (!inv) break;
        const today = todayISO();
        const term = isISODate(inv.issueDate) && isISODate(inv.dueDate) ? Math.max(0, diffDays(inv.issueDate, inv.dueDate)) : DEFAULT_TERM_DAYS;
        const copy = JSON.parse(JSON.stringify(inv));
        Object.assign(copy, {
          id: uid(), number: nextNumber(today.slice(0, 4)), issueDate: today, dueDate: addDays(today, term),
          status: 'draft', paidDate: '', flagged: false, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
        });
        copy.lines = copy.lines.map((l) => ({ ...l, id: uid() }));
        data.invoices.push(copy);
        save();
        go(`#/invoice/${encodeURIComponent(copy.id)}`);
        toast(`Duplicated as ${copy.number} (draft).`);
        break;
      }
      case 'delete-invoice': {
        if (!inv) break;
        if (!window.confirm(`Delete invoice ${inv.number || 'Untitled'}? This can’t be undone.`)) break;
        const num = inv.number;
        data.invoices = data.invoices.filter((v) => v.id !== inv.id);
        editor = null;
        save();
        go('#/invoices');
        toast(`Deleted invoice ${num || 'Untitled'}.`);
        break;
      }
      default: break;
    }
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (btn && !btn.disabled) { handleAction(btn.dataset.action, btn, e); return; }
    // Whole-row click opens the invoice (the number link stays the keyboard target)
    const row = e.target.closest('.inv-row');
    if (row && !e.target.closest('a, button')) go(`#/invoice/${encodeURIComponent(row.dataset.id)}`);
  });

  const app = $('#app');
  app.addEventListener('input', (e) => {
    if (e.target.id === 'inv-search') { ui.query = e.target.value; renderListBody(); return; }
    if (current.view === 'editor') onEditorInput(e);
  });
  app.addEventListener('change', (e) => {
    if (e.target.id === 'inv-sort') { ui.sort = e.target.value; renderListBody(); return; }
  });
  app.addEventListener('focusout', (e) => {
    if (current.view !== 'editor' || !editor) return;
    const key = e.target.dataset && e.target.dataset.key;
    if (key && !editor.touched.has(key)) { editor.touched.add(key); refreshEditor(); }
  });
  app.addEventListener('keydown', (e) => {
    if (current.view !== 'editor' || !editor) return;
    if (e.altKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
      const li = e.target.closest('.line');
      const inv = editorInvoice();
      if (!li || !inv || inv.status === 'paid') return;
      e.preventDefault();
      moveLine(li.dataset.lineId, e.key === 'ArrowUp' ? -1 : 1, selectorFor(e.target));
    } else if (e.key === 'Enter' && e.target.dataset.lineField && !e.isComposing) {
      // Enter on the last line's field adds a new line — a fast keyboard flow
      const li = e.target.closest('.line');
      if (li && !li.nextElementSibling) { e.preventDefault(); handleAction('add-line', null, e); }
    }
  });
  app.addEventListener('pointerdown', onPointerDown);
  app.addEventListener('pointermove', onPointerMove);
  app.addEventListener('pointerup', onPointerUp);
  app.addEventListener('pointercancel', onPointerUp);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !menu.hidden) closeMenu(true);
  });

  window.addEventListener('hashchange', onRoute);
  window.addEventListener('beforeprint', () => {
    if (!editor) { /* printing outside the editor prints nothing app-specific */ }
  });
  window.addEventListener('pagehide', () => {
    if (editor) { const inv = editorInvoice(); if (inv) { inv.flagged = Object.keys(validateInvoice(inv)).length > 0; save(); } }
  });

  // Keep "Overdue" fresh if the tab stays open past midnight
  setInterval(() => { if (current.view === 'invoices') renderListBody(); }, 60 * 60 * 1000);

  renderBanner();
  onRoute();
})();
