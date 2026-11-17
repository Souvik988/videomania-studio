import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeLook, previewSettled, type LookRead, type LookSet } from './look.ts';
import { MIXED } from './mixed.ts';
import { TEXT_FILL, textColorCss } from './clip-look.ts';

type Thing = { id: string; css: Record<string, string> };
const readOf = (t: Thing): LookRead => (prop) => t.css[prop];

/** A look over `things` that records what it is asked to write and to show. */
function watched(things: Thing[]) {
  const commits: [string, LookSet][][] = [];
  const previews: [string, LookSet][][] = [];
  let reverts = 0;
  const look = makeLook(things, readOf, {
    commit: (sets) => commits.push(sets.map(([t, s]) => [t.id, s])),
    preview: (sets) => previews.push(sets.map(([t, s]) => [t.id, s])),
    revert: () => { reverts++; },
  });
  return { look, commits, previews, reverts: () => reverts };
}

test('a look tells a value its things agree on, and MIXED when they do not', () => {
  const a = { id: 'a', css: { opacity: '0.5', color: '#ffffff' } };
  const b = { id: 'b', css: { opacity: '0.5', color: '#000000' } };
  const { look } = watched([a, b]);
  assert.equal(look.n, 2);
  assert.equal(look.common((read) => read('opacity')), '0.5');
  assert.equal(look.common((read) => read('color')), MIXED);
  assert.equal(watched([]).look.common((read) => read('opacity')), MIXED, 'nothing in hand agrees on nothing');
});

test('a commit writes only what it changes, and only for the things it changes', () => {
  const a = { id: 'a', css: { opacity: '1' } };
  const b = { id: 'b', css: { opacity: '0.5' } };
  const { look, commits } = watched([a, b]);
  look.commit(() => ({ opacity: '0.5', filter: 'none' }));
  assert.deepEqual(commits, [[['a', { opacity: '0.5', filter: 'none' }], ['b', { filter: 'none' }]]]);
  look.commit((read) => ({ opacity: read('opacity') ?? null }));
  assert.equal(commits.length, 1, 'a no-op is not an undo step');
});

test('a preview kept by a commit is still written, though the things read as the preview by then', () => {
  const thing = { id: 'a', css: { opacity: '1' } };
  const { look, previews } = watched([thing]);
  look.preview(() => ({ opacity: '0.4' }));
  assert.deepEqual(previews, [[['a', { opacity: '0.4' }]]]);
  /* measured again while previewed: the panel makes a new look over what the picture shows */
  const now = watched([{ id: 'a', css: { opacity: '0.4' } }]);
  now.look.commit(() => ({ opacity: '0.4' }));
  assert.deepEqual(now.commits, [[['a', { opacity: '0.4' }]]]);
});

test('a commit is worked out from before its preview: a text color dragged in the picker keeps taking over the words\' own fill', () => {
  /* gold words: their page paints them with a fill of their own over their color */
  const gold = { id: 'head', css: { color: '#b39458', [TEXT_FILL]: '#b39458' } };
  const { look, previews } = watched([gold]);
  look.preview((read) => textColorCss(read, '#6b5020'));
  assert.deepEqual(previews, [[['head', { color: '#6b5020', [TEXT_FILL]: 'currentcolor' }]]]);
  /* previewed, the words' fill follows their color: measured again, they have no fill of their own */
  const now = watched([{ id: 'head', css: { color: '#6b5020' } }]);
  now.look.preview((read) => textColorCss(read, '#402d07'));
  now.look.commit((read) => textColorCss(read, '#402d07'));
  assert.deepEqual(now.commits, [[['head', { color: '#402d07', [TEXT_FILL]: 'currentcolor' }]]]);
});

test('a preview taken back, or painted back by hand, leaves nothing for the next commit to work from', () => {
  const gold = { id: 'head', css: { color: '#b39458', [TEXT_FILL]: '#b39458' } };
  const first = watched([gold]);
  first.look.preview((read) => textColorCss(read, '#6b5020'));
  first.look.revert();
  assert.equal(first.reverts(), 1);
  const plain = watched([{ id: 'head', css: { color: '#ffffff' } }]);
  plain.look.commit((read) => textColorCss(read, '#ff0000'));
  assert.deepEqual(plain.commits, [[['head', { color: '#ff0000' }]]], 'reverted: the fill from before is not used');

  const second = watched([gold]);
  second.look.preview((read) => textColorCss(read, '#6b5020'));
  previewSettled();
  const again = watched([{ id: 'head', css: { color: '#ffffff' } }]);
  again.look.commit((read) => textColorCss(read, '#ff0000'));
  assert.deepEqual(again.commits, [[['head', { color: '#ff0000' }]]], 'settled: the fill from before is not used');
});
