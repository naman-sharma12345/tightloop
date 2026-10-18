set -e
cd /tmp/tlb_push/benchmark/blind
T=$(mktemp -d /tmp/tlb-leaknc-XXXX); cp -r checks/reference/kanban $T/clean; cp -r checks/reference/kanban $T/planted
python3 leakgrep_r2.py $T/clean | tail -1
P=$T/planted; mkdir -p $P/.claude/skills/x; echo hi > $P/.claude/skills/x/SKILL.md
sed -i 's#</body>#<!-- tightloop --></body>#' $P/index.html
echo "OK 12 controls clicked" > $P/look_out.txt; echo "console error x" > $P/console.log; echo "plan" > $P/NOTES.md
python3 -c "import zlib,struct;open('$P/screenshot.png','wb').write(b'\x89PNG\r\n\x1a\n')"
python3 -c "open('$P/icon.png','wb').write(b'\x89PNG')"; echo "// v4c" > $P/extra.js
python3 leakgrep_r2.py $P || echo "planted exit=$?"
# zip: clean + planted entry
python3 - <<EOF
import zipfile; z=zipfile.ZipFile('$T/clean.zip','w'); z.write('$T/clean/index.html','viewer/builds/kanban-A-x/index.html'); z.close()
z=zipfile.ZipFile('$T/planted.zip','w'); z.write('$T/clean/index.html','viewer/builds/kanban-A-x/index.html'); z.writestr('viewer/builds/kanban-B-y/app.js','// ponytail'); z.close()
EOF
python3 leakgrep_r2.py $T/clean.zip | tail -1
python3 leakgrep_r2.py $T/planted.zip || echo "planted zip exit=$?"
rm -rf $T
