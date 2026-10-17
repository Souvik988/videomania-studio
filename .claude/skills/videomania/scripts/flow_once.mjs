// Flow single-click helper for Video Mania. Never generates on its own.
//
//   node flow_once.mjs inspect
//       Report composer state: prompt, settings chip, model, ratio, credits text, progress.
//       Opens and closes Flow's settings panel to read the model (no generation).
//   node flow_once.mjs click --expect-model omni --id G1 --approval "user's approval words"
//       Pre-flight (prompt present, nothing generating, model matches, button in view), then ONE
//       real mouse click on "Start generation"; appends a line to the ledger. Refuses otherwise.
//   node flow_once.mjs watch [--max 300]
//       Observe only: poll until a new media tile appears or the time limit passes.
//   node flow_once.mjs fetch --out <dir>
//       Click Flow's "Download batch" (no credits), wait for the zip in Downloads, copy it to <dir>.
//       Then run: python scripts/flow_ingest.py --dir <dir> --id <ID> (extract, probe, QC sheet, provenance).
//
// Requires the Flow Chrome window started by the google-flow MCP in CDP mode (127.0.0.1:9222).
// Standing user rules: references/flow-asset-production.md (Omni Flash only, never Veo 3.1,
// one explicit approval per generation, keep watermarks).

import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const MCP_DIR = process.env.FLOW_MCP_DIR || path.join(os.homedir(), "video-production-workbench", "mcp", "google-flow-mcp");
const require = createRequire(path.join(MCP_DIR, "package.json"));
const puppeteer = require("puppeteer");
const CDP = process.env.FLOW_BROWSER_CDP_URL || "http://127.0.0.1:9222";
const LEDGER = path.join(MCP_DIR, "outputs", "flow-click-ledger.jsonl");

const args = process.argv.slice(2);
const op = args[0];
const opt = (name, dflt = undefined) => { const i = args.indexOf(`--${name}`); return i > 0 ? args[i + 1] : dflt; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function flowPage() {
  const browser = await puppeteer.connect({ browserURL: CDP, defaultViewport: null });
  const pages = await browser.pages();
  const page = pages.find((p) => /flow\.google\.com\/project/.test(p.url())) || pages.find((p) => /flow\.google\.com/.test(p.url()));
  if (!page) { await browser.disconnect(); throw new Error("No Flow tab found on " + CDP); }
  return { browser, page };
}

async function state(page) {
  return page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
    const tb = document.querySelector('[role="textbox"]');
    const btn = document.querySelector('button[aria-label="Start generation"]');
    const chip = document.querySelector('button[aria-label="Settings trigger"]');
    const tiles = Array.from(document.querySelectorAll("img")).filter((e) => vis(e) && e.naturalWidth > 150 && /flow-content\.google/.test(e.src)).length;
    const txt = document.body.innerText.replace(/\s+/g, " ");
    return {
      url: location.href.slice(0, 90),
      prompt: (tb?.innerText || "").slice(0, 160),
      settingsChip: (chip?.innerText || "").replace(/\s+/g, " ").trim(),
      startEnabled: !!btn && !btn.disabled,
      progress: document.querySelectorAll('[role="progressbar"]').length,
      percent: (txt.match(/\b(\d{1,3})%/) || [])[1] || null,
      mediaTiles: tiles,
    };
  });
}

async function readPanel(page) {
  const trig = await page.$('button[aria-label="Settings trigger"]');
  if (!trig) return { error: "no settings trigger" };
  await trig.click();
  await sleep(1000);
  const panel = await page.evaluate(() => {
    const radios = Array.from(document.querySelectorAll('[role="radio"]')).map((e) => ({ t: (e.innerText || "").replace(/\s+/g, " ").trim(), on: e.getAttribute("aria-checked") === "true" }));
    const model = (document.querySelector('button[aria-label="Select model family"]')?.innerText || "").replace("arrow_drop_down", "").trim();
    const credits = ((document.body.innerText.match(/Generating will use[^\n]*/) || [])[0] || "").trim();
    return { selected: radios.filter((r) => r.on).map((r) => r.t), model, credits };
  });
  await page.keyboard.press("Escape");
  await sleep(400);
  return panel;
}

function ledger(entry) {
  fs.mkdirSync(path.dirname(LEDGER), { recursive: true });
  fs.appendFileSync(LEDGER, JSON.stringify(entry) + "\n");
}

