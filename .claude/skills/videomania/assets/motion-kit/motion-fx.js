/* motion-fx.js: premium effects for Video Mania, built on motion-kit.js.
 *
 * Each effect is one object changing shape (playbook §3), implemented from the recipes in
 * motion-graphics-skills/skills/motion-effects/references/effects.md (MIT, Charlie Hills) and
 * herk-edit-kit MOTION_PHILOSOPHY (MIT, Nate Herk), adapted to HyperFrames' single paused
 * timeline. Each effect:
 *   - builds its own DOM inside `parent` (absolute positioning, film coordinates)
 *   - takes every colour/font from CSS variables on :root (set them from the motion brief):
 *       --mk-ground --mk-surface --mk-ink --mk-muted --mk-line --mk-accent --mk-accent2
 *       --mk-display (display font) --mk-ui (UI font) --mk-radius
 *   - lands its one move at `at` (anchor it to the spoken word) and keeps one thing alive in the
 *     hold. Exits are the caller's choice (a bridge into the next scene, never a fade-out by default)
 *   - returns handles {root, ...} so the next scene can reuse an element as its bridge
 * Words and numbers come from the caller (the narration); nothing here invents content.
 */
(function (root) {
  "use strict";
  const MK = root.MK;
  if (!MK) throw new Error("motion-fx.js needs motion-kit.js loaded first");
  const FX = {};
  const el = (tag, css, parent, html) => {
    const d = document.createElement(tag);
    // stacks, lifts and morphs overlap by design; tell HyperFrames' layout check so it doesn't
    // report them (captions and the film's own text are not created here and stay checked)
    d.setAttribute("data-layout-allow-overlap", "");
    if (css) d.style.cssText = css;
    if (html != null) d.innerHTML = html;
    if (parent) parent.appendChild(d);
    return d;
  };
  const P = (p) => (typeof p === "string" ? document.querySelector(p) : p);
  const V = (name) => `var(--mk-${name})`;
  const spring = MK.spring({ stiffness: 260, damping: 24 });

  /**
   * Masked headline: lines rise through cut lines, an accent underline draws under one word.
   * opts: {x,y,w, lines:["line one","line two"], size:120, accentWord:"word", align:"left"|"center", by:"words"}
   */
  FX.headline = function (tl, parent, at, o) {
    parent = P(parent);
    const box = el("div", `position:absolute;left:${o.x}px;top:${o.y}px;width:${o.w}px;text-align:${o.align || "left"};` +
      `font-family:${V("display")};font-weight:800;font-size:${o.size || 120}px;line-height:0.95;color:${V("ink")};text-transform:${o.upper === false ? "none" : "uppercase"}`, parent);
    const lines = o.lines.map((t) => el("div", "", box, null));
    lines.forEach((l, i) => (l.textContent = o.lines[i]));
    lines.forEach((l, i) => MK.maskRise(tl, l, at + i * 0.12, { by: o.by || "words", stagger: o.stagger ?? 0.06, dur: 0.6 }));
    let ul = null;
    if (o.accentWord) {
      const unit = Array.from(box.querySelectorAll(".mk-unit")).find((u) => u.textContent.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "") === o.accentWord.toLowerCase());
      if (unit) {
        unit.style.color = V("accent");
        ul = el("div", `position:absolute;left:0;right:0;bottom:-0.06em;height:0.09em;border-radius:0.05em;background:${V("accent")};transform-origin:left center`, unit.parentNode);
        unit.parentNode.style.position = "relative";
        unit.parentNode.style.overflow = "visible";
        tl.fromTo(ul, { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: MK.ease.glide }, at + 0.35 + 0.12 * (o.lines.length - 1));
      }
    }
    return { root: box, underline: ul };
  };

  /**
   * Chart morph: bars slim to hairlines left→right while a line draws through their tops; the
   * last value gets a tag. Values never change (bars and line show the SAME numbers).
   * opts: {x,y,w,h, values:[..], labels:[..], tag:"92", sample:true (adds an "example" chip)}
   */
  FX.chartMorph = function (tl, parent, at, o) {
    parent = P(parent);
    const max = Math.max(...o.values) * 1.12, n = o.values.length;
    const wrap = el("div", `position:absolute;left:${o.x}px;top:${o.y}px;width:${o.w}px;height:${o.h}px`, parent);
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("width", o.w); svg.setAttribute("height", o.h); svg.style.cssText = "position:absolute;left:0;top:0;overflow:visible";
    wrap.appendChild(svg);
    const pad = 20, gw = (o.w - pad * 2) / n, base = o.h - 60;
    const pts = o.values.map((v, i) => [pad + gw * (i + 0.5), base - (v / max) * (base - 20)]);
    for (let k = 0; k <= 3; k++) {
      const y = base - (k / 3) * (base - 20);
      const g = document.createElementNS(NS, "line");
      Object.entries({ x1: pad, x2: o.w - pad, y1: y, y2: y, stroke: "currentColor", "stroke-width": 2, opacity: 0.12 }).forEach(([a, b]) => g.setAttribute(a, b));
      svg.appendChild(g);
    }
    svg.style.color = "var(--mk-ink)";
    const bars = pts.map(([x, y], i) => {
      const b = el("div", `position:absolute;left:${x - gw * 0.3}px;top:${y}px;width:${gw * 0.6}px;height:${base - y}px;border-radius:12px 12px 0 0;background:${i === n - 1 ? V("accent") : V("muted")};transform-origin:50% 100%`, wrap);
      tl.fromTo(b, { scaleY: 0 }, { scaleY: 1, duration: spring.duration, ease: spring.ease }, at - 0.9 + i * 0.06);
      tl.to(b, { scaleX: 0.06, duration: 0.45, ease: MK.ease.glide }, at + i * 0.07);
      if (o.labels) el("div", `position:absolute;left:${x - 60}px;top:${base + 14}px;width:120px;text-align:center;font:600 26px ${V("ui")};color:${V("muted")}`, wrap).textContent = o.labels[i];
      return b;
    });
    const d = "M" + pts.map((p) => p.join(" ")).join(" L");
    const fill = document.createElementNS(NS, "path");
    fill.setAttribute("d", d + ` L${pts[n - 1][0]} ${base} L${pts[0][0]} ${base} Z`);
    fill.setAttribute("fill", "var(--mk-accent)"); fill.setAttribute("opacity", 0);
    svg.appendChild(fill);
    const line = document.createElementNS(NS, "path");
    Object.entries({ d, fill: "none", stroke: "var(--mk-accent)", "stroke-width": 8, "stroke-linecap": "round", "stroke-linejoin": "round" }).forEach(([a, b]) => line.setAttribute(a, b));
    svg.appendChild(line);
    MK.drawPath(tl, line, at + 0.35, 0.8);
    tl.fromTo(fill, { opacity: 0 }, { opacity: 0.14, duration: 0.6 }, at + 0.5);
    const dots = pts.map(([x, y], i) => {
      const c = el("div", `position:absolute;left:${x - 11}px;top:${y - 11}px;width:22px;height:22px;border-radius:50%;background:${i === n - 1 ? V("accent") : V("card")};border:5px solid ${V("accent")};box-sizing:border-box`, wrap);
      tl.fromTo(c, { scale: 0 }, { scale: 1, duration: spring.duration, ease: spring.ease }, at + 0.35 + (i / (n - 1)) * 0.8);
      return c;
    });
    if (o.tag) {
      const [lx, ly] = pts[n - 1];
      const t = el("div", `position:absolute;left:${lx - 70}px;top:${ly - 96}px;width:140px;padding:10px 0;border-radius:16px;text-align:center;background:${V("accent")};color:${V("ground")};font:800 40px ${V("ui")}`, wrap);
      t.textContent = o.tag;
      tl.fromTo(t, { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: spring.duration, ease: spring.ease }, at + 1.2);
      tl.fromTo(t, { scale: 1 }, { scale: 1.06, duration: 0.9, ease: "sine.inOut", yoyo: true, repeat: 3, immediateRender: false }, at + 1.8); // living hold
    }
    if (o.sample) {
      const c = el("div", `position:absolute;right:${pad}px;top:-56px;padding:6px 16px;border-radius:999px;border:2px solid ${V("line")};font:600 22px ${V("ui")};color:${V("muted")}`, wrap);
      c.textContent = o.sampleLabel || "example";
    }
    return { root: wrap, bars, line, dots };
  };

  /**
   * Dashboard zoom: brackets snap around one tile, the rest dims, the tile lifts from its exact
   * slot into a large card with dashed guides from corner to corner; contents wait for room.
   * opts: {tiles:[{x,y,w,h,title,value}], pick:index, card:{x,y,w,h}, title, value, delta}
   */
  FX.dashboardZoom = function (tl, parent, at, o) {
    parent = P(parent);
    const wrap = el("div", "position:absolute;inset:0", parent);
    const tiles = o.tiles.map((t, i) => {
      const d = el("div", `position:absolute;left:${t.x}px;top:${t.y}px;width:${t.w}px;height:${t.h}px;border-radius:${V("radius")};background:${V("card")};border:2px solid ${V("line")};box-sizing:border-box;padding:24px`, wrap);
      el("div", `font:700 28px ${V("ui")};color:${V("muted")}`, d).textContent = t.title;
      el("div", `font:800 56px ${V("display")};color:${V("ink")};margin-top:10px`, d).textContent = t.value;
      tl.fromTo(d, { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: MK.ease.enter }, at - 1.0 + i * 0.07);
      return d;
    });
    const t = o.tiles[o.pick];
    const br = MK.brackets(tl, wrap, t, at, { color: "var(--mk-accent)" });
    tl.to(br, { opacity: 0, duration: 0.3, ease: "power2.in" }, at + 1.3);
    tiles.forEach((d, i) => { if (i !== o.pick) tl.to(d, { opacity: 0.25, filter: "blur(3px)", duration: 0.6, ease: "power2.inOut" }, at + 0.3); });
    const shell = el("div", `position:absolute;left:${o.card.x}px;top:${o.card.y}px;width:${o.card.w}px;height:${o.card.h}px;border-radius:32px;background:${V("card")};box-shadow:0 40px 90px rgba(0,0,0,.28);padding:48px;box-sizing:border-box`, wrap);
    const kids = [
      el("div", `font:700 36px ${V("ui")};color:${V("muted")}`, shell),
      el("div", `font:900 ${Math.round(o.card.w / 4.2)}px ${V("display")};color:${V("ink")};letter-spacing:-0.03em;margin-top:18px`, shell),
      el("div", `display:inline-block;margin-top:18px;padding:8px 22px;border-radius:999px;background:${V("accent")};color:${V("ground")};font:800 34px ${V("ui")}`, shell),
    ];
    kids[0].textContent = o.title; kids[1].textContent = o.value; kids[2].textContent = o.delta || "";
    if (!o.delta) kids[2].style.display = "none";
    const NS = "http://www.w3.org/2000/svg";
    const g = document.createElementNS(NS, "svg");
    g.setAttribute("width", 1080); g.setAttribute("height", 1920); g.style.cssText = "position:absolute;left:0;top:0;overflow:visible;pointer-events:none";
    wrap.insertBefore(g, shell);
    const c = o.card;
    [[t.x, t.y, c.x, c.y], [t.x + t.w, t.y, c.x + c.w, c.y], [t.x, t.y + t.h, c.x, c.y + c.h], [t.x + t.w, t.y + t.h, c.x + c.w, c.y + c.h]].forEach(([x1, y1, x2, y2]) => {
      const l = document.createElementNS(NS, "line");
      Object.entries({ x1, y1, x2, y2, stroke: "var(--mk-accent)", "stroke-width": 3, "stroke-dasharray": "10 10", opacity: 0 }).forEach(([a, b]) => l.setAttribute(a, b));
      g.appendChild(l);
      tl.fromTo(l, { opacity: 0 }, { opacity: 0.6, duration: 0.3 }, at + 0.55);
      tl.to(l, { opacity: 0, duration: 0.4 }, at + 1.4);
    });
    // the picked tile BECOMES the card: hide it as the shell leaves its slot (no duplicate)
    tl.to(tiles[o.pick], { opacity: 0, duration: 0.12, ease: "none" }, at + 0.55);
    MK.morph(tl, shell, { ...t, r: 24 }, { ...c, r: 32 }, at + 0.55, 0.85, { ghost: false, contents: kids });
    return { root: wrap, card: shell, tiles };
  };

  /**
   * Card → workspace: a small card grows from its own corner into a full window; the title is a
   * shared element that travels into the title bar; dashed ghost stays at the origin.
   * opts: {from:{x,y,w,h}, to:{x,y,w,h}, title, body:[lines as plain text]}
   */
  FX.cardToWorkspace = function (tl, parent, at, o) {
    parent = P(parent);
    const wrap = el("div", "position:absolute;inset:0", parent);
    const shell = el("div", `position:absolute;left:${o.to.x}px;top:${o.to.y}px;width:${o.to.w}px;height:${o.to.h}px;border-radius:28px;background:${V("card")};box-shadow:0 30px 80px rgba(0,0,0,.25);overflow:hidden`, wrap);
    const bar = el("div", `position:absolute;left:0;top:0;right:0;height:84px;background:${V("line")}`, shell);
    [0, 1, 2].forEach((i) => el("div", `position:absolute;left:${28 + i * 30}px;top:32px;width:18px;height:18px;border-radius:9px;background:${[V("accent"), V("accent2"), V("muted")][i]}`, bar));
    const side = el("div", `position:absolute;left:0;top:84px;bottom:0;width:${Math.round(o.to.w * 0.26)}px;background:${V("ground")};opacity:.6`, shell);
    const lines = (o.body || []).map((txt, i) => {
      const d = el("div", `position:absolute;left:${Math.round(o.to.w * 0.3)}px;top:${140 + i * 64}px;right:48px;font:500 34px ${V("ui")};color:${V("ink")}`, shell);
      d.textContent = txt;
      return d;
    });
    const title = el("div", `position:absolute;left:${o.from.x + 28}px;top:${o.from.y + 26}px;font:800 40px ${V("ui")};color:${V("ink")};white-space:nowrap`, wrap);
    title.textContent = o.title;
    tl.fromTo(title, { x: 0, y: 0 }, { x: o.to.x + 130 - (o.from.x + 28), y: o.to.y + 20 - (o.from.y + 26), duration: 0.85, ease: MK.ease.glide }, at);
    MK.morph(tl, shell, { ...o.from, r: 24 }, { ...o.to, r: 28 }, at, 0.85, { ghostColor: "var(--mk-muted)", contents: [side, ...lines] });
    return { root: wrap, window: shell, title };
  };

  /**
   * Spring stack: cards fan out on real springs with per-card damping (top card overshoots most),
   * a dashed ghost shows the top card's resting angle. opts: {x,y,w,h, cards:[{title, sub}], angles:[-9,0,9]}
   */
  FX.springStack = function (tl, parent, at, o) {
    parent = P(parent);
    const wrap = el("div", `position:absolute;left:${o.x}px;top:${o.y}px;width:${o.w}px;height:${o.h}px`, parent);
    const angles = o.angles || [-10, 0, 10];
    const dampings = [30, 20, 11];
    const n = o.cards.length;
    const els = o.cards.map((c, i) => {
      const d = el("div", `position:absolute;left:0;top:0;width:${o.w}px;height:${o.h}px;border-radius:30px;background:${V("card")};border:2px solid ${V("line")};box-sizing:border-box;padding:40px;transform-origin:50% 120%;box-shadow:0 24px 60px rgba(0,0,0,.18)`, wrap);
      el("div", `font:800 52px ${V("display")};color:${V("ink")}`, d).textContent = c.title;
      if (c.sub) el("div", `font:500 32px ${V("ui")};color:${V("muted")};margin-top:12px`, d).textContent = c.sub;
      return d;
    });
    const ghost = el("div", `position:absolute;left:0;top:0;width:${o.w}px;height:${o.h}px;border-radius:30px;border:3px dashed ${V("accent")};box-sizing:border-box;transform-origin:50% 120%;opacity:0;transform:rotate(${angles[n - 1]}deg)`, wrap);
    tl.fromTo(ghost, { opacity: 0 }, { opacity: 0.35, duration: 0.3 }, at);
    els.forEach((d, i) => {
      const s = MK.spring({ stiffness: 220, damping: dampings[Math.min(i, 2)] });
      tl.fromTo(d, { rotation: 0, x: 0 }, { rotation: angles[i], x: (i - (n - 1) / 2) * 30, duration: s.duration, ease: s.ease }, at + (n - 1 - i) * 0.05);
    });
    tl.to(ghost, { opacity: 0, duration: 0.4 }, at + 1.6);
    return { root: wrap, cards: els };
  };

  /**
   * Flowing paths: pulses travel curved connectors from one source through N channels into one
   * result; each node answers with a ring when a pulse arrives; a second wave keeps the hold alive.
   * opts: {source:{x,y,label}, channels:[{x,y,label}], result:{x,y,label}}
   */
  FX.flowingPaths = function (tl, parent, at, o) {
    parent = P(parent);
    const wrap = el("div", "position:absolute;inset:0", parent);
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("width", 1080); svg.setAttribute("height", 1920); svg.style.cssText = "position:absolute;left:0;top:0;overflow:visible";
    wrap.appendChild(svg);
    const curve = (a, b) => { const my = (a.y + b.y) / 2; return `M${a.x} ${a.y} C${a.x} ${my} ${b.x} ${my} ${b.x} ${b.y}`; };
    const node = (n, t, accent) => {
      const d = el("div", `position:absolute;left:${n.x}px;top:${n.y}px;transform:translate(-50%,-50%);padding:16px 30px;border-radius:999px;background:${accent ? V("accent") : V("card")};color:${accent ? V("ground") : V("ink")};border:2px solid ${V("line")};font:700 34px ${V("ui")};white-space:nowrap;z-index:2`, wrap);
      d.textContent = n.label;
      tl.fromTo(d, { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1, duration: spring.duration, ease: spring.ease }, t);
      const ring = el("div", `position:absolute;left:${n.x}px;top:${n.y}px;width:120px;height:120px;margin:-60px 0 0 -60px;border-radius:50%;border:4px solid ${V("accent")};opacity:0;z-index:1`, wrap);
      return { d, ring };
    };
    const src = node(o.source, at - 0.6, false);
    const res = node(o.result, at - 0.4, true);
    const chans = o.channels.map((c, i) => node(c, at - 0.5 + i * 0.05, false));
    const pulse = (from, to, t, targetRing) => {
      const path = document.createElementNS(NS, "path");
      Object.entries({ d: curve(from, to), fill: "none", stroke: "var(--mk-muted)", "stroke-width": 4, opacity: 0.35 }).forEach(([a, b]) => path.setAttribute(a, b));
      svg.insertBefore(path, svg.firstChild);
      const lit = path.cloneNode(); lit.setAttribute("stroke", "var(--mk-accent)"); lit.setAttribute("opacity", 1); lit.setAttribute("stroke-width", 6);
      svg.appendChild(lit);
      MK.drawPath(tl, lit, t, 0.9, { ease: "power2.inOut" });
      const dot = document.createElementNS(NS, "circle"); dot.setAttribute("r", 11); dot.setAttribute("fill", "var(--mk-accent)"); dot.setAttribute("opacity", 0);
      svg.appendChild(dot);
      const L = path.getTotalLength(), p = { k: 0 };
      const apply = () => { const q = path.getPointAtLength(L * p.k); dot.setAttribute("cx", q.x); dot.setAttribute("cy", q.y); dot.setAttribute("opacity", p.k > 0 && p.k < 1 ? 1 : 0); };
      apply();
      tl.fromTo(p, { k: 0 }, { k: 1, duration: 0.9, ease: "power2.inOut", onUpdate: apply }, t);
      tl.fromTo(targetRing, { scale: 0.4, opacity: 0.9 }, { scale: 1.6, opacity: 0, duration: 0.6, ease: "power2.out", immediateRender: false }, t + 0.9);
    };
    o.channels.forEach((c, i) => pulse(o.source, c, at + i * 0.14, chans[i].ring));
    o.channels.forEach((c, i) => pulse(c, o.result, at + 1.5 + i * 0.14, res.ring));
    o.channels.forEach((c, i) => pulse(o.source, c, at + 3.4 + i * 0.14, chans[i].ring)); // second wave keeps the hold alive
    return { root: wrap, source: src.d, result: res.d, channels: chans.map((c) => c.d) };
  };

  /**
   * Counter tag: a tag swings in on a string (damped pendulum), the number rolls up and lands on
   * the spoken word with a punch. opts: {x,y,w,h, from, to, format:{prefix,group}, label}
   */
  FX.counterTag = function (tl, parent, at, o) {
    parent = P(parent);
    // rig drops in (y); swing hangs inside it and rotates as a damped pendulum (rotation),
    // so the two transforms never fight over one element
    const rig = el("div", `position:absolute;left:${o.x}px;top:0;width:${o.w}px;height:${o.y + o.h}px`, parent);
    const swing = el("div", `position:absolute;inset:0;transform-origin:${o.w / 2}px 0px`, rig);
    el("div", `position:absolute;left:${o.w / 2 - 2}px;top:0;width:4px;height:${o.y}px;background:${V("muted")}`, swing);
    const tag = el("div", `position:absolute;left:0;top:${o.y}px;width:${o.w}px;height:${o.h}px;border-radius:28px;background:${V("card")};border:8px solid ${V("accent")};box-sizing:border-box;overflow:hidden`, swing);
    const fillL = el("div", `position:absolute;inset:0;background:${V("accent")};opacity:0`, tag);
    const num = el("div", `position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:900 ${Math.round(o.h * 0.5)}px ${V("ui")};color:${V("ink")};letter-spacing:-0.03em`, tag);
    const hole = el("div", `position:absolute;left:${o.w / 2 - 14}px;top:${o.y + 18}px;width:28px;height:28px;border-radius:50%;background:${V("muted")}`, swing);
    tl.fromTo(rig, { y: -(o.y + o.h + 100) }, { y: 0, duration: 0.45, ease: "power3.out" }, at - 1.4);
    const p = { t: 0 };
    const sw = () => gsap.set(swing, { rotation: 9 * Math.exp(-2.4 * p.t) * Math.cos(7 * p.t) });
    tl.fromTo(p, { t: 0 }, { t: 3, duration: 3, ease: "none", onUpdate: sw }, at - 0.95);
    MK.countUp(tl, num, o.from || 0, o.to, at - 0.9, 0.9, { ease: "power3.out", format: o.format || {} });
    tl.fromTo(fillL, { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power2.out" }, at);
    tl.fromTo(tag, { scale: 1.14 }, { scale: 1, duration: 0.35, ease: "power2.out", immediateRender: false }, at);
    if (o.label) {
      const l = el("div", `position:absolute;left:${o.x}px;top:${o.y + o.h + 40}px;width:${o.w}px;text-align:center;font:800 44px ${V("ui")};letter-spacing:0.16em;color:${V("ink")}`, parent);
      l.textContent = o.label;
      MK.maskRise(tl, l, at - 0.6, { by: "words" });
    }
    return { root: rig, tag, number: num, hole };
  };

  /**
   * Notification stack: cards slide in on springs, each pushing the stack down; newest on top.
   * opts: {x,y,w, items:[{title, body, time}] with times[] spoken anchors}
   */
  FX.notifications = function (tl, parent, times, o) {
    parent = P(parent);
    const wrap = el("div", `position:absolute;left:${o.x}px;top:${o.y}px;width:${o.w}px`, parent);
    const H = o.h || 150, gap = 18;
    const cards = o.items.map((it) => {
      const d = el("div", `position:absolute;left:0;top:0;width:${o.w}px;height:${H}px;border-radius:30px;background:${V("card")};box-shadow:0 16px 40px rgba(0,0,0,.16);box-sizing:border-box;padding:24px 30px;border:1px solid ${V("line")}`, wrap);
      el("div", `width:64px;height:64px;border-radius:18px;background:${V("accent")};position:absolute;left:28px;top:${(H - 64) / 2}px`, d);
      const t = el("div", `position:absolute;left:116px;top:30px;right:30px;font:800 32px ${V("ui")};color:${V("ink")}`, d); t.textContent = it.title;
      const b = el("div", `position:absolute;left:116px;top:76px;right:30px;font:500 28px ${V("ui")};color:${V("muted")}`, d); b.textContent = it.body;
      if (it.time) { const m = el("div", `position:absolute;right:30px;top:32px;font:500 24px ${V("ui")};color:${V("muted")}`, d); m.textContent = it.time; }
      return d;
    });
    const s = MK.spring({ stiffness: 240, damping: 21 });
    cards.forEach((c, i) => {
      tl.fromTo(c, { y: -H - 40, opacity: 0, scale: 0.94 }, { y: 0, opacity: 1, scale: 1, duration: s.duration, ease: s.ease }, times[i]);
      cards.slice(0, i).forEach((older, j) => {
        tl.to(older, { y: (i - j) * (H + gap), duration: s.duration, ease: s.ease }, times[i]);
      });
    });
    return { root: wrap, cards };
  };

  /** Cursor that glides to a point and clicks with a ripple and a press on the target. */
  FX.cursorClick = function (tl, parent, from, to, at, { target = null, dur = 0.7 } = {}) {
    parent = P(parent);
    const c = el("div", "position:absolute;left:0;top:0;width:46px;height:58px;z-index:40;pointer-events:none", parent,
      `<svg width="46" height="58" viewBox="0 0 40 52"><path d="M4 4v40l11-10 8 16 7-3-8-16h15z" fill="#111" stroke="#fff" stroke-width="3" stroke-linejoin="round"/></svg>`);
    tl.fromTo(c, { x: from[0], y: from[1], opacity: 0 }, { x: to[0], y: to[1], opacity: 1, duration: dur, ease: MK.ease.move }, at - dur);
    tl.fromTo(c, { scale: 1 }, { scale: 0.86, duration: 0.08, yoyo: true, repeat: 1, ease: "power1.inOut", immediateRender: false }, at);
    const r = el("div", `position:absolute;left:${to[0] - 40}px;top:${to[1] - 40}px;width:80px;height:80px;border-radius:50%;border:4px solid ${V("accent")};opacity:0;z-index:39`, parent);
    tl.fromTo(r, { scale: 0.3, opacity: 0.9 }, { scale: 1.8, opacity: 0, duration: 0.5, ease: "power2.out", immediateRender: false }, at);
    if (target) tl.fromTo(P(target), { scale: 1 }, { scale: 0.95, duration: 0.08, yoyo: true, repeat: 1, immediateRender: false }, at);
    return { cursor: c, ripple: r };
  };

  /** Keyhole/iris pass: the next layer opens through a shape at a point (bridge between scenes). */
  FX.irisPass = function (tl, layer, at, { cx, cy, r0 = 18, r1 = 1600, shape = "keyhole", dur = 0.35 } = {}) {
    MK.iris(tl, layer, { cx, cy, r0, r1, shape }, at, dur, "power3.in");
  };

  /** Particle logo/wordmark: seeded dots fly on arcs into points sampled from text rendered to canvas. */
  FX.particleWord = function (tl, parent, at, { text, x, y, w, h, font = "900 200px Inter", step = 12, color = "#fff", seed = 11 } = {}) {
    const cv = document.createElement("canvas");
    cv.width = w; cv.height = h;
    const g = cv.getContext("2d");
    g.fillStyle = "#000"; g.font = font; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText(text, w / 2, h / 2);
    const data = g.getImageData(0, 0, w, h).data, pts = [];
    for (let yy = 0; yy < h; yy += step) for (let xx = 0; xx < w; xx += step) if (data[(yy * w + xx) * 4 + 3] > 128) pts.push([x + xx, y + yy]);
    return MK.particlesTo(tl, parent, pts, at - 1.1, { seed, spread: 520, origin: [x + w / 2, y + h / 2], dur: 1.0, size: step * 0.7, color, window: 0.4 });
  };

  root.MKFX = FX;
})(typeof window !== "undefined" ? window : globalThis);
