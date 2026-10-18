#!/bin/bash
# r2 network-block proof: same bwrap prefix as blind_driver_r2.py (incl. sandbox_hosts on /etc/hosts)
set -u
TD=/home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3
WT=$(mktemp -d /tmp/tlb-nettest-XXXX)
B=(bwrap --dev-bind / / --tmpfs /home/user/tab --bind /home/user/tab/work/tl_tools /home/user/tab/work/tl_tools --tmpfs /home/user/.prime --tmpfs /dev/shm --tmpfs /tmp --bind $WT $WT --ro-bind $TD/sandbox_hosts /etc/hosts --chdir $WT --die-with-parent)
for u in https://github.com https://raw.githubusercontent.com/naman-sharma12345/tightloop/main/README.md https://api.github.com/repos/naman-sharma12345/tightloop https://codeload.github.com/naman-sharma12345/tightloop/zip/refs/heads/main; do
  h=$(echo $u | cut -d/ -f3)
  o=$(timeout -k 2 15 "${B[@]}" curl -sS -m 8 -o /dev/null -w "%{http_code}" "$u" 2>&1); echo "INSIDE  curl $h -> rc=$? ${o:0:90}"
done
o=$(timeout -k 2 20 "${B[@]}" git ls-remote https://github.com/naman-sharma12345/tightloop 2>&1 | tail -1); echo "INSIDE  git ls-remote github.com -> ${o:0:90}"
o=$(timeout -k 2 15 "${B[@]}" getent hosts github.com 2>&1); echo "INSIDE  getent hosts github.com -> $o"
o=$(curl -sS -m 8 -o /dev/null -w "%{http_code}" https://github.com 2>&1); echo "OUTSIDE curl github.com -> $o (control: host network itself works)"
umask 077; printf 'x-api-key: %s\n' "$MK" > $WT/.h
o=$(timeout -k 2 70 "${B[@]}" curl -sS -m 60 -o $WT/.r -w "%{http_code}" -H "content-type: application/json" -H "anthropic-version: 2023-06-01" -H @$WT/.h -d '{"model":"claude-opus-5-5","max_tokens":5,"messages":[{"role":"user","content":"Reply with OK"}]}' "$MB/v1/messages" 2>&1)
echo "INSIDE  minimal model call (curl, same sandbox) -> HTTP $o reply: $(python3 -c "import json;print(''.join(c.get('text','') for c in json.load(open('$WT/.r')).get('content',[]))[:20])" 2>&1)"
rm -rf $WT
