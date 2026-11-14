// Voxel-diorama kit: sets. A set is a function that fills a collector `V`.
//   V.box(x, y, z, w, h, d, colour, {glow})        one solid block (min corner + size, in voxels; y is up)
//   V.vox(x, y, z, w, h, d, colour, {unit, jitter}) the same volume as separate small cubes (unit 0.5 = fine detail)
//   V.plate({ at, w, h, px, draw(ctx, w, h, rnd), glow, solid })   a flat art layer at a depth (2.5D)
//   V.light({ kind, color, intensity, at, dist })
// Units: 1 = one voxel. The floor is y = 0. The stage (where the cast stands) is around (0, 0, 8).
//
// House rules for sets (user notes, 2026-11-13): fine detail, never big squares; clean; and depth in
// layers: every view has a foreground, the subject, a middle ground and a far distance. Far distance is
// built the 2D-game way, with flat plates at different depths behind a window or a horizon, so near
// layers cross the frame faster than far ones when the camera moves.
// Add a set by exporting another function and listing it in SETS; add its named places to MARKS.

// ---- plate painters -------------------------------------------------------------------------------
export function paintSky(top, bottom, stars = 140, moon = null) {
  return (x, w, h, rnd) => {
    const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, top); g.addColorStop(1, bottom);
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    for (let i = 0; i < stars; i++) { x.fillStyle = `rgba(255,255,255,${0.25 + rnd() * 0.6})`; const s = rnd() > 0.9 ? 3 : 2; x.fillRect(rnd() * w, rnd() * h * 0.7, s, s); }
    if (moon) { x.fillStyle = moon.c; x.beginPath(); x.arc(w * moon.x, h * moon.y, moon.r, 0, 7); x.fill(); x.fillStyle = top; x.beginPath(); x.arc(w * moon.x + moon.r * 0.4, h * moon.y - moon.r * 0.25, moon.r * 0.9, 0, 7); x.fill(); }
  };
}
export function paintSkyline(o) {   // { color, wins:[colours], rate, minH, maxH, bw:[min,max], cell }
  return (x, w, h, rnd) => {
    let px = 0;
    while (px < w) {
      const bw = o.bw[0] + rnd() * (o.bw[1] - o.bw[0]), bh = h * (o.minH + rnd() * (o.maxH - o.minH)), top = h - bh;
      x.fillStyle = o.color; x.fillRect(px, top, bw - 3, bh);
      if (rnd() > 0.55) x.fillRect(px + bw * 0.3, top - 10, bw * 0.12, 10);
      if (rnd() > 0.7) x.fillRect(px + bw * 0.55, top - 22, 3, 22);
      const c = o.cell || 12;
      for (let wy = top + c; wy < h - c; wy += c * 1.6) for (let wx = px + c * 0.6; wx < px + bw - c * 1.2; wx += c * 1.35)
        if (rnd() < o.rate) { x.fillStyle = o.wins[Math.floor(rnd() * o.wins.length)]; x.fillRect(wx, wy, c * 0.62, c * 0.85); }
      px += bw;
    }
  };
}
export const WINS = ["#ffd98a", "#ffb057", "#fff1c9", "#7ff0e4", "#ff6a5a"];

