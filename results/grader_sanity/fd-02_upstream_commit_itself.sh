set -u
W=$(mktemp -d /tmp/tlw-upstream-XXXX); git clone -q /home/user/tab/work/tl_tools/tl-cache/fd.git $W && cd $W && git checkout -q ed4766419152120bb0b21516f581b4a4ac71f531 && git log --oneline -1 && (timeout -k 5 600 cargo test --test tests test_pattern_with_forward_slash 2>&1 | grep -E "^test |test result|C.Foo2|did not produce"); cd /; rm -rf "$W"
