import { test } from 'node:test';
import assert from 'node:assert/strict';
import { givenAfter, pagesToSend } from '../chat/src/lib/skill-pages.ts';

test('a skill named in a message sends its page the first time a session meets it, then only its name', () => {
  assert.deepEqual(pagesToSend(['brand', 'pace', 'brand'], undefined, 'codex', null), ['brand', 'pace']);
  /* the first message, before the agent has a session of its own; then the session it started */
  let given = givenAfter(undefined, 'codex', null, ['brand']);
  given = givenAfter(given, 'codex', 's1', ['brand'], { fresh: true });
  assert.deepEqual(pagesToSend(['brand', 'pace'], given, 'codex', 's1'), ['pace']);
  given = givenAfter(given, 'codex', 's1', ['pace']);
  assert.deepEqual(given.codex, { session: 's1', names: ['brand', 'pace'] });
  assert.deepEqual(pagesToSend(['brand', 'pace'], given, 'codex', 's1'), []);
});

test('another agent, or a session that could not be taken up again, has none of the pages from before', () => {
  const given = givenAfter(undefined, 'codex', 's1', ['brand']);
  assert.deepEqual(pagesToSend(['brand'], given, 'claude', null), ['brand'], 'another agent');
  assert.deepEqual(pagesToSend(['brand'], given, 'codex', 's2'), ['brand'], 'another session');
  const fresh = givenAfter(given, 'codex', 's2', ['pace'], { fresh: true });
  assert.deepEqual(fresh.codex, { session: 's2', names: ['pace'] });
  assert.deepEqual(givenAfter(given, 'codex', 's1', ['pace'], { fresh: true }).codex, { session: 's1', names: ['pace'] }, 'started again under its id: what this message sent');
  assert.deepEqual(given.codex, { session: 's1', names: ['brand'] }, 'the record given is left as it was');
});
