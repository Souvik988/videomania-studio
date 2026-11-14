// Voxel-diorama kit: the cast. Original pixel-art characters drawn by code on a fine grid.
// A character is a function (pose, state) -> grid of colours. Parts are blocked in at coarse scale
// (b = 2x2 fine pixels per unit), then detailed in fine pixels (f): a shade tone on the side away from
// the light, a highlight, rounded corners, and one dark outline pixel around the silhouette.
// House rule: sprites are at least 60 px tall; big square pixels read as cheap.
// Add a character by adding a drawer to CAST; add a pose by adding a branch. Never trace someone else's character.

const OUT = "#120c14";

class Grid {
  constructor(w, h) { this.w = w; this.h = h; this.px = new Array(w * h).fill(null); }
  r(x, y, w, h, c) {
    for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++)
      if (i >= 0 && j >= 0 && i < this.w && j < this.h) this.px[j * this.w + i] = c;
  }
  get(x, y) { return x >= 0 && y >= 0 && x < this.w && y < this.h ? this.px[y * this.w + x] : null; }
  /** Clear the four corner pixels of a box (n = corner size), so blocks read as rounded. */
  round(x, y, w, h, n = 1) {
    for (let k = 0; k < n; k++) for (let m = 0; m < n - k; m++) {
      this.r(x + m, y + k, 1, 1, null); this.r(x + w - 1 - m, y + k, 1, 1, null);
      this.r(x + m, y + h - 1 - k, 1, 1, null); this.r(x + w - 1 - m, y + h - 1 - k, 1, 1, null);
    }
  }
  /** Recolour pixels of colour `from` inside a box (for shade bands that follow the part's shape). */
  tint(x, y, w, h, from, to) {
    for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) if (this.get(i, j) === from) this.px[j * this.w + i] = to;
  }
  outline(c = OUT) {
    const o = this.px.slice();
    for (let j = 0; j < this.h; j++) for (let i = 0; i < this.w; i++) {
      if (this.px[j * this.w + i]) continue;
      if (this.get(i - 1, j) || this.get(i + 1, j) || this.get(i, j - 1) || this.get(i, j + 1)) o[j * this.w + i] = c;
    }
    this.px = o;
  }
}

// ---- Mani: the host. Headphones, mustard hoodie, indigo hair. 60 x 68 fine grid. ----
const M = { skin: "#f4cda6", skinS: "#dba882", skinH: "#fbe0c2", blush: "#ee9d8a", hair: "#2b2440", hairL: "#4a3d6e", hairD: "#1c1730",
  phone: "#19c8b9", phoneS: "#0e8f86", phoneH: "#7ff0e4", hood: "#f5b21a", hoodS: "#cf8d0c", hoodH: "#ffd257",
  pants: "#2c3046", pantsS: "#1d2032", shoe: "#f4f1ea", shoeS: "#c9c4b6", eye: "#1a1420", mouth: "#7a2e2e", tongue: "#d9645a", white: "#ffffff" };

