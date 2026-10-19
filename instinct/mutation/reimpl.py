#!/usr/bin/env python3
"""focus_series independent re-implementation (task 8f64be04, written 2026-10-19 ~05:53Z, before addendum 1 was committed).
Written from the PREREG.md definitions (71d8ca85) and from reading src/ext/focus_series.rs (PxRect::from_xywh, score_plane) at 8c073452.
NOT part of PREREG.md. Used for: the F4c values in PREREG_ADDENDUM_1.md (b6636a39), and the per-mutant value predictions in its
MUTATION PREDICTIONS section (M1 rect +1 px, M2 kernel -3). Prints every number quoted there."""
import math

W, H = 160, 90
def checker(x, y): return 255.0 if ((x // 8) + (y // 8)) % 2 == 1 else 0.0
CHK = [[checker(x, y) for x in range(W)] for y in range(H)]
SPLIT = [[128.0 if x >= 80 else checker(x, y) for x in range(W)] for y in range(H)]

def box(rect, w=W, h=H, shift=0):
    """Rect placement. shift=0 is score_plane at 8c073452; shift=1 models mutant M1 (r.x0+1, r.y0+1, r.x1+1, r.y1+1)."""
    x0, y0, x1, y1 = 1, 1, w - 1, h - 1                                              # interior, as score_plane
    if rect is not None:
        rx0, ry0 = math.floor(rect[0]), math.floor(rect[1])                          # PxRect::from_xywh: floor(x), floor(y)
        rx1, ry1 = math.floor(rect[0] + rect[2]), math.floor(rect[1] + rect[3])      # floor(x + w), floor(y + h), exclusive
        x0, y0 = max(x0, rx0 + shift), max(y0, ry0 + shift)                          # x0 = x0.max(r.x0)  (M1: r.x0 + 1)
        x1, y1 = min(x1, rx1 + shift), min(y1, ry1 + shift)                          # x1 = x1.min(r.x1)  (M1: r.x1 + 1)
    return x0, y0, x1, y1

def score(y, b, kc=4.0):
    """Sequential f64 sums in the same loop order as score_plane; kc=4 is the real kernel, kc=3 models mutant M2."""
    x0, y0, x1, y1 = b
    if x1 <= x0 or y1 <= y0: return None
    sl = sl2 = sg = 0.0; n = 0
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            p = lambda dx, dy: y[yy + dy][xx + dx]
            c = p(0, 0); l = p(-1, 0) + p(1, 0) + p(0, -1) + p(0, 1) - kc * c
            gx = (p(1, -1) + 2 * p(1, 0) + p(1, 1)) - (p(-1, -1) + 2 * p(-1, 0) + p(-1, 1))
            gy = (p(-1, 1) + 2 * p(0, 1) + p(1, 1)) - (p(-1, -1) + 2 * p(0, -1) + p(1, -1))
            sl += l; sl2 += l * l; sg += math.sqrt(gx * gx + gy * gy); n += 1
    m = sl / n
    return round(max(sl2 / n - m * m, 0.0), 6), round(sg / n, 6), n

if __name__ == "__main__":
    print("calibration on ALREADY-MEASURED values (SCORE.tsv / b1.run.log):")
    print("  S frame 0 whole        ", score(CHK, box(None)), " measured 39714.636076 / 421.02446")
    print("  F2 A [8,8,64,74]       ", score(SPLIT, box([8, 8, 64, 74])), " measured 41299.662162 / 432.242329")
    print("  F2 B [88,8,64,74]      ", score(SPLIT, box([88, 8, 64, 74])), " measured 0 / 0")
    print("F4 (clean code):")
    for r in ([150, 80, 20, 20], [150, 80, 10, 10], [150, 80, 9, 9]):
        print("  ramp f0", r, score(CHK, box(r)), " split", score(SPLIT, box(r)))
    print("M1 model (shift=1):")
    print("  F2 A                   ", score(SPLIT, box([8, 8, 64, 74], shift=1)))
    print("  F2 B                   ", score(SPLIT, box([88, 8, 64, 74], shift=1)))
    print("  F4c ramp f0            ", score(CHK, box([150, 80, 20, 20], shift=1)))
    print("M2 model (kc=3):")
    print("  F2 A                   ", score(SPLIT, box([8, 8, 64, 74]), 3.0))
    print("  F4c ramp f0            ", score(CHK, box([150, 80, 20, 20]), 3.0))
    print("  S frame 0 whole        ", score(CHK, box(None), 3.0))
