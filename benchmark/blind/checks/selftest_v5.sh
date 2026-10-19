#!/usr/bin/env bash
# Self-test for check_app_v5.py: every reference must score full marks; every negative control must fail
# EXACTLY the intended check(s) and nothing else. Writes results/blind_v5_selftest.txt (relative to repo root).
# Box rule: run only while no round-2 build runs; each checker run is nice -n 19 + timeout -k 5 240.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../../.." && pwd)"
REF="$HERE/reference_v5"; OUT="${SELFTEST_OUT:-$(mktemp -d /tmp/tlv5_selftest.XXXXXX)}"; mkdir -p "$OUT"
RES="$ROOT/results/blind_v5_selftest.txt"; mkdir -p "$ROOT/results"
run_one() {
  local d="$1" n app t0; n="$(basename "$d")"; app="${n%%_*}"; t0=$(date +%s)
  nice -n 19 timeout -k 5 240 python3 "$HERE/check_app_v5.py" "$app" "$d" "$OUT/$n.png" "$OUT/$n.json" > "$OUT/$n.log" 2>&1
  echo "$n rc=$? $(( $(date +%s) - t0 ))s $(tail -1 "$OUT/$n.log")"
}
for d in "$REF"/*/; do            # at most 3 checker runs at a time
  while [ "$(jobs -rp | wc -l)" -ge 3 ]; do wait -n; done
  run_one "$d" &
done
wait
python3 - "$OUT" "$RES" <<'PY'
import json, os, sys, glob
out, res = sys.argv[1:3]
BTN = "every visible button changes page state"
OVF = "375 px wide: no horizontal page scroll (scrollWidth <= viewport)"
DEL = {"habits": "delete asks with native confirm(); cancel keeps, OK deletes",
       "recipes": "delete asks with native confirm(); cancel keeps, OK deletes",
       "pomodoro": "task delete asks with native confirm(); cancel keeps, OK deletes"}
SPEC = {"habits_streakwrong": "streak = consecutive done days ending today (or yesterday): 2, then 3 with today",
        "recipes_noscale": "typing servings 6 then 2 rescales (300/0.75/3/2.25, 100/0.25/1/0.75; 'salt to taste' unchanged)",
        "pomodoro_nocount": "a finished focus adds 1 to the active task's .count only"}
lines, allok = [], True
for f in sorted(glob.glob(os.path.join(out, "*.json"))):
    n = os.path.basename(f)[:-5]; app, _, kind = n.partition("_")
    try: r = json.load(open(f))
    except Exception as e:
        lines.append(f"{n}: NO RESULT ({e})"); allok = False; continue
    failed = [c["name"] for c in r["checks"] if not c["ok"]]
    want = set() if not kind else {"deadbtn": {BTN}, "noconfirm": {DEL[app]}, "overflow": {OVF}}.get(kind) or {SPEC[n]}
    ok = set(failed) == want
    allok &= ok
    role = "reference" if not kind else "control"
    lines.append(f"{'PASS' if ok else 'FAIL'}  {n:22s} {role:9s} {r['passed']}/{r['total']}  failed={failed or 'none'}"
                 + ("" if ok else f"  EXPECTED={sorted(want) or 'none'}")
                 + (f"  dead_buttons={r.get('buttons_no_effect')}" if kind == "deadbtn" else "")
                 + (f"  w375={r.get('w375_scrollWidth_vs_viewport')}" if kind == "overflow" else ""))
lines.append(f"SELFTEST {'OK' if allok else 'FAILED'}: {len(lines)} apps")
open(res, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
sys.exit(0 if allok else 1)
PY
