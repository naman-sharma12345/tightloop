set -u
T=$(mktemp -d /tmp/tlb-packdry-XXXX); R=/tmp/tlb_push/benchmark/blind/checks/reference
for case in clean planted; do
  for a in bookmarks expenses kanban; do for L in A B C D; do mkdir -p $T/$case/out/$a/$L; cp -r $R/$a/. $T/$case/out/$a/$L/; done; done
done
P=$T/planted/out
mkdir -p $P/bookmarks/C/.claude/skills/tightloop && echo x > $P/bookmarks/C/.claude/skills/tightloop/SKILL.md
echo "12 controls clicked, 0 console errors" > $P/expenses/B/look_report.txt; echo err > $P/expenses/B/console.log
printf '\x89PNG' > $P/kanban/D/screenshot.png
for case in clean planted; do
  mkdir -p $T/$case/spec
  echo "=== pack dry-run: $case"
  R2_SNAP=/tmp/tlb_push R2_OUT=$T/$case/out R2_BL=$T/$case/bl R2_VD=$T/$case/viewer R2_LEAKLOG=$T/$case/leak.log R2_SPECDIR=$T/$case/spec timeout -k 5 200 python3 /home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3/pack_r2.py 2>&1 | grep -v '^/tmp/tlb-packdry-[A-Za-z0-9]*/[a-z0-9]*/viewer.zip$' | tail -14
  echo "exit=${PIPESTATUS[0]}"
  [ -f $T/$case/spec/blind_strip_log_r2.json ] && python3 -c "import json;d=json.load(open('$T/$case/spec/blind_strip_log_r2.json'));print('dropped:',{k:v['dropped'] for k,v in d.items() if v['dropped']})"
done
# planted 2: a skill word inside app code that the strip cannot drop
P2=$T/planted2/out; mkdir -p $T/planted2/spec
for a in bookmarks expenses kanban; do for L in A B C D; do mkdir -p $P2/$a/$L; cp -r $R/$a/. $P2/$a/$L/; done; done
echo '<!-- tightloop -->' >> $P2/kanban/A/index.html
echo "=== pack dry-run: planted2 (word in app code)"
R2_SNAP=/tmp/tlb_push R2_OUT=$P2 R2_BL=$T/planted2/bl R2_VD=$T/planted2/viewer R2_LEAKLOG=$T/planted2/leak.log R2_SPECDIR=$T/planted2/spec timeout -k 5 200 python3 /home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3/pack_r2.py 2>&1 | tail -8; echo "exit=${PIPESTATUS[0]}"
rm -rf $T
