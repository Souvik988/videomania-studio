import assert from 'node:assert/strict';
import { test } from 'node:test';
import { accountName, accountTrouble } from '../chat/src/lib/account-trouble.ts';

test('a turn that failed for the account offers Switch account; one that failed for the work does not', () => {
  for (const error of [
    'Your organization has disabled Claude subscription access for Claude Code · Use an Anthropic API key instead, or ask your admin to enable access',
    'Not logged in · Please run /login',
    'Session expired. Please run /login to sign in again.',
    'Claude Code is not signed in. Sign in under Settings → Agents.',
    'Kimi is not signed in. Sign in under Settings → Agents.',
    'API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"Invalid bearer token"}}',
    'Request failed with status 403 Forbidden',
    'Unauthorized: invalid API key',
    'Cursor: Authentication required',
  ]) assert.equal(accountTrouble(error), true, error);
  for (const error of [
    'Claude Code stopped while answering without saying why. If it cannot reach its service, check the network or proxy, then try again.',
    'Codex 0.120.0 is older than OpsGen needs (0.132.0 or later): update Codex, then try again.',
    'The model gpt-5 does not exist',
    'Rate limit reached: 429',
    '',
  ]) assert.equal(accountTrouble(error), false, error);
  assert.equal(accountTrouble(null), false);
});

test("the account a failed turn names: its organization and email, not a personal account's organization again", () => {
  assert.equal(accountName({ method: 'claude.ai', email: 'me@example.test', org: 'Acme Films' }), 'Acme Films · me@example.test');
  assert.equal(accountName({ method: 'claude.ai', email: 'me@example.test', org: "me@example.test's Organization" }), 'me@example.test');
  assert.equal(accountName({ method: 'chatgpt' }), null);
  assert.equal(accountName(undefined), null);
});
