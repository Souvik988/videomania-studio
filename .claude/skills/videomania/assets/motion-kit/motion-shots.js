/* motion-shots.js — the Video Mania shot & effect library (MKS), built on motion-kit.js + GSAP.
 *
 * Eighteen named effects the user asked for (2026-10-23): orbit, casualCam, uiWorld, frameBreak,
 * digitalZoom, phoneMockup, checklist, headlineWall, zoomThrough, chartGrid, pullbackReveal,
 * greenScreen, paperCut, doodleBoil, vertigo, coverStory, glassType, slideUpText.
 * Sources: the product-video shot library of nextwork-projects/ai-video-editor-cooked (MIT: orbit,
 * push-through, grid, rack focus, log-space zooms), Daniel Do's Fusion "Slide Up Text" macro
 * (per-letter expo slide behind a soft mask), the Vox / paper-diorama grammar (paper cut, doodle,
 * headline wall, cover story), Nate Herk's Claude + Blender guide (one timeline, stills first).
 * Usage notes and when-to-use: references/motion-effects-library.md.
 *
 * Contract (same as motion-fx.js):
 *   - every function is (tl, parent|target, at, opts) and adds seek-safe tweens to ONE paused
 *     timeline: initial states set at 0 (and applied immediately), every fromTo has
 *     immediateRender:false and repeats its from-vars in its to-vars (render-only pitfall);
 *   - words, numbers and media come from the caller (the narration, real recordings, ChatGPT
 *     cutouts); nothing here invents content;
 *   - colours/fonts come from CSS variables (--mk-ink --mk-accent --mk-ground --mk-display --mk-ui)
 *     or the type kit roles when window.TK is present;
 *   - deterministic: randomness only from MK.rng(seed);
 *   - returns handles so the next beat can reuse an element as its bridge.
 */
