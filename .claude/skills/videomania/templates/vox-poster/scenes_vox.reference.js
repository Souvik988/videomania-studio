// Bill Kaun Bharta Hai — Shotlin, 9:16. COLOUR VOX EDITORIAL build (2026-10-23, after the user's reference reel).
// Every frame is a designed poster: persistent chrome (header + spec footer), one kinetic editorial line in a fixed
// top zone (sans + script payoff + bold extended + Didone hero), cut-out photos breaking out of colour frames,
// 3D colour objects, product-label spec cards; transitions are focus pulls, irises and letterbox bars.
window.buildVox = function (tl, W, H, scene) {
  const FPS = 30, sn = (t) => Math.round(t * FPS) / FPS;
  const C = { cream: "#F3EDE2", paper: "#FBF7EF", navy: "#0F1A2E", cobalt: "#2B4DFF", tang: "#FF6A2B", butter: "#FFD45C", mint: "#3DDC97", ink: "#111522", label: "#F6F1E7" };
  const F = { didone: "'Bodoni Moda', serif", script: "'Pinyon Script', cursive", ext: "'Archivo', sans-serif", sans: "'VM Clean', 'Inter', sans-serif",
    mono: "'JetBrains Mono', monospace", round: "'Unbounded', sans-serif" };
  const glide = MK.bezier(0.45, 0, 0.15, 1);
  const V = (n) => "media/vox/" + n;
  const CA = (a = 2, k = 0.5) => `${-a}px 0 rgba(255,50,90,${k}), ${a}px 0 rgba(30,170,255,${k})`;
  const CAF = (a = 2, k = 0.45) => `drop-shadow(${-a}px 0 0 rgba(255,50,90,${k})) drop-shadow(${a}px 0 0 rgba(30,170,255,${k}))`;
  const E = (tag, css, parent, html) => {
    const d = document.createElement(tag);
    d.setAttribute("data-layout-allow-overlap", "");
    d.setAttribute("data-layout-allow-overflow", "");
    if (css) d.style.cssText = css;
    if (html != null) d.innerHTML = html;
    if (parent) (typeof parent === "string" ? document.querySelector(parent) : parent).appendChild(d);
    return d;
  };
  const FT = (t, from, to, at) => { gsap.set(t, from); tl.set(t, from, 0); tl.fromTo(t, { ...from }, { ...from, ...to, immediateRender: false }, sn(at)); };
  const FX = (t, from, to, at) => tl.fromTo(t, { ...from }, { ...to, immediateRender: false }, sn(at));
  const TO = (t, to, at) => tl.to(t, { ...to }, sn(at));
  const rng = (seed) => MK.rng(seed);

  // ───────────── stage: bg + scenes share one camera (focus pulls blur both) ─────────────
  const root = document.getElementById("root");
  const stage = E("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;z-index:1;transform-origin:50% 45%`, null);
  root.insertBefore(stage, root.firstChild);
  const bgHost = document.getElementById("bg"); bgHost.className = "layer"; bgHost.style.background = C.cream;
  stage.appendChild(bgHost);
  stage.appendChild(document.getElementById("world"));
  stage.appendChild(document.getElementById("scenes"));
  tl.set(stage, { filter: "blur(0px)", scale: 1 }, 0);

  // backgrounds: L = cream satin (photo), D = navy velvet (photo), G = cream + cobalt grid, B = electric cobalt
  const BG = {};
  const bgL = E("div", `position:absolute;inset:-60px;background:${C.cream} url(${V("bg_satin.jpg")}) center/cover`, bgHost);
  const bgD = E("div", `position:absolute;inset:-60px;background:${C.navy} url(${V("bg_velvet.jpg")}) center/cover`, bgHost);
  const bgG = E("div", `position:absolute;inset:0;background-color:${C.paper};background-image:linear-gradient(rgba(43,77,255,.16) 2px,transparent 2px),linear-gradient(90deg,rgba(43,77,255,.16) 2px,transparent 2px);background-size:90px 90px;background-position:-20px 30px`, bgHost);
  const bgB = E("div", `position:absolute;inset:0;background:radial-gradient(ellipse 90% 70% at 50% 45%,#3d5cff,${C.cobalt} 55%,#1a2fb8)`, bgHost);
  E("div", `position:absolute;inset:0;opacity:.18;background:radial-gradient(circle,#000 1.3px,transparent 1.9px) 0 0/12px 12px;mix-blend-mode:multiply`, bgB);
  Object.assign(BG, { L: bgL, D: bgD, G: bgG, B: bgB });
  // slow drift on the photo grounds so a ground is never frozen
  FX(bgL, { x: 0, y: 0, scale: 1.02 }, { x: -40, y: 30, scale: 1.08, duration: 53.2, ease: "none" }, 0);
  FX(bgD, { x: 0, y: 0, scale: 1.08 }, { x: 40, y: -30, scale: 1.02, duration: 53.2, ease: "none" }, 0);
  // initial ground set inline (no competing sets at t=0); later switches are timeline sets
  Object.entries(BG).forEach(([n, el]) => (el.style.opacity = n === "D" ? 1 : 0));
  const setBG = (at, k) => { if (at > 0) Object.entries(BG).forEach(([n, el]) => tl.set(el, { opacity: n === k ? 1 : 0 }, sn(at))); };

  // ───────────── transitions ─────────────
  const fx = E("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;z-index:45;pointer-events:none`, root);
  function focusPull(at, k = 16) {
    FX(stage, { filter: "blur(0px)", scale: 1 }, { filter: `blur(${k}px)`, scale: 1.035, duration: 0.17, ease: "power2.in" }, at - 0.17);
    FX(stage, { filter: `blur(${k}px)`, scale: 1.035 }, { filter: "blur(0px)", scale: 1, duration: 0.38, ease: "power3.out" }, at);
  }
  function iris(at, cx, cy, color, dur = 0.34) {
    const d = E("div", `position:absolute;inset:0;background:${color}`, fx);
    FT(d, { clipPath: `circle(0px at ${cx}px ${cy}px)` }, { clipPath: `circle(2300px at ${cx}px ${cy}px)`, duration: dur, ease: "power3.in" }, at - dur);
    // hide with a short tween (a zero-length set here did not stick in the sequential render)
    FT(d, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.1, ease: "none" }, at);
  }
  function flash(at, color = "#fff") {
    const d = E("div", `position:absolute;inset:0;background:${color}`, fx);
    FT(d, { opacity: 0 }, { opacity: 0.9, duration: 0.06, ease: "none" }, at - 0.06);
    FX(d, { opacity: 0.9 }, { opacity: 0, duration: 0.3, ease: "power2.out" }, at);
  }
  function letterbox(a, b, h = 210) {
    const t = E("div", `position:absolute;left:0;top:0;width:${W}px;height:${h}px;background:#05070d`, fx);
    const u = E("div", `position:absolute;left:0;bottom:0;width:${W}px;height:${h}px;background:#05070d`, fx);
    FT(t, { yPercent: -101 }, { yPercent: 0, duration: 0.45, ease: "power3.out" }, a);
    FT(u, { yPercent: 101 }, { yPercent: 0, duration: 0.45, ease: "power3.out" }, a);
    TO([t, u], { yPercent: (i) => (i ? 101 : -101), duration: 0.35, ease: "power2.in" }, b - 0.35);
  }

  // ───────────── chrome: header + spec footer (colour flips with the ground) ─────────────
  const chrome = E("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;z-index:35;pointer-events:none;color:${C.ink}`, root);
  const hdr = E("div", `position:absolute;left:60px;top:96px;width:520px;text-shadow:${CA(1.5, 0.35)}`, chrome,
    `<div style="display:flex;align-items:center;gap:12px;font:800 34px/1 ${F.ext};font-stretch:125%;letter-spacing:.02em"><img src="${V("ic_app.png")}" style="width:46px;height:46px;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.3))">SHOTLIN</div>
     <div style="margin-top:4px;font:700 12px/1.1 ${F.mono};letter-spacing:.06em;opacity:.8">© 2026 · D2C SYSTEMS</div>
     <div style="margin-top:8px;font:400 12px/1.35 ${F.mono};opacity:.62;width:470px">Online store system for Indian sellers. Android app, iOS app, website, advanced dashboard, cart recovery, delivery rules, analytics and marketing tools.</div>`);
  const counter = E("div", `position:absolute;right:62px;top:104px;font:italic 800 46px/1 ${F.ext};font-stretch:110%;text-shadow:${CA(2, 0.45)}`, chrome, "00001");
  const plus = E("div", `position:absolute;right:62px;top:170px;font:300 34px/1 ${F.sans};opacity:.7`, chrome, "+");
  const bar = (seed, w, h) => { const r = rng(seed); let x = 0, s = ""; while (x < w) { const bw = 1 + Math.floor(r() * 4); if (r() > 0.35) s += `<rect x="${x}" y="0" width="${bw}" height="${h}" fill="currentColor"/>`; x += bw + 1; } return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${s}</svg>`; };
  const qr = (seed, n = 25, px = 4) => {
    const r = rng(seed); let s = "";
    const finder = (x, y) => `<rect x="${x}" y="${y}" width="${7 * px}" height="${7 * px}" fill="currentColor"/><rect x="${x + px}" y="${y + px}" width="${5 * px}" height="${5 * px}" fill="${"var(--qrbg,#F6F1E7)"}"/><rect x="${x + 2 * px}" y="${y + 2 * px}" width="${3 * px}" height="${3 * px}" fill="currentColor"/>`;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const f = (i < 8 && j < 8) || (i < 8 && j > n - 9) || (i > n - 9 && j < 8); if (!f && r() > 0.52) s += `<rect x="${i * px}" y="${j * px}" width="${px}" height="${px}" fill="currentColor"/>`; }
    return `<svg width="${n * px}" height="${n * px}">${s}${finder(0, 0)}${finder((n - 7) * px, 0)}${finder(0, (n - 7) * px)}</svg>`;
  };
  const xbox = (w, h) => `<svg width="${w}" height="${h}"><rect x="1" y="1" width="${w - 2}" height="${h - 2}" fill="none" stroke="currentColor" stroke-width="2"/><path d="M1 1L${w - 1} ${h - 1}M${w - 1} 1L1 ${h - 1}" stroke="currentColor" stroke-width="1.5"/></svg>`;
  const star = (s) => `<svg width="${s}" height="${s}" viewBox="0 0 40 40"><path d="M20 2L20 38M2 20L38 20M7 7L33 33M33 7L7 33" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/></svg>`;
  const globe = (s) => `<svg width="${s}" height="${s}" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="20" cy="20" r="18"/><ellipse cx="20" cy="20" rx="8" ry="18"/><ellipse cx="20" cy="20" rx="18" ry="7"/><path d="M2 20H38M20 2V38"/></svg>`;
  const ftr = E("div", `position:absolute;left:60px;top:1296px;width:960px;height:112px;box-sizing:border-box;border:2px solid currentColor;display:flex;align-items:center;gap:20px;padding:0 20px;opacity:.82;text-shadow:${CA(1.2, 0.3)}`, chrome,
    `<div style="display:flex;flex-direction:column;gap:8px"><span style="background:currentColor;padding:2px 10px;font:800 20px ${F.ext}"><span class="yr" style="color:var(--chromebg,${C.cream})">2026</span></span>${xbox(130, 40)}</div>
     <div style="height:72px">${bar(7, 150, 72)}</div>
     <div style="flex:1;font:400 11px/1.4 ${F.mono};opacity:.8">© SHOTLIN SYSTEMS<br>BUILD YOUR STORE · APPS · WEBSITE<br>DASHBOARD · RECOVERY · MARKETING</div>
     <div style="font:800 15px/1.1 ${F.ext};font-stretch:125%;text-align:right">BILL KAUN<br>BHARTA HAI?</div>
     <div>${star(58)}</div>`);
  FT(hdr, { opacity: 0.4, y: -14 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, 0.0);
  FT(ftr, { opacity: 0.35, y: 20 }, { opacity: 0.82, y: 0, duration: 0.4, ease: "power3.out" }, 0.0);
  const chromeMode = (at, dark, n) => {
    tl.set(chrome, { color: dark ? C.cream : C.ink, "--chromebg": dark ? C.navy : C.cream }, sn(at));
    tl.set(counter, { innerText: String(n).padStart(5, "0") }, sn(at));
  };
  tl.set(chrome, { color: C.cream }, 0);

  // ───────────── kinetic editorial line (the film's caption home: one fixed top zone) ─────────────
  const textLayer = E("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;z-index:36;pointer-events:none`, root);
  const ROLE = {
    s: (c) => `font:500 54px/1.15 ${F.sans};color:${c};letter-spacing:-.01em`,
    b: (c) => `font:800 60px/1.05 ${F.ext};font-stretch:125%;color:${c};text-transform:uppercase;letter-spacing:-.005em`,
    c: (c, t) => `font:400 ${Math.round(132 * Math.min(1, 8 / Math.max(4, (t || '').length)))}px/0.78 ${F.script};color:${c};padding:0 14px 0 2px`,
    d: (c) => `font:900 150px/0.9 ${F.didone};color:${c};text-transform:uppercase;letter-spacing:-.01em`,
    h: (c) => `font:600 54px/1.15 ${F.sans};color:${C.ink};background:linear-gradient(${C.butter},${C.butter}) 0 88%/0% 42% no-repeat;padding:0 4px`,
  };
  function kline(parts, o) {
    const { y = 290, dark = false, out, w = 960, align = "center", x = 60 } = o;
    const ink = dark ? C.cream : C.ink;
    const box = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;display:flex;flex-wrap:wrap;justify-content:${align === "center" ? "center" : "flex-start"};align-items:baseline;column-gap:18px;row-gap:2px`, o.parent || textLayer);
    const spans = parts.map(([txt, role, t, col]) => {
      const sp = E("span", `display:inline-block;white-space:nowrap;${ROLE[role](col || ink, txt)};text-shadow:${role === "h" ? "none" : CA(role === "c" ? 2.5 : 2, dark ? 0.55 : 0.4)}`, box, txt);
      const at = t - 0.04;
      if (role === "s") FT(sp, { opacity: 0, y: 26, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.38, ease: "power3.out" }, at);
      else if (role === "b") FT(sp, { opacity: 0, scale: 1.3, filter: "blur(8px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.26, ease: "expo.out" }, at);
      else if (role === "c") FT(sp, { opacity: 0, clipPath: "inset(-20% 100% -30% 0%)", x: -10 }, { opacity: 1, clipPath: "inset(-20% -30% -30% 0%)", x: 0, duration: 0.6, ease: "power2.out" }, at);
      else if (role === "d") FT(sp, { opacity: 0, letterSpacing: "0.25em", filter: "blur(16px)" }, { opacity: 1, letterSpacing: "-0.01em", filter: "blur(0px)", duration: 0.6, ease: "expo.out" }, at);
      else if (role === "h") { FT(sp, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, at); FX(sp, { backgroundSize: "0% 42%" }, { backgroundSize: "100% 42%", duration: 0.35, ease: "power2.out" }, at + 0.12); }
      return sp;
    });
    if (out != null) TO(spans.slice().reverse(), { opacity: 0, y: -16, filter: "blur(10px)", duration: 0.22, ease: "power2.in", stagger: 0.02 }, out - 0.22);
    FX(box, { y: 0 }, { y: -10, duration: Math.max(0.5, (out || parts[parts.length - 1][2] + 2) - parts[0][2]), ease: "none" }, parts[0][2]);
    return { box, spans };
  }
  // hero Didone word with scan stripes and RGB fringe (the reference's NOBODY)
  function hero(parent, text, x, y, size, color, at, o = {}) {
    const d = E("div", `position:absolute;left:${x}px;top:${y}px;${o.w ? `width:${o.w}px;text-align:center;` : ""}white-space:nowrap;font:900 ${size}px/0.88 ${F.didone};font-variation-settings:"opsz" 6;text-transform:uppercase;letter-spacing:-.015em;
      color:transparent;background:repeating-linear-gradient(0deg,${color} 0 ${size * 0.034}px,${color}cc ${size * 0.034}px ${size * 0.05}px);-webkit-background-clip:text;background-clip:text;
      filter:${CAF(3, 0.7)} drop-shadow(0 ${size * 0.04}px ${size * 0.08}px rgba(0,0,0,.35))`, parent, text);
    FT(d, { opacity: 0, scale: 1.25, letterSpacing: "0.2em", filter: `blur(18px)` }, { opacity: 1, scale: 1, letterSpacing: "-0.015em", filter: `blur(0px)`, duration: 0.55, ease: "expo.out" }, at);
    tl.set(d, { filter: `${CAF(3, 0.7)} drop-shadow(0 ${size * 0.04}px ${size * 0.08}px rgba(0,0,0,.35))` }, sn(at + 0.56));
    FX(d, { x: 0 }, { x: 4, duration: 0.05, yoyo: true, repeat: 3, ease: "none" }, at + 0.1);
    return d;
  }

  // ───────────── material ─────────────
  function frame(parent, x, y, w, h, color, at, o = {}) {
    const f = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;background:${color};border-radius:${o.r ?? 10}px;overflow:hidden;
      box-shadow:0 30px 60px rgba(10,15,40,.35), inset 0 0 0 2px rgba(255,255,255,.12)`, parent);
    if (o.img) E("img", `position:absolute;inset:0;width:100%;height:100%;object-fit:cover;${o.imgCss || ""}`, f).src = V(o.img);
    if (o.grid) E("div", `position:absolute;inset:0;opacity:.25;background-image:linear-gradient(rgba(255,255,255,.5) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.5) 1px,transparent 1px);background-size:44px 44px`, f);
    FT(f, { clipPath: o.open || "inset(50% 0% 50% 0%)", opacity: 1 }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "expo.out" }, at);
    return f;
  }
  function cut(parent, name, x, y, w, at, o = {}) {
    const wrap = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;z-index:${o.z || 3};transform-origin:50% 90%`, parent);
    const img = E("img", `display:block;width:100%;filter:drop-shadow(0 26px 30px rgba(10,15,40,.38)) ${CAF(2, 0.35)}`, wrap); img.src = V(name + ".png");
    if (at != null) FT(wrap, { opacity: o.live ? 1 : 0, y: o.dy ?? 90, filter: `blur(${o.live ? 3 : 14}px)`, scale: 1.04 }, { opacity: 1, y: 0, filter: "blur(0px)", scale: 1, duration: 0.6, ease: "power3.out" }, at);
    wrap.img = img;
    return wrap;
  }
  function obj(parent, name, x, y, w, at, o = {}) {
    const wrap = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;z-index:${o.z || 4}`, parent);
    if (o.ring) {
      const r = E("div", `position:absolute;left:${-w * 0.15}px;top:${-w * 0.15}px;width:${w * 1.3}px;height:${w * 1.3}px;border-radius:50%;border:3px dotted ${o.ring};opacity:.85`, wrap);
      FT(r, { rotation: 0, scale: 0.6, opacity: 0 }, { rotation: 90, scale: 1, opacity: 0.85, duration: 4, ease: "none" }, at);
    }
    const inner = E("div", ``, wrap);
    const img = E("img", `display:block;width:100%;position:relative;filter:drop-shadow(0 24px 26px rgba(10,15,40,.38)) ${CAF(1.5, 0.3)}`, inner); img.src = V(name + ".png");
    if (at != null) FT(inner, { opacity: 0, scale: 0.4, rotation: o.r ?? -18, y: 40, filter: "blur(10px)" }, { opacity: 1, scale: 1, rotation: 0, y: 0, filter: "blur(0px)", duration: 0.55, ease: "back.out(1.7)" }, at);
    if (at != null && o.float !== false) FX(img, { y: 0, rotation: 0 }, { y: -14, rotation: 2, duration: 1.6, yoyo: true, repeat: 3, ease: "sine.inOut" }, at + 0.55);
    wrap.inner = inner;
    return wrap;
  }
  // product-label spec card (the reference's APPLE INC 004 / IPHONE cards), in the film's colours
  function spec(parent, o) {
    const { x, y, w, h, title, num, sub = "", accent = C.tang, glyph = "S", img, at, seed = 3, kind = "label", foot = "", numSize } = o;
    const card = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;box-sizing:border-box;border-radius:22px;background:${C.label};color:${C.ink};
      padding:${w * 0.03}px;box-shadow:0 34px 70px rgba(10,15,40,.4), inset 0 0 0 2px rgba(17,21,34,.15);--qrbg:${C.label};overflow:hidden;filter:${CAF(1.4, 0.3)}`, parent);
    const u = w / 900;
    E("div", `display:flex;align-items:center;gap:${16 * u}px`, card,
      `<div style="width:${96 * u}px;height:${96 * u}px;border-radius:${10 * u}px;background:${accent};display:flex;align-items:center;justify-content:center;font:900 ${58 * u}px ${F.round};color:${C.ink}">${glyph}</div>
       <div style="flex:1;min-width:0"><div style="font:900 ${66 * u * Math.min(1, 11 / title.length)}px/0.95 ${F.ext};font-stretch:125%;letter-spacing:-.01em;white-space:nowrap">${title}</div>
       <div style="display:flex;gap:${10 * u}px;align-items:center;margin-top:${6 * u}px;height:${34 * u}px;overflow:hidden">${bar(seed, 220 * u, 34 * u)}<span style="font:700 ${13 * u}px/1.1 ${F.mono};opacity:.7">${sub}</span></div></div>
       <div style="font:900 ${50 * u}px ${F.sans}">↗</div>`);
    if (num != null) E("div", `display:flex;align-items:center;gap:${18 * u}px;margin-top:${10 * u}px`, card,
      `<div class="num" style="font:900 ${(numSize || 150) * u}px/0.95 ${F.round};letter-spacing:-.03em;white-space:nowrap">${num}</div>${globe(90 * u)}<div style="flex:1"></div><div style="font:700 ${16 * u}px/1.2 ${F.mono};text-align:right;opacity:.75">CE · A1<br>${foot}</div>`);
    let well = null;
    if (kind === "product") {
      well = E("div", `position:relative;margin-top:${14 * u}px;height:${h - (num != null ? 520 : 330) * u}px;border-radius:${12 * u}px;overflow:hidden;background:${accent}`, card);
      E("div", `position:absolute;inset:0;opacity:.25;background-image:linear-gradient(rgba(17,21,34,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(17,21,34,.35) 1px,transparent 1px);background-size:${40 * u}px ${40 * u}px`, well);
      if (img) E("img", `position:absolute;inset:0;width:100%;height:100%;object-fit:cover`, well).src = V(img);
    }
    E("div", `display:flex;align-items:flex-end;gap:${14 * u}px;margin-top:${12 * u}px`, card,
      `<div style="flex:1"><div style="height:${34 * u}px;overflow:hidden">${bar(seed + 9, 560 * u, 34 * u)}</div>
         <div style="font:400 ${11 * u}px/1.35 ${F.mono};opacity:.65;margin-top:${6 * u}px">SHOTLIN SYSTEMS · ${title} · MADE FOR INDIAN SELLERS · ${sub}</div></div>
       <div style="transform:scale(${u});transform-origin:100% 100%">${qr(seed + 21, 25, 4)}</div>`);
    if (at != null) FT(card, { opacity: 0, y: 160, rotation: 4, filter: "blur(14px)" }, { opacity: 1, y: 0, rotation: 0, filter: `blur(0px) ${CAF(1.4, 0.3)}`, duration: 0.6, ease: "expo.out" }, at);
    card.well = well;
    return card;
  }
  function phone(parent, x, y, w, h, color = C.navy) {
    const ph = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${w * 0.14}px;background:${color};
      box-shadow:0 40px 80px rgba(10,15,40,.45), inset 0 0 0 3px rgba(255,255,255,.18)`, parent);
    const scr = E("div", `position:absolute;left:${w * 0.035}px;top:${w * 0.035}px;right:${w * 0.035}px;bottom:${w * 0.035}px;border-radius:${w * 0.11}px;overflow:hidden;background:#fff`, ph);
    E("div", `position:absolute;left:50%;top:${w * 0.05}px;width:${w * 0.28}px;height:${w * 0.075}px;margin-left:${-w * 0.14}px;border-radius:40px;background:${color};z-index:9`, ph);
    return { ph, scr };
  }
  function mkScene(id, a, b, fn) { const s = E("div", "", "#scenes"); s.className = "scene"; s.id = id; scene(id, a, b, fn); return s; }
  const push = (el, a, b, k = 1.05) => FX(el, { scale: 1 }, { scale: k, duration: b - a, ease: "sine.inOut" }, a);
  const brackets = (parent, bx, at, color) => MK.brackets(tl, parent, bx, at, { color, size: 56, stroke: 8 });
  const tagMono = (parent, text, x, y, at, bgc = C.butter, fg = C.ink) => {
    const d = E("div", `position:absolute;left:${x}px;top:${y}px;padding:10px 18px;background:${bgc};color:${fg};font:800 26px ${F.mono};letter-spacing:.12em;white-space:nowrap;box-shadow:0 12px 24px rgba(0,0,0,.25)`, parent, text);
    FT(d, { opacity: 0, clipPath: "inset(0 100% 0 0)" }, { opacity: 1, clipPath: "inset(0 0% 0 0)", duration: 0.32, ease: "steps(8)" }, at);
    return d;
  };

  // ═════════ A 0–2.9 · navy velvet · HOOK: AJEEB ═════════
  setBG(0, "D"); chromeMode(0, true, 1);
  mkScene("v01", 0, 2.92, (s) => {
    const cam = E("div", `position:absolute;inset:0;transform-origin:50% 60%`, s); push(cam, 0, 2.9, 1.06);
    kline([["Online", "s", 0.35], ["shopping", "b", 1.25, C.butter], ["mein ek", "s", 1.61]], { y: 268, dark: true, out: 2.85 });
    hero(cam, "AJEEB", 0, 370, 250, C.butter, 1.87, { w: W });
    kline([["scene hai,", "c", 2.27, C.cream]], { y: 590, dark: true, out: 2.85 });
    frame(cam, 230, 820, 620, 440, C.tang, 0.0, { grid: true, open: "inset(14% 0% 14% 0%)" });
    const k = cut(cam, "cut_keeper_receipt", 250, 720, 580, 0.0, { dy: 70, live: true });
    obj(cam, "obj_receipt", 760, 640, 230, 0.15, { ring: C.butter, r: 20 });
    // the question, big, on frame 0's story: who pays?
    const plate = E("div", `position:absolute;left:70px;top:640px;padding:14px 22px 16px;background:${C.butter};color:${C.ink};border-radius:10px;z-index:9;box-shadow:0 18px 36px rgba(0,0,0,.4);transform-origin:20% 50%`, cam,
      `<div style="font:800 24px ${F.mono};letter-spacing:.16em">BILL · PAID BY</div><div style="font:900 84px/0.95 ${F.round};color:${C.tang};letter-spacing:.04em">? ? ?</div>`);
    FT(plate, { opacity: 0, scale: 2, rotation: 6 }, { opacity: 1, scale: 1, rotation: -5, duration: 0.2, ease: "expo.out" }, 0.62);
    FX(plate, { rotation: -5 }, { rotation: -3, duration: 0.6, ease: "elastic.out(1,0.35)" }, 0.82);
    // the AJEEB boom shakes the frame
    [[10, -4], [-12, 5], [8, -3], [-5, 2], [0, 0]].forEach(([x, r], i) => tl.set(cam, { x, rotation: r * 0.2 }, sn(1.87 + i * 0.034)));
    TO(k, { y: -12, duration: 1.6, ease: "sine.inOut" }, 0.9);
  });
  gsap.set("#v01", { opacity: 1, visibility: "visible" }); tl.fromTo("#v01", { opacity: 1, visibility: "visible" }, { opacity: 1, visibility: "visible", duration: 0.05, immediateRender: true }, 0); // visible on frame 0 itself, even after a backward seek
  focusPull(2.88); setBG(2.88, "L"); chromeMode(2.88, false, 2);

  // ═════════ B 2.88–7.4 · cream satin · customer shops / shopkeeper pays ═════════
  mkScene("v02", 2.88, 7.42, (s) => {
    kline([["Shopping", "c", 3.15, C.cobalt], ["customer", "b", 3.61], ["karta hai,", "s", 4.01]], { y: 290, out: 4.9 });
    const left = E("div", `position:absolute;inset:0;transform-origin:0% 75%`, s);
    frame(left, 110, 700, 560, 520, C.cobalt, 2.95, { img: "photo_market.jpg", imgCss: "opacity:.5;mix-blend-mode:luminosity" });
    cut(left, "cut_shopper_walk", 420, 640, 330, 3.45, { z: 2 });
    cut(left, "cut_shopper_phone", 120, 540, 540, 3.12, { z: 3 });
    const cart = obj(left, "obj_cart", 690, 520, 300, 3.6, { ring: C.tang });
    push(left, 3.0, 4.9, 1.04);
    TO(left, { x: -20, y: -90, scale: 0.6, duration: 0.6, ease: glide }, 4.93);
    kline([["lekin kabhi kabhi", "s", 4.93], ["bill", "c", 5.77, C.tang], ["dukaandaar", "b", 6.19, C.tang], ["bharta hai,", "s", 6.69]], { y: 290, out: 7.3 });
    frame(s, 560, 780, 440, 440, C.tang, 5.35, { grid: true });
    const keeper = cut(s, "cut_keeper_receipt", 560, 640, 440, 5.47);
    // the bill: a mini spec label flies from the cart (customer side) onto the shopkeeper
    const bill = E("div", `position:absolute;left:330px;top:640px;width:250px;padding:16px 18px;border-radius:12px;background:${C.label};box-shadow:0 20px 40px rgba(0,0,0,.3);z-index:8;--qrbg:${C.label}`, s,
      `<div style="font:900 44px/1 ${F.ext};font-stretch:125%;color:${C.ink}">BILL</div><div style="height:26px;overflow:hidden;color:${C.ink};margin-top:6px">${bar(41, 210, 26)}</div>
       <div style="font:800 18px ${F.mono};color:${C.tang};margin-top:6px">PAID BY: ?</div>`);
    FT(bill, { opacity: 0, scale: 0.4, x: 0, y: 0, rotation: -20 }, { opacity: 1, scale: 0.9, rotation: -6, duration: 0.35, ease: "back.out(2)" }, 5.77);
    FX(bill, { x: 0, rotation: -6, scale: 0.9 }, { x: 380, rotation: 8, scale: 1, duration: 0.5, ease: "power2.inOut" }, 6.1);
    FX(bill, { y: 0 }, { y: -110, duration: 0.22, ease: "power2.out" }, 6.1);
    FX(bill, { y: -110 }, { y: 300, duration: 0.3, ease: "power2.in" }, 6.32);
    tl.set(bill.lastElementChild, { innerText: "PAID BY: ?" }, 0); tl.set(bill.lastElementChild, { innerText: "PAID BY: DUKAANDAAR" }, sn(6.62));
    FX(bill, { scale: 1.12 }, { scale: 1, duration: 0.2, ease: "expo.out" }, 6.62);
    push(keeper, 5.5, 7.3, 1.05);
  });
  iris(7.36, 780, 960, C.cobalt); setBG(7.36, "B"); chromeMode(7.36, true, 3);

  // ═════════ C 7.36–8.45 · electric cobalt · KAISE? ═════════
  mkScene("v03", 7.36, 8.47, (s) => {
    const d = cut(s, "cut_keeper_despair", 190, 660, 700, 7.38, { dy: 60 });
    hero(s, "KAISE?", 0, 420, 228, C.butter, 7.5, { w: W });
    tagMono(s, "QUESTION · 001", 60, 300, 7.55, C.ink, C.butter);
    push(s, 7.4, 8.45, 1.06);
    TO(s.children, { opacity: 0, duration: 0.15, ease: "power2.in" }, 8.28);
  });
  focusPull(8.45); setBG(8.45, "G"); chromeMode(8.45, false, 4);

  // ═════════ D 8.45–12.9 · cobalt grid paper · ad → customer → cart → gaayab ═════════
  mkScene("v04", 8.45, 12.92, (s) => {
    kline([["Aap", "s", 8.53], ["Facebook", "b", 8.67, C.cobalt], ["pe", "s", 9.07], ["ad", "c", 9.25, C.tang], ["chalao,", "s", 9.43]], { y: 290, out: 10.05 });
    const card = mock(s, "mk_ad", 330, 510, 520, 8.48, { ry: 24, hold: 1.5 });
    const fb = E("div", `position:absolute;left:770px;top:540px;width:120px;height:120px;border-radius:50%;background:#1877F2;z-index:10;box-shadow:0 16px 30px rgba(24,119,242,.45);display:flex;align-items:center;justify-content:center`, s,
      `<svg viewBox="0 0 24 24" width="74" height="74"><path fill="#fff" d="M14 8h3V4h-3c-2.8 0-4.5 1.8-4.5 4.6V11H7v4h2.5v9h4v-9h3l.5-4h-3.5V9c0-.6.4-1 1-1z"/></svg>`);
    FT(fb, { opacity: 0, scale: 0.2, rotation: -40 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2)" }, 8.67);
    TO(fb, { y: -1300, duration: 0.4, ease: "expo.in" }, 9.95);
    const spTag = tagMono(s, "SPONSORED · AD 001", 470, 470, 9.25, C.cobalt, "#fff"); spTag.style.zIndex = 9;
    const mega = obj(s, "obj_megaphone", 10, 840, 380, 8.67, { r: -24, z: 6 });
    const coins = obj(s, "obj_coins", 800, 1000, 220, 9.0, { float: false, z: 7 });
    FX(coins, { x: 0, y: 0, scale: 1, opacity: 1 }, { x: -560, y: -60, scale: 0.25, opacity: 0, duration: 0.45, ease: "power2.in" }, 9.4);
    TO([card, mega, spTag], { y: -1300, duration: 0.4, ease: "expo.in", stagger: 0.03 }, 9.95);
    // the store in a phone; the customer walks in; the cart fills
    kline([["customer", "c", 10.13, C.cobalt], ["aaye,", "s", 10.51], ["cart", "b", 11.19, C.tang], ["bhare,", "s", 11.35]], { y: 290, out: 11.98 });
    const { ph, scr } = phone(s, 330, 540, 440, 740, C.navy);
    FT(ph, { opacity: 0, y: 500, rotation: 8 }, { opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: "expo.out" }, 10.05);
    E("div", `height:72px;background:${C.cobalt};color:#fff;font:900 30px/72px ${F.ext};font-stretch:125%;padding-left:24px;margin-top:0;padding-top:30px`, scr, "YOUR STORE");
    const tiles = ["Kurta", "Saree", "Juttis", "Bangles"].map((n, i) => {
      const t = E("div", `position:absolute;left:${16 + (i % 2) * 196}px;top:${118 + Math.floor(i / 2) * 280}px;width:184px;height:264px;border-radius:16px;overflow:hidden;background:${[C.tang, C.butter, C.cobalt, C.mint][i]}`, scr,
        `<div style="position:absolute;left:0;right:0;bottom:0;height:96px;background:#fff;padding:10px 12px;box-sizing:border-box">
           <div style="font:800 22px ${F.sans};color:${C.ink}">${n}</div><div class="btn" style="margin-top:6px;height:40px;border-radius:10px;background:${C.ink};color:#fff;font:800 17px/40px ${F.sans};text-align:center">Add to cart</div></div>`);
      FT(t, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }, 10.2 + i * 0.06);
      return t;
    });
    const shopper = cut(s, "cut_shopper_phone", 20, 760, 380, 10.13, { z: 6, dy: 0 });
    FX(shopper, { x: -420 }, { x: 0, duration: 0.5, ease: "power3.out" }, 10.13);
    const cart = obj(s, "obj_cart", 700, 900, 330, 11.19, { ring: C.tang, z: 7 });
    [0, 1, 3].forEach((k, i) => FX(tiles[k].querySelector(".btn"), { scale: 1, background: C.ink }, { scale: 0.9, background: C.mint, duration: 0.08, ease: "power2.out" }, 11.19 + i * 0.13));
    // gaayab: the customer glitches out (RGB slice jitter on twos), a dashed ghost stays
    kline([["aur", "s", 12.01], ["gaayab,", "c", 12.19, C.tang]], { y: 290, out: 12.85 });
    const ghost = E("div", `position:absolute;left:40px;top:780px;width:330px;height:430px;border:5px dashed ${C.tang};border-radius:24px;z-index:5`, s);
    FT(ghost, { opacity: 0 }, { opacity: 1, duration: 0.12 }, 12.42);
    const jit = [[18, 0.6, "hue-rotate(60deg)"], [-26, 1, "none"], [34, 0.4, "hue-rotate(-80deg)"], [-12, 0.7, "invert(.2)"], [40, 0.2, "none"], [0, 0, "none"]];
    jit.forEach(([dx, op, f], i) => tl.set(shopper, { x: dx, opacity: op, filter: `${f} blur(${i}px)`, skewX: dx / 4 }, sn(12.19 + i * 0.05)));
    TO([ph, cart, ghost], { y: 1400, duration: 0.4, ease: "power2.in" }, 12.62);
  });
  focusPull(12.9); setBG(12.9, "D"); chromeMode(12.9, true, 5);

  // ═════════ E 12.9–16.9 · navy velvet · money burns → ORDER 0 → lekin ek second ═════════
  mkScene("v05", 12.9, 16.92, (s) => {
    kline([["Ad ka", "s", 12.97], ["paisa", "b", 13.35, C.tang], ["gaya,", "c", 13.65, C.butter]], { y: 290, dark: true, out: 14.2 });
    const burn = obj(s, "obj_money_burn", 230, 520, 620, 12.95, { r: 14, ring: C.tang });
    const spend = tagMono(s, "AD SPEND · ₹ ? ? ?", 300, 1060, 13.35, C.tang, C.ink); spend.style.zIndex = 9;
    TO(spend, { y: -900, opacity: 0, duration: 0.35, ease: "expo.in" }, 14.05);
    FX(burn, { y: 0, rotation: 0 }, { y: -80, rotation: -6, duration: 0.8, ease: "sine.inOut" }, 13.2);
    TO(burn, { y: -900, filter: "blur(16px)", opacity: 0, duration: 0.35, ease: "expo.in" }, 14.05);
    kline([["order", "b", 14.27, C.cream]], { y: 300, dark: true, out: 15.6 });
    const zero = hero(s, "0", 0, 380, 760, C.tang, 14.61, { w: W });
    const lab = spec(s, { x: 250, y: 1030, w: 580, h: 210, title: "ORDERS", sub: "TODAY · LIVE", accent: C.tang, glyph: "0", at: 14.72, seed: 19 });
    push(s, 14.3, 15.6, 1.05);
    // lekin ek second: cinema bars, time freezes, the abandoned cart waits in a spotlight
    letterbox(15.62, 16.92);
    TO([zero, lab], { scale: 0.7, opacity: 0, filter: "blur(16px)", duration: 0.35, ease: "power2.in" }, 15.62);
    kline([["Lekin", "s", 15.66], ["ek second,", "c", 15.95, C.butter]], { y: 380, dark: true, out: 16.88 });
    const spot = E("div", `position:absolute;left:190px;top:700px;width:700px;height:620px;background:radial-gradient(ellipse at 50% 60%,rgba(255,212,92,.35),transparent 65%)`, s);
    FT(spot, { opacity: 0 }, { opacity: 1, duration: 0.5 }, 15.9);
    obj(s, "obj_cart", 360, 760, 360, 16.0, { ring: C.butter, z: 6 });
  });
  focusPull(16.9); setBG(16.9, "L"); chromeMode(16.9, false, 6);

  // ═════════ F 16.9–24.4 · cream satin · abandoned cart → reminder → order → profit pakka? ═════════
  mkScene("v06", 16.9, 24.42, (s) => {
    kline([["Agar aap uska", "s", 16.88], ["abandoned", "c", 17.57, C.tang], ["cart", "b", 18.17], ["dekh sako,", "s", 18.51]], { y: 290, out: 19.42 });
    const g = E("div", `position:absolute;inset:0;transform-origin:50% 62%`, s);
    frame(g, 130, 640, 820, 600, C.navy, 16.95, { grid: true });
    const cart = obj(g, "obj_cart", 290, 700, 500, 17.0, { float: false, z: 4 });
    const mag = obj(g, "obj_magnifier", 620, 980, 330, 17.2, { z: 6 });
    FX(mag, { x: 0, y: 0 }, { x: -300, y: -200, duration: 1.6, ease: "sine.inOut" }, 17.75);
    brackets(g, { x: 270, y: 690, w: 540, h: 520 }, 17.57, C.butter);
    tagMono(g, "ABANDONED · 001", 150, 600, 17.6, C.tang, C.ink);
    // digital zoom punch on "cart"
    [1.0, 1.12, 1.22].forEach((k, i) => tl.set(g, { scale: k }, sn(18.17 + i * 0.07)));
    TO(g, { x: -1200, scale: 1, duration: 0.42, ease: "expo.in" }, 19.25);
    kline([["aur", "s", 19.47], ["reminder", "c", 19.61, C.cobalt], ["bhej sako toh,", "s", 20.13]], { y: 290, out: 21.02 });
    const kp = cut(s, "cut_keeper_phone", 520, 600, 500, 19.45);
    const chat = mock(s, "mk_chat", 40, 560, 460, 19.47, { ry: 22, hold: 2 });
    obj(s, "ic_bell", 400, 470, 150, 19.62, { r: -30, z: 9, ring: C.butter });
    const note = E("div", `position:absolute;left:40px;top:600px;width:520px;border-radius:30px;background:rgba(255,255,255,.96);box-shadow:0 24px 50px rgba(10,15,40,.35);padding:18px 22px;display:flex;gap:16px;align-items:center;z-index:12;box-sizing:border-box`, s,
      `<img src="${V("ic_app.png")}" style="width:78px;height:78px;object-fit:contain">
       <div style="flex:1"><div style="display:flex;justify-content:space-between;font:800 22px ${F.sans};color:${C.ink}"><span>Shotlin</span><span style="opacity:.5;font-weight:600">now</span></div>
       <div style="font:700 26px/1.25 ${F.sans};color:${C.ink};margin-top:4px">Aapka cart wait kar raha hai 🛒</div>
       <div style="font:600 22px ${F.sans};color:${C.cobalt};margin-top:4px">Order complete karein →</div></div>`.replace("🛒", ""));
    FT(note, { opacity: 0, y: -180, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: MK.spring({ stiffness: 230, damping: 17 }).ease }, 19.62);
    FX(note, { x: 0 }, { x: 6, duration: 0.05, yoyo: true, repeat: 3, ease: "none" }, 20.13);
    TO(note, { y: -900, opacity: 0, duration: 0.35, ease: "power2.in" }, 21.4);
    const sendP = obj(s, "obj_plane", 300, 700, 150, 20.1, { float: false, z: 9 });
    FX(sendP, { x: 0, y: 0, rotation: 0, opacity: 1 }, { x: 420, y: -330, rotation: 20, opacity: 0, duration: 0.7, ease: "power2.in" }, 20.25);
    const bub = E("div", `display:none;position:absolute;left:70px;top:720px;width:500px;border-radius:40px 40px 40px 10px;background:${C.cobalt};color:#fff;padding:28px 32px;box-sizing:border-box;
      font:700 38px/1.25 ${F.sans};box-shadow:0 30px 60px rgba(43,77,255,.45);z-index:7`, s,
      `Aapka cart abhi bhi<br>wait kar raha hai <div style="margin-top:16px;display:inline-block;background:${C.butter};color:${C.ink};border-radius:14px;padding:8px 18px;font:800 28px ${F.sans}">Order complete karein →</div>`);
    FT(bub, { opacity: 0, x: 420, y: 60, scale: 0.3, rotation: 12 }, { opacity: 1, x: 0, y: 0, scale: 1, rotation: -2, duration: 0.5, ease: "back.out(1.5)" }, 20.13);
    // the order comes back
    kline([["aur", "s", 21.09], ["order", "b", 21.59, C.mint], ["aa hi gaya,", "c", 22.03, C.ink]], { y: 290, out: 23.02 });
    TO(chat, { x: -700, opacity: 0, duration: 0.4, ease: "power2.in" }, 21.4);
    const ord = mock(s, "mk_notify", 50, 560, 430, 21.55, { ry: 20, hold: 2.4 });
    const cart2 = obj(s, "obj_cart", 330, 980, 250, 21.95, { ring: C.mint, z: 6 });
    kline([["toh", "s", 23.09], ["profit", "b", 23.25, C.mint], ["pakka?", "c", 23.77, C.tang]], { y: 290, out: 24.32 });
    const coins = obj(s, "obj_coins", 620, 900, 280, 23.25, { z: 8, float: false });
    const q = MKS.doodleBoil(tl, s, 23.8, { d: "M30,30 C30,5 70,5 70,30 C70,48 50,50 50,66 M50,84 L50,88", x: 840, y: 860, w: 170, h: 250, color: C.tang, stroke: 12, hold: 0.5 });
    tl.set(q.svg, { opacity: 0 }, 0); tl.set(q.svg, { opacity: 1 }, sn(23.8));
    FX(coins, { rotation: 0 }, { rotation: -14, y: 30, duration: 0.4, ease: "back.out(2)" }, 23.8);
    TO([kp, ord, cart2, coins, q.svg], { y: 1400, duration: 0.35, ease: "power2.in", stagger: 0.02 }, 24.2);
  });
  focusPull(24.42); setBG(24.42, "G"); chromeMode(24.42, false, 7);

  // ═════════ G 24.4–28.1 · grid paper · the bill prints the hidden costs ═════════
  mkScene("v07", 24.42, 28.64, (s) => {
    kline([["Discount,", "b", 24.61, C.tang], ["delivery,", "b", 25.55, C.tang], ["packaging,", "b", 26.15, C.tang]], { y: 290, out: 26.95 });
    kline([["bacha", "s", 26.99], ["kitna?", "c", 27.33, C.tang]], { y: 270, out: 28.1 });
    const bill = E("div", `position:absolute;left:300px;top:470px;width:480px;height:800px;background:#fff;border-radius:6px;box-shadow:0 40px 80px rgba(10,15,40,.35);color:${C.ink};
      clip-path:polygon(${Array.from({ length: 35 }, (_, i) => `${(i / 34) * 100}% ${i % 2 ? 1.3 : 0}%`).join(",")},${Array.from({ length: 35 }, (_, i) => `${100 - (i / 34) * 100}% ${100 - (i % 2 ? 1.3 : 0)}%`).join(",")})`, s,
      `<div style="text-align:center;margin-top:34px;font:900 92px/1 ${F.didone};letter-spacing:.02em">BILL</div>
       <div style="text-align:center;font:700 18px ${F.mono};letter-spacing:.2em;opacity:.6;margin-top:6px">ONLINE ORDER · DUKAANDAAR COPY</div>
       <div style="margin:18px 30px;border-top:3px dashed rgba(17,21,34,.3)"></div>`);
    FT(bill, { y: 900, rotation: -3 }, { y: 0, rotation: 0, duration: 0.55, ease: "expo.out" }, 24.35);
    const rows = [["ORDER", "1 ✓", 24.5], ["AD SPEND", "− ₹ ? ? ?", 24.55], ["DISCOUNT", "− ₹", 24.61], ["DELIVERY", "− ₹", 25.55], ["PACKAGING", "− ₹", 26.15]];
    rows.forEach(([l, v, t], i) => {
      const r = E("div", `position:absolute;left:30px;right:30px;top:${210 + i * 72}px;display:flex;gap:10px;align-items:baseline;font:700 32px ${F.mono}`, bill,
        `<span>${l}</span><span style="flex:1;border-bottom:3px dotted rgba(17,21,34,.3)"></span><span style="color:${C.tang}">${v}</span>`);
      FT(r, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.3, ease: "steps(9)" }, t);
    });
    const tot = E("div", `position:absolute;left:30px;right:30px;top:600px;border-top:5px double rgba(17,21,34,.5);padding-top:20px;display:flex;justify-content:space-between;font:900 64px/1 ${F.ext};font-stretch:125%`, bill,
      `<span>BACHA</span><span style="color:${C.tang}">?</span>`);
    FT(tot, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.3, ease: "steps(8)" }, 26.99);
    const paperIn = (name, x, y, w, at, r) => {
      const d = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;z-index:5`, s);
      const im = E("img", `display:block;width:100%;filter:drop-shadow(0 16px 18px rgba(10,15,40,.3))`, d); im.src = V(name + ".png");
      FT(d, { opacity: 0, y: -120, rotation: r - 16, scale: 1.15 }, { opacity: 1, y: 0, rotation: r, scale: 1, duration: 0.42, ease: "steps(6)" }, at);
      FX(d, { rotation: r }, { rotation: r + 3, duration: 0.25, ease: "steps(3)", yoyo: true, repeat: 5 }, at + 0.45);
      return d;
    };
    paperIn("pc_discount", 20, 560, 230, 24.62, -8);
    paperIn("pc_scooter", 770, 600, 290, 25.55, 4);
    paperIn("pc_boxes", 30, 930, 240, 26.15, -6);
    const money = paperIn("pc_money", 760, 420, 260, 27.0, 6);
    FX(money, { x: 0, y: 0, opacity: 1 }, { x: 380, y: -360, rotation: 30, opacity: 0, duration: 0.9, ease: "power2.in" }, 27.45);
    cut(s, "cut_keeper_despair", 720, 820, 360, 26.9, { z: 9 });
    const c = MKS.doodleBoil(tl, s, 27.3, { shape: "circle", x: 640, y: 1060, w: 160, h: 140, color: C.tang, stroke: 10, hold: 0.7 });
    tl.set(c.svg, { opacity: 0 }, 0); tl.set(c.svg, { opacity: 1 }, sn(27.3)); c.svg.style.zIndex = 10;
    push(s, 24.5, 28.0, 1.04);
    // the tear: two halves fly apart on "Isi liye"
    const halves = [0, 1].map((k) => {
      const h = bill.cloneNode(true); s.appendChild(h);
      h.querySelectorAll("[style]").forEach((n) => { if ((n.style.clipPath || "").startsWith("inset")) n.style.clipPath = "none"; });
      h.style.clipPath = k ? "polygon(52% 0,100% 0,100% 100%,47% 100%,53% 70%,46% 45%,54% 22%)" : "polygon(0 0,52% 0,54% 22%,46% 45%,53% 70%,47% 100%,0 100%)";
      tl.set(h, { opacity: 0 }, 0); tl.set(h, { opacity: 1 }, sn(28.06));
      FX(h, { x: 0, rotation: 0, y: 0 }, { x: k ? 120 : -120, rotation: k ? 9 : -9, y: 30, duration: 0.18, ease: "power3.out" }, 28.07);
      FX(h, { x: k ? 120 : -120, rotation: k ? 9 : -9, y: 30 }, { x: k ? 760 : -760, rotation: k ? 30 : -30, y: 700, duration: 0.36, ease: "power2.in" }, 28.26);
      return h;
    });
    tl.set(bill, { opacity: 0 }, sn(28.06));
  });
  flash(28.6, C.butter); setBG(28.6, "D"); chromeMode(28.6, true, 8);

  // ═════════ H 28.1–34.9 · navy velvet · SHOTLIN + the module deck ═════════
  mkScene("v08", 28.5, 34.92, (s) => {
    kline([["isi liye", "c", 28.09, C.tang]], { y: 250, dark: true, out: 29.85 });
    const sh = hero(s, "SHOTLIN", 0, 410, 180, C.butter, 28.53, { w: W });
    kline([["ke", "s", 29.03], ["system", "b", 29.17, C.cream], ["mein,", "s", 29.49]], { y: 1100, dark: true, out: 29.85 });
    const icon = E("div", `position:absolute;left:390px;top:720px;width:300px;perspective:1200px;z-index:5`, s);
    const ii = E("img", `display:block;width:100%;filter:drop-shadow(0 30px 40px rgba(0,0,0,.5)) drop-shadow(0 0 60px rgba(255,212,92,.35))`, icon); ii.src = V("ic_app.png");
    FT(ii, { opacity: 0, rotationY: -200, scale: 0.3, y: 120 }, { opacity: 1, rotationY: 0, scale: 1, y: 0, duration: 0.8, ease: "back.out(1.4)" }, 28.6);
    TO(sh, { y: -150, scale: 0.42, opacity: 0, duration: 0.35, ease: "power2.in" }, 29.6);
    TO(icon, { y: -500, scale: 0.4, opacity: 0, duration: 0.35, ease: "power2.in" }, 29.62);
    const deck = [
      { title: "CART RECOVERY", sub: "ORDERS WAPAS", accent: C.tang, glyph: "↺", img: "obj_cart.png", extra: [["ic_shield.png", 70, 8, 150]], at: 29.87 },
      { title: "DELIVERY RULES", sub: "PIN · WEIGHT · COD", accent: C.cobalt, glyph: "⇢", img: "pc_map.png", extra: [["ic_pin.png", 64, 6, 170]], at: 30.85 },
      { title: "CUSTOMER ANALYTICS", sub: "WHO BUYS · WHO LEAVES", accent: C.mint, glyph: "◔", img: "ic_chart.png", at: 31.95 },
      { title: "MARKETING TOOLS", sub: "OFFERS · CAMPAIGNS", accent: C.butter, glyph: "✦", img: "obj_megaphone.png", extra: [["ic_coupon.png", 6, 52, 210], ["ic_bell.png", 74, 4, 150]], at: 33.01 },
    ].map((d, i) => {
      const c = spec(s, { x: 110, y: 330, w: 860, h: 820, title: d.title, num: "00" + (i + 1), sub: d.sub, accent: d.accent, glyph: d.glyph, kind: "product", at: d.at, seed: 31 + i * 7, numSize: 130, foot: "MODULE" });
      if (d.img) { const im = E("img", `position:absolute;left:50%;top:50%;height:86%;transform:translate(-50%,-50%);filter:drop-shadow(0 20px 24px rgba(0,0,0,.35))`, c.well); im.src = V(d.img); FT(im, { scale: 0.6, rotation: -10 }, { scale: 1, rotation: 0, duration: 0.6, ease: "back.out(1.6)" }, d.at + 0.15); }
      (d.extra || []).forEach(([src, lx, ty, ew], k) => { const ex = E("img", `position:absolute;left:${lx}%;top:${ty}%;width:${ew}px;filter:drop-shadow(0 16px 18px rgba(0,0,0,.35))`, c.well); ex.src = V(src); FT(ex, { opacity: 0, scale: 0.3, rotation: -25 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.5, ease: "back.out(2)" }, d.at + 0.3 + k * 0.12); });
      if (d.chart) [0.3, 0.5, 0.42, 0.7, 0.9, 0.62, 0.95].forEach((v, k) => { const b = E("div", `position:absolute;left:${60 + k * 100}px;bottom:30px;width:64px;height:${v * 70}%;border-radius:10px 10px 2px 2px;background:${k === 6 ? C.ink : "rgba(17,21,34,.45)"};transform-origin:50% 100%`, c.well); FT(b, { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: "power3.out" }, d.at + 0.2 + k * 0.05); });
      if (d.chart) E("div", `position:absolute;right:20px;top:16px;font:700 18px ${F.mono};color:${C.ink};opacity:.7`, c.well, "ILLUSTRATIVE");
      return c;
    });
    // older cards step back as each new one lands (a deck), then fan into a 2×2 grid on "sab milte hain"
    deck.forEach((c, i) => deck.slice(0, i).forEach((p, j) => TO(p, { y: -36 * (i - j), scale: 1 - 0.05 * (i - j), filter: `brightness(${1 - 0.18 * (i - j)})`, duration: 0.45, ease: glide }, [29.87, 30.85, 31.95, 33.01][i])));
    const slots = [[-215, -260], [215, -260], [-215, 200], [215, 200]];
    deck.forEach((c, i) => TO(c, { x: slots[i][0], y: slots[i][1] + 40, scale: 0.47, filter: "brightness(1)", rotation: [-3, 2, 2, -2][i], duration: 0.55, ease: glide }, 34.0 + i * 0.03));
    kline([["sab", "s", 34.07], ["milte", "c", 34.33, C.butter], ["hain.", "b", 34.65, C.cream]], { y: 1170, dark: true, out: 34.9 });
    TO(deck, { y: "-=1400", duration: 0.35, ease: "expo.in", stagger: 0.02 }, 34.82);
  });
  focusPull(34.92); setBG(34.92, "L"); chromeMode(34.92, false, 9);

  // ═════════ I 34.9–38.8 · cream satin · the store's festival look from the dashboard ═════════
  mkScene("v09", 34.92, 38.82, (s) => {
    kline([["Aur", "s", 35.11], ["festival", "c", 35.29, C.tang], ["pe aap ka", "s", 35.77], ["look", "b", 36.47, C.cobalt]], { y: 280, out: 36.86 });
    kline([["bhi", "s", 36.73], ["dashboard se", "b", 36.93, C.cobalt], ["change", "c", 37.63, C.tang], ["kar sakte ho.", "s", 37.85]], { y: 280, out: 38.7 });
    const page = E("div", `position:absolute;left:100px;top:560px;width:880px;height:640px;z-index:2;border-radius:30px;background:#fff;overflow:hidden;box-shadow:0 40px 80px rgba(10,15,40,.35)`, s);
    FT(page, { opacity: 0, y: 200, rotation: -3, filter: "blur(12px)" }, { opacity: 1, y: 0, rotation: 0, filter: "blur(0px)", duration: 0.55, ease: "expo.out" }, 34.95);
    E("div", `height:60px;background:${C.navy};display:flex;align-items:center;gap:12px;padding-left:24px;color:#fff;font:700 22px ${F.mono}`, page, `● ● ●&nbsp;&nbsp;&nbsp;yourstore.in`);
    const hero1 = E("div", `position:absolute;left:24px;right:24px;top:84px;height:320px;border-radius:20px;overflow:hidden;background:#ddd`, page);
    const himg = E("img", `position:absolute;inset:0;width:100%;height:100%;object-fit:cover`, hero1); himg.src = V("photo_store.jpg");
    FT(himg, { filter: "grayscale(1) brightness(1.05)" }, { filter: "grayscale(1) brightness(1.05)", duration: 0.01 }, 34.95);
    FX(himg, { filter: "grayscale(1) brightness(1.05)" }, { filter: "grayscale(0) brightness(1)", duration: 0.5, ease: "power2.out" }, 37.66);
    const lab = E("div", `position:absolute;left:28px;bottom:24px;padding:10px 20px;background:#fff;font:800 34px ${F.sans};color:${C.ink};border-radius:12px`, hero1, "New arrivals");
    const fest = E("div", `position:absolute;inset:0;background:linear-gradient(115deg,rgba(122,20,40,.85),rgba(255,106,43,.55) 60%,transparent)`, hero1,
      `<div style="position:absolute;left:30px;top:60px;font:400 120px/0.8 ${F.script};color:${C.butter}">Festive</div><div style="position:absolute;left:36px;top:180px;font:900 40px ${F.ext};font-stretch:125%;color:#fff">COLLECTION</div>`);
    FT(fest, { clipPath: "circle(0px at 90% 100%)" }, { clipPath: "circle(1200px at 90% 100%)", duration: 0.55, ease: "power2.inOut" }, 37.66);
    [0, 1, 2].forEach((i) => {
      const p = E("div", `position:absolute;left:${24 + i * 284}px;top:428px;width:264px;height:180px;border-radius:16px;background:#eee`, page,
        `<div style="position:absolute;left:14px;bottom:12px;font:800 26px ${F.sans};color:${C.ink}">${["Kurta", "Saree", "Juttis"][i]}</div>`);
      FX(p, { background: "#eeeeee" }, { background: [C.butter, "#ffb38f", "#bfe9d4"][i], duration: 0.3 }, 37.75 + i * 0.06);
    });
    obj(s, "obj_diya", 800, 470, 210, 37.8, { ring: C.tang, z: 8 });
    const tab = mock(s, "mk_tablet", 430, 820, 600, 37.9, { ry: -18, hold: 0.8, z: 9 });
    const gar = E("img", `position:absolute;left:90px;top:405px;width:900px;z-index:0;filter:drop-shadow(0 16px 18px rgba(0,0,0,.3))`, s); gar.src = V("obj_garland.png");
    FT(gar, { opacity: 0, y: 160 }, { opacity: 1, y: 0, duration: 0.6, ease: "back.out(1.3)" }, 37.85);
    const panel = E("div", `position:absolute;left:470px;top:1110px;width:520px;height:130px;border-radius:28px;background:${C.navy};color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 30px;box-sizing:border-box;z-index:10;box-shadow:0 24px 50px rgba(0,0,0,.35)`, s,
      `<span style="font:800 30px ${F.sans}">DASHBOARD · Theme</span>`);
    const sw = E("div", `width:120px;height:64px;border-radius:32px;background:#556;position:relative`, panel);
    const knob = E("div", `position:absolute;left:6px;top:6px;width:52px;height:52px;border-radius:50%;background:#fff`, sw);
    FT(panel, { opacity: 0, y: 160 }, { opacity: 1, y: 0, duration: 0.45, ease: "back.out(1.5)" }, 36.47);
    const dft = tagMono(s, "THEME · DEFAULT", 600, 590, 35.6, C.ink, C.cream); dft.style.zIndex = 9;
    TO(dft, { opacity: 0, y: -30, duration: 0.2 }, 37.6);
    FX(himg, { scale: 1 }, { scale: 1.14, duration: 3.6, ease: "none" }, 35.0);
    const cur = E("div", `position:absolute;left:0;top:0;width:64px;height:64px;z-index:12`, s,
      `<svg viewBox="0 0 24 24" width="64" height="64"><path d="M4 2l15 11-6.5 1.2L16 21l-3 1.4-3.4-6.8L4 20z" fill="#fff" stroke="${C.ink}" stroke-width="1.6"/></svg>`);
    FT(cur, { x: 980, y: 1560, opacity: 0 }, { x: 560, y: 800, opacity: 1, duration: 0.9, ease: glide }, 35.8);
    FX(cur, { x: 560, y: 800 }, { x: 880, y: 1170, duration: 0.9, ease: glide }, 36.75);
    FX(cur, { scale: 1 }, { scale: 0.8, duration: 0.08, yoyo: true, repeat: 1 }, 37.58);
    TO(cur, { opacity: 0, duration: 0.2 }, 38.3);
    FX(knob, { x: 0 }, { x: 56, duration: 0.25, ease: "back.out(2)" }, 37.63);
    FX(sw, { background: "#555566" }, { background: C.tang, duration: 0.2 }, 37.63);
  });
  iris(38.82, 540, 900, C.navy); setBG(38.82, "D"); chromeMode(38.82, true, 10);

  // ═════════ J 38.8–43.0 · navy velvet · KEYNOTE: the Shotlin device family, one hero at a time ═════════
  // each branded mockup swings in on a 3D spring, keeps a slow orbit, then the camera dives into the dashboard
  function mock(parent, name, x, y, w, at, o = {}) {
    const st = E("div", `position:absolute;left:${x}px;top:${y}px;width:${w}px;perspective:1600px;z-index:${o.z || 4}`, parent);
    const body = E("div", `position:relative;transform-style:preserve-3d`, st);
    const img = E("img", `display:block;width:100%;filter:drop-shadow(0 40px 46px rgba(0,0,0,.5)) ${CAF(1.5, 0.3)}`, body); img.src = V(name + ".png");
    const ry = o.ry ?? -28;
    FT(body, { opacity: 0, rotationY: ry, rotationX: 12, y: 340, scale: 0.82, filter: "blur(14px)" }, { opacity: 1, rotationY: ry * 0.3, rotationX: 4, y: 0, scale: 1, filter: "blur(0px)", duration: 0.75, ease: "expo.out" }, at);
    FX(body, { rotationY: ry * 0.3 }, { rotationY: -ry * 0.25, duration: o.hold || 3, ease: "sine.inOut" }, at + 0.75);
    const glare = E("div", `position:absolute;inset:0;background:linear-gradient(115deg,transparent 35%,rgba(255,255,255,.22) 48%,transparent 60%);background-size:260% 100%;mix-blend-mode:screen;pointer-events:none;-webkit-mask:url(${V(name + ".png")}) center/100% 100% no-repeat;mask:url(${V(name + ".png")}) center/100% 100% no-repeat`, body);
    FT(glare, { backgroundPosition: "130% 0" }, { backgroundPosition: "-40% 0", duration: 1.3, ease: "power2.inOut" }, at + 0.3);
    st.body = body;
    return st;
  }
  const devTag = (parent, n, t, x, y, at, col) => {
    const d = E("div", `position:absolute;left:${x}px;top:${y}px;display:flex;align-items:center;gap:14px;z-index:9;white-space:nowrap`, parent,
      `<span style="background:${col};color:${C.ink};font:900 30px/1 ${F.round};padding:10px 14px;border-radius:10px">${n}</span><span style="font:900 46px/1 ${F.ext};font-stretch:125%;color:${C.cream};text-shadow:${CA(2, 0.5)}">${t}</span>`);
    FT(d, { opacity: 0, x: -40, filter: "blur(8px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.4, ease: "power3.out" }, at);
    return d;
  };
  mkScene("v10", 38.82, 43.04, (s) => {
    const spot = E("div", `position:absolute;left:0;top:0;width:${W}px;height:${H}px;background:radial-gradient(ellipse 60% 40% at 50% 46%,rgba(43,77,255,.45),transparent 70%)`, s);
    FT(spot, { opacity: 0 }, { opacity: 1, duration: 0.6 }, 38.8);
    const floor = E("div", `position:absolute;left:-200px;top:1020px;width:1480px;height:600px;transform:perspective(900px) rotateX(64deg);transform-origin:50% 0;
      background-image:linear-gradient(rgba(255,212,92,.22) 2px,transparent 2px),linear-gradient(90deg,rgba(255,212,92,.22) 2px,transparent 2px);background-size:80px 80px`, s);
    FX(floor, { backgroundPosition: "0px 0px" }, { backgroundPosition: "0px 160px", duration: 4.2, ease: "none" }, 38.8);
    const cam = E("div", `position:absolute;inset:0;transform-origin:50% 48%`, s);
    const and = mock(cam, "mk_android", 300, 360, 480, 38.72, { ry: -30, hold: 3.6 });
    const t1 = devTag(cam, "01", "ANDROID APP", 250, 262, 38.85, C.mint);
    TO(and, { x: -210, y: 120, scale: 0.72, duration: 0.55, ease: glide }, 39.62);
    TO(t1, { opacity: 0, y: -40, duration: 0.25, ease: "power2.in" }, 39.6);
    const ios = mock(cam, "mk_iphone", 560, 380, 440, 39.66, { ry: 30, hold: 2.8 });
    const t2 = devTag(cam, "02", "iOS APP", 330, 262, 39.78, C.cobalt);
    TO([and, ios], { y: "+=150", scale: (i) => [0.52, 0.56][i], duration: 0.55, ease: glide }, 40.5);
    TO(t2, { opacity: 0, y: -40, duration: 0.25, ease: "power2.in" }, 40.48);
    const lap = mock(cam, "mk_laptop", 140, 340, 800, 40.52, { ry: -14, hold: 2, z: 2 });
    const t3 = devTag(cam, "03", "WEBSITE", 330, 262, 40.64, C.tang);
    // "advanced dashboard": everything steps back, the monitor takes the stage
    TO([and, ios, lap, t1, t2, t3], { opacity: 0, scale: 0.4, filter: "blur(12px)", duration: 0.4, ease: "power2.in", stagger: 0.02 }, 41.45);
    const mon = mock(cam, "mk_monitor", 60, 380, 960, 41.5, { ry: -10, hold: 1.4, z: 5 });
    const t4 = devTag(cam, "04", "DASHBOARD", 300, 262, 42.11, C.butter);
    const adv = E("div", `position:absolute;left:250px;top:1150px;padding:8px 20px;background:${C.butter};color:${C.ink};font:900 58px/1 ${F.ext};font-stretch:125%;transform:rotate(-3deg);z-index:9;box-shadow:0 12px 26px rgba(0,0,0,.35)`, cam, "ADVANCED");
    FT(adv, { opacity: 0, scale: 2.2 }, { opacity: 1, scale: 1, duration: 0.18, ease: "expo.out" }, 41.57);
    // digital zoom steps onto the charts, then a zoom-through dive into the screen (bridge into the price label)
    [1.0, 1.14, 1.28].forEach((k, i) => tl.set(cam, { scale: k }, sn(42.11 + i * 0.08)));
    MK.brackets(tl, cam, { x: 330, y: 470, w: 600, h: 330 }, 42.15, { color: C.butter, size: 50, stroke: 8 });
    FX(cam, { scale: 1.28 }, { scale: 4.2, filter: "blur(10px)", duration: 0.5, ease: "expo.in" }, 42.5);
  });
  flash(43.02, C.butter); focusPull(43.02); setBG(43.02, "L"); chromeMode(43.02, false, 11);

  // ═════════ K 43.0–45.3 · cream satin · the one label that answers it: ₹50,000 ═════════
  mkScene("v11", 43.02, 45.32, (s) => {
    kline([["poora", "s", 43.03], ["system", "b", 43.39, C.cobalt], ["sirf", "c", 43.77, C.tang]], { y: 280, out: 45.28 });
    // loop closure: the SAME torn bill, taped back together, now prints the Shotlin system and one honest total
    const zz = (n, k) => Array.from({ length: n }, (_, i) => `${(i / (n - 1)) * 100}% ${k ? 100 - (i % 2 ? 1.2 : 0) : (i % 2 ? 1.2 : 0)}%`);
    const bill = E("div", `position:absolute;left:250px;top:430px;width:580px;height:840px;background:#fff;border-radius:6px;color:${C.ink};box-shadow:0 40px 80px rgba(10,15,40,.35);
      clip-path:polygon(${zz(35, 0).join(",")},${zz(35, 1).reverse().join(",")})`, s,
      `<div style="text-align:center;margin-top:28px;font:900 84px/1 ${F.didone};font-variation-settings:'opsz' 6">BILL</div>
       <div style="text-align:center;font:700 17px ${F.mono};letter-spacing:.18em;opacity:.6;margin-top:6px">DUKAANDAAR COPY · SHOTLIN SE</div>
       <div style="margin:16px 30px;border-top:3px dashed rgba(17,21,34,.3)"></div>`);
    FT(bill, { y: 1000, rotation: -5 }, { y: 0, rotation: -1.5, duration: 0.55, ease: "expo.out" }, 42.98);
    // the seam and tape: proof it is the bill that tore at 28 s
    E("div", `position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none`, bill,
      `<svg width="580" height="840" style="position:absolute;inset:0"><polyline points="${Array.from({ length: 21 }, (_, i) => `${290 + (MK.hash(i, 3) - 0.5) * 34},${i * 42}`).join(" ")}" fill="none" stroke="rgba(17,21,34,.28)" stroke-width="2.5"/></svg>`);
    [[96, -8], [572, 6], [790, -4]].forEach(([y, r], i) => {
      const t = E("div", `position:absolute;left:225px;top:${y}px;width:130px;height:40px;background:rgba(255,212,92,.82);transform:rotate(${r}deg);box-shadow:0 2px 4px rgba(0,0,0,.12)`, bill);
      FT(t, { opacity: 0, scaleX: 0.2 }, { opacity: 1, scaleX: 1, duration: 0.18, ease: "power3.out" }, 43.05 + i * 0.08);
    });
    const rows = ["ANDROID + iOS APP", "WEBSITE", "ADV. DASHBOARD", "CART RECOVERY", "DELIVERY RULES", "ANALYTICS", "MARKETING TOOLS"];
    rows.forEach((t, i) => {
      const r = E("div", `position:absolute;left:30px;right:30px;top:${196 + i * 56}px;display:flex;gap:10px;align-items:baseline;font:700 27px ${F.mono}`, bill,
        `<span>${t}</span><span style="flex:1;border-bottom:3px dotted rgba(17,21,34,.3)"></span><span style="color:${C.mint};font-weight:900">✓</span>`);
      FT(r, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.2, ease: "steps(7)" }, 43.12 + i * 0.1);
    });
    const tot = E("div", `position:absolute;left:30px;right:30px;top:612px;border-top:5px double rgba(17,21,34,.5);padding-top:16px`, bill,
      `<div style="font:800 22px ${F.mono};letter-spacing:.2em;opacity:.7">POORA SYSTEM · EK BAAR</div>
       <div class="amt" style="font:900 90px/1 ${F.round};white-space:nowrap;letter-spacing:-.03em;margin-top:6px;color:${C.ink}">₹50,000</div>`);
    FT(tot, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.2, ease: "steps(6)" }, 43.95);
    const amt = tot.querySelector(".amt"); amt.style.transformOrigin = "0% 60%";
    FT(amt, { opacity: 0, scale: 1.7, filter: "blur(12px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.22, ease: "expo.out" }, 44.29);
    FX(bill, { x: 0 }, { x: 7, duration: 0.04, yoyo: true, repeat: 3, ease: "none" }, 44.31);
    const icon = E("img", `position:absolute;left:740px;top:400px;width:200px;z-index:6;filter:drop-shadow(0 20px 26px rgba(0,0,0,.35))`, s); icon.src = V("ic_app.png");
    FT(icon, { opacity: 0, scale: 0.3, rotation: -40 }, { opacity: 1, scale: 1, rotation: 10, duration: 0.5, ease: "back.out(1.8)" }, 43.2);
    obj(s, "obj_coins", 790, 960, 260, 44.4, { z: 9, float: false });
    push(s, 43.1, 45.2, 1.04);
  });
  focusPull(45.32); chromeMode(45.32, false, 12);

  // ═════════ L 45.3–47.7 · cream satin · apne business ke liye actual system? ═════════
  mkScene("v12", 45.32, 47.72, (s) => {
    kline([["Apne business ke liye", "s", 45.6], ["actual", "c", 46.51, C.tang], ["system", "b", 46.87, C.cobalt], ["dekhna hai?", "h", 47.15]], { y: 280, out: 47.68 });
    frame(s, 150, 700, 780, 540, C.cobalt, 45.35, { img: "photo_store.jpg", imgCss: "opacity:.85" });
    const k = cut(s, "cut_keeper_proud", 250, 560, 580, 45.45, { z: 4 });
    push(k, 45.6, 47.6, 1.05);
    mock(s, "mk_laptop", -150, 560, 520, 45.9, { ry: 18, hold: 1.5, z: 3 });
    mock(s, "mk_android", 830, 640, 230, 46.3, { ry: -24, hold: 1.2, z: 5 });
    mock(s, "mk_iphone", 880, 930, 190, 46.6, { ry: -24, hold: 1.0, z: 5 });
    obj(s, "ic_app", 60, 1010, 170, 46.87, { z: 6, r: -30 });
  });
  focusPull(47.72); chromeMode(47.72, false, 13);

  // ═════════ M 47.7–53.2 · cream satin · comment CONTROL → demo in DM → end ═════════
  mkScene("v13", 47.72, 53.2, (s) => {
    kline([["neeche", "c", 47.75, C.tang]], { y: 250 });
    const cm = E("div", `position:absolute;left:0;right:0;top:420px;text-align:center;font:700 34px ${F.mono};letter-spacing:.6em;color:${C.ink}`, s, "COMMENT");
    FT(cm, { opacity: 0, letterSpacing: "1.2em" }, { opacity: 1, letterSpacing: "0.6em", duration: 0.5, ease: "power3.out" }, 48.6);
    const ctl = E("div", `position:absolute;left:0;right:0;top:470px;text-align:center;font:900 132px/1 ${F.ext};font-stretch:125%;color:${C.cobalt};text-shadow:${CA(3, 0.5)}`, s, "“CONTROL”");
    FT(ctl, { opacity: 0, scale: 1.5, filter: "blur(16px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }, 48.17);
    // the demo kit (document) in perspective, a second page behind
    const doc = E("div", `position:absolute;left:290px;top:640px;width:500px;height:440px;perspective:1600px`, s);
    const back = E("div", `position:absolute;inset:0;background:${C.label};border-radius:12px;transform:rotate(-7deg) translate(-24px,10px);box-shadow:0 30px 60px rgba(10,15,40,.25)`, doc);
    const front = E("div", `position:absolute;inset:0;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 40px 80px rgba(10,15,40,.35);transform:rotateY(-10deg) rotate(2deg);--qrbg:#fff;color:${C.ink}`, doc,
      `<div style="height:120px;background:${C.cobalt};padding:22px 30px;box-sizing:border-box;color:#fff;position:relative"><img src="${V("ic_app.png")}" style="position:absolute;right:22px;top:16px;width:88px"><div style="font:900 30px ${F.ext};font-stretch:125%">SHOTLIN</div><div style="font:700 18px ${F.mono};opacity:.8;margin-top:6px">D2C SYSTEMS · 2026</div></div>
       <div style="padding:28px 30px"><div style="font:400 92px/0.85 ${F.script};color:${C.tang}">Complete</div><div style="font:900 46px/1 ${F.ext};font-stretch:125%;margin-top:8px">WORKING DEMO</div>
       
       <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:14px"><span style="background:${C.butter};padding:8px 16px;font:900 26px ${F.ext};font-stretch:125%">FREE · DM</span>${qr(97, 21, 4)}</div></div>`);
    FT(doc, { opacity: 0, y: 300, rotation: 6, filter: "blur(12px)" }, { opacity: 1, y: 0, rotation: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }, 47.85);
    kline([["Complete", "s", 49.37], ["working demo", "c", 49.87, C.tang], ["DM mein bhej denge", "b", 50.47, C.ink]], { y: 1095, w: 980, x: 50 });
    const plane = obj(s, "obj_plane", -200, 1000, 260, 50.3, { float: false, z: 9 });
    FX(plane, { x: 0, y: 0, rotation: -10 }, { x: 900, y: -560, rotation: 18, duration: 1.0, ease: glide }, 50.35);
    TO(plane, { opacity: 0, duration: 0.2 }, 51.3);
    push(s, 47.8, 53.2, 1.04);
    FX(ctl, { scale: 1 }, { scale: 1.06, duration: 0.6, yoyo: true, repeat: 1, ease: "sine.inOut" }, 51.6);
  });

  window.CAP_OFF = [[0, 99]]; // every spoken word is set as the film's kinetic editorial line
};
