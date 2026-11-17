// @ts-check
/**
 * OpsGen's agent edit layer: the whole timeline in a few lines, and every edit as a small JSON operation, applied
 * atomically through the film-doc parser (an edit that leaves film.html invalid is refused and nothing is written).
 * Built for agents: input and output are compact, so a film is edited in a handful of tokens per change.
 *
 *   opsgen tl [--film <dir>] [--json]                       the timeline, one line per track
 *   opsgen edit '<op | [ops]>' [--film <dir>] [--dry]       apply operations; prints what changed + the new timeline
 *   opsgen edit @ops.json                                   operations from a file
 *
 * Operations ({op, ...}); times are film seconds unless said; `id` names a clip:
 *   add     {src, at, track?, in?, out?, len?, id?, volume?, speed?, style?, class?, box?:{x,y,w,h,r}}   track: index | "new" | "new-top"
 *   move    {id, at?, track?, by?}                    by: shift in seconds
 *   trim    {id, in?, out?}                           source seconds (#t=in,out)
 *   len     {id, dur}                                  set the clip's length on the film (changes out, keeps speed)
 *   set     {id, volume?, speed?, disabled?, style?, class?, box?, muted?}
 *   delete  {id, ripple?}                              ripple: close the gap on its track
 *   dup     {id, at, track?, newId?}
 *   split   {id, t}                                    -> <id> and <id>-b at film time t
 *   ramp    {id, speeds:[[dur, speed], ...]}           speed ramp: consecutive pieces of the clip, each dur film s at its speed
 *   freeze  {id, t, dur}                               hold the frame at film time t for dur s (a still is made), ripple after
 *   kf      {id, name?, frames:{"0%":"scale: 1", "100%":"scale: 1.1"}, dur?, ease?, delay?}   keyframed motion (CSS)
 *   fade    {id, in?, out?}                            seconds of fade in / out
 *   ripple  {track, from, by}                          shift every clip on a track starting at >= from
 *   track   {add?: "top"|"bottom"|index, remove?: index, lock?: index, unlock?: index, mute?: index, unmute?: index, hide?: index, show?: index}
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { filmHtml, readFilmFile, kindOf, clipFade, FILM_FILE } from './film-doc.mjs';

const r3 = (n) => Math.round(n * 1000) / 1000;

/** the project folder: --film, else the folder around cwd holding film.html */
export function filmDir(opt) {
  if (opt) return resolve(opt);
  let d = process.cwd();
  for (;;) {
    if (existsSync(join(d, FILM_FILE))) return d;
    const up = dirname(d);
    if (up === d) throw new Error('no film.html here or above: pass --film <folder>');
    d = up;
  }
}

/** native lengths of media files, cached in .film/agent-probe.json */
function prober(dir) {
  const cacheFile = join(dir, '.film', 'agent-probe.json');
  let cache = {};
  try { cache = JSON.parse(readFileSync(cacheFile, 'utf8')); } catch { /* none yet */ }
  let dirty = false;
  const native = (src) => {
    const file = src.split('#')[0];
    if (/\.html?$/i.test(file) || /\.(png|jpe?g|webp|gif|svg)$/i.test(file)) return NaN;
    if (cache[file] != null) return cache[file];
    try {
      const out = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', join(dir, file)], { encoding: 'utf8' });
      cache[file] = Number(out.trim());
    } catch { cache[file] = NaN; }
    dirty = true;
    return cache[file];
  };
  native.save = () => { if (dirty) { mkdirSync(join(dir, '.film'), { recursive: true }); writeFileSync(cacheFile, JSON.stringify(cache)); } };
  return native;
}

/** a clip's place on the film: {at, end, len, from, to, speed} */
function span(clip, native) {
  const kind = kindOf(clip);
  const t = clip.time ?? [];
  const speed = kind === 'page' || kind === 'still' ? 1 : (clip.speed ?? 1);
  const from = t[0] ?? 0;
  let to = t[1];
  if (to == null) to = kind === 'still' ? from : native(clip.src);
  const len = (to - from) / speed;
  const at = clip.at ?? 0;
  return { at, end: at + (isFinite(len) ? len : 0), len, from, to, speed };
}

