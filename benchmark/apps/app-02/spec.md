# app-02: mdlite (Node.js, no dependencies)

Build `mdlite.mjs` in the workspace root. It is run as:

    node mdlite.mjs FILE

It reads a Markdown file and prints HTML to stdout, nothing else.

Supported subset, and the exact output for each construct:
- `# ` to `###### ` at line start: `<h1>text</h1>` ... `<h6>text</h6>`.
- Any other non-empty line: `<p>text</p>`. Consecutive non-empty lines are
  separate paragraphs (one `<p>` per line).
- Lines starting with `- ` form a list: each item becomes `<li>text</li>`,
  and the whole run of consecutive `- ` lines is wrapped in one
  `<ul>...</ul>`.
- Blank lines separate blocks and produce no output.
- Inline markup inside any text: `**b**` -> `<strong>b</strong>`,
  `*i*` -> `<em>i</em>`, `` `c` `` -> `<code>c</code>`,
  `[t](u)` -> `<a href="u">t</a>`. Inline markup is not nested.

The last line of output ends with a newline. Only Node.js built-ins may be
used (the file must run with `node mdlite.mjs`, no npm install).
