/** Measure the real menus at window edges, including options that arrive while the submenu is open. */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright-core';
import shellConfig from '../shell/vite.config.ts';

test('agent submenus stay inside the viewport as options and window dimensions change', { timeout: 60_000 }, async () => {
  const server = await createServer({
    ...shellConfig, configFile: false, root: fileURLToPath(new URL('..', import.meta.url)),
    server: { host: '127.0.0.1', port: 0 }, logLevel: 'error',
    plugins: [...shellConfig.plugins, {
      name: 'model-popover-layout-fixture',
      configureServer(app) {
        app.middlewares.use('/model-popover-layout', (_req, res, next) => {
          res.setHeader('content-type', 'text/html');
          void app.transformIndexHtml('/model-popover-layout', '<!doctype html><html><body><div id="root"></div><script type="module" src="/bench/model-popover-layout.tsx"></script></body></html>')
            .then((html) => res.end(html), next);
        });
      },
    }],
  });
  let browser;
  try {
    await server.listen();
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 900, height: 650 }, reducedMotion: 'reduce' });
    page.setDefaultTimeout(5000);
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/model-popover-layout`);
    await page.locator('[data-model-picker] button').first().click();
    const effort = page.locator('[data-agent-option="effort"]');
    const side = page.getByRole('button', { name: 'Low', exact: true }).locator('..');
    const settle = () => page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
    const assertInside = async (message) => {
      await settle();
      const rect = await side.boundingBox();
      const { width, height } = page.viewportSize();
      assert.ok(rect.x >= 7 && rect.y >= 7 && rect.x + rect.width <= width - 7 && rect.y + rect.height <= height - 7,
        `${message}: ${JSON.stringify(rect)} in ${width} × ${height}`);
      const card = await effort.locator('..').boundingBox();
      assert.ok(rect.x >= card.x + card.width + 1, 'the submenu stays beside its parent card');
    };
    await settle();
    await effort.hover();
    await assertInside('initial menu near the bottom and right edges');
    await page.evaluate(() => window.modelPopoverFixture.grow(3));
    await assertInside('an open effort menu grows when new options arrive');
    await page.setViewportSize({ width: 900, height: 360 });
    await assertInside('only the viewport height shrinks');
    await page.evaluate(() => window.modelPopoverFixture.grow(30));
    await assertInside('a tall menu scrolls within the viewport');
    assert.equal(await side.evaluate((el) => el.scrollHeight > el.clientHeight), true);
    await page.getByRole('button', { name: 'Extra effort 30', exact: true }).click();
    assert.equal(await effort.getAttribute('aria-expanded'), 'true', 'the last choice remains selectable');
    await page.setViewportSize({ width: 340, height: 360 });
    await assertInside('narrow window after choosing the last effort');
    await page.locator('[data-agent-option="model"]').hover();
    const modelMenu = page.getByRole('button', { name: 'A model with a much longer display name', exact: true }).locator('..');
    await settle();
    const modelRect = await modelMenu.boundingBox();
    assert.ok(modelRect.x >= 7 && modelRect.x + modelRect.width <= 333, 'long model labels also stay within a narrow window');
    assert.deepEqual(errors, []);
  } finally {
    await browser?.close();
    await server.close();
  }
});
