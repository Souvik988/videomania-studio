/* motion-kit.js: Video Mania's motion toolkit for HyperFrames compositions.
 *
 * Fills the gaps between the hyperframes-animation rules (48 atomic recipes, 22 blueprints) and
 * what premium Opus 5.5 motion needs (references/motion-design-playbook.md). Every helper ADDS
 * tweens to ONE paused GSAP timeline that HyperFrames seeks; nothing runs on its own clock.
 *
 * Contract (same as hyperframes-animation/rules-index.md):
 *   - seek-safe both directions: fromTo / set with explicit states, absolute values, no += tweens
 *   - deterministic: MK.rng / MK.hash only, never Math.random or Date.now
 *   - paint/transform properties only (transform, opacity, clip-path, filter, stroke-dashoffset,
 *     colour); never width/height/top/left tweens: morphs use clip-path on a full-size shell
 *   - DOM is measured/built once at build time, never inside onUpdate
 *
 * Load after GSAP:  <script src="vendor/gsap-3.14.2.min.js"></script><script src="motion-kit.js"></script>
 * Pure maths (springs, bezier, rng, camera fit) also loads in Node for tests: require('./motion-kit.js').
 */
(function (root) {
  "use strict";
  const MK = {};

  // ───────────────────────── maths ─────────────────────────
  MK.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  MK.lerp = (a, b, k) => a + (b - a) * k;

  /** Seeded PRNG (mulberry32). Same seed, same sequence, every render. */
  MK.rng = function (seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  /** Stateless hash in [0,1) for index-derived variation (stagger jitter, particle spots). */
  MK.hash = (i, salt = 0) => {
    const s = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453123;
    return s - Math.floor(s);
  };

  /** cubic-bezier(x1,y1,x2,y2) as an ease function p∈[0,1] → [0,1] (Newton + bisection). */
  MK.bezier = function (x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (t) => ((ax * t + bx) * t + cx) * t;
    const sy = (t) => ((ay * t + by) * t + cy) * t;
    const dx = (t) => (3 * ax * t + 2 * bx) * t + cx;
    return function (p) {
      if (p <= 0) return 0;
      if (p >= 1) return 1;
      let t = p;
      for (let i = 0; i < 8; i++) {
        const e = sx(t) - p, d = dx(t);
        if (Math.abs(e) < 1e-6) return sy(t);
        if (Math.abs(d) < 1e-6) break;
        t -= e / d;
      }
      let lo = 0, hi = 1;
      t = p;
      for (let i = 0; i < 30; i++) {
        const v = sx(t);
        if (Math.abs(v - p) < 1e-6) break;
        if (v < p) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
      return sy(t);
    };
  };

  /** Named curves. `glide` is the default signature morph curve from the playbook. */
  MK.ease = {
    glide: MK.bezier(0.45, 0, 0.15, 1),
    enter: MK.bezier(0.16, 1, 0.3, 1),   // expo-like out: confident arrivals
    exit: MK.bezier(0.7, 0, 0.84, 0),    // expo-like in: throw away
    move: MK.bezier(0.65, 0, 0.35, 1),   // in-out between positions
  };

  /**
   * Damped spring as a GSAP ease, solved analytically (no simulation, so seeking is exact).
   * Returns { ease, duration, overshoot }: use `duration` as the tween length so the spring's
   * natural settle time maps onto p∈[0,1]. damping ratio z = damping / (2*sqrt(stiffness*mass)).
   * Tight UI: {stiffness:260, damping:24}; soft card: {170, 18}; playful: {200, 12}.
   */
  MK.spring = function ({ stiffness = 200, damping = 22, mass = 1, velocity = 0, settle = 0.002 } = {}) {
    const w0 = Math.sqrt(stiffness / mass);
    const z = damping / (2 * Math.sqrt(stiffness * mass));
    let x;
    if (z < 1) {
      const wd = w0 * Math.sqrt(1 - z * z);
      const B = (z * w0 + -velocity) / wd;
      x = (t) => 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + B * Math.sin(wd * t));
    } else {
      const B = w0 - velocity;
      x = (t) => 1 - Math.exp(-w0 * t) * (1 + B * t);
    }
    let T = 0.05, maxV = 0;
    for (let t = 0; t < 10; t += 1 / 240) {
      const v = x(t);
      maxV = Math.max(maxV, v);
      if (Math.abs(1 - v) > settle) T = t + 1 / 240;
    }
    const duration = Math.round(T * 1000) / 1000;
    const ease = (p) => (p >= 1 ? 1 : x(p * duration));
    return { ease, duration, overshoot: Math.max(0, maxV - 1) };
  };

  /** Snap a time to the frame grid (steep eases alias at sub-frame ends; playbook §13.4). */
  MK.snap = (t, fps = 30) => Math.round(t * fps) / fps;

  /**
   * Camera fit for an exact world window {x,y,w,h} inside a frame {w,h}: returns the transform
   * (scale, translate) that centres the window. Windows, not scale factors: edges fall where you say.
   */
  MK.fitWindow = function (win, frame) {
    const s = Math.min(frame.w / win.w, frame.h / win.h);
    return { scale: s, x: frame.w / 2 - (win.x + win.w / 2) * s, y: frame.h / 2 - (win.y + win.h / 2) * s };
  };

  /** Keyhole outline (circle + tapered slot) as a clip-path polygon string. */
  MK.keyholePath = function (cx, cy, r, steps = 32) {
    const a0 = Math.asin(0.57), pts = [];
    for (let i = 0; i <= steps; i++) {
      const a = Math.PI / 2 + a0 + (2 * Math.PI - 2 * a0) * (i / steps);
      pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
    }
    pts.push([cx + 0.86 * r, cy + 2.71 * r], [cx - 0.86 * r, cy + 2.71 * r]);
    return "polygon(" + pts.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(",") + ")";
  };

  MK.formatNumber = (v, { decimals = 0, prefix = "", suffix = "", group = "intl" } = {}) => {
    const n = Number(v).toFixed(decimals);
    const [i, d] = n.split(".");
    let int = i;
    if (group === "intl") int = i.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    else if (group === "indian") {
      const last3 = i.slice(-3), rest = i.slice(0, -3);
      int = (rest ? rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," : "") + last3;
    }
    return prefix + int + (d ? "." + d : "") + suffix;
  };

  // ───────────────────────── DOM helpers (browser only) ─────────────────────────
  const hasDOM = typeof document !== "undefined";
  const $ = (q) => (typeof q === "string" ? document.querySelector(q) : q);
  const $$ = (q) => (typeof q === "string" ? Array.from(document.querySelectorAll(q)) : Array.from(q));

  /** Pad the timeline to the slot length, so HyperFrames never hides the composition early (§13.1). */
  MK.pad = (tl, duration) => tl.to({}, { duration }, 0);

  /**
   * Split an element's text into masked units for mask-line reveals. Each unit is wrapped as
   * <span class="mk-mask"><span class="mk-unit">…</span></span>; returns the inner units.
   * by: "words" | "chars" | "lines" (lines = existing child elements).
   */
  MK.split = function (el, by = "words") {
    el = $(el);
    if (el.dataset.mkSplit) return $$(el.querySelectorAll(".mk-unit"));
    el.dataset.mkSplit = by;
    const wrap = (txt) => {
      const m = document.createElement("span");
      m.className = "mk-mask";
      m.style.cssText = "display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:0.08em;margin-bottom:-0.08em";
      const u = document.createElement("span");
      u.className = "mk-unit";
      u.style.cssText = "display:inline-block;will-change:transform";
      u.textContent = txt;
      m.appendChild(u);
      return m;
    };
    if (by === "lines") {
      Array.from(el.children).forEach((c) => {
        const m = wrap("");
        m.firstChild.appendChild(c.cloneNode(true));
        el.replaceChild(m, c);
      });
    } else {
      const text = el.textContent;
      el.textContent = "";
      const parts = by === "chars" ? Array.from(text) : text.split(/(\s+)/);
      parts.forEach((p) => {
        if (/^\s+$/.test(p)) el.appendChild(document.createTextNode(p.includes("\n") ? " " : p));
        else if (p.length) el.appendChild(wrap(p === " " ? " " : p));
      });
    }
    return $$(el.querySelectorAll(".mk-unit"));
  };

  /**
   * Mask-line reveal: units rise through a clean cut line (no pop-ins, no typewriter headlines).
   * opts: by ("words"), stagger (0.05), dur (0.6), ease (MK.ease.enter), from (110 = yPercent)
   */
  MK.maskRise = function (tl, el, at, { by = "words", stagger = 0.05, dur = 0.6, ease = MK.ease.enter, from = 110 } = {}) {
    const units = MK.split(el, by);
    tl.fromTo(units, { yPercent: from }, { yPercent: 0, duration: dur, ease, stagger }, at);
    return units;
  };

  /** Mask-line exit (faster than the entry: exits are shorter than entrances). */
  MK.maskFall = function (tl, el, at, { stagger = 0.03, dur = 0.35, ease = MK.ease.exit, to = -110 } = {}) {
    const units = $$($(el).querySelectorAll(".mk-unit"));
    tl.fromTo(units, { yPercent: 0 }, { yPercent: to, duration: dur, ease, stagger, immediateRender: false }, at);
    return units;
  };

  /**
   * Word-reveal carrier (dark-lit recipe): the first word carries momentum with a long slide,
   * the tail decays. `times` are each word's spoken start (anchor to ASR); lead (s) shows the
   * picture slightly ahead of the word so it reads as inevitable.
   */
  MK.wordCarrier = function (tl, els, times, { distances = [360, 120, 60, 25, 12], lead = 0.06, axis = "x" } = {}) {
    $$(els).forEach((el, i) => {
      const d = distances[Math.min(i, distances.length - 1)];
      const first = i === 0;
      tl.fromTo(el, { [axis]: d, opacity: 0 },
        { [axis]: 0, opacity: 1, duration: first ? 0.33 : 0.2, ease: first ? "expo.out" : "power2.out" },
        Math.max(0, times[i] - lead));
    });
  };

  /**
   * Shape morph with a ghost: ONE object changing shape (playbook §3). `shell` is absolutely
   * positioned at the END box (its final layout); the move is a clip-path inset that starts at
   * the FROM box, so nothing tweens width/height. Old contents fade in the first quarter; new
   * contents (opts.contents) fade in after halfway. A dashed ghost stays at the start box.
   *   from/to: {x, y, w, h, r} in the shell's parent coordinates
   */
  MK.morph = function (tl, shell, from, to, at, dur = 0.8, { ease = MK.ease.glide, ghost = true, oldContents = null, contents = null, ghostColor = "currentColor" } = {}) {
    shell = $(shell);
    const inset = (b) => `inset(${b.y - to.y}px ${to.x + to.w - (b.x + b.w)}px ${to.y + to.h - (b.y + b.h)}px ${b.x - to.x}px round ${b.r ?? 0}px)`;
    tl.fromTo(shell, { clipPath: inset(from) }, { clipPath: inset(to), duration: dur, ease }, at);
    if (oldContents) tl.fromTo($$(oldContents), { opacity: 1 }, { opacity: 0, duration: dur * 0.25, ease: "power1.in", immediateRender: false }, at);
    if (contents) tl.fromTo($$(contents), { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: dur * 0.45, ease: "power2.out", stagger: 0.05 }, at + dur * 0.5);
    let g = null;
    if (ghost && hasDOM) {
      g = document.createElement("div");
      g.className = "mk-ghost";
      g.style.cssText = `position:absolute;left:${from.x}px;top:${from.y}px;width:${from.w}px;height:${from.h}px;` +
        `border:2px dashed ${ghostColor};border-radius:${from.r ?? 0}px;opacity:0;pointer-events:none;box-sizing:border-box`;
      shell.parentNode.insertBefore(g, shell);
      tl.fromTo(g, { opacity: 0 }, { opacity: 0.28, duration: dur * 0.3, ease: "power1.out" }, at + dur * 0.15);
    }
    return g;
  };

  /**
   * Camera through one persistent world (storytelling-and-retention.md §4). `world` holds the
   * whole space at its natural size (transform-origin 0 0). Each stop is an exact window.
   *   const cam = MK.camera(tl, "#world", {w:1080, h:1920});
   *   cam.set({x,y,w,h}, 0); cam.to({x,y,w,h}, at, dur)
   * Duration should grow with distance travelled; default ease is the in-out move curve.
   */
  MK.camera = function (tl, world, frame) {
    world = $(world);
    if (hasDOM) world.style.transformOrigin = "0 0";
    let last = null;
    return {
      set(win, at = 0) {
        const f = MK.fitWindow(win, frame);
        tl.set(world, { x: f.x, y: f.y, scale: f.scale }, at);
        last = win;
      },
      to(win, at, dur = 1.2, ease = MK.ease.move) {
        const a = MK.fitWindow(last || win, frame), b = MK.fitWindow(win, frame);
        tl.fromTo(world, { x: a.x, y: a.y, scale: a.scale }, { x: b.x, y: b.y, scale: b.scale, duration: dur, ease, immediateRender: false }, at);
        last = win;
      },
      /** suggested duration for a move: longer for longer travel (0.7–2.2 s) */
      durationFor(win) {
        if (!last) return 1.0;
        const a = MK.fitWindow(last, frame), b = MK.fitWindow(win, frame);
        const dist = Math.hypot(a.x - b.x, a.y - b.y) / Math.max(frame.w, frame.h) + Math.abs(Math.log(b.scale / a.scale));
        return MK.clamp(0.7 + dist * 0.9, 0.7, 2.2);
      },
    };
  };

  /**
   * Spotlight: exactly one element at full brightness; context quiet but legible; spent dimmer.
   * Call at every narration beat with the active ids; previously active ids become "spent"
   * unless listed in `context`. Levels follow the herk-edit-kit luma targets.
   */
  MK.spotlight = function (tl, items, { active = 1, context = 0.56, spent = 0.33, dur = 0.35 } = {}) {
    const state = {};
    Object.keys(items).forEach((k) => (state[k] = null));
    return {
      at(t, activeIds, contextIds = []) {
        const A = new Set([].concat(activeIds)), C = new Set(contextIds);
        Object.entries(items).forEach(([k, el]) => {
          let target;
          if (A.has(k)) target = active;
          else if (C.has(k)) target = context;
          else if (state[k] !== null) target = spent;
          else return; // not yet drawn: leave alone
          tl.to($(el), { opacity: target, duration: dur, ease: "power2.inOut" }, t);
          state[k] = target;
        });
      },
    };
  };

  /** Count-up through a proxy; text is a pure function of the proxy value (seek-safe). */
  MK.countUp = function (tl, el, from, to, at, dur = 0.9, { ease = "power3.out", format = {} } = {}) {
    el = $(el);
    const p = { v: from };
    el.textContent = MK.formatNumber(from, format);
    tl.fromTo(p, { v: from }, { v: to, duration: dur, ease, onUpdate: () => (el.textContent = MK.formatNumber(p.v, format)) }, at);
  };

  /** Draw an SVG path or line on (stroke-dashoffset), length measured once at build time. */
  MK.drawPath = function (tl, path, at, dur = 0.8, { ease = MK.ease.glide, reverse = false } = {}) {
    $$(typeof path === "string" ? document.querySelectorAll(path) : [].concat(path)).forEach((p) => {
      const L = p.getTotalLength ? p.getTotalLength() : 1000;
      p.style.strokeDasharray = `${L} ${L}`;
      tl.fromTo(p, { strokeDashoffset: reverse ? -L : L }, { strokeDashoffset: 0, duration: dur, ease }, at);
    });
  };

  /** Typing inside an input box (the ONE place typing belongs). Optional blinking caret element. */
  MK.typeText = function (tl, el, text, at, dur, { caret = null, blink = 0.5, until = null } = {}) {
    el = $(el);
    const p = { n: 0 };
    el.textContent = "";
    tl.fromTo(p, { n: 0 }, { n: text.length, duration: dur, ease: "none", onUpdate: () => (el.textContent = text.slice(0, Math.round(p.n))) }, at);
    if (caret) {
      caret = $(caret);
      const end = until ?? at + dur + 1.5;
      for (let t = at; t < end; t += blink) tl.set(caret, { opacity: Math.round((t - at) / blink) % 2 === 0 ? 1 : 0 }, t);
      tl.set(caret, { opacity: 0 }, end);
    }
  };

  /**
   * Iris reveal of an element through a growing shape centred on (cx, cy) in the element's own
   * coordinates. shape: "circle" | "keyhole". Use for "look through" transitions (keyhole→scene).
   */
  MK.iris = function (tl, el, { cx, cy, r0 = 0, r1 = 1500, shape = "circle" }, at, dur = 0.5, ease = "power3.in") {
    el = $(el);
    const p = { r: r0 };
    const apply = () => (el.style.clipPath = shape === "keyhole" ? MK.keyholePath(cx, cy, p.r) : `circle(${p.r}px at ${cx}px ${cy}px)`);
    apply();
    tl.fromTo(p, { r: r0 }, { r: r1, duration: dur, ease, onUpdate: apply }, at);
    tl.set(el, { clipPath: "none" }, at + dur + 0.001);
  };

  /** Brackets snapping around a target box before it lifts ("this one"): 4 L-corners. */
  MK.brackets = function (tl, parent, box, at, { color = "#f3a712", size = 28, stroke = 5, pad = 10, dur = 0.3 } = {}) {
    parent = $(parent);
    const corners = [[0, 0, 1, 1], [1, 0, -1, 1], [0, 1, 1, -1], [1, 1, -1, -1]].map(([ax, ay, sx, sy]) => {
      const d = document.createElement("div");
      const x = box.x - pad + ax * (box.w + 2 * pad) - (ax ? size : 0);
      const y = box.y - pad + ay * (box.h + 2 * pad) - (ay ? size : 0);
      d.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:${size}px;height:${size}px;box-sizing:border-box;pointer-events:none;` +
        `border-${sx > 0 ? "left" : "right"}:${stroke}px solid ${color};border-${sy > 0 ? "top" : "bottom"}:${stroke}px solid ${color};opacity:0`;
      parent.appendChild(d);
      tl.fromTo(d, { opacity: 0, x: -sx * 18, y: -sy * 18 }, { opacity: 1, x: 0, y: 0, duration: dur, ease: "back.out(2)" }, at);
      return d;
    });
    return corners;
  };

  /**
   * Seeded particles that fly on gentle arcs into target points (particle logo, dots forming a
   * shape). targets: [[x,y],…]; each particle starts at a seeded scatter position.
   */
  MK.particlesTo = function (tl, parent, targets, at, { seed = 7, spread = 600, origin = [0, 0], dur = 1.1, size = 8, color = "#fff", window: w = 1.0 } = {}) {
    parent = $(parent);
    const r = MK.rng(seed);
    return targets.map(([tx, ty], i) => {
      const d = document.createElement("div");
      d.style.cssText = `position:absolute;left:0;top:0;width:${size}px;height:${size}px;border-radius:50%;background:${color};will-change:transform`;
      parent.appendChild(d);
      const sx = origin[0] + (r() - 0.5) * spread * 2, sy = origin[1] + (r() - 0.5) * spread * 2;
      const delay = (tx / 2000 + r() * 0.15) * w;
      const p = { k: 0 };
      const bend = (r() - 0.5) * 240;
      const apply = () => {
        const k = p.k, x = MK.lerp(sx, tx, k), y = MK.lerp(sy, ty, k) + bend * Math.sin(Math.PI * k);
        d.style.transform = `translate(${x - size / 2}px, ${y - size / 2}px)`;
      };
      apply();
      tl.fromTo(p, { k: 0 }, { k: 1, duration: dur, ease: MK.ease.glide, onUpdate: apply }, at + delay);
      return d;
    });
  };

  /**
   * Grain overlay: SVG fractal noise re-seeded every frame through the timeline (deterministic).
   * Returns the svg element; call once with the film duration.
   */
  MK.grain = function (tl, parent, duration, { opacity = 0.07, fps = 24, blend = "overlay", w = 1080, h = 1920, freq = 0.8 } = {}) {
    parent = $(parent);
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.style.cssText = `position:absolute;inset:0;width:100%;height:100%;opacity:${opacity};mix-blend-mode:${blend};pointer-events:none;z-index:60`;
    const id = "mkgrain" + Math.floor(MK.hash(w, h) * 1e6);
    svg.innerHTML = `<filter id="${id}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="${freq}" numOctaves="2" seed="1" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="${w}" height="${h}" filter="url(#${id})"/>`;
    parent.appendChild(svg);
    const turb = svg.querySelector("feTurbulence");
    const p = { t: 0 };
    tl.fromTo(p, { t: 0 }, { t: duration, duration, ease: "none", onUpdate: () => turb.setAttribute("seed", String(Math.floor(p.t * fps) % 16)) }, 0);
    return svg;
  };

  /**
   * Captions driven by the timeline (seek-safe tl.set at cue/word times). cues: window.CUES from
   * caption_track.py (phrase or chunk mode). off: [[a,b],…] windows where a headline spells the
   * words. colours: {ink, dim, fr, go}. Chunk cues carry a cue-level class `c` (whole chunk).
   */
  MK.captions = function (tl, container, cues, { off = [], colors = { ink: "#fffaf2", dim: "rgba(255,250,242,0.5)", fr: "#ff7a66", go: "#ffc23d" }, className = "cue" } = {}) {
    container = $(container);
    const isOff = (a, b) => off.some(([x, y]) => a < y && b > x);
    cues.forEach((c) => {
      if (isOff(c.s, c.e)) return;
      const d = document.createElement("div");
      d.className = className;
      d.style.opacity = 0;
      c.lines.forEach((ln) => {
        const L = document.createElement("span");
        L.className = "ln";
        ln.forEach((w, i) => {
          const s = document.createElement("span");
          s.textContent = (i ? " " : "") + w.w;
          const col = c.c ? colors[c.c] || colors.ink : colors.ink;
          s.style.color = c.c ? col : colors.dim;
          L.appendChild(s);
          if (!c.c) {
            tl.set(s, { color: w.c ? colors[w.c] : colors.ink }, Math.max(c.s, w.s - 0.03));
          }
        });
        d.appendChild(L);
      });
      container.appendChild(d);
      tl.set(d, { opacity: 1 }, Math.max(0, c.s));
      tl.set(d, { opacity: 0 }, c.e);
    });
  };

  /** Video bracketing (§13.2): poster hidden at the video's start, last frame shown at its end. */
  MK.bracketVideo = function (tl, { poster = null, last = null, start, end }) {
    if (poster) { tl.set($(poster), { opacity: 1 }, 0); tl.set($(poster), { opacity: 0 }, start); }
    if (last) { tl.set($(last), { opacity: 0 }, 0); tl.set($(last), { opacity: 1 }, end); }
  };

  /** Word timings → beat list for anchoring (words: [{word,start,end}]); finds a word near a time. */
  MK.wordAt = (words, text, near = 0) => {
    const key = (s) => s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
    const k = key(text);
    let best = null;
    for (const w of words) if (key(w.word) === k && (!best || Math.abs(w.start - near) < Math.abs(best.start - near))) best = w;
    return best;
  };

  root.MK = MK;
  if (typeof module !== "undefined" && module.exports) module.exports = MK;
})(typeof window !== "undefined" ? window : globalThis);
