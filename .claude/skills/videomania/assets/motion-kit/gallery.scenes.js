// Gallery / look book: every motion-fx effect plus camera windows and spotlight, one per scene.
// Inject with: new_composition.py --project mk-gallery --look <look> --format 9:16 --duration 34 --scenes-js assets/motion-kit/gallery.scenes.js --gallery
      const label = (s, text, at) => { const d = document.createElement("div"); d.style.cssText = "position:absolute;left:90px;top:250px;font:700 30px var(--mk-mono);letter-spacing:.12em;color:var(--mk-muted)"; d.textContent = text; s.appendChild(d); MK.maskRise(tl, d, at, { by: "chars", stagger: 0.012 }); };
      scene("s01", 0, 3, (s, t) => { label(s, "01 HEADLINE · MASK RISE", t + 0.1);
        MKFX.headline(tl, s, t + 0.3, { x: 90, y: 560, w: 900, lines: ["One object", "changes shape"], size: 150, accentWord: "shape" }); });
      scene("s02", 3, 6.2, (s, t) => { label(s, "02 CHART MORPH", t + 0.1);
        MKFX.chartMorph(tl, s, t + 1.2, { x: 90, y: 560, w: 900, h: 640, values: [42, 55, 48, 70, 64, 92], labels: ["M", "T", "W", "T", "F", "S"], tag: "92", sample: true }); });
      scene("s03", 6.2, 9.5, (s, t) => { label(s, "03 DASHBOARD ZOOM", t + 0.1);
        MKFX.dashboardZoom(tl, s, t + 1.1, { tiles: [{ x: 90, y: 420, w: 430, h: 260, title: "Orders", value: "1,284" }, { x: 560, y: 420, w: 430, h: 260, title: "Repeat", value: "37%" }, { x: 90, y: 720, w: 900, h: 300, title: "Revenue", value: "₹4.2L" }],
          pick: 1, card: { x: 90, y: 480, w: 900, h: 700 }, title: "Repeat customers", value: "37%", delta: "example" }); });
      scene("s04", 9.5, 12.5, (s, t) => { label(s, "04 CARD → WORKSPACE", t + 0.1);
        MKFX.cardToWorkspace(tl, s, t + 0.9, { from: { x: 90, y: 1050, w: 420, h: 200 }, to: { x: 60, y: 400, w: 960, h: 820 }, title: "Launch plan", body: ["Banner swapped", "Offer live", "Customers notified"] }); });
      scene("s05", 12.5, 15.5, (s, t) => { label(s, "05 SPRING STACK", t + 0.1);
        MKFX.springStack(tl, s, t + 0.9, { x: 240, y: 520, w: 600, h: 620, cards: [{ title: "Basic", sub: "one app" }, { title: "Pro", sub: "app + web" }, { title: "Full", sub: "app + web + dashboard" }] }); });
      scene("s06", 15.5, 19.5, (s, t) => { label(s, "06 FLOWING PATHS", t + 0.1);
        MKFX.flowingPaths(tl, s, t + 0.9, { source: { x: 540, y: 520, label: "Your offer" }, channels: [{ x: 230, y: 860, label: "App" }, { x: 540, y: 860, label: "iOS" }, { x: 850, y: 860, label: "Web" }], result: { x: 540, y: 1200, label: "Customers" } }); });
      scene("s07", 19.5, 22.5, (s, t) => { label(s, "07 COUNTER TAG", t + 0.1);
        MKFX.counterTag(tl, s, t + 2.0, { x: 190, y: 560, w: 700, h: 300, to: 50000, format: { prefix: "₹", group: "indian" }, label: "POORA SYSTEM" }); });
      scene("s08", 22.5, 25.5, (s, t) => { label(s, "08 NOTIFICATIONS + CLICK", t + 0.1);
        const n = MKFX.notifications(tl, s, [t + 0.5, t + 0.9, t + 1.3], { x: 90, y: 440, w: 900, items: [{ title: "New order", body: "2 items · example", time: "now" }, { title: "Cart recovered", body: "reminder sent", time: "1m" }, { title: "Banner live", body: "SALE is up", time: "2m" }] });
        MKFX.cursorClick(tl, s, [980, 1500], [700, 520], t + 2.1, { target: n.cards[2] }); });
      scene("s09", 25.5, 27.2, (s, t) => { label(s, "09 KEYHOLE PASS", t + 0.1);
        const door = document.createElement("div"); door.style.cssText = "position:absolute;left:390px;top:620px;width:300px;height:520px;border-radius:16px;background:var(--mk-surface);border:10px solid var(--mk-ink);box-sizing:border-box"; s.appendChild(door);
        const hole = document.createElement("div"); hole.style.cssText = "position:absolute;left:526px;top:846px;width:28px;height:28px;border-radius:50%;background:var(--mk-ink)"; s.appendChild(hole);
        const next = document.createElement("div"); next.style.cssText = "position:absolute;inset:0;background:var(--mk-accent);display:flex;align-items:center;justify-content:center;font:900 130px var(--mk-display);color:#fff;text-transform:uppercase"; next.textContent = "inside"; s.appendChild(next);
        MKFX.irisPass(tl, next, t + 0.8, { cx: 540, cy: 860, r0: 14, r1: 1700, dur: 0.45 }); });
      scene("s10", 27.2, 30, (s, t) => { label(s, "10 PARTICLE WORD", t + 0.1);
        MKFX.particleWord(tl, s, t + 1.6, { text: "MANIA", x: 90, y: 700, w: 900, h: 300, font: "800 260px 'Barlow Condensed'", step: 11, color: "var(--mk-accent)" }); });
      scene("s11", 30, 34, (s, t) => { label(s, "11 CAMERA WINDOWS + SPOTLIGHT", t + 0.1);
        const world = document.createElement("div"); world.style.cssText = "position:absolute;left:0;top:0;width:2400px;height:1600px"; s.appendChild(world);
        const st = {}; [["a", 200, 300, "Problem"], ["b", 1000, 900, "Product"], ["c", 1800, 300, "Proof"]].forEach(([k, x, y, txt]) => {
          const d = document.createElement("div"); d.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:420px;height:300px;border-radius:30px;background:var(--mk-surface);border:3px solid var(--mk-line);display:flex;align-items:center;justify-content:center;font:900 70px var(--mk-display);text-transform:uppercase;opacity:0.33`; d.textContent = txt; world.appendChild(d); st[k] = d; });
        const cam = MK.camera(tl, world, { w: W, h: H });
        cam.set({ x: 0, y: 0, w: 2400, h: 1600 }, t);
        const sp = MK.spotlight(tl, st);
        sp.at(t + 0.2, ["a"]); cam.to({ x: 120, y: 200, w: 580, h: 500 }, t + 0.6, 0.9);
        sp.at(t + 1.6, ["b"], ["a"]); cam.to({ x: 920, y: 800, w: 580, h: 500 }, t + 1.6, cam.durationFor({ x: 920, y: 800, w: 580, h: 500 }));
        sp.at(t + 2.8, ["c"]); cam.to({ x: 0, y: 0, w: 2400, h: 1600 }, t + 2.8, 1.0); });

      // scene("s01", 0, 3.2, (s, t0) => {
      //   MKFX.headline(tl, s, t0 + 0.15, { x: 90, y: 360, w: 900, lines: ["one idea", "per beat"], size: 150, accentWord: "beat" });
      // });

