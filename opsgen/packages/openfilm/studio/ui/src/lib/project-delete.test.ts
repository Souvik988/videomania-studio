import { test } from 'node:test';
import assert from 'node:assert/strict';
import { stillThere } from './project-delete.ts';

const now = () => Promise.resolve();

test('a delete whose answer was lost counts once the project leaves the list; one refused stays', async () => {
  /* the open project's request was cut off, the server still moving it: gone at the second look */
  const lists = [['a', 'b'], ['b']];
  const left = await stillThere([{ id: 'a', lost: true }, { id: 'b', lost: false }], async () => lists.shift() ?? ['b'], { wait: now });
  assert.deepEqual(left.map((f) => f.id), ['b']);
});

test('a project already gone was deleted; an unreadable list changes nothing; a lost one still there after the tries stays', async () => {
  assert.deepEqual(await stillThere([{ id: 'a', lost: false }], async () => [], { wait: now }), []);
  assert.deepEqual((await stillThere([{ id: 'a', lost: false }], () => Promise.reject(new Error('down')), { wait: now })).map((f) => f.id), ['a']);
  let reads = 0;
  const left = await stillThere([{ id: 'a', lost: true }], async () => { reads += 1; return ['a']; }, { tries: 3, wait: now });
  assert.deepEqual([left.map((f) => f.id), reads], [['a'], 3]);
});
