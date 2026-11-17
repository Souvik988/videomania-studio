import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright-core';
import shellConfig from '../shell/vite.config.ts';

test('agent menus fetch efforts for the picked model, retain Default, and ignore an outdated probe', { timeout: 60_000 }, async () => {
  const server = await createServer({
    ...shellConfig, configFile: false, root: fileURLToPath(new URL('..', import.meta.url)),
    server: { host: '127.0.0.1', port: 0 }, logLevel: 'error',
    plugins: [...shellConfig.plugins, {
      name: 'model-options-fixture',
      configureServer(app) {
        app.middlewares.use('/model-options', (_req, res, next) => {
          res.setHeader('content-type', 'text/html');
          void app.transformIndexHtml('/model-options', '<!doctype html><html><body><div id="root"></div><script type="module" src="/bench/model-options.tsx"></script></body></html>')
            .then((html) => res.end(html), next);
        });
      },
    }],
  });
  let browser;
  try {
    await server.listen();
    browser = await chromium.launch({ headless: true });
    for (const agent of ['opencode', 'cursor', 'copilot']) {
      const page = await browser.newPage({ viewport: { width: 900, height: 650 }, reducedMotion: 'reduce' });
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.message));
      await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/model-options?agent=${agent}`);
      await page.waitForFunction(() => window.modelOptionsFixture?.state().options?.length);
      await page.locator('[data-model-picker] button').first().click();
      await page.locator('[data-agent-option="model"]').hover();
      await page.getByRole('button', { name: 'Reasoning model', exact: true }).click();
      await page.waitForFunction(() => window.modelOptionsFixture.state().options.some((o) => o.category === 'thought_level'));
      assert.equal(await page.evaluate(() => window.modelOptionsFixture.calls.at(-1)), 'reasoning', 'the probe receives the model the user picked');
      const effortId = await page.evaluate(() => window.modelOptionsFixture.effortId);
      await page.locator(`[data-agent-option="${effortId}"]`).hover();
      for (const choice of ['Default', 'Low', 'High', 'Max']) assert.equal(await page.getByRole('button', { name: choice, exact: true }).isVisible(), true);
      await page.getByRole('button', { name: 'High', exact: true }).click();
      assert.equal(await page.evaluate(() => {
        const fixture = window.modelOptionsFixture;
        return fixture.state().prefs[fixture.effortId];
      }), 'high');
      await page.evaluate(() => window.modelOptionsFixture.send());
      assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.sent), [['model', 'reasoning'], [effortId, 'high'], ['prompt']], 'the selected model is applied before its effort and before sending');
      if (agent === 'cursor') {
        await page.evaluate(() => window.modelOptionsFixture.desync());
        await page.evaluate(() => window.modelOptionsFixture.send());
        assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.sent), [['model', 'reasoning'], [effortId, 'high'], ['prompt']], 'Cursor reasserts the model when the actual session no longer matches its cached state');
      }
      await page.evaluate(() => window.modelOptionsFixture.publish());
      await page.getByRole('button', { name: 'Extra high', exact: true }).waitFor({ state: 'visible' });
      await page.getByRole('button', { name: 'Default', exact: true }).click();
      assert.equal(await page.evaluate(() => {
        const fixture = window.modelOptionsFixture;
        return fixture.state().prefs[fixture.effortId];
      }), 'default', 'Default is sent to the agent to reset a previous effort');
      await page.evaluate(() => window.modelOptionsFixture.send());
      assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.sent), [...(agent === 'cursor' ? [['model', 'reasoning']] : []), [effortId, 'default'], ['prompt']], 'Default resets the effort on an existing conversation');
      await page.locator('[data-agent-option="fast"]').hover();
      await page.getByRole('button', { name: 'Fast', exact: true }).click();
      assert.equal(await page.evaluate(() => window.modelOptionsFixture.state().prefs.fast), 'true');
      await page.locator('[data-agent-option="model"]').hover();
      await page.getByRole('button', { name: 'Auto', exact: true }).click();
      assert.equal(await page.locator('[data-agent-option="fast"]').count(), 0, 'the old speed selector is hidden immediately on a model switch');
      await page.waitForFunction(() => window.modelOptionsFixture.state().options.find((o) => o.category === 'model')?.currentValue === 'default');
      assert.equal(await page.evaluate(() => window.modelOptionsFixture.state().prefs.model), 'default', 'Cursor Auto remains a valid native model selection');
      assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.state().rawPrefs), { model: 'default' }, 'Auto does not inherit speed, context or effort from the previous model');
      assert.equal(await page.evaluate(() => window.modelOptionsFixture.state().summary.effort), null, 'Auto is not mislabeled with a stale High effort');
      if (agent === 'cursor') {
        await page.locator('[data-agent-option="model"]').hover();
        await page.getByRole('button', { name: 'Grok 4.7', exact: true }).click();
        await page.waitForFunction(() => window.modelOptionsFixture.state().options.find((o) => o.category === 'model')?.currentValue === 'grok');
        assert.equal(await page.locator('[data-agent-option="reasoning"]').count(), 0, 'the GPT reasoning parameter does not carry into Grok');
        await page.locator('[data-agent-option="reasoning_effort"]').hover();
        await page.getByRole('button', { name: 'Medium', exact: true }).click();
        await page.evaluate(() => window.modelOptionsFixture.send());
        assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.sent), [['model', 'grok'], ['reasoning_effort', 'medium'], ['prompt']], 'Grok receives its own effort id and no stale parameters');
      }
      await page.evaluate(() => {
        window.modelOptionsFixture.model('reasoning');
        window.modelOptionsFixture.model('plain');
      });
      await page.waitForFunction(() => window.modelOptionsFixture.state().options.find((o) => o.category === 'model')?.currentValue === 'plain');
      assert.equal(await page.evaluate(() => window.modelOptionsFixture.state().options.some((o) => o.category === 'thought_level')), false, 'a model with no variants does not retain the old effort list');
      assert.equal(await page.locator('[data-agent-option="fast"]').count(), 0, 'a model without a speed parameter has no speed row');
      await page.evaluate(() => window.modelOptionsFixture.stale());
      assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.state().prefs), { model: 'plain' }, 'unsupported settings from older saved preferences are excluded');
      await page.evaluate(() => window.modelOptionsFixture.send());
      assert.deepEqual(await page.evaluate(() => window.modelOptionsFixture.sent), [['model', 'plain'], ['prompt']], 'a model without parameters is sent no stale speed, effort or context');
      assert.deepEqual(errors, []);
      await page.close();
    }
    const page = await browser.newPage();
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/model-options?agent=cursor&legacy=1`);
    await page.waitForFunction(() => window.modelOptionsFixture?.state().options?.some((o) => o.category === 'thought_level'));
    assert.equal(await page.evaluate(() => window.modelOptionsFixture.state().prefs.model), 'reasoning');
    assert.equal(await page.evaluate(() => window.modelOptionsFixture.state().prefs.reasoning), 'high', 'the old Cursor model selection retains its embedded effort');
    await page.close();
  } finally {
    await browser?.close();
    await server.close();
  }
});
