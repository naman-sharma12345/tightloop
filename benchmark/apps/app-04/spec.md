# app-04: wordfreq (Rust, no external crates)

Build a Rust binary crate named `wordfreq` (binary name `wordfreq`). It is
run as:

    wordfreq [--top N]

- It reads all of standard input.
- A word is a maximal run of non-whitespace characters, lowercased, with
  leading and trailing ASCII punctuation (non-alphanumeric) removed. Empty
  results after stripping are ignored.
- It prints one line per distinct word: `<count> <word>`.
- Lines are sorted by count descending; ties are sorted by word ascending
  (byte order).
- With `--top N`, at most N lines are printed.
- Output ends with a newline after the last line (no trailing blank line).
- Only the Rust standard library may be used.
