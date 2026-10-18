import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

function render(tmp, md) {
  const f = join(tmp, 'in.md');
  writeFileSync(f, md);
  return execFileSync('node', ['mdlite.mjs', f], { encoding: 'utf8' });
}

test('heading and paragraph', (t) => {
  assert.equal(render(t.tmpdir || '.', '# Hi\n\nworld\n'),
    '<h1>Hi</h1>\n<p>world</p>\n');
});

test('inline markup', (t) => {
  assert.equal(render(t.tmpdir || '.', 'a **b** *c* `d` [e](http://x)\n'),
    '<p>a <strong>b</strong> <em>c</em> <code>d</code> <a href="http://x">e</a></p>\n');
});

test('list', (t) => {
  assert.equal(render(t.tmpdir || '.', '- one\n- two\n'),
    '<ul><li>one</li><li>two</li></ul>\n');
});
