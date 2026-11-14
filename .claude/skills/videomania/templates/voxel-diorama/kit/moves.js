// Voxel-diorama kit: moves. Named tricks a shot can call, each a pure function of time.
// The catalogue with "use when" for every move is engines/moves.json (searchable in the Pocket, kind "move").
//
// Shot fields handled here:
//   burst:  [{ t, x, y, n, kinds, size }]          shapes pop out around a point (x, y as fractions of the frame)
//   search: { text, t: [a, b], x, y, w }           a search bar that types its text
//   meter:  { label, value, t, x, y, n }           a segmented level bar that fills
//   cursor: { from: [x, y], to: [x, y], t: [a, b], click }   a pointer that travels and clicks
//   fan:    { t, at: [x, y, z], labels: [...], w } cards dealt onto an arc, in the world
//   strip:  { t: [a, b], at: [x, y, z], count }    a film strip of thumbnails bending through the world
// Word effects, transitions (flash, iris), the "through" 3D word and the camera moves live in voxel-kit.js.

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const outCubic = (u) => 1 - Math.pow(1 - u, 3);
const outBack = (u) => 1 + 2.4 * Math.pow(u - 1, 3) + 1.4 * Math.pow(u - 1, 2);
const smooth = (u) => u * u * (3 - 2 * u);
const SHAPES = {
  star: '<polygon points="50,4 61,36 96,36 67,57 78,92 50,70 22,92 33,57 4,36 39,36"/>',
  spark: '<polygon points="50,0 60,40 100,50 60,60 50,100 40,60 0,50 40,40"/>',
  heart: '<path d="M50 90 C10 60 0 35 20 18 C35 6 48 14 50 28 C52 14 65 6 80 18 C100 35 90 60 50 90Z"/>',
  bolt: '<polygon points="58,0 18,56 46,56 36,100 84,40 54,40"/>',
  dot: '<circle cx="50" cy="50" r="42"/>',
};

