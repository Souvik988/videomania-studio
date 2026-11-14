// Voxel-diorama kit: the engine. Turns a shot list (window.SHOTS, see ../README.md) into the film.
// Everything drawn is a pure function of time: renderAt(t) builds frame t from nothing, so frames can
// be rendered in any order (HyperFrames `hf-seek`). No wall clock, no unseeded random, no free loops.
import * as THREE from "three";
import { CAST, spriteCanvas } from "./cast.js";
import { SETS, MARKS, HAS_SCREEN } from "./sets.js";
import { buildFromData } from "./setdata.js";
import { createMoves } from "./moves.js";

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, u) => a + (b - a) * u;
const smooth = (u) => u * u * (3 - 2 * u);
const outCubic = (u) => 1 - Math.pow(1 - u, 3);
const outBack = (u) => 1 + 2.4 * Math.pow(u - 1, 3) + 1.4 * Math.pow(u - 1, 2);
const tri = (p) => 1 - Math.abs(2 * clamp(p) - 1);
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const TRANS = { mosaic: 0.56, dots: 0.62, pixelate: 0.5, whip: 0.3, flash: 0.36, iris: 0.7, cut: 0 };
const JIT = ["#ff5a4e", "#ffc94a", "#3cf0dd", "#ffffff", "#ff8ad8"];

