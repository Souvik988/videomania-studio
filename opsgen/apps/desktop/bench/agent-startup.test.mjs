import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright-core';
import shellConfig from '../shell/vite.config.ts';

test('selected model loads before background discovery, ignores an older roster and refreshes after configuration changes', { timeout: 60_000 }, async () => {
  const server = await createServer({
    ...shellConfig, configFile: false, root: fileURLToPath(new URL('..', import.meta.url)), server: { host: '127.0.0.1', port: 0 }, logLevel: 'error',
    plugins: [...shellConfig.plugins, { name: 'agent-startup-fixture', configureServer(app) {
      app.middlewares.use('/agent-startup-ui', (_req, res, next) => {
        res.setHeader('content-type', 'text/html');
        void app.transformIndexHtml('/agent-startup-ui', '<!doctype html><html><body><div id="root"></div><script type="module" src="/bench/agent-startup.tsx"></script></body></html>').then((html) => res.end(html), next);
      });
    } }],
  });
  let browser;
  try {
    await server.listen();
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1000, height: 650 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/agent-startup-ui`);
    await page.waitForFunction(() => window.agentStartupFixture && window.agentStartupFixture.state() === null);
    await page.evaluate(() => window.agentStartupFixture.checking());
    assert.deepEqual(await page.evaluate(() => window.agentStartupFixture.calls), [], 'the saved selection is kept while it is checking, instead of probing a different ready agent');
    await page.evaluate(() => window.agentStartupFixture.ready());
    await page.getByRole('button', { name: 'Codex Ready Model', exact: true }).waitFor();
    assert.deepEqual(await page.evaluate(() => window.agentStartupFixture.calls), ['codex']);
    assert.equal(await page.evaluate(() => window.agentStartupFixture.state().find((a) => a.id === 'cursor').status), 'checking');
    await page.evaluate(() => window.agentStartupFixture.release());
    await page.waitForTimeout(30);
    assert.equal(await page.evaluate(() => window.agentStartupFixture.state().find((a) => a.id === 'codex').status), 'ready', 'an old checking snapshot cannot replace a newer ready update');
    await page.locator('[data-model-picker] button').first().click();
    assert.deepEqual(await page.evaluate(() => window.agentStartupFixture.calls), ['codex'], 'opening the menu does not prefetch other agents');
    await page.getByRole('button', { name: 'OpenCode', exact: true }).click();
    await page.getByRole('button', { name: 'OpenCode Ready Model', exact: true }).waitFor();
    assert.deepEqual(await page.evaluate(() => window.agentStartupFixture.calls), ['codex', 'opencode']);
    await page.evaluate(() => window.agentStartupFixture.refresh());
    await page.getByRole('button', { name: 'OpenCode Updated Model', exact: true }).waitFor();
    assert.deepEqual(await page.evaluate(() => window.agentStartupFixture.calls), ['codex', 'opencode', 'opencode']);
    assert.deepEqual(errors, []);
  } finally { await browser?.close(); await server.close(); }
});
