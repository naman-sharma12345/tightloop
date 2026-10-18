#!/usr/bin/env python3
"""One tiny agent-CLI call inside the hardened sandbox, the exact build invocation (fresh workspace + fresh config dir), no tools:
shows the CLI starts with an empty config, reaches the model API through the egress, and writes only to its own config dir,
which is wiped afterwards. Not a build. Prints rc, result subtype, reply, usage, and the config dir's entry count."""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sandbox_r2 as S
env = S.clean_env(); os.environ.clear(); os.environ.update(env)
sd, pp = S.start_proxy(env)
wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-"); subprocess.run(["git", "init", "-q"], cwd=wt)
r = subprocess.run(["timeout", "-k", "5", "150"] + S.prefix(wt, cfg, sd) + ["claude", "-p", "Reply with the single word OK.", "--output-format", "stream-json",
                   "--verbose", "--max-turns", "1", "--disallowedTools", "WebFetch", "WebSearch", "Bash", "Edit", "Write", "Read"],
                   capture_output=True, text=True, env=env, timeout=170)
ev = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith("{")]
res = [e for e in ev if e.get("type") == "result"]
n_cfg = sum(len(fs) for _, _, fs in os.walk(cfg))
S.stop_proxy(sd, pp); shutil.rmtree(wt, ignore_errors=True); shutil.rmtree(cfg, ignore_errors=True)
out = {"rc": r.returncode, "result": res[0].get("subtype") if res else None, "is_error": res[0].get("is_error") if res else None,
       "reply": str(res[0].get("result"))[:20] if res else None, "usage_in_out": [res[0].get("usage", {}).get("input_tokens"), res[0].get("usage", {}).get("output_tokens")] if res else None,
       "files_written_to_own_config_dir": n_cfg, "config_dir_wiped": not os.path.exists(cfg), "stderr_tail": S.redact(r.stderr[-200:], env)}
print(json.dumps(out)); sys.exit(0 if out["result"] == "success" and not out["is_error"] else 1)
