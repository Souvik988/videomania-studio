import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import mimo, { baseFor } from './mimo.mjs';
import { wav } from './common.mjs';

const KEY = 'sk-test_0123456789abcdef';
/** a fake Xiaomi MiMo on 127.0.0.1: `reply` answers each request; `seen` keeps them. */
let server;
let reply = () => [404, {}];
const seen = [];

before(async () => {
  server = createServer(async (req, res) => {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const call = { method: req.method, url: new URL(req.url, 'http://x'), headers: req.headers, body: Buffer.concat(chunks) };
    seen.push(call);
    const [status, body] = await reply(call);
    res.writeHead(status, { 'content-type': 'application/json' }).end(JSON.stringify(body));
  });
  await new Promise((done) => server.listen(0, '127.0.0.1', done));
  process.env.OPSGEN_MIMO_URL = `http://127.0.0.1:${server.address().port}`;
});
after(() => server.close());
beforeEach(() => { seen.length = 0; });

const ctx = (files = {}, model, key = KEY) => ({ key, model, root: '/project', signal: new AbortController().signal, say: () => {}, read: async (p) => files[p] });
const sent = (call) => JSON.parse(call.body.toString('utf8'));
const asked = (call) => sent(call).messages[0].content[0].input_audio.data;

/** Speech ffmpeg can cut: `sine` with a real pause of `gap` seconds between two stretches. */
function speechWithAPause(gap) {
  const dir = mkdtempSync(join(tmpdir(), 'mimo-cut-'));
  const file = join(dir, 'talk.wav');
  execFileSync('ffmpeg', ['-v', 'error', '-y',
    '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.8',
    '-f', 'lavfi', `-i`, `anullsrc=r=16000:cl=mono:d=${gap}`,
    '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.8',
    '-filter_complex', '[0:a][1:a][2:a]concat=n=3:v=0:a=1', '-ac', '1', '-ar', '16000', file]);
  return new Uint8Array(readFileSync(file));
}

test('transcription: MiMo-V2.5-ASR with the audio inline in a chat completion, the key as api-key', async () => {
  reply = () => [200, { choices: [{ finish_reason: 'stop', message: { content: 'Hello，大家好。' } }], usage: { seconds: 4 } }];
  const mp3 = new Uint8Array(Buffer.concat([Buffer.from('ID3'), Buffer.alloc(100)]));
  const result = await mimo.run('asr', { src: 'assets/upload/talk.mp4' }, ctx({ 'assets/upload/talk.mp4': mp3 }));
  const call = seen.at(-1);
  const body = sent(call);
  assert.equal(call.url.pathname, '/v1/chat/completions');
  assert.equal(call.headers['api-key'], KEY);
  assert.equal(body.model, 'mimo-v2.5-asr');
  assert.equal(body.messages[0].content[0].type, 'input_audio');
  assert.match(asked(call), /^data:audio\/mpeg;base64,/);
  /* nothing to cut at (the bytes are not audio ffmpeg can read): one stretch, its words over the counted seconds */
  assert.equal(seen.filter((c) => c.url.pathname === '/v1/chat/completions').length, 1);
  assert.deepEqual(result.files, [], 'the provider writes no files: runGet lands the transcript');
  assert.deepEqual(result.index, [{ src: 'assets/upload/talk.mp4', text: 'Hello，大家好。', dur: 4, transcribed: true, words: [
    { token: 'Hello，', start: 0, end: 2.4 }, { token: '大', start: 2.4, end: 2.8 }, { token: '家', start: 2.8, end: 3.2 }, { token: '好。', start: 3.2, end: 4 }] }]);
  assert.equal(result.receipt.provider, 'mimo');
  assert.equal(result.receipt.model, 'mimo-v2.5-asr');
  assert.equal(result.receipt.text, 'Hello，大家好。');
  assert.match(result.receipt.notes[0], /pauses/);
  assert.match(result.cost.note, /billed by Xiaomi MiMo/);
});

