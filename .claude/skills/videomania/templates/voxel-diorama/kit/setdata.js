// Voxel-diorama kit: sets as data. A set is a JSON file (sets/<name>.json) that lists prefabs, boxes,
// plates and lights. No code is needed to make a new world: the set builder (crew/04b-set-builder.md)
// writes this file from a concept picture, renders it with scripts/set_preview.py and compares.
//
// {
//   "name": "cafe", "about": "...", "palette": { "wood": "#8e4d24" },      colours usable as "$wood"
//   "marks": { "door": [x, y, z] },                                        named places for cast and cameras
//   "cams":  { "wide": { "from": [..], "to": [..], "look": [..], "fov": 34 } },   this set's own camera presets
//   "castLight": { "key": "#ffb057", "keySide": -1, "rim": "#19c8b9", "rimSide": 1, "shade": 0.3 },   how sprites are lit here (-1 = from the left)
//   "screen": { "at": [x, y, z], "w": 17, "h": 10 },                       optional monitor the film can draw on
//   "items": [
//     { "prefab": "table", "at": [x, y, z], "size": [w, h, d], "color": "$wood", "rot": 0 },
//     { "box": [x, y, z, w, h, d], "color": "#222", "glow": 0 },
//     { "vox": [x, y, z, w, h, d], "color": "#2f9e58", "unit": 0.5, "jitter": 0.03 },
//     { "plate": { "paint": "skyline", "at": [x, y, z], "w": 200, "h": 60, "glow": 1.5, "opts": {...} } },
//     { "plate": { "src": "assets/plates/hills.png", "at": [x, y, z], "w": 160, "h": 60 } },
//     { "relief": { "src": "assets/plates/vista.png", "depth": "assets/plates/vista_depth.png", "at": [x, y, z], "w": 240, "h": 160, "amount": 40 } },
//     { "light": { "kind": "point", "color": "#ffb057", "intensity": 300, "at": [x, y, z], "dist": 80 } }
//   ]
// }
// Units: 1 = one voxel, y up, floor at y = 0, +z towards the camera. A prefab's `at` is the point on the
// floor under its centre; `size` is [width, height, depth]; `rot` is 0, 90, 180 or 270 degrees.
import { paintSky, paintSkyline, WINS } from "./sets.js";

const BOOKS = ["#c8121f", "#19c8b9", "#ffb057", "#e8e2d6", "#3b4a8a", "#7a2e2e", "#2f9e58", "#d9a57c"];

function local(V, at, rot) {   // a box in the prefab's own space -> the world, turned in 90 degree steps
  const r = (((rot || 0) % 360) + 360) % 360;
  const T = (x, z, w, d) => r === 0 ? [at[0] + x, at[2] + z, w, d] : r === 90 ? [at[0] + z, at[2] - x - w, d, w]
    : r === 180 ? [at[0] - x - w, at[2] - z - d, w, d] : [at[0] - z - d, at[2] + x, d, w];
  const B = (x, y, z, w, h, d, c, o) => { const [wx, wz, ww, wd] = T(x, z, w, d); V.box(wx, at[1] + y, wz, ww, h, wd, c, o); };
  const P = (x, y, z) => { const [wx, wz] = T(x, z, 0, 0); return [wx, at[1] + y, wz]; };
  return { B, P };
}

