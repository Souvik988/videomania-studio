/** Conversation options through the real menu and send path, with agent IPC kept inside an isolated fixture. */
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { _electron as electron } from 'playwright-core';
import { filmHtml } from 'opsgen/film-doc';
import { DESKTOP, buildShell, prepare } from './app.mjs';
import { loadChat, saveSessions } from '../src/chat-store.mjs';
import { launcherEnvironment, loginShellEnvironment } from '../src/environment.mjs';

buildShell();
const dir = join(DESKTOP, '.dev', `conversation-agent-${Date.now()}`);
prepare(dir);
const film = join(dir, 'projects', 'conversation');
mkdirSync(film);
writeFileSync(join(film, 'film.html'), filmHtml({ stage: { w: 1920, h: 1080 }, tracks: [] }));
const now = new Date().toISOString();
saveSessions(film, { last: 'saved', sessions: [{
  id: 'saved', title: 'Saved conversation', turns: 1, createdAt: now, updatedAt: now,
  agent: 'byok', agentPrefs: { byok: { model: 'model-x', effort: 'high' } },
}] });

const { PATH } = await loginShellEnvironment();
const app = await electron.launch({
  executablePath: createRequire(import.meta.url)('electron'), args: [DESKTOP], cwd: DESKTOP,
  env: { ...launcherEnvironment(process.env, PATH), OPSGEN_DESKTOP_FLAVOR: 'bench', OPSGEN_BENCH_DIR: dir },
});
let page;
try {
  const findPage = async (matches) => {
    for (let attempt = 0; attempt < 300; attempt++) {
      const found = app.context().pages().find((p) => matches(p.url()));
      if (found) return found;
      await new Promise((done) => setTimeout(done, 100));
    }
    throw new Error('The desktop page did not open.');
  };
  await findPage((url) => url.startsWith('http://127.0.0.1:'));
  // Only the agent boundary is replaced: the menu, conversation loading/saving and send path are real.
  await app.evaluate(({ ipcMain }) => {
    const models = [
      { id: 'model-x', name: 'Model X', model: 'x', levels: ['low', 'high'], effort: 'low' },
      { id: 'model-y', name: 'Model Y', model: 'y', levels: ['low', 'medium'], effort: 'medium' },
    ].map((m) => ({ ...m, format: 'responses', baseUrl: 'http://127.0.0.1:1/v1', last4: 'test' }));
    const options = [
      { id: 'model', name: 'Model', category: 'model', type: 'select', currentValue: 'model-x', options: models.map((m) => ({ value: m.id, name: m.name })) },
      { id: 'effort', name: 'Effort', category: 'thought_level', type: 'select', currentValue: 'low', options: [{ value: 'low', name: 'Low' }, { value: 'high', name: 'High' }] },
    ];
    const info = () => ({ sessionId: 'fixture', configOptions: options, authMethods: [], mcp: false });
    const handle = (channel, fn) => { ipcMain.removeHandler(channel); ipcMain.handle(channel, fn); };
    handle('desktop:agents:list', () => [{ id: 'byok', name: 'Own key', shown: true, status: 'ready', byok: { models } }]);
    handle('desktop:local-agents:probe', () => ({ ok: true, info: info() }));
    handle('desktop:local-agents:start', () => ({ ok: true, key: 'fixture', info: info() }));
    handle('desktop:local-agents:set-option', (_event, { configId, value }) => {
      const option = options.find((o) => o.id === configId);
      assertOption(option, value);
      option.currentValue = value;
      return { ok: true, result: { configOptions: options } };
    });
    function assertOption(option, value) {
      if (!option?.options.some((o) => o.value === value)) throw new Error(`Invalid fixture option: ${value}`);
    }
    handle('desktop:local-agents:prompt', (event) => {
      globalThis.conversationAgentSent = Object.fromEntries(options.map((o) => [o.id, o.currentValue]));
      event.sender.send('desktop:local-agents:event', { key: 'fixture', kind: 'update', update: { sessionUpdate: 'agent_message_chunk', content: { type: 'text', text: 'Fixture answer.' } } });
      return { ok: true, stopReason: 'end_turn' };
    });
  });
  await app.context().addInitScript(() => {
    localStorage.setItem('openfilm.language', 'en');
    localStorage.setItem('openfilm.local-agents.v2', JSON.stringify({ picked: 'byok', prefs: { byok: { model: 'model-y', effort: 'medium' } }, options: {} }));
  });
  const run = JSON.parse(readFileSync(join(dir, 'home/run.json'), 'utf8'));
  const response = await fetch(`${run.origin}/api/open`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-studio-key': run.key },
    body: JSON.stringify({ path: film, fallback: 0 }),
  });
  assert.equal(response.status, 200);
  page = await findPage((url) => url.includes('/projects/'));
  await page.waitForSelector('[data-prompt-editor]');
  // Reload after Playwright has attached so the stored global choice precedes the chat's hydration.
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('[data-prompt-editor]');
  const model = page.getByRole('button', { name: /^Model X/ });
  await model.waitFor();
  assert.match(await model.innerText(), /High/, 'the menu keeps Model X\'s High effort when the global Model Y only offers Low and Medium');
  await page.locator('[data-prompt-editor]').fill('Check the saved effort.');
  await page.locator('[data-prompt-editor]').press('Enter');
  await page.getByText('Fixture answer.', { exact: true }).waitFor();
  assert.deepEqual(await app.evaluate(() => globalThis.conversationAgentSent), { model: 'model-x', effort: 'high' }, 'the next message uses the conversation\'s model and effort');
  await page.waitForFunction(async (project) => {
    const { sessions } = await window.openfilmNative.chat.load(project);
    return sessions.find((s) => s.id === 'saved')?.turns === 2;
  }, film);
  assert.deepEqual(loadChat(film).sessions.find((s) => s.id === 'saved').agentPrefs.byok, { model: 'model-x', effort: 'high' }, 'sending preserves the saved effort');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: /^Model X.*High/ }).waitFor();
  console.log('Conversation agent passed: menu, sent options, saved preferences and reload retain Model X / High despite global Model Y / Medium.');
} catch (error) {
  if (page && !page.isClosed()) await page.screenshot({ path: join(dir, 'failed.png') }).catch(() => {});
  console.error(`Conversation agent artifacts: ${dir}`);
  throw error;
} finally {
  await app.close();
}