function load(dir) {
  const path = join(dir, FILM_FILE);
  const text = readFileSync(path, 'utf8');
  const { doc, problems } = readFilmFile(text);
  if (!doc) throw new Error(`${FILM_FILE} has problems:\n  ${problems.join('\n  ')}`);
  return { path, text, doc };
}

const KIND_MARK = { video: 'V', page: 'P', still: 'I', audio: 'A', sound: 'A' };

/** the timeline in a few lines */
export function timeline(dir, json = false) {
  const { doc } = load(dir);
  const native = prober(dir);
  let end = 0;
  const tracks = doc.tracks.map((tr, i) => {
    const clips = tr.clips.map((c) => {
      const s = span(c, native);
      end = Math.max(end, s.end);
      const fade = clipFade(c);
      return { id: c.id, kind: kindOf(c), src: c.src.split('#')[0], at: r3(s.at), end: r3(s.end), in: r3(s.from), out: isFinite(s.to) ? r3(s.to) : null,
        ...(s.speed !== 1 ? { speed: s.speed } : {}), ...(c.volume != null && c.volume !== 1 ? { vol: c.volume } : {}),
        ...(c.disabled ? { off: true } : {}), ...(fade ? { fade } : {}), ...(c.style && /animation/.test(c.style) ? { anim: true } : {}) };
    });
    return { track: i, ...(tr.locked ? { locked: true } : {}), ...(tr.muted ? { muted: true } : {}), ...(tr.hidden ? { hidden: true } : {}), ...(tr.captions ? { captions: tr.captions.src } : {}), clips };
  });
  native.save();
  const out = { stage: `${doc.stage.w}x${doc.stage.h}`, length: r3(end), tracks };
  if (json) return out;
  const lines = [`stage ${out.stage} · ${out.length}s · ${tracks.length} tracks`];
  for (const t of tracks) {
    const flags = ['locked', 'muted', 'hidden'].filter((f) => t[f]).join(',');
    const cl = t.clips.map((c) => {
      const extra = [c.speed ? `x${c.speed}` : '', c.vol != null ? `v${c.vol}` : '', c.off ? 'off' : '', c.fade ? `f${c.fade.join('/')}` : '', c.anim ? 'kf' : ''].filter(Boolean).join(' ');
      return `${c.id}[${c.at}→${c.end}${extra ? ' ' + extra : ''}]`;
    }).join(' ');
    lines.push(`T${t.track}${flags ? `(${flags})` : ''} ${t.captions ? `captions ${t.captions}` : (t.clips[0] ? KIND_MARK[t.clips[0].kind] ?? '?' : '-')}: ${cl}`);
  }
  return lines.join('\n');
}

function find(doc, id) {
  for (let ti = 0; ti < doc.tracks.length; ti++) {
    const ci = doc.tracks[ti].clips.findIndex((c) => c.id === id);
    if (ci >= 0) return { ti, ci, clip: doc.tracks[ti].clips[ci] };
  }
  throw new Error(`no clip "${id}" (opsgen tl lists them)`);
}

function uniqueId(doc, base) {
  const used = new Set(doc.tracks.flatMap((t) => t.clips.map((c) => c.id)));
  let id = base.replace(/[^\w.-]+/g, '-'), n = 2;
  while (used.has(id)) id = `${base}-${n++}`;
  return id;
}

function trackIndex(doc, track, at, end) {
  if (track === 'new' || track === 'new-bottom') { doc.tracks.push({ clips: [] }); return doc.tracks.length - 1; }
  if (track === 'new-top') { doc.tracks.unshift({ clips: [] }); return 0; }
  if (Number.isInteger(track)) {
    if (!doc.tracks[track]) throw new Error(`no track ${track}`);
    return track;
  }
  return -1;
}

function sortTrack(tr) { tr.clips.sort((a, b) => (a.at ?? 0) - (b.at ?? 0)); }

