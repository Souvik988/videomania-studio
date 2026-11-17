import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import fsPromises from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { filmHtml, readFilmFile } from '../../src/film-doc.mjs';
import { filmCaptions } from './captions.mjs';
import { FileError, moveFile } from './files.mjs';
import { CUT_NOTE, transcriptPath } from './transcripts.mjs';

const MEDIA = Buffer.from('the original media bytes');
const ORIGINAL = Buffer.from(`\ufeffWEBVTT\r\n\r\nNOTE Keep this production note exactly.\r\n\r\n${CUT_NOTE}\r\n\r\ncue-1\r\n00:00:00.125 --> 00:00:01.875 align:start\r\n<v Ann><00:00:00.125>Hello <00:00:00.875>world.\r\n`);
const FRENCH = Buffer.from('WEBVTT\n\nNOTE French translation.\n\n00:00:00.125 --> 00:00:01.875\nBonjour le monde.\n');
const CHINESE = Buffer.from('WEBVTT\r\n\r\n00:00:00.125 --> 00:00:01.875\r\n你好，世界。\r\n');
const TRANSCRIPTS = [['', ORIGINAL], ['fr', FRENCH], ['zh-CN', CHINESE]];

function put(root, rel, bytes) {
  mkdirSync(dirname(join(root, rel)), { recursive: true });
  writeFileSync(join(root, rel), bytes);
}