// ---- studio: a creator's room at night -------------------------------------------------------------
export function studio(V, opt = {}) {
  const P = { wall: "#221414", wall2: "#2a1919", trim: "#150c0c", floor: "#1a0f0e", floor2: "#20130f", desk: "#8e4d24", deskS: "#6a3716", deskH: "#a85f30",
    rug: opt.rug || "#c8121f", rug2: opt.rug2 || "#9b0d17", rug3: "#e0343f", metal: "#2c2c33", metalH: "#44444e", dark: "#0f0f13", key: "#e8e2d6",
    lamp: "#ffc94a", plant: "#2f9e58", plant2: "#1f7a43", plant3: "#46b96c", pot: "#b8552e", potS: "#93411f", paper: "#efe6d2", accent: opt.accent || "#19c8b9",
    voice: opt.voice || "#e11d2e", voice2: opt.voice2 || "#ff6a1a" };
  const r = V.rnd;
  // floor: thin planks
  for (let i = -30; i < 30; i++) V.box(i * 2, -1, -20, 1.94, 1, 62, i % 3 === 0 ? P.floor2 : P.floor, { jitter: 0.012 });
  // back wall: wooden slats, with a window opening (x 14..34, y 9..27) onto the night city
  const WX0 = 14, WX1 = 34, WY0 = 9, WY1 = 27;
  for (let i = -30; i < 30; i++) {
    const x = i * 2, c = i % 2 ? P.wall : P.wall2;
    if (x >= WX0 && x < WX1) { V.box(x, 0, -20, 1.9, WY0, 1, c); V.box(x, WY1, -20, 1.9, 42 - WY1, 1, c); }
    else V.box(x, 0, -20, 1.9, 42, 1, c);
  }
  V.box(-60, 0, -19.2, 120, 1.2, 0.5, P.trim);                                             // skirting
  V.box(WX0 - 0.6, WY0 - 0.6, -19.6, WX1 - WX0 + 1.2, 0.6, 1.2, P.deskS); V.box(WX0 - 0.6, WY1, -19.6, WX1 - WX0 + 1.2, 0.6, 1.2, P.deskS);
  V.box(WX0 - 0.6, WY0, -19.6, 0.6, WY1 - WY0, 1.2, P.deskS); V.box(WX1, WY0, -19.6, 0.6, WY1 - WY0, 1.2, P.deskS);
  V.box((WX0 + WX1) / 2 - 0.2, WY0, -19.4, 0.4, WY1 - WY0, 0.5, P.deskS); V.box(WX0, (WY0 + WY1) / 2 - 0.2, -19.4, WX1 - WX0, 0.4, 0.5, P.deskS);
  // the far distance, in three flat layers behind the window (2.5D parallax)
  V.plate({ at: [24, 24, -120], w: 300, h: 150, px: [1024, 512], solid: true, glow: 0.9, draw: paintSky("#0a0d24", "#2a1a3e", 160, { x: 0.56, y: 0.3, r: 26, c: "#ffe9b8" }) });
  V.plate({ at: [24, 6, -80], w: 220, h: 60, px: [2048, 560], glow: 1.5, draw: paintSkyline({ color: "#141a33", wins: WINS, rate: 0.16, minH: 0.35, maxH: 0.9, bw: [50, 110], cell: 9 }) });
  V.plate({ at: [26, 2, -44], w: 130, h: 44, px: [2048, 700], glow: 1.9, draw: paintSkyline({ color: "#0a0d1c", wins: WINS, rate: 0.3, minH: 0.3, maxH: 0.95, bw: [110, 230], cell: 16 }) });
  // left wall
  for (let k = -10; k < 22; k++) V.box(-41, 0, k * 2, 1, 42, 1.9, k % 2 ? P.wall : P.wall2);
  // rug: clean rings
  for (let x = -15; x <= 15; x += 0.5) for (let z = -8; z <= 8; z += 0.5) {
    const d = (x * x) / 225 + (z * z) / 64; if (d > 1) continue;
    V.box(x, 0, 8 + z, 0.5, 0.25, 0.5, d > 0.9 ? P.rug2 : d > 0.62 ? P.rug : d > 0.55 ? P.rug3 : d > 0.2 ? P.rug : P.rug2);
  }
  // desk with a drawer unit
  V.box(-15, 7.4, -14, 30, 0.6, 12, P.desk); V.box(-15, 7.2, -14, 30, 0.2, 12, P.deskH); V.box(-15, 6.6, -14, 30, 0.6, 12, P.deskS);
  [[-14.4, -13.4], [-14.4, -3.2]].forEach(([x, z]) => V.box(x, 0, z, 0.8, 6.6, 0.8, P.deskS));
  V.box(8, 0.6, -13.6, 6.4, 6, 11, P.deskS); [1.2, 3.2, 5.2].forEach((y) => { V.box(8.3, y, -2.7, 5.8, 1.6, 0.2, P.desk); V.box(10.6, y + 0.7, -2.5, 1.2, 0.25, 0.2, P.metalH); });
  // desk mat, keyboard, mouse, mug, notes, books
  V.box(-9, 8, -7.5, 18, 0.12, 6, "#17171c");
  V.box(-6, 8.12, -6.4, 11, 0.45, 3.6, P.metal);
  for (let x = 0; x < 20; x++) for (let z = 0; z < 6; z++) V.box(-5.75 + x * 0.53, 8.57, -6.15 + z * 0.55, 0.42, 0.18, 0.44, (x * 3 + z) % 11 === 0 ? P.accent : (x + z * 5) % 17 === 0 ? P.voice2 : P.key);
  V.box(6, 8.12, -5.6, 1.1, 0.5, 1.8, P.key);
  V.vox(-9.5, 8, -5.5, 1.5, 2, 1.5, P.paper, { unit: 0.5, jitter: 0.02 }); V.box(-8, 8.6, -5, 0.5, 1, 0.5, P.paper);
  [[4, P.voice2], [5.2, P.accent], [3.2, "#ffd166"]].forEach(([x, c], i) => V.box(x, 8.12, -9 - i * 0.2, 1, 0.06, 1, c, { glow: 0.9 }));
  [["#3b4a8a", 0], ["#7a2e2e", 0.5], ["#e8e2d6", 1.0]].forEach(([c, y]) => V.box(10, 8 + y, -11.5, 3.6 - y, 0.5, 2.6, c));
  // monitor: thin bezel on a stand (the screen plane is added by the engine at MARKS.screen)
  V.box(-2.5, 8, -11, 5, 0.4, 2.6, P.metal); V.box(-0.6, 8.4, -10.2, 1.2, 3, 0.7, P.metalH);
  V.box(-9, 11.2, -10.9, 18, 10.6, 0.7, P.dark); V.box(-9, 11, -10.6, 18, 0.3, 0.5, P.metalH);
  // desk lamp: base, arm, a fine stepped shade that glows
  V.box(-13.2, 8, -9.4, 2.6, 0.4, 2.6, P.metal); V.box(-12.2, 8.4, -8.4, 0.5, 6.4, 0.5, P.metalH);
  for (let i = 0; i < 6; i++) { const w = 5 - i * 0.6; V.box(-12 - w / 2, 14.6 + i * 0.5, -8.15 - w / 2, w, 0.5, w, P.lamp, { glow: 2.7 - i * 0.18 }); }
  // plant: fine leaves in a rounded crown
  V.box(10.6, 8, -11.4 + 4, 2.8, 0.5, 2.8, P.potS); V.vox(10.8, 8.5, -7.2, 2.5, 1.5, 2.5, P.pot, { unit: 0.5, jitter: 0.03 });
  for (let i = 0; i < 260; i++) {
    const a = r() * 6.283, rr = Math.pow(r(), 0.6) * 2.6, yy = r();
    V.box(12 + Math.cos(a) * rr * (1 - yy * 0.5), 10 + yy * 6.5, -6 + Math.sin(a) * rr * (1 - yy * 0.5), 0.5, 0.5, 0.5, [P.plant, P.plant2, P.plant3][Math.floor(r() * 3)]);
  }
  // chair
  V.box(-3, 4, -8.6, 6, 0.8, 5, "#5a3a28"); V.box(-2.6, 4.8, -4, 5.2, 4.2, 0.6, "#5a3a28"); V.box(-2.6, 8.4, -4, 5.2, 0.6, 0.7, "#6d4832");
  V.box(-3.3, 5.6, -8.2, 0.5, 0.4, 4.4, P.metalH); V.box(2.8, 5.6, -8.2, 0.5, 0.4, 4.4, P.metalH);
  V.box(-0.4, 0.5, -6.4, 0.8, 3.5, 0.8, P.metal); [[-2.4, -6.2], [1.6, -6.2], [-0.4, -8.4], [-0.4, -4]].forEach(([x, z]) => V.box(x, 0, z, 0.8, 0.5, 0.8, P.metal));
  // shelves on the back wall: thin book spines and a few glowing trinkets
  const books = ["#c8121f", "#19c8b9", "#ffb057", "#e8e2d6", "#3b4a8a", "#7a2e2e", "#2f9e58", "#d9a57c"];
  [[-38, 13], [-38, 20.5], [-38, 28], [-12, 28]].forEach(([sx, sy], si) => {
    const len = si === 3 ? 22 : 20;
    V.box(sx, sy, -19, len, 0.4, 2.2, P.deskS);
    let x = sx + 0.3;
    while (x < sx + len - 1) {
      if (r() > 0.86) { V.box(x + 0.4, sy + 0.4, -18.4, 1, 1, 1, [P.accent, P.voice2, "#ffd166"][Math.floor(r() * 3)], { glow: 1.5 }); x += 2.2; continue; }
      const w = 0.3 + Math.floor(r() * 3) * 0.2, h = 2.4 + Math.floor(r() * 6) * 0.4;
      V.box(x, sy + 0.4, -18.8, w, h, 1.6, books[Math.floor(r() * books.length)], { jitter: 0.03 }); x += w + 0.08;
    }
  });
  // framed prints that glow softly: they become the colour blobs behind the cast
  [[-34, 4, P.voice, 1.2], [-25, 5, P.voice2, 1.0], [40, 12, P.accent, 1.1], [46, 24, P.voice, 1.0]].forEach(([x, y, c, gl]) => {
    V.box(x, y, -19.1, 6, 5, 0.3, P.dark); V.box(x + 0.5, y + 0.5, -18.9, 5, 4, 0.15, c, { glow: gl });
  });
  [[2, 10, P.accent], [16, 14, P.voice], [30, 22, P.voice2]].forEach(([z, y, c]) => { V.box(-40.2, y, z, 0.3, 4.4, 5.4, P.dark); V.box(-40, y + 0.4, z + 0.4, 0.15, 3.6, 4.6, c, { glow: 1.0 }); });
  // a cool floor lamp on the right, for colour contrast and middle-ground depth
  V.box(27, 0, -13, 2, 0.4, 2, P.metal); V.box(27.75, 0.4, -12.25, 0.5, 17, 0.5, P.metalH); V.vox(26.5, 17.4, -13.5, 3, 3, 3, P.accent, { unit: 0.5, glow: 1.5 });
  // foreground: string lights overhead and dust in the air between the lens and the stage
  const bulbs = [P.lamp, P.voice2, P.accent, "#fff1c9"];
  for (let i = 0; i <= 40; i++) { const u = i / 40, x = -36 + u * 72, sag = Math.sin(u * Math.PI) * 4; V.box(x, 27 - sag + Math.sin(u * 22) * 0.2, 17 + Math.sin(u * 9) * 1.2, 0.36, 0.36, 0.36, bulbs[i % 4], { glow: 2.4 }); }
  for (let i = 0; i <= 30; i++) { const u = i / 30, x = -30 + u * 60, sag = Math.sin(u * Math.PI) * 3; V.box(x, 22.5 - sag, 25 + Math.cos(u * 7) * 1.5, 0.3, 0.3, 0.3, bulbs[(i + 2) % 4], { glow: 2.2 }); }
  for (let i = 0; i < 150; i++) V.box(-28 + r() * 56, 2 + r() * 22, 2 + r() * 30, 0.1, 0.1, 0.1, "#ffd9a0", { glow: 1.2 + r() });
  V.box(-24, 0, 20, 5, 4, 4, "#2a1a14"); V.box(-23.4, 4, 20.6, 3.8, 2.4, 2.8, "#3a2418");                 // crates, front left
  V.light({ kind: "point", color: "#ffb057", intensity: 440, at: [-12, 14, -7.5], dist: 90 });
  V.light({ kind: "point", color: "#ffc08f", intensity: 170, at: [-6, 20, 22], dist: 70 });
  V.light({ kind: "point", color: "#bfeee8", intensity: 60, at: [0, 16, -6], dist: 40, decay: 1.8 });
  V.light({ kind: "point", color: opt.accent || "#19c8b9", intensity: 90, at: [28, 17, -10], dist: 50 });
  V.light({ kind: "dir", color: P.voice, intensity: 0.7, at: [-30, 18, -20] });
  V.light({ kind: "dir", color: "#7f8fd9", intensity: 0.25, at: [30, 14, 24] });
  V.light({ kind: "hemi", color: "#6a5a7a", ground: "#140909", intensity: 0.5 });
}

