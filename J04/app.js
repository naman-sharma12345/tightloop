/* Folio: a small invoice builder. Plain JavaScript, no dependencies. */
(() => {
  'use strict';

  // ---------------------------------------------------------------- constants

  const KEY = 'r11-invoice-builder';
  const CURRENCIES = ['USD', 'EUR', 'GBP', 'INR', 'JPY'];
  const CURRENCY_INFO = {
    USD: { locale: 'en-US', name: 'US dollar' },
    EUR: { locale: 'de-DE', name: 'Euro' },
    GBP: { locale: 'en-GB', name: 'British pound' },
    INR: { locale: 'en-IN', name: 'Indian rupee' },
    JPY: { locale: 'ja-JP', name: 'Japanese yen' },
  };
  const STATUSES = ['draft', 'sent', 'paid'];
  const STATUS_META = {
    draft: { label: 'Draft', icon: 'pencil' },
    sent: { label: 'Sent', icon: 'send' },
    overdue: { label: 'Overdue', icon: 'clock' },
    paid: { label: 'Paid', icon: 'check-circle' },
  };
  const FILTERS = ['all', 'draft', 'sent', 'overdue', 'paid'];
  const LINE_PROPS = ['description', 'quantity', 'unitPrice', 'discount', 'taxRate'];
  const CSV_HEADER = 'number,client,issue_date,due_date,currency,total,status';

  // ---------------------------------------------------------------- helpers

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ESC[c]);
  const icon = (name, cls = '') =>
    `<svg class="icon ${cls}" aria-hidden="true" focusable="false"><use href="#i-${name}"></use></svg>`;
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const plural = (n, one, many = one + 's') => `${n} ${n === 1 ? one : many}`;
  const isObj = (v) => !!v && typeof v === 'object' && !Array.isArray(v);

  // Dates are stored as local ISO strings (YYYY-MM-DD).
  const pad = (n) => String(n).padStart(2, '0');
  const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const todayISO = () => toISO(new Date());
  function isISO(s) {
    if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
    const [y, m, d] = s.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    return dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d;
  }
  const fromISO = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
  const addDays = (s, n) => { const d = fromISO(s); d.setDate(d.getDate() + n); return toISO(d); };
  const daysBetween = (a, b) => Math.round((Date.UTC(...b.split('-').map((v, i) => (i === 1 ? v - 1 : +v))) -
    Date.UTC(...a.split('-').map((v, i) => (i === 1 ? v - 1 : +v)))) / 86400000);
  const dateFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  const timeFmt = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', second: '2-digit' });
  const fmtDate = (s) => (isISO(s) ? dateFmt.format(fromISO(s)) : '—');

  // ---------------------------------------------------------------- money
  // All amounts are BigInt minor units. Inputs are kept as the strings the
  // user typed so a draft with a typo survives a reload.

  const digitCache = {};
  function curDigits(cur) {
    if (!(cur in digitCache)) {
      digitCache[cur] = new Intl.NumberFormat('en', { style: 'currency', currency: cur })
        .resolvedOptions().maximumFractionDigits;
    }
    return digitCache[cur];
  }
  const fmtCache = {};
  function moneyFormatter(cur) {
    if (!fmtCache[cur]) {
      fmtCache[cur] = new Intl.NumberFormat(CURRENCY_INFO[cur].locale, { style: 'currency', currency: cur });
    }
    return fmtCache[cur];
  }
  function toMajorString(minor, digits) {
    const neg = minor < 0n;
    let s = (neg ? -minor : minor).toString();
    if (digits === 0) return (neg ? '-' : '') + s;
    s = s.padStart(digits + 1, '0');
    return (neg ? '-' : '') + s.slice(0, -digits) + '.' + s.slice(-digits);
  }
  function fmtMoney(minor, cur) {
    const str = toMajorString(minor, curDigits(cur));
    // Strings keep full decimal precision where Intl supports it.
    try { return moneyFormatter(cur).format(str); } catch (e) { return moneyFormatter(cur).format(Number(str)); }
  }
  // Integer division rounding half away from zero.
  function roundDiv(n, d) {
    const neg = n < 0n;
    const a = neg ? -n : n;
    const q = (2n * a + d) / (2n * d);
    return neg ? -q : q;
  }
  // Parse a non-negative decimal string into an integer scaled by 10^scale.
  function parseDec(raw, scale) {
    const s = String(raw ?? '').trim();
    if (!s) return { err: 'empty' };
    if (s.startsWith('-')) return { err: 'neg' };
    const m = /^(\d*)(?:\.(\d*))?$/.exec(s);
    if (!m || (!m[1] && !m[2])) return { err: 'nan' };
    const frac = (m[2] || '').replace(/0+$/, '');
    if (frac.length > scale) return { err: 'dec' };
    return { v: BigInt((m[1] || '0') + frac.padEnd(scale, '0')) };
  }
  // Percentages 0-100 with up to 2 decimals, scaled by 100. Empty means 0.
  function parsePct(raw) {
    if (!String(raw ?? '').trim()) return { v: 0n };
    const r = parseDec(raw, 2);
    if (r.err === 'dec') return { err: 'Max. 2 decimals.' };
    if (r.err || r.v > 10000n) return { err: 'Use 0 to 100.' };
    return r;
  }
  const fmtRate = (rate100) => `${Number(rate100) / 100}%`;

  function lineCalc(line, cur) {
    const d = curDigits(cur);
    const errors = {};
    if (!String(line.description || '').trim()) errors.description = 'Add a description.';
    const q = parseDec(line.quantity, 2);
    if (q.err) {
      errors.quantity = {
        empty: 'Enter a quantity.', neg: 'Must be more than 0.',
        nan: 'Use a number like 1.5.', dec: 'Max. 2 decimals.',
      }[q.err];
    } else if (q.v === 0n) errors.quantity = 'Must be more than 0.';
    const p = parseDec(line.unitPrice, d);
    if (p.err) {
      errors.unitPrice = {
        empty: 'Enter a price (0 is fine).', neg: "Can't be negative.",
        nan: 'Use a number like 99.5.',
        dec: d === 0 ? `${cur} has no cents. Use a whole number.` : `Max. ${d} decimals.`,
      }[p.err];
    }
    const disc = parsePct(line.discount);
    if (disc.err) errors.discount = disc.err;
    const tax = parsePct(line.taxRate);
    if (tax.err) errors.taxRate = tax.err;

    let calc = null;
    if (!errors.quantity && !errors.unitPrice && !errors.discount && !errors.taxRate) {
      const raw = q.v * p.v; // minor units x 100
      const gross = roundDiv(raw, 100n);
      const discount = roundDiv(raw * disc.v, 1000000n);
      const net = gross - discount;
      calc = { gross, discount, net, tax: roundDiv(net * tax.v, 10000n), rate: tax.v };
    }
    return { errors, calc };
  }

  function invoiceCalc(inv) {
    const errors = {};
    const lines = {};
    let subtotal = 0n, discount = 0n, taxTotal = 0n, invalidLines = 0;
    const taxes = new Map();

    const num = inv.number.trim();
    if (!num) errors.number = 'Give this invoice a number.';
    else if (state.invoices.some((o) => o.id !== inv.id && o.number.trim().toLowerCase() === num.toLowerCase())) {
      errors.number = `${num} is already used by another invoice. Pick a different number.`;
    }
    if (!inv.clientId || !findClient(inv.clientId)) errors.client = 'Choose who this invoice is for.';
    if (!isISO(inv.issueDate)) errors.issueDate = 'Pick an issue date.';
    if (!isISO(inv.dueDate)) errors.dueDate = 'Pick a due date.';
    else if (isISO(inv.issueDate) && inv.dueDate < inv.issueDate) errors.dueDate = "Due date can't be before the issue date.";
    if (!inv.lines.length) errors.lines = 'Add at least one line item.';

    for (const line of inv.lines) {
      const r = lineCalc(line, inv.currency);
      for (const [k, msg] of Object.entries(r.errors)) errors[`l-${line.id}-${k}`] = msg;
      if (!r.calc) { invalidLines++; continue; }
      const c = r.calc;
      lines[line.id] = c;
      subtotal += c.gross;
      discount += c.discount;
      taxTotal += c.tax;
      if (c.rate > 0n) {
        const g = taxes.get(c.rate) || { base: 0n, tax: 0n };
        g.base += c.net;
        g.tax += c.tax;
        taxes.set(c.rate, g);
      }
    }
    const taxList = [...taxes.entries()]
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
      .map(([rate, g]) => ({ rate, ...g }));
    return {
      errors, lines, subtotal, discount, taxes: taxList, taxTotal,
      total: subtotal - discount + taxTotal, invalidLines,
      valid: Object.keys(errors).length === 0,
    };
  }

  // ---------------------------------------------------------------- state

  let state = emptyState();
  let storageOk = true;
  let lastSavedAt = null;

  function emptyState() {
    return { version: 1, profile: { name: '', address: '', taxId: '', currency: 'USD', taxRate: '0' }, clients: [], invoices: [] };
  }

  // Strict shape check used both for localStorage and for imports. Throws
  // with a plain-language reason when something is off.
  function normalizeState(input) {
    let obj = input;
    if (isObj(obj) && isObj(obj.data) && !('invoices' in obj)) obj = obj.data;
    if (!isObj(obj)) throw new Error("it isn't a Folio backup");
    if (!Array.isArray(obj.clients) || !Array.isArray(obj.invoices)) throw new Error('the clients or invoices list is missing');
    const str = (v, what) => {
      if (v == null) return '';
      if (typeof v === 'string') return v;
      if (typeof v === 'number' && Number.isFinite(v)) return String(v);
      throw new Error(`${what} has an unexpected value`);
    };
    const p = obj.profile == null ? {} : obj.profile;
    if (!isObj(p)) throw new Error('the business profile is malformed');
    const pCur = p.currency == null || p.currency === '' ? 'USD' : p.currency;
    if (!CURRENCIES.includes(pCur)) throw new Error(`the default currency "${pCur}" isn't supported`);
    const profile = {
      name: str(p.name, 'The business name'), address: str(p.address, 'The business address'),
      taxId: str(p.taxId, 'The tax ID'), currency: pCur, taxRate: str(p.taxRate, 'The default tax rate') || '0',
    };
    if (parsePct(profile.taxRate).err) throw new Error('the default tax rate is not between 0 and 100');

    const clientIds = new Set();
    const clients = obj.clients.map((c, i) => {
      const where = `client ${i + 1}`;
      if (!isObj(c)) throw new Error(`${where} is malformed`);
      const id = str(c.id, `The id of ${where}`);
      if (!id || clientIds.has(id)) throw new Error(`${where} has a missing or duplicate id`);
      const name = str(c.name, `The name of ${where}`).trim();
      if (!name) throw new Error(`${where} has no name`);
      clientIds.add(id);
      return { id, name, email: str(c.email, `The email of ${where}`).trim(), address: str(c.address, `The address of ${where}`) };
    });

    const invIds = new Set();
    const invoices = obj.invoices.map((v, i) => {
      const where = `invoice ${i + 1}`;
      if (!isObj(v)) throw new Error(`${where} is malformed`);
      const id = str(v.id, `The id of ${where}`);
      if (!id || invIds.has(id)) throw new Error(`${where} has a missing or duplicate id`);
      invIds.add(id);
      let status = String(v.status ?? 'draft').toLowerCase();
      if (status === 'overdue') status = 'sent';
      if (!STATUSES.includes(status)) throw new Error(`${where} has an unknown status`);
      const currency = v.currency == null ? profile.currency : v.currency;
      if (!CURRENCIES.includes(currency)) throw new Error(`${where} uses an unsupported currency`);
      const clientId = str(v.clientId, `The client of ${where}`);
      if (clientId && !clientIds.has(clientId)) throw new Error(`${where} points to a client that doesn't exist`);
      if (!Array.isArray(v.lines)) throw new Error(`${where} has no line items list`);
      const lineIds = new Set();
      const lines = v.lines.map((l, j) => {
        if (!isObj(l)) throw new Error(`line ${j + 1} of ${where} is malformed`);
        let lid = str(l.id, 'A line id');
        if (!lid || lineIds.has(lid)) lid = uid() + j;
        lineIds.add(lid);
        const out = { id: lid };
        for (const k of LINE_PROPS) out[k] = str(l[k], `A line of ${where}`);
        return out;
      });
      const num = (x) => (typeof x === 'number' && Number.isFinite(x) ? x : Date.now());
      return {
        id, number: str(v.number, `The number of ${where}`), clientId,
        issueDate: str(v.issueDate, 'A date'), dueDate: str(v.dueDate, 'A date'), currency, status,
        paidDate: status === 'paid' ? str(v.paidDate, 'A date') : '', notes: str(v.notes, 'Notes'), lines,
        showErrors: !!v.showErrors, createdAt: num(v.createdAt), updatedAt: num(v.updatedAt),
      };
    });
    return { version: 1, profile, clients, invoices };
  }

  function loadState() {
    let raw = null;
    try { raw = localStorage.getItem(KEY); } catch (e) { storageOk = false; return 'blocked'; }
    if (raw == null) return null;
    try { state = normalizeState(JSON.parse(raw)); return null; } catch (e) { state = emptyState(); return 'corrupt'; }
  }

  function persist() {
    if (!storageOk) return false;
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
      lastSavedAt = new Date();
      updateSavedIndicator();
      return true;
    } catch (e) {
      toast("Couldn't save your changes. Browser storage may be full or turned off.", 'error');
      return false;
    }
  }

  const findClient = (id) => state.clients.find((c) => c.id === id);
  const findInvoice = (id) => state.invoices.find((v) => v.id === id);
  const clientName = (inv) => findClient(inv.clientId)?.name || '';
  const touchInvoice = (inv) => { inv.updatedAt = Date.now(); };
  function effStatus(inv) {
    if (inv.status === 'sent' && isISO(inv.dueDate) && inv.dueDate < todayISO()) return 'overdue';
    return inv.status;
  }
  function nextNumber(year = todayISO().slice(0, 4)) {
    const re = new RegExp(`^${year}-(\\d+)$`);
    let max = 0;
    for (const inv of state.invoices) {
      const m = re.exec(inv.number.trim());
      if (m) max = Math.max(max, parseInt(m[1], 10));
    }
    return `${year}-${String(max + 1).padStart(4, '0')}`;
  }
  const newLine = () => ({
    id: uid(), description: '', quantity: '1', unitPrice: '', discount: '0', taxRate: state.profile.taxRate || '0',
  });

  // ---------------------------------------------------------------- ui state

  const ui = {
    filter: 'all', search: '', sort: 'date-desc',
    touched: new Set(),
    route: null,
    clientDialog: null,
  };
  const main = $('#main');

  // ---------------------------------------------------------------- small ui pieces

  function badge(st) {
    const m = STATUS_META[st];
    return `<span class="badge badge-${st}">${icon(m.icon)}<span>${m.label}</span></span>`;
  }
  function emptyState_({ ic, title, text, action = '' }) {
    return `<div class="empty">
      <div class="empty-art" aria-hidden="true">${icon(ic)}</div>
      <h2 class="empty-title">${title}</h2>
      <p class="empty-text">${text}</p>
      ${action}
    </div>`;
  }
  function button(action, ic, label, variant = 'secondary', extra = '') {
    return `<button type="button" class="btn btn-${variant}" data-action="${action}" ${extra}>${icon(ic)}<span>${label}</span></button>`;
  }
  function currencyOptions(selected) {
    return CURRENCIES.map((c) =>
      `<option value="${c}" ${c === selected ? 'selected' : ''}>${c} · ${CURRENCY_INFO[c].name}</option>`).join('');
  }

  function toast(msg, kind = 'success') {
    const t = document.createElement('div');
    t.className = `toast toast-${kind}`;
    t.innerHTML = `${icon(kind === 'error' ? 'alert' : kind === 'info' ? 'info' : 'check-circle')}<span>${esc(msg)}</span>`;
    $('#toasts').append(t);
    setTimeout(() => {
      t.classList.add('is-leaving');
      setTimeout(() => t.remove(), 250);
    }, kind === 'error' ? 7000 : 4200);
  }
  function announce(msg) {
    const a = $('#announcer');
    a.textContent = '';
    setTimeout(() => { a.textContent = msg; }, 30);
  }
  function showNotice(kind) {
    const text = kind === 'corrupt'
      ? "We couldn't read your saved data, so Folio started with an empty workspace. Anything you add from now on will be saved."
      : "Your browser is blocking local storage, so changes will be lost when you close this tab.";
    $('#notice').innerHTML = `<div class="banner banner-warn" role="alert">${icon('alert')}
      <p>${text}</p>
      <button type="button" class="btn btn-ghost btn-sm" data-action="dismiss-notice">Dismiss</button></div>`;
  }

  // ---------------------------------------------------------------- routing

  function parseRoute() {
    const parts = location.hash.replace(/^#\/?/, '').split('/');
    if (parts[0] === 'invoice' && parts[1]) return { view: 'editor', id: decodeURIComponent(parts[1]) };
    if (parts[0] === 'clients') return { view: 'clients' };
    return { view: 'invoices' };
  }

  function leaveEditor(id) {
    ui.touched.clear();
    const inv = findInvoice(id);
    if (!inv || inv.status === 'paid') return;
    const calc = invoiceCalc(inv);
    if (calc.valid) {
      if (inv.showErrors) { inv.showErrors = false; persist(); }
      return;
    }
    inv.showErrors = true;
    persist();
    const n = Object.keys(calc.errors).length;
    toast(`Draft ${inv.number || ''} kept. ${plural(n, 'field')} still ${n === 1 ? 'needs' : 'need'} attention and ${n === 1 ? 'is' : 'are'} marked in the editor.`, 'info');
  }

  function render(focus) {
    const r = ui.route;
    const printable = r.view === 'editor' && !!findInvoice(r.id);
    document.body.classList.toggle('has-print-doc', printable);
    if (!printable) $('#print-doc').innerHTML = '';
    if (r.view === 'editor') {
      const inv = findInvoice(r.id);
      if (inv) renderEditor(inv); else renderMissing();
    } else if (r.view === 'clients') renderClients();
    else renderInvoices();
    $$('.nav-link').forEach((a) => {
      const on = a.dataset.nav === (r.view === 'clients' ? 'clients' : 'invoices');
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    if (focus) {
      window.scrollTo(0, 0);
      $('h1', main)?.focus({ preventScroll: true });
    }
  }

  function onRoute() {
    const prev = ui.route;
    const next = parseRoute();
    if (prev && prev.view === 'editor' && !(next.view === 'editor' && next.id === prev.id)) leaveEditor(prev.id);
    ui.route = next;
    render(true);
  }

  // ---------------------------------------------------------------- invoices list

  function renderInvoices() {
    document.title = 'Invoices · Folio';
    const counts = { all: 0, draft: 0, sent: 0, overdue: 0, paid: 0 };
    for (const inv of state.invoices) { counts.all++; counts[effStatus(inv)]++; }
    const sub = counts.all
      ? `${plural(counts.all, 'invoice')}${counts.overdue ? ` · <span class="sub-alert">${counts.overdue} overdue</span>` : ''}`
      : 'Create, send and track your invoices.';
    const hasInv = counts.all > 0;

    main.innerHTML = `
      <div class="page-head">
        <div class="page-title">
          <h1 tabindex="-1">Invoices</h1>
          <p class="page-sub">${sub}</p>
        </div>
        <div class="page-actions">
          <div class="btn-group" role="group" aria-label="Data">
            ${button('import-json', 'upload', 'Import JSON', 'ghost', 'id="btn-import"')}
            ${button('export-json', 'download', 'Export JSON', 'ghost')}
            ${button('export-csv', 'download', 'Export CSV', 'ghost', hasInv ? '' : 'disabled')}
          </div>
          ${button('new-invoice', 'plus', 'New invoice', 'primary', 'id="btn-new-invoice"')}
        </div>
      </div>
      <p class="form-alert" id="import-error" role="alert" hidden></p>
      ${hasInv ? `
      <div class="toolbar">
        <div class="search">
          <label class="sr-only" for="inv-search">Search by client or invoice number</label>
          ${icon('search', 'search-icon')}
          <input type="search" id="inv-search" placeholder="Search client or number" value="${esc(ui.search)}" autocomplete="off">
        </div>
        <div class="segmented" role="group" aria-label="Filter by status">
          ${FILTERS.map((f) => `<button type="button" class="seg" data-action="filter" data-filter="${f}" aria-pressed="${ui.filter === f}">
            <span>${f === 'all' ? 'All' : STATUS_META[f].label}</span><span class="seg-count">${counts[f]}</span></button>`).join('')}
        </div>
        <div class="sort">
          <label for="inv-sort">Sort</label>
          <select id="inv-sort">
            <option value="date-desc">Newest first</option>
            <option value="date-asc">Oldest first</option>
            <option value="total-desc">Highest total</option>
            <option value="total-asc">Lowest total</option>
          </select>
        </div>
      </div>` : ''}
      <div id="inv-results"></div>
      <p class="sr-only" id="inv-count" aria-live="polite"></p>`;
    const sort = $('#inv-sort');
    if (sort) sort.value = ui.sort;
    renderInvoiceResults();
  }

  function listRows() {
    const today = todayISO();
    return state.invoices.map((inv) => {
      const calc = invoiceCalc(inv);
      return { inv, calc, st: effStatus(inv), client: clientName(inv), today };
    });
  }
  function sortRows(rows, sort) {
    const [key, dir] = sort.split('-');
    const sign = dir === 'asc' ? 1 : -1;
    const majorValue = (r) => Number(r.calc.total) / 10 ** curDigits(r.inv.currency);
    return rows.sort((a, b) => {
      let c = 0;
      if (key === 'total') c = majorValue(a) - majorValue(b);
      else c = a.inv.issueDate < b.inv.issueDate ? -1 : a.inv.issueDate > b.inv.issueDate ? 1 : 0;
      if (c === 0) c = a.inv.number.localeCompare(b.inv.number, undefined, { numeric: true });
      return c * sign;
    });
  }

  function renderInvoiceResults() {
    const box = $('#inv-results');
    if (!box) return;
    if (!state.invoices.length) {
      const noClients = !state.clients.length;
      box.innerHTML = emptyState_({
        ic: 'inbox',
        title: 'No invoices yet',
        text: noClients
          ? 'Start by adding a client, then create your first invoice. Your business details live under Business profile.'
          : 'Create your first invoice. It saves as you type, so you can come back to it anytime.',
        action: `<div class="empty-actions">
          ${noClients ? button('new-client', 'users', 'Add a client', 'secondary') : ''}
          ${button('new-invoice', 'plus', 'Create an invoice', 'primary')}</div>`,
      });
      $('#inv-count').textContent = '';
      return;
    }
    const q = ui.search.trim().toLowerCase();
    let rows = listRows().filter((r) => (ui.filter === 'all' || r.st === ui.filter) &&
      (!q || r.inv.number.toLowerCase().includes(q) || r.client.toLowerCase().includes(q)));
    rows = sortRows(rows, ui.sort);
    $('#inv-count').textContent = `${plural(rows.length, 'invoice')} shown`;

    if (!rows.length) {
      const what = ui.filter === 'all' ? '' : ` ${STATUS_META[ui.filter].label.toLowerCase()}`;
      box.innerHTML = emptyState_({
        ic: 'search',
        title: `No${what} invoices match`,
        text: q ? `Nothing matches “${esc(ui.search.trim())}”. Try another client name or number, or clear the filters.`
          : 'There are no invoices with this status yet. Clear the filter to see everything.',
        action: button('clear-filters', 'x', 'Clear filters', 'secondary'),
      });
      return;
    }

    box.innerHTML = `
      <div class="table-card">
      <table class="inv-table">
        <caption class="sr-only">Invoices</caption>
        <thead><tr>
          <th scope="col">Number</th><th scope="col">Client</th><th scope="col">Issued</th>
          <th scope="col">Due</th><th scope="col" class="num">Total</th><th scope="col">Status</th>
        </tr></thead>
        <tbody>
        ${rows.map(({ inv, calc, st, client }) => {
          const href = `#/invoice/${encodeURIComponent(inv.id)}`;
          const attention = inv.showErrors && !calc.valid && inv.status !== 'paid'
            ? `<span class="attn" title="Needs attention">${icon('alert')}<span class="sr-only">, needs attention</span></span>` : '';
          return `<tr data-href="${href}">
            <td class="c-number"><a class="row-link" href="${href}">${esc(inv.number || 'Untitled')}</a>${attention}</td>
            <td class="c-client">${client ? esc(client) : '<span class="muted">No client</span>'}</td>
            <td class="c-issued"><span class="cell-label">Issued </span>${fmtDate(inv.issueDate)}</td>
            <td class="c-due"><span class="cell-label">Due </span>${fmtDate(inv.dueDate)}</td>
            <td class="c-total num">${fmtMoney(calc.total, inv.currency)}</td>
            <td class="c-status">${badge(st)}</td>
          </tr>`;
        }).join('')}
        </tbody>
      </table>
      </div>`;
  }

  // ---------------------------------------------------------------- clients

  function renderClients() {
    document.title = 'Clients · Folio';
    const usage = {};
    for (const inv of state.invoices) if (inv.clientId) usage[inv.clientId] = (usage[inv.clientId] || 0) + 1;
    const sorted = [...state.clients].sort((a, b) => a.name.localeCompare(b.name));
    const initials = (n) => n.trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase();

    main.innerHTML = `
      <div class="page-head">
        <div class="page-title">
          <h1 tabindex="-1">Clients</h1>
          <p class="page-sub">${state.clients.length ? plural(state.clients.length, 'client') : 'The people and companies you bill.'}</p>
        </div>
        <div class="page-actions">${button('new-client', 'plus', 'New client', 'primary', 'id="btn-new-client"')}</div>
      </div>
      ${sorted.length ? `<ul class="client-grid" role="list">
        ${sorted.map((c) => `<li class="client-card" data-id="${esc(c.id)}">
          <div class="client-top">
            <span class="avatar" aria-hidden="true">${esc(initials(c.name))}</span>
            <div class="client-id">
              <h2 class="client-name">${esc(c.name)}</h2>
              <p class="client-usage">${usage[c.id] ? plural(usage[c.id], 'invoice') : 'No invoices yet'}</p>
            </div>
          </div>
          <dl class="client-details">
            <div>${icon('mail')}<dt class="sr-only">Email</dt><dd>${c.email ? esc(c.email) : '<span class="muted">No email</span>'}</dd></div>
            <div>${icon('pin')}<dt class="sr-only">Address</dt><dd>${c.address.trim() ? esc(c.address) : '<span class="muted">No address</span>'}</dd></div>
          </dl>
          <div class="card-actions">
            <button type="button" class="btn btn-secondary btn-sm" data-action="edit-client" id="edit-${esc(c.id)}">${icon('pencil')}<span>Edit<span class="sr-only"> ${esc(c.name)}</span></span></button>
            <button type="button" class="btn btn-danger-ghost btn-sm" data-action="delete-client" id="del-${esc(c.id)}" aria-describedby="cerr-${esc(c.id)}">${icon('trash')}<span>Delete<span class="sr-only"> ${esc(c.name)}</span></span></button>
          </div>
          <p class="inline-alert" id="cerr-${esc(c.id)}" role="alert" hidden></p>
        </li>`).join('')}
      </ul>` : emptyState_({
        ic: 'users',
        title: 'No clients yet',
        text: 'Add the people or companies you work with. You’ll pick one each time you create an invoice.',
        action: button('new-client', 'plus', 'Add your first client', 'primary'),
      })}`;
  }

  function deleteClient(id) {
    const c = findClient(id);
    if (!c) return;
    const used = state.invoices.filter((v) => v.clientId === id);
    if (used.length) {
      const nums = used.slice(0, 3).map((v) => v.number || 'Untitled').join(', ') + (used.length > 3 ? ', …' : '');
      const err = $(`#cerr-${CSS.escape(id)}`);
      err.innerHTML = `${icon('alert')}<span>${esc(c.name)} can’t be deleted because ${used.length === 1 ? 'an invoice uses' : `${used.length} invoices use`} this client (${esc(nums)}). Delete those invoices or switch them to another client first.</span>`;
      err.hidden = false;
      return;
    }
    if (!window.confirm(`Delete client “${c.name}”? This can’t be undone.`)) return;
    state.clients = state.clients.filter((x) => x.id !== id);
    persist();
    render(false);
    toast(`${c.name} deleted.`);
    ($('.client-card [data-action="edit-client"]') || $('#btn-new-client') || $('h1', main))?.focus();
  }

  // ---------------------------------------------------------------- editor

  const currentInvoice = () => (ui.route?.view === 'editor' ? findInvoice(ui.route.id) : null);

  function renderMissing() {
    document.title = 'Invoice not found · Folio';
    main.innerHTML = `<div class="page-head"><div class="page-title"><h1 tabindex="-1">Invoice not found</h1></div></div>
      ${emptyState_({ ic: 'file', title: 'This invoice doesn’t exist', text: 'It may have been deleted or the link is out of date.',
        action: `<a class="btn btn-primary" href="#/invoices">${icon('arrow-left')}<span>Back to invoices</span></a>` })}`;
  }

  function field(key, label, control, extraClass = '') {
    return `<div class="field ${extraClass}" data-wrap="${key}">
      <label for="f-${key}">${label}</label>${control}
      <p class="field-error" id="err-${key}" hidden></p></div>`;
  }

  function renderEditor(inv) {
    document.title = `Invoice ${inv.number || 'draft'} · Folio`;
    const ro = inv.status === 'paid';
    const st = effStatus(inv);
    const RO = ro ? 'readonly' : '';
    const DIS = ro ? 'disabled' : '';
    const ctl = (key, prop, attrs = '') =>
      `id="f-${key}" data-field="${key}" data-prop="${prop}" aria-describedby="err-${key}" ${attrs}`;
    const p = state.profile;

    const actions = [];
    if (inv.status === 'draft') actions.push(button('mark-sent', 'send', 'Mark as sent', 'primary', 'id="btn-primary-action"'));
    if (inv.status === 'sent') actions.push(button('mark-paid', 'check', 'Mark as paid', 'primary', 'id="btn-primary-action"'));
    if (inv.status === 'paid') actions.push(button('reopen', 'unlock', 'Reopen', 'primary', 'id="btn-primary-action"'));
    actions.push(button('duplicate', 'copy', 'Duplicate'));
    actions.push(button('print', 'printer', 'Print'));
    actions.push(button('delete-invoice', 'trash', 'Delete', 'danger-ghost'));

    let banner = '';
    if (ro) {
      banner = `<div class="banner banner-paid">${icon('lock')}<p><strong>Paid on ${fmtDate(inv.paidDate)}.</strong> This invoice is locked. Reopen it to make changes.</p></div>`;
    } else if (st === 'overdue') {
      const days = daysBetween(inv.dueDate, todayISO());
      banner = `<div class="banner banner-overdue">${icon('clock')}<p><strong>Overdue by ${plural(days, 'day')}.</strong> It was due on ${fmtDate(inv.dueDate)}. Mark it as paid once the payment arrives.</p></div>`;
    }

    const clientOpts = `<option value="">${state.clients.length ? 'Choose a client…' : 'No clients yet'}</option>` +
      [...state.clients].sort((a, b) => a.name.localeCompare(b.name))
        .map((c) => `<option value="${esc(c.id)}" ${c.id === inv.clientId ? 'selected' : ''}>${esc(c.name)}</option>`).join('');

    const fromBody = p.name || p.address || p.taxId
      ? `<p class="from-name">${esc(p.name || 'Unnamed business')}</p>
         ${p.address ? `<p class="from-line">${esc(p.address)}</p>` : ''}
         ${p.taxId ? `<p class="from-line">Tax ID ${esc(p.taxId)}</p>` : ''}`
      : `<p class="muted">Add your business name and address so they appear on the invoice.</p>`;

    main.innerHTML = `
      <div class="editor ${ro ? 'is-locked' : ''}">
        <div class="editor-head">
          <a class="back-link" href="#/invoices">${icon('arrow-left')}<span>All invoices</span></a>
          <div class="editor-title-row">
            <div class="editor-title">
              <h1 tabindex="-1"><span class="h-kicker">Invoice</span> <span id="ed-number">${esc(inv.number || 'Untitled')}</span></h1>
              ${badge(st)}
            </div>
            <p class="saved" id="saved-ind"></p>
          </div>
          <div class="editor-actions">${actions.join('')}</div>
        </div>
        ${banner}
        <p class="form-alert" id="ed-attn" hidden></p>

        <section class="card" aria-labelledby="sec-details">
          <h2 class="card-title" id="sec-details">Details</h2>
          <div class="details-grid">
            ${field('number', 'Invoice number', `<input ${ctl('number', 'number', `value="${esc(inv.number)}" autocomplete="off" spellcheck="false" ${RO}`)}>`, 'f-number')}
            ${field('client', 'Client', `<div class="with-action">
                <select ${ctl('client', 'clientId', DIS)}>${clientOpts}</select>
                ${ro ? '' : `<button type="button" class="btn btn-secondary btn-icon-text" data-action="new-client-inline" id="btn-new-client-inline">${icon('plus')}<span>New<span class="sr-only"> client</span></span></button>`}
              </div>`, 'f-client')}
            ${field('issueDate', 'Issue date', `<input type="date" ${ctl('issueDate', 'issueDate', `value="${esc(inv.issueDate)}" ${RO}`)}>`)}
            ${field('dueDate', 'Due date', `<input type="date" ${ctl('dueDate', 'dueDate', `value="${esc(inv.dueDate)}" ${RO}`)}>`)}
            ${field('currency', 'Currency', `<select ${ctl('currency', 'currency', DIS)}>${currencyOptions(inv.currency)}</select>`)}
          </div>
        </section>

        <section class="card" aria-labelledby="sec-lines">
          <div class="card-title-row">
            <h2 class="card-title" id="sec-lines">Line items</h2>
            ${ro ? '' : `<p class="hint" id="reorder-hint">${icon('grip')}<span>Drag the handle, or press <kbd>Alt</kbd>+<kbd>↑</kbd> / <kbd>Alt</kbd>+<kbd>↓</kbd> in a line to reorder.</span></p>`}
          </div>
          <div id="lines"></div>
          <div class="lines-foot">
            ${ro ? '' : button('add-line', 'plus', 'Add line', 'secondary', 'id="btn-add-line"')}
            <p class="field-error" id="err-lines" hidden></p>
          </div>
          <div class="totals-wrap">
            <section class="totals-card" aria-labelledby="sec-totals">
              <h3 class="sr-only" id="sec-totals">Totals</h3>
              <div id="totals"></div>
            </section>
          </div>
        </section>

        <div class="editor-bottom">
          <section class="card" aria-labelledby="sec-notes">
            <h2 class="card-title" id="sec-notes">Notes</h2>
            <div class="field">
              <label for="f-notes" class="sr-only">Notes shown on the invoice</label>
              <textarea id="f-notes" data-field="notes" data-prop="notes" rows="3" placeholder="Payment instructions, thank-you note…" ${RO}>${esc(inv.notes)}</textarea>
            </div>
          </section>
          <section class="card from-card" aria-labelledby="sec-from">
            <div class="card-title-row">
              <h2 class="card-title" id="sec-from">From</h2>
              <button type="button" class="btn btn-ghost btn-sm" data-action="open-settings" id="btn-edit-profile">${icon('pencil')}<span>Edit<span class="sr-only"> business profile</span></span></button>
            </div>
            ${fromBody}
          </section>
        </div>
      </div>`;
    renderLines(inv);
    updateDerived(inv);
  }

  function renderLines(inv) {
    const box = $('#lines');
    if (!box) return;
    const ro = inv.status === 'paid';
    const n = inv.lines.length;
    if (!n) {
      box.innerHTML = `<div class="empty empty-sm">
        <div class="empty-art" aria-hidden="true">${icon('list')}</div>
        <p class="empty-text">No line items yet. ${ro ? '' : 'Add what you’re billing for: a description, quantity and price.'}</p></div>`;
      return;
    }
    const cur = `<span class="cur-code">${inv.currency}</span>`;
    box.innerHTML = `
      <div class="lines-head" aria-hidden="true">
        <span></span><span>Description</span><span>Qty</span><span>Unit price (${cur})</span>
        <span>Discount</span><span>Tax</span><span class="ta-r">Amount</span><span></span>
      </div>
      <ol class="lines" aria-label="Line items">
      ${inv.lines.map((line, idx) => {
        const key = (prop) => `l-${line.id}-${prop}`;
        const inp = (prop, label, extra = '', suffix = '') => `
          <div class="lf lf-${prop}">
            <label class="lf-label" for="f-${key(prop)}">${label}<span class="sr-only">, line ${idx + 1}</span></label>
            <div class="${suffix ? 'affix' : ''}">
              <input id="f-${key(prop)}" data-field="${key(prop)}" data-line="${line.id}" data-prop="${prop}"
                value="${esc(line[prop])}" aria-describedby="err-${key(prop)}" autocomplete="off" ${ro ? 'readonly' : ''} ${extra}>
              ${suffix ? `<span class="suffix" aria-hidden="true">${suffix}</span>` : ''}
            </div>
            <p class="field-error" id="err-${key(prop)}" hidden></p>
          </div>`;
        return `<li class="line" data-line="${line.id}">
          <div class="line-handle">
            ${ro ? `<span class="line-no">${idx + 1}</span>` : `<button type="button" class="drag-handle" data-action="drag"
              aria-label="Move line ${idx + 1} of ${n}. Drag, or press Alt plus Up or Down arrow." aria-keyshortcuts="Alt+ArrowUp Alt+ArrowDown">${icon('grip')}</button>`}
            <span class="line-tag" aria-hidden="true">Line ${idx + 1}</span>
          </div>
          ${inp('description', 'Description', 'placeholder="What did you deliver?"')}
          ${inp('quantity', 'Qty', 'inputmode="decimal"')}
          ${inp('unitPrice', `Unit price <span class="lf-cur">(${cur})</span>`, 'inputmode="decimal" placeholder="0"')}
          ${inp('discount', 'Discount', 'inputmode="decimal"', '%')}
          ${inp('taxRate', 'Tax', 'inputmode="decimal"', '%')}
          <div class="lf lf-amount">
            <span class="lf-label" aria-hidden="true">Amount</span>
            <output class="line-amount" id="amt-${line.id}" aria-label="Amount, line ${idx + 1}"></output>
          </div>
          <div class="line-remove">
            ${ro ? '' : `<button type="button" class="icon-btn icon-btn-danger" data-action="remove-line" aria-label="Remove line ${idx + 1}">${icon('trash')}</button>`}
          </div>
        </li>`;
      }).join('')}
      </ol>`;
  }

  function setFieldError(key, msg) {
    const ctl = document.getElementById(`f-${key}`);
    const er = document.getElementById(`err-${key}`);
    if (ctl) {
      if (msg) ctl.setAttribute('aria-invalid', 'true'); else ctl.removeAttribute('aria-invalid');
      ctl.closest('.field, .lf')?.classList.toggle('has-error', !!msg);
    }
    if (er && er.dataset.msg !== (msg || '')) {
      er.dataset.msg = msg || '';
      er.hidden = !msg;
      er.innerHTML = msg ? `${icon('alert')}<span>${esc(msg)}</span>` : '';
    }
  }

  function totalsHTML(inv, c) {
    const m = (v) => fmtMoney(v, inv.currency);
    const rows = [`<div class="t-row"><dt>Subtotal</dt><dd>${m(c.subtotal)}</dd></div>`];
    rows.push(`<div class="t-row"><dt>Discount</dt><dd>${c.discount ? m(-c.discount) : m(0n)}</dd></div>`);
    if (!c.taxes.length) rows.push(`<div class="t-row"><dt>Tax</dt><dd>${m(0n)}</dd></div>`);
    for (const t of c.taxes) {
      rows.push(`<div class="t-row"><dt>Tax ${fmtRate(t.rate)} <span class="t-base">on ${m(t.base)}</span></dt><dd>${m(t.tax)}</dd></div>`);
    }
    rows.push(`<div class="t-row t-grand"><dt>Total <span class="t-cur">${inv.currency}</span></dt><dd>${m(c.total)}</dd></div>`);
    const note = c.invalidLines
      ? `<p class="t-note">${icon('alert')}<span>${plural(c.invalidLines, 'line')} not included until ${c.invalidLines === 1 ? 'its' : 'their'} numbers are fixed.</span></p>` : '';
    return `<dl class="totals">${rows.join('')}</dl>${note}`;
  }

  function updateDerived(inv) {
    const calc = invoiceCalc(inv);
    if (calc.valid && inv.showErrors) inv.showErrors = false;
    for (const line of inv.lines) {
      const out = document.getElementById(`amt-${line.id}`);
      const c = calc.lines[line.id];
      if (out) {
        out.textContent = c ? fmtMoney(c.net, inv.currency) : '—';
        out.title = c && c.discount ? `${fmtMoney(c.gross, inv.currency)} before discount` : '';
      }
    }
    $$('.cur-code', main).forEach((s) => { s.textContent = inv.currency; });
    const totals = $('#totals');
    if (totals) totals.innerHTML = totalsHTML(inv, calc);
    const num = $('#ed-number');
    if (num) num.textContent = inv.number.trim() || 'Untitled';
    document.title = `Invoice ${inv.number.trim() || 'draft'} · Folio`;

    const show = (k) => inv.status !== 'paid' && (inv.showErrors || ui.touched.has(k));
    const keys = ['number', 'client', 'issueDate', 'dueDate', 'lines'];
    for (const l of inv.lines) for (const p of LINE_PROPS) keys.push(`l-${l.id}-${p}`);
    for (const k of keys) setFieldError(k, show(k) ? calc.errors[k] : '');

    const attn = $('#ed-attn');
    if (attn) {
      const n = Object.keys(calc.errors).length;
      const on = inv.showErrors && n > 0 && inv.status !== 'paid';
      attn.hidden = !on;
      attn.innerHTML = on ? `${icon('alert')}<span>${plural(n, 'field')} ${n === 1 ? 'needs' : 'need'} attention. ${n === 1 ? 'It’s' : 'They’re'} marked below. Your draft is saved either way.</span>` : '';
    }
    updateSavedIndicator();
    renderPrint(inv, calc);
    return calc;
  }

  function updateSavedIndicator() {
    const el = $('#saved-ind');
    const inv = currentInvoice();
    if (!el || !inv) return;
    if (!storageOk) {
      el.className = 'saved is-off';
      el.innerHTML = `${icon('alert')}<span>Not saved: storage is blocked</span>`;
      return;
    }
    const when = lastSavedAt && lastSavedAt.getTime() >= inv.updatedAt - 1000 ? lastSavedAt : new Date(inv.updatedAt);
    const sameDay = toISO(when) === todayISO();
    el.className = 'saved';
    el.innerHTML = `${icon('check')}<span>Saved ${sameDay ? timeFmt.format(when) : `${dateFmt.format(when)}, ${timeFmt.format(when)}`}</span>`;
    el.classList.remove('pulse');
    void el.offsetWidth;
    el.classList.add('pulse');
  }

  function focusFirstError(inv) {
    const calc = invoiceCalc(inv);
    const keys = ['number', 'client', 'issueDate', 'dueDate'];
    for (const l of inv.lines) for (const p of LINE_PROPS) keys.push(`l-${l.id}-${p}`);
    const k = keys.find((x) => calc.errors[x]);
    (k ? document.getElementById(`f-${k}`) : $('#btn-add-line'))?.focus();
  }

  function rerenderEditorKeepFocus(inv, focusId) {
    const a = document.activeElement;
    const id = focusId || a?.id;
    renderEditor(inv);
    const n = id && document.getElementById(id);
    if (n) n.focus({ preventScroll: true });
  }

  function onEditorInput(e) {
    const t = e.target;
    const inv = currentInvoice();
    if (!inv || !t.dataset || !t.dataset.prop || inv.status === 'paid') return;
    const prop = t.dataset.prop;
    if (t.dataset.line) {
      const line = inv.lines.find((l) => l.id === t.dataset.line);
      if (!line || line[prop] === t.value) return;
      line[prop] = t.value;
    } else {
      if (inv[prop] === t.value) return;
      inv[prop] = t.value;
    }
    ui.touched.add(t.dataset.field);
    if (prop === 'issueDate' && inv.dueDate) ui.touched.add('dueDate');
    touchInvoice(inv);
    persist();
    updateDerived(inv);
  }

  function addLine(inv) {
    const line = newLine();
    inv.lines.push(line);
    touchInvoice(inv);
    persist();
    renderLines(inv);
    updateDerived(inv);
    document.getElementById(`f-l-${line.id}-description`)?.focus();
  }

  function removeLine(inv, id) {
    const i = inv.lines.findIndex((l) => l.id === id);
    if (i < 0) return;
    inv.lines.splice(i, 1);
    for (const p of LINE_PROPS) ui.touched.delete(`l-${id}-${p}`);
    touchInvoice(inv);
    persist();
    renderLines(inv);
    updateDerived(inv);
    const next = inv.lines[Math.min(i, inv.lines.length - 1)];
    (next ? $(`.line[data-line="${next.id}"] [data-action="remove-line"]`) : $('#btn-add-line'))?.focus();
    announce(`Line ${i + 1} removed.`);
  }

  function moveLine(inv, id, dir, focusId) {
    const i = inv.lines.findIndex((l) => l.id === id);
    const j = i + dir;
    if (i < 0) return;
    if (j < 0 || j >= inv.lines.length) {
      announce(`This line is already ${dir < 0 ? 'first' : 'last'}.`);
      return;
    }
    const [line] = inv.lines.splice(i, 1);
    inv.lines.splice(j, 0, line);
    afterReorder(inv, id, focusId);
  }

  function afterReorder(inv, id, focusId) {
    touchInvoice(inv);
    persist();
    renderLines(inv);
    updateDerived(inv);
    const row = $(`.line[data-line="${id}"]`);
    const f = (focusId && document.getElementById(focusId)) || row?.querySelector('.drag-handle');
    f?.focus({ preventScroll: false });
    row?.classList.add('just-moved');
    const pos = inv.lines.findIndex((l) => l.id === id) + 1;
    announce(`Line moved to position ${pos} of ${inv.lines.length}.`);
  }

  function markSent(inv) {
    const calc = invoiceCalc(inv);
    if (!calc.valid) {
      inv.showErrors = true;
      persist();
      updateDerived(inv);
      toast('Fix the marked fields before sending this invoice.', 'error');
      focusFirstError(inv);
      return;
    }
    inv.status = 'sent';
    touchInvoice(inv);
    persist();
    rerenderEditorKeepFocus(inv, 'btn-primary-action');
    toast(`Invoice ${inv.number} marked as sent.`);
  }

  function openPaidDialog(inv) {
    const calc = invoiceCalc(inv);
    if (!calc.valid) {
      inv.showErrors = true;
      updateDerived(inv);
      toast('Fix the marked fields before marking this invoice as paid.', 'error');
      focusFirstError(inv);
      return;
    }
    $('#p-date').value = todayISO();
    setDialogError('p-date', '');
    openDialog($('#dlg-paid'));
  }

  function duplicateInvoice(inv) {
    const today = todayISO();
    const term = isISO(inv.issueDate) && isISO(inv.dueDate) ? Math.max(0, daysBetween(inv.issueDate, inv.dueDate)) : 30;
    const copy = {
      ...inv,
      id: uid(), number: nextNumber(), issueDate: today, dueDate: addDays(today, term),
      status: 'draft', paidDate: '', showErrors: false, createdAt: Date.now(), updatedAt: Date.now(),
      lines: inv.lines.map((l) => ({ ...l, id: uid() })),
    };
    state.invoices.push(copy);
    persist();
    toast(`Duplicated as ${copy.number}.`);
    location.hash = `#/invoice/${encodeURIComponent(copy.id)}`;
  }

  function deleteInvoice(inv) {
    if (!window.confirm(`Delete invoice ${inv.number || 'Untitled'}? This can’t be undone.`)) return;
    state.invoices = state.invoices.filter((v) => v.id !== inv.id);
    persist();
    ui.route = { view: 'invoices' };
    toast(`Invoice ${inv.number || 'Untitled'} deleted.`);
    if (location.hash !== '#/invoices') location.hash = '#/invoices';
    else render(true);
  }

  function createInvoice() {
    const today = todayISO();
    const inv = {
      id: uid(), number: nextNumber(), clientId: state.clients.length === 1 ? state.clients[0].id : '',
      issueDate: today, dueDate: addDays(today, 30), currency: state.profile.currency || 'USD',
      status: 'draft', paidDate: '', notes: '', lines: [newLine()], showErrors: false,
      createdAt: Date.now(), updatedAt: Date.now(),
    };
    state.invoices.push(inv);
    persist();
    location.hash = `#/invoice/${encodeURIComponent(inv.id)}`;
  }

  // ---------------------------------------------------------------- print view

  function renderPrint(inv, calc) {
    const doc = $('#print-doc');
    const p = state.profile;
    const c = findClient(inv.clientId);
    const m = (v) => fmtMoney(v, inv.currency);
    const multiline = (s) => esc(s).replace(/\n/g, '<br>');
    const st = effStatus(inv);
    doc.innerHTML = `
      <article class="pd">
        <header class="pd-head">
          <div>
            <p class="pd-biz">${esc(p.name || 'Your business')}</p>
            ${p.address ? `<p>${multiline(p.address)}</p>` : ''}
            ${p.taxId ? `<p>Tax ID: ${esc(p.taxId)}</p>` : ''}
          </div>
          <div class="pd-title">
            <h1>Invoice</h1>
            <p class="pd-num">${esc(inv.number)}</p>
            ${st === 'paid' ? `<p class="pd-stamp">Paid ${fmtDate(inv.paidDate)}</p>` : ''}
          </div>
        </header>
        <section class="pd-block">
          <h2>Bill to</h2>
          <p class="pd-strong">${esc(c ? c.name : '—')}</p>
          ${c && c.email ? `<p>${esc(c.email)}</p>` : ''}
          ${c && c.address ? `<p>${multiline(c.address)}</p>` : ''}
        </section>
        <section class="pd-block pd-dates">
          <p><span>Issue date</span> ${fmtDate(inv.issueDate)}</p>
          <p><span>Due date</span> ${fmtDate(inv.dueDate)}</p>
          <p><span>Currency</span> ${inv.currency}</p>
        </section>
        <table class="pd-lines">
          <thead><tr><th>Description</th><th class="num">Qty</th><th class="num">Unit price</th><th class="num">Discount</th><th class="num">Tax</th><th class="num">Amount</th></tr></thead>
          <tbody>
            ${inv.lines.map((l) => {
              const lc = calc.lines[l.id];
              const price = parseDec(l.unitPrice, curDigits(inv.currency));
              return `<tr>
                <td>${esc(l.description)}</td>
                <td class="num">${esc(l.quantity)}</td>
                <td class="num">${price.err ? esc(l.unitPrice) : m(price.v)}</td>
                <td class="num">${esc(l.discount || '0')}%</td>
                <td class="num">${esc(l.taxRate || '0')}%</td>
                <td class="num">${lc ? m(lc.net) : '—'}</td></tr>`;
            }).join('')}
          </tbody>
        </table>
        <section class="pd-totals">${totalsHTML(inv, calc)}</section>
        ${inv.notes.trim() ? `<section class="pd-block pd-notes"><h2>Notes</h2><p>${multiline(inv.notes)}</p></section>` : ''}
      </article>`;
  }

  // ---------------------------------------------------------------- dialogs

  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function openDialog(dlg) {
    const active = document.activeElement;
    dlg._return = active;
    dlg._returnId = active && active.id;
    dlg.showModal();
    const first = $$('input, select, textarea', dlg).find((x) => !x.disabled);
    (first || $$(FOCUSABLE, dlg)[0])?.focus();
  }

  function setupDialog(dlg) {
    dlg.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;
      const items = $$(FOCUSABLE, dlg).filter((x) => x.offsetParent !== null || x === document.activeElement);
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('close', () => {
      let target = dlg._return;
      if (!target || !target.isConnected) target = dlg._returnId && document.getElementById(dlg._returnId);
      (target || $('h1', main))?.focus();
    });
  }

  function setDialogError(id, msg) {
    const input = document.getElementById(id);
    const er = document.getElementById(`${id}-err`);
    if (msg) input.setAttribute('aria-invalid', 'true'); else input.removeAttribute('aria-invalid');
    input.closest('.field')?.classList.toggle('has-error', !!msg);
    er.hidden = !msg;
    er.innerHTML = msg ? `${icon('alert')}<span>${esc(msg)}</span>` : '';
  }

  function openSettings() {
    const p = state.profile;
    $('#s-name').value = p.name;
    $('#s-address').value = p.address;
    $('#s-taxid').value = p.taxId;
    $('#s-currency').value = p.currency;
    $('#s-taxrate').value = p.taxRate;
    setDialogError('s-taxrate', '');
    openDialog($('#dlg-settings'));
  }

  function saveSettings(e) {
    e.preventDefault();
    const rate = $('#s-taxrate').value.trim() || '0';
    const r = parsePct(rate);
    setDialogError('s-taxrate', r.err || '');
    if (r.err) { $('#s-taxrate').focus(); return; }
    state.profile = {
      name: $('#s-name').value.trim(), address: $('#s-address').value.trim(), taxId: $('#s-taxid').value.trim(),
      currency: $('#s-currency').value, taxRate: rate,
    };
    persist();
    render(false);
    $('#dlg-settings').close();
    toast('Business profile saved. New invoices will use these defaults.');
  }

  function openClientDialog(id, forInvoice) {
    const c = id ? findClient(id) : null;
    ui.clientDialog = { id: c ? c.id : null, forInvoice: forInvoice || null };
    $('#dlg-client-title').textContent = c ? 'Edit client' : 'New client';
    $('#c-name').value = c ? c.name : '';
    $('#c-email').value = c ? c.email : '';
    $('#c-address').value = c ? c.address : '';
    setDialogError('c-name', '');
    setDialogError('c-email', '');
    openDialog($('#dlg-client'));
  }

  function saveClient(e) {
    e.preventDefault();
    const name = $('#c-name').value.trim();
    const email = $('#c-email').value.trim();
    const nameErr = name ? '' : 'Enter the client’s name.';
    const emailErr = email && !/^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/.test(email)
      ? 'That email doesn’t look right. Use a format like name@company.com.' : '';
    setDialogError('c-name', nameErr);
    setDialogError('c-email', emailErr);
    if (nameErr) { $('#c-name').focus(); return; }
    if (emailErr) { $('#c-email').focus(); return; }
    const ctx = ui.clientDialog || {};
    let client;
    if (ctx.id && findClient(ctx.id)) {
      client = findClient(ctx.id);
      Object.assign(client, { name, email, address: $('#c-address').value.trim() });
    } else {
      client = { id: uid(), name, email, address: $('#c-address').value.trim() };
      state.clients.push(client);
    }
    const inv = ctx.forInvoice && findInvoice(ctx.forInvoice);
    if (inv && inv.status !== 'paid') {
      inv.clientId = client.id;
      ui.touched.add('client');
      touchInvoice(inv);
    }
    persist();
    if (inv) {
      $('#dlg-client')._returnId = 'f-client';
      $('#dlg-client')._return = null;
    }
    render(false);
    $('#dlg-client').close();
    toast(ctx.id ? `${name} updated.` : `${name} added.`);
  }

  function savePaid(e) {
    e.preventDefault();
    const inv = currentInvoice();
    if (!inv) { $('#dlg-paid').close(); return; }
    const d = $('#p-date').value;
    let err = '';
    if (!isISO(d)) err = 'Pick the date the payment arrived.';
    else if (isISO(inv.issueDate) && d < inv.issueDate) err = 'The paid date can’t be before the issue date.';
    setDialogError('p-date', err);
    if (err) { $('#p-date').focus(); return; }
    inv.status = 'paid';
    inv.paidDate = d;
    inv.showErrors = false;
    touchInvoice(inv);
    persist();
    renderEditor(inv);
    $('#dlg-paid')._returnId = 'btn-primary-action';
    $('#dlg-paid')._return = null;
    $('#dlg-paid').close();
    toast(`Invoice ${inv.number} marked as paid.`);
  }

  // ---------------------------------------------------------------- import / export

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }
  const csvCell = (v) => (/[",\r\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);

  function exportCSV() {
    if (!state.invoices.length) return;
    const rows = sortRows(listRows(), ui.sort).map(({ inv, calc, st, client }) => [
      inv.number, client, inv.issueDate, inv.dueDate, inv.currency,
      toMajorString(calc.total, curDigits(inv.currency)), STATUS_META[st].label,
    ].map((v) => csvCell(String(v))).join(','));
    download(`invoices-${todayISO()}.csv`, [CSV_HEADER, ...rows].join('\n') + '\n', 'text/csv;charset=utf-8');
    toast(`Exported ${plural(rows.length, 'invoice')} as CSV.`);
  }

  function exportJSON() {
    const payload = { app: KEY, version: 1, exportedAt: new Date().toISOString(), data: state };
    download(`folio-backup-${todayISO()}.json`, JSON.stringify(payload, null, 2), 'application/json');
    toast('Exported everything as JSON.');
  }

  function showImportError(msg) {
    const el = $('#import-error');
    if (el) {
      el.hidden = !msg;
      el.innerHTML = msg ? `${icon('alert')}<span>${esc(msg)}</span>` : '';
    }
    if (msg) toast(msg, 'error');
  }

  function importFile(file) {
    showImportError('');
    if (!file) return;
    const fail = (why) => showImportError(`Couldn’t import “${file.name}”: ${why}. Nothing was changed.`);
    if (file.size > 5 * 1024 * 1024) { fail('the file is larger than 5 MB'); return; }
    const reader = new FileReader();
    reader.onerror = () => fail('the file couldn’t be read');
    reader.onload = () => {
      let next;
      try {
        let parsed;
        try { parsed = JSON.parse(String(reader.result)); } catch (e) { throw new Error('it isn’t valid JSON'); }
        next = normalizeState(parsed);
      } catch (e) {
        fail(e.message || 'the file isn’t a Folio backup');
        return;
      }
      state = next;
      if (!persist() && storageOk) return;
      ui.touched.clear();
      ui.filter = 'all';
      ui.search = '';
      render(false);
      toast(`Imported ${plural(state.invoices.length, 'invoice')} and ${plural(state.clients.length, 'client')}.`);
      $('#btn-import')?.focus();
    };
    reader.readAsText(file);
  }

  // ---------------------------------------------------------------- events

  document.addEventListener('click', (e) => {
    const closer = e.target.closest('[data-close]');
    if (closer) { closer.closest('dialog')?.close(); return; }
    const a = e.target.closest('[data-action]');
    if (!a) {
      const tr = e.target.closest('tr[data-href]');
      if (tr && !e.target.closest('a, button')) location.hash = tr.dataset.href;
      return;
    }
    if (a.disabled) return;
    const inv = currentInvoice();
    switch (a.dataset.action) {
      case 'skip': main.focus(); break;
      case 'dismiss-notice': $('#notice').innerHTML = ''; main.focus(); break;
      case 'open-settings': openSettings(); break;
      case 'new-invoice': createInvoice(); break;
      case 'new-client': openClientDialog(null); break;
      case 'new-client-inline': if (inv) openClientDialog(null, inv.id); break;
      case 'edit-client': openClientDialog(a.closest('[data-id]').dataset.id); break;
      case 'delete-client': deleteClient(a.closest('[data-id]').dataset.id); break;
      case 'export-csv': exportCSV(); break;
      case 'export-json': exportJSON(); break;
      case 'import-json': { const f = $('#import-file'); f.value = ''; f.click(); break; }
      case 'filter':
        ui.filter = a.dataset.filter;
        $$('[data-action="filter"]').forEach((b) => b.setAttribute('aria-pressed', String(b === a)));
        renderInvoiceResults();
        break;
      case 'clear-filters':
        ui.filter = 'all';
        ui.search = '';
        renderInvoices();
        $('#inv-search')?.focus();
        break;
      case 'add-line': if (inv && inv.status !== 'paid') addLine(inv); break;
      case 'remove-line': if (inv && inv.status !== 'paid') removeLine(inv, a.closest('.line').dataset.line); break;
      case 'mark-sent': if (inv) markSent(inv); break;
      case 'mark-paid': if (inv) openPaidDialog(inv); break;
      case 'reopen':
        if (!inv) break;
        inv.status = 'sent';
        inv.paidDate = '';
        touchInvoice(inv);
        persist();
        rerenderEditorKeepFocus(inv, 'btn-primary-action');
        toast(`Invoice ${inv.number} reopened. You can edit it again.`);
        break;
      case 'duplicate': if (inv) duplicateInvoice(inv); break;
      case 'print': window.print(); break;
      case 'delete-invoice': if (inv) deleteInvoice(inv); break;
      default: break;
    }
  });

  main.addEventListener('input', (e) => {
    if (e.target.id === 'inv-search') {
      ui.search = e.target.value;
      renderInvoiceResults();
      return;
    }
    if (ui.route?.view === 'editor') onEditorInput(e);
  });
  main.addEventListener('change', (e) => {
    if (e.target.id === 'inv-sort') {
      ui.sort = e.target.value;
      renderInvoiceResults();
      return;
    }
    if (ui.route?.view === 'editor') onEditorInput(e);
  });
  main.addEventListener('focusout', (e) => {
    const t = e.target;
    const inv = currentInvoice();
    if (!inv || !t.dataset || !t.dataset.field || t.dataset.field === 'notes') return;
    // Required fields left empty get marked once the user moves on.
    if (!ui.touched.has(t.dataset.field) && t.value === '' && t.dataset.prop !== 'discount' && t.dataset.prop !== 'taxRate') {
      ui.touched.add(t.dataset.field);
      updateDerived(inv);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (!e.altKey || e.ctrlKey || e.metaKey || (e.key !== 'ArrowUp' && e.key !== 'ArrowDown')) return;
    const row = e.target.closest && e.target.closest('.line[data-line]');
    const inv = currentInvoice();
    if (!row || !inv || inv.status === 'paid') return;
    e.preventDefault();
    moveLine(inv, row.dataset.line, e.key === 'ArrowUp' ? -1 : 1, e.target.id);
  });

  // Pointer-based drag so it works the same for mouse, pen and touch.
  let drag = null;
  document.addEventListener('pointerdown', (e) => {
    const handle = e.target.closest('.drag-handle');
    if (!handle || e.button !== 0) return;
    const inv = currentInvoice();
    if (!inv || inv.status === 'paid') return;
    e.preventDefault();
    const row = handle.closest('.line');
    try { handle.setPointerCapture(e.pointerId); } catch (err) { /* capture is optional */ }
    drag = { id: row.dataset.line, row, list: row.parentElement, moved: false };
    row.classList.add('is-dragging');
    document.body.classList.add('is-dragging-line');
    handle.focus({ preventScroll: true });
  });
  document.addEventListener('pointermove', (e) => {
    if (!drag) return;
    e.preventDefault();
    const rows = $$('.line', drag.list);
    const di = rows.indexOf(drag.row);
    const mid = (r) => { const b = r.getBoundingClientRect(); return b.top + b.height / 2; };
    const after = rows.slice(di + 1).filter((r) => mid(r) <= e.clientY).pop();
    if (after) { after.after(drag.row); drag.moved = true; return; }
    const before = rows.slice(0, di).find((r) => mid(r) >= e.clientY);
    if (before) { before.before(drag.row); drag.moved = true; }
  });
  function endDrag() {
    if (!drag) return;
    const d = drag;
    drag = null;
    d.row.classList.remove('is-dragging');
    document.body.classList.remove('is-dragging-line');
    const inv = currentInvoice();
    if (!d.moved || !inv) return;
    const order = $$('.line', d.list).map((r) => r.dataset.line);
    inv.lines.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
    afterReorder(inv, d.id);
  }
  document.addEventListener('pointerup', endDrag);
  document.addEventListener('pointercancel', endDrag);

  $('#import-file').addEventListener('change', (e) => importFile(e.target.files && e.target.files[0]));
  $('#form-settings').addEventListener('submit', saveSettings);
  $('#form-client').addEventListener('submit', saveClient);
  $('#form-paid').addEventListener('submit', savePaid);
  $$('dialog').forEach(setupDialog);
  $$('.currency-options').forEach((s) => { s.innerHTML = currencyOptions('USD'); });

  window.addEventListener('hashchange', onRoute);
  // Keep the Overdue state honest if the tab stays open past midnight.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && ui.route && ui.route.view === 'invoices') renderInvoices();
  });
  window.addEventListener('storage', (e) => {
    if (e.key !== KEY || e.newValue == null) return;
    try { state = normalizeState(JSON.parse(e.newValue)); render(false); } catch (err) { /* ignore foreign writes */ }
  });

  // ---------------------------------------------------------------- boot

  const notice = loadState();
  if (notice) showNotice(notice);
  ui.route = parseRoute();
  render(false);
})();
