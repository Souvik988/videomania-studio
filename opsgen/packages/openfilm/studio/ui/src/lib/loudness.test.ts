import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dbToVolume, measuredSpan, normalizeVolume, VOLUME_DB_MAX, VOLUME_DB_MIN, volumeToDb } from './loudness.ts';

test('a clip 6 dB too quiet gets twice the gain; one too loud less', () => {
  assert.deepEqual(normalizeVolume(-20, -14), { volume: 1.995, reached: true });
  assert.deepEqual(normalizeVolume(-8, -14), { volume: 0.501, reached: true });
  assert.deepEqual(normalizeVolume(-16, -16), { volume: 1, reached: true });
});

test('a clip 13 dB too quiet, as a voice recorded on a phone often is, reaches the target', () => {
  assert.deepEqual(normalizeVolume(-27, -14), { volume: 4.467, reached: true });
});

test('past 500% the clip gets the most it can, and says the loudness it reaches', () => {
  const plan = normalizeVolume(-30, -14);
  assert.equal(plan.volume, 5);
  assert.equal('reached' in plan && plan.reached, false);
  assert.ok('lufs' in plan && Math.abs(plan.lufs - -16) < 0.01, JSON.stringify(plan));
});

test('the volume slider in dB: 0 dB as is, +6 dB twice, the bottom silent, the top 500%', () => {
  assert.equal(VOLUME_DB_MAX, 14);
  assert.equal(volumeToDb(1), 0);
  assert.equal(volumeToDb(2), 6);
  assert.equal(volumeToDb(0.5), -6);
  assert.equal(volumeToDb(5), 14);
  assert.equal(volumeToDb(0), VOLUME_DB_MIN);
  assert.equal(dbToVolume(0), 1);
  assert.equal(dbToVolume(6), 1.995);
  assert.equal(dbToVolume(-6), 0.501);
  assert.equal(dbToVolume(14), 5);
  assert.equal(dbToVolume(VOLUME_DB_MIN), 0);
  /* what the slider writes it shows again */
  for (const db of [-40, -12.5, -0.1, 0.1, 3, 9.9]) assert.equal(volumeToDb(dbToVolume(db)), db);
});

test('silence has no loudness to bring anywhere', () => {
  assert.deepEqual(normalizeVolume(-70, -14), { silent: true });
  assert.deepEqual(normalizeVolume(null, -14), { silent: true });
  assert.deepEqual(normalizeVolume(Number.NEGATIVE_INFINITY, -14), { silent: true });
});

test('what is measured is the part of the file the clip plays, speed included', () => {
  assert.deepEqual(measuredSpan({ inMs: 2000, speed: 2, startMs: 10_000, endMs: 13_000 }), { from: 2, to: 8 });
  assert.deepEqual(measuredSpan({ startMs: 0, endMs: 1500 }), { from: 0, to: 1.5 });
});