export function createMoves({ THREE, scene, camera, W, H, pal, shots, layer, imgs = {}, mapX = (x) => x, mapY = (y) => y, U = H }) {
  const cols = [pal.voice, pal.voice2, pal.accent, "#ffffff", "#ffd166"];
  const el = (tag, cls, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) e.style.cssText = css; return e; };
  let seed = 7; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);

  // ---------------------------------------------------------------- on-screen moves (DOM)
  const dom = shots.map((s) => {
    if (!s.burst && !s.search && !s.meter && !s.cursor) return null;
    const box = el("div", "vd-moves"); layer.appendChild(box); const o = { box };
    o.bursts = (s.burst || []).map((b) => {
      const n = b.n || 7, kinds = b.kinds || ["star", "spark", "heart", "bolt"], ph = rnd() * 6.28;
      return { b, parts: Array.from({ length: n }, (_, i) => {
        const size = U * 0.07 * (b.size || 1) * (0.7 + (i % 3) * 0.25), e = el("div", "vd-burst", `width:${size}px;height:${size}px;`);
        e.innerHTML = `<svg viewBox="0 0 100 100" width="100%" height="100%" fill="${cols[i % cols.length]}">${SHAPES[kinds[i % kinds.length]] || SHAPES.star}</svg>`;
        box.appendChild(e);
        return { e, size, ang: ph + (i / n) * 6.283, rad: U * (0.11 + (i % 3) * 0.045) * (b.size || 1), spin: (i % 2 ? 1 : -1) * (20 + i * 7) };
      }) };
    });
    if (s.search) { const q = s.search, e = el("div", "vd-search", `left:${mapX(q.x ?? 0.3) * W}px;top:${mapY(q.y ?? 0.42) * H}px;width:${Math.min(0.9, (q.w ?? 0.4) * (W > H ? 1 : 1.9)) * W}px;font-size:${U * 0.036}px;`);
      e.innerHTML = '<span class="vd-search-text"></span><span class="vd-search-btn">&#8593;</span>'; box.appendChild(e); o.search = { q, e, txt: e.firstChild }; }
    if (s.meter) { const m = s.meter, n = m.n || 12, e = el("div", "vd-meter", `left:${mapX(m.x ?? 0.56) * W}px;top:${mapY(m.y ?? 0.5) * H}px;font-size:${U * 0.022}px;`);
      const row = el("div", "vd-meter-row"); const segs = Array.from({ length: n }, () => { const g = el("i"); row.appendChild(g); return g; });
      e.appendChild(row); const lab = el("div", "vd-meter-label"); lab.textContent = m.label || "LEVEL"; e.appendChild(lab); box.appendChild(e); o.meter = { m, e, segs }; }
    if (s.cursor) { const e = el("div", "vd-cursor", `width:${U * 0.05}px;height:${U * 0.05}px;`);
      e.innerHTML = '<svg viewBox="0 0 100 100" width="100%" height="100%"><polygon points="8,4 8,84 30,64 46,98 60,92 44,58 74,58" fill="#fff" stroke="#111" stroke-width="6" stroke-linejoin="round"/></svg>';
      const ring = el("div", "vd-click"); box.appendChild(ring); box.appendChild(e); o.cursor = { c: s.cursor, e, ring }; }
    return o;
  });

  // ---------------------------------------------------------------- world moves (3D)
  const cardTex = (label, i, thumb, src) => {
    const c = document.createElement("canvas"); c.width = 320; c.height = 200; const x = c.getContext("2d");
    const pic = src && imgs[src] && imgs[src].naturalWidth ? imgs[src] : null;
    if (pic) {   // a real frame or picture (asset-first)
      const r = Math.max(320 / pic.naturalWidth, 200 / pic.naturalHeight), pw = pic.naturalWidth * r, ph = pic.naturalHeight * r;
      x.drawImage(pic, (320 - pw) / 2, (200 - ph) / 2, pw, ph);
      x.strokeStyle = "#ffffff"; x.lineWidth = 6; x.strokeRect(3, 3, 314, 194);
      if (label) { x.fillStyle = "rgba(0,0,0,0.55)"; x.fillRect(10, 146, 30 + label.length * 18, 44); x.fillStyle = "#ffffff"; x.font = "800 30px Inter, system-ui, sans-serif"; x.textBaseline = "bottom"; x.fillText(label, 22, 184); }
      const tq = new THREE.CanvasTexture(c); tq.colorSpace = THREE.SRGBColorSpace; tq.anisotropy = 4; return tq;
    }
    const g = x.createLinearGradient(0, 0, 320, 200); const a = cols[i % 3], b = ["#1a1030", "#0d2b2a", "#2a1408"][i % 3];
    g.addColorStop(0, thumb ? a : "#14161b"); g.addColorStop(1, b); x.fillStyle = g; x.fillRect(0, 0, 320, 200);
    if (thumb) { for (let k = 0; k < 9; k++) { x.fillStyle = cols[(i + k) % cols.length]; x.globalAlpha = 0.5; x.fillRect(rnd() * 280, rnd() * 160, 20 + rnd() * 70, 8 + rnd() * 26); } x.globalAlpha = 1; }
    else { x.fillStyle = a; x.fillRect(22, 26, 120, 10); x.fillStyle = "#3a4150"; [56, 80, 104].forEach((y, k) => x.fillRect(22, y, 250 - k * 50, 9)); }
    x.strokeStyle = "#ffffff"; x.lineWidth = 6; x.strokeRect(3, 3, 314, 194);
    if (label) { x.fillStyle = "#ffffff"; x.font = "700 30px Inter, system-ui, sans-serif"; x.textBaseline = "bottom"; x.fillText(label, 22, 182); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
  };
  const card = (label, i, w, thumb, src) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, w * 0.625), new THREE.MeshBasicMaterial({ map: cardTex(label, i, thumb, src), side: THREE.DoubleSide, color: new THREE.Color(1.15, 1.15, 1.15) })); m.visible = false; scene.add(m); return m; };
  let world = null;
  const buildWorld = () => shots.map((s) => {
    const o = {};
    if (s.fan) { const labels = s.fan.labels || ["v1", "v2", "v3", "v4", "v5", "v6"]; o.fan = labels.map((l, i) => card(l, i, s.fan.w || 6.4, false, (s.fan.imgs || [])[i])); }
    if (s.strip) o.strip = Array.from({ length: s.strip.count || 9 }, (_, i) => card("", i, s.strip.w || 7, true, (s.strip.imgs || [])[i % Math.max(1, (s.strip.imgs || []).length)]));
    return o;
  });


  // ---------------------------------------------------------------- particles: dots that become shapes
  // particles: { at: [x, y, z], size: 7, n: 1400, color, seq: [["scatter", t], ["sphere", t], ["ring", t], ...], spin: 0.35 }
  // Shapes: scatter, sphere, ring, cube, grid, line, burst, helix, wave. Each point travels from its place in one
  // shape to its place in the next over `morph` seconds (default 0.7), with a small stagger so it flows.
  const SHAPE = {
    scatter: (i, n, r) => [(r(i, 1) - 0.5) * 7, (r(i, 2) - 0.5) * 4, (r(i, 3) - 0.5) * 5],
    sphere: (i, n) => { const y = 1 - (i + 0.5) / n * 2, rr = Math.sqrt(1 - y * y), a = i * 2.39996; return [Math.cos(a) * rr, y, Math.sin(a) * rr]; },
    ring: (i, n, r) => { const a = (i / n) * 6.283, w = 1 + (r(i, 4) - 0.5) * 0.12; return [Math.cos(a) * 1.3 * w, (r(i, 5) - 0.5) * 0.08, Math.sin(a) * 1.3 * w]; },
    cube: (i, n, r) => { const f = Math.floor(r(i, 6) * 6), u = r(i, 7) * 2 - 1, v = r(i, 8) * 2 - 1, s = 0.85;
      return [[s, u, v], [-s, u, v], [u, s, v], [u, -s, v], [u, v, s], [u, v, -s]][f].map((q, k) => (k === 0 || k === 1 || k === 2 ? q * (Math.abs(q) === s ? 1 : s) : q)); },
    grid: (i, n) => { const c = Math.ceil(Math.sqrt(n)); return [((i % c) / (c - 1) - 0.5) * 3, (Math.floor(i / c) / (c - 1) - 0.5) * 1.8, 0]; },
    line: (i, n) => [((i / (n - 1)) - 0.5) * 4, 0, 0],
    burst: (i, n, r) => { const p = SHAPE.sphere(i, n); const k = 2.2 + r(i, 9) * 2.5; return [p[0] * k, p[1] * k, p[2] * k]; },
    helix: (i, n) => { const u = i / n, a = u * 6.283 * 4; return [Math.cos(a) * 0.9, (u - 0.5) * 3, Math.sin(a) * 0.9]; },
    wave: (i, n) => { const c = Math.ceil(Math.sqrt(n)), x = ((i % c) / (c - 1) - 0.5) * 4, z = (Math.floor(i / c) / (c - 1) - 0.5) * 2.4; return [x, Math.sin(x * 2.2 + z * 1.4) * 0.3, z]; },
  };
  const hash = (i, k) => { const s = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return s - Math.floor(s); };
  const dotTex = (() => { const c = document.createElement("canvas"); c.width = c.height = 32; const x = c.getContext("2d");
    const g = x.createRadialGradient(16, 16, 0, 16, 16, 16); g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.45, "rgba(255,255,255,0.9)"); g.addColorStop(1, "rgba(255,255,255,0)");
    x.fillStyle = g; x.fillRect(0, 0, 32, 32); return new THREE.CanvasTexture(c); })();
  const parts = shots.map((s) => {
    if (!s.particles) return null;
    const P = s.particles, n = P.n || 1400, geo = new THREE.BufferGeometry(), pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    const cs = (P.colors || [P.color || pal.accent, "#ffffff", pal.voice2]).map((c) => new THREE.Color(c));
    for (let i = 0; i < n; i++) { const c = cs[i % 7 === 0 ? 1 : i % 11 === 0 ? 2 % cs.length : 0]; col.set([c.r * 1.8, c.g * 1.8, c.b * 1.8], i * 3); }
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3)); geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    const mat = new THREE.PointsMaterial({ size: P.dot || 0.42, map: dotTex, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true });
    const pts = new THREE.Points(geo, mat); pts.frustumCulled = false; pts.visible = false; scene.add(pts);
    return { P, n, pts, pos };
  });
  function drawParticles(si, t) {
    parts.forEach((p) => { if (p) p.pts.visible = false; });
    const p = parts[si]; if (!p) return;
    const { P, n, pts, pos } = p, seq = P.seq || [["scatter", 0], ["sphere", 1]], M = P.morph || 0.7, sz = P.size || 7;
    let k = 0; while (k + 1 < seq.length && t >= seq[k + 1][1]) k++;
    const A = SHAPE[seq[k][0]] || SHAPE.scatter, B = k + 1 < seq.length ? SHAPE[seq[k + 1][0]] : null;
    for (let i = 0; i < n; i++) {
      let q = A(i, n, hash);
      const nextT = B ? seq[k + 1][1] : Infinity;
      if (k > 0) {   // still arriving from the previous shape
        const prev = SHAPE[seq[k - 1][0]] || SHAPE.scatter, u = smooth(clamp((t - seq[k][1] - hash(i, 11) * 0.25) / M));
        const a = prev(i, n, hash); q = [a[0] + (q[0] - a[0]) * u, a[1] + (q[1] - a[1]) * u, a[2] + (q[2] - a[2]) * u];
      }
      const wob = 0.03 * Math.sin(t * 2 + i);
      pos[i * 3] = q[0] * sz + wob; pos[i * 3 + 1] = q[1] * sz + wob; pos[i * 3 + 2] = q[2] * sz;
    }
    pts.geometry.attributes.position.needsUpdate = true;
    pts.position.set(...P.at); pts.rotation.set(0.25, t * (P.spin ?? 0.35), 0);
    const first = seq[0][1], fade = clamp((t - first + 0.2) / 0.3);
    pts.material.opacity = fade; pts.visible = true;
  }

  function draw(si, t, alpha) {
    drawParticles(si, t);
    dom.forEach((o, i) => { if (o) o.box.style.display = i === si ? "block" : "none"; });
    const s = shots[si], o = dom[si];
    if (o) {
      o.box.style.opacity = String(alpha);
      for (const { b, parts } of o.bursts) for (const [i, p] of parts.entries()) {
        const a = clamp((t - b.t - i * 0.03) / 0.36), out = clamp((t - b.t - (b.hold ?? 1.5)) / 0.3);
        const r = p.rad * (0.25 + 0.75 * outBack(a)) + Math.sin(t * 1.7 + i) * H * 0.006;
        p.e.style.opacity = String(a <= 0 ? 0 : 1 - out);
        p.e.style.transform = `translate(${mapX(b.x ?? 0.5) * W + Math.cos(p.ang) * r - p.size / 2}px,${mapY(b.y ?? 0.4) * H + Math.sin(p.ang) * r * 0.7 - p.size / 2}px) rotate(${p.spin * (1 - outCubic(a)) + Math.sin(t * 2 + i) * 6}deg) scale(${outBack(a) * (1 - out * 0.5)})`;
      }
      if (o.search) { const { q, e, txt } = o.search, a = clamp((t - q.t[0]) / 0.3), k = clamp((t - q.t[0] - 0.25) / Math.max(0.1, (q.t[1] - q.t[0]) * 0.8));
        e.style.opacity = String(a); e.style.transform = `scale(${0.9 + 0.1 * outBack(a)})`;
        txt.textContent = q.text.slice(0, Math.floor(q.text.length * k)) + (Math.floor(t * 3) % 2 || k < 1 ? "|" : ""); }
      if (o.meter) { const { m, e, segs } = o.meter, a = clamp((t - m.t) / 0.25), k = outCubic(clamp((t - m.t - 0.15) / 0.9)) * (m.value ?? 1);
        e.style.opacity = String(a); segs.forEach((g, i) => { g.style.background = i / segs.length < k ? pal.voice : "rgba(255,255,255,0.14)"; }); }
      if (o.cursor) { const { c, e, ring } = o.cursor, k = smooth(clamp((t - c.t[0]) / Math.max(0.1, c.t[1] - c.t[0])));
        const x = (c.from[0] + (c.to[0] - c.from[0]) * k) * W, y = (c.from[1] + (c.to[1] - c.from[1]) * k - Math.sin(k * Math.PI) * 0.04) * H, cl = clamp((t - c.t[1]) / 0.35);
        e.style.opacity = String(clamp((t - c.t[0] + 0.1) / 0.15)); e.style.transform = `translate(${x}px,${y}px) scale(${c.click !== false && cl > 0 && cl < 0.4 ? 0.82 : 1})`;
        ring.style.opacity = String(c.click === false || cl <= 0 ? 0 : 1 - cl); ring.style.transform = `translate(${x - U * 0.04}px,${y - U * 0.04}px) scale(${0.3 + cl * 1.6})`; ring.style.width = ring.style.height = U * 0.08 + "px"; }
    }
    if (!world) world = buildWorld();
    world.forEach((w) => { (w.fan || []).forEach((m) => { m.visible = false; }); (w.strip || []).forEach((m) => { m.visible = false; }); });
    const w = world[si];
    if (w.fan) { const f = s.fan, n = w.fan.length, R = f.radius || 30;
      w.fan.forEach((m, i) => { const a = clamp((t - f.t - i * 0.09) / 0.42); if (a <= 0) return;
        const ang = (i - (n - 1) / 2) * (f.spread || 0.2), e = outBack(a);
        m.position.set(f.at[0] + Math.sin(ang) * R, f.at[1] - (1 - outCubic(a)) * 6 + Math.cos(ang) * 1.5 + Math.sin(t * 1.4 + i) * 0.12, f.at[2] + (1 - Math.cos(ang)) * R * 0.9);
        m.rotation.set(-0.08, -ang * 1.1, (i - (n - 1) / 2) * -0.03); m.scale.setScalar(e); m.visible = true; }); }
    if (w.strip) { const f = s.strip, n = w.strip.length, k = clamp((t - f.t[0]) / Math.max(0.1, f.t[1] - f.t[0])), cw = (f.w || 7) * 1.06;
      w.strip.forEach((m, i) => { const u = i - (n - 1) / 2 + (0.5 - k) * n * 1.5, x = u * cw;      // the strip runs through the frame
        const bend = x * 0.045;
        m.position.set(f.at[0] + x * Math.cos(0.5), f.at[1] + Math.sin(bend) * 3 - x * 0.08, f.at[2] + x * Math.sin(0.5) + Math.cos(bend * 2) * 1.2);
        m.rotation.set(Math.sin(bend) * 0.25, -0.5 + bend * 0.4, -0.12 - bend * 0.15); m.visible = t >= f.t[0] && t <= f.t[1] + 0.2; }); }
  }
  return { draw };
}
