#!/usr/bin/env python3
"""READ-ONLY: applies benchmark/blind/v5c_TOKEN_SPLIT_RULE.md (commit 7f9f269) to the stream-json logs of all 10 v5c-round builds.
Writes files/tl_blind/v5c/TOKEN_WHY.tsv. Counting uses the token-counting endpoint (no model run); credentials are read from the box's
capability file and never printed or written."""
import json, os, re, glob, urllib.request
TD = "/home/user/tab/tasks/70a3e3bd-9718-4f28-a168-4eee812d5557"
OUTP = "/home/user/tab/files/tl_blind/v5c/TOKEN_WHY.tsv"
d = json.load(open("/home/user/tab/.model-capability.json"))
URL = d["base_url"].rstrip("/") + "/anthropic/v1/messages/count_tokens"; KEY = d["token"]; del d
_cache = {}
def ct(text):
    text = text or "."
    if text in _cache: return _cache[text]
    body = {"model": "claude-opus-5-5", "messages": [{"role": "user", "content": text}]}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json", "user-agent": "tightloop-measure/1"})
    n = json.load(urllib.request.urlopen(req, timeout=60))["input_tokens"]; _cache[text] = n; return n
BASE = ct(".") - 1
APPX = re.compile(r"\.(html?|css|js|mjs|json|svg)$", re.I)
def is_app(p):
    p = p.strip("'\"")
    if p.startswith("/"):
        if not re.match(r"/tmp/tlb-[^/]+/[^/]+$", p): return False
    elif "/" in p.strip("./"): return False
    b = os.path.basename(p)
    if re.search(r"test|spec|check|shot|probe|kt\.", b, re.I): return False
    return bool(APPX.search(b))
def bash_writes(c):
    t = []
    t += re.findall(r"cat\s*>>?\s*([^\s<;|&]+)\s*<<", c)
    t += re.findall(r"tee\s+(?:-a\s+)?([^\s<;|&]+)\s*<<", c)
    t += re.findall(r"sed\s+-i\S*\s+(?:-e\s+)?(?:'[^']*'|\"[^\"]*\"|\S+)\s+([^\s;|&]+)", c)
    t += re.findall(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wa]", c)
    t += re.findall(r"Path\(\s*['\"]([^'\"]+)['\"]\s*\)\.write_text", c)
    t += re.findall(r"(?:>|>>)\s*([\w./-]+\.(?:html?|css|js|mjs|json|svg))\b", c)
    return t
def targets(name, inp):
    if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        p = inp.get("file_path", ""); return [os.path.basename(p)] if is_app(p) else []
    if name != "Bash": return []
    return sorted(set(os.path.basename(x) for x in bash_writes(inp.get("command", "")) if is_app(x)))
VER = re.compile(r"http\.server|SimpleHTTPRequestHandler|(?<![\w-])serve(?![\w-])|playwright|puppeteer|selenium|chromium|chrome|headless|ms-playwright|"
                 r"jsdom|\bassert\b|node\s+--check|node\s+--test|pytest|curl\s+\S*(localhost|127\.0\.0\.1)", re.I)
BROWSER = re.compile(r"sync_playwright|async_playwright|\.launch\(|puppeteer\.launch|webdriver\.", re.I)
FAIL = re.compile(r"Executable doesn't exist|BrowserType\.launch|Failed to launch|ModuleNotFoundError|Traceback|Error:|playwright install|Looks like Playwright|Exit code [1-9]", re.I)
CLICK = re.compile(r"\.(click|dblclick|fill|check|drag_to|press|select_option|set_input_files|dispatch_event)\(\s*(?:['\"]([^'\"]*)['\"])?")
def result_text(c):
    cc = c.get("content"); return cc if isinstance(cc, str) else " ".join(x.get("text", "") for x in (cc or []) if isinstance(x, dict))
