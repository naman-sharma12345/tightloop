import subprocess, sys, os

WS = os.path.dirname(os.path.abspath(__file__))

def run(args):
    return subprocess.run([sys.executable, "csvstat.py"] + args,
                          cwd=WS, capture_output=True, text=True)

def write(tmp_path, text):
    p = tmp_path / "data.csv"
    p.write_text(text)
    return str(p)

CSV = "name,age,score\na,10,1.5\nb,20,2.5\nc,,3.0\n"

def test_count(tmp_path):
    f = write(tmp_path, CSV)
    r = run([f, "age", "count"])
    assert r.returncode == 0 and r.stdout == "2\n"

def test_min_max(tmp_path):
    f = write(tmp_path, CSV)
    assert run([f, "score", "min"]).stdout == "1.5\n"
    assert run([f, "score", "max"]).stdout == "3.0\n"

def test_mean(tmp_path):
    f = write(tmp_path, CSV)
    r = run([f, "score", "mean"])
    assert r.returncode == 0 and r.stdout.strip() == "2.33"

def test_missing_column(tmp_path):
    f = write(tmp_path, CSV)
    r = run([f, "nope", "count"])
    assert r.returncode == 1 and r.stderr.strip() != ""
