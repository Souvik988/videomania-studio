import assert from 'node:assert/strict';
import { test } from 'node:test';

import { PLAYBACK_SPEEDS, SPEED_MAX, SPEED_MIN, speedStep } from './playback-speed.ts';

test('the player plays from 0.25× to 4×, 3× and 4× the fastest', () => {
  assert.equal(SPEED_MIN, 0.25);
  assert.equal(SPEED_MAX, 4);
  assert.deepEqual(PLAYBACK_SPEEDS.slice(-3), [2, 3, 4]);
});

test('a speed is on the step nearest to it', () => {
  assert.equal(PLAYBACK_SPEEDS[speedStep(1)], 1);
  assert.equal(PLAYBACK_SPEEDS[speedStep(4)], 4);
  assert.equal(PLAYBACK_SPEEDS[speedStep(2.4)], 2);
  assert.equal(PLAYBACK_SPEEDS[speedStep(8)], 4);
  assert.equal(PLAYBACK_SPEEDS[speedStep(0.1)], 0.25);
  assert.equal(PLAYBACK_SPEEDS[speedStep(1.25)], 1);
});
