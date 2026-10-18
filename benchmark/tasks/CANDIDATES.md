# Task candidates (paper only - nothing here is vendored or verified)

Widening list across the three kinds. Every entry is UNVERIFIED: it becomes
a task only after license re-read at the pinned commit, a clean hidden-patch
extraction, and a reference-fix run proving the grader both ways.

## Bug fixes (real upstream fix commits that add tests)

- cli/cli (MIT) - gh command fixes with Go tests
- BurntSushi/ripgrep (MIT) - regex/glob edge cases with Rust integration tests
- junegunn/fzf (MIT) - Go, has test suite
- sindresorhus/ky (MIT) - HTTP client, node:test coverage
- tinyhttp/tinyhttp (MIT) - Express-like, node tests

## Features (real upstream feature commits checked by upstream tests)

- sharkdp/fd (MIT/Apache-2.0) - new flag additions with integration tests
- clap-rs/clap (MIT/Apache-2.0) - builder API additions
- gin-gonic/gin (MIT) - middleware additions
- axios/axios (MIT) - interceptor/adapter features

## Small apps (from-scratch specs, pinned tests)

- app-05: ini-file parser library + CLI (Python, pytest)
- app-06: static file server with range requests (Go, go test) - even, holdout
- app-07: JSON diff CLI (Node, node:test)
- app-08: cron-expression parser (Rust, cargo test) - even, holdout