rows = []
rr = {json.loads(l)["build"]: json.loads(l) for l in open(TD + "/blind_rows_v5c.jsonl")}
for f in sorted(glob.glob(TD + "/logs_v5c/*.agent.stdout")):
    bid = os.path.basename(f).split(".agent")[0]
    ev = [json.loads(l) for l in open(f) if l.strip().startswith("{")]
    rs = [e for e in ev if e.get("type") == "result"]
    if not rs: continue
    u = rs[-1]["usage"]; out_total = u["output_tokens"]; think = (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)
    units = []; seen = set(); results = {}
    for e in ev:
        if e.get("type") == "assistant":
            for c in e["message"]["content"]:
                k = (e["message"]["id"], json.dumps(c, sort_keys=True))
                if k in seen: continue
                seen.add(k)
                if c["type"] == "tool_use": units.append(("tool", c["name"], c["input"], c["id"]))
                elif c["type"] == "text": units.append(("text", None, c["text"], None))
        elif e.get("type") == "user":
            for c in e["message"]["content"] if isinstance(e["message"].get("content"), list) else []:
                if isinstance(c, dict) and c.get("type") == "tool_result": results[c["tool_use_id"]] = result_text(c)
    scripts = {}   # script files written in this build (any path) -> their text
    created = {}; writes = {}; phase = "first"
    cat = {"first": 0, "verify": 0, "rewrite": 0, "other": 0, "final": 0}
    mixed = 0; first_checks = 0; ncalls = 0; first_calls = 0
    browser_calls = []; clicks = []
    # end of the initial run of app-file-creating calls (rule: first pass ends at the first call that, after an app file exists, creates no new one)
    _c = set(); first_end = len(units) - 1; last_create = -1
    for i, (kind, name, inp, uid) in enumerate(units):
        if kind != "tool": continue
        tg = targets(name, inp); new = [x for x in tg if x not in _c]
        if _c and not new: first_end = last_create; break
        _c.update(tg)
        if new: last_create = i
    else:
        first_end = last_create if last_create >= 0 else len(units) - 1
    for idx, (kind, name, inp, uid) in enumerate(units):
        if kind == "text":
            tok = max(ct(inp) - BASE, 0)
            cat["first" if idx <= first_end else "final"] += tok; continue
        ncalls += 1
        txt = "\n".join(str(v) for v in inp.values()); tok = max(ct(txt) - BASE, 0)
        cmd = inp.get("command", "") if name == "Bash" else ""
        # remember script files this call writes (for "runs a script written earlier")
        if name == "Write": scripts[os.path.basename(inp.get("file_path", ""))] = inp.get("content", "")
        for m in re.finditer(r"cat\s*>\s*([^\s<;|&]+)\s*<<\s*'?(\w+)'?\n(.*?)\n\2", cmd, re.S): scripts[os.path.basename(m.group(1))] = m.group(3)
        runs = [s for s in scripts if s and re.search(r"(python3?|node|bash|sh)\s+\S*" + re.escape(s) + r"\b", cmd)]
        ver = bool(VER.search(txt)) or any(VER.search(scripts[s]) for s in runs)
        is_browser = bool(BROWSER.search(cmd)) or any(BROWSER.search(scripts[s]) for s in runs)
        if is_browser:
            res = results.get(uid, ""); fl = [l.strip() for l in res.splitlines() if FAIL.search(l)]
            src = cmd + "\n" + "\n".join(scripts[s] for s in runs)
            lits = [x for x in re.findall(r"print\(\s*f?['\"]([^'\"{]{3,})", src) if x.strip()]
            ran = (not fl) and any(x.strip()[:20] in res for x in lits)     # positive evidence: the script's own print reached the result
            pick = ([l for l in fl if "Executable doesn't exist" in l] + [("Playwright's missing-browser banner ('playwright install'; the Executable-doesn't-exist line was cut by tail)") for l in fl if "playwright install" in l]
                    + [l for l in fl if "Traceback" not in l and not l.startswith("Exit code")] + fl)
            browser_calls.append((ran, (pick[0] if pick else ("" if ran else "no output from the script (it did not run or printed nothing)"))[:170]))
            for m in CLICK.finditer(src): clicks.append(m.group(2) if m.group(2) is not None else "(" + m.group(1) + " var)")
        tg = targets(name, inp); new = [x for x in tg if x not in created]
        for x in tg: writes[x] = writes.get(x, 0) + 1; created.setdefault(x, ncalls)
        if phase == "first":
            if created and not new: phase = "after"
            else:
                cat["first"] += tok; first_calls += 1
                if ver: first_checks += 1
                continue
        if tg:
            cat["rewrite"] += tok
            if ver: mixed += 1
        elif ver: cat["verify"] += tok
        else: cat["other"] += tok
    vis = sum(cat.values())
    if not browser_calls: launched, err = "no script", ""
    elif any(ok for ok, _ in browser_calls): launched, err = "yes", ""
    else:
        launched = "no"; errs = [e for _, e in browser_calls if e]
        err = sorted(errs, key=lambda e: (0 if "Executable doesn't exist" in e else 1 if "banner" in e else 2 if not e.startswith("Exit code") else 3))[0] if errs else ""
    uniq = []
    for c in clicks:
        if c not in uniq: uniq.append(c)
    r = rr.get(bid, {})
    rows.append([bid, r.get("arm"), r.get("cost_weighted"), r.get("cache_read"), r.get("cache_creation"), out_total, think, out_total - think,
                 cat["first"], cat["verify"], cat["rewrite"], cat["other"], cat["final"], (out_total - think) - vis,
                 sum(1 for v in writes.values() if v > 1), ";".join(f"{k}x{v}" for k, v in sorted(writes.items())), mixed, first_checks,
                 ncalls, first_calls, "yes" if browser_calls else "no", len(browser_calls), launched, err.replace("\t", " "),
                 ("clicked: " if launched == "yes" else "script targets (never executed): " if browser_calls else "") + " | ".join(uniq)])
hdr = ["build", "arm", "cost_weighted", "cache_read", "cache_write", "output_total", "thinking_tokens", "visible_output",
       "first_pass_write", "clicktest_verification", "rewrite_edit", "other_tool", "final_reply", "visible_unattributed",
       "app_files_written_or_edited_more_than_once", "app_file_write_counts", "mixed_calls", "first_pass_calls_with_checks",
       "tool_calls", "first_pass_tool_calls", "clicktest_script", "browser_script_runs", "browser_launched", "launch_error_first_line", "features_clicked"]
with open(OUTP, "w") as fh:
    fh.write("\t".join(hdr) + "\n")
    for r in rows: fh.write("\t".join("" if x is None else str(x) for x in r) + "\n")
print(open(OUTP).read())