export function createFilm(SHOTS) {
  const root = document.querySelector("[data-composition-id]");
  const W = +root.dataset.width, H = +root.dataset.height;
  const pal = Object.assign({ voice: "#e11d2e", voice2: "#ff6a1a", accent: "#19c8b9", ink: "#ffffff" }, SHOTS.palette || {});
  const shots = SHOTS.shots;
  const DUR = SHOTS.duration || shots[shots.length - 1].t1;

  // ------------------------------------------------------------------ renderer and post
  const canvas = document.getElementById("vd-canvas");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;   // the post pass tone-maps and encodes
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: true });
  rt.depthTexture = new THREE.DepthTexture(W, H);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#050304");
  const camera = new THREE.PerspectiveCamera(32, W / H, 0.5, 400);
  // Portrait (9:16) mode: the same shot list, natively vertical. The camera keeps PORT_KEEP of the landscape
  // width and opens up vertically, so the world fills the tall frame; type and overlays move into the space
  // above and below the action; type is sized from the width.
  const PORT = H > W, PORT_KEEP = SHOTS.portraitKeep ?? 0.62;
  const portFov = (f) => PORT ? 2 * Math.atan(Math.tan(f * Math.PI / 360) * (16 / 9) / (W / H) * PORT_KEEP) * 180 / Math.PI : f;
  const mapX = (x) => PORT ? 0.05 + x * 0.9 : x;
  const mapY = (y) => PORT ? (y < 0.5 ? 0.05 + y * 0.42 : 0.72 + (y - 0.5) * 0.42) : y;
  const TB = PORT ? W * 0.082 : H * 0.064;

  const lens = Object.assign({ aperture: 0.38, maxBlur: 9, glow: 0.42, glowRadius: 30, exposure: 1.7, grain: 0.022, vignette: 0.45, taps: 20, sat: 1.22, contrast: 1.1 }, SHOTS.lens || {});
  const post = new THREE.ShaderMaterial({
    depthTest: false, depthWrite: false,
    defines: { TAPS: lens.taps },
    uniforms: {
      tColor: { value: rt.texture }, tDepth: { value: rt.depthTexture }, uRes: { value: new THREE.Vector2(W, H) },
      uNear: { value: camera.near }, uFar: { value: camera.far }, uFocus: { value: 20 }, uAperture: { value: lens.aperture },
      uMaxR: { value: lens.maxBlur * H / 1080 }, uGlow: { value: lens.glow }, uGlowR: { value: lens.glowRadius * H / 1080 },
      uExposure: { value: lens.exposure }, uGrain: { value: lens.grain }, uVig: { value: lens.vignette }, uTime: { value: 0 },
      uBlock: { value: 1 }, uMosaic: { value: 0 }, uDots: { value: 0 }, uWhip: { value: 0 }, uFade: { value: 0 }, uFlash: { value: 0 }, uIris: { value: 0 }, uWash: { value: new THREE.Color(1, 1, 1) }, uWashK: { value: 0 }, uLook: { value: 0 }, uSat: { value: lens.sat }, uCon: { value: lens.contrast },
      uM1: { value: new THREE.Color(pal.voice) }, uM2: { value: new THREE.Color(pal.voice).multiplyScalar(0.62) },
      uM3: { value: new THREE.Color(pal.voice).multiplyScalar(0.36) },
      uD1: { value: new THREE.Color(pal.voice2) }, uD2: { value: new THREE.Color("#ffd166") },
    },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `
      uniform sampler2D tColor, tDepth; uniform vec2 uRes;
      uniform float uNear, uFar, uFocus, uAperture, uMaxR, uGlow, uGlowR, uExposure, uGrain, uVig, uTime, uBlock, uMosaic, uDots, uWhip, uFade, uFlash, uIris, uWashK, uLook, uSat, uCon; uniform vec3 uWash;
      uniform vec3 uM1, uM2, uM3, uD1, uD2; varying vec2 vUv;
      float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float dist(vec2 uv){ float d = texture2D(tDepth, uv).x; return (uNear * uFar) / (uFar - (uFar - uNear) * d); }
      float coc(float d){ float k = d > uFocus ? (d - uFocus) / max(d, 0.001) : (uFocus - d) / max(d, 0.001) * 0.9; return clamp(k * uAperture, 0.0, 1.0); }
      void main(){
        vec2 uv = vUv;
        if (uBlock > 1.5) { vec2 b = vec2(uBlock) / uRes; uv = (floor(uv / b) + 0.5) * b; }
        uv.x += uWhip * 0.16;
        float dc = dist(uv); float rpx = coc(dc) * uMaxR;
        vec3 acc = vec3(0.0), glow = vec3(0.0); float ws = 0.0;
        for (int i = 0; i < TAPS; i++) {
          float fi = float(i) + 0.5; float rr = sqrt(fi / float(TAPS)); float a = fi * 2.39996323;
          vec2 o = vec2(cos(a), sin(a)) * rr;
          vec2 suv = uv + o * rpx / uRes; suv.x += (fi / float(TAPS) - 0.5) * abs(uWhip) * 0.22;
          float ds = dist(suv);
          float w = ds >= dc - 1.0 ? 1.0 : smoothstep(0.0, 1.0, coc(ds) * 2.0) + 0.04;
          acc += texture2D(tColor, suv).rgb * w; ws += w;
          glow += max(texture2D(tColor, uv + o * uGlowR / uRes).rgb - 1.0, 0.0);
        }
        vec3 col = acc / ws + glow / float(TAPS) * uGlow;
        col = 1.0 - exp(-col * uExposure);
        col = pow(col, vec3(1.0 / 2.2));
        { float l0 = dot(col, vec3(0.299, 0.587, 0.114)); col = mix(vec3(l0), col, uSat); col = clamp((col - 0.5) * uCon + 0.5, 0.0, 1.0); }   // crisp grade: saturation, contrast
        col *= 1.0 - uVig * smoothstep(0.42, 1.0, length(vUv - 0.5) * 1.3);
        col += (hash(vUv * uRes + uTime * 61.0) - 0.5) * uGrain;
        if (uWashK > 0.001) { float l = dot(col, vec3(0.299, 0.587, 0.114)); col = mix(col, uWash * (0.25 + 1.35 * l), uWashK); }
        if (uLook > 0.5) { float l = dot(col, vec3(0.299, 0.587, 0.114));
          if (uLook < 1.5) col = vec3(1.0) - col;                                   // negative
          else if (uLook < 2.5) col = mix(uM1 * 0.9, vec3(1.0), step(0.32, l));     // red silhouette
          else col = vec3(l * 1.15); }                                              // monochrome
        if (uMosaic > 0.001) {
          float cell = uRes.y / 8.0; vec2 g = floor(vUv * uRes / cell); vec2 n = uRes / cell;
          float d = (g.x / n.x + (1.0 - g.y / n.y)) * 0.5 + hash(g) * 0.18; float q = uMosaic * 2.0;
          float on = q <= 1.0 ? step(d, q * 1.2) : step((q - 1.0) * 1.2, d - 0.02);
          float h = hash(g + 7.0); vec3 m = h < 0.34 ? uM1 : (h < 0.67 ? uM2 : uM3);
          col = mix(col, m, on);
        }
        if (uDots > 0.001) {
          float cell = uRes.y / 22.0; vec2 g = floor(vUv * uRes / cell); vec2 n = uRes / cell;
          float d = g.x / n.x + hash(g) * 0.25; float q = uDots * 2.0;
          float on = q <= 1.0 ? step(d, q * 1.3) : step((q - 1.0) * 1.3, d - 0.02);
          vec2 f = fract(vUv * uRes / cell) - 0.5; float sq = max(abs(f.x), abs(f.y));
          col = mix(col, mix(uD1 * 0.8, uD2, smoothstep(0.42, 0.34, sq)), on);
        }
        if (uIris > 0.001) { vec2 q = (vUv - 0.5) * vec2(uRes.x / uRes.y, 1.0); col = mix(uM1, col, step(length(q), (1.0 - uIris) * 1.06)); }
        col = mix(col, vec3(1.0, 0.97, 0.92), uFlash);
        gl_FragColor = vec4(col * (1.0 - uFade), 1.0);
      }`,
  });
  const postScene = new THREE.Scene();
  postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), post));
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  // ------------------------------------------------------------------ sets (voxels)
  const cube = new THREE.BoxGeometry(1, 1, 1);
  const litMat = new THREE.MeshStandardMaterial({ roughness: 0.86, metalness: 0.0, flatShading: true });
  const glowMat = new THREE.MeshBasicMaterial();
  const setGroups = {}, dataSets = {}, setInfo = {}, pending = [];
  const loadImg = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error("missing picture: " + src)); i.src = src; });
  /** Build a relief: a finely divided plane whose points are pulled towards the camera by the depth map
   *  (white = near). Points are also scaled towards the main camera, so from that view the picture looks
   *  unchanged; from anywhere else, near parts slide faster than far parts. */
  async function makeRelief(rl, group) {
    const [img, dep] = await Promise.all([loadImg(rl.src), loadImg(rl.depth)]);
    const sx = rl.seg || 320, sy = Math.max(2, Math.round(sx * rl.h / rl.w)), amount = rl.amount ?? 30, D = rl.view || 110;
    const c = document.createElement("canvas"); c.width = sx + 1; c.height = sy + 1;
    const x = c.getContext("2d", { willReadFrequently: true }); x.drawImage(dep, 0, 0, sx + 1, sy + 1);
    const dd = x.getImageData(0, 0, sx + 1, sy + 1).data;
    const geo = new THREE.PlaneGeometry(rl.w, rl.h, sx, sy), pos = geo.attributes.position;
    for (let k = 0; k < pos.count; k++) {
      const z = Math.pow(dd[k * 4] / 255, rl.gamma ?? 0.7) * amount, f = 1 - z / D;   // gamma spreads the middle distance
      pos.setXYZ(k, pos.getX(k) * f, pos.getY(k) * f, z);
    }
    pos.needsUpdate = true;
    const tex = new THREE.Texture(img); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4; tex.needsUpdate = true;
    const g = rl.glow || 1;
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(g, g, g) }));
    m.position.set(...rl.at); m.frustumCulled = false; group.add(m);
  }
  const loader = new THREE.TextureLoader();
  function buildSet(name) {
    if (setGroups[name]) return setGroups[name];
    const lit = [], glow = [], plates = [], lights = [], reliefs = []; let seed = 99;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
    const V = {
      box(x, y, z, w, h, d, c, o = {}) { (o.glow ? glow : lit).push({ p: [x + w / 2, y + h / 2, z + d / 2], s: [w, h, d], c, g: o.glow || 0, j: o.jitter || 0 }); },
      vox(x, y, z, w, h, d, c, o = {}) {
        const u = o.unit || 1;
        for (let i = 0; i < w; i += u) for (let j = 0; j < h; j += u) for (let k = 0; k < d; k += u) V.box(x + i, y + j, z + k, u, u, u, c, o);
      },
      /** A flat art plate (2.5D layer): { at:[x,y,z] centre, w, h in voxels, px:[cw,ch] canvas size, draw(ctx,cw,ch), glow, ry } */
      plate(pl) { plates.push(pl); },
      /** A relief plate: a picture pushed back along its depth map, so a moving camera gives real parallax.
       *  { src, depth, at:[x,y,z] centre, w, h, amount (voxels of depth), view (distance to the main camera), glow } */
      relief(pl) { reliefs.push(pl); },
      /** A light: { kind:"point"|"dir"|"hemi", color, ground, intensity, at:[x,y,z], dist, decay } */
      light(l) { lights.push(l); },
      rnd,
    };
    const setOpt = Object.assign({ accent: pal.accent, voice: pal.voice, voice2: pal.voice2 }, (SHOTS.sets || {})[name] || {});
    if (dataSets[name]) {   // a set described as data (sets/<name>.json): marks, cameras and a screen come with it
      const info = buildFromData(V, dataSets[name], setOpt); setInfo[name] = info; info.filePlates.forEach((pl) => plates.push(pl));
    } else (SETS[name] || SETS.studio)(V, setOpt);
    const group = new THREE.Group();
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color();
    for (const [list, mat] of [[lit, litMat], [glow, glowMat]]) {
      if (!list.length) continue;
      const mesh = new THREE.InstancedMesh(cube, mat, list.length);
      list.forEach((b, i) => {
        m4.compose(v3(b.p), q, v3(b.s)); mesh.setMatrixAt(i, m4);
        col.set(b.c); if (b.j) col.offsetHSL(0, 0, (rnd() - 0.5) * b.j * 2); if (b.g) col.multiplyScalar(b.g);
        mesh.setColorAt(i, col);
      });
      mesh.instanceMatrix.needsUpdate = true; mesh.instanceColor.needsUpdate = true; mesh.frustumCulled = false;
      group.add(mesh);
    }
    for (const pl of plates) {   // 2.5D layers: flat art at a depth; the moving camera gives the parallax
      let tex;
      if (pl.src) tex = loader.load(pl.src);
      else { const cnv = document.createElement("canvas"); cnv.width = pl.px ? pl.px[0] : 1024; cnv.height = pl.px ? pl.px[1] : 512;
        pl.draw(cnv.getContext("2d"), cnv.width, cnv.height, rnd); tex = new THREE.CanvasTexture(cnv); }
      tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
      const g = pl.glow || 1;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(pl.w, pl.h), new THREE.MeshBasicMaterial({ map: tex, alphaTest: pl.solid ? 0 : 0.5, color: new THREE.Color(g, g, g) }));
      m.position.set(...pl.at); if (pl.ry) m.rotation.y = pl.ry; m.frustumCulled = false; group.add(m);
    }
    for (const rl of reliefs) pending.push(makeRelief(rl, group));
    for (const l of lights) {
      let L;
      if (l.kind === "hemi") L = new THREE.HemisphereLight(l.color, l.ground || "#080606", l.intensity);
      else if (l.kind === "dir") L = new THREE.DirectionalLight(l.color, l.intensity);
      else L = new THREE.PointLight(l.color, l.intensity, l.dist || 90, l.decay || 1.7);
      if (l.at) L.position.set(...l.at);
      group.add(L);
    }
    group.visible = false; scene.add(group); setGroups[name] = group;
    return group;
  }
  // Sets are built once their data is in: built-in sets are code, every other name is sets/<name>.json
  // (or SHOTS.setData[name] inline). Extra plates from files: SHOTS.plates = [{ set, src, at, w, h, glow }].
  const setNames = [...new Set(shots.map((s) => s.set || "studio"))];
  let built = false;
  const dataReady = Promise.all(setNames.filter((n) => !SETS[n]).map((n) =>
    (SHOTS.setData && SHOTS.setData[n] ? Promise.resolve(SHOTS.setData[n]) : fetch(`sets/${n}.json`).then((r) => { if (!r.ok) throw new Error(`set '${n}' not found: sets/${n}.json`); return r.json(); }))
      .then((d) => { dataSets[n] = d; }))).then(() => {
    setNames.forEach(buildSet);
    (SHOTS.plates || []).forEach((pl) => {
      const g = buildSet(pl.set || "studio"), k = pl.glow || 1;
      if (pl.depth) { pending.push(makeRelief(pl, g)); return; }
      const tex = loader.load(pl.src); tex.colorSpace = THREE.SRGBColorSpace;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(pl.w, pl.h), new THREE.MeshBasicMaterial({ map: tex, alphaTest: 0.5, color: new THREE.Color(k, k, k) }));
      m.position.set(...pl.at); m.frustumCulled = false; g.add(m);
    });
    return Promise.all(pending.concat(scrLoads()));
  }).then(() => { built = true; });

  // ------------------------------------------------------------------ monitor screen
  const scrCanvas = document.createElement("canvas"); scrCanvas.width = 680; scrCanvas.height = 400;
  const scrTex = new THREE.CanvasTexture(scrCanvas); scrTex.colorSpace = THREE.SRGBColorSpace;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(17, 10), new THREE.MeshBasicMaterial({ map: scrTex, color: new THREE.Color(1.5, 1.5, 1.5) }));
  screen.position.set(...MARKS.screen); scene.add(screen);
  let scrKey = "";
  // screen: { kind: "image", src, crop: [sx, sy, sw, sh], zoom: 0.08, at: [fx, fy] } - a generated picture on the monitor (ChatGPT bridge)
  var SCR_IMG = {};
  function assetSrcs() {   // every real picture the shot list names (asset-first: these come from the image bridge or real footage)
    const out = new Set();
    for (const s of shots) {
      const sc = s.screen || {};
      if (sc.src) out.add(sc.src);
      if (sc.kind === "frames") for (let i = 0; i < (sc.count || 1); i++) out.add(frameSrc(sc, i));
      (s.cards || []).forEach((c) => c.img && out.add(c.img));
      ((s.fan && s.fan.imgs) || []).forEach((u) => out.add(u));
      ((s.strip && s.strip.imgs) || []).forEach((u) => out.add(u));
    }
    return [...out];
  }
  function frameSrc(sc, i) { return sc.src.replace(/%0(\d)d/, (_, n) => String(i + (sc.first ?? 1)).padStart(+n, "0")); }
  function scrLoads() {
    return assetSrcs().map((u) => new Promise((res) => {
      if (SCR_IMG[u]) return res(); const im = new Image(); SCR_IMG[u] = im;
      im.onload = im.onerror = () => res(); im.src = u; }));
  }
  function drawScreen(spec, u) {
    const fi = spec && spec.kind === "frames" ? Math.min((spec.count || 1) - 1, Math.floor(clamp(u) * (spec.count || 1) * (spec.loops || 1)) % (spec.count || 1)) : 0;
    const step = Math.floor(clamp(u) * 24), key = JSON.stringify(spec || 0) + step + "|" + fi;
    if (key === scrKey) return; scrKey = key;
    const x = scrCanvas.getContext("2d"), w = 680, h = 400, f = "Inter, system-ui, sans-serif";
    x.fillStyle = "#0e1013"; x.fillRect(0, 0, w, h);
    x.fillStyle = "#1a1d22"; x.fillRect(0, 0, w, 30);
    ["#ff5f57", "#febc2e", "#28c840"].forEach((c, i) => { x.fillStyle = c; x.beginPath(); x.arc(18 + i * 18, 15, 5, 0, 7); x.fill(); });
    const kind = (spec && spec.kind) || "idle", lines = (spec && spec.lines) || [];
    if (kind === "chat") {
      x.fillStyle = "#e9e6dc"; x.font = `600 26px ${f}`; x.textAlign = "center"; x.fillText(spec.title || "What are we making?", w / 2, 150);
      x.fillStyle = "#1c2026"; x.strokeStyle = "#343a44"; x.lineWidth = 2; x.beginPath(); x.roundRect(110, 185, 460, 64, 14); x.fill(); x.stroke();
      const txt = lines[0] || "", n = Math.floor(txt.length * clamp(u * 1.6));
      x.fillStyle = "#cfd3da"; x.font = `500 20px ${f}`; x.textAlign = "left"; x.fillText(txt.slice(0, n) + (step % 2 ? "▍" : ""), 130, 224);
      x.fillStyle = pal.voice; x.beginPath(); x.roundRect(520, 197, 38, 38, 9); x.fill();
    } else if (kind === "code") {
      const cols = [pal.accent, "#e9e6dc", pal.voice2, "#8b93a1", pal.voice];
      const total = Math.max(lines.length, 9), shown = Math.ceil(total * clamp(u * 1.3));
      for (let i = 0; i < shown; i++) {
        const y = 62 + i * 34; x.fillStyle = "#4a515c"; x.font = `500 15px ${f}`; x.textAlign = "right"; x.fillText(String(i + 1), 44, y + 6);
        if (lines[i]) { x.fillStyle = cols[i % cols.length]; x.font = `500 19px 'Pixelify Sans', monospace`; x.textAlign = "left"; x.fillText(lines[i], 64 + (i % 3) * 18, y + 7); }
        else { x.fillStyle = cols[i % cols.length]; x.globalAlpha = 0.75; x.fillRect(64 + (i % 3) * 18, y - 6, 120 + ((i * 53) % 260), 12); x.globalAlpha = 1; }
      }
    } else if (kind === "frames") {   // footage: frame fi of the sequence, under the window bar
      const im = SCR_IMG[frameSrc(spec, fi)];
      if (im && im.naturalWidth) { x.imageSmoothingEnabled = true; x.drawImage(im, 0, 30, w, h - 30); }
      if (spec.title) { x.fillStyle = "rgba(0,0,0,0.55)"; x.fillRect(0, 30, w, 34); x.fillStyle = "#ffffff"; x.font = `600 17px ${f}`; x.textAlign = "left"; x.fillText("\u25CF " + spec.title, 14, 53); }
      if (spec.bar !== false) { x.fillStyle = "rgba(255,255,255,0.3)"; x.fillRect(16, h - 18, w - 32, 5); x.fillStyle = pal.voice; x.fillRect(16, h - 18, (w - 32) * clamp(u), 5); }
    } else if (kind === "image" && SCR_IMG[spec.src] && SCR_IMG[spec.src].naturalWidth) {
      const im = SCR_IMG[spec.src], c = spec.crop || [0, 0, im.naturalWidth, im.naturalHeight];
      const z = 1 + (spec.zoom ?? 0.08) * clamp(u), [fx, fy] = spec.at || [0.5, 0.5];
      const sw = c[2] / z, sh = c[3] / z, sx = c[0] + (c[2] - sw) * fx, sy = c[1] + (c[3] - sh) * fy;
      x.imageSmoothingEnabled = !spec.pixel; x.drawImage(im, sx, sy, sw, sh, 0, 30, w, h - 30);
    } else if (kind === "player") {   // the film quoting itself: a small player with a title and a moving progress bar
      x.fillStyle = "#16181d"; x.fillRect(40, 54, w - 80, h - 110);
      const g = x.createLinearGradient(40, 54, w - 40, h - 56); g.addColorStop(0, pal.voice2); g.addColorStop(1, pal.voice);
      x.fillStyle = g; x.globalAlpha = 0.85; x.fillRect(48, 62, w - 96, h - 136); x.globalAlpha = 1;
      x.fillStyle = "#ffffff"; x.font = `800 44px ${f}`; x.textAlign = "center"; x.fillText(spec.title || "this_video.mp4", w / 2, h / 2 - 6);
      x.font = `500 18px ${f}`; x.globalAlpha = 0.8; x.fillText(spec.sub || "", w / 2, h / 2 + 30); x.globalAlpha = 1;
      x.fillStyle = "rgba(255,255,255,0.25)"; x.fillRect(48, h - 64, w - 96, 6); x.fillStyle = pal.voice; x.fillRect(48, h - 64, (w - 96) * clamp(0.18 + u * 0.6), 6);
      x.beginPath(); x.arc(48 + (w - 96) * clamp(0.18 + u * 0.6), h - 61, 9, 0, 7); x.fill();
      x.textAlign = "left"; x.fillStyle = "#e9e6dc"; x.font = `600 16px ${f}`; x.fillText("● " + (spec.file || "tutorial.mp4"), 52, 40);
    } else if (kind === "timeline") {
      const cols = [pal.voice, pal.accent, pal.voice2, "#e9e6dc"];
      for (let tr = 0; tr < 4; tr++) {
        x.fillStyle = "#171a1f"; x.fillRect(20, 60 + tr * 70, w - 40, 56);
        let px = 30, k = 0;
        while (px < w - 60) { const cw = 50 + ((tr * 97 + k * 61) % 120); x.fillStyle = cols[(tr + k) % cols.length]; x.globalAlpha = 0.9; x.beginPath(); x.roundRect(px, 68 + tr * 70, Math.min(cw, w - 40 - px), 40, 6); x.fill(); x.globalAlpha = 1; px += cw + 8; k++; }
      }
      x.fillStyle = "#ffffff"; x.fillRect(30 + (w - 70) * clamp(u), 44, 3, 330);
    } else {
      x.fillStyle = pal.accent; x.globalAlpha = 0.5; x.fillRect(w / 2 - 60, h / 2 - 3, 120, 6); x.globalAlpha = 1;
    }
    scrTex.needsUpdate = true;
  }

  // ------------------------------------------------------------------ cast (pixel sprites)
  const texCache = new Map(), depthCache = new Map();
  const depthTexOf = (cnv) => {
    if (!depthCache.has(cnv)) { const t = new THREE.CanvasTexture(cnv); t.magFilter = t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; depthCache.set(cnv, t); }
    return depthCache.get(cnv);
  };
  const texOf = (cnv) => {
    if (!texCache.has(cnv)) { const t = new THREE.CanvasTexture(cnv); t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.colorSpace = THREE.SRGBColorSpace; texCache.set(cnv, t); }
    return texCache.get(cnv);
  };
  const shadowTex = (() => {
    const c = document.createElement("canvas"); c.width = c.height = 64; const x = c.getContext("2d");
    const g = x.createRadialGradient(32, 32, 2, 32, 32, 30); g.addColorStop(0, "rgba(0,0,0,0.6)"); g.addColorStop(1, "rgba(0,0,0,0)");
    x.fillStyle = g; x.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c);
  })();
  const actors = {};
  // Sprites are lit by the room: darker on the side away from the key light, a touch of the key colour on the
  // lit side, and a rim of light along the silhouette on the rim side. Each set can give its own `castLight`.
  const LIGHTS = {
    studio: { key: "#ffb057", keySide: -1, rim: pal.accent, rimSide: 1, shade: 0.34 },
    "city-night": { key: "#ffd9a0", keySide: 1, rim: pal.voice, rimSide: -1, shade: 0.4 },
    void: { key: "#bff5ee", keySide: 0, rim: pal.accent, rimSide: 1, shade: 0.15 },
    default: { key: "#ffc08f", keySide: -1, rim: "#9fd8ff", rimSide: 1, shade: 0.3 },
  };
  const spriteMat = () => new THREE.ShaderMaterial({
    side: THREE.DoubleSide,
    uniforms: { map: { value: null }, uTexel: { value: new THREE.Vector2(1 / 60, 1 / 68) }, uTint: { value: new THREE.Color(1.1, 1.06, 1.02) },
      uKey: { value: new THREE.Color("#ffb057") }, uKeySide: { value: -1 }, uRim: { value: new THREE.Color("#19c8b9") }, uRimSide: { value: 1 },
      uShade: { value: 0.3 }, uFlip: { value: 1 }, uFlash: { value: 0 },
      uDepth: { value: null }, uHasDepth: { value: 0 }, uLift: { value: 1.0 }, uBump: { value: 6.0 }, uDTexel: { value: new THREE.Vector2(1 / 60, 1 / 68) } },
    // 2.5D picture mascots: a depth map pushes the sprite mesh toward the camera (real parallax) and its normals light it
    vertexShader: `uniform sampler2D uDepth; uniform float uHasDepth, uLift; varying vec2 vUv;
      void main(){ vUv = uv; vec3 p = position;
        if (uHasDepth > 0.5) p.z += texture2D(uDepth, uv).r * uLift;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0); }`,
    fragmentShader: `
      uniform sampler2D map, uDepth; uniform vec2 uTexel, uDTexel; uniform vec3 uTint, uKey, uRim; uniform float uKeySide, uRimSide, uShade, uFlip, uFlash, uHasDepth, uBump; varying vec2 vUv;
      void main(){
        vec4 c = texture2D(map, vUv); if (c.a < 0.5) discard;
        float side = (vUv.x - 0.5) * 2.0 * uFlip;
        float away = smoothstep(-0.15, 1.0, -side * uKeySide);
        vec3 col = c.rgb * uTint * (1.0 - uShade * away) + c.rgb * uKey * 0.2 * smoothstep(0.0, 1.0, side * uKeySide);
        if (uHasDepth > 0.5) {   // light the relief: lit side, shadow side, darker recesses, a soft sheen
          float d = texture2D(uDepth, vUv).r;
          float dx = texture2D(uDepth, vUv + vec2(uDTexel.x * 2.0, 0.0)).r - texture2D(uDepth, vUv - vec2(uDTexel.x * 2.0, 0.0)).r;
          float dy = texture2D(uDepth, vUv + vec2(0.0, uDTexel.y * 2.0)).r - texture2D(uDepth, vUv - vec2(0.0, uDTexel.y * 2.0)).r;
          vec3 N = normalize(vec3(-dx * uBump * uFlip, -dy * uBump, 1.0));
          vec3 L = normalize(vec3(uKeySide * 0.8, 0.55, 0.6));
          float diff = max(dot(N, L), 0.0), back = max(dot(N, vec3(-L.x, 0.2, 0.3)), 0.0);
          float ao = mix(0.62, 1.0, smoothstep(0.05, 0.55, d));
          float sheen = pow(max(dot(reflect(-L, N), vec3(0.0, 0.0, 1.0)), 0.0), 18.0);
          col = c.rgb * uTint * ao * (0.52 + 0.78 * diff) + c.rgb * uKey * 0.32 * diff + uKey * sheen * 0.12 - c.rgb * 0.18 * back * (1.0 - diff);
        }
        float n1 = texture2D(map, vUv + vec2(uRimSide * uFlip * uTexel.x * 1.2, uTexel.y * 0.6)).a;
        float n2 = texture2D(map, vUv + vec2(uRimSide * uFlip * uTexel.x * 2.4, uTexel.y * 1.2)).a;
        col += uRim * (step(n1, 0.5) * 0.85 + step(n2, 0.5) * 0.3);
        gl_FragColor = vec4(mix(col, vec3(1.6), uFlash), 1.0);
      }`,
  });
  function addActor(who, d) {
    const mat = spriteMat(); mat.uniforms.uTexel.value.set(1 / d.w, 1 / d.h);
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(d.w * d.px, d.h * d.px), mat);
    const sh = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.5), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
    sh.rotation.x = -Math.PI / 2;
    mesh.visible = sh.visible = false; scene.add(mesh, sh);
    return (actors[who] = { mesh, sh, def: d, seed: who.length * 1.37 });
  }
  for (const who of Object.keys(CAST)) addActor(who, CAST[who]);
  // Cast members from pictures: SHOTS.cast = { fox: { src: "assets/cast/fox.png", tall: 9, head: 0.7 } }
  // (make the picture with scripts/sprite_import.py). One picture serves every pose; actions still move it.
  // Picture mascots with many poses: SHOTS.cast = { me: { poses: "assets/mascot/poses.json", tall: 10 } }
  // (make them with scripts/pose_sheet.py from a ChatGPT pose sheet). Every pose shares one pixel scale; a
  // pose the shot asks for that the mascot lacks falls back (POSE_FALLBACK), then to idle/talk.
  const POSE_FALLBACK = { happy: ["cheer", "thumbs", "wave"], sit: ["sit_code", "floor_code"], code: ["sit_code", "holo_type", "floor_code"],
    run: ["run", "walk"], fly: ["fly", "jump"], present: ["point", "talk"], idle: ["idle", "talk"], talk: ["talk", "idle"] };
  const imgCanvas = (img) => { const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight; c.getContext("2d").drawImage(img, 0, 0); return c; };
  for (const [who, c] of Object.entries(SHOTS.cast || {})) {
    const d = { w: 32, h: 32, px: 0.3, head: c.head ?? 0.7, image: null, poses: [] }, a = addActor(who, d);
    if (c.poses) {
      const base = c.poses.replace(/[^/]*$/, "");
      pending.push(fetch(c.poses).then((r) => r.json()).then((meta) => Promise.all(Object.entries(meta.poses).map(([name, v]) =>
        Promise.all([loadImg(base + v.src), v.depth ? loadImg(base + v.depth) : null]).then(([img, dep]) => [name, imgCanvas(img), dep ? imgCanvas(dep) : null])))).then((list) => {
        d.images = Object.fromEntries(list.map((q) => [q[0], q[1]])); d.poses = Object.keys(d.images);
        d.depths = Object.fromEntries(list.filter((q) => q[2]).map((q) => [q[0], q[2]])); d.lift = c.lift ?? 0.9;
        const ref = d.images[c.ref || "idle"] || d.images.talk || list[0][1];
        d.w = ref.width; d.h = ref.height; d.px = (c.tall || 10) / d.h; d.image = null; d.unit = true;
        a.mesh.geometry = new THREE.PlaneGeometry(1, 1, 48, 72);
      }));
      continue;
    }
    pending.push(loadImg(c.src).then((img) => {
      const cnv = document.createElement("canvas"); cnv.width = img.naturalWidth; cnv.height = img.naturalHeight; cnv.getContext("2d").drawImage(img, 0, 0);
      d.w = cnv.width; d.h = cnv.height; d.px = (c.tall || 9) / d.h; d.image = cnv;
      a.mesh.geometry = new THREE.PlaneGeometry(d.w * d.px, d.h * d.px); a.mesh.material.uniforms.uTexel.value.set(1 / d.w, 1 / d.h);
    }));
  }
  function poseCanvas(d, pose) {
    if (!d.images) return null;
    if (d.images[pose]) return d.images[pose];
    for (const alt of POSE_FALLBACK[pose] || []) if (d.images[alt]) return d.images[alt];
    return d.images.idle || d.images.talk || Object.values(d.images)[0];
  }
  const ghost = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ size: 0.2, vertexColors: true, transparent: true, depthWrite: false }));
  ghost.frustumCulled = false; ghost.visible = false; scene.add(ghost);
  const ghostCache = new Map();
  function spriteDots(who, pose, d) {   // the sprite's pixels as points (cached)
    const key = who + "|" + pose; if (ghostCache.has(key)) return ghostCache.get(key);
    const cnv = poseCanvas(d, pose) || d.image || spriteCanvas(who, pose, {}); const x = cnv.getContext("2d").getImageData(0, 0, cnv.width, cnv.height).data;
    const P = [], C = [];
    for (let j = 0; j < cnv.height; j++) for (let i = 0; i < cnv.width; i++) { const o = (j * cnv.width + i) * 4; if (x[o + 3] < 128) continue;
      P.push((i - cnv.width / 2) * d.px, (cnv.height - j) * d.px, 0); C.push(x[o] / 255 * 1.2, x[o + 1] / 255 * 1.2, x[o + 2] / 255 * 1.2); }
    const r = { P: new Float32Array(P), C: new Float32Array(C) }; ghostCache.set(key, r); return r;
  }
  const trail = Array.from({ length: 12 }, () => { const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, color: new THREE.Color(pal.accent).multiplyScalar(1.8) })); m.visible = false; scene.add(m); return m; });

  const mark = (m, set) => (Array.isArray(m) ? m : (setInfo[set] && setInfo[set].marks[m]) || MARKS[m] || MARKS.stage);
  const P3 = (m, set) => { const a = mark(m, set); return [a[0], a[1] || 0, a[2]]; };
  const cr = (p0, p1, p2, p3, u) => 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u);
  /** A cast member's state at time t, from their action track.
   *    acts: [{ do, t: [start, end], ... }] in order; the position carries from one action to the next.
   *    walk / run  { to }                 step cycle along the ground
   *    jump        { to?, height }        an arc; lands with a squash
   *    fly         { to | path: [...], }  a smooth curve through the points, head first, with a light trail
   *    land        {}                     squash and settle where they are
   *    sit, wave, pose { pose }           hold a pose
   *  `to` / `walk` on the cast entry is the short form of one walk action. */
  function castState(s, c, t) {
    const set = s.set || "studio";
    let m = P3(c.at, set);
    const acts = c.acts || (c.to ? [{ do: "walk", to: c.to, t: c.walk || [s.t0, s.t1] }] : []);
    const st = { m, pose: c.pose || "idle", rotZ: 0, sx: 1, sy: 1, moving: false, dir: 0, cadence: 2.2, trail: false, ground: m[1] };
    for (const a of acts) {
      const [t0, t1] = a.t || [s.t0, s.t1];
      if (t < t0) break;
      const k = clamp((t - t0) / Math.max(0.01, t1 - t0)), live = t < t1;
      const to = a.to ? P3(a.to, set) : m;
      if (a.do === "walk" || a.do === "run") {
        const run = a.do === "run";
        st.dir = to[0] - m[0];
        const here = [lerp(m[0], to[0], k), lerp(m[1], to[1], k), lerp(m[2], to[2], k)];
        if (live) { st.moving = true; st.pose = "walk"; st.cadence = run ? 10 : 6; st.rotZ = run ? -0.16 * Math.sign(st.dir || 1) : 0;
          here[1] += Math.abs(Math.sin(t * st.cadence * Math.PI / 2)) * (run ? 0.8 : 0.45); }
        m = live ? here : to; st.ground = lerp(st.ground, to[1], k);
      } else if (a.do === "jump") {
        const h = a.height ?? 6, e = k;
        st.dir = to[0] - m[0];
        const here = [lerp(m[0], to[0], e), lerp(m[1], to[1], e) + Math.sin(e * Math.PI) * h, lerp(m[2], to[2], e)];
        if (live) { st.pose = "jump"; const v = Math.cos(e * Math.PI); st.sy = 1 + 0.16 * Math.abs(v); st.sx = 1 - 0.1 * Math.abs(v);
          if (e < 0.12) { const q = e / 0.12; st.sy = 0.8 + 0.36 * q; st.sx = 1.14 - 0.24 * q; } }
        else { const q = clamp((t - t1) / 0.18); st.sy = 1 - 0.22 * Math.sin(q * Math.PI); st.sx = 1 + 0.16 * Math.sin(q * Math.PI); }
        m = live ? here : to; st.ground = to[1];
      } else if (a.do === "fly") {
        const pts = [m, ...(a.path ? a.path.map((q) => P3(q, set)) : [to])], n = pts.length - 1;
        const e = smooth(k), f = Math.min(n - 1e-6, e * n), i = Math.floor(f), u = f - i;
        const g = (j) => pts[clamp(j, 0, n)];
        const at = (uu, ii) => [0, 1, 2].map((ax) => cr(g(ii - 1)[ax], g(ii)[ax], g(ii + 1)[ax], g(ii + 2)[ax], uu));
        const here = at(u, i), ahead = at(Math.min(1, u + 0.04), i);
        const vx = ahead[0] - here[0], vy = ahead[1] - here[1];
        st.dir = Math.abs(vx) > 1e-4 ? vx : pts[n][0] - pts[0][0];   // face the way they are moving right now
        if (live) { st.pose = "fly"; st.trail = true; const sgn = Math.sign(st.dir || 1);
          st.rotZ = -sgn * (1.1 - clamp(Math.atan2(vy, Math.abs(vx) + 1e-3), -0.9, 0.9) * 0.8) * smooth(clamp(k / 0.12)) * smooth(clamp((1 - k) / 0.12));
          here[1] += Math.sin(t * 5) * 0.25; st.sy = 1.06; }
        else { const q = clamp((t - t1) / 0.2); st.sy = 1 - 0.24 * Math.sin(q * Math.PI); st.sx = 1 + 0.18 * Math.sin(q * Math.PI); }
        m = live ? here : pts[n]; if (!live) st.ground = pts[n][1];
      } else if (a.do === "land") { if (live) { st.sy = 1 - 0.26 * Math.sin(k * Math.PI); st.sx = 1 + 0.2 * Math.sin(k * Math.PI); st.pose = a.pose || "idle"; }
      } else if (live || a.hold) { st.pose = a.pose || a.do; if (a.do === "sit") m = [m[0], m[1] - (a.drop ?? 0), m[2]]; }
      if (!live && a.then) st.pose = a.then;
    }
    st.m = m;
    return st;
  }
  const castPos = castState;

  // ------------------------------------------------------------------ cards and props
  const things = new Map();
  function cardMesh(c) {
    const cnv = document.createElement("canvas"); cnv.width = 256; cnv.height = 300; const x = cnv.getContext("2d");
    const pic = c.img && SCR_IMG[c.img] && SCR_IMG[c.img].naturalWidth ? SCR_IMG[c.img] : null;
    if (pic) {   // a real icon from the image bridge: the picture is the card
      const sz = 220, r = Math.min(sz / pic.naturalWidth, sz / pic.naturalHeight);
      x.drawImage(pic, 128 - pic.naturalWidth * r / 2, 6 + (sz - pic.naturalHeight * r) / 2, pic.naturalWidth * r, pic.naturalHeight * r);
      x.fillStyle = "#ffffff"; x.font = "800 34px Inter, system-ui, sans-serif"; x.textAlign = "center"; x.lineWidth = 7; x.strokeStyle = "rgba(0,0,0,0.6)";
      x.strokeText(c.label || "", 128, 272); x.fillText(c.label || "", 128, 272);
      const tp = new THREE.CanvasTexture(cnv); tp.colorSpace = THREE.SRGBColorSpace; tp.anisotropy = 4;
      const mp = new THREE.Mesh(new THREE.PlaneGeometry(4.6 * (c.scale || 1), 5.4 * (c.scale || 1)), new THREE.MeshBasicMaterial({ map: tp, alphaTest: 0.2, side: THREE.DoubleSide, color: new THREE.Color(1.12, 1.12, 1.12) }));
      scene.add(mp); return mp;
    }
    x.fillStyle = "#14161b"; x.strokeStyle = "#2c313a"; x.lineWidth = 4; x.beginPath(); x.roundRect(28, 8, 200, 200, 40); x.fill(); x.stroke();
    x.strokeStyle = x.fillStyle = c.color || pal.accent; x.lineWidth = 10; x.lineCap = "round"; x.lineJoin = "round";
    const I = c.icon || "doc";
    if (I === "doc") { x.strokeRect(88, 58, 80, 100); [84, 106, 128].forEach((y) => { x.beginPath(); x.moveTo(104, y); x.lineTo(152, y); x.stroke(); }); }
    else if (I === "board") { [[72, 62], [136, 62], [72, 118]].forEach(([a, b]) => x.strokeRect(a, b, 48, 40)); x.fillRect(136, 118, 48, 40); }
    else if (I === "play") { x.beginPath(); x.moveTo(100, 62); x.lineTo(168, 108); x.lineTo(100, 154); x.closePath(); x.fill(); }
    else if (I === "cc") { x.beginPath(); x.roundRect(64, 76, 128, 64, 14); x.stroke(); x.beginPath(); x.moveTo(88, 108); x.lineTo(168, 108); x.stroke(); }
    else if (I === "mic") { x.beginPath(); x.roundRect(110, 52, 36, 66, 18); x.fill(); x.beginPath(); x.arc(128, 104, 36, 0.15, Math.PI - 0.15); x.stroke(); x.beginPath(); x.moveTo(128, 140); x.lineTo(128, 162); x.stroke(); }
    else { x.beginPath(); x.arc(128, 96, 34, 0, 7); x.fill(); x.fillRect(114, 132, 28, 22); }
    x.fillStyle = "#ffffff"; x.font = "700 34px Inter, system-ui, sans-serif"; x.textAlign = "center"; x.fillText(c.label || "", 128, 268);
    const t = new THREE.CanvasTexture(cnv); t.colorSpace = THREE.SRGBColorSpace;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 5.4), new THREE.MeshBasicMaterial({ map: t, alphaTest: 0.2, side: THREE.DoubleSide, color: new THREE.Color(1.25, 1.25, 1.25) }));
    scene.add(m); return m;
  }
  function docMesh(p) {
    const g = new THREE.Group(), std = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.9, flatShading: true });
    const add = (x, y, z, w, h, d, c) => { const m = new THREE.Mesh(cube, std(c)); m.scale.set(w, h, d); m.position.set(x, y, z); g.add(m); };
    add(0, 0, 0, 6, 8, 0.7, "#e8dcc0"); add(0, 1.6, 0.4, 6, 1.6, 0.2, p.color || pal.voice);
    [-0.2, -1.2, -2.2, -3.0].forEach((y, i) => add(i === 3 ? -1 : 0, y, 0.4, i === 3 ? 2.6 : 4.4, 0.35, 0.15, "#2a2420"));
    scene.add(g); return g;
  }
  const thing = (key, make) => { if (!things.has(key)) things.set(key, make()); return things.get(key); };

  // ------------------------------------------------------------------ type layer (DOM, above the canvas)
  const typeLayer = document.getElementById("vd-type");
  const typeNodes = shots.map((s, si) => {
    if (!s.lines) return null;
    const ty = Object.assign({ x: 0.08, y: 0.16, w: 0.4, align: "left", size: 1 }, s.type || {});
    const box = document.createElement("div"); box.className = "vd-block" + (ty.compose ? " vd-compose" : "");
    const bx = PORT ? 0.06 : ty.x, bw = PORT ? 0.88 : ty.w, by = mapY(ty.y);
    box.style.cssText = `left:${bx * W}px;top:${by * H}px;width:${bw * W}px;text-align:${PORT ? "left" : ty.align};font-size:${TB * ty.size}px;`;
    if (ty.ink) box.style.color = ty.ink;                 // per-shot type colours, for bright worlds
    if (ty.punch) box.style.setProperty("--voice", ty.punch);
    if (ty.ink && ty.ink !== "#ffffff") box.style.textShadow = "none";
    const groups = s.lines.map((line) => {
      const el = document.createElement("div"); el.className = "vd-line"; box.appendChild(el);
      const words = line.map(([text, t, role, fx, place]) => {
        if (text === "\n") { el.appendChild(document.createElement("br")); return null; }
        const w = document.createElement("span"); w.className = "vd-w vd-" + (role || "say") + (fx ? " vd-fx-" + fx : ""); el.appendChild(w);
        let chars = null;   // word effects: "mark" (marker box), "bracket" (corner brackets), "jitter" (coloured letters drop in), "type" (typed)
        if (fx === "jitter" || fx === "type") chars = [...text].map((ch) => { const c = document.createElement("span"); c.className = "vd-ch"; c.textContent = ch; w.appendChild(c); return c; });
        else w.textContent = text;
        const num = role === "num" && /^(\d+(?:\.\d+)?)(.*)$/.exec(text);
        if (ty.compose && place) {   // a word with its own place, angle and curve in the composition
          w.style.position = "absolute"; w.style.left = mapX(place.x ?? 0) * W + "px"; w.style.top = mapY(place.y ?? 0) * H + "px";
          w.style.fontSize = (place.size || 1) + "em"; w.dataset.rot = place.rot || 0; w.dataset.tilt = place.tilt || 0; w.dataset.skew = place.skew || 0;
          if (place.arc && !chars) { const cs = [...text]; w.textContent = ""; chars = cs.map((ch, i) => { const c = document.createElement("span"); c.className = "vd-ch"; c.textContent = ch;
            c.style.transform = `translateY(${Math.pow((i - (cs.length - 1) / 2) / Math.max(1, cs.length / 2), 2) * -place.arc}em) rotate(${(i - (cs.length - 1) / 2) * place.arc * 9}deg)`; c.dataset.arc = "1"; w.appendChild(c); return c; }); }
        }
        if (ty.flicker !== false && !chars && role !== "num" && role !== "soft") {   // letters flicker in colours, then settle
          const cs = [...text]; w.textContent = ""; chars = cs.map((ch) => { const c = document.createElement("span"); c.className = "vd-ch"; c.textContent = ch; w.appendChild(c); return c; }); w.dataset.flick = "1";
        }
        return { el: w, t, role: role || "say", fx, chars, place, num: num ? { v: +num[1], suf: num[2], dec: (num[1].split(".")[1] || "").length } : null };
      }).filter(Boolean);
      return { el, words, t: Math.min(...words.map((w) => w.t)) };
    });
    if (ty.depth) box.classList.add("vd-depth");
    typeLayer.appendChild(box);
    return { box, groups, depth: !!ty.depth };
  });
  const moves = createMoves({ THREE, scene, camera, W, H, pal, shots, layer: typeLayer, imgs: SCR_IMG, mapX, mapY, U: PORT ? W * 0.5625 : H });
  // doodles: [{ kind: "circle" | "underline" | "x" | "arrow" | "check" | "star" | "scribble", t, dur, x, y, w, h,
  //            to: [x, y] (arrow), on: "card:<id>" | "me" | [x, y, z] (follow a thing in the world), color, width, hold }]
  const SVGNS = "http://www.w3.org/2000/svg";
  const doodleRnd = (seed) => { let a = seed * 9301 + 49297; return () => { a = (a * 9301 + 49297) % 233280; return a / 233280; }; };
  function doodlePaths(d, seed) {
    const r = doodleRnd(seed), j = (v) => (r() - 0.5) * v, P = [];
    const x = d.x * W, y = d.y * H, w = (d.w ?? 0.2) * W, h = (d.h ?? 0.1) * H;
    const line = (pts) => "M" + pts.map((q) => q[0].toFixed(1) + " " + q[1].toFixed(1)).join(" L");
    const k = d.kind || "circle";
    if (k === "circle") { const pts = []; const a0 = -1.9 + j(0.4);
      for (let i = 0; i <= 64; i++) { const a = a0 + (i / 64) * Math.PI * 2.18, rr = 1 + j(0.035) + i * 0.0012;
        pts.push([x + Math.cos(a) * w / 2 * rr, y + Math.sin(a) * h / 2 * rr]); } P.push(line(pts)); }
    else if (k === "underline") { for (let s2 = 0; s2 < 2; s2++) { const pts = [];
      for (let i = 0; i <= 16; i++) pts.push([x - w / 2 + (i / 16) * w + j(2), y + Math.sin(i / 16 * Math.PI) * h * 0.08 * (s2 ? -1 : 1) + s2 * h * 0.12 + j(2)]); P.push(line(pts)); } }
    else if (k === "x") { P.push(line([[x - w / 2 + j(8), y - h / 2 + j(8)], [x, y + j(6)], [x + w / 2 + j(8), y + h / 2 + j(8)]]));
      P.push(line([[x + w / 2 + j(8), y - h / 2 + j(8)], [x + j(6), y], [x - w / 2 + j(8), y + h / 2 + j(8)]])); }
    else if (k === "check") P.push(line([[x - w / 2, y], [x - w / 8, y + h / 2], [x + w / 2, y - h / 2]]));
    else if (k === "arrow") { const tx = d.to[0] * W, ty = d.to[1] * H, mx = (x + tx) / 2 + (ty - y) * 0.25, my = (y + ty) / 2 - (tx - x) * 0.25, pts = [];
      for (let i = 0; i <= 24; i++) { const u = i / 24; pts.push([(1 - u) * (1 - u) * x + 2 * u * (1 - u) * mx + u * u * tx + j(1.5), (1 - u) * (1 - u) * y + 2 * u * (1 - u) * my + u * u * ty + j(1.5)]); }
      P.push(line(pts)); const ang = Math.atan2(ty - pts[20][1], tx - pts[20][0]), L = H * 0.035;
      P.push(line([[tx - Math.cos(ang - 0.5) * L, ty - Math.sin(ang - 0.5) * L], [tx, ty], [tx - Math.cos(ang + 0.5) * L, ty - Math.sin(ang + 0.5) * L]])); }
    else if (k === "star") { const pts = []; for (let i = 0; i <= 10; i++) { const a = -Math.PI / 2 + i * Math.PI * 0.8; pts.push([x + Math.cos(a) * w / 2 + j(4), y + Math.sin(a) * h / 2 + j(4)]); } P.push(line(pts)); }
    else { const pts = []; for (let i = 0; i <= 30; i++) pts.push([x - w / 2 + (i / 30) * w + j(6), y + (i % 2 ? -1 : 1) * h / 2 + j(6)]); P.push(line(pts)); }
    return P;
  }
  const doodleNodes = shots.map((s, si) => {
    if (!s.doodles) return null;
    const svg = document.createElementNS(SVGNS, "svg"); svg.setAttribute("width", W); svg.setAttribute("height", H);
    svg.style.cssText = "position:absolute;left:0;top:0;pointer-events:none;display:none;overflow:visible;"; typeLayer.appendChild(svg);
    const items = s.doodles.map((d, di) => { const g = document.createElementNS(SVGNS, "g"); svg.appendChild(g); return { d, g, di, built: null }; });
    return { svg, items };
  });
  function doodleAnchor(s, d, t) {
    let v = null;
    if (Array.isArray(d.on)) v = new THREE.Vector3(...d.on);
    else if (typeof d.on === "string" && d.on.startsWith("card:")) { const c = (s.cards || []).find((q) => q.id === d.on.slice(5)); if (c) v = new THREE.Vector3(c.at[0], c.at[1], c.at[2]); }
    else if (d.on && actors[d.on] && actors[d.on].mesh.visible) v = actors[d.on].mesh.position.clone();
    if (!v) return null; v.project(camera); return [(v.x + 1) / 2, (1 - v.y) / 2];
  }
  function drawDoodles(si, t, alpha) {
    doodleNodes.forEach((n, i) => { if (n) n.svg.style.display = i === si ? "block" : "none"; });
    const n = doodleNodes[si]; if (!n) return; const s = shots[si];
    n.svg.style.opacity = String(alpha * clamp((s.t1 - t) / 0.12));
    for (const it of n.items) {
      const d = Object.assign({}, it.d), a = doodleAnchor(s, d, t);
      if (a) { d.x = a[0] + (d.dx || 0); d.y = a[1] + (d.dy || 0); }
      const key = [d.x, d.y].map((v) => v.toFixed(3)).join(",");
      if (it.key !== key) {   // (re)build the strokes where the anchor is now
        it.g.innerHTML = ""; it.key = key;
        it.paths = doodlePaths(d, 17 + it.di * 31).map((pd, pi) => { const e = document.createElementNS(SVGNS, "path"); e.setAttribute("d", pd);
          e.setAttribute("fill", "none"); e.setAttribute("stroke", d.color || pal.voice); e.setAttribute("stroke-width", String((d.width || 1) * H * 0.0085));
          e.setAttribute("stroke-linecap", "round"); e.setAttribute("stroke-linejoin", "round"); e.style.filter = "drop-shadow(0 2px 3px rgba(0,0,0,0.35))";
          it.g.appendChild(e); const L = e.getTotalLength(); e.style.strokeDasharray = `${L} ${L}`; return { e, L }; });
      }
      const dur = d.dur || 0.45, k = clamp((t - d.t) / dur), out = d.hold != null ? clamp((t - d.t - dur - d.hold) / 0.2) : 0, np = it.paths.length;
      it.paths.forEach((q, pi) => { const kk = clamp(k * np - pi); q.e.style.strokeDashoffset = String(q.L * (1 - outCubic(kk))); });
      it.g.style.opacity = String(k <= 0 ? 0 : 1 - out);
    }
  }
  function drawType(si, t, alpha) {
    typeNodes.forEach((n, i) => { if (n) n.box.style.display = i === si ? "block" : "none"; });
    const n = typeNodes[si]; if (!n) return;
    const s = shots[si];
    n.box.style.opacity = String(alpha * clamp((s.t1 - t) / 0.12));
    n.groups.forEach((g, gi) => {
      const next = n.groups[gi + 1], end = next ? next.t : Infinity;
      const live = t >= g.t - 0.02 && t < end;
      g.el.style.display = live ? "block" : "none";
      if (!live) return;
      g.el.style.opacity = String(clamp((end - t) / 0.1));
      if (n.box.classList.contains("vd-compose")) {   // earlier lines stay as a dimmed layer under the new one
        n.groups.forEach((h, hi) => { if (hi === gi - 1) { h.el.style.display = "block"; h.el.style.opacity = String(0.28 * clamp((t - g.t + 0.6) / 0.3));
          if (n.depth) h.el.style.transform = `translateZ(${-700 * outCubic(clamp((t - g.t) / 0.5))}px) rotateY(${-6 * clamp((t - g.t) / 0.5)}deg)`; } });
        // depth: the live group drifts slowly in 3D space while it is on screen
        g.el.style.transform = n.depth ? `rotateY(${Math.sin((t - g.t) * 0.7) * 4}deg) rotateX(${Math.sin((t - g.t) * 0.5) * 2}deg)` : "";
      }
      for (const w of g.words) {
        const a = clamp((t - w.t) / (w.role === "punch" ? 0.3 : 0.22)), e = outCubic(a);
        const rot = +(w.el.dataset.rot || 0), tilt = +(w.el.dataset.tilt || 0), skew = +(w.el.dataset.skew || 0);
        const sc = w.role === "punch" || w.role === "num" ? 1.32 - 0.32 * outBack(a) : 1;
        const lean = rot || tilt || skew ? `${n.depth ? "" : "perspective(900px) "}rotateY(${tilt}deg) rotate(${rot}deg) skewX(${skew}deg) ` : "";
        // depth typography: the word flies in from far (from: "deep", default with type.depth), from behind the lens ("near")
        // or from the side ("side"), sits at its own depth (place.z, px), then keeps drifting back slowly
        const pl = w.place || {}, from = pl.from || (n.depth ? "deep" : null);
        const z0 = from === "deep" ? -1600 : from === "near" ? 700 : 0, x0 = from === "side" ? (pl.x > 0.5 ? 900 : -900) : 0;
        const depthT = n.depth || pl.z || from ? `translate3d(${(1 - e) * x0}px,0,${(pl.z || 0) + (1 - e) * z0 - Math.max(0, t - w.t) * 22}px) ` : "";
        // effects on the whole word
        if (w.fx === "mark") w.el.style.backgroundSize = `${outCubic(clamp((t - w.t - 0.05) / 0.3)) * 100}% 100%`;
        if (w.fx === "bracket") w.el.style.setProperty("--b", String(outBack(clamp((t - w.t - 0.08) / 0.32))));
        if (!w.chars) {
          w.el.style.opacity = String(a <= 0 ? 0 : 0.15 + 0.85 * e);
          w.el.style.transform = `${depthT}${lean}translate3d(0,${(1 - e) * 0.38}em,0) scale(${sc})`;
        } else {
          // letters: flicker in colour and settle (default), drop in with colour (jitter), or type
          w.el.style.opacity = a <= 0 ? "0" : "1";
          w.el.style.transform = `${depthT}${lean}scale(${sc})`;
          w.chars.forEach((ch, i) => {
            if (w.fx === "type") { ch.style.opacity = t >= w.t + i * 0.05 ? "1" : "0"; return; }
            const slow = w.fx === "jitter", step = slow ? 0.04 : 0.028, ca = clamp((t - w.t - i * step) / (slow ? 0.28 : 0.2)), ce = outBack(ca);
            ch.style.opacity = ca <= 0 ? "0" : "1";
            if (!ch.dataset.arc) ch.style.transform = `translate3d(0,${(1 - ce) * (slow ? -0.8 : -0.45)}em,0) rotate(${(1 - ca) * (i % 2 ? 14 : -14)}deg)`;
            ch.style.color = t - w.t < step * i + (slow ? 0.75 : 0.32) ? JIT[(i + Math.floor(t * 12)) % JIT.length] : "";
          });
        }
        if (w.num) { const k = outCubic(clamp((t - w.t) / 0.55)); w.el.textContent = (w.num.v * k).toFixed(w.num.dec) + w.num.suf; }
      }
    });
  }

  // ------------------------------------------------------------------ kinetic 3D type (words that stand in the world)
  // An extruded word is a stack of flat copies of one text texture: the front copy carries the face colour,
  // the copies behind it get darker, so it reads as a solid block when the camera moves past it.
  function word3d(w) {
    const role = w.role || "punch";
    const font = role === "say" ? "800 200px Inter" : role === "num" ? "600 200px 'Pixelify Sans'" : role === "accent" ? "italic 600 200px 'EB Garamond'" : "400 200px Anton";
    const text = role === "punch" ? String(w.text).toUpperCase() : String(w.text);
    const cnv = document.createElement("canvas"); let x = cnv.getContext("2d"); x.font = font;
    const mw = Math.ceil(x.measureText(text).width) + 40; cnv.width = mw; cnv.height = 260; x = cnv.getContext("2d");
    x.font = font; x.fillStyle = "#ffffff"; x.textBaseline = "middle"; x.fillText(text, 20, 138);
    const tex = new THREE.CanvasTexture(cnv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    const h = w.size || 6, wd = h * mw / 260, depth = w.depth ?? h * 0.24, N = 16;
    const face = new THREE.Color(w.color || (role === "punch" ? pal.voice : role === "num" ? pal.voice2 : "#ffffff"));
    const g = new THREE.Group(), geo = new THREE.PlaneGeometry(wd, h);
    for (let i = N; i >= 0; i--) {
      const c = i === 0 ? face.clone().multiplyScalar(1.3) : face.clone().multiplyScalar(0.14 + 0.26 * (1 - i / N));
      const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex, alphaTest: 0.5, color: c, side: THREE.DoubleSide }));
      m.position.z = -depth * i / N; g.add(m);
    }
    scene.add(g); return g;
  }

  // ------------------------------------------------------------------ camera
  const CAMS = {
    // `side` puts the subject on the left ("left", default) or right third, leaving the other side for type
    "hero-push": (p, c) => { const k = c.side === "right" ? -1 : c.side === "centre" ? 0 : 1;
      return { from: [p[0] + 2.4 + k * 4.4, p[1] + 0.4, p[2] + 27], to: [p[0] + 1.2 + k * 3.8, p[1] + 0.2, p[2] + 22.5], look: [p[0] + k * 3.6, p[1] - 0.3, p[2]], fov: 30 }; },
    "hero-orbit": (p, c) => { const R = c.dist || 25, o = (a) => [p[0] + Math.sin(a) * R, p[1] + 1.2, p[2] + Math.cos(a) * R]; return { from: o(-0.34), to: o(0.1), look: [p[0], p[1] - (c.dist ? 1.5 : 0), p[2]], fov: 30 }; },
    "low-hero": (p) => ({ from: [p[0] - 7, 2.2, p[2] + 19], to: [p[0] - 5, 3.0, p[2] + 17], look: [p[0], p[1] + 0.6, p[2]], fov: 34 }),
    // a sideways move past the subject: the clearest way to show depth, near things cross faster than far ones
    "dolly": (p, c) => { const k = c.dir === "left" ? -1 : 1; return { from: [p[0] - 13 * k, p[1] + 1.4, p[2] + 31], to: [p[0] + 11 * k, p[1] + 0.8, p[2] + 28], look: [p[0], p[1] - 0.5, p[2] - 4], fov: 32 }; },
    "two-shot": () => ({ from: [-3.5, 7.2, 36], to: [2, 6.6, 32], look: [0.5, 5.6, 8.5], fov: 32 }),
    "wide-orbit": () => { const o = (a) => [Math.sin(a) * 50, 17, -2 + Math.cos(a) * 50]; return { from: o(0.5), to: o(0.2), look: [0, 8, -3], fov: 34 }; },
    "top-down": () => ({ from: [0, 46, -6.5], to: [0, 40, -7.5], look: [0, 8, -8], up: [0.12, 0, -1], upTo: [-0.05, 0, -1], fov: 34 }),
    "monitor-push": () => ({ from: [3, 16, 16], to: [0.4, 16.4, 2.5], look: MARKS.screen, fov: 34 }),
    "prop-rack": (p) => ({ from: [p[0] + 7, p[1] + 2, p[2] + 19], to: [p[0] + 4.5, p[1] + 1.2, p[2] + 15], look: p, fov: 30 }),
    "void-centre": (p) => ({ from: [p[0] + 1.5, p[1] + 1.2, p[2] + 31], to: [p[0], p[1] + 0.6, p[2] + 26], look: p, fov: 30 }),
    // film language: each has one job (references/cinematography.md)
    "crane": (p) => ({ from: [p[0] + 4, p[1] - 3, p[2] + 24], to: [p[0] - 2, p[1] + 15, p[2] + 34], look: p, lookTo: [p[0], p[1] - 2, p[2]], fov: 34 }),
    "pull-back": (p) => ({ from: [p[0] + 1, p[1] + 0.3, p[2] + 12], to: [p[0] - 3, p[1] + 5, p[2] + 46], look: p, fov: 34 }),
    "push-through": (p) => ({ from: [p[0] - 4, p[1] + 5, p[2] + 50], to: [p[0] + 0.6, p[1] + 0.2, p[2] + 13], look: p, fov: 34 }),
    "dutch": (p) => ({ from: [p[0] + 5, p[1] - 2, p[2] + 24], to: [p[0] + 3, p[1] - 1.4, p[2] + 21], look: p, up: [0.26, 1, 0], upTo: [0.17, 1, 0], fov: 32 }),
    "ots": (p) => ({ from: [p[0] - 9, p[1] + 3, p[2] + 15], to: [p[0] - 7.5, p[1] + 2.6, p[2] + 13], look: [p[0] + 9, p[1] - 1, p[2] - 4], fov: 36 }),
    "vertigo": (p) => ({ from: [p[0] + 0.5, p[1] + 0.3, p[2] + 15], to: [p[0] + 0.5, p[1] + 0.3, p[2] + 40], look: p, fov: 60, fovTo: 23 }),
    "snap-zoom": (p) => ({ from: [p[0] + 3, p[1] + 1, p[2] + 34], to: [p[0] + 2, p[1] + 0.8, p[2] + 31], look: p, fov: 40 }),
  };
  function place(si, t) {   // where everything is in shot si at time t
    const s = shots[si], pos = {};
    (s.cast || []).forEach((c) => { const m = castState(s, c, t ?? s.t0).m; const d = (actors[c.who] || {}).def || CAST[c.who]; if (!d) return; pos[c.who] = [m[0], m[1] + d.h * d.px * d.head, m[2]]; });
    (s.props || []).forEach((p) => { pos["prop:" + p.id] = p.at; });
    (s.cards || []).forEach((c) => { pos["card:" + c.id] = c.at; });
    return pos;
  }
  function point(si, ref, t) {
    if (Array.isArray(ref)) return ref;
    const pos = place(si, t), info = setInfo[shots[si].set || "studio"];
    if (pos[ref]) return pos[ref];
    if (ref === "screen") return info && info.screen ? info.screen.at : MARKS.screen;
    if (ref === "desk") return [0, 9, -8];
    if (info && info.marks[ref]) { const m = info.marks[ref]; return [m[0], (m[1] || 0) + 6, m[2]]; }
    if (MARKS[ref]) { const m = MARKS[ref]; return [m[0], m[1] + 6, m[2]]; }
    const first = Object.values(pos)[0]; return first || [0, 6, 8];
  }
  function cameraAt(si, t) {
    const s = shots[si], c = Object.assign({ preset: "hero-push" }, s.cam || {});
    // the subject is read at the middle of the shot (or live with `follow: true`), so a walking subject stays in frame
    const on = point(si, c.on || (s.cast && s.cast[0] && s.cast[0].who) || "stage", c.follow ? t : (s.t0 + s.t1) / 2);
    const info = setInfo[s.set || "studio"], own = info && info.cams[c.preset];
    const base = own ? Object.assign({}, own) : (CAMS[c.preset] || CAMS["hero-push"])(on, c);
    const k = Object.assign(base, c);
    const lin = clamp((t - s.t0) / (s.t1 - s.t0)), u = 0.55 * lin + 0.45 * smooth(lin);   // still moving at both cuts
    if (c.keys && c.keys.length > 1) {   // a long take: a smooth path through keyframes, never stopping inside the shot
      const ks = c.keys; let i = 0; while (i < ks.length - 2 && t >= ks[i + 1].t) i++;
      const a = ks[i], b = ks[i + 1], q = clamp((t - a.t) / Math.max(0.01, b.t - a.t)), e = 0.25 * q + 0.75 * smooth(q);
      const P = (j, key) => v3((ks[clamp(j, 0, ks.length - 1)][key]) || ks[clamp(j, 0, ks.length - 1)].from);
      const cr3 = (key) => { const p0 = P(i - 1, key), p1 = P(i, key), p2 = P(i + 1, key), p3 = P(i + 2, key);
        return new THREE.Vector3(...[0, 1, 2].map((ax) => { const g = (v) => v.getComponent(ax); return 0.5 * ((2 * g(p1)) + (-g(p0) + g(p2)) * e + (2 * g(p0) - 5 * g(p1) + 4 * g(p2) - g(p3)) * e * e + (-g(p0) + 3 * g(p1) - 3 * g(p2) + g(p3)) * e * e * e); })); };
      k.from = cr3("from").toArray(); k.to = k.from; k.look = cr3("look").toArray(); k.lookTo = k.look;
      k.fov = lerp(a.fov || k.fov || 34, b.fov || a.fov || k.fov || 34, e); k.fovTo = k.fov;
      if (a.up || b.up) { k.up = v3(a.up || [0, 1, 0]).lerp(v3(b.up || [0, 1, 0]), e).toArray(); k.upTo = k.up; }
    }
    const from = v3(k.from), to = v3(k.to || k.from);
    camera.position.lerpVectors(from, to, c.keys ? 0 : u);
    camera.position.x += Math.sin(t * 0.71) * 0.1; camera.position.y += Math.sin(t * 0.93 + 1.3) * 0.07;
    if (k.shake) { camera.position.x += (Math.sin(t * 23.1) * 0.12 + Math.sin(t * 37.7) * 0.07) * k.shake; camera.position.y += Math.sin(t * 29.3 + 1) * 0.1 * k.shake; }
    const look = v3(k.look).lerp(v3(k.lookTo || k.look), u);
    camera.up.copy(v3(k.up || [0, 1, 0]).lerp(v3(k.upTo || k.up || [0, 1, 0]), u)).normalize();
    camera.fov = lerp(k.fov || 32, k.fovTo || k.fov || 32, u);
    const sn = k.snap || (c.preset === "snap-zoom" ? { t: (s.t0 + s.t1) / 2, fov: 17 } : null);   // a sudden punch-in on a word
    if (sn) camera.fov = lerp(camera.fov, sn.fov, outCubic(clamp((t - sn.t) / 0.14)));
    camera.fov = portFov(camera.fov);
    camera.updateProjectionMatrix();
    camera.lookAt(look);
    const f = s.focus || c.on || (s.cast && s.cast[0] && s.cast[0].who) || look.toArray();
    const fp = typeof f === "object" && !Array.isArray(f)
      ? v3(point(si, f.from, t)).lerp(v3(point(si, f.to, t)), smooth(clamp((lin - 0.25) / 0.5)))
      : v3(point(si, f, t));
    post.uniforms.uFocus.value = camera.position.distanceTo(fp);
    return u;
  }

  // ------------------------------------------------------------------ one frame
  function renderAt(t) {
    if (!built) return;
    t = clamp(t, 0, DUR - 1e-4);
    let si = shots.findIndex((s) => t >= s.t0 && t < s.t1); if (si < 0) si = shots.length - 1;
    const s = shots[si], local = t - s.t0;
    for (const [name, g] of Object.entries(setGroups)) g.visible = name === (s.set || "studio");
    const setName = s.set || "studio", scr = setInfo[setName] && setInfo[setName].screen;
    const inStudio = !!HAS_SCREEN[setName] || !!scr;
    screen.visible = inStudio;
    if (scr) { screen.position.set(...scr.at); screen.scale.set((scr.w || 17) / 17, (scr.h || 10) / 10, 1); } else { screen.position.set(...MARKS.screen); screen.scale.set(1, 1, 1); }
    const u = cameraAt(si, t);
    post.uniforms.uAperture.value = (s.lens && s.lens.aperture) ?? lens.aperture;
    if (inStudio) drawScreen(s.screen, u);
    // cast
    for (const a of Object.values(actors)) a.mesh.visible = a.sh.visible = false;
    trail.forEach((m) => { m.visible = false; }); ghost.visible = false;
    const L = Object.assign({}, LIGHTS.default, LIGHTS[setName] || {}, (setInfo[setName] && setInfo[setName].castLight) || {});
    (s.cast || []).forEach((c) => {
      const a = actors[c.who]; if (!a) return; const d = a.def, cs = castState(s, c, t), m = cs.m, U = a.mesh.material.uniforms;
      const talking = cs.pose === "talk" && (!c.say || (t >= c.say[0] && t < c.say[1]));
      const stt = { blink: ((t + a.seed) % 3.4) < 0.12, mouth: talking && Math.floor(t * 8) % 2 === 0, alt: Math.floor(t * cs.cadence) % 2 === 0 };
      const pc = poseCanvas(d, cs.pose);
      U.map.value = texOf(pc || d.image || spriteCanvas(c.who, cs.pose, stt));
      if (pc) U.uTexel.value.set(1 / pc.width, 1 / pc.height);
      const pd = d.depths && pc ? d.depths[Object.keys(d.images).find((k) => d.images[k] === pc)] : null;
      U.uHasDepth.value = pd && c.flat !== true ? 1 : 0;
      if (pd) { U.uDepth.value = depthTexOf(pd); U.uDTexel.value.set(1 / pd.width, 1 / pd.height); U.uLift.value = d.lift; }
      const flip = (c.flip ?? ((cs.moving || cs.trail) && cs.dir < 0)) ? -1 : 1;
      U.uFlip.value = flip; U.uKey.value.set(L.key); U.uKeySide.value = L.keySide; U.uRim.value.set(L.rim); U.uRimSide.value = L.rimSide; U.uShade.value = L.shade;
      let y = 0, rot = cs.rotZ;
      let breathe = 1;
      if (d.unit && !cs.moving && !cs.trail) {   // picture mascot: smooth breathing, a talk bounce on syllables
        breathe = 1 + 0.012 * Math.sin((t + a.seed) * 2.6) + (talking ? 0.018 * Math.abs(Math.sin(t * 9.5)) : 0);
        if (cs.pose === "cheer") y += Math.abs(Math.sin(t * 6.5)) * 0.6;
      } else if (!cs.moving && !cs.trail) {
        y = (Math.floor(t * 4 + a.seed) % 2) * 0.18;
        if (cs.pose === "jump" && !c.acts) y += Math.abs(Math.sin(t * 6.5)) * 1.8; else if (cs.pose === "cheer") y += Math.abs(Math.sin(t * 6.5)) * 0.7;
      }
      if ((d.image || d.unit) && cs.moving) { rot += Math.sin(t * cs.cadence * Math.PI) * 0.06; y += Math.abs(Math.sin(t * cs.cadence * Math.PI)) * 0.35; }   // pictures step
      if (c.enter === "hop") { const e = clamp(local / 0.4); y += Math.sin(e * Math.PI) * 3 * (1 - e * 0.3); }
      const PW = pc ? pc.width * d.px : 1, H = (pc ? pc.height : d.h) * d.px;
      a.mesh.position.set(m[0], m[1] + y + (H / 2) * cs.sy * breathe, m[2]);
      a.mesh.rotation.set(0, Math.atan2(camera.position.x - m[0], camera.position.z - m[2]), rot);
      a.mesh.scale.set(flip * cs.sx * PW, cs.sy * breathe * (pc ? H : 1), 1);
      const lift = clamp((m[1] + y - cs.ground) / 14), w = (pc ? Math.min(PW, d.w * d.px * 1.3) : d.w * d.px) * 0.9 * (1 - lift * 0.55);
      a.sh.position.set(m[0], cs.ground + 0.36, m[2]); a.sh.scale.set(w, w, 1); a.sh.material.opacity = 1 - lift * 0.7;
      a.mesh.visible = a.sh.visible = true;
      for (const td of c.dissolve || []) {   // 0.18 s out to pixels, 0.3 s back together
        const q = (t - td) / 0.48; if (q <= 0 || q >= 1) continue;
        const spread = q < 0.38 ? smooth(q / 0.38) : 1 - smooth((q - 0.38) / 0.62), dots = spriteDots(c.who, cs.pose, d), n = dots.P.length / 3;
        const pos = new Float32Array(dots.P.length);
        for (let i = 0; i < n; i++) { const h1 = Math.sin(i * 12.9898) * 43758.5453, h2 = Math.sin(i * 78.233) * 12543.31, h3 = Math.sin(i * 39.425) * 9871.7;
          const rx = (h1 - Math.floor(h1) - 0.5) * 9, ry = (h2 - Math.floor(h2) - 0.5) * 7 + 1.5, rz = (h3 - Math.floor(h3) - 0.5) * 4;
          pos[i * 3] = dots.P[i * 3] * flip + rx * spread; pos[i * 3 + 1] = dots.P[i * 3 + 1] + ry * spread; pos[i * 3 + 2] = rz * spread; }
        ghost.geometry.setAttribute("position", new THREE.BufferAttribute(pos, 3)); ghost.geometry.setAttribute("color", new THREE.BufferAttribute(dots.C, 3));
        ghost.position.set(m[0], m[1], m[2]); ghost.rotation.y = a.mesh.rotation.y; ghost.material.size = d.px * 1.15; ghost.visible = true;
        a.mesh.visible = q > 0.92;
      }
      if (cs.trail) trail.forEach((tm, i) => {
        const p = castState(s, c, t - (i + 1) * 0.04); if (!p.trail) return;
        const k = 1 - i / trail.length, sz = 0.9 * k;
        tm.position.set(p.m[0], p.m[1] + H * 0.45, p.m[2] - 0.2); tm.scale.set(sz, sz, 1); tm.material.opacity = 0.75 * k;
        tm.rotation.y = a.mesh.rotation.y; tm.visible = true;
      });
    });
    // cards and props
    for (const m of things.values()) m.visible = false;
    (s.cards || []).forEach((c) => {
      const m = thing(`card|${si}|${c.id}`, () => cardMesh(c)), a = clamp((t - (c.t ?? s.t0)) / 0.32);
      if (a <= 0) return; const sc = outBack(a);
      m.position.set(c.at[0], c.at[1] + Math.sin(t * 1.3 + c.at[0]) * 0.18, c.at[2]); m.scale.setScalar(sc);
      m.rotation.y = Math.atan2(camera.position.x - c.at[0], camera.position.z - c.at[2]); m.visible = true;
    });
    (s.props || []).forEach((p) => {
      const m = thing(`prop|${p.id}`, () => docMesh(p)), a = clamp((t - (p.t ?? s.t0)) / 0.4);
      if (a <= 0) return;
      m.position.set(p.at[0], p.at[1] + Math.sin(t * 1.1) * 0.22 + (1 - outCubic(a)) * -3, p.at[2]);
      m.scale.setScalar((p.scale || 1) * outBack(a)); m.rotation.set(0.08, -0.35 + Math.sin(t * 0.6) * 0.12, 0.06); m.visible = true;
    });
    (s.type3d || []).forEach((w, i) => {
      const a = clamp((t - (w.t ?? s.t0)) / (w.dur || 0.5)); if (a <= 0) return;
      const g = thing(`t3|${si}|${i}`, () => word3d(w)), e = outCubic(a), bk = outBack(a), anim = w.anim || "slam";
      if (anim === "through") {   // starts far away, flies at the lens and passes it
        const q = clamp((t - w.t) / (w.dur || 1.0)); if (q >= 1) return; const k = q * q;
        g.position.set(lerp(w.at[0], camera.position.x, k), lerp(w.at[1], camera.position.y, k), lerp(w.at[2], camera.position.z + 4, k));
        g.rotation.set(0, (w.ry || 0) * (1 - k), 0); g.scale.setScalar(1 + q * 0.6); g.visible = true; return;
      }
      let [x, y, z] = w.at, sc = 1, rx = 0, ry = (w.ry || 0) + Math.sin(t * 0.8 + i) * 0.035;
      if (anim === "slam") { sc = 2.3 - 1.3 * bk; z += (1 - e) * 14; rx = (1 - e) * -0.3; }
      else if (anim === "rise") { y -= (1 - e) * 5; rx = (1 - bk) * -1.35; }
      else if (anim === "swing") { ry += (1 - bk) * 1.5; }
      else if (anim === "drop") { y += (1 - bk) * 11; }
      g.position.set(x, y, z); g.rotation.set(rx, ry, 0); g.scale.setScalar(sc); g.visible = true;
    });
    // transitions: each sits across a cut, half before and half after
    const U = post.uniforms; U.uMosaic.value = U.uDots.value = U.uWhip.value = U.uFlash.value = U.uIris.value = 0; U.uBlock.value = 1; let cover = 0;
    for (let i = 0; i < shots.length - 1; i++) {
      const kind = shots[i].out || "cut", d = TRANS[kind] || 0; if (!d) continue;
      const p = (t - (shots[i].t1 - d / 2)) / d; if (p <= 0 || p >= 1) continue;
      const k = tri(p); cover = Math.max(cover, k);
      if (kind === "mosaic") U.uMosaic.value = p;
      else if (kind === "dots") U.uDots.value = p;
      else if (kind === "pixelate") U.uBlock.value = 1 + 70 * k * k * (H / 1080);
      else if (kind === "whip") U.uWhip.value = (p < 0.5 ? 1 : -1) * k;
      else if (kind === "flash") U.uFlash.value = k;
      else if (kind === "iris") U.uIris.value = k;
    }
    U.uFade.value = Math.max(t < 0.25 && !shots[0].flicker ? 1 - clamp(t / 0.25) : 0, 1 - clamp((DUR - t) / 0.3));
    // wash: [{ t, color, k }] - the world's colour turns on a word without a cut
    U.uSat.value = (s.grade && s.grade.sat) ?? lens.sat; U.uCon.value = (s.grade && s.grade.contrast) ?? lens.contrast;   // per-shot grade: { sat, contrast }
    U.uWashK.value = 0;
    for (const w of s.wash || []) { const a = clamp((t - w.t) / (w.dur || 0.25)); if (a > 0) { U.uWash.value.set(w.color); U.uWashK.value = (w.k ?? 0.65) * smooth(a); } }
    // flicker: { t: [a, b], looks: ["negative", "red", "mono", "normal", ...] } - a burst of looks on the opening onsets
    U.uLook.value = 0;
    if (s.flicker && t >= s.flicker.t[0] && t < s.flicker.t[1]) {
      const L = s.flicker.looks || ["negative", "red", "mono", "normal"], n = L.length, i = Math.min(n - 1, Math.floor((t - s.flicker.t[0]) / ((s.flicker.t[1] - s.flicker.t[0]) / n)));
      U.uLook.value = { normal: 0, negative: 1, red: 2, mono: 3 }[L[i]] || 0;
    }
    U.uTime.value = Math.floor(t * 30);
    drawType(si, t, 1 - clamp(cover * 1.7));
    drawDoodles(si, t, 1 - clamp(cover * 1.7));
    moves.draw(si, t, 1 - clamp(cover * 1.7));
    renderer.setRenderTarget(rt); renderer.render(scene, camera);
    renderer.setRenderTarget(null); renderer.render(postScene, postCam);
  }

  window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
  const ready = Promise.all([dataReady, document.fonts.ready]).then(() => Promise.all(
    ["800 40px Inter", "400 40px Anton", "italic 500 40px 'EB Garamond'", "600 40px 'Pixelify Sans'"].map((f) => document.fonts.load(f))
  )).then(() => { scrKey = ""; renderAt(window.__hfThreeTime || 0); });
  window.__hf = window.__hf || {}; window.__hf.buildReady = window.__hf.buildReady || {}; window.__hf.buildReady["voxel-diorama"] = ready;
  if (/[?&]preview/.test(location.search)) {   // local preview only: play in real time
    const t0 = performance.now(); const loop = () => { renderAt(((performance.now() - t0) / 1000) % DUR); requestAnimationFrame(loop); }; ready.then(loop);
  }
  return { renderAt, duration: DUR, ready };
}
