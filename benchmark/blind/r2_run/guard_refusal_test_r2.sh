#!/bin/bash
# driver guard refusal test (Naman m:b3c5c470 pt 4, m:5eb8c3c4 pt 6). Never creates START_OK; uses only refusing conditions.
set -u
DRV=${1:-/home/user/tab/work/tl_blind_r2/benchmark/blind/r2_run/blind_driver_r2.py}
SNAP=${2:-/home/user/tab/work/tl_blind_r2}
echo "== 1. real launch as the driver would run: python3 $DRV"
timeout -k 5 60 python3 "$DRV"; echo "exit=$?"
echo "== 2. guard with a snapshot dir that has no .snap_commit (empty dir)"
E=$(mktemp -d /tmp/tlb-guardXXXX); timeout -k 5 60 python3 "$DRV" --guard-test "$E" /home/user/tab/files/tl_blind/r2/START_OK; echo "exit=$?"; rm -rf "$E"
echo "== 3. a fake build process named cargo running (symlink to sleep) while the guard runs"
F=$(mktemp -d /tmp/tlb-guardXXXX); ln -s "$(command -v sleep)" "$F/cargo"; "$F/cargo" 30 & FP=$!
sleep 0.5; timeout -k 5 60 python3 "$DRV" --guard-test "$SNAP" /home/user/tab/files/tl_blind/r2/START_OK; echo "exit=$?"
kill $FP; rm -rf "$F"
echo "== START_OK present: $([ -e /home/user/tab/files/tl_blind/r2/START_OK ] && echo yes || echo no) (never created by this test)"