function drawMani(pose, st) {
  const act = pose; if (pose === "jump") pose = "cheer";
  const g = new Grid(60, 68), X = 10, Y = 2;
  const b = (x, y, w, h, c) => g.r(x * 2 + X, y * 2 + Y, w * 2, h * 2, c);   // coarse block
  const f = (x, y, w, h, c) => g.r(x + X, y + Y, w, h, c);                   // fine pixels
  const rd = (x, y, w, h, n) => g.round(x + X, y + Y, w, h, n);
  const tn = (x, y, w, h, a, c) => g.tint(x + X, y + Y, w, h, a, c);

  // legs and shoes
  if (pose === "sit") {   // legs forward, feet towards the viewer
    f(13, 44, 7, 6, M.pants); f(24, 44, 7, 6, M.pants); f(19, 45, 1, 5, M.pantsS); f(30, 45, 1, 5, M.pantsS);
    f(12, 50, 9, 4, M.shoe); f(23, 50, 9, 4, M.shoe); f(12, 53, 9, 1, M.shoeS); f(23, 53, 9, 1, M.shoeS); rd(12, 50, 9, 4, 1); rd(23, 50, 9, 4, 1);
  } else if (pose === "fly") {   // legs together, trailing
    f(16, 44, 12, 13, M.pants); f(21, 44, 2, 13, M.pantsS); f(26, 45, 2, 12, M.pantsS); f(15, 57, 14, 4, M.shoe); f(15, 60, 14, 1, M.shoeS); rd(15, 57, 14, 4, 1);
  } else if (pose === "walk") {   // one leg planted, the other lifted; they swap on the alt frame
    const A = st.alt ? 14 : 24, Bx = st.alt ? 24 : 14;
    f(A - 2, 44, 6, 14, M.pants); f(A + 3, 44, 1, 14, M.pantsS); f(A - 4, 58, 9, 4, M.shoe); f(A - 4, 61, 9, 1, M.shoeS); rd(A - 4, 58, 9, 4, 1);
    f(Bx + 1, 44, 6, 10, M.pants); f(Bx + 6, 44, 1, 10, M.pantsS); f(Bx + 1, 54, 8, 4, M.shoe); f(Bx + 1, 57, 8, 1, M.shoeS); rd(Bx + 1, 54, 8, 4, 1);
  } else {
    b(7, 22, 3, 7, M.pants); b(12, 22, 3, 7, M.pants);
    tn(18, 44, 2, 14, M.pants, M.pantsS); tn(28, 44, 2, 14, M.pants, M.pantsS); f(14, 50, 6, 1, M.pantsS); f(24, 51, 6, 1, M.pantsS);
    b(6, 29, 4, 2, M.shoe); b(12, 29, 4, 2, M.shoe);
    f(12, 61, 8, 1, M.shoeS); f(24, 61, 8, 1, M.shoeS); rd(12, 58, 8, 4, 1); rd(24, 58, 8, 4, 1);
  }
  // hoodie body
  b(6, 13, 10, 9, M.hood);
  tn(28, 26, 4, 18, M.hood, M.hoodS); f(12, 40, 20, 4, M.hoodS); f(12, 26, 3, 16, M.hoodH);
  f(16, 35, 12, 4, M.hoodS); f(17, 35, 10, 1, M.hood); f(16, 39, 12, 1, M.hoodS);        // pocket
  f(17, 26, 10, 3, M.hoodS); f(19, 26, 6, 2, M.hood);                                    // hood collar
  f(20, 28, 1, 6, M.white); f(23, 28, 1, 5, M.white); f(20, 34, 1, 1, M.shoeS); f(23, 33, 1, 1, M.shoeS);
  rd(12, 26, 20, 18, 1);
  // neck and head
  f(19, 23, 6, 3, M.skinS);
  b(6, 4, 10, 8, M.skin); rd(12, 8, 20, 16, 2);
  tn(29, 9, 3, 15, M.skin, M.skinS); f(14, 22, 16, 2, M.skinS); rd(12, 8, 20, 16, 2); f(13, 12, 2, 6, M.skinH);
  f(14, 18, 3, 2, M.blush); f(27, 18, 3, 2, M.blush);
  // hair: a cap with a swept fringe and a highlight strand
  b(6, 1, 10, 3, M.hair); b(5, 2, 12, 3, M.hair); f(12, 8, 20, 3, M.hair);
  f(12, 11, 7, 2, M.hair); f(12, 13, 4, 1, M.hair); f(25, 11, 7, 2, M.hair); f(28, 13, 4, 1, M.hair);
  f(16, 3, 10, 1, M.hairL); f(14, 5, 5, 1, M.hairL); f(27, 5, 3, 6, M.hairD); f(20, 11, 4, 1, M.hairD);
  rd(10, 2, 24, 8, 2);
  // headphones: band over the hair, a cup on each ear with a highlight
  f(10, 0, 24, 2, M.phone); f(12, 0, 8, 1, M.phoneH); f(8, 1, 3, 10, M.phone); f(33, 1, 3, 10, M.phone); rd(8, 0, 28, 3, 1);
  f(6, 10, 6, 10, M.phone); f(32, 10, 6, 10, M.phone); f(7, 11, 2, 6, M.phoneH); f(35, 12, 2, 7, M.phoneS); f(9, 12, 2, 7, M.phoneS);
  rd(6, 10, 6, 10, 1); rd(32, 10, 6, 10, 1);
  // face
  if (st.blink) { f(16, 16, 4, 1, M.eye); f(24, 16, 4, 1, M.eye); }
  else { f(16, 14, 4, 4, M.eye); f(24, 14, 4, 4, M.eye); f(16, 14, 2, 2, M.white); f(24, 14, 2, 2, M.white); f(19, 17, 1, 1, M.hairL); f(27, 17, 1, 1, M.hairL); }
  f(15, 12, 5, 1, M.hair); f(24, 12, 5, 1, M.hair);                                      // brows
  if (pose === "cheer" || pose === "fly" || pose === "wave") { f(19, 19, 6, 3, M.mouth); f(20, 21, 4, 1, M.tongue); f(19, 19, 6, 1, M.white); }
  else if (st.mouth) { f(20, 19, 4, 3, M.mouth); f(21, 21, 2, 1, M.tongue); }
  else if (pose === "think") f(20, 20, 3, 1, M.mouth);
  else { f(19, 20, 6, 1, M.mouth); f(18, 19, 1, 1, M.mouth); f(25, 19, 1, 1, M.mouth); }   // a small smile
  // arms by pose (the pointing arm is on the viewer's right)
  const hand = (x, y) => { f(x, y, 4, 4, M.skin); f(x + 3, y + 1, 1, 3, M.skinS); rd(x, y, 4, 4, 1); };
  const armDown = (x) => { f(x, 26, 4, 16, M.hood); f(x + 3, 27, 1, 15, M.hoodS); f(x, 40, 4, 2, M.hoodS); rd(x, 26, 4, 16, 1); hand(x, 42); };
  if (pose === "point") { armDown(8); f(32, 26, 4, 6, M.hood); f(32, 28, 12, 4, M.hood); f(32, 31, 12, 1, M.hoodS); f(42, 28, 2, 4, M.hoodS); hand(44, 28); }
  else if (pose === "wave") { armDown(8); const up = st.alt ? 0 : 2; f(32, 24, 4, 6, M.hood); f(36, 10 + up, 4, 16 - up, M.hood); f(39, 11 + up, 1, 15 - up, M.hoodS); hand(36 + (st.alt ? 2 : -1), 6 + up); }
  else if (pose === "fly") {   // one fist forward (up, since the sprite is turned to fly head first), the other arm back
    f(8, 24, 4, 6, M.hood); f(5, 6, 4, 20, M.hood); f(8, 7, 1, 19, M.hoodS); hand(5, 2); armDown(32);
  }
  else if (pose === "cheer") {
    f(8, 24, 4, 6, M.hood); f(4, 8, 4, 18, M.hood); f(7, 9, 1, 17, M.hoodS); hand(4, 4);
    f(32, 24, 4, 6, M.hood); f(36, 8, 4, 18, M.hood); f(39, 9, 1, 17, M.hoodS); hand(36, 4);
  } else if (pose === "think") { armDown(8); f(32, 26, 4, 10, M.hood); f(28, 32, 6, 4, M.hood); f(26, 24, 4, 9, M.hood); f(29, 25, 1, 8, M.hoodS); hand(26, 21); }
  else if (pose === "talk") {
    armDown(8);
    if (st.alt) { f(32, 26, 4, 8, M.hood); f(34, 30, 8, 4, M.hood); f(34, 33, 8, 1, M.hoodS); hand(40, 26); }
    else { f(32, 26, 4, 10, M.hood); f(34, 32, 8, 4, M.hood); f(34, 35, 8, 1, M.hoodS); hand(42, 32); }
  } else if (pose === "walk") {   // arms swing against the legs
    const sw = (x, up) => { f(x, 26, 4, 13 - up, M.hood); f(x + 3, 27, 1, 12 - up, M.hoodS); rd(x, 26, 4, 13 - up, 1); hand(x + (up ? (x < 20 ? -2 : 2) : 0), 39 - up); };
    sw(8, st.alt ? 4 : 0); sw(32, st.alt ? 0 : 4);
  } else { armDown(8); armDown(32); }
  g.outline();
  return g;
}