async function main() {
  if (op === "inspect") {
    const { browser, page } = await flowPage();
    const s = await state(page);
    const panel = await readPanel(page);
    console.log(JSON.stringify({ ...s, panel }, null, 2));
    await browser.disconnect();
    return 0;
  }
  if (op === "click") {
    const expectModel = (opt("expect-model", "omni") || "").toLowerCase();
    const id = opt("id");
    const approval = opt("approval");
    if (!id || !approval) { console.error("REFUSED: --id and --approval (the user's approval words) are required"); return 2; }
    const { browser, page } = await flowPage();
    const s = await state(page);
    const panel = await readPanel(page);
    const problems = [];
    if (!s.prompt) problems.push("composer has no prompt");
    if (!s.startEnabled) problems.push("Start generation is not enabled");
    if (s.progress > 0 || s.percent) problems.push("a generation already appears to be running");
    if (!panel.model.toLowerCase().includes(expectModel)) problems.push(`model is "${panel.model}", expected to contain "${expectModel}"`);
    if (/veo/i.test(panel.model)) problems.push("Veo models are banned by the user");
    if (problems.length) { console.log(JSON.stringify({ refused: problems, state: s, panel }, null, 2)); await browser.disconnect(); return 3; }
    const btn = await page.$('button[aria-label="Start generation"]');
    await btn.evaluate((e) => e.scrollIntoView({ block: "center" }));
    const box = await btn.boundingBox();
    const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (!box || box.y + box.height > vp.h || box.x + box.width > vp.w) { console.log("REFUSED: button not fully in view", JSON.stringify({ box, vp })); await browser.disconnect(); return 4; }
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 6 });
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    const entry = { at: new Date().toISOString(), id, approval, model: panel.model, settings: s.settingsChip, credits: panel.credits, prompt: s.prompt, url: s.url };
    ledger(entry);
    console.log(JSON.stringify({ clickedOnce: true, ...entry }, null, 2));
    await browser.disconnect();
    return 0;
  }
  if (op === "watch") {
    const max = Number(opt("max", "300"));
    const { browser, page } = await flowPage();
    const before = (await state(page)).mediaTiles;
    const t0 = Date.now();
    while ((Date.now() - t0) / 1000 < max) {
      const s = await state(page);
      console.log(`${Math.round((Date.now() - t0) / 1000)}s tiles=${s.mediaTiles} progress=${s.progress} pct=${s.percent}`);
      if (s.mediaTiles > before && !s.progress && !s.percent) { console.log("DONE: new media tile present"); break; }
      if (s.mediaTiles > 0 && before === 0 && !s.percent && (Date.now() - t0) > 20000) { console.log("DONE: media tile present"); break; }
      await sleep(10000);
    }
    await page.screenshot({ path: path.join(MCP_DIR, "screenshots", `watch-${Date.now()}.png`) });
    await browser.disconnect();
    return 0;
  }
  if (op === "fetch") {
    const out = opt("out");
    if (!out) { console.error("--out <dir> required"); return 2; }
    const dl = path.join(os.homedir(), "Downloads");
    const startedAt = Date.now();
    const { browser, page } = await flowPage();
    const btn = await page.$('button[aria-label="Download batch"]');
    if (!btn) { console.log("REFUSED: no 'Download batch' button (select the generated tile first)"); await browser.disconnect(); return 3; }
    await btn.click(); // download only; no generation, no credits
    await browser.disconnect();
    let found = null;
    for (let i = 0; i < 60 && !found; i++) {
      await sleep(3000);
      const zips = fs.readdirSync(dl).filter((f) => f.endsWith(".zip") || f.endsWith(".mp4"))
        .map((f) => ({ f, t: fs.statSync(path.join(dl, f)).mtimeMs })).filter((x) => x.t >= startedAt - 2000).sort((a, b) => b.t - a.t);
      if (zips.length && !fs.existsSync(path.join(dl, zips[0].f + ".crdownload"))) found = zips[0].f;
    }
    if (!found) { console.log("TIMEOUT: no new download in", dl); return 5; }
    fs.mkdirSync(out, { recursive: true });
    const dest = path.join(out, "flow-download" + path.extname(found));
    fs.copyFileSync(path.join(dl, found), dest);
    console.log(JSON.stringify({ downloaded: path.join(dl, found), copiedTo: dest }, null, 2));
    return 0;
  }
  console.error("usage: inspect | click --expect-model omni --id G1 --approval \"...\" | watch | fetch --out <dir>");
  return 1;
}

main().then((code) => process.exit(code)).catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