export const PREFABS = {
  // surfaces ------------------------------------------------------------------------------------------
  floor(V, p, { B }) { const [w, , d] = p.size || [80, 0, 60], k = p.plank || 2;
    for (let i = 0; i < w / k; i++) B(-w / 2 + i * k, -1, -d / 2, k - 0.06, 1, d, i % 3 === 0 ? (p.color2 || p.color) : p.color, { jitter: 0.012 }); },
  wall(V, p, { B }) {   // slats along x; an optional opening { x, y, w, h } (x from the wall's centre) gets a frame
    const [w, h, t] = p.size || [80, 40, 1], k = p.slat || 2, o = p.window;
    for (let i = 0; i < w / k; i++) {
      const x = -w / 2 + i * k, c = i % 2 ? p.color : (p.color2 || p.color);
      if (o && x + k > o.x - o.w / 2 && x < o.x + o.w / 2) { B(x, 0, -t / 2, k - 0.1, o.y, t, c); B(x, o.y + o.h, -t / 2, k - 0.1, h - o.y - o.h, t, c); }
      else B(x, 0, -t / 2, k - 0.1, h, t, c);
    }
    B(-w / 2, 0, t / 2, w, 1.1, 0.4, p.trim || "#150c0c");
    if (o) { const f = p.frame || "#6a3716", x0 = o.x - o.w / 2;
      B(x0 - 0.6, o.y - 0.6, -t / 2, o.w + 1.2, 0.6, t + 0.6, f); B(x0 - 0.6, o.y + o.h, -t / 2, o.w + 1.2, 0.6, t + 0.6, f);
      B(x0 - 0.6, o.y, -t / 2, 0.6, o.h, t + 0.6, f); B(x0 + o.w, o.y, -t / 2, 0.6, o.h, t + 0.6, f);
      for (let i = 1; i < (o.panes || 3); i++) B(x0 + (o.w * i) / (o.panes || 3) - 0.2, o.y, 0, 0.4, o.h, 0.4, f);
      B(x0, o.y + o.h * 0.5 - 0.2, 0, o.w, 0.4, 0.4, f); } },
  rug(V, p, { B }) { const [w, , d] = p.size || [30, 0, 16], c2 = p.color2 || p.color, c3 = p.color3 || p.color;
    for (let x = -w / 2; x <= w / 2; x += 0.5) for (let z = -d / 2; z <= d / 2; z += 0.5) {
      const q = p.round === false ? Math.max(Math.abs(x) / (w / 2), Math.abs(z) / (d / 2)) ** 2 : (x * x) / ((w * w) / 4) + (z * z) / ((d * d) / 4);
      if (q <= 1) B(x, 0, z, 0.5, 0.25, 0.5, q > 0.9 ? c2 : q > 0.62 ? p.color : q > 0.55 ? c3 : q > 0.2 ? p.color : c2); } },
  // furniture -----------------------------------------------------------------------------------------
  table(V, p, { B }) { const [w, h, d] = p.size || [8, 6, 8], c = p.color || "#8e4d24", s = p.color2 || "#6a3716";
    B(-w / 2, h - 0.6, -d / 2, w, 0.6, d, c); B(-w / 2, h - 0.8, -d / 2, w, 0.2, d, s);
    if (p.round) { B(-0.5, 0.4, -0.5, 1, h - 1.2, 1, s); B(-1.6, 0, -1.6, 3.2, 0.4, 3.2, s); }
    else [[-w / 2 + 0.3, -d / 2 + 0.3], [w / 2 - 1, -d / 2 + 0.3], [-w / 2 + 0.3, d / 2 - 1], [w / 2 - 1, d / 2 - 1]].forEach(([x, z]) => B(x, 0, z, 0.7, h - 0.8, 0.7, s)); },
  chair(V, p, { B }) { const [w, h, d] = p.size || [4, 8, 4], c = p.color || "#5a3a28", sh = h * 0.45;
    B(-w / 2, sh, -d / 2, w, 0.6, d, c); B(-w / 2, sh + 0.6, -d / 2, w, h - sh - 0.6, 0.6, c); B(-w / 2, h - 0.5, -d / 2, w, 0.5, 0.7, p.color2 || c);
    [[-w / 2, -d / 2], [w / 2 - 0.5, -d / 2], [-w / 2, d / 2 - 0.5], [w / 2 - 0.5, d / 2 - 0.5]].forEach(([x, z]) => B(x, 0, z, 0.5, sh, 0.5, p.legs || "#2c2c33")); },
  stool(V, p, { B }) { const h = (p.size || [3, 6, 3])[1], c = p.color || "#c8121f";
    B(-1.5, h - 0.7, -1.5, 3, 0.7, 3, c); B(-1.2, h - 0.9, -1.2, 2.4, 0.2, 2.4, p.color2 || "#2c2c33"); B(-0.3, 0.3, -0.3, 0.6, h - 1.2, 0.6, "#44444e"); B(-1.3, 0, -1.3, 2.6, 0.3, 2.6, "#2c2c33"); B(-1.1, h * 0.35, -1.1, 2.2, 0.2, 2.2, "#44444e"); },
  counter(V, p, { B }) { const [w, h, d] = p.size || [22, 8, 6], c = p.color || "#6a3716";
    B(-w / 2, 0, -d / 2, w, h - 0.6, d, c); B(-w / 2 - 0.3, h - 0.6, -d / 2 - 0.3, w + 0.6, 0.6, d + 0.6, p.top || "#e8e2d6");
    for (let i = 0; i < w / 3; i++) B(-w / 2 + 0.4 + i * 3, 0.8, d / 2, 2.2, h - 2.2, 0.15, p.color2 || "#8e4d24"); B(-w / 2, 0, d / 2, w, 0.6, 0.3, "#150c0c"); },
  shelf(V, p, { B }) { const [w, h, d] = p.size || [16, 24, 3], rows = p.rows || 4, c = p.color || "#6a3716", rh = h / rows;
    B(-w / 2, 0, -d / 2, 0.5, h, d, c); B(w / 2 - 0.5, 0, -d / 2, 0.5, h, d, c); B(-w / 2, 0, -d / 2, w, h, 0.3, p.back || "#1c1010");
    for (let r = 0; r <= rows; r++) B(-w / 2, r * rh - (r === rows ? 0.4 : 0), -d / 2, w, 0.4, d, c);
    for (let r = 0; r < rows; r++) { let x = -w / 2 + 0.7;
      while (x < w / 2 - 1.2) {
        if (V.rnd() > 0.88) { B(x + 0.3, r * rh + 0.4, -d / 2 + 0.8, 1, 1, 1, [p.accent || "#19c8b9", "#ff6a1a", "#ffd166"][Math.floor(V.rnd() * 3)], { glow: 1.4 }); x += 2; continue; }
        const bw = 0.3 + Math.floor(V.rnd() * 3) * 0.2, bh = rh * (0.45 + V.rnd() * 0.4);
        B(x, r * rh + 0.4, -d / 2 + 0.5, bw, bh, d - 1, BOOKS[Math.floor(V.rnd() * BOOKS.length)], { jitter: 0.03 }); x += bw + 0.08; } } },
  sofa(V, p, { B }) { const [w, h, d] = p.size || [14, 7, 6], c = p.color || "#3b4a8a", s = p.color2 || c;
    B(-w / 2, 1, -d / 2, w, 2.4, d, c); B(-w / 2, 3.4, -d / 2, w, h - 3.4, 1.6, s); B(-w / 2, 1, -d / 2, 1.6, 4.2, d, s); B(w / 2 - 1.6, 1, -d / 2, 1.6, 4.2, d, s);
    [[-w / 2 + 0.3, -d / 2 + 0.3], [w / 2 - 0.9, -d / 2 + 0.3], [-w / 2 + 0.3, d / 2 - 0.9], [w / 2 - 0.9, d / 2 - 0.9]].forEach(([x, z]) => B(x, 0, z, 0.6, 1, 0.6, "#2c2c33")); },
  crate(V, p, { B }) { const [w, h, d] = p.size || [4, 4, 4], c = p.color || "#3a2418"; B(-w / 2, 0, -d / 2, w, h, d, c); B(-w / 2 - 0.1, h * 0.45, -d / 2 - 0.1, w + 0.2, 0.4, d + 0.2, p.color2 || "#2a1a14"); },
  stairs(V, p, { B }) { const [w, h, d] = p.size || [8, 12, 12], n = p.steps || 8;
    for (let i = 0; i < n; i++) B(-w / 2, 0, d / 2 - (i + 1) * (d / n), w, (i + 1) * (h / n), d / n, i % 2 ? p.color : (p.color2 || p.color)); },
  door(V, p, { B }) { const [w, h] = p.size || [7, 15, 1], c = p.color || "#6a3716"; B(-w / 2, 0, -0.3, w, h, 0.6, c); B(-w / 2 + 0.8, h * 0.55, 0.3, w - 1.6, h * 0.35, 0.1, p.glass || "#7ff0e4", { glow: 0.5 }); B(w / 2 - 1.4, h * 0.45, 0.3, 0.5, 0.5, 0.5, "#ffd166", { glow: 1.2 }); },
  // small things ----------------------------------------------------------------------------------------
  plant(V, p, { B, P }) { const [r, h] = p.size || [2.6, 9], g = p.colors || ["#2f9e58", "#1f7a43", "#46b96c"];
    B(-1.3, 0, -1.3, 2.6, 0.5, 2.6, "#93411f"); B(-1.1, 0.5, -1.1, 2.2, 1.6, 2.2, p.pot || "#b8552e");
    const n = Math.round(110 * r * (h / 9) / 2.6);
    for (let i = 0; i < n; i++) { const a = V.rnd() * 6.283, rr = Math.pow(V.rnd(), 0.6) * r, yy = V.rnd();
      B(Math.cos(a) * rr * (1 - yy * 0.5) - 0.25, 2.1 + yy * (h - 2.1), Math.sin(a) * rr * (1 - yy * 0.5) - 0.25, 0.5, 0.5, 0.5, g[Math.floor(V.rnd() * g.length)]); } },
  tree(V, p, { B }) { const [r, h] = p.size || [5, 20], g = p.colors || ["#2f9e58", "#1f7a43", "#46b96c"];
    B(-0.8, 0, -0.8, 1.6, h * 0.5, 1.6, p.trunk || "#5a3a28");
    for (let i = 0; i < 420; i++) { const a = V.rnd() * 6.283, b = Math.acos(2 * V.rnd() - 1), rr = Math.pow(V.rnd(), 0.5) * r;
      B(Math.sin(b) * Math.cos(a) * rr - 0.35, h * 0.7 + Math.cos(b) * rr * 0.8, Math.sin(b) * Math.sin(a) * rr - 0.35, 0.7, 0.7, 0.7, g[Math.floor(V.rnd() * g.length)]); } },
  cup(V, p, { B }) { B(-0.5, 0, -0.5, 1, 1.2, 1, p.color || "#efe6d2"); B(0.5, 0.4, -0.15, 0.3, 0.5, 0.3, p.color || "#efe6d2"); B(-0.35, 1.2, -0.35, 0.7, 0.05, 0.7, "#4a2c1c"); },
  machine(V, p, { B }) {   // an espresso machine
    B(-3, 0, -2, 6, 5, 4, p.color || "#c9c4b6"); B(-3, 5, -2, 6, 0.6, 4, "#8d8a85"); B(-2.4, 2.2, 2, 4.8, 0.4, 1, "#44444e"); B(-1.6, 1, 2, 0.5, 1.2, 0.5, "#2c2c33"); B(1.1, 1, 2, 0.5, 1.2, 0.5, "#2c2c33");
    B(-2.2, 3.6, 2, 0.6, 0.6, 0.1, "#e11d2e", { glow: 1.6 }); B(-1.2, 3.6, 2, 0.6, 0.6, 0.1, "#19c8b9", { glow: 1.4 }); B(1, 5.6, -1, 1.4, 2.4, 1.4, "#44444e"); },
  case(V, p, { B }) {   // a glass pastry case: a lit box with small coloured things inside
    const [w, h, d] = p.size || [8, 4, 4]; B(-w / 2, 0, -d / 2, w, 0.4, d, "#44444e"); B(-w / 2, h - 0.3, -d / 2, w, 0.3, d, "#44444e");
    [[-w / 2, -d / 2], [w / 2 - 0.3, -d / 2], [-w / 2, d / 2 - 0.3], [w / 2 - 0.3, d / 2 - 0.3]].forEach(([x, z]) => B(x, 0.4, z, 0.3, h - 0.7, 0.3, "#44444e"));
    B(-w / 2 + 0.3, 0.4, -d / 2 + 0.3, w - 0.6, 0.15, d - 0.6, "#fff1c9", { glow: 1.3 });
    for (let i = 0; i < w - 1.5; i += 1.4) B(-w / 2 + 0.8 + i, 0.55, -0.5 + (i % 2) * 0.6, 0.9, 0.7, 0.9, ["#ffb057", "#d9645a", "#efe6d2", "#7a2e2e"][Math.floor(i) % 4]); },
  picture(V, p, { B }) { const [w, h] = p.size || [6, 5]; B(-w / 2, 0, -0.15, w, h, 0.3, "#0f0f13"); B(-w / 2 + 0.5, 0.5, 0.15, w - 1, h - 1, 0.12, p.color || "#e11d2e", { glow: p.glow ?? 1.1 }); },
  "monitor-frame"(V, p, { B }) { const [w, h] = p.size || [18, 10.6]; B(-2.5, 0, -1.3, 5, 0.4, 2.6, "#2c2c33"); B(-0.6, 0.4, -0.35, 1.2, 3, 0.7, "#44444e"); B(-w / 2, 3.2, -0.35, w, h, 0.7, "#0f0f13"); },
  // lights ----------------------------------------------------------------------------------------------
  pendant(V, p, { B, P }) { const top = p.top ?? 38, y = p.size ? p.size[1] : 22, c = p.color || "#ffc94a";
    B(-0.1, y + 2.4, -0.1, 0.2, top - y - 2.4, 0.2, "#2c2c33");
    for (let i = 0; i < 4; i++) { const w = 4.4 - i * 0.9; B(-w / 2, y + i * 0.6, -w / 2, w, 0.6, w, i === 0 ? c : "#2c2c33", i === 0 ? { glow: 2.6 } : {}); }
    V.light({ kind: "point", color: p.light || "#ffb057", intensity: p.intensity ?? 260, at: P(0, y - 1.5, 0), dist: p.dist || 70 }); },
  floorlamp(V, p, { B, P }) { const h = (p.size || [3, 17])[1], c = p.color || "#19c8b9";
    B(-1, 0, -1, 2, 0.4, 2, "#2c2c33"); B(-0.25, 0.4, -0.25, 0.5, h, 0.5, "#44444e");
    for (let x = -1.5; x < 1.5; x += 0.5) for (let y = 0; y < 3; y += 0.5) for (let z = -1.5; z < 1.5; z += 0.5) B(x, h + 0.4 + y, z, 0.5, 0.5, 0.5, c, { glow: 1.5 });
    V.light({ kind: "point", color: c, intensity: p.intensity ?? 90, at: P(0, h, 2), dist: 50 }); },
  desklamp(V, p, { B, P }) { const c = p.color || "#ffc94a"; B(-1.3, 0, -1.3, 2.6, 0.4, 2.6, "#2c2c33"); B(-0.25, 0.4, -0.25, 0.5, 6.4, 0.5, "#44444e");
    for (let i = 0; i < 6; i++) { const w = 5 - i * 0.6; B(-w / 2, 6.6 + i * 0.5, -w / 2, w, 0.5, w, c, { glow: 2.7 - i * 0.18 }); }
    V.light({ kind: "point", color: p.light || "#ffb057", intensity: p.intensity ?? 420, at: P(0, 6, 0.5), dist: 90 }); },
  streetlamp(V, p, { B, P }) { const h = (p.size || [1, 22])[1]; B(-0.3, 0, -0.3, 0.6, h, 0.6, "#2c2c33"); B(-0.3, h, -0.3, 5, 0.5, 0.6, "#2c2c33");
    for (let x = 3; x < 4.5; x += 0.5) for (let z = -0.75; z < 0.75; z += 0.5) B(x, h - 1.5, z, 0.5, 1.5, 0.5, "#ffe2a8", { glow: 2.6 });
    V.light({ kind: "point", color: "#ffd9a0", intensity: p.intensity ?? 260, at: P(4, h - 3, 2), dist: 70 }); },
  neon(V, p, { B }) {   // glowing bars: segments [[x, y, w, h], ...] in the sign's own plane
    (p.segments || [[-4, 0, 8, 0.6], [-4, 3, 8, 0.6], [-4, 0, 0.6, 3.6], [3.4, 0, 0.6, 3.6]]).forEach(([x, y, w, h]) => B(x, y, 0, w, h, 0.3, p.color || "#ff5a4e", { glow: p.glow ?? 2.4 })); },
  stringlights(V, p) { const a = p.from, b = p.to, n = p.count || 36, cs = p.colors || ["#ffc94a", "#ff6a1a", "#19c8b9", "#fff1c9"];
    for (let i = 0; i <= n; i++) { const u = i / n; V.box(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u - Math.sin(u * Math.PI) * (p.sag ?? 4), a[2] + (b[2] - a[2]) * u + Math.sin(u * 9) * 1.1, 0.36, 0.36, 0.36, cs[i % cs.length], { glow: 2.4 }); } },
  dust(V, p) { const [x, y, z, w, h, d] = p.box || [-28, 2, 2, 56, 22, 30];
    for (let i = 0; i < (p.count || 140); i++) V.box(x + V.rnd() * w, y + V.rnd() * h, z + V.rnd() * d, 0.1, 0.1, 0.1, p.color || "#ffd9a0", { glow: 1.2 + V.rnd() }); },
  railing(V, p, { B }) { const w = (p.size || [80, 3.4])[0], h = (p.size || [80, 3.4])[1]; for (let x = -w / 2; x < w / 2; x += 1.5) B(x, 0, 0, 0.25, h, 0.25, p.color || "#0c0c12"); B(-w / 2, h, 0, w, 0.3, 0.3, p.color || "#0c0c12"); },
  // far distance: a night city in flat layers (the 2.5D way) ---------------------------------------------------
  city(V, p) { const [x, y, z] = p.at, s = p.scale || 1, moon = p.moon === false ? null : { x: 0.56, y: 0.3, r: 26, c: "#ffe9b8" };
    V.plate({ at: [x, y + 18 * s, z - 100 * s], w: 300 * s, h: 150 * s, px: [1024, 512], solid: true, glow: 0.9, draw: paintSky(p.sky || "#0a0d24", p.horizon || "#2a1a3e", 160, moon) });
    V.plate({ at: [x, y, z - 60 * s], w: 220 * s, h: 60 * s, px: [2048, 560], glow: 1.5, draw: paintSkyline({ color: "#141a33", wins: WINS, rate: 0.16, minH: 0.35, maxH: 0.9, bw: [50, 110], cell: 9 }) });
    V.plate({ at: [x + 2, y - 4 * s, z - 24 * s], w: 130 * s, h: 44 * s, px: [2048, 700], glow: 1.9, draw: paintSkyline({ color: "#0a0d1c", wins: WINS, rate: 0.3, minH: 0.3, maxH: 0.95, bw: [110, 230], cell: 16 }) }); },
};

