/* talking-character.js — a coded, seek-safe talking character (MKTC), built on motion-kit.js + GSAP.
 *
 * A layered 2D character (body, head, eyes, brows, mouth) driven by a viseme track from
 * scripts/viseme_track.py: the mouth swaps shapes on the cues, the eyes blink on a seeded random
 * schedule, the head bobs with the voice envelope and nods on accents, the body breathes. It
 * renders with no GPU and no paid API, so it works in any HyperFrames composition.
 *
 * Contract (same as motion-fx.js / motion-shots.js):
 *   - adds seek-safe tweens to ONE paused timeline; initial state set at 0;
 *   - deterministic: randomness only from MK.rng(seed) (blinks are scheduled in advance);
 *   - parts are plain images (ChatGPT-made, sliced by scripts/character_parts.py) or the built-in
 *     vector fallback, so the rig can be previewed before any art exists;
 *   - never invents speech: the track comes from the real voiceover.
 *
 * Usage:
 *   const ch = MKTC.rig(tl, "#stage", 0 /* seconds in the film where the voice file starts *\/, {
 *     x: 560, y: 300, w: 520, track,                // track = parsed talk.json
 *     parts: window.CHAR_PARTS || null,             // parts.json from character_parts.py, or null for the vector fallback
 *     base: "media/char/",                           // folder holding the part PNGs
 *     seed: 7 });
 *   MKTC.show(tl, ch, 1.2, 9.8);                     // when the character is on screen (pop in / out)
 *   MKTC.look(tl, ch, 4.1, { x: 0.8, y: -0.2 });     // glance toward a graphic (-1..1)
 *   MKTC.reaction(tl, ch, 6.5, "surprise");           // surprise | smile | think
 */