function overlap(tr, native, skip) {
  const spans = tr.clips.filter((c) => c !== skip).map((c) => ({ c, s: span(c, native) })).sort((a, b) => a.s.at - b.s.at);
  for (let i = 1; i < spans.length; i++) {
    if (spans[i].s.at < spans[i - 1].s.end - 1e-3) return `${spans[i - 1].c.id} and ${spans[i].c.id} overlap`;
  }
  return null;
}

/** apply one operation to doc (mutates); returns a short line saying what it did */
function apply(doc, op, native, dir) {
  const o = op.op;
  if (o === 'add') {
    const time = op.in != null || op.out != null || op.len != null
      ? [op.in ?? 0, op.out ?? (op.len != null ? (op.in ?? 0) + op.len * (op.speed ?? 1) : undefined)].filter((v) => v != null)
      : undefined;
    const clip = { src: op.src, id: uniqueId(doc, op.id ?? op.src.split('/').pop().split('#')[0].replace(/\.\w+$/, '')), at: op.at ?? 0,
      ...(time ? { time } : {}), ...(op.volume != null ? { volume: op.volume } : {}), ...(op.speed != null ? { speed: op.speed } : {}),
      ...(op.style ? { style: op.style } : {}), ...(op.class ? { class: op.class } : {}), ...(op.box ? { box: op.box } : {}) };
    let ti = trackIndex(doc, op.track ?? -1);
    if (ti < 0) {   // the first track that is free at its time and holds the same kind, else a new one
      const s = span(clip, native);
      ti = doc.tracks.findIndex((tr) => !tr.captions && !tr.locked && tr.clips.length && kindOf(tr.clips[0]) === kindOf(clip)
        && tr.clips.every((c) => { const cs = span(c, native); return cs.end <= s.at + 1e-3 || cs.at >= s.end - 1e-3; }));
      if (ti < 0) { doc.tracks.push({ clips: [] }); ti = doc.tracks.length - 1; }
    }
    doc.tracks[ti].clips.push(clip);
    sortTrack(doc.tracks[ti]);
    return `added ${clip.id} on T${ti} at ${clip.at}`;
  }
  const { ti, ci, clip } = op.id ? find(doc, op.id) : { ti: -1, ci: -1, clip: null };
  switch (o) {
    case 'move': {
      if (op.by != null) clip.at = r3((clip.at ?? 0) + op.by);
      if (op.at != null) clip.at = r3(op.at);
      if (op.track != null) {
        const to = trackIndex(doc, op.track);
        doc.tracks[ti].clips.splice(ci, 1);
        doc.tracks[to].clips.push(clip);
        sortTrack(doc.tracks[to]);
        return `moved ${clip.id} to T${to} at ${clip.at}`;
      }
      sortTrack(doc.tracks[ti]);
      return `moved ${clip.id} to ${clip.at}`;
    }
    case 'trim': {
      const s = span(clip, native);
      clip.time = [r3(op.in ?? s.from), r3(op.out ?? s.to)];
      return `trimmed ${clip.id} to #t=${clip.time.join(',')}`;
    }
    case 'len': {
      const s = span(clip, native);
      clip.time = [r3(s.from), r3(s.from + op.dur * s.speed)];
      return `${clip.id} lasts ${op.dur}s`;
    }
    case 'set': {
      for (const k of ['volume', 'speed', 'style', 'class', 'box']) if (op[k] !== undefined) clip[k] = op[k];
      if (op.muted) clip.volume = 0;
      if (op.disabled != null) { if (op.disabled) clip.disabled = true; else delete clip.disabled; }
      return `set ${clip.id}`;
    }
    case 'delete': {
      const s = span(clip, native);
      doc.tracks[ti].clips.splice(ci, 1);
      if (op.ripple) for (const c of doc.tracks[ti].clips) if ((c.at ?? 0) >= s.end - 1e-3) c.at = r3((c.at ?? 0) - s.len);
      return `deleted ${clip.id}${op.ripple ? ` (rippled ${r3(s.len)}s)` : ''}`;
    }
    case 'dup': {
      const copy = JSON.parse(JSON.stringify(clip));
      copy.id = uniqueId(doc, op.newId ?? `${clip.id}-copy`);
      copy.at = op.at;
      const to = op.track != null ? trackIndex(doc, op.track) : ti;
      doc.tracks[to].clips.push(copy);
      sortTrack(doc.tracks[to]);
      return `duplicated ${clip.id} as ${copy.id} at ${op.at}`;
    }
    case 'split': {
      const s = span(clip, native);
      if (!(op.t > s.at + 1e-3 && op.t < s.end - 1e-3)) throw new Error(`split ${clip.id}: ${op.t} is not inside ${s.at}–${s.end}`);
      const cut = r3(s.from + (op.t - s.at) * s.speed);
      const b = JSON.parse(JSON.stringify(clip));
      clip.time = [r3(s.from), cut];
      b.id = uniqueId(doc, `${clip.id}-b`);
      b.at = r3(op.t);
      b.time = [cut, r3(s.to)];
      doc.tracks[ti].clips.splice(ci + 1, 0, b);
      return `split ${clip.id} at ${op.t} -> ${clip.id}, ${b.id}`;
    }
    case 'ramp': {
      const s = span(clip, native);
      let src = s.from, at = s.at;
      const pieces = [];
      op.speeds.forEach(([dur, speed], k) => {
        const p = JSON.parse(JSON.stringify(clip));
        p.id = k === 0 ? clip.id : uniqueId(doc, `${clip.id}-r${k}`);
        p.at = r3(at); p.speed = speed; p.time = [r3(src), r3(Math.min(s.to, src + dur * speed))];
        src = p.time[1]; at += dur;
        pieces.push(p);
      });
      doc.tracks[ti].clips.splice(ci, 1, ...pieces);
      const shift = r3(at - s.end);
      if (Math.abs(shift) > 1e-3) for (const c of doc.tracks[ti].clips) if (!pieces.includes(c) && (c.at ?? 0) >= s.end - 1e-3) c.at = r3((c.at ?? 0) + shift);
      return `ramped ${clip.id} into ${pieces.length} pieces (${op.speeds.map((x) => 'x' + x[1]).join(' ')}), track shifted ${shift}s`;
    }
    case 'freeze': {
      const s = span(clip, native);
      const srcT = r3(s.from + (op.t - s.at) * s.speed);
      const still = `assets/freeze-${clip.id}-${String(srcT).replace('.', '_')}.png`;
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(srcT), '-i', join(dir, clip.src.split('#')[0]), '-frames:v', '1', join(dir, still)]);
      apply(doc, { op: 'split', id: clip.id, t: op.t }, native, dir);
      const after = doc.tracks[ti].clips.find((c) => c.id !== clip.id && c.at === r3(op.t) && c.src === clip.src);
      for (const c of doc.tracks[ti].clips) if ((c.at ?? 0) >= op.t - 1e-3) c.at = r3((c.at ?? 0) + op.dur);
      doc.tracks[ti].clips.push({ src: still, id: uniqueId(doc, `${clip.id}-freeze`), at: r3(op.t), time: [0, op.dur], ...(clip.box ? { box: clip.box } : {}) });
      sortTrack(doc.tracks[ti]);
      return `froze ${clip.id} at ${op.t} for ${op.dur}s (${still})${after ? '' : ''}`;
    }
    case 'kf': {
      const name = (op.name ?? `kf-${clip.id}`).replace(/[^\w-]/g, '-');
      doc.keyframes = doc.keyframes ?? {};
      doc.keyframes[name] = Object.entries(op.frames).map(([k, v]) => `${k} { ${v} }`).join(' ');
      const s = span(clip, native);
      const anim = `animation: ${name} ${op.dur ?? r3(s.len)}s ${op.ease ?? 'ease-in-out'} ${op.delay ?? 0}s both`;
      clip.style = [clip.style?.replace(/(^|;\s*)animation:[^;]*/g, '').replace(/^;\s*/, ''), anim].filter(Boolean).join('; ');
      return `keyframed ${clip.id} with ${name}`;
    }
    case 'fade': {
      const own = (clip.overrides ?? []).filter((x) => x.at !== undefined);
      const cur = clipFade(clip) ?? [0, 0];
      clip.overrides = [...own, { fade: [op.in ?? cur[0], op.out ?? cur[1]] }];
      return `fade ${clip.id} ${op.in ?? cur[0]}/${op.out ?? cur[1]}`;
    }
    case 'ripple': {
      for (const c of doc.tracks[op.track].clips) if ((c.at ?? 0) >= op.from - 1e-3) c.at = r3((c.at ?? 0) + op.by);
      return `rippled T${op.track} from ${op.from} by ${op.by}`;
    }
    case 'track': {
      if (op.add != null) { const t = { clips: [] }; if (op.add === 'top') doc.tracks.unshift(t); else if (Number.isInteger(op.add)) doc.tracks.splice(op.add, 0, t); else doc.tracks.push(t); return 'track added'; }
      if (op.remove != null) { if (doc.tracks[op.remove].clips.length) throw new Error(`T${op.remove} is not empty`); doc.tracks.splice(op.remove, 1); return `T${op.remove} removed`; }
      for (const [k, f, v] of [['lock', 'locked', true], ['unlock', 'locked', false], ['mute', 'muted', true], ['unmute', 'muted', false], ['hide', 'hidden', true], ['show', 'hidden', false]]) {
        if (op[k] != null) { if (v) doc.tracks[op[k]][f] = true; else delete doc.tracks[op[k]][f]; return `T${op[k]} ${k}`; }
      }
      throw new Error('track: add | remove | lock | unlock | mute | unmute | hide | show');
    }
    default:
      throw new Error(`no operation "${o}" (add move trim len set delete dup split ramp freeze kf fade ripple track)`);
  }
}

