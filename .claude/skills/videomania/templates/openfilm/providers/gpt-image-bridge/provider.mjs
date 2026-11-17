// @ts-check
/**
 * Claude Editor: the ChatGPT image bridge as an OpenFilm media provider (asset-first, no API key).
 * Installed by `vm openfilm setup` into ~/.openfilm/providers/gpt-image-bridge/provider.mjs.
 * Makes pictures with the codex CLI logged in to the person's ChatGPT account (the gpt-image-bridge skill), with up
 * to 4 reference pictures through Video Mania's gpt_image_ref.sh. 4-6 minutes a picture.
 */
import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';

const BRIDGE = process.env.GPT_IMAGE_BRIDGE || join(homedir(), '.claude', 'skills', 'gpt-image-bridge', 'bin', 'gpt-image-2');
const REF = process.env.VM_GPT_IMAGE_REF || join(homedir(), '.claude', 'skills', 'videomania', 'scripts', 'gpt_image_ref.sh');
const SIZE = { '1:1': '1024x1024', '3:2': '1536x1024', '16:9': '1536x1024', '4:3': '1536x1024', '2:3': '1024x1536', '9:16': '1024x1536', '3:4': '1024x1536' };

function run(/** @type {string[]} */ args, /** @type {AbortSignal} */ signal) {
  return new Promise((resolve, reject) => {
    execFile('bash', args, { signal, timeout: 15 * 60 * 1000, maxBuffer: 16 << 20, windowsHide: true }, (err, out, errout) => {
      if (err) reject(new Error(`image bridge failed: ${(errout || out || String(err)).slice(-600)}`));
      else resolve(out);
    });
  });
}

/** @type {import('./contract.mjs').Provider} */
const provider = {
  id: 'gpt-image-bridge',
  name: 'ChatGPT image bridge (Claude Editor)',
  env: 'GPT_IMAGE_BRIDGE',
  keysUrl: 'https://github.com/openai/codex',
  billingUrl: 'https://chatgpt.com/',
  verbs: ['image'],
  models: { image: [{ id: 'gpt-image-bridge', name: 'GPT Image via codex (your ChatGPT plan)', spec: { ratios: Object.keys(SIZE), refs: 4 } }] },
  ready: () => existsSync(BRIDGE),
  async run(verb, args, ctx) {
    if (verb !== 'image') throw new Error(`the image bridge makes pictures only, not ${verb}`);
    const prompt = String(args.prompt ?? '').trim();
    if (!prompt) throw new Error('--prompt says what to make');
    const name = String(args.out ?? 'picture').replace(/\.[a-z0-9]{2,4}$/i, '').replace(/[^\w.-]+/g, '-') || 'picture';
    const size = SIZE[String(args.ratio ?? '3:2')] ?? '1536x1024';
    const work = await mkdtemp(join(tmpdir(), 'cebridge-'));
    try {
      const out = join(work, `${name}.png`);
      const refs = [].concat(/** @type {any} */ (args.ref ?? args.refs ?? [])).filter(Boolean).slice(0, 4);
      ctx.say(`Making "${name}" with the ChatGPT image bridge (${size}${refs.length ? `, ${refs.length} reference(s)` : ''}); this takes 4-6 minutes.`);
      if (refs.length) {
        const flags = [];
        for (const [i, r] of refs.entries()) {
          const p = join(work, `ref_${i}.png`);
          await writeFile(p, await ctx.read(String(r)));
          flags.push('--ref', p);
        }
        await run([REF, prompt, out, ...flags, '--size', size], ctx.signal);
      } else {
        await run([BRIDGE, prompt, out, '--size', size], ctx.signal);
      }
      const bytes = new Uint8Array(await readFile(out));
      const path = `assets/image/${name}.png`;
      return {
        files: [{ path, bytes }],
        index: [{ src: path, kind: 'image', from: { mode: 'generate', prompt, provider: 'gpt-image-bridge', model: 'gpt-image-bridge' } }],
        receipt: { provider: 'gpt-image-bridge', model: 'gpt-image-bridge', images: [{ src: path }], note: 'made with your ChatGPT plan through codex; no API key' },
      };
    } finally {
      await rm(work, { recursive: true, force: true });
    }
  },
};

export default provider;