const PAINT = { sky: (o) => paintSky(o.top || "#0a0d24", o.bottom || "#2a1a3e", o.stars ?? 160, o.moon || null), skyline: (o) => paintSkyline(Object.assign({ color: "#141a33", wins: WINS, rate: 0.2, minH: 0.3, maxH: 0.9, bw: [60, 140], cell: 10 }, o)) };

/** Fill the collector V from a set description. Returns { marks, cams, screen, plates } for the engine. */
export function buildFromData(V, data, opt = {}) {
  const pal = Object.assign({ accent: opt.accent, voice: opt.voice, voice2: opt.voice2 }, data.palette || {});
  const col = (c) => (typeof c === "string" && c[0] === "$" ? pal[c.slice(1)] || "#ff00ff" : c);
  const fix = (o) => { const r = {}; for (const [k, v] of Object.entries(o)) r[k] = /^(color|color2|color3|top|trim|frame|pot|light|back|accent|glass|legs|trunk)$/.test(k) ? col(v) : k === "colors" ? v.map(col) : v; return r; };
  const filePlates = [];
  const run = (items, off) => {
    for (const raw of items || []) {
      const sh = (a) => [a[0] + off[0], a[1] + off[1], a[2] + off[2]];
      if (raw.repeat) { const n = raw.repeat.count || 1, st = raw.repeat.step || [0, 0, 0]; for (let i = 0; i < n; i++) run(raw.items, [off[0] + st[0] * i, off[1] + st[1] * i, off[2] + st[2] * i]); continue; }
      const it = fix(raw);
      if (it.prefab) { const fn = PREFABS[it.prefab]; if (!fn) { console.warn("unknown prefab", it.prefab); continue; }
        const p = Object.assign({}, it, { at: sh(it.at || [0, 0, 0]) }); if (p.from) { p.from = sh(p.from); p.to = sh(p.to); } if (p.box) p.box = [...sh(p.box), ...p.box.slice(3)];
        fn(V, p, local(V, p.at, p.rot)); }
      else if (it.box) { const [x, y, z] = sh(it.box); V.box(x, y, z, it.box[3], it.box[4], it.box[5], it.color, { glow: it.glow || 0, jitter: it.jitter || 0 }); }
      else if (it.vox) { const [x, y, z] = sh(it.vox); V.vox(x, y, z, it.vox[3], it.vox[4], it.vox[5], it.color, { glow: it.glow || 0, jitter: it.jitter || 0, unit: it.unit || 1 }); }
      else if (it.plate) { const pl = Object.assign({}, it.plate, { at: sh(it.plate.at) });
        if (pl.src) filePlates.push(pl); else V.plate(Object.assign(pl, { draw: (PAINT[pl.paint] || PAINT.sky)(pl.opts || {}) })); }
      else if (it.relief) V.relief(Object.assign({}, it.relief, { at: sh(it.relief.at) }));
      else if (it.light) V.light(Object.assign({}, it.light, { color: col(it.light.color), at: it.light.at ? sh(it.light.at) : undefined }));
    }
  };
  run(data.items, [0, 0, 0]);
  return { marks: data.marks || {}, cams: data.cams || {}, screen: data.screen || null, castLight: data.castLight || null, filePlates };
}
