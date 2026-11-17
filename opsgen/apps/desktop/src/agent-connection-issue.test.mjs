import { test } from 'node:test';
import assert from 'node:assert/strict';
import { agentConnectionIssue } from './agent-connection-issue.mjs';

test('model quota and provider credentials are distinguished from discovery, authentication and temporary rate limits', () => {
  assert.equal(agentConnectionIssue(new Error('Internal error: Free usage limit reached. Connect a provider or switch models.')).kind, 'quota');
  assert.equal(agentConnectionIssue('insufficient_quota').kind, 'quota');
  assert.equal(agentConnectionIssue('余额不足').kind, 'quota');
  assert.equal(agentConnectionIssue(new Error('llm-deepseek: no API key for provider route "deepseek-official"')).kind, 'credentials');
  for (const error of ['429 Too many requests', 'rate limit exceeded', 'not signed in', 'This is a desktop app', 'API key rejected', '', null]) {
    assert.equal(agentConnectionIssue(error), null, String(error));
  }
});
