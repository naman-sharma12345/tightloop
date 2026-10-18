#!/usr/bin/env python3
"""v5 driver helper (root steer 20:10Z): the agent CLI never gets the skill text in argv. runner.launch builds
`claude ... --append-system-prompt <text>`; sandbox_argv() writes <text> to a file in the build's own fresh config dir (bound
inside the sandbox at sandbox_r2.CFG_IN) and replaces the pair with `--append-system-prompt-file <neutral path>`. The text the
model receives is byte-identical; only how it reaches the CLI changes. The no-skill arm has no such flag (runner adds none), so
argv shows whether a skill is present but never which one. runner.py is not changed."""
import os
NAME = "append.txt"
def sandbox_argv(cmd, cfg_host, cfg_in):
    cmd = list(cmd)
    if "--append-system-prompt" in cmd:
        i = cmd.index("--append-system-prompt")
        text = cmd[i + 1]
        p = os.path.join(cfg_host, NAME)
        with open(p, "w") as f: f.write(text)
        os.chmod(p, 0o444)
        cmd[i:i + 2] = ["--append-system-prompt-file", cfg_in + "/" + NAME]
    return cmd