// ---- Bit: the sidekick. A small CRT-monitor robot with a pixel face. 32 x 34 fine grid. ----
const B = { shell: "#ece9df", shellS: "#bdb8a8", shellH: "#ffffff", screen: "#0d2b2a", screenL: "#14403d", face: "#3cf0dd", faceD: "#1fb5a6",
  leg: "#8d8a85", legS: "#6b6964", foot: "#3a3836", tip: "#ff4b3e", tipH: "#ffb0a8" };

function drawBit(pose, st) {
  const g = new Grid(32, 34), Y = pose === "jump" ? 0 : 2;
  const f = (x, y, w, h, c) => g.r(x, y + Y, w, h, c);
  const rd = (x, y, w, h, n) => g.round(x, y + Y, w, h, n);
  // antenna
  f(15, 2, 2, 4, B.leg); f(16, 2, 1, 4, B.legS); f(14, 0, 4, 3, st.blink ? B.leg : B.tip); if (!st.blink) f(14, 0, 2, 1, B.tipH); rd(14, 0, 4, 3, 1);
  // shell with a bevel, then the screen
  f(4, 6, 24, 18, B.shell); f(4, 22, 24, 2, B.shellS); f(26, 6, 2, 18, B.shellS); f(4, 6, 24, 1, B.shellH); f(4, 6, 1, 16, B.shellH); rd(4, 6, 24, 18, 2);
  f(6, 8, 20, 13, B.screen); f(6, 8, 20, 1, B.screenL); f(7, 9, 6, 1, B.screenL); f(7, 10, 3, 1, B.screenL); rd(6, 8, 20, 13, 1);
  f(22, 22, 3, 1, B.leg); f(7, 22, 2, 1, B.tip);                                          // vents and a power light
  if (pose === "happy" || pose === "jump" || pose === "fly") {
    [[9, 14], [10, 13], [11, 12], [12, 13], [13, 14], [18, 14], [19, 13], [20, 12], [21, 13], [22, 14]].forEach(([x, y]) => f(x, y, 1, 2, B.face));
    f(12, 17, 8, 2, B.face); f(11, 16, 1, 2, B.face); f(20, 16, 1, 2, B.face); f(13, 19, 6, 1, B.faceD);
  } else {
    if (st.blink) { f(10, 13, 4, 1, B.face); f(18, 13, 4, 1, B.face); }
    else { f(10, 11, 4, 4, B.face); f(18, 11, 4, 4, B.face); f(10, 11, 1, 1, B.screen); f(13, 14, 1, 1, B.screen); f(18, 11, 1, 1, B.screen); f(21, 14, 1, 1, B.screen); f(12, 12, 1, 1, B.shellH); f(20, 12, 1, 1, B.shellH); }
    if (st.mouth) { f(14, 16, 4, 3, B.face); f(15, 17, 2, 1, B.screen); } else { f(12, 17, 8, 1, B.face); f(11, 16, 1, 1, B.face); f(20, 16, 1, 1, B.face); }
  }
  // legs and feet
  const ly = 24, lh = pose === "jump" ? 2 : 4, l1 = pose === "walk" && st.alt ? 2 : lh, l2 = pose === "walk" && !st.alt ? 2 : lh;
  f(8, ly, 4, l1, B.leg); f(20, ly, 4, l2, B.leg); f(11, ly, 1, l1, B.legS); f(23, ly, 1, l2, B.legS);
  if (pose === "fly") { f(9, ly + 4, 3, st.alt ? 4 : 3, "#ffb347"); f(21, ly + 4, 3, st.alt ? 3 : 4, "#ffb347"); f(10, ly + 5, 1, 2, "#fff1c9"); f(22, ly + 5, 1, 2, "#fff1c9"); }
  f(6, ly + l1, 8, 2, B.foot); f(18, ly + l2, 8, 2, B.foot); rd(6, ly + l1, 8, 2, 1); rd(18, ly + l2, 8, 2, 1);
  g.outline();
  return g;
}