(function (root) {
  "use strict";
  const MK = root.MK;
  if (!MK) throw new Error("talking-character.js needs motion-kit.js loaded first");
  const MKTC = {};
  const FPS = () => root.__MKS_FPS || 30;
  const snap = (t) => Math.round(t * FPS()) / FPS();
  const P = (p) => (typeof p === "string" ? document.querySelector(p) : p);
  const el = (tag, css, parent, html) => {
    const d = document.createElement(tag);
    d.setAttribute("data-layout-allow-overlap", "");
    if (css) d.style.cssText = css;
    if (html != null) d.innerHTML = html;
    if (parent) P(parent).appendChild(d);
    return d;
  };

  // ---------- pure maths (also tested in Node) ----------

  /** blink times: seeded, 2.2 to 5.4 s apart, never inside the first 0.8 s; occasional double blink */
  MKTC.blinkTimes = function (seed, duration) {
    const r = MK.rng(seed);
    const out = [];
    let t = 0.8 + r() * 1.6;
    while (t < duration - 0.3) {
      out.push(+t.toFixed(3));
      if (r() < 0.18) out.push(+(t + 0.28).toFixed(3));
      t += 2.2 + r() * 3.2;
    }
    return out;
  };

  /** collapse a viseme cue list to the minimal set of "show shape v at t" switches, min hold in seconds */
  MKTC.switches = function (cues, minHold) {
    const hold = minHold == null ? 1 / FPS() : minHold;
    const sw = [];
    for (const c of cues) {
      const last = sw[sw.length - 1];
      if (last && last.v === c.v) continue;
      if (last && c.t0 - last.t < hold) { last.v = c.v; continue; }
      sw.push({ t: c.t0, v: c.v });
    }
    return sw;
  };

  /** head pose from the envelope (0..1) at frame i: small, always-on-the-beat, never a shake */
  MKTC.pose = function (env, i, fps) {
    const e = env[Math.min(env.length - 1, Math.max(0, i))] || 0;
    const t = i / fps;
    return {
      y: -e * 9 + Math.sin(t * 1.3) * 3,
      rot: Math.sin(t * 0.9) * 1.4 + (e - 0.4) * 1.6,
      sc: 1 + e * 0.012,
    };
  };

  // ---------- vector fallback character (no art needed) ----------

  const MOUTHS = {
    X: '<path d="M30 56 Q50 60 70 56" fill="none" stroke="#3a1f1f" stroke-width="4" stroke-linecap="round"/>',
    A: '<path d="M30 56 L70 56" stroke="#3a1f1f" stroke-width="5" stroke-linecap="round"/>',
    B: '<path d="M30 54 Q50 66 70 54 Z" fill="#7a2f33"/><rect x="34" y="54" width="32" height="6" fill="#fff"/>',
    C: '<ellipse cx="50" cy="60" rx="19" ry="11" fill="#7a2f33"/><rect x="36" y="50" width="28" height="6" fill="#fff"/>',
    D: '<ellipse cx="50" cy="62" rx="21" ry="17" fill="#6a2328"/><rect x="34" y="47" width="32" height="7" fill="#fff"/><ellipse cx="50" cy="70" rx="12" ry="6" fill="#d9626a"/>',
    E: '<ellipse cx="50" cy="61" rx="11" ry="14" fill="#6a2328"/>',
    F: '<ellipse cx="50" cy="60" rx="7" ry="8" fill="#6a2328"/>',
    G: '<path d="M32 54 Q50 58 68 54 L66 60 Q50 64 34 60 Z" fill="#fff"/><path d="M34 60 Q50 70 66 60" fill="none" stroke="#3a1f1f" stroke-width="4"/>',
    H: '<ellipse cx="50" cy="60" rx="16" ry="10" fill="#7a2f33"/><ellipse cx="50" cy="55" rx="8" ry="4" fill="#d9626a"/>',
  };
  MKTC.MOUTH_KEYS = Object.keys(MOUTHS);
  MKTC.vectorMouth = (k) => `<svg viewBox="0 0 100 100" width="100%" height="100%"><g transform="translate(10,22) scale(.8)">${MOUTHS[k] || MOUTHS.X}</g></svg>`;
  const vectorHead = (skin, hair) =>
    `<svg viewBox="0 0 100 100" width="100%" height="100%"><ellipse cx="50" cy="52" rx="34" ry="40" fill="${skin}"/><path d="M14 44 Q16 8 50 8 Q84 8 86 44 Q70 22 50 24 Q30 22 14 44Z" fill="${hair}"/><circle cx="36" cy="44" r="4" fill="#222"/><circle cx="64" cy="44" r="4" fill="#222"/><path d="M28 36 Q36 31 44 35 M56 35 Q64 31 72 36" stroke="#2a1a14" stroke-width="3" fill="none" stroke-linecap="round"/></svg>`;
  const vectorLids = (skin) =>
    `<svg viewBox="0 0 100 100" width="100%" height="100%"><path d="M30 44 Q36 48 42 44 M58 44 Q64 48 70 44" stroke="#222" stroke-width="3" fill="none" stroke-linecap="round"/><rect x="29" y="39" width="14" height="9" fill="${skin}" opacity=".96"/><rect x="57" y="39" width="14" height="9" fill="${skin}" opacity=".96"/><path d="M30 44 Q36 48 42 44 M58 44 Q64 48 70 44" stroke="#222" stroke-width="3" fill="none" stroke-linecap="round"/></svg>`;

  // ---------- the rig ----------

  /**
   * rig(tl, parent, voiceStart, o)
   *   o.x,o.y,o.w   character box (head+shoulders) in the parent
   *   o.track       parsed talk.json (cues, env, accents, fps)
   *   o.parts       parts.json from character_parts.py: {head, mouthBox:{x,y,w,h}, eyeBox, mouths:{X..H}, lids}
   *                 fractions are of the head image; null = vector fallback
   *   o.base        folder of part images
   *   o.skin,o.hair colours for the vector fallback
   */
  MKTC.rig = function (tl, parent, voiceStart, o) {
    const { x = 0, y = 0, w = 500, track, parts = null, base = "", seed = 1, skin = "#f0c8a0", hair = "#2b1b12" } = o;
    const fps = track.fps || 30;
    const dur = track.duration;
    const h = o.h || w * (parts && parts.aspect ? parts.aspect : 1);
    const root_ = el("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;transform-origin:50% 90%;opacity:0`, parent);
    const aim = el("div", `position:absolute;inset:0;transform-origin:50% 85%`, root_); // look + reactions
    const head = el("div", `position:absolute;inset:0;transform-origin:50% 85%`, aim);   // voice-driven bob
    const sw = (a, b) => el("div", a, head, b);
    let mouths = {}, lids;
    if (parts) {
      const img = (src) => { const i = el("img", `position:absolute;inset:0;width:100%;height:100%;object-fit:contain`, head); i.src = base + src; return i; };
      img(parts.head);
      const mb = parts.mouthBox;
      for (const k of MKTC.MOUTH_KEYS) {
        if (!parts.mouths || !parts.mouths[k]) continue;
        const m = el("img", `position:absolute;left:${mb.x * 100}%;top:${mb.y * 100}%;width:${mb.w * 100}%;height:${mb.h * 100}%;object-fit:fill;opacity:0`, head);
        m.src = base + parts.mouths[k];
        mouths[k] = m;
      }
      if (parts.lids) {
        const eb = parts.eyeBox;
        lids = el("img", `position:absolute;left:${eb.x * 100}%;top:${eb.y * 100}%;width:${eb.w * 100}%;height:${eb.h * 100}%;object-fit:fill;opacity:0`, head);
        lids.src = base + parts.lids;
      }
    } else {
      sw(`position:absolute;inset:0`, vectorHead(skin, hair));
      for (const k of MKTC.MOUTH_KEYS) mouths[k] = sw(`position:absolute;inset:0;opacity:0`, MKTC.vectorMouth(k));
      lids = sw(`position:absolute;inset:0;opacity:0`, vectorLids(skin));
    }
    // initial state at 0, applied now too
    gsap.set(root_, { opacity: 0 });
    tl.set(root_, { opacity: 0 }, 0);
    Object.values(mouths).forEach((m) => { gsap.set(m, { opacity: 0 }); tl.set(m, { opacity: 0 }, 0); });
    const rest = mouths.X || Object.values(mouths)[0];
    if (rest) { gsap.set(rest, { opacity: 1 }); tl.set(rest, { opacity: 1 }, 0); }
    if (lids) { gsap.set(lids, { opacity: 0 }); tl.set(lids, { opacity: 0 }, 0); }

    // mouth: one switch per cue change
    let cur = rest;
    for (const s of MKTC.switches(track.cues)) {
      const m = mouths[s.v] || mouths.C || rest;
      if (!m || m === cur) continue;
      const at = snap(voiceStart + s.t);
      tl.set(cur, { opacity: 0 }, at);
      tl.set(m, { opacity: 1 }, at);
      cur = m;
    }
    // blinks: 4-frame closed lids
    if (lids) for (const t of MKTC.blinkTimes(seed, dur)) {
      tl.set(lids, { opacity: 1 }, snap(voiceStart + t));
      tl.set(lids, { opacity: 0 }, snap(voiceStart + t + 4 / FPS()));
    }
    // head: pose every 3 frames from the envelope (small, on the voice)
    const env = track.env || [];
    const step = 3;
    let prev = { y: 0, rotation: 0, scale: 1 };
    for (let i = 0; i < env.length; i += step) {
      const p = MKTC.pose(env, i, fps);
      const to = { y: p.y * (w / 500), rotation: p.rot, scale: p.sc };
      tl.fromTo(head, { ...prev }, { ...to, duration: step / fps, ease: "sine.inOut", immediateRender: false }, snap(voiceStart + i / fps));
      prev = to;
    }
    // accents: a nod (on the aim layer, so it never fights the voice-driven bob)
    for (const t of track.accents || []) {
      const at = snap(voiceStart + t);
      tl.fromTo(aim, { yPercent: 0 }, { yPercent: 1.6, duration: 0.08, ease: "power2.out", immediateRender: false }, at);
      tl.fromTo(aim, { yPercent: 1.6 }, { yPercent: 0, duration: 0.22, ease: "power2.inOut", immediateRender: false }, at + 0.08);
    }
    // body breath: explicit up/down segments (no yoyo/repeat, so any seek lands the same)
    for (let k = 0, t = 0; t < dur + voiceStart; k++, t += 2.2) {
      tl.fromTo(root_, { scaleY: k % 2 ? 1.012 : 1 }, { scaleY: k % 2 ? 1 : 1.012, duration: 2.2, ease: "sine.inOut", immediateRender: false }, snap(t));
    }
    return { root: root_, aim, head, mouths, lids, w, h, voiceStart, track };
  };

  /** pop the character in at `a` and out at `b` (film seconds). Spring in, quick out (asymmetric). */
  MKTC.show = function (tl, ch, a, b) {
    tl.fromTo(ch.root, { opacity: 0, y: 40, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "back.out(1.5)", immediateRender: false }, snap(a));
    if (b != null) tl.fromTo(ch.root, { opacity: 1, y: 0, scale: 1 }, { opacity: 0, y: 30, scale: 0.96, duration: 0.3, ease: "power2.in", immediateRender: false }, snap(b - 0.3));
    return ch;
  };

  /** glance toward a graphic: dir.x,dir.y in -1..1 (turns the head a few degrees, shifts it slightly) */
  MKTC.look = function (tl, ch, at, dir, hold) {
    const d = dir || { x: 0, y: 0 };
    const to = { x: d.x * ch.w * 0.03, rotation: d.x * 4 + d.y * -2 };
    tl.fromTo(ch.aim, { x: 0, rotation: 0 }, { ...to, duration: 0.28, ease: "power3.out", immediateRender: false }, snap(at));
    tl.fromTo(ch.aim, { ...to }, { x: 0, rotation: 0, duration: 0.45, ease: "power2.inOut", immediateRender: false }, snap(at + (hold == null ? 1.1 : hold)));
    return ch;
  };

  /** quick whole-character reactions that sit on top of the talking */
  MKTC.reaction = function (tl, ch, at, kind) {
    const A = snap(at);
    const FT = (t, a, b, d, e, at) => tl.fromTo(t, { ...a }, { ...b, duration: d, ease: e, immediateRender: false }, at);
    if (kind === "surprise") {
      FT(ch.aim, { scale: 1 }, { scale: 1.06 }, 0.1, "power3.out", A);
      FT(ch.aim, { scale: 1.06 }, { scale: 1 }, 0.45, "elastic.out(1,0.5)", A + 0.1);
    } else if (kind === "smile") {
      FT(ch.aim, { rotation: 0 }, { rotation: -3 }, 0.3, "power2.out", A);
      FT(ch.aim, { rotation: -3 }, { rotation: 0 }, 0.5, "power2.inOut", A + 0.9);
    } else if (kind === "think") {
      FT(ch.aim, { rotation: 0, y: 0 }, { rotation: 5, y: -6 }, 0.4, "power2.out", A);
      FT(ch.aim, { rotation: 5, y: -6 }, { rotation: 0, y: 0 }, 0.5, "power2.inOut", A + 1.2);
    }
    return ch;
  };

  root.MKTC = MKTC;
  if (typeof module !== "undefined" && module.exports) module.exports = MKTC;
})(typeof window !== "undefined" ? window : globalThis);
