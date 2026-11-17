import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import vm from 'node:vm';
import { registerSkillsIpc } from './skills-ipc.mjs';
import { readSkill } from 'opsgen/skills';

test('the preload carries a chosen cover through preview and commit into the installed skill', async (t) => {
  const root = mkdtempSync(join(tmpdir(), 'of-skill-ipc-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const source = join(root, 'source');
  const mine = join(root, 'mine');
  mkdirSync(source);
  writeFileSync(join(source, 'SKILL.md'), '---\nname: picture\ndescription: A picture\n---\nSteps.');
  const handlers = new Map();
  registerSkillsIpc({ handle: (channel, fn) => handlers.set(channel, fn) }, {
    trusted: () => true, projects: async () => [], dataDir: join(root, 'data'), mine,
    reveal() {}, pickFolder: async () => source, refreshSkills() {}, log() {},
  });
  let native;
  vm.runInNewContext(readFileSync(new URL('./preload.cjs', import.meta.url), 'utf8'), {
    process: { platform: process.platform },
    require: () => ({
      contextBridge: { exposeInMainWorld: (_key, value) => { native = value; } },
      ipcRenderer: { invoke: (channel, opts) => handlers.get(channel)({}, opts) },
    }),
  });
  const preview = await native.skills.previewFolder(null);
  assert.equal(preview.ok, true);
  const cover = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
  const result = await native.skills.commit(preview.id, { picture: cover });
  assert.equal(result.ok, true);
  const installed = readSkill(join(mine, 'picture'), 'mine');
  assert.ok(installed.cover);
  assert.deepEqual(readFileSync(join(installed.folder, installed.cover)), Buffer.from(cover.split(',')[1], 'base64'));
});