test('speech cut at its pauses: each stretch asked for on its own, its words in the time it was said', async () => {
  reply = () => (seen.filter((c) => c.url.pathname === '/v1/chat/completions').length === 1
    ? [200, { choices: [{ message: { content: '第一段。' } }], usage: { seconds: 1 } }]
    : [200, { choices: [{ message: { content: 'Second stretch.' } }], usage: { seconds: 1 } }]);
  const file = speechWithAPause(0.8);
  const result = await mimo.run('asr', { src: 'assets/talk.wav' }, ctx({ 'assets/talk.wav': file }));
  const mine = seen.filter((c) => c.url.pathname === '/v1/chat/completions');
  assert.equal(mine.length, 2, 'two stretches, one request each');
  assert.match(asked(mine[0]), /^data:audio\/mpeg;base64,/);
  assert.notEqual(asked(mine[0]), asked(mine[1]), 'each stretch its own audio');
  /* 0.8 s speech, 0.8 s pause, 0.8 s speech: the cut is the pause's middle, at 1.2 s */
  assert.equal(result.index[0].dur, 2.4);
  assert.equal(result.index[0].text, '第一段。 Second stretch.');
  const words = result.index[0].words;
  assert.deepEqual(words.map((w) => w.token), ['第', '一', '段。', 'Second', 'stretch.']);
  assert.equal(words[0].start, 0);
  assert.ok(words[2].end <= 1.21 && words[2].end >= 1.19, `the first stretch's last word ends at the pause (${words[2].end})`);
  assert.ok(words[3].start >= 1.19 && words[3].start <= 1.21, `the second stretch starts at the pause (${words[3].start})`);
  assert.ok(words.at(-1).end <= 2.41, 'words never past the file');
});

test('the model chosen in Settings is the one asked for', async () => {
  reply = () => [200, { choices: [{ message: { content: 'Two.' } }], usage: { seconds: 1 } }];
  const mp3 = new Uint8Array(Buffer.concat([Buffer.from('ID3'), Buffer.alloc(10)]));
  await mimo.run('asr', { src: 'assets/talk.mp3' }, ctx({ 'assets/talk.mp3': mp3 }, 'mimo-v2.5-asr'));
  assert.equal(sent(seen.at(-1)).model, 'mimo-v2.5-asr');
});

test('speech over 100 MB is refused before anything is sent', async () => {
  const before = seen.length;
  const huge = new Uint8Array(100 * 1024 * 1024);
  await assert.rejects(mimo.run('asr', { src: 'assets/big.mp3' }, ctx({ 'assets/big.mp3': huge })), /under 100 MB.*No audio was uploaded/);
  assert.equal(seen.length, before);
});

test('the key says where it answers: a Token Plan key at its gateway, a platform key at the pay-as-you-go API', () => {
  assert.equal(baseFor('tp-test_0123456789abcdef'), 'https://token-plan-cn.xiaomimimo.com');
  assert.equal(baseFor('sk-test_0123456789abcdef'), 'https://api.xiaomimimo.com');
});

test('a Token Plan key pointed elsewhere is told where it belongs; a used-up plan is a balance', async () => {
  const mp3 = new Uint8Array(Buffer.concat([Buffer.from('ID3'), Buffer.alloc(10)]));
  const files = { 'assets/talk.mp3': mp3 };
  reply = () => [401, { error: { message: 'Invalid API Key' } }];
  await assert.rejects(mimo.run('asr', { src: 'assets/talk.mp3' }, ctx(files, undefined, 'tp-test_0123456789abcdef')),
    /Token Plan key answers at https:\/\/token-plan-cn\.xiaomimimo\.com; check OPSGEN_MIMO_URL/);
  reply = () => [429, { error: { message: 'quota exhausted' } }];
  await assert.rejects(mimo.run('asr', { src: 'assets/talk.mp3' }, ctx(files)), (e) => e.code === 'balance');
  reply = () => [401, { error: { message: 'Invalid API Key' } }];
  await assert.rejects(mimo.run('asr', { src: 'assets/talk.mp3' }, ctx(files)), /did not accept your key.*Settings/, 'a platform key that is simply wrong says only that');
});

