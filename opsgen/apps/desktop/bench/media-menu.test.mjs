/** Media-pane context menus in an isolated app; file pickers are cancelled without touching personal media. */
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { _electron as electron } from 'playwright-core';
import { filmHtml } from 'opsgen/film-doc';
import { DESKTOP, buildShell, prepare } from './app.mjs';
import { launcherEnvironment, loginShellEnvironment } from '../src/environment.mjs';

buildShell();
const dir = join(DESKTOP, '.dev', `media-menu-${Date.now()}`);
prepare(dir);
const film = join(dir, 'projects', 'empty');
mkdirSync(film);
writeFileSync(join(film, 'film.html'), filmHtml({ stage: { w: 1920, h: 1080 }, tracks: [] }));
const { PATH } = await loginShellEnvironment();
const app = await electron.launch({
  executablePath: createRequire(import.meta.url)('electron'), args: [DESKTOP], cwd: DESKTOP,
  env: { ...launcherEnvironment(process.env, PATH), OPSGEN_DESKTOP_FLAVOR: 'bench', OPSGEN_BENCH_DIR: dir },
});
let page;
try {
  for (let attempt = 0; attempt < 100; attempt++) {
    page = app.context().pages().find((p) => p.url().startsWith('http://127.0.0.1:'));
    if (page) break;
    await new Promise((done) => setTimeout(done, 100));
  }
  assert.ok(page);
  const run = JSON.parse(readFileSync(join(dir, 'home/run.json'), 'utf8'));
  const response = await fetch(`${run.origin}/api/open`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-studio-key': run.key },
    body: JSON.stringify({ path: film, fallback: 0 }),
  });
  assert.equal(response.status, 200);
  for (let attempt = 0; attempt < 100; attempt++) {
    const candidate = app.context().pages().find((p) => p.url().includes('/projects/'));
    if (candidate) { page = candidate; break; }
    await new Promise((done) => setTimeout(done, 100));
  }
  await page.waitForSelector('[data-prompt-editor]');
  await page.evaluate(() => localStorage.setItem('openfilm.language', 'zh-CN'));
  await page.reload({ waitUntil: 'domcontentloaded' });
  const errors = [], filePicks = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/api/pick-files', async (route) => {
    filePicks.push(route.request().postDataJSON());
    await route.fulfill({ json: { paths: [] } });
  });
  await app.evaluate(({ dialog }) => {
    globalThis.mediaMenuFolderPicks = [];
    dialog.showOpenDialog = async (_window, options) => {
      globalThis.mediaMenuFolderPicks.push(options);
      return { canceled: true, filePaths: [] };
    };
  });
  const menu = page.getByRole('menu');
  const blankItems = ['新建文件夹', '导入媒体', '链接文件…', '链接文件夹…'];
  const expectBlank = async (target, options = {}) => {
    await target.click({ button: 'right', ...options });
    await menu.waitFor({ timeout: 2000 });
    assert.deepEqual(await menu.getByRole('menuitem').allTextContents(), blankItems);
  };
  const closeMenu = async () => {
    await page.locator('[data-prompt-editor]').click();
    await menu.waitFor({ state: 'hidden' });
  };
  const empty = page.getByText('还没有媒体', { exact: true });
  await page.getByRole('button', { name: '素材', exact: true }).click();
  await empty.waitFor();
  const placeholder = empty.locator('..');
  // Both the full-size placeholder and its nested text/icon must behave like blank space.
  for (const target of [placeholder, empty, placeholder.locator('p'), placeholder.locator('svg').first()]) {
    await expectBlank(target, target === placeholder ? { position: { x: 10, y: 10 } } : {});
    await closeMenu();
  }
  await expectBlank(empty);
  await page.screenshot({ path: join(dir, 'empty-menu.png'), animations: 'disabled' });
  const filePick = page.waitForResponse('**/api/pick-files');
  await menu.getByRole('menuitem', { name: '链接文件…', exact: true }).click();
  await filePick;
  assert.deepEqual(filePicks, [{ title: '选择要链接的文件' }]);
  await empty.waitFor();
  await expectBlank(empty);
  await menu.getByRole('menuitem', { name: '链接文件夹…', exact: true }).click();
  for (let attempt = 0; attempt < 100 && !(await app.evaluate(() => globalThis.mediaMenuFolderPicks.length)); attempt++) {
    await new Promise((done) => setTimeout(done, 20));
  }
  const picks = await app.evaluate(() => globalThis.mediaMenuFolderPicks);
  assert.equal(picks.length, 1);
  assert.equal(picks[0].title, '选择要链接的文件夹');
  assert.ok(picks[0].properties.includes('openDirectory'));
  await empty.waitFor();
  await expectBlank(empty);
  await menu.getByRole('menuitem', { name: '新建文件夹', exact: true }).click();
  const name = page.locator('[data-media-new-folder] input');
  await name.fill('Empty folder');
  assert.equal(await name.evaluate((input) => {
    const event = new MouseEvent('contextmenu', { bubbles: true, cancelable: true });
    input.dispatchEvent(event);
    return event.defaultPrevented;
  }), false, 'naming a folder keeps the native input context menu');
  assert.equal(await menu.count(), 0);
  await name.press('Enter');
  const folder = page.locator('[data-media-folder][data-media-key="assets/Empty folder"]');
  await folder.waitFor();
  await folder.click({ button: 'right' });
  await menu.getByRole('menuitem', { name: '重命名', exact: true }).waitFor();
  assert.equal(await menu.getByRole('menuitem', { name: '链接文件…', exact: true }).count(), 0);
  await closeMenu();
  writeFileSync(join(film, 'assets', 'note.txt'), 'Media menu fixture');
  const file = page.locator('[data-media-path="assets/note.txt"]');
  await file.waitFor();
  await file.click({ button: 'right' });
  await menu.getByRole('menuitem', { name: '重命名', exact: true }).waitFor();
  assert.equal(await menu.getByRole('menuitem', { name: '新建文件夹', exact: true }).count(), 0);
  await closeMenu();
  await expectBlank(folder.locator('..').locator('..'), { position: { x: 8, y: 180 } });
  await closeMenu();
  await page.getByRole('button', { name: '列表显示', exact: true }).click();
  await expectBlank(folder.locator('..').getByText('名称', { exact: true }));
  await closeMenu();
  await page.getByRole('button', { name: '网格显示', exact: true }).click();
  await folder.dblclick();
  await expectBlank(page.getByText('此文件夹为空', { exact: true }));
  await closeMenu();
  const search = page.getByPlaceholder('搜索', { exact: true });
  if (!(await search.count())) await page.getByRole('button', { name: '搜索媒体', exact: true }).click();
  await search.fill('missing-file');
  await expectBlank(page.getByText('没有符合搜索条件的内容。', { exact: true }));
  await closeMenu();
  await search.fill('');
  await page.getByText('此文件夹为空', { exact: true }).waitFor();
  await page.getByRole('button', { name: '收藏', exact: true }).click();
  await page.getByText('收藏里还没有东西', { exact: true }).click({ button: 'right' });
  await menu.waitFor();
  assert.deepEqual(await menu.getByRole('menuitem').allTextContents(), blankItems.slice(0, 2));
  await closeMenu();
  assert.deepEqual(errors, []);
  console.log('Media menus passed: empty background/text/icon, file and folder pickers, new-folder input, file/folder menus, populated background, list header, empty folder, no search results and Saved without link actions.');
  console.log(`Media menu artifacts: ${dir}`);
} catch (error) {
  if (page && !page.isClosed()) await page.screenshot({ path: join(dir, 'failed.png') }).catch(() => {});
  console.error(`Media menu artifacts: ${dir}`);
  throw error;
} finally {
  await app.close();
}
