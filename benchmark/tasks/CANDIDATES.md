# Task candidates (paper only - nothing here is vendored or verified)

Widening list across the three kinds. Every entry is UNVERIFIED: it becomes
a task only after license re-read at the pinned commit, a clean hidden-patch
extraction, and a reference-fix run proving the grader both ways.

## Bug fixes (real upstream fix commits that add tests)

- cli/cli (MIT) - gh command fixes with Go tests
  - VERIFIED candidate ghcli-01: commit 221e12681 (Add a shared result line for unchanged artifacts), license re-read live at the fix commit (MIT), baseline fails (undefined: PrintUnchanged), reference fix passes (go test exit 0). Mined and checked 2026-10-18; not yet vendored.
- BurntSushi/ripgrep (MIT) - regex/glob edge cases with Rust integration tests (BLOCKED on a Rust toolchain for verification)
- junegunn/fzf (MIT) - Go, has test suite (mined 2026-10-18: 0 commits matched the fix+separate-test-file pattern)
- sindresorhus/ky (MIT) - HTTP client (mined 2026-10-18: 0 pattern matches)
- tinyhttp/tinyhttp (MIT) - Express-like (mined 2026-10-18: 0 pattern matches)

## Features (real upstream feature commits checked by upstream tests)

- sharkdp/fd (MIT/Apache-2.0) - new flag additions with integration tests
- clap-rs/clap (MIT/Apache-2.0) - builder API additions
- gin-gonic/gin (MIT) - middleware additions
  - VERIFIED candidate ginfeat-01: commit dbd8a251 (feat: AbortWithStatusPureJSON), license re-read live (MIT), baseline fails (undefined method), reference fix passes (go test exit 0). Mined and checked 2026-10-18; not yet vendored.
- axios/axios (MIT) - interceptor/adapter features

## Small apps (from-scratch specs, pinned tests)

- app-05: ini-file parser library + CLI (Python, pytest)
- app-06: static file server with range requests (Go, go test) - even, holdout
- app-07: JSON diff CLI (Node, node:test)
- app-08: cron-expression parser (Rust, cargo test) - even, holdout
