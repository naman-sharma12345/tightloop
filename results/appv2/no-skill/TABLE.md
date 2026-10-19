# APPV2 no-skill baseline: per-spec tokens (n=3, worker numbers = claims)

cw = in + 5*out + 0.1*cache_read + 1.25*cache_write; tokens = in + out + cache_read + cache_write

## habits (n=3)
- tokens median 1,818,196 [1,113,347-1,870,078] per run ['1,870,078', '1,113,347', '1,818,196']
- cw median 596,348.95 [486,596.85-604,873.20] per run [596348.95, 486596.85, 604873.2]
- output median 60,365 [59,380-66,201]; turns median 25 [17-27]; wall median 635 s [612-675]
- checker v2 per run ['1/2', '1/2', '1/2']; browser_crash_events [0, 0, 0]

## invoice (n=3)
- tokens median 2,612,366 [2,030,322-2,960,282] per run ['2,612,366', '2,030,322', '2,960,282']
- cw median 877,047.60 [868,566.45-929,478.15] per run [929478.15, 877047.6, 868566.45]
- output median 102,504 [90,886-102,947]; turns median 28 [22-36]; wall median 904 s [835-1024]
- checker v2 per run ['1/2', '2/2', '2/2']; browser_crash_events [0, 0, 0]

## trip (n=3)
- tokens median 2,686,577 [1,994,718-3,596,932] per run ['1,994,718', '3,596,932', '2,686,577']
- cw median 858,594.75 [719,493.70-1,059,801.60] per run [719493.7, 1059801.6, 858594.75]
- output median 92,890 [82,630-106,492]; turns median 31 [24-35]; wall median 857 s [761-1119]
- checker v2 per run ['1/2', '1/2', '1/2']; browser_crash_events [0, 0, 0]

