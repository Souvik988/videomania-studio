import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { WINDOW_BUTTONS_H, previewTop } from '../chat/src/lib/preview-top.ts';

test('on Windows the lightbox starts below the window\'s buttons; elsewhere where it did', () => {
  assert.equal(previewTop('Win32'), `${WINDOW_BUTTONS_H + 8}px`);
  assert.equal(previewTop('MacIntel'), 'max(1rem, var(--inset-titlebar-h, 0px))');
  assert.equal(previewTop('Linux x86_64'), 'max(1rem, var(--inset-titlebar-h, 0px))');
});

test('the buttons\' height is the one the window draws them at (main.mjs, titleBarOverlay)', () => {
  const main = readFileSync(new URL('./main.mjs', import.meta.url), 'utf8');
  const overlay = main.match(/const overlayColours = [^\n]*height: (\d+)/);
  assert.ok(overlay, 'main.mjs sets the title bar overlay\'s height');
  assert.equal(Number(overlay[1]), WINDOW_BUTTONS_H);
});
