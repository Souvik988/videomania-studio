// node typography/tests/type-kit.test.cjs — structural checks of the browser runtime against the config.
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const root = path.resolve(__dirname, "..");
const read = (p) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const reg = read("config/font-registry.json");
const presets = read("config/typography-presets.json").presets;
const pairs = read("config/pairing-presets.json").pairings;

const roles = {};
for (const [k, r] of Object.entries(reg.roles)) roles[k] = { css: r.css_family, stack: "serif", load: ["400"], animations: r.animations, line_height: r.line_height, tracking_em: r.tracking_em };
global.window = { TK_CONFIG: { roles, pairings: Object.fromEntries(pairs.map((p) => [p.id, p])), presets: Object.fromEntries(presets.map((p) => [p.id, p])) } };
eval(fs.readFileSync(path.join(root, "src/type-kit.js"), "utf8"));
const TK = window.TK;

let n = 0;
const ok = (c, m) => { assert.ok(c, m); n++; };
for (const [k, r] of Object.entries(reg.roles)) for (const a of r.animations) ok(typeof TK.anim[a] === "function", `${k}: ${a} implemented`);
for (const p of presets) for (const [k, v] of Object.entries(p.animation)) if (/in$/.test(k) && typeof v === "string") ok(typeof TK.anim[v] === "function", `${p.id}: ${v}`);
ok(TK.ANIMS.length >= 23, "23+ animation presets");
ok(TK.depth("soft").includes("rgba(0,0,0"), "soft depth shadow");
ok(TK.depth("hard", "74,11,6").startsWith("0 .045em 0 rgba(74,11,6"), "hard depth tints its extrusion");
ok(TK.applyCase("your content needs", "sentence") === "Your content needs", "sentence case");
ok(TK.applyCase("start pairing", "title") === "Start Pairing", "title case");
ok(TK.family("impact_hook").startsWith('"VM Impact"'), "role family");
TK.init({ W: 1080, H: 1920 });
ok(TK.k === 1, "k from the short side");
TK.init({ W: 1920, H: 1080 });
ok(TK.k === 1, "k for 16:9");
// connected scripts must refuse per-letter splitting
const fake = { dataset: { tkRole: "elegant_script" }, textContent: "Beautiful" };
assert.throws(() => TK.split(fake, "chars"), /connected script/);
n++;
console.log(`type-kit: ${n} checks passed`);
