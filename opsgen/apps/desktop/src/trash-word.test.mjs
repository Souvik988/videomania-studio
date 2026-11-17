import { test } from 'node:test';
import assert from 'node:assert/strict';

/** The chat's words as a system shows them: the dictionary read afresh, with that system's `navigator.platform`. */
async function wordsOn(platform, file, name) {
  const before = Object.getOwnPropertyDescriptor(globalThis, 'navigator');
  Object.defineProperty(globalThis, 'navigator', { value: { platform }, configurable: true });
  try {
    return JSON.stringify((await import(`../chat/src/i18n/locales/${file}?${platform}`))[name]);
  } finally {
    if (before) Object.defineProperty(globalThis, 'navigator', before);
  }
}

test('the chat names the trash as the system does: the Recycle Bin on Windows, the Trash on a Mac', async () => {
  assert.ok((await wordsOn('Win32', 'zh-CN.ts', 'zhCN')).includes('移到回收站'));
  assert.ok((await wordsOn('MacIntel', 'zh-CN.ts', 'zhCN')).includes('移到废纸篓'));
  assert.ok((await wordsOn('Win32', 'en-US.ts', 'enUS')).includes('to the Recycle Bin'));
  assert.ok((await wordsOn('MacIntel', 'en-US.ts', 'enUS')).includes('to the Trash'));
});
