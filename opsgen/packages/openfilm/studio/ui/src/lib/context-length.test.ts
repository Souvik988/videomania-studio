import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseContextLength } from './context-length.ts';

test('a context length as typed: empty is none, a whole number from 32K to 10M holds, anything else does not', () => {
  assert.deepEqual(parseContextLength(''), {});
  assert.deepEqual(parseContextLength('  '), {});
  assert.deepEqual(parseContextLength('200000'), { context: 200_000 });
  assert.deepEqual(parseContextLength(' 1,000,000 '), { context: 1_000_000 }, 'thousands separators');
  assert.deepEqual(parseContextLength('128.000'), { context: 128_000 }, 'a thousands point');
  assert.deepEqual(parseContextLength('32000'), { context: 32_000 });
  assert.deepEqual(parseContextLength('10000000'), { context: 10_000_000 });
  assert.deepEqual(parseContextLength('200 000'), { context: 200_000 });
  for (const bad of ['31999', '4000', '10000001', '128K', '-8000', '1e6', 'abc', '128000.5', '40000,5', '1,0000']) assert.equal(parseContextLength(bad), null, bad);
});
