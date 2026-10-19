#!/usr/bin/env python3
"""tightloop v9 per-row thinking + pre-write measure (v9_PREREG.md reporting; a byte-for-byte copy of
benchmark/blind/v8_run/split_prewrite_v8.py except this docstring line). Applies the FROZEN expenses split rule UNCHANGED:
the code block of /home/user/tab/files/tl_blind/expenses_thinking/SPLIT_RULE.md (sha256 a3ccc9b4305e8bad5d15f0829f86b44fc3434b1b7d80422da4dde7af87ae1063,
written 2026-10-18T22:59:09Z) is extracted and exec'd as-is after the sha is checked; nothing in it is edited.
prewrite_block = the SPLIT.tsv descriptive column: the scaled token count of the thinking block right before the first app write
(the last thinking block before the first tool call for which the rule's app_targets() is non-empty), scaled by the rule's own
factor (exact result thinking_tokens / sum of per-block estimates). 0 if no thinking block precedes the first app write.
Usage: split_prewrite_v8.py <stream-json log> [...]  -> one TSV line per log: log, thinking_total, 5 buckets, prewrite_block, n_blocks"""
import hashlib, re, sys, json
RULE = "/home/user/tab/files/tl_blind/expenses_thinking/SPLIT_RULE.md"
SHA = "a3ccc9b4305e8bad5d15f0829f86b44fc3434b1b7d80422da4dde7af87ae1063"
raw = open(RULE, "rb").read(); assert hashlib.sha256(raw).hexdigest() == SHA, "split rule changed - stop"
code = raw.decode().split("## Code (the rule)", 1)[1].split("```python", 1)[1].split("```", 1)[0]
g = {}; exec(code, g)
def prewrite(path):
    """Same event walk as the rule's split_run(); returns the est of the last think before the first app write."""
    events = [json.loads(l) for l in open(path) if l.strip().startswith("{")]
    est_run, last_think = 0, None
    for o in events:
        t = o.get("type")
        if t == "system" and o.get("subtype") == "thinking_tokens":
            est_run = o.get("estimated_tokens", est_run)
        elif t == "assistant":
            for c in o["message"].get("content", []):
                if c.get("type") == "thinking": last_think = est_run; est_run = 0
                elif c.get("type") == "tool_use" and g["app_targets"](c): return last_think or 0
    return None   # no app write in the run
if __name__ == "__main__":
    print("log\tthinking_total\tplanning\tschema\tvalidation\tretry\tother\tprewrite_block\tn_blocks")
    for p in sys.argv[1:]:
        b = g["bucketize"](p); pw = prewrite(p)
        pws = "NA" if pw is None else round(pw * b["scale"])
        print("\t".join(str(x) for x in [p, b["exact_total"]] + [round(b["buckets"][k]) for k in ("planning", "schema", "validation", "retry", "other")] + [pws, len(b["blocks"])]))
