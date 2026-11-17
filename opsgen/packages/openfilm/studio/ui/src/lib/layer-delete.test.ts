import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pointersOf, propsWithoutDeleted, withDeleted } from './layer-delete.ts';
import type { ComponentProp } from './component-props.ts';
import type { FilmOverride } from './film.ts';

test('a deleted layer keeps one entry: display none, where its first was', () => {
  const all: FilmOverride[] = [
    { fade: [0.5, 0] },
    { at: '#title', t: [4, 0], style: { color: 'red' }, text: 'Hi' },
    { at: '.card', n: 2, s: 1.2 },
    { at: '#title', lock: true },
  ];
  assert.deepEqual(withDeleted(all, [{ at: '#title' }]), [
    { fade: [0.5, 0] },
    { at: '#title', style: { display: 'none' } },
    { at: '.card', n: 2, s: 1.2 },
  ]);
  /* one of several matches: its own entry, the others' left alone */
  assert.deepEqual(withDeleted(all, [{ at: '.card', n: 1 }]), [...all, { at: '.card', n: 1, style: { display: 'none' } }]);
  assert.deepEqual(withDeleted(undefined, [{ at: '#x' }]), [{ at: '#x', style: { display: 'none' } }]);
});

test('what points only at deleted layers goes with them; the clip\'s own entry stays', () => {
  const all: FilmOverride[] = [{ fade: [0, 1] }, { at: '#card' }, { at: '#title', t: [1, 1] }, { at: '.note', style: { color: 'red' } }];
  assert.deepEqual(withDeleted(all, [{ at: '#card' }], [true, true, true, false]), [
    { fade: [0, 1] },
    { at: '#card', style: { display: 'none' } },
    { at: '.note', style: { color: 'red' } },
  ]);
  assert.equal(withDeleted([{ at: '#title', t: [1, 1] }], [], [true]), null);
});

test('the properties made of deleted layers go; a variable is no layer\'s', () => {
  const props: ComponentProp[] = [
    { name: 'Title', type: 'text', at: '#title' },
    { name: 'Accent', type: 'var', var: '--accent' },
    { name: 'Photo', type: 'image', kind: 'img', at: 'img', n: 2 },
  ];
  const pointers = pointersOf([{ fade: [0, 1] }, { at: '#a', n: 3 }], props);
  assert.deepEqual(pointers, { overrides: [null, { at: '#a', n: 3 }], props: [{ at: '#title' }, null, { at: 'img', n: 2 }] });
  assert.deepEqual(propsWithoutDeleted(props, [true, true, false]).map((p) => p.name), ['Accent', 'Photo']);
});