// ---- city-night: an outdoor set made only of flat layers (the 2D-game way) --------------------------
export function cityNight(V, opt = {}) {
  const voice = opt.voice || "#e11d2e", accent = opt.accent || "#19c8b9", r = V.rnd;
  V.plate({ at: [0, 40, -220], w: 520, h: 240, px: [1024, 512], solid: true, glow: 0.9, draw: paintSky("#070a1e", "#3a1f45", 220, { x: 0.68, y: 0.34, r: 30, c: "#ffe9b8" }) });
  V.plate({ at: [0, 22, -170], w: 420, h: 90, px: [2048, 440], glow: 1.2, draw: paintSkyline({ color: "#1a2142", wins: WINS, rate: 0.1, minH: 0.25, maxH: 0.85, bw: [40, 90], cell: 7 }) });
  V.plate({ at: [10, 18, -110], w: 300, h: 80, px: [2048, 546], glow: 1.6, draw: paintSkyline({ color: "#111730", wins: WINS, rate: 0.2, minH: 0.3, maxH: 0.95, bw: [80, 170], cell: 11 }) });
  V.plate({ at: [-12, 16, -62], w: 210, h: 70, px: [2048, 682], glow: 2.0, draw: paintSkyline({ color: "#0a0d1c", wins: WINS, rate: 0.32, minH: 0.35, maxH: 1, bw: [150, 300], cell: 18 }) });
  // street: pavement, kerb, lane marks, two street lamps, a low wall with neon in the middle ground
  V.box(-140, -1, -60, 280, 1, 110, "#101018");
  for (let i = -14; i < 14; i++) V.box(i * 10, 0, -18, 5, 0.06, 0.6, "#3a3a44");
  V.box(-140, 0, -8, 280, 0.5, 1, "#24242e");
  for (let i = -30; i < 30; i++) V.box(i * 2, 0, -7, 1.94, 0.3, 30, i % 2 ? "#17171f" : "#1b1b24", { jitter: 0.01 });
  [[-22, voice], [24, accent]].forEach(([x, c]) => {
    V.box(x, 0, -10, 0.6, 22, 0.6, "#2c2c33"); V.box(x, 22, -10, 5, 0.5, 0.6, "#2c2c33"); V.vox(x + 3.5, 20.5, -10.5, 1.5, 1.5, 1.5, "#ffe2a8", { unit: 0.5, glow: 2.6 });
    V.light({ kind: "point", color: "#ffd9a0", intensity: 260, at: [x + 4, 19, -8], dist: 70 });
    V.box(x - 7, 0, -30, 14, 7, 1, "#161622"); V.box(x - 6, 2, -29.4, 12, 0.5, 0.2, c, { glow: 2.0 }); V.box(x - 6, 4.4, -29.4, 8, 0.5, 0.2, c, { glow: 1.6 });
  });
  for (let i = 0; i < 60; i++) { const x = -44 + i * 1.5; V.box(x, 0, 22, 0.25, 3 + (i % 7 === 0 ? 1.5 : 0), 0.25, "#0c0c12"); }    // railing, foreground
  V.box(-45, 3, 22, 90, 0.3, 0.3, "#0c0c12");
  for (let i = 0; i < 160; i++) V.box(-40 + r() * 80, 1 + r() * 26, -20 + r() * 50, 0.1, 0.1, 0.1, "#bfd9ff", { glow: 1 + r() });
  V.light({ kind: "hemi", color: "#6f7fd0", ground: "#0a0a12", intensity: 0.75 });
  V.light({ kind: "dir", color: voice, intensity: 0.5, at: [-30, 20, -30] });
}

