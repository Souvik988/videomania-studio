import { test } from 'node:test';
import assert from 'node:assert/strict';
import { opensOnClick, posterRetryDelay, posterTry, within } from './projects-page.ts';

test('a list that never comes fails in its own time; one that comes or fails is passed on as it is', async () => {
  assert.equal(await within(Promise.resolve(3), 50), 3);
  await assert.rejects(within(Promise.reject(new Error('refused')), 50), /refused/);
  const t0 = Date.now();
  await assert.rejects(within(new Promise(() => {}), 50), /no answer within/);
  assert.ok(Date.now() - t0 < 1000);
});

test('a poster still being drawn is asked for again, less often each time, then given up on', () => {
  assert.deepEqual([0, 1, 2, 3, 4].map(posterRetryDelay), [4000, 8000, 16000, 32000, null]);
  assert.equal(posterTry('/api/projects/a/poster', 0), '/api/projects/a/poster');
  assert.equal(posterTry('/api/projects/a/poster', 2), '/api/projects/a/poster?try=2');
  assert.equal(posterTry('/api/projects/a/poster?cover=5', 1), '/api/projects/a/poster?cover=5&try=1');
});

test('a card opens on a click or a key press, not on the second click of a double-click', () => {
  /* a key press (Enter, Space) is a click of detail 0 */
  assert.equal(opensOnClick({ detail: 0 }), true);
  assert.equal(opensOnClick({ detail: 1 }), true);
  /* the first click already opened a folder; what is under the pointer now was not aimed at */
  assert.equal(opensOnClick({ detail: 2 }), false);
  assert.equal(opensOnClick({ detail: 3 }), false);
});