function project(t, sources = ['assets/voice.wav']) {
  const root = mkdtempSync(join(tmpdir(), 'of-files-transcripts-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const src of sources) put(root, src, MEDIA);
  put(root, 'film.html', filmHtml({ stage: { w: 320, h: 180 }, tracks: [{
    clips: sources.map((src, index) => ({ id: `clip-${index}`, src, at: index * 3, time: [0, 2] })),
  }] }));
  return root;
}

function putTranscripts(root, src) {
  for (const [language, bytes] of TRANSCRIPTS) put(root, transcriptPath(src, language || undefined), bytes);
}

function assertTranscripts(root, src, present = true) {
  for (const [language, bytes] of TRANSCRIPTS) {
    const path = join(root, transcriptPath(src, language || undefined));
    if (present) assert.deepEqual(readFileSync(path), bytes, path);
    else assert.equal(existsSync(path), false, path);
  }
}

function filmSources(root) {
  return readFilmFile(readFileSync(join(root, 'film.html'), 'utf8')).value.tracks.flatMap((track) => track.clips.map((clip) => clip.src));
}

async function captions(root) {
  const value = await filmCaptions(root, { duration: async () => 2 });
  return { ...value, cues: value.cues.map(({ src, ...cue }) => cue) };
}

for (const [from, to] of [
  ['assets/voice.wav', 'assets/narration.wav'],
  ['assets/voice.mp4', 'assets/cuts/interview.mp4'],
]) {
  test(`${from} → ${to} preserves raw transcripts and translated film captions`, async (t) => {
    const root = project(t, [from]);
    putTranscripts(root, from);
    const before = await captions(root);
    assert.equal(before.cues.length, 1);
    assert.deepEqual([...before.languages].sort(), ['fr', 'zh-CN']);
    assert.ok(before.cues[0].alt.fr && before.cues[0].alt['zh-CN']);

    assert.deepEqual(await moveFile(root, from, to), { path: to, clips: 1, pages: 0 });

    assert.equal(existsSync(join(root, from)), false);
    assert.deepEqual(readFileSync(join(root, to)), MEDIA);
    assertTranscripts(root, to);
    assertTranscripts(root, from, false);
    assert.deepEqual(filmSources(root), [to]);
    assert.deepEqual(await captions(root), before);
  });
}

test('a case-only media rename keeps canonical subtitles and translated captions', async (t) => {
  const from = 'assets/voice.wav', to = 'assets/VOICE.wav';
  const root = project(t, [from]);
  putTranscripts(root, from);
  const before = await captions(root);

  await moveFile(root, from, to);

  const names = readdirSync(join(root, 'assets'));
  for (const [language] of TRANSCRIPTS) {
    const suffix = language ? `.${language}` : '';
    assert.ok(names.includes(`VOICE${suffix}.vtt`));
    assert.equal(names.includes(`voice${suffix}.vtt`), false);
  }
  assertTranscripts(root, to);
  assert.deepEqual(readFileSync(join(root, to)), MEDIA);
  assert.deepEqual(filmSources(root), [to]);
  assert.deepEqual(await captions(root), before);
});

test('voice.mp4 and voice.m4a keep shared subtitles when one is renamed', async (t) => {
  const from = 'assets/voice.mp4', other = 'assets/voice.m4a', to = 'assets/narration.mp4';
  const root = project(t, [from, other]);
  putTranscripts(root, from);
  const before = await captions(root);
  assert.equal(before.cues.length, 2);

  await moveFile(root, from, to);

  assert.equal(existsSync(join(root, from)), false);
  assert.deepEqual(readFileSync(join(root, to)), MEDIA);
  assertTranscripts(root, from);
  assertTranscripts(root, to);
  assert.deepEqual(readFileSync(join(root, other)), MEDIA);
  assert.deepEqual(filmSources(root), [to, other]);
  assert.deepEqual(await captions(root), before);
});

test('a case-only rename of one of two media sharing subtitles keeps them for both', async (t) => {
  const from = 'assets/Voice.mp4', other = 'assets/Voice.m4a', to = 'assets/voice.mp4';
  const root = project(t, [from, other]);
  putTranscripts(root, from);

  await moveFile(root, from, to);

  assert.deepEqual(readFileSync(join(root, to)), MEDIA);
  assertTranscripts(root, to);
  assertTranscripts(root, other);
  assert.deepEqual(filmSources(root), [to, other]);
});

for (const shared of [false, true]) {
  test(`page links follow moved media and ${shared ? 'keep shared' : 'follow unique'} VTT tracks`, async (t) => {
    const from = 'assets/voice.mp4', to = 'assets/cuts/interview.mp4';
    const root = project(t, shared ? [from, 'assets/voice.m4a'] : [from]);
    putTranscripts(root, from);
    put(root, 'scenes/player.html', '<video src="../assets/voice.mp4"><track src="../assets/voice.vtt"></video>');
    const otherPage = '<audio src="../assets/voice.m4a"><track src="../assets/voice.vtt"></audio>';
    if (shared) put(root, 'scenes/other.html', otherPage);

    await moveFile(root, from, to);

    const track = shared ? '../assets/voice.vtt' : '../assets/cuts/interview.vtt';
    assert.equal(readFileSync(join(root, 'scenes/player.html'), 'utf8'), `<video src="../assets/cuts/interview.mp4"><track src="${track}"></video>`);
    if (shared) assert.equal(readFileSync(join(root, 'scenes/other.html'), 'utf8'), otherPage);
    assertTranscripts(root, to);
  });
}

for (const [language, directory] of [['', false], ['fr', true]]) {
  test(`an existing target ${language || 'base'} VTT ${directory ? 'directory' : 'file'} prevents all changes`, async (t) => {
    const from = 'assets/voice.wav', to = 'assets/cuts/narration.wav';
    const root = project(t, [from]);
    putTranscripts(root, from);
    const target = transcriptPath(to, language || undefined);
    const marker = directory ? `${target}/keep.txt` : target;
    put(root, marker, 'existing destination');
    const film = readFileSync(join(root, 'film.html'));

    await assert.rejects(moveFile(root, from, to), (error) => error instanceof FileError && error.status === 409);

    assert.deepEqual(readFileSync(join(root, from)), MEDIA);
    assert.equal(existsSync(join(root, to)), false);
    assertTranscripts(root, from);
    assert.deepEqual(readFileSync(join(root, 'film.html')), film);
    assert.equal(readFileSync(join(root, marker), 'utf8'), 'existing destination');
    for (const [other] of TRANSCRIPTS) {
      const path = transcriptPath(to, other || undefined);
      if (path !== target) assert.equal(existsSync(join(root, path)), false);
    }
  });
}

for (const shared of [false, true]) for (const failure of ['sidecar', 'media']) {
  test(`${failure} failure rolls back ${shared ? 'shared copies' : 'moved sidecars'} before changing the film`, async (t) => {
    const from = 'assets/voice.mp4', to = 'assets/edited/narration.mp4';
    const root = project(t, shared ? [from, 'assets/voice.m4a'] : [from]);
    putTranscripts(root, from);
    const film = readFileSync(join(root, 'film.html'));
    const method = failure === 'sidecar' && shared ? 'copyFile' : 'rename';
    const original = fsPromises[method];
    const denied = Object.assign(new Error('file is locked'), { code: 'EACCES' });
    let sidecars = 0, published;
    const sources = new Set(TRANSCRIPTS.map(([language]) => join(root, transcriptPath(from, language || undefined))));
    t.mock.method(fsPromises, method, async (source, destination, ...args) => {
      const fail = failure === 'media' ? source === join(root, from) : sources.has(source) && ++sidecars === 2;
      if (fail) {
        published = TRANSCRIPTS.filter(([language]) => existsSync(join(root, transcriptPath(to, language || undefined)))).length;
        throw denied;
      }
      return original(source, destination, ...args);
    });
    syncBuiltinESMExports();
    try {
      await assert.rejects(moveFile(root, from, to), (error) => error === denied);
    } finally {
      t.mock.restoreAll();
      syncBuiltinESMExports();
    }

    assert.equal(published, failure === 'sidecar' ? 1 : 3, 'failure happens after sidecars have been published');
    assert.deepEqual(readFileSync(join(root, from)), MEDIA);
    assert.equal(existsSync(join(root, to)), false);
    assertTranscripts(root, from);
    assertTranscripts(root, to, false);
    assert.deepEqual(readFileSync(join(root, 'film.html')), film);
  });
}

test('media with no source transcript can still be renamed beside an existing destination VTT', async (t) => {
  const from = 'assets/voice.wav', to = 'assets/narration.wav';
  const root = project(t, [from]);
  put(root, transcriptPath(to), ORIGINAL);

  assert.deepEqual(await moveFile(root, from, to), { path: to, clips: 1, pages: 0 });

  assert.equal(existsSync(join(root, from)), false);
  assert.deepEqual(readFileSync(join(root, to)), MEDIA);
  assert.deepEqual(readFileSync(join(root, transcriptPath(to))), ORIGINAL);
  assert.deepEqual(filmSources(root), [to]);
});

for (const folder of [false, true]) {
  test(`${folder ? 'a whole-folder move' : 'an extension-only rename'} keeps existing sidecars and captions`, async (t) => {
    const from = 'assets/voices/voice.wav', to = folder ? 'assets/edited/voice.wav' : 'assets/voices/voice.mp3';
    const root = project(t, [from]);
    putTranscripts(root, from);
    const before = await captions(root);

    await moveFile(root, folder ? 'assets/voices' : from, folder ? 'assets/edited' : to);

    assertTranscripts(root, to);
    assert.deepEqual(filmSources(root), [to]);
    assert.deepEqual(await captions(root), before);
  });
}
