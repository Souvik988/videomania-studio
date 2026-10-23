// node motion-shots.test.cjs — structural checks for the MKS shot library (no browser needed)
const assert = require("node:assert/strict");
global.window = global;
window.MK = require("./motion-kit.js");
require("./motion-shots.js");
const MKS = window.MKS;

let n = 0;
const ok = (c, m) => { assert.ok(c, m); n++; };
const want = ["orbit", "casualCam", "uiWorld", "frameBreak", "digitalZoom", "phoneMockup", "checklist", "headlineWall", "zoomThrough",
  "chartGrid", "pullbackReveal", "greenScreen", "paperCut", "doodleBoil", "vertigo", "coverStory", "glassType", "slideUpText"];
want.forEach((k) => ok(typeof MKS[k] === "function", `MKS.${k} exists`));
ok(MKS.NAMES.length === 18 && want.every((k) => MKS.NAMES.includes(k)), "NAMES lists the 18 effects");
["circle", "underline", "arrow", "star", "squiggle", "check"].forEach((k) => ok(/^M[\d., CLMZ-]+$/.test(MKS.DOODLES[k]), `doodle ${k} uses absolute pairs`));
// every doodle has an even count of numbers (x,y pairs), which the pixel scaler relies on
Object.entries(MKS.DOODLES).forEach(([k, d]) => ok((d.match(/-?\d*\.?\d+/g) || []).length % 2 === 0, `doodle ${k} has x,y pairs`));
// log-space camera: at p=0 the frame shows `from`, and the transform is a pure translate+scale
const fake = { style: {} };
const tl = { fromTo: (t, a, b) => { b.onUpdate && (a.p = 1, t.p = 1, b.onUpdate()); return tl; } };
const st = MKS.logCam(tl, fake, 0, { x: 0, y: 0, w: 1920, h: 1080 }, { x: 960, y: 540, w: 480, h: 270 }, 1, { W: 1920, H: 1080 });
ok(/scale\(4\)/.test(fake.style.transform), "logCam lands on the target rect (scale 4)");
ok(/translate\(-3840px, -2160px\)/.test(fake.style.transform), "logCam centres the target rect (centre 1200,675 × 4)");
console.log(`motion-shots: ${n} checks passed`);
