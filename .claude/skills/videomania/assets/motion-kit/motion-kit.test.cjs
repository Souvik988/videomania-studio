// node motion-kit.test.cjs: pure-maths checks for motion-kit.js (no browser needed)
const assert = require("node:assert/strict");
const MK = require("./motion-kit.js");

let passed = 0;
const test = (name, fn) => { fn(); passed++; console.log("ok  " + name); };
const near = (a, b, eps, msg) => assert.ok(Math.abs(a - b) <= eps, `${msg}: ${a} vs ${b}`);

test("rng is deterministic per seed and differs across seeds", () => {
  const a = MK.rng(42), b = MK.rng(42), c = MK.rng(43);
  const sa = [a(), a(), a()], sb = [b(), b(), b()], sc = [c(), c(), c()];
  assert.deepEqual(sa, sb);
  assert.notDeepEqual(sa, sc);
  sa.forEach((v) => assert.ok(v >= 0 && v < 1));
});

test("hash is stateless and in [0,1)", () => {
  assert.equal(MK.hash(5, 2), MK.hash(5, 2));
  for (let i = 0; i < 200; i++) { const v = MK.hash(i, 3); assert.ok(v >= 0 && v < 1); }
});

test("bezier endpoints and linear case", () => {
  const lin = MK.bezier(0.25, 0.25, 0.75, 0.75);
  [0, 0.1, 0.37, 0.5, 0.9, 1].forEach((p) => near(lin(p), p, 1e-4, "linear bezier"));
  const g = MK.ease.glide;
  near(g(0), 0, 1e-9, "glide 0"); near(g(1), 1, 1e-9, "glide 1");
  let prev = 0;
  for (let p = 0.01; p <= 1; p += 0.01) { const v = g(p); assert.ok(v >= prev - 1e-6, "glide monotonic"); prev = v; }
  near(MK.bezier(0.42, 0, 0.58, 1)(0.5), 0.5, 1e-4, "ease-in-out symmetric midpoint");
});

test("spring settles at 1 and its overshoot follows damping", () => {
  const tight = MK.spring({ stiffness: 260, damping: 24 });
  const soft = MK.spring({ stiffness: 200, damping: 12 });
  const crit = MK.spring({ stiffness: 200, damping: 2 * Math.sqrt(200) });
  [tight, soft, crit].forEach((s) => { near(s.ease(0), 0, 1e-9, "spring starts at 0"); assert.equal(s.ease(1), 1); near(s.ease(0.999), 1, 0.01, "spring settles"); });
  assert.ok(soft.overshoot > tight.overshoot, "less damping overshoots more");
  assert.ok(crit.overshoot < 1e-3, "critically damped does not overshoot");
  assert.ok(tight.duration > 0.2 && tight.duration < 3, `tight duration sane: ${tight.duration}`);
  assert.equal(MK.spring({ stiffness: 260, damping: 24 }).ease(0.4), tight.ease(0.4), "deterministic");
});

test("fitWindow centres the window exactly", () => {
  const f = MK.fitWindow({ x: 100, y: 200, w: 540, h: 960 }, { w: 1080, h: 1920 });
  near(f.scale, 2, 1e-9, "scale");
  near(100 * f.scale + f.x, 0, 1e-9, "left edge to 0");
  near((200 + 960) * f.scale + f.y, 1920, 1e-9, "bottom edge to frame bottom");
});

test("snap rounds to frame boundaries", () => {
  near(MK.snap(1.01, 30), 1.0, 1e-9, "snap down"); near(MK.snap(1.02, 30), 1.0333333, 1e-6, "snap up");
});

test("number formatting: intl and indian grouping", () => {
  assert.equal(MK.formatNumber(50000, { prefix: "₹", group: "indian" }), "₹50,000");
  assert.equal(MK.formatNumber(1234567, { group: "indian" }), "12,34,567");
  assert.equal(MK.formatNumber(1234567, { group: "intl" }), "1,234,567");
  assert.equal(MK.formatNumber(12.345, { decimals: 1, suffix: "%" }), "12.3%");
});

test("keyhole path is a closed polygon around the centre", () => {
  const s = MK.keyholePath(540, 900, 100);
  assert.ok(s.startsWith("polygon(") && s.endsWith(")"));
  assert.ok(s.split(",").length > 30);
});

console.log(`\n${passed} tests passed`);