/** apply operations atomically; returns lines */
export function edit(dir, ops, { dry = false } = {}) {
  const { path, text, doc } = load(dir);
  const native = prober(dir);
  const list = Array.isArray(ops) ? ops : [ops];
  const said = list.map((op) => apply(doc, op, native, dir));
  for (const [i, tr] of doc.tracks.entries()) {
    const bad = tr.captions ? null : overlap(tr, native);
    if (bad) throw new Error(`T${i}: ${bad} (clips on one track may not overlap): nothing was written`);
  }
  const next = filmHtml(doc, text);
  const check = readFilmFile(next);
  if (!check.doc) throw new Error(`the edit would break ${FILM_FILE}: ${check.problems.join('; ')}: nothing was written`);
  native.save();
  if (!dry) writeFileSync(path, next);
  return [...said.map((s) => (dry ? '(dry) ' : '') + s), '', timeline(dir)];
}

function parseOps(arg) {
  if (!arg) throw new Error("give operations: opsgen edit '{\"op\":\"move\",\"id\":\"x\",\"at\":2}' (or @file.json)");
  const raw = arg.startsWith('@') ? readFileSync(arg.slice(1), 'utf8') : arg;
  return JSON.parse(raw);
}

/** CLI: opsgen tl / opsgen edit (raw argv after the command) */
export function agentCommand(cmd, argv) {
  const flag = (name) => { const i = argv.indexOf(name); if (i < 0) return undefined; const v = argv[i + 1]; argv.splice(i, 2); return v; };
  const has = (name) => { const i = argv.indexOf(name); if (i < 0) return false; argv.splice(i, 1); return true; };
  try {
    const film = flag('--film');
    const json = has('--json');
    const dry = has('--dry');
    const dir = filmDir(film);
    if (cmd === 'tl') {
      const t = timeline(dir, json);
      return { code: 0, lines: [json ? JSON.stringify(t) : t] };
    }
    return { code: 0, lines: edit(dir, parseOps(argv[0]), { dry }) };
  } catch (e) {
    return { code: 1, lines: [`opsgen ${cmd}: ${e instanceof Error ? e.message : e}`] };
  }
}
