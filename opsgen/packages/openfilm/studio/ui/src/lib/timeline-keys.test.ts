import { test } from 'node:test';
import assert from 'node:assert/strict';
import { letterOf, loopBack, playStart, shuttleRate } from './timeline-keys.ts';

test('a letter is read by what it types, or where it sits when it types no Latin letter', () => {
  assert.equal(letterOf({ key: 'J', code: 'KeyJ' }), 'j');
  /* a French keyboard's A is where Q is on a US one: the letter it types counts */
  assert.equal(letterOf({ key: 'a', code: 'KeyQ' }), 'a');
  /* Korean: ㅓ is on J */
  assert.equal(letterOf({ key: 'ㅓ', code: 'KeyJ' }), 'j');
});

test('J / K / L: L faster each time up to 4×, J the same backwards, K stops; the other way starts at 1×', () => {
  let rate = 0;
  const seen = [];
  for (const key of ['l', 'l', 'l', 'l'] as const) { rate = shuttleRate(rate, key); seen.push(rate); }
  assert.deepEqual(seen, [1, 2, 4, 4]);
  assert.equal(shuttleRate(4, 'j'), -1);
  assert.equal(shuttleRate(-1, 'j'), -2);
  assert.equal(shuttleRate(-4, 'j'), -4);
  assert.equal(shuttleRate(-2, 'l'), 1);
  assert.equal(shuttleRate(2, 'k'), 0);
});

test('a loop goes back to the range\'s start at its end, or the film\'s without a range', () => {
  const range = { startMs: 1000, endMs: 3000 };
  assert.equal(loopBack(2500, range, 10_000), null);
  assert.equal(loopBack(3000, range, 10_000), 1000);
  assert.equal(loopBack(3400, range, 10_000), 1000, 'a tick past the end still loops');
  assert.equal(loopBack(9999.5, null, 10_000), 0);
  assert.equal(loopBack(5000, null, 10_000), null);
  /* playing starts where the playhead is inside the range, else at its start */
  assert.equal(playStart(2000, range, 10_000), 2000);
  assert.equal(playStart(500, range, 10_000), 1000);
  assert.equal(playStart(3000, range, 10_000), 1000);
  assert.equal(playStart(4000, null, 10_000), 4000);
  assert.equal(playStart(10_000, null, 10_000), 0);
});
