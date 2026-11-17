import { test } from 'node:test';
import assert from 'node:assert/strict';
import { MODEL_WAIT_MS, QUIET_MS, idleStatus } from '../chat/src/lib/agent-activity-runs.ts';

test('quiet, any agent says "Working", then "Still working" after half a minute', () => {
  for (const ownAgent of [false, true]) {
    assert.equal(idleStatus(0, ownAgent), 'act.working');
    assert.equal(idleStatus(QUIET_MS - 1, ownAgent), 'act.working');
    assert.equal(idleStatus(QUIET_MS, ownAgent), 'act.stillWorking');
    assert.equal(idleStatus(MODEL_WAIT_MS - 1, ownAgent), 'act.stillWorking');
  }
});

test('after two minutes of quiet, the app\'s own agent says it waits for the model; other agents still say "Still working"', () => {
  assert.equal(MODEL_WAIT_MS, 2 * 60_000);
  assert.equal(idleStatus(MODEL_WAIT_MS, true), 'act.waitingForModel');
  assert.equal(idleStatus(10 * 60_000, true), 'act.waitingForModel');
  assert.equal(idleStatus(MODEL_WAIT_MS, false), 'act.stillWorking');
  assert.equal(idleStatus(10 * 60_000, false), 'act.stillWorking');
});
