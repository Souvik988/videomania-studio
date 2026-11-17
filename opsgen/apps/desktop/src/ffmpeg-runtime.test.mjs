import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fetchFfmpeg, ffmpegIn, unzipEntry } from './ffmpeg-runtime.mjs';
import { zipFiles } from '../../../packages/openfilm/studio/server/zip.mjs';

/** A response whose body comes in one piece. */
const answer = (bytes) => new Response(new ReadableStream({ start(c) { c.enqueue(bytes); c.close(); } }), { headers: { 'content-length': String(bytes.length) } });

test('a build whose checksum is not the pinned one is not kept', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'of-ffmpeg-'));
  const fetch = async () => answer(Buffer.from('not ffmpeg'));
  await assert.rejects(fetchFfmpeg(dir, { platform: 'darwin', arch: 'arm64', fetch }), /did not match its checksum/);
  assert.equal(ffmpegIn(dir, 'darwin'), false);
});

test('no build for a platform says so', async () => {
  await assert.rejects(fetchFfmpeg(mkdtempSync(join(tmpdir(), 'of-ffmpeg-')), { platform: 'linux', arch: 'x64' }), /no ffmpeg to download for linux-x64/);
});

test('a download that fails is tried again, three times in all', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'of-ffmpeg-'));
  const asked = [];
  const fetch = async (url) => { asked.push(url.split('/').pop()); throw new TypeError('fetch failed'); };
  await assert.rejects(fetchFfmpeg(dir, { platform: 'win32', arch: 'x64', fetch }), /fetch failed/);
  assert.deepEqual(asked.filter((n) => n === 'ffmpeg-9.0.2-essentials_build.zip').length, 3, 'one archive, both programs in it');
});

test('a download that stops coming is stopped and tried again', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'of-ffmpeg-'));
  let tries = 0;
  const fetch = async (url, { signal }) => {
    if (url.endsWith('ffmpeg-osx-x64')) tries++;
    /* fetch ends a body whose request is aborted with an error */
    return new Response(new ReadableStream({ start(c) { signal.addEventListener('abort', () => c.error(new DOMException('aborted', 'AbortError'))); } }));
  };
  await assert.rejects(fetchFfmpeg(dir, { platform: 'darwin', arch: 'x64', fetch, stallMs: 50 }), /stalled/);
  assert.equal(tries, 3);
});

test('the installer\'s copy has FFmpeg\'s license and where its source is', async () => {
  /* the programs themselves are the pinned builds: a stand-in with the pinned checksum is not to be had, so this
     checks the license files only, with the programs already there */
  const dir = mkdtempSync(join(tmpdir(), 'of-ffmpeg-'));
  writeFileSync(join(dir, 'ffmpeg'), '');
  writeFileSync(join(dir, 'ffprobe'), '');
  const asked = [];
  const fetch = async (url) => { asked.push(url); return answer(Buffer.from('GPL v3 text')); };
  await fetchFfmpeg(dir, { platform: 'darwin', arch: 'arm64', license: true, fetch });
  assert.deepEqual(asked, ['https://raw.githubusercontent.com/FFmpeg/FFmpeg/n8.1.2/COPYING.GPLv3'], 'the license of the version it is, nothing else');
  assert.equal(readFileSync(join(dir, 'LICENSE'), 'utf8'), 'GPL v3 text');
  assert.match(readFileSync(join(dir, 'SOURCE'), 'utf8'), /^FFmpeg 8\.1\.2,[^]*ffmpeg-8\.1\.2\.tar\.xz/);
});

test('a program comes out of a zip as it went in', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'of-ffmpeg-'));
  const program = Buffer.from('MZ'.repeat(5000));
  await zipFiles(join(dir, 'build.zip'), [{ name: 'build/LICENSE', data: Buffer.from('license') }, { name: 'build/bin/ffmpeg.exe', data: program }]);
  const zip = readFileSync(join(dir, 'build.zip'));
  assert.deepEqual(unzipEntry(zip, 'build/bin/ffmpeg.exe'), program);
  assert.equal(unzipEntry(zip, 'build/LICENSE').toString(), 'license');
  assert.throws(() => unzipEntry(zip, 'build/bin/ffprobe.exe'), /has no build\/bin\/ffprobe\.exe/);
  assert.throws(() => unzipEntry(Buffer.from('not a zip'), 'x'), /not a zip/);
});