export function voidSet(V, opt = {}) {
  const c = opt.accent || "#19c8b9";
  V.box(-80, -1, -80, 160, 1, 160, "#050707");
  for (let i = -24; i <= 24; i++) {
    const strong = i % 2 === 0;
    V.box(i * 3 - 0.04, 0, -72, strong ? 0.1 : 0.05, 0.05, 144, c, { glow: strong ? 0.6 : 0.3 });
    V.box(-72, 0, i * 3 - 0.04, 144, 0.05, strong ? 0.1 : 0.05, c, { glow: strong ? 0.6 : 0.3 });
  }
  for (let i = 0; i < 120; i++) V.box(-30 + V.rnd() * 60, 1 + V.rnd() * 22, -30 + V.rnd() * 60, 0.1, 0.1, 0.1, c, { glow: 0.8 + V.rnd() });
  V.light({ kind: "hemi", color: "#7fd9d0", ground: "#050707", intensity: 0.5 });
}

export const SETS = { studio, void: voidSet, "city-night": cityNight };
export const HAS_SCREEN = { studio: true };

// Named places. [x, y, z] in voxels.
export const MARKS = {
  stage: [0, 0, 8], "stage-left": [-5, 0, 8], "stage-right": [5, 0, 9], "stage-front": [0, 0, 13],
  "desk-left": [-19, 0, -4], "desk-right": [19, 0, -4], desk: [0, 8, -8], screen: [0, 16.5, -10.1],
  lamp: [-12, 16, -8], window: [24, 18, -20], centre: [0, 0, 0], "centre-left": [-6, 0, 0], "centre-right": [6, 0, 1],
  street: [0, 0, 6], "street-left": [-6, 0, 6], "street-right": [6, 0, 7],
};
