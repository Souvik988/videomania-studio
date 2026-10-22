/* Video Mania type kit (TK): the seven font roles, eight pairings and ten presets of
 * typography/config/*.json, rendered on one paused GSAP timeline (HyperFrames: seek-safe, every
 * initial state set at 0, every fromTo with immediateRender:false, from-vars repeated in to-vars).
 *
 *   TK.init({ W, H, fps })                       canvas size (sizes are px at a 1080 short side)
 *   await TK.load(["impact_hook", ...])          load the faces before building (never paint a fallback)
 *   TK.style(el, role, spec)                     apply a role's face + a preset tier's spec
 *   TK.anim[name](tl, el, t, opts) → end time    23 animation presets (see ANIMS below)
 *   TK.title(tl, parent, parts, t)               a composed multi-font title (hero / pairing cards)
 *   TK.captions(tl, root, cues, opts)            rhythmic multi-font captions, word-synced
 *   TK.out(tl, els, t, kind)                     minimalFade | fastDrop | softFade
 *   TK.extrude(tl, frontEl, t, opts)             stacked-layer 3D extrusion for one hero word
 *
 * Config comes from window.TK_CONFIG (type-kit.config.js, written by build_typekit.py).
 */
(function () {
  const C = window.TK_CONFIG;
  if (!C) throw new Error("type-kit: load type-kit.config.js first");
  const TK = { C, W: 1920, H: 1080, k: 1, fps: 30 };
  const snap = (t) => Math.round(t * TK.fps) / TK.fps;
  TK.snap = snap;

  TK.init = function ({ W, H, fps = 30 }) {
    Object.assign(TK, { W, H, fps, k: Math.min(W, H) / 1080 });
    return TK;
  };

  /* ---------------- faces ---------------- */
  TK.family = (role) => {
    const r = C.roles[role];
    if (!r) throw new Error("type-kit: unknown role " + role);
    return `"${r.css}", ${r.stack}`;
  };
  TK.load = async function (roles = Object.keys(C.roles)) {
    const reqs = [];
    for (const role of roles) {
      const r = C.roles[role];
      for (const w of r.load) reqs.push(document.fonts.load(`${w} 100px "${r.css}"`, r.sample || "Aa"));
    }
    await Promise.all(reqs);
    await document.fonts.ready;
  };

  /* ---------------- depth (the soft drop shadow the user asked for) ---------------- */
  // em-based, so the shadow scales with the type; `tint` colours the extrusion / glow.
  TK.depth = function (kind = "soft", tint = "0,0,0") {
    const soft = "0 .035em 0 rgba(0,0,0,.30), 0 .08em .14em rgba(0,0,0,.55), 0 .2em .55em rgba(0,0,0,.42), 0 .45em 1.1em rgba(0,0,0,.30)";
    if (kind === "none") return "none";
    if (kind === "hard") return `0 .045em 0 rgba(${tint},.95), 0 .09em 0 rgba(0,0,0,.45), 0 .14em .2em rgba(0,0,0,.6), 0 .3em .7em rgba(0,0,0,.45)`;
    if (kind === "glow") return `${soft}, 0 0 .5em rgba(${tint},.45)`;
    if (kind === "strong") return `0 .035em 0 rgba(0,0,0,.4), 0 .06em .1em rgba(0,0,0,.8), 0 .16em .4em rgba(0,0,0,.7), 0 .4em 1em rgba(0,0,0,.5)`;
    return soft;
  };

  const CASES = {
    upper: (s) => s.toUpperCase(),
    lower: (s) => s.toLowerCase(),
    title: (s) => s.replace(/(^|\s)(\p{L})/gu, (m, a, b) => a + b.toUpperCase()),
    sentence: (s) => s.charAt(0).toUpperCase() + s.slice(1),
    "as-spoken": (s) => s,
  };
  TK.applyCase = (s, c) => (CASES[c] || CASES["as-spoken"])(s);

  /** Apply a role's face and a tier spec ({weight, px, italic, case, color, tracking_em, depth, tint}). */
  TK.style = function (el, role, spec = {}) {
    const r = C.roles[role];
    const px = (spec.px || 60) * TK.k * (spec.scale || 1);
    Object.assign(el.style, {
      fontFamily: TK.family(role),
      fontWeight: String(spec.weight || r.weight || 400),
      fontStyle: spec.italic ? "italic" : "normal",
      fontSize: px + "px",
      lineHeight: String(spec.line_height || r.line_height || 1),
      letterSpacing: (spec.tracking_em != null ? spec.tracking_em : r.tracking_em || 0) + "em",
      color: spec.color || "#fffaf2",
      textShadow: TK.depth(spec.depth || "soft", spec.tint || "0,0,0"),
      whiteSpace: "nowrap",
    });
    if (spec.case && el.childElementCount === 0) el.textContent = TK.applyCase(el.textContent, spec.case);
    el.dataset.tkRole = role;
    return el;
  };

  /* ---------------- splitting (never used on connected scripts) ---------------- */
  const SCRIPT_ROLES = new Set(["elegant_script", "expressive_script"]);
  function split(el, by) {
    if (SCRIPT_ROLES.has(el.dataset.tkRole) && by === "chars")
      throw new Error("type-kit: per-letter animation breaks connected script; use handwriting / writeOn");
    const text = el.textContent;
    el.textContent = "";
    const parts = by === "chars" ? Array.from(text) : text.split(/(\s+)/);
    const units = [];
    for (const p of parts) {
      if (/^\s+$/.test(p)) { el.appendChild(document.createTextNode(p)); continue; }
      const s = document.createElement("span");
      s.style.display = "inline-block";
      s.textContent = p;
      el.appendChild(s);
      units.push(s);
    }
    return units;
  }
  TK.split = split;

  /* ---------------- animation presets ---------------- */
  // Each: (tl, el, t, o) → end time. `el` is an element (or array for word-level presets).
  const FT = (tl, el, from, to, t) => {
    tl.set(el, from, 0);
    tl.fromTo(el, from, { ...to, immediateRender: false }, snap(t));
  };
  const A = {};
  // Impact
  A.punchIn = (tl, el, t, o = {}) => { const d = o.dur || 0.26; FT(tl, el, { opacity: 0, scale: o.from || 1.55, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: d, ease: "expo.out" }, t); return t + d; };
  A.scalePop = (tl, el, t, o = {}) => { const d = o.dur || 0.42; FT(tl, el, { opacity: 0, scale: 0.35 }, { opacity: 1, scale: 1, duration: d, ease: "back.out(2.2)" }, t); return t + d; };
  A.impactBounce = (tl, el, t, o = {}) => { const d = o.dur || 0.62; FT(tl, el, { opacity: 0, yPercent: -70, scaleY: 1.18 }, { opacity: 1, yPercent: 0, scaleY: 1, duration: d, ease: "elastic.out(1, 0.6)" }, t); return t + d; };
  A.kineticWords = (tl, el, t, o = {}) => { const w = split(el, "words"), st = o.stagger || 0.09; w.forEach((u, i) => A.punchIn(tl, u, t + i * st, { dur: 0.22 })); return t + (w.length - 1) * st + 0.22; };
  // Helvetica
  A.minimalFade = (tl, el, t, o = {}) => { const d = o.dur || 0.3; FT(tl, el, { opacity: 0 }, { opacity: 1, duration: d, ease: "power2.out" }, t); return t + d; };
  A.cleanWordReveal = (tl, el, t, o = {}) => {
    const units = Array.isArray(el) ? el : split(el, "words"), st = o.stagger || 0.07, d = o.dur || 0.26;
    units.forEach((u, i) => FT(tl, u, { opacity: 0, yPercent: 38, filter: "blur(6px)" }, { opacity: 1, yPercent: 0, filter: "blur(0px)", duration: d, ease: "power3.out" }, o.times ? o.times[i] : t + i * st));
    return (o.times ? o.times[units.length - 1] : t + (units.length - 1) * st) + d;
  };
  A.captionSlide = (tl, el, t, o = {}) => { const d = o.dur || 0.32; FT(tl, el, { opacity: 0, x: -28 * TK.k }, { opacity: 1, x: 0, duration: d, ease: "power3.out" }, t); return t + d; };
  A.activeHighlight = (tl, el, t, o = {}) => { const d = o.dur || 0.12; FT(tl, el, { color: o.idle || "rgba(255,250,242,.5)" }, { color: o.color || "#ffd27a", duration: d, ease: "none" }, t); return t + d; };
  // Garamond
  A.editorialHighlight = (tl, el, t, o = {}) => {
    const d = o.dur || 0.5, ls = parseFloat(el.style.letterSpacing) || 0;
    FT(tl, el, { opacity: 0, yPercent: 45, letterSpacing: (ls + 0.08) + "em", clipPath: "inset(-20% -10% 100% -10%)" },
      { opacity: 1, yPercent: 0, letterSpacing: ls + "em", clipPath: "inset(-20% -10% -40% -10%)", duration: d, ease: "expo.out" }, t);
    return t + d;
  };
  A.elegantFade = (tl, el, t, o = {}) => { const d = o.dur || 0.7; FT(tl, el, { opacity: 0, y: 14 * TK.k, filter: "blur(5px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: "sine.out" }, t); return t + d; };
  A.serifAccent = (tl, el, t, o = {}) => { const d = o.dur || 0.45; FT(tl, el, { opacity: 0, scale: 1.18, rotation: -3 }, { opacity: 1, scale: 1, rotation: 0, duration: d, ease: "power3.out" }, t); return t + d; };
  // Cormorant Garamond
  A.luxuryReveal = (tl, el, t, o = {}) => {
    const d = o.dur || 1.0, ls = parseFloat(el.style.letterSpacing) || 0;
    FT(tl, el, { opacity: 0, letterSpacing: (ls + 0.32) + "em", filter: "blur(10px)" }, { opacity: 1, letterSpacing: ls + "em", filter: "blur(0px)", duration: d, ease: "power2.out" }, t);
    return t + d;
  };
  A.cinematicLetters = (tl, el, t, o = {}) => {
    const c = split(el, "chars"), st = o.stagger || 0.045, d = o.dur || 0.6;
    c.forEach((u, i) => FT(tl, u, { opacity: 0, yPercent: 30, filter: "blur(8px)" }, { opacity: 1, yPercent: 0, filter: "blur(0px)", duration: d, ease: "power3.out" }, t + i * st));
    return t + (c.length - 1) * st + d;
  };
  A.softTitle = (tl, el, t, o = {}) => { const d = o.dur || 0.9; FT(tl, el, { opacity: 0, scale: 1.05 }, { opacity: 1, scale: 1, duration: d, ease: "sine.out" }, t); return t + d; };
  // Scripts: whole-word masks only (the joins stay intact)
  const wipeDur = (el, o) => o.dur || Math.min(1.4, Math.max(0.5, el.textContent.length * 0.075));
  A.handwriting = (tl, el, t, o = {}) => {
    const d = wipeDur(el, o);
    FT(tl, el, { opacity: 1, clipPath: "inset(-40% 100% -40% -12%)", x: -6 * TK.k }, { opacity: 1, clipPath: "inset(-40% -12% -40% -12%)", x: 0, duration: d, ease: "power1.inOut" }, t);
    return t + d;
  };
  A.gracefulFade = (tl, el, t, o = {}) => { const d = o.dur || 0.8; FT(tl, el, { opacity: 0, y: 18 * TK.k, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: "sine.out" }, t); return t + d; };
  A.scriptFloat = (tl, el, t, o = {}) => {
    const end = A.gracefulFade(tl, el, t, o), hold = o.hold || 1.6, amp = (o.amp || 8) * TK.k;
    tl.fromTo(el, { y: 0 }, { y: -amp, duration: hold / 2, ease: "sine.inOut", yoyo: true, repeat: 1, immediateRender: false }, snap(end));
    return end;
  };
  // A soft leading edge sweeping left → right through a gradient mask (Blacksword's write-on)
  A.writeOn = (tl, el, t, o = {}) => {
    const d = wipeDur(el, o) * 1.1;
    el.style.webkitMaskImage = el.style.maskImage = "linear-gradient(90deg, #000 calc(var(--wo) - 14%), transparent var(--wo))";
    el.style.webkitMaskSize = el.style.maskSize = "100% 100%";
    FT(tl, el, { opacity: 1, "--wo": "-14%" }, { opacity: 1, "--wo": "118%", duration: d, ease: "power1.inOut" }, t);
    return t + d;
  };
  A.expressiveReveal = (tl, el, t, o = {}) => { const end = A.writeOn(tl, el, t, o); tl.fromTo(el, { scale: 1.08 }, { scale: 1, duration: end - t + 0.3, ease: "power2.out", immediateRender: false }, snap(t)); return end; };
  A.maskEntrance = (tl, el, t, o = {}) => { const d = o.dur || 0.6; FT(tl, el, { opacity: 1, yPercent: 60, clipPath: "inset(-40% -15% 100% -15%)" }, { opacity: 1, yPercent: 0, clipPath: "inset(-40% -15% -40% -15%)", duration: d, ease: "expo.out" }, t); return t + d; };
  // Rockwell
  A.editorialSlide = (tl, el, t, o = {}) => { const d = o.dur || 0.55; FT(tl, el, { opacity: 0, x: 70 * TK.k * (o.dir || 1) }, { opacity: 1, x: 0, duration: d, ease: "expo.out" }, t); return t + d; };
  A.staggeredHeadline = (tl, el, t, o = {}) => {
    const lines = el.children.length ? Array.from(el.children) : split(el, "words"), st = o.stagger || 0.09, d = o.dur || 0.5;
    lines.forEach((u, i) => FT(tl, u, { opacity: 0, yPercent: 90, clipPath: "inset(-10% -5% 100% -5%)" }, { opacity: 1, yPercent: 0, clipPath: "inset(-10% -5% -30% -5%)", duration: d, ease: "expo.out" }, t + i * st));
    return t + (lines.length - 1) * st + d;
  };
  A.structuredReveal = (tl, el, t, o = {}) => { const d = o.dur || 0.42; FT(tl, el, { opacity: 1, clipPath: "inset(-20% 100% -30% 0%)" }, { opacity: 1, clipPath: "inset(-20% -2% -30% 0%)", duration: d, ease: "steps(7)" }, t); return t + d; };
  TK.anim = A;
  TK.ANIMS = Object.keys(A);

  /** Exits: minimalFade | fastDrop | softFade. */
  TK.out = function (tl, els, t, kind = "minimalFade") {
    els = [].concat(els);
    const to = kind === "fastDrop" ? { opacity: 0, yPercent: 60, duration: 0.16, ease: "power2.in", stagger: 0.02 }
      : kind === "softFade" ? { opacity: 0, filter: "blur(6px)", duration: 0.45, ease: "sine.in" }
      : { opacity: 0, y: 10 * TK.k, duration: 0.2, ease: "power2.in", stagger: 0.015 };
    tl.to(els, to, snap(t));
    return t + to.duration;
  };

  /* ---------------- composed titles ---------------- */
  /** parts: [{ text, role, px, weight, italic, case, color, depth, tint, x, y, align, anim, at, opts, z }]
   *  x/y: anchor (align left|center|right; y is the baseline box top). Returns the elements. */
  TK.title = function (tl, parent, parts, t) {
    const host = typeof parent === "string" ? document.querySelector(parent) : parent;
    return parts.map((p) => {
      const e = document.createElement("div");
      e.textContent = p.text;
      e.className = "tk-part";
      e.style.position = "absolute";
      e.style.left = p.x + "px";
      e.style.top = p.y + "px";
      if (p.z != null) e.style.zIndex = p.z;
      host.appendChild(e);
      TK.style(e, p.role, p);
      const ax = p.align === "center" ? -50 : p.align === "right" ? -100 : 0;
      e.dataset.ax = ax;
      tl.set(e, { xPercent: ax }, 0);
      e.style.transformOrigin = p.align === "right" ? "100% 60%" : p.align === "center" ? "50% 60%" : "0% 60%";
      const anim = p.anim || C.roles[p.role].animations[0];
      A[anim](tl, e, p.at != null ? p.at : t, p.opts || {});
      return e;
    });
  };

  /* ---------------- 3D extruded type ---------------- */
  /** Stacked-layer extrusion for one hero word (Impact / heavy weights only; thin faces lose the
   *  illusion). Back layers are real DOM copies at 1–3 px steps — after hyperframes-animation
   *  rules/3d-text-depth-layers.md — so depth can grow on entry, which text-shadow cannot.
   *  o: { layers: 5, dx: 0, dy: 3, back: "120,40,8", alphaMax: .8, alphaStep: .12, grow: .45 }
   *  Returns the front element (style and animate it like any TK.title part). */
  TK.extrude = function (tl, front, t, o = {}) {
    const n = o.layers || 5, dx = (o.dx != null ? o.dx : 0) * TK.k, dy = (o.dy != null ? o.dy : 3) * TK.k;
    const host = front.parentNode, backs = [];
    for (let i = n - 1; i >= 1; i--) {
      const b = front.cloneNode(true);
      b.removeAttribute("id");
      const a = Math.max((o.alphaMax || 0.8) - i * (o.alphaStep || 0.12), 0.12);
      Object.assign(b.style, { color: `rgba(${o.back || "120,40,8"},${a})`, textShadow: "none", background: "none", webkitTextFillColor: "currentColor", zIndex: (front.style.zIndex || 0) - 1 });
      b.dataset.layer = i;
      host.insertBefore(b, front);
      backs.push(b);
    }
    const ax = +(front.dataset.ax || 0);   // same anchor as the front (TK.title alignment)
    tl.set(backs, { opacity: 0, xPercent: ax }, 0);
    backs.forEach((b) => {
      const i = +b.dataset.layer;
      tl.fromTo(b, { opacity: 0, x: 0, y: 0, xPercent: ax }, { opacity: 1, x: i * dx, y: i * dy, xPercent: ax, duration: o.grow || 0.45, ease: "power2.out", immediateRender: false }, snap(t + (n - 1 - i) * 0.03));
    });
    return { front, backs };
  };

  /* ---------------- captions ---------------- */
  /**
   * cues: [{ s, e, lines: [[{ w, s, c }]] }]  c: "a" accent word, "r" punch word (problem / warning)
   * opts: {
   *   preset: "MULTI_FONT_STORYTELLING" (any preset with body / accent / punch tiers),
   *   layout(cue, i) → { x, y, align: "left"|"right"|"center", style: "stack"|"line", tilt, skip }
   *       x = anchor x, y = bottom of the block (px, canvas space). Defaults: lower middle, alternating style.
   *   skip(cue) → true to hide (a headline already spells it)
   *   strip: regex of trailing punctuation to drop (default /[,.…]+$/)
   *   scale: multiplies every tier's size (e.g. 1.3 for a 16:9 film that is also cut to 9:16)
   * }
   * Rhythm the engine enforces: words land on their spoken time; accent / punch words own a line in a
   * stack (the size contrast), sit inline (~0.8×) in a line cue; blocks on a side tilt a few degrees
   * toward the subject (depth); the block drifts 1 % while it reads (never frozen).
   */
  TK.captions = function (tl, root, cues, opts = {}) {
    const host = typeof root === "string" ? document.querySelector(root) : root;
    const P = C.presets[opts.preset || "MULTI_FONT_STORYTELLING"];
    const tiers = { body: [P.roles.body, P.body], a: [P.roles.accent || P.roles.body, P.accent || P.body], r: [P.roles.punch || P.roles.accent || P.roles.body, P.punch || P.accent || P.body] };
    const anims = { body: P.animation.in, a: P.animation.accent_in || P.animation.in, r: P.animation.punch_in || P.animation.accent_in || P.animation.in };
    const strip = opts.strip || /[,.…]+$/;
    const lead = P.animation.lead_s != null ? P.animation.lead_s : 0.04;
    const made = [];
    cues.forEach((cue, i) => {
      if (opts.skip && opts.skip(cue, i)) return;
      const L = Object.assign({ x: TK.W / 2, y: TK.H - 70 * TK.k, align: "center", style: i % 2 ? "line" : "stack", tilt: null }, opts.layout ? opts.layout(cue, i) : {});
      if (L.skip) return;
      // classes: "a"/"go" → accent (payoff), "r"/"fr" → punch (problem); one key word per cue
      let keyed = false;
      const words = cue.lines.flat().map((w) => {
        let c = w.c === "go" ? "a" : w.c === "fr" ? "r" : w.c;
        if (c === "a" || c === "r") { if (keyed && opts.oneKey !== false) c = ""; keyed = true; }
        return { ...w, c };
      });
      const hasKey = keyed;
      const style = hasKey ? L.style : "line";
      const blk = document.createElement("div");
      blk.className = "tk-cap tk-" + style;
      Object.assign(blk.style, { position: "absolute", bottom: TK.H - L.y + "px", display: "flex", flexDirection: "column",
        alignItems: L.align === "left" ? "flex-start" : L.align === "right" ? "flex-end" : "center", gap: (style === "stack" ? 2 : 0) * TK.k + "px" });
      if (L.align === "left") blk.style.left = L.x + "px";
      else if (L.align === "right") blk.style.right = TK.W - L.x + "px";
      else { blk.style.left = L.x + "px"; blk.style.transform = "translateX(-50%)"; }
      const tilt = L.tilt != null ? L.tilt : L.align === "left" ? 7 : L.align === "right" ? -7 : 0;
      const inner = document.createElement("div");   // the 3D plane; GSAP animates the words inside it
      inner.style.cssText = `display:flex;flex-direction:column;align-items:inherit;transform:perspective(${1400 * TK.k}px) rotateY(${tilt}deg);transform-origin:${L.align === "right" ? "100%" : L.align === "left" ? "0%" : "50%"} 100%`;
      blk.appendChild(inner);
      host.appendChild(blk);
      // lines: in a stack every key word owns a line; in a line cue everything shares one
      const lines = [];
      let cur = null;
      for (const w of words) {
        const key = w.c === "a" || w.c === "r";
        if (style === "stack" && key) { lines.push({ key: true, words: [w] }); cur = null; continue; }
        if (!cur) { cur = { key: false, words: [] }; lines.push(cur); }
        cur.words.push(w);
      }
      const spans = [];
      for (const ln of lines) {
        const row = document.createElement("div");
        row.style.cssText = "display:flex;align-items:baseline;white-space:nowrap";
        row.style.gap = 0.26 * (P.body.px || 48) * TK.k * (opts.scale || 1) + "px";
        inner.appendChild(row);
        for (const w of ln.words) {
          const tier = w.c === "a" ? "a" : w.c === "r" ? "r" : "body";
          const [role, spec] = tiers[tier];
          const sp = document.createElement("span");
          sp.textContent = w.w.replace(strip, "");
          sp.style.display = "inline-block";
          row.appendChild(sp);
          const sc = (tier !== "body" && style === "line" ? 0.62 : 1) * (opts.scale || 1);
          const cs = tier === "body" ? (w === words[0] && spec.case === "sentence" ? "sentence" : "as-spoken") : spec.case;
          TK.style(sp, role, { ...spec, scale: sc, depth: tier === "r" ? "hard" : P.depth, tint: tier === "r" ? "74,11,6" : tier === "a" ? "120,50,8" : "0,0,0", case: cs });
          sp.style.transformOrigin = "50% 85%";
          spans.push({ sp, tier, at: Math.max(cue.s, (w.s != null ? w.s : cue.s) - lead) });
        }
      }
      // gap between rows: key rows sit tight on the small rows (optical leading)
      Array.from(inner.children).forEach((row, k) => { if (k) row.style.marginTop = (lines[k].key || lines[k - 1].key ? -0.02 : 0.02) * (P.accent ? P.accent.px : 60) * TK.k * (opts.scale || 1) + "px"; });
      tl.set(blk, { opacity: 0 }, 0);
      tl.set(blk, { opacity: 1 }, snap(cue.s - lead));
      for (const { sp, tier, at } of spans) A[anims[tier]](tl, sp, at, tier === "body" ? { dur: 0.24 } : {});
      tl.fromTo(inner, { y: 0 }, { y: -0.012 * TK.H, duration: Math.max(0.2, cue.e - cue.s), ease: "none", immediateRender: false }, snap(cue.s));
      const outAt = Math.max(cue.s + 0.25, cue.e - 0.14);
      tl.to(spans.map((x) => x.sp).reverse(), { opacity: 0, y: 12 * TK.k, filter: "blur(4px)", duration: 0.16, ease: "power2.in", stagger: 0.015 }, snap(outAt));
      tl.set(blk, { opacity: 0 }, snap(cue.e + 0.06));
      made.push(blk);
    });
    return made;
  };

  window.TK = TK;
})();
