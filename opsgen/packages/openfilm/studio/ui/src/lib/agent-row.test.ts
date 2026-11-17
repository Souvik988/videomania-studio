import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accountOrg, missingActions, ownModelError, switchOffer } from './agent-row.ts';
import { zhCN } from '../i18n/zh-CN.ts';

test('an agent not found offers Locate and its installer, or its install page', () => {
  const host = { locate: true, install: true };
  assert.deepEqual(missingActions({ installer: 'irm https://example.test/install.ps1 | iex', install: 'https://example.test' }, host), { locate: true, install: 'run' });
  assert.deepEqual(missingActions({ install: 'https://example.test' }, host), { locate: true, install: 'page' });
  assert.deepEqual(missingActions({ installer: 'x', install: 'https://example.test' }, { locate: false, install: false }), { locate: false, install: 'page' });
});

test("Claude Code setup avoids reinstalling the app and still lets an existing CLI be selected", () => {
  assert.deepEqual(missingActions({ setupRequired: 'code-tab', install: 'https://example.test' }, { locate: true, install: true }), { locate: true, install: null });
});

test("an account's organization is named unless it only repeats the email, as a personal Claude account's does", () => {
  assert.equal(accountOrg({ org: "me@example.test's Organization", email: 'me@example.test' }), null);
  assert.equal(accountOrg({ org: 'Acme Films', email: 'me@example.test' }), 'Acme Films');
  assert.equal(accountOrg({ org: "me@example.test's Organization" }), "me@example.test's Organization");
  assert.equal(accountOrg({ email: 'me@example.test' }), null);
});

test("an own model not saved is said in the person's language, with the address, status or reason; the service's own words as they are", () => {
  const t = (path: string) => path.split('.').reduce<unknown>((at, part) => (at as Record<string, unknown> | undefined)?.[part], zhCN) as string | undefined ?? path;
  assert.equal(ownModelError({ error: 'in English', code: 'web-page', url: 'https://example.test/v1/responses', status: 405 }, t), 'https://example.test/v1/responses 返回的是网页（405），不是 API：请检查地址和 API 格式。');
  assert.equal(ownModelError({ error: 'in English', code: 'unreachable', reason: 'fetch failed' }, t), '连不上这个服务：fetch failed');
  assert.equal(ownModelError({ error: 'in English', code: 'no-key' }, t), '请粘贴密钥。');
  assert.equal(ownModelError({ error: 'Unknown parameter: max_output_tokens' }, t), 'Unknown parameter: max_output_tokens');
  assert.equal(ownModelError({ error: 'from a newer app', code: 'something-new' }, t), 'from a newer app');
});

test('a connected agent switches account here when it signs out with its own command; else the row says where', () => {
  const host = { switchAccount: true };
  assert.equal(switchOffer({ id: 'claude', status: 'ready', signOut: true }, host), 'here');
  assert.equal(switchOffer({ id: 'deepseek', status: 'ready' }, host), 'elsewhere');
  assert.equal(switchOffer({ id: 'claude', status: 'ready', signOut: true }, { switchAccount: false }), 'elsewhere', 'an older app');
  assert.equal(switchOffer({ id: 'claude', status: 'off', signOut: true }, host), null);
  assert.equal(switchOffer({ id: 'byok', status: 'ready' }, host), null);
});
