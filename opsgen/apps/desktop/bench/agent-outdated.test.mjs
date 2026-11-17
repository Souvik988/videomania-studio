import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright-core';
import shellConfig from '../shell/vite.config.ts';

test('a Claude Code older than the chat was tried with says so in Settings › Agents, with the command that updates it', { timeout: 90_000 }, async () => {
  const server = await createServer({
    ...shellConfig, configFile: false, root: fileURLToPath(new URL('..', import.meta.url)),
    server: { host: '127.0.0.1', port: 0 }, logLevel: 'error',
    plugins: [...shellConfig.plugins, { name: 'agent-outdated-fixture', configureServer(app) {
      app.middlewares.use('/agent-outdated-ui', (_req, res, next) => {
        res.setHeader('content-type', 'text/html');
        void app.transformIndexHtml('/agent-outdated-ui', '<!doctype html><html><body><div id="root"></div><script type="module" src="/bench/agent-sign-in.tsx"></script></body></html>')
          .then((html) => res.end(html), next);
      });
    } }],
  });
  let browser;
  try {
    await server.listen();
    browser = await chromium.launch({ headless: true });
    for (const locale of ['en', 'zh-CN']) {
      const page = await browser.newPage({ viewport: { width: 1100, height: 700 } });
      const errors = [];
      page.on('pageerror', (error) => errors.push(error.message));
      await page.addInitScript((locale) => {
        localStorage.setItem('openfilm.language', locale);
        const agents = [
          { id: 'claude', name: 'Claude Code', shown: true, status: 'ready', path: '/usr/local/bin/claude',
            outdated: { version: '2.1.288', tested: '2.1.308', update: 'npm i -g @anthropic-ai/claude-code@latest' } },
          { id: 'codex', name: 'Codex', shown: true, status: 'ready', path: '/opt/homebrew/bin/codex' },
        ];
        window.openfilmHost = { version: 1, agents: {
          list: async () => agents, refresh: async () => agents, connect: async () => ({ ok: true }),
          disconnect: async () => {}, setShown: async () => {}, onChange: () => () => {},
        } };
      }, locale);
      await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/agent-outdated-ui`);
      const zh = locale === 'zh-CN';
      const row = (name) => page.locator('div.py-4').filter({ has: page.getByText(name, { exact: true }) });
      const said = zh ? 'Claude Code 2.1.288 比 OpsGen 测过的 2.1.308 旧' : 'Claude Code 2.1.288 is older than the 2.1.308 OpsGen was tested with';
      await row('Claude Code').getByRole('status').filter({ hasText: said }).waitFor();
      assert.equal(await row('Claude Code').getByText('npm i -g @anthropic-ai/claude-code@latest', { exact: true }).isVisible(), true, 'the command that updates it');
      assert.equal(await row('Claude Code').getByText(zh ? '已连接' : 'Connected', { exact: true }).isVisible(), true, 'an older one still works: it stays connected');
      assert.equal(await row('Codex').getByText(/2\.1\.310/).count(), 0, 'an agent that is not older says nothing');
      if (process.env.OPSGEN_OUTDATED_PREVIEW) await page.screenshot({ path: `${process.env.OPSGEN_OUTDATED_PREVIEW}-${locale}.png`, fullPage: true });
      assert.deepEqual(errors, []);
      await page.close();
    }
  } finally { await browser?.close(); await server.close(); }
});