(function (root) {
  "use strict";
  const MK = root.MK;
  if (!MK) throw new Error("motion-shots.js needs motion-kit.js loaded first");
  const MKS = {};
  const FPS = () => root.__MKS_FPS || 30;
  const snap = (t) => Math.round(t * FPS()) / FPS();
  const P = (p) => (typeof p === "string" ? document.querySelector(p) : p);
  const V = (n, fb) => `var(--mk-${n}${fb ? ", " + fb : ""})`;
  const el = (tag, css, parent, html) => {
    const d = document.createElement(tag);
    d.setAttribute("data-layout-allow-overlap", "");
    if (css) d.style.cssText = css;
    if (html != null) d.innerHTML = html;
    if (parent) P(parent).appendChild(d);
    return d;
  };
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = (tag, attrs, parent) => {
    const n = document.createElementNS(svgNS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  /** seek-safe fromTo: hidden/initial state at 0 (applied now too), from-vars repeated in to-vars */
  const FT = (tl, t, from, to, at) => {
    gsap.set(t, from);
    tl.set(t, from, 0);
    tl.fromTo(t, { ...from }, { ...from, ...to, immediateRender: false }, snap(at));
  };
  const media = (parent, src, css, attrs) => {
    // images as <img>; videos as HyperFrames-owned <video> (pass data-start/duration/media-start/track-index)
    if (/\.(mp4|webm|mov)$/i.test(src)) {
      const v = el("video", css, parent);
      v.src = src; v.muted = true; v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
      for (const k in attrs || {}) v.setAttribute(k, attrs[k]);
      return v;
    }
    const i = el("img", css, parent);
    i.src = src;
    return i;
  };
  // single-quoted family names: these strings also go inside style="…" attributes of HTML templates
  const fontOf = (role, fb) => (root.TK && root.TK.C && root.TK.C.roles[role] ? root.TK.family(role) : fb).replace(/"/g, "'");
  const depth = (k, tint) => (root.TK ? root.TK.depth(k, tint) : "0 .06em .14em rgba(0,0,0,.6), 0 .2em .6em rgba(0,0,0,.45)");

  /** Log-space camera between two rects of a W×H stage: zoom-in and zoom-out read at the same speed. */
  function logCam(tl, target, at, from, to, dur, o = {}) {
    target = P(target);
    const W = o.W, H = o.H;
    const fit = (r) => Math.min(W / r.w, H / r.h);
    const s0 = fit(from), s1 = fit(to);
    const c0 = [from.x + from.w / 2, from.y + from.h / 2], c1 = [to.x + to.w / 2, to.y + to.h / 2];
    const st = { p: 0 };
    const apply = () => {
      const p = st.p;
      const s = s0 * Math.pow(s1 / s0, p);
      // the focus path follows the scale's progress so the frame centre glides with the zoom
      const k = Math.log(s / s0) / (Math.log(s1 / s0) || 1);
      const q = isFinite(k) ? k : p;
      const cx = MK.lerp(c0[0], c1[0], q), cy = MK.lerp(c0[1], c1[1], q);
      target.style.transformOrigin = "0 0";
      target.style.transform = `translate(${W / 2 - cx * s}px, ${H / 2 - cy * s}px) scale(${s})`;
      if (o.blur) target.style.filter = `blur(${o.blur(p)}px)`;
    };
    apply();
    tl.fromTo(st, { p: 0 }, { p: 1, duration: dur, ease: o.ease || "power2.inOut", immediateRender: false, onUpdate: apply }, snap(at));
    return st;
  }
  MKS.logCam = logCam;

  /* 1 ─────────── ORBIT: one lifted element turning slowly in 3D, its shadow sliding the other way */
  MKS.orbit = function (tl, parent, at, o) {
    const { src, x, y, w, h, dur = 4, deg = 16, lift = 60, radius = 24, page } = o;
    const stage = el("div", `position:absolute;left:0;top:0;width:100%;height:100%;perspective:1800px`, parent);
    if (page) {
      const bg = media(stage, page, `position:absolute;left:-10%;top:-10%;width:120%;height:120%;object-fit:cover;filter:blur(8px) brightness(.55);transform:rotateX(28deg);opacity:.85`);
      FT(tl, bg, { x: 0 }, { x: -deg * 6, duration: dur, ease: "sine.inOut" }, at);
    }
    const shadow = el("div", `position:absolute;left:${x + w * 0.05}px;top:${y + h * 0.92}px;width:${w * 0.9}px;height:${h * 0.2}px;border-radius:50%;background:rgba(0,0,0,.75);filter:blur(40px)`, stage);
    const card = el("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${radius}px;overflow:hidden;transform-style:preserve-3d;box-shadow:0 24px 60px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.14)`, stage);
    media(card, src, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, o.videoAttrs);
    const sheen = el("div", `position:absolute;inset:0;background:linear-gradient(115deg,transparent 35%,rgba(255,255,255,.22) 50%,transparent 65%);background-size:250% 100%`, card);
    FT(tl, card, { opacity: 0, rotationY: -deg, rotationX: 10, z: 0, y: 30 }, { opacity: 1, rotationX: 5, z: lift, y: 0, duration: 0.8, ease: "power3.out" }, at);
    tl.fromTo(card, { rotationY: -deg }, { rotationY: deg, duration: dur, ease: "sine.inOut", immediateRender: false }, snap(at));
    FT(tl, shadow, { opacity: 0, x: deg * 4 }, { opacity: 1, x: -deg * 4, duration: dur, ease: "sine.inOut" }, at);
    FT(tl, sheen, { backgroundPosition: "120% 0" }, { backgroundPosition: "-20% 0", duration: dur * 0.6, ease: "power1.inOut" }, at + dur * 0.2);
    return { stage, card, shadow };
  };

  /* 2 ─────────── CASUAL CAM: handheld UGC drift + snap punch-ins on stressed words */
  MKS.casualCam = function (tl, target, at, o = {}) {
    target = P(target);
    const { dur = 6, amp = 7, rot = 0.5, seed = 7, step = 0.22, punches = [], origin = "50% 35%" } = o;
    target.style.transformOrigin = origin;
    const r = MK.rng(seed);
    let px = 0, py = 0, pr = 0;
    tl.set(target, { x: 0, y: 0, rotation: 0 }, 0);
    for (let t = 0; t < dur; t += step) {
      // smoothed noise: each step drifts toward a new random point, never a jump
      const nx = (r() - 0.5) * 2 * amp, ny = (r() - 0.5) * 2 * amp * 0.7, nr = (r() - 0.5) * 2 * rot;
      px = MK.lerp(px, nx, 0.6); py = MK.lerp(py, ny, 0.6); pr = MK.lerp(pr, nr, 0.6);
      tl.to(target, { x: px, y: py, rotation: pr, duration: step, ease: "sine.inOut" }, snap(at + t));
    }
    // punches: a 2-frame snap in, a slow log-feeling ease back (ai-video-editor-cooked zoom rule)
    punches.forEach(({ t, scale = 1.14, hold = 0.5 }) => {
      tl.fromTo(target, { scale: 1 }, { scale, duration: 2 / FPS(), ease: "power4.out", immediateRender: false }, snap(t));
      tl.to(target, { scale: 1, duration: 0.8, ease: "power2.inOut" }, snap(t + hold));
    });
    return { target };
  };

  /* 3 ─────────── UI WORLD: a field of UI cards in depth; the camera dollies through to a hero card */
  MKS.uiWorld = function (tl, parent, at, o) {
    const { cards, W = 1920, H = 1080, dur = 3.2, seed = 3, hero = 0, travel = 2600 } = o;
    const stage = el("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;perspective:1400px;overflow:hidden`, parent);
    const world = el("div", `position:absolute;left:${W / 2}px;top:${H / 2}px;width:0;height:0;transform-style:preserve-3d`, stage);
    const r = MK.rng(seed);
    const nodes = cards.map((c, i) => {
      const isHero = i === hero;
      const z = isHero ? -travel + 120 : -r() * travel * 1.3 + 400;
      const x = isHero ? 0 : (r() - 0.5) * W * 1.4, y = isHero ? 0 : (r() - 0.5) * H * 1.2;
      const w = c.w || (isHero ? W * 0.5 : 520), h = c.h || (isHero ? W * 0.5 * 0.62 : 330);
      const n = el("div", `position:absolute;left:${-w / 2}px;top:${-h / 2}px;width:${w}px;height:${h}px;border-radius:22px;overflow:hidden;background:${V("surface", "#16131a")};
        box-shadow:0 30px 80px rgba(0,0,0,.6),inset 0 0 0 1px rgba(255,255,255,.12);transform:translate3d(${x}px,${y}px,${z}px) rotateY(${isHero ? 0 : (r() - 0.5) * 30}deg)`, world, c.html || "");
      if (c.src) media(n, c.src, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, c.videoAttrs);
      return n;
    });
    FT(tl, nodes, { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power2.out", stagger: 0.04 }, at);
    FT(tl, world, { z: 0, rotationY: 6 }, { z: travel - 380, rotationY: 0, duration: dur, ease: "power3.inOut" }, at);
    return { stage, world, cards: nodes, hero: nodes[hero] };
  };

  /* 4 ─────────── FRAME BREAK: the subject leaves its frame — a cut-out pops out past the border */
  MKS.frameBreak = function (tl, parent, at, o) {
    const { frameSrc, cutoutSrc, x, y, w, h, out = 110, radius = 28, border = 14, tilt = 12 } = o;
    const stage = el("div", `position:absolute;left:0;top:0;width:100%;height:100%;perspective:1600px`, parent);
    const card = el("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${radius}px;overflow:hidden;
      box-shadow:0 0 0 ${border}px ${V("paper", "#f4efe6")},0 40px 90px rgba(0,0,0,.6);transform-origin:50% 100%`, stage);
    media(card, frameSrc, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, o.videoAttrs);
    const pop = media(stage, cutoutSrc, `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;object-fit:cover;transform-origin:50% 100%;
      filter:drop-shadow(0 26px 30px rgba(0,0,0,.55))`);
    // the cut-out starts clipped to the card's rect, then the clip opens upward as it rises out
    FT(tl, card, { rotationX: 0, scale: 1 }, { rotationX: tilt, scale: 0.96, duration: 0.6, ease: "power3.out" }, at);
    FT(tl, pop, { clipPath: `inset(0% 0% 0% 0% round ${radius}px)`, y: 0, scale: 1 },
      { clipPath: `inset(-60% -20% 0% -20% round ${radius}px)`, y: -out, scale: 1.12, duration: 0.6, ease: "back.out(1.6)" }, at);
    return { stage, card, pop };
  };

  /* 5 ─────────── DIGITAL ZOOM: stepped punch-ins onto a region, each step a 2-frame snap with a
   *               chromatic flicker and HUD brackets (security-cam / screen-recording energy) */
  MKS.digitalZoom = function (tl, target, at, o) {
    target = P(target);
    const { region, W = 1920, H = 1080, steps = [1.6, 2.6], gap = 0.45, hud, label } = o;
    target.style.transformOrigin = "0 0";
    const cx = region.x + region.w / 2, cy = region.y + region.h / 2;
    const tf = (s) => ({ x: W / 2 - cx * s, y: H / 2 - cy * s, scale: s });
    tl.set(target, { x: 0, y: 0, scale: 1 }, 0);
    let prev = { x: 0, y: 0, scale: 1 };
    steps.forEach((s, i) => {
      const t = at + i * gap, to = tf(s);
      tl.fromTo(target, { ...prev }, { ...to, duration: 2 / FPS(), ease: "power4.out", immediateRender: false }, snap(t));
      tl.set(target, { filter: "drop-shadow(6px 0 0 rgba(255,40,40,.75)) drop-shadow(-6px 0 0 rgba(40,140,255,.75)) contrast(1.15)" }, snap(t));
      tl.set(target, { filter: "none" }, snap(t + 3 / FPS()));
      prev = to;
    });
    if (hud) {
      const hudEl = el("div", `position:absolute;left:${W * 0.3}px;top:${H * 0.28}px;width:${W * 0.4}px;height:${H * 0.44}px;pointer-events:none`, hud);
      const c = (css) => el("div", `position:absolute;width:56px;height:56px;border-color:${V("accent", "#ff8a1f")};border-style:solid;border-width:0;${css}`, hudEl);
      const corners = [c("left:0;top:0;border-left-width:5px;border-top-width:5px"), c("right:0;top:0;border-right-width:5px;border-top-width:5px"),
        c("left:0;bottom:0;border-left-width:5px;border-bottom-width:5px"), c("right:0;bottom:0;border-right-width:5px;border-bottom-width:5px")];
      FT(tl, hudEl, { opacity: 0, scale: 1.3 }, { opacity: 1, scale: 1, duration: 0.18, ease: "power3.out" }, at);
      if (label) {
        const lb = el("div", `position:absolute;right:0;top:-54px;font:700 30px ${V("mono", "monospace")};letter-spacing:.14em;color:${V("accent", "#ff8a1f")}`, hudEl, label);
        steps.forEach((s, i) => tl.set(lb, { textContent: `${label} ${s.toFixed(1)}×` }, snap(at + i * gap)));
      }
      return { target, hud: hudEl, corners };
    }
    return { target };
  };

  /* 6 ─────────── PHONE MOCKUP: coded device with the real screen recording, glass sheen, float */
  MKS.phoneMockup = function (tl, parent, at, o) {
    const { src, x, y, w = 330, tilt = -14, float = true, dur = 4 } = o;
    const h = w * 2.13, r = w * 0.17;
    const stage = el("div", `position:absolute;left:0;top:0;width:100%;height:100%;perspective:1800px`, parent);
    const ph = el("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${r}px;background:#0d0c0e;transform-style:preserve-3d;
      box-shadow:inset 0 0 0 2px #3a383d,inset 0 0 0 7px #0d0c0e,0 50px 100px rgba(0,0,0,.65),0 0 0 1px rgba(255,255,255,.08)`, stage);
    const scr = el("div", `position:absolute;left:${w * 0.04}px;top:${w * 0.04}px;right:${w * 0.04}px;bottom:${w * 0.04}px;border-radius:${r * 0.82}px;overflow:hidden;background:#111`, ph);
    media(scr, src, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, o.videoAttrs);
    el("div", `position:absolute;left:50%;top:${w * 0.07}px;width:${w * 0.3}px;height:${w * 0.09}px;margin-left:${-w * 0.15}px;border-radius:99px;background:#000`, ph);
    const glare = el("div", `position:absolute;inset:0;border-radius:${r}px;background:linear-gradient(120deg,transparent 30%,rgba(255,255,255,.18) 45%,transparent 60%);background-size:260% 100%;pointer-events:none`, ph);
    FT(tl, ph, { opacity: 0, y: 380, rotationY: tilt * 2.4, rotationX: 18, rotation: tilt * 0.4 },
      { opacity: 1, y: 0, rotationY: tilt, rotationX: 6, rotation: 0, duration: 0.95, ease: "expo.out" }, at);
    FT(tl, glare, { backgroundPosition: "130% 0" }, { backgroundPosition: "-30% 0", duration: 1.4, ease: "power2.inOut" }, at + 0.35);
    if (float) tl.fromTo(ph, { y: 0 }, { y: -16, duration: dur / 2, ease: "sine.inOut", yoyo: true, repeat: 1, immediateRender: false }, snap(at + 0.95));
    return { stage, phone: ph, screen: scr };
  };

  /* 7 ─────────── CHECKLIST: rows slide in, each box ticks itself on its spoken word */
  MKS.checklist = function (tl, parent, at, o) {
    const { x, y, w = 760, items, size = 54, gap = 26, strike = false } = o;
    const box = el("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px`, parent);
    const rows = items.map((it, i) => {
      const row = el("div", `display:flex;align-items:center;gap:${size * 0.45}px;margin-bottom:${gap}px;font:700 ${size}px/1.1 ${fontOf("clean_caption", V("ui", "sans-serif"))};color:${V("ink", "#fff")};text-shadow:${depth("soft")}`, box);
      const cb = el("div", `flex:0 0 auto;width:${size * 1.05}px;height:${size * 1.05}px;border-radius:${size * 0.24}px;box-shadow:inset 0 0 0 ${size * 0.08}px ${V("ink", "#fff")};position:relative`, row);
      const fill = el("div", `position:absolute;inset:0;border-radius:inherit;background:${V("accent", "#ff8a1f")}`, cb);
      const s = svg("svg", { viewBox: "0 0 24 24", width: size * 1.05, height: size * 1.05, style: "position:absolute;left:0;top:0;overflow:visible" }, cb);
      const tick = svg("path", { d: "M5 12.5l4.2 4.2L19 7", fill: "none", stroke: "#1b0f05", "stroke-width": 3.2, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);
      const txt = el("span", `position:relative`, row, it.text);
      const t = it.at != null ? it.at : at + 0.35 + i * 0.5;
      FT(tl, row, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.42, ease: "power3.out" }, at + i * 0.09);
      FT(tl, fill, { scale: 0 }, { scale: 1, duration: 0.3, ease: "back.out(2.4)" }, t);
      MK.drawPath(tl, tick, snap(t + 0.08), 0.22, { ease: "power2.out" });
      if (strike) {
        const ln = el("div", `position:absolute;left:0;top:55%;height:${size * 0.08}px;width:100%;background:${V("accent", "#ff8a1f")};transform-origin:0 50%`, txt);
        FT(tl, ln, { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: "power2.inOut" }, t + 0.12);
      }
      return { row, fill, tick };
    });
    return { box, rows };
  };

  /* 8 ─────────── HEADLINE WALL: a tilted wall of headline cards, the camera pans, one lifts out */
  MKS.headlineWall = function (tl, parent, at, o) {
    const { cards, W = 1920, H = 1080, cols = 4, highlight = 0, dur = 3, cw = 600, ch = 360, mark = true } = o;
    const stage = el("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;perspective:1600px;overflow:hidden`, parent);
    const rows = Math.ceil(cards.length / cols), gx = 34;
    const wall = el("div", `position:absolute;left:${W / 2 - (cols * (cw + gx)) / 2}px;top:${H / 2 - (rows * (ch + gx)) / 2}px;width:${cols * (cw + gx)}px;height:${rows * (ch + gx)}px;transform-style:preserve-3d`, stage);
    const serif = fontOf("classical_highlight", "Georgia, serif"), sans = fontOf("clean_caption", "sans-serif");
    const nodes = cards.map((c, i) => {
      const n = el("div", `position:absolute;left:${(i % cols) * (cw + gx)}px;top:${Math.floor(i / cols) * (ch + gx)}px;width:${cw}px;height:${ch}px;padding:26px 30px;box-sizing:border-box;
        background:#f3eee4;color:#141012;border-radius:6px;box-shadow:0 18px 40px rgba(0,0,0,.45);overflow:hidden`, wall,
        `<div style="font:700 22px ${sans};letter-spacing:.16em;text-transform:uppercase;color:#b3261e">${c.kicker || ""}</div>
         <div style="font:600 italic 58px/1.02 ${serif};margin-top:14px">${c.title}</div>
         ${c.src ? `<img src="${c.src}" style="position:absolute;right:20px;bottom:20px;width:120px;height:120px;object-fit:cover;border-radius:4px;filter:grayscale(1) contrast(1.1)">` : ""}`);
      return n;
    });
    FT(tl, wall, { rotationX: 30, rotationZ: -7, x: 260, y: 60, scale: 1.05 }, { rotationX: 22, rotationZ: -4, x: -200, y: 0, scale: 1, duration: dur, ease: "sine.inOut" }, at);
    FT(tl, nodes, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out", stagger: { each: 0.035, from: "random" } }, at);
    const hero = nodes[highlight];
    const lift = at + dur * 0.55;
    tl.to(nodes.filter((n) => n !== hero), { opacity: 0.35, filter: "blur(2px)", duration: 0.4, ease: "power2.out" }, snap(lift));
    // the lifted card glides toward the wall's centre so it never lands half off-frame
    const hx = (highlight % cols) * (cw + gx) + cw / 2, hy = Math.floor(highlight / cols) * (ch + gx) + ch / 2;
    const wallW = cols * (cw + gx), wallH = rows * (ch + gx);
    FT(tl, hero, { z: 0, scale: 1, x: 0, y: 0 }, { z: 260, scale: 1.18, x: (wallW / 2 - hx) * 0.7 - 200 * -1, y: (wallH / 2 - hy) * 0.7, duration: 0.6, ease: "back.out(1.5)" }, lift);
    let circle = null;
    if (mark) {
      const s = svg("svg", { viewBox: `0 0 ${cw} ${ch}`, width: cw, height: ch, style: "position:absolute;left:0;top:0;overflow:visible" }, hero);
      circle = svg("path", { d: `M${cw * 0.08},${ch * 0.5} C${cw * 0.06},${ch * 0.05} ${cw * 0.95},${ch * 0.02} ${cw * 0.96},${ch * 0.48} C${cw * 0.97},${ch * 0.96} ${cw * 0.05},${ch * 1.0} ${cw * 0.1},${ch * 0.38}`,
        fill: "none", stroke: "#e2231a", "stroke-width": 7, "stroke-linecap": "round" }, s);
      MK.drawPath(tl, circle, snap(lift + 0.4), 0.45, { ease: "power2.inOut" });
    }
    return { stage, wall, cards: nodes, hero, circle };
  };

  /* 9 ─────────── ZOOM-THROUGH CUT: the camera dives into a rect; the next scene grows out of it */
  MKS.zoomThrough = function (tl, world, next, at, o) {
    world = P(world); next = P(next);
    const { rect, W = 1920, H = 1080, dur = 0.9, radius = 24 } = o;
    // the dive: log-space zoom from the full frame onto the rect, motion blur in the last 40 %
    logCam(tl, world, at, { x: 0, y: 0, w: W, h: H }, rect, dur, { W, H, ease: "expo.in", blur: (p) => (p > 0.6 ? (p - 0.6) * 22 : 0) });
    // the next scene: clipped to the rect's on-screen box, opening to full frame as the dive lands
    const fitS = Math.min(W / rect.w, H / rect.h);
    const bx = (W - rect.w * fitS) / 2, by = (H - rect.h * fitS) / 2;
    FT(tl, next, { opacity: 0, clipPath: `inset(${by}px ${bx}px ${by}px ${bx}px round ${radius}px)` },
      { opacity: 1, clipPath: `inset(0px 0px 0px 0px round 0px)`, duration: dur * 0.45, ease: "power3.out" }, at + dur * 0.7);
    tl.set(world, { opacity: 0 }, snap(at + dur * 0.7 + dur * 0.45));
    return { world, next };
  };

  /* 10 ────────── CHART GRID: a grid of mini charts flies in; the camera pushes into one */
  MKS.chartGrid = function (tl, parent, at, o) {
    const { cells, W = 1920, H = 1080, cols = 3, focus = null, dur = 2.6 } = o;
    const rows = Math.ceil(cells.length / cols), g = W * 0.02;
    const cw = (W * 0.9 - g * (cols - 1)) / cols, ch = (H * 0.84 - g * (rows - 1)) / rows;
    const ox = (W - (cw * cols + g * (cols - 1))) / 2, oy = (H - (ch * rows + g * (rows - 1))) / 2;
    const stage = el("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px`, parent);
    const disp = fontOf("impact_hook", V("display", "sans-serif")), sans = fontOf("clean_caption", "sans-serif");
    const nodes = cells.map((c, i) => {
      const x = ox + (i % cols) * (cw + g), y = oy + Math.floor(i / cols) * (ch + g);
      const n = el("div", `position:absolute;left:${x}px;top:${y}px;width:${cw}px;height:${ch}px;border-radius:22px;background:${V("surface", "#16131a")};
        box-shadow:0 20px 50px rgba(0,0,0,.5),inset 0 0 0 1px rgba(255,255,255,.1);overflow:hidden;padding:24px 28px;box-sizing:border-box`, stage,
        `<div style="font:600 22px ${sans};letter-spacing:.06em;color:${V("muted", "rgba(255,255,255,.6)")};text-transform:uppercase">${c.label}</div>`);
      const t = at + 0.1 + i * 0.09;
      FT(tl, n, { opacity: 0, y: 120, scale: 0.92, filter: "blur(12px)" }, { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "power3.out" }, t);
      const plotW = cw - 56, plotH = ch - 110;
      if (c.type === "number") {
        const num = el("div", `font:400 ${Math.min(plotH, 150)}px/1 ${disp};color:${V("ink", "#fff")};margin-top:18px`, n, "0");
        MK.countUp(tl, num, 0, c.value, snap(t + 0.3), 1.0, { ease: "power2.out", format: c.format || {} });
      } else {
        const s = svg("svg", { width: plotW, height: plotH, style: "position:absolute;left:28px;bottom:26px;overflow:visible" }, n);
        const vals = c.values, max = Math.max(...vals);
        if (c.type === "line") {
          const pts = vals.map((v, k) => `${(k / (vals.length - 1)) * plotW},${plotH - (v / max) * plotH}`).join(" L");
          const ln = svg("path", { d: "M" + pts, fill: "none", stroke: c.color || "#ff8a1f", "stroke-width": 6, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);
          MK.drawPath(tl, ln, snap(t + 0.3), 0.9, { ease: "power2.inOut" });
        } else {
          const bw = (plotW / vals.length) * 0.62;
          vals.forEach((v, k) => {
            const bh = (v / max) * plotH;
            const b = svg("rect", { x: k * (plotW / vals.length), y: plotH - bh, width: bw, height: bh, rx: 6, fill: k === vals.length - 1 ? (c.color || "#ff8a1f") : "rgba(255,255,255,.28)" }, s);
            FT(tl, b, { scaleY: 0, transformOrigin: "50% 100%" }, { scaleY: 1, duration: 0.55, ease: "power3.out" }, t + 0.3 + k * 0.05);
          });
        }
      }
      return n;
    });
    if (focus != null) {
      const fx = ox + (focus % cols) * (cw + g), fy = oy + Math.floor(focus / cols) * (ch + g);
      tl.to(nodes.filter((_, i) => i !== focus), { opacity: 0.3, duration: 0.4 }, snap(at + dur * 0.6));
      logCam(tl, stage, at + dur * 0.6, { x: 0, y: 0, w: W, h: H }, { x: fx - g, y: fy - g, w: cw + 2 * g, h: ch + 2 * g }, 0.9, { W, H, ease: "power3.inOut" });
    }
    return { stage, cells: nodes };
  };

  /* 11 ────────── PULLBACK REVEAL: open tight on a detail, pull back (log space) to the whole */
  MKS.pullbackReveal = function (tl, target, at, o) {
    const { detail, W = 1920, H = 1080, dur = 1.8, rack = 10 } = o;
    return logCam(tl, target, at, detail, { x: 0, y: 0, w: W, h: H }, dur, { W, H, ease: "power3.inOut", blur: (p) => rack * Math.max(0, 0.25 - p) * 4 });
  };

  /* 12 ────────── GREEN SCREEN SANDWICH: plate → type behind → keyed subject → foreground,
   *               with plate parallax, a rim light on the subject and a contact shadow */
  MKS.greenScreen = function (tl, parent, at, o) {
    const { plate, subject, behind = [], W = 1920, H = 1080, parallax = 0.35, rim = "255,160,70", dur = 6, subjectAttrs, plateAttrs } = o;
    const stage = el("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;overflow:hidden`, parent);
    const plateW = el("div", `position:absolute;inset:-6%`, stage);
    media(plateW, plate, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, plateAttrs);
    const behindL = el("div", `position:absolute;inset:0`, stage);
    const shadow = el("div", `position:absolute;left:${W * 0.3}px;top:${H * 0.92}px;width:${W * 0.4}px;height:${H * 0.08}px;border-radius:50%;background:rgba(0,0,0,.55);filter:blur(30px)`, stage);
    const subj = el("div", `position:absolute;inset:0`, stage);
    media(subj, subject, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;filter:drop-shadow(-3px 0 6px rgba(${rim},.55)) drop-shadow(3px 0 8px rgba(120,160,255,.35))`, subjectAttrs);
    const front = el("div", `position:absolute;inset:0`, stage);
    FT(tl, plateW, { x: 0, scale: 1.04 }, { x: -W * 0.02 * parallax * 4, scale: 1.08, duration: dur, ease: "sine.inOut" }, at);
    FT(tl, subj, { x: 0 }, { x: -W * 0.02 * 4, duration: dur, ease: "sine.inOut" }, at);
    const words = behind.map((b) => {
      const d = el("div", `position:absolute;left:${b.x}px;top:${b.y}px;white-space:nowrap;font:400 ${b.size || 300}px/0.9 ${fontOf("impact_hook", V("display", "sans-serif"))};color:${b.color || "#fff4e6"};text-transform:uppercase;text-shadow:${depth("hard", "120,40,8")}`, behindL, b.text);
      FT(tl, d, { yPercent: 110, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.5, ease: "expo.out" }, b.at != null ? b.at : at);
      return d;
    });
    return { stage, plate: plateW, behind: behindL, subject: subj, front, shadow, words };
  };

  /* 13 ────────── PAPER CUT: Vox collage — paper ground, torn-edge cutouts with white borders and
   *               tape, stop-motion "on twos" entrances, a marker circle */
  MKS.paperGround = function (parent, o = {}) {
    const { color = "#efe6d2", halftone = true, seed = 1 } = o;
    const g = el("div", `position:absolute;inset:0;background:${color}`, parent);
    const id = "pg" + seed + Math.floor(MK.hash(seed) * 1e6);
    g.innerHTML = `<svg width="100%" height="100%" style="position:absolute;inset:0"><filter id="${id}"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="${seed}"/>
      <feColorMatrix values="0 0 0 0 .35  0 0 0 0 .3  0 0 0 0 .25  0 0 0 .22 0"/></filter><rect width="100%" height="100%" filter="url(#${id})"/></svg>` +
      (halftone ? `<div style="position:absolute;inset:0;opacity:.18;background:radial-gradient(circle,#000 1.1px,transparent 1.6px) 0 0/9px 9px;mix-blend-mode:multiply"></div>` : "");
    return g;
  };
  const tornPoly = (seed, n = 22, j = 2.2) => {
    const r = MK.rng(seed), pts = [];
    const edge = (fx, fy) => { for (let i = 0; i <= n; i++) { const k = i / n; pts.push(fx(k, (r() - 0.5) * j)); } };
    edge((k, d) => `${k * 100}% ${Math.max(0, d)}%`);
    edge((k, d) => `${100 - Math.max(0, d)}% ${k * 100}%`);
    edge((k, d) => `${100 - k * 100}% ${100 - Math.max(0, d)}%`);
    edge((k, d) => `${Math.max(0, d)}% ${100 - k * 100}%`);
    return `polygon(${pts.join(",")})`;
  };
  MKS.paperCut = function (tl, parent, at, o) {
    const { pieces, onTwos = true, seed = 11 } = o;
    const r = MK.rng(seed);
    const nodes = pieces.map((pc, i) => {
      const t = pc.at != null ? pc.at : at + i * 0.25;
      const wrap = el("div", `position:absolute;left:${pc.x}px;top:${pc.y}px;width:${pc.w}px;filter:drop-shadow(0 10px 14px rgba(0,0,0,.35))`, parent);
      const paper = el("div", `position:relative;padding:${pc.border == null ? 12 : pc.border}px;background:#fbf8f1;clip-path:${tornPoly(seed + i)}`, wrap);
      if (pc.src) media(paper, pc.src, `display:block;width:100%;${pc.gray ? "filter:grayscale(1) contrast(1.15)" : ""}`);
      else el("div", `width:100%;height:${pc.h || pc.w * 0.6}px;background:${pc.color || "#e2231a"}`, paper);
      if (pc.tape !== false) el("div", `position:absolute;left:50%;top:-14px;width:${pc.w * 0.32}px;height:30px;margin-left:${-pc.w * 0.16}px;background:rgba(240,228,190,.75);transform:rotate(${(r() - 0.5) * 10}deg)`, wrap);
      const rot = pc.rot != null ? pc.rot : (r() - 0.5) * 10;
      // stop-motion: stepped ease = new pose every other frame, slight overshoot on landing
      FT(tl, wrap, { opacity: 0, y: -90, rotation: rot - 14, scale: 1.12 },
        { opacity: 1, y: 0, rotation: rot, scale: 1, duration: 0.42, ease: onTwos ? "steps(6)" : "back.out(1.8)" }, t);
      return wrap;
    });
    return { pieces: nodes };
  };

  /* 14 ────────── DOODLE BOIL: a hand-drawn stroke draws on, then "boils" (re-drawn wobble every
   *               1/boilFps s via a re-seeded turbulence displacement, exactly like hand animation) */
  const DOODLES = {
    circle: "M10,52 C8,18 88,6 92,46 C95,84 18,96 14,40",
    underline: "M4,70 C30,64 62,76 96,66",
    arrow: "M8,80 C30,60 52,44 86,22 M70,18 L88,20 L82,38",
    star: "M50,8 L61,38 L94,38 L67,57 L77,90 L50,70 L23,90 L33,57 L6,38 L39,38 Z",
    squiggle: "M4,50 C14,30 24,70 34,50 C44,30 54,70 64,50 C74,30 84,70 94,50",
    check: "M12,54 L40,80 L90,18",
  };
  MKS.doodleBoil = function (tl, parent, at, o) {
    const { shape = "circle", d, x, y, w = 300, h = 200, color = "#e2231a", stroke = 6, draw = 0.5, hold = 2, boilFps = 8, amp = 2.4, seed = 5 } = o;
    const id = "boil" + seed + Math.floor(MK.hash(seed, 9) * 1e6);
    // shapes are authored on a 0-100 box; scale them to pixels so the draw-on dash and the stroke share one space
    let k = 0;
    const px = (d || DOODLES[shape]).replace(/-?\d*\.?\d+/g, (n) => ((k++ % 2 ? h : w) * parseFloat(n) / 100).toFixed(1));
    const s = svg("svg", { viewBox: `0 0 ${w} ${h}`, width: w, height: h, style: `position:absolute;left:${x}px;top:${y}px;overflow:visible` }, P(parent));
    const f = svg("filter", { id, x: "-20%", y: "-20%", width: "140%", height: "140%" }, s);
    const turb = svg("feTurbulence", { type: "fractalNoise", baseFrequency: "0.012", numOctaves: "2", seed: String(seed) }, f);
    svg("feDisplacementMap", { in: "SourceGraphic", scale: String(amp * 2.5), xChannelSelector: "R", yChannelSelector: "G" }, f);
    const path = svg("path", { d: px, fill: "none", stroke: color, "stroke-width": stroke, "stroke-linecap": "round", "stroke-linejoin": "round", filter: `url(#${id})` }, s);
    MK.drawPath(tl, path, snap(at), draw, { ease: "power2.inOut" });
    const step = 1 / boilFps;
    for (let t = 0, k = 0; t < draw + hold; t += step, k++) tl.set(turb, { attr: { seed: seed + (k % 4) } }, snap(at + t));
    return { svg: s, path };
  };
  MKS.DOODLES = DOODLES;

  /* 15 ────────── VERTIGO (dolly zoom): layers scale by depth while the subject holds its size */
  MKS.vertigo = function (tl, layers, at, o = {}) {
    const { dur = 1.6, amount = 1.45, ease = "power2.inOut", origin = "50% 45%" } = o;
    // layers: [{ el, depth }] depth 0 = subject (fixed), 1 = far background (full effect)
    return layers.map(({ el: e, depth: dp }) => {
      e = P(e);
      e.style.transformOrigin = origin;
      const s = 1 + (amount - 1) * dp;
      FT(tl, e, { scale: 1, filter: "blur(0px)" }, { scale: s, filter: `blur(${dp * 3}px)`, duration: dur, ease }, at);
      return e;
    });
  };

  /* 16 ────────── COVER STORY: the frame becomes a magazine cover — masthead behind the subject's
   *               head, cover lines, issue line, barcode */
  MKS.coverStory = function (tl, parent, at, o) {
    const { W = 1080, H = 1920, masthead = "SHOTLIN", subject, plate, lines = [], issue = "", color = "#e2231a", subjectAttrs, plateAttrs } = o;
    const stage = el("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;overflow:hidden;background:#f3eee4`, parent);
    if (plate) media(stage, plate, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, plateAttrs);
    const mh = el("div", `position:absolute;left:0;right:0;top:${H * 0.03}px;text-align:center;font:400 ${W * 0.26}px/0.86 ${fontOf("impact_hook", V("display", "sans-serif"))};color:${color};letter-spacing:-.01em;text-transform:uppercase`, stage, masthead);
    const subj = subject ? media(stage, subject, `position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover`, subjectAttrs) : null;
    const col = el("div", `position:absolute;left:${W * 0.06}px;top:${H * 0.6}px;width:${W * 0.6}px`, stage);
    const ls = lines.map((ln, i) => {
      const d = el("div", `margin-bottom:${H * 0.022}px;color:${ln.color || "#fff"};text-shadow:${depth("soft")}`, col,
        `<div style="font:400 ${ln.big ? W * 0.15 : W * 0.075}px/0.95 ${fontOf(ln.big ? "impact_hook" : "classical_highlight", "serif")};${ln.italic ? "font-style:italic;" : ""}text-transform:${ln.big ? "uppercase" : "none"}">${ln.text}</div>` +
        (ln.sub ? `<div style="font:600 ${W * 0.034}px/1.2 ${fontOf("clean_caption", "sans-serif")};margin-top:6px;opacity:.9">${ln.sub}</div>` : ""));
      FT(tl, d, { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 0.45, ease: "power3.out" }, at + 0.5 + i * 0.16);
      return d;
    });
    const iss = el("div", `position:absolute;left:${W * 0.06}px;top:${H * 0.215}px;font:700 ${W * 0.022}px ${V("mono", "monospace")};letter-spacing:.2em;color:${color}`, stage, issue);
    const bar = el("div", `position:absolute;right:${W * 0.06}px;bottom:${H * 0.04}px;width:${W * 0.16}px;height:${W * 0.1}px;background:#fff;padding:8px;box-sizing:border-box`, stage,
      `<div style="width:100%;height:100%;background:repeating-linear-gradient(90deg,#000 0 2px,transparent 2px 4px,#000 4px 7px,transparent 7px 9px)"></div>`);
    FT(tl, stage, { scale: 1.08 }, { scale: 1, duration: 0.9, ease: "power3.out" }, at);
    FT(tl, mh, { yPercent: -100, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.6, ease: "expo.out" }, at + 0.15);
    FT(tl, [iss, bar], { opacity: 0 }, { opacity: 1, duration: 0.3 }, at + 0.9);
    return { stage, masthead: mh, subject: subj, lines: ls };
  };

  /* 17 ────────── GLASS TYPE: frosted-glass letters — the scene behind is blurred and brightened
   *               only inside the glyphs (canvas-drawn mask in the loaded font), with a light edge */
  MKS.glassType = function (tl, parent, at, o) {
    const { text, x, y, size = 260, role = "impact_hook", font, weight = 400, blur = 18, tint = "255,255,255", upper = true } = o;
    const fam = font || fontOf(role, "sans-serif");
    const str = upper ? text.toUpperCase() : text;
    const c = document.createElement("canvas");
    const ctx = c.getContext("2d");
    ctx.font = `${weight} ${size}px ${fam}`;
    const m = ctx.measureText(str);
    const pad = size * 0.25, w = Math.ceil(m.width + pad * 2), h = Math.ceil(size * 1.35);
    c.width = w; c.height = h;
    ctx.font = `${weight} ${size}px ${fam}`;
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#fff";
    ctx.fillText(str, pad, h / 2);
    const url = c.toDataURL("image/png");
    const box = el("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px`, parent);
    const glass = el("div", `position:absolute;inset:0;backdrop-filter:blur(${blur}px) saturate(1.5) brightness(1.25);-webkit-backdrop-filter:blur(${blur}px) saturate(1.5) brightness(1.25);
      background:linear-gradient(170deg,rgba(${tint},.42),rgba(${tint},.12) 55%,rgba(${tint},.26));-webkit-mask:url(${url}) 0 0/100% 100% no-repeat;mask:url(${url}) 0 0/100% 100% no-repeat`, box);
    const edge = el("div", `position:absolute;left:${pad}px;top:0;height:${h}px;line-height:${h}px;white-space:nowrap;font:${weight} ${size}px ${fam};color:transparent;
      -webkit-text-stroke:${Math.max(2, size / 110)}px rgba(255,255,255,.75);text-shadow:0 ${size * 0.04}px ${size * 0.12}px rgba(0,0,0,.35)`, box, str);
    FT(tl, box, { opacity: 0, y: 40, scale: 1.04, filter: "blur(10px)" }, { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "power3.out" }, at);
    return { box, glass, edge };
  };

  /* 18 ────────── SLIDE-UP TEXT (Daniel Do macro): letters slide up from behind a soft-edged line,
   *               ~0.7 frame apart, expo ease-out with a little motion blur; mirrored exit */
  MKS.slideUpText = function (tl, parent, at, o) {
    const { text, x, y, size = 120, role = "clean_caption", weight = 700, color = "#fff", align = "left", per = 0.7, dur = 0.55, out = null, soft = 0.12 } = o;
    const box = el("div", `position:absolute;left:${x}px;top:${y}px;white-space:nowrap;${align === "center" ? "transform:translateX(-50%);" : align === "right" ? "transform:translateX(-100%);" : ""}
      font:${weight} ${size}px/1.15 ${fontOf(role, "sans-serif")};color:${color};text-shadow:${depth("soft")};
      -webkit-mask-image:linear-gradient(to bottom,#000 ${100 - soft * 100}%,transparent 100%);mask-image:linear-gradient(to bottom,#000 ${100 - soft * 100}%,transparent 100%);padding-bottom:${size * 0.12}px`, parent);
    const chars = Array.from(text).map((ch) => el("span", `display:inline-block;white-space:pre`, box, ch === " " ? " " : ch));
    const st = per / FPS();
    chars.forEach((c, i) => FT(tl, c, { yPercent: 105, opacity: 0, filter: "blur(3px)" }, { yPercent: 0, opacity: 1, filter: "blur(0px)", duration: dur, ease: "expo.out" }, at + i * st));
    if (out != null) tl.to(chars, { yPercent: -105, opacity: 0, filter: "blur(3px)", duration: dur * 0.7, ease: "expo.in", stagger: st }, snap(out));
    return { box, chars };
  };

  MKS.NAMES = ["orbit", "casualCam", "uiWorld", "frameBreak", "digitalZoom", "phoneMockup", "checklist", "headlineWall", "zoomThrough", "chartGrid",
    "pullbackReveal", "greenScreen", "paperCut", "doodleBoil", "vertigo", "coverStory", "glassType", "slideUpText"];
  root.MKS = MKS;
})(typeof window !== "undefined" ? window : globalThis);
