// node talking-character.test.cjs — structural + determinism checks for MKTC (no browser needed)
const assert = require("node:assert/strict");
global.window = global;
window.MK = require("./motion-kit.js");
const MKTC = require("./talking-character.js");
let n = 0;
const ok = (c, m) => { assert.ok(c, m); n++; };

ok(["rig", "show", "look", "reaction", "blinkTimes", "switches", "pose", "vectorMouth"].every((k) => typeof MKTC[k] === "function"), "API present");
ok(MKTC.MOUTH_KEYS.join("") === "XABCDEFGH", "nine mouth shapes X A-H");
MKTC.MOUTH_KEYS.forEach((k) => ok(/<svg/.test(MKTC.vectorMouth(k)), `vector mouth ${k}`));

// blinks: deterministic, spaced, inside the clip
const b1 = MKTC.blinkTimes(7, 30), b2 = MKTC.blinkTimes(7, 30), b3 = MKTC.blinkTimes(8, 30);
ok(JSON.stringify(b1) === JSON.stringify(b2), "blinks are deterministic for a seed");
ok(JSON.stringify(b1) !== JSON.stringify(b3), "a different seed gives a different schedule");
ok(b1[0] >= 0.8 && b1[b1.length - 1] < 30, "blinks stay inside the clip and skip the first 0.8 s");
const gaps = b1.slice(1).map((t, i) => t - b1[i]);
ok(gaps.every((g) => g >= 0.27), "no blink closer than 0.27 s");
ok(b1.length >= 5 && b1.length <= 16, `plausible blink count for 30 s (${b1.length})`);

// switches: collapses repeats and sub-frame holds
const cues = [{ t0: 0, t1: .1, v: "X" }, { t0: .1, t1: .2, v: "X" }, { t0: .2, t1: .21, v: "D" }, { t0: .21, t1: .5, v: "C" }, { t0: .5, t1: .8, v: "C" }, { t0: .8, t1: 1, v: "A" }];
const sw = MKTC.switches(cues, 1 / 30);
ok(sw.map((s) => s.v).join("") === "XCA", `switches collapse to XCA, got ${sw.map((s) => s.v).join("")}`);
ok(sw.every((s, i) => i === 0 || s.t > sw[i - 1].t), "switch times strictly increase");

// pose: bounded, small
const env = Array.from({ length: 300 }, (_, i) => (Math.sin(i / 7) + 1) / 2);
let maxY = 0, maxR = 0;
for (let i = 0; i < 300; i++) { const p = MKTC.pose(env, i, 30); maxY = Math.max(maxY, Math.abs(p.y)); maxR = Math.max(maxR, Math.abs(p.rot)); ok(p.sc >= 1 && p.sc < 1.02, "scale stays within 2%"); }
ok(maxY < 14 && maxR < 4, `head motion stays small (y ${maxY.toFixed(1)}, rot ${maxR.toFixed(1)})`);

// rig builds against a fake DOM + timeline and makes only seek-safe calls
const calls = { set: 0, fromTo: 0, to: 0 };
const tl = { set: () => { calls.set++; return tl; }, fromTo: (t, a, b) => { calls.fromTo++; ok(b.immediateRender === false, "fromTo has immediateRender:false"); return tl; }, to: () => { calls.to++; return tl; } };
const mkEl = () => ({ style: {}, setAttribute() {}, appendChild() {}, set innerHTML(v) {} });
global.document = { createElement: mkEl, querySelector: mkEl };
global.gsap = { set() {} };
const track = { fps: 30, duration: 6, cues: [{ t0: 0, t1: 1, v: "X" }, { t0: 1, t1: 1.3, v: "D" }, { t0: 1.3, t1: 2, v: "C" }, { t0: 2, t1: 6, v: "X" }], env: new Array(180).fill(0.3), accents: [1.2, 3.4] };
const ch = MKTC.rig(tl, mkEl(), 2, { x: 0, y: 0, w: 500, track, seed: 3 });
ok(ch.root && ch.head && ch.aim && Object.keys(ch.mouths).length === 9, "rig returns root/aim/head and nine mouths");
ok(calls.to === 0, "no implicit-start tl.to calls (all fromTo)");
ok(calls.set > 8 && calls.fromTo > 60, `rig emitted ${calls.set} sets and ${calls.fromTo} fromTos`);
MKTC.show(tl, ch, 2, 8); MKTC.look(tl, ch, 3, { x: .8, y: 0 }); MKTC.reaction(tl, ch, 4, "surprise");
ok(calls.to === 0, "show/look/reaction add no implicit-start tweens either");
console.log(`talking-character: ${n} checks passed`);