test('a key it does not accept, an emptied account and an untranscribable answer each say so plainly', async () => {
  const mp3 = new Uint8Array(Buffer.concat([Buffer.from('ID3'), Buffer.alloc(10)]));
  const files = { 'assets/talk.mp3': mp3 };
  reply = () => [402, { error: { message: 'Insufficient account balance' } }];
  await assert.rejects(mimo.run('asr', { src: 'assets/talk.mp3' }, ctx(files)), (e) => e.code === 'balance');
  reply = () => [200, { choices: [{ message: { content: null } }] }];
  const silent = await mimo.run('asr', { src: 'assets/talk.mp3' }, ctx(files));
  assert.equal(silent.index[0].text, '', 'silence is an answer, not an error');
  assert.equal(silent.index[0].dur, undefined);
});

test('voices: the nine the API names, a limit honored; filters are said not to narrow them', async () => {
  const all = await mimo.run('voice', { limit: 100 }, ctx());
  assert.deepEqual(all.receipt.voices.map((v) => v.voiceId), ['mimo_default', '冰糖', '茉莉', '苏打', '白桦', 'Mia', 'Chloe', 'Milo', 'Dean']);
  assert.equal(all.receipt.voices[0].name, 'Default');
  assert.equal(all.receipt.voices[2].name, '茉莉');
  assert.equal(all.receipt.notes, undefined, 'asked for nothing: nothing said');
  const few = await mimo.run('voice', { limit: 2, language: 'en', gender: 'f', prompt: 'whispery' }, ctx());
  assert.deepEqual(few.receipt.voices.map((v) => v.voiceId), ['mimo_default', '冰糖']);
  assert.equal(few.receipt.notes.length, 3);
});

test('voice-over: MiMo-V2.5-TTS as a WAV in the answer, the line as the assistant\'s message', async () => {
  reply = () => [200, { choices: [{ message: { content: '', audio: { data: Buffer.from(wav(new Uint8Array(48000), 24000)).toString('base64') } } }] }];
  const result = await mimo.run('tts', { out: 'line', text: 'Hello there.', voice: 'Chloe' }, ctx());
  const body = sent(seen.at(-1));
  assert.equal(seen.at(-1).url.pathname, '/v1/chat/completions');
  assert.equal(seen.at(-1).headers['api-key'], KEY);
  assert.equal(body.model, 'mimo-v2.5-tts');
  assert.deepEqual(body.messages, [{ role: 'assistant', content: 'Hello there.' }]);
  assert.deepEqual(body.audio, { format: 'wav', voice: 'Chloe' });
  assert.equal(result.files[0].path, 'assets/audio/vo/line.wav');
  assert.equal(result.files[0].bytes.length, 48044, 'the WAV as it came, header and all');
  assert.deepEqual(result.index, [{ src: 'assets/audio/vo/line.wav', kind: 'audio', dur: 1, text: 'Hello there.', voice: 'Chloe',
    from: { mode: 'synth', text: 'Hello there.', provider: 'mimo', model: 'mimo-v2.5-tts' } }]);
  assert.equal(result.receipt.voice, 'Chloe');
  assert.match(result.receipt.notes[0], /no word timings/);
});

test('a voice it does not know is said so in the answer; an answer with no audio is refused', async () => {
  const files = {};
  reply = () => [400, { error: { code: '400', message: 'Param Incorrect', param: 'Unknown voice: NoSuchVoice. Available voices: [mimo_default, Chloe]' } }];
  await assert.rejects(mimo.run('tts', { out: 'x', text: 'hi', voice: 'NoSuchVoice' }, ctx(files)), /Xiaomi MiMo answered 400: Param Incorrect/);
  reply = () => [200, { choices: [{ message: { content: '' } }] }];
  await assert.rejects(mimo.run('tts', { out: 'x', text: 'hi', voice: 'Chloe' }, ctx(files)), /answered with no audio/);
});

test('another verb is refused', async () => {
  await assert.rejects(mimo.run('sfx', { out: 'x', prompt: 'boom' }, ctx()), /Xiaomi MiMo does not do sfx/);
});