export const CAST = {
  mani: { draw: drawMani, w: 60, h: 68, px: 0.18, poses: ["idle", "talk", "point", "cheer", "think", "walk", "fly", "sit", "wave", "jump"], head: 0.78 },
  bit: { draw: drawBit, w: 32, h: 34, px: 0.18, poses: ["idle", "talk", "happy", "jump", "walk", "fly"], head: 0.55 },
};

const cache = new Map();
/** A canvas of the sprite at one device pixel per grid pixel (the engine scales it with nearest filtering). */
export function spriteCanvas(who, pose, st = {}) {
  const def = CAST[who];
  if (!def) throw new Error(`unknown cast member '${who}'`);
  if (!def.poses.includes(pose)) pose = "idle";
  const key = `${who}|${pose}|${st.blink ? 1 : 0}${st.mouth ? 1 : 0}${st.alt ? 1 : 0}`;
  if (cache.has(key)) return cache.get(key);
  const g = def.draw(pose, st);
  const c = document.createElement("canvas");
  c.width = g.w; c.height = g.h;
  const x = c.getContext("2d");
  for (let j = 0; j < g.h; j++) for (let i = 0; i < g.w; i++) {
    const col = g.px[j * g.w + i];
    if (col) { x.fillStyle = col; x.fillRect(i, j, 1, 1); }
  }
  cache.set(key, c);
  return c;
}
