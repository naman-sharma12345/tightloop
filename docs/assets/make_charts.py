"""Draws docs/assets/chart_tokens.png and chart_defects.png for the README.
Data: tokens from results/appv2/*/BUILD_RESULTS.tsv (input + output, where input is the
uncached input only; median of 3 per spec; the y-axis says so. The footer also gives the
cost-weighted sums so both numbers stay traceable);
defects from benchmark/blind/defect_r11/SCORES_r11_ns.jsonl and arms/SCORES_r11_arms.jsonl
(weighted_score, median per spec) after the label reveal. Numbers are typed in below so the
chart does not need the sealed key. Run: python docs/assets/make_charts.py"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

OUT = os.path.dirname(os.path.abspath(__file__))
BG, FG, MUTED, GRID, MINT, WARN = "#0a0e17", "#e6edf3", "#8b949e", "#1a2130", "#3ddc97", "#f0883e"
COL = {"no-skill": "#3b4350", "v4c (classic)": "#8b949e", "v11 (default)": MINT}
SPECS = ["habits", "invoice", "trip"]
# input+output per build, median of 3 (raw tokens)
TOKENS_IO = {"no-skill": [60409, 102548, 92938], "v4c (classic)": [65802, 110308, 90540],
             "v11 (default)": [60236, 87249, 73934]}
DEFECT_MEDIAN = {"no-skill": [0, 1, 1], "v4c (classic)": [0, 1, 3], "v11 (default)": [1, 3, 1]}
MAJORS = {"no-skill": [0, 0, 1], "v4c (classic)": [0, 1, 3], "v11 (default)": [0, 2, 1]}
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "text.color": FG, "xtick.color": FG,
                     "ytick.color": MUTED, "axes.edgecolor": GRID})


def base(title, lines):
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#3b4350")
    ax.tick_params(length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    fig.text(0.06, 0.93, title, fontsize=15, fontweight="bold")
    for i, line in enumerate(lines):
        fig.text(0.06, 0.875 - 0.04 * i, line, fontsize=9, color=MUTED)
    return fig, ax


def finish(fig, ax, top, path, left=0.07):
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(SPECS, fontsize=11)
    fig.subplots_adjust(left=left, right=0.98, top=top, bottom=0.17)
    fig.legend(handles=[mp.Patch(color=c, label=k) for k, c in COL.items()], loc="lower center", ncol=3,
               frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0), labelcolor=FG)
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


x, w = np.arange(3), 0.26
fig, ax = base("Input+output tokens per app build (median of 3)",
               ["Input+output summed over 9 builds: no-skill 765k, v4c 789k, v11 703k (8% below no-skill).",
                "Cost-weighted sums over 9 builds: no-skill 7.00M, v4c 6.13M, v11 4.82M "
                "(formula in the README)."])
for i, (k, v) in enumerate(TOKENS_IO.items()):
    bars = ax.bar(x + (i - 1) * w, v, w * 0.92, color=COL[k], zorder=3)
    for r, val in zip(bars, v):
        ax.text(r.get_x() + r.get_width() / 2, val + 1500, f"{val / 1000:.1f}k", ha="center", va="bottom",
                fontsize=8.5, color=MINT if k.startswith("v11") else FG,
                fontweight="bold" if k.startswith("v11") else "normal")
ax.set_ylim(0, 125000)
ax.set_yticks([0, 25000, 50000, 75000, 100000, 125000])
ax.set_yticklabels(["0", "25k", "50k", "75k", "100k", "125k"], fontsize=8.5)
ax.set_ylabel("input+output tokens (median of 3)", fontsize=9, color=MUTED)
finish(fig, ax, 0.79, os.path.join(OUT, "chart_tokens.png"), left=0.11)

fig, ax = base("Defect score per app build (lower is better)",
               ["Frozen weighted defect count (blocker 10, major 3, minor 1), median of 3 blind-scored builds.",
                "Orange: majors found in those 3 builds. Totals over 9 builds: no-skill 7 (1 major), "
                "v4c 16 (4), v11 15 (3)."])
for i, (k, v) in enumerate(DEFECT_MEDIAN.items()):
    xs = x + (i - 1) * w
    ax.bar(xs, [max(t, 0.04) for t in v], w * 0.92, color=COL[k], zorder=3)
    for xx, val, m in zip(xs, v, MAJORS[k]):
        ax.text(xx, val + 0.07, str(val), ha="center", va="bottom", fontsize=11, fontweight="bold",
                color=MINT if k.startswith("v11") else FG)
        ax.text(xx, val + 0.42, f"{m} major" + ("" if m == 1 else "s"), ha="center", va="bottom",
                fontsize=7.5, color=WARN if m else "#5b6472")
ax.text(1.0, 4.05, "invoice with the beforeprint print check: 1 / 1 / 1", ha="center", fontsize=8,
        color=MUTED, style="italic")
ax.set_ylim(0, 4.4)
ax.set_yticks([0, 1, 2, 3, 4])
ax.set_yticklabels([str(t) for t in range(5)], fontsize=8.5)
finish(fig, ax, 0.79, os.path.join(OUT, "chart_defects.png"))
