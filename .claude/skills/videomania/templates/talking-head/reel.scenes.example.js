// Worked layouts for a talking-head reel (R1: coded character). REFERENCE, NOT A RUNNABLE FILM:
// it shows how MKTC (character) and MKS (graphics) are composed on one paused timeline in a
// scaffolded composition (new_composition.py loads mk/motion-kit.js, motion-shots.js, talking-character.js).
// Not rendered end to end yet: render a short draft and have the critic look before relying on it.
//
// Inputs you provide:
//   window.TALK   = the parsed talk.json   (scripts/viseme_track.py)
//   window.PARTS  = the parsed parts.json  (scripts/character_parts.py), or null for the vector stand-in
//   WORDS         = [{w, start, end}] measured word times from the voiceover transcript
//   media/char/   = the part PNGs
window.buildTalkingReel = function (tl, W, H, scene) {
  const stage = document.getElementById("scenes");
  const at = (word, lead = 0.2) => { const w = WORDS.find((x) => x.w.toLowerCase().startsWith(word)); return w ? w.start - lead : 0; };

  // one character for the whole film; the voice file starts at film time 0
  const cw = Math.round(W * (W > H ? 0.30 : 0.62));
  const ch = MKTC.rig(tl, stage, 0, { x: (W - cw) / 2, y: H * 0.34, w: cw, track: window.TALK, parts: window.PARTS, base: "media/char/", seed: 11 });

  // 1. BREAKOUT (0 to 5 s): alive on frame 0, hook word behind, kinetic line in the top zone
  scene("S1-hook", 0, 5, (s) => {
    MKTC.show(tl, ch, 0, 5);                                // pops in immediately; frame 0 already shows the rest pose
    MKS.slideUpText(tl, s, 0.15, { text: "NOBODY TELLS YOU", x: W / 2, y: H * 0.12, size: Math.round(W * 0.085), align: "center", color: "var(--mk-ink, #fff)" });
    MKS.headlineWall && MKS.headlineWall(tl, s, 0.4, { words: ["BILL", "KAUN", "BHARTA", "HAI"], y: H * 0.62, size: Math.round(W * 0.16) });
  });

  // 2. CORNER PRESENTER (5 to 14 s): character shrinks to a corner window, the frame explains
  scene("S2-explain", 5, 14, (s) => {
    tl.fromTo(ch.root, { scale: 1, x: 0, y: 0 }, { scale: 0.42, x: W * 0.28, y: H * 0.30, duration: 0.6, ease: "expo.inOut", immediateRender: false }, 5);
    MKS.chartGrid && MKS.chartGrid(tl, s, at("cost", 0.2), { x: W * 0.08, y: H * 0.18, w: W * 0.84, h: H * 0.40 });
    MKTC.look(tl, ch, at("cost", 0.35), { x: -0.9, y: 0.1 }, 1.1);   // glance at the incoming chart
  });

  // 3. CUT-AWAY (14 to 19 s): character leaves, voice continues over a full-frame graphic
  scene("S3-cutaway", 14, 19, (s) => {
    tl.fromTo(ch.root, { opacity: 1 }, { opacity: 0, duration: 0.25, ease: "power2.in", immediateRender: false }, 14);
    MKS.phoneMockup && MKS.phoneMockup(tl, s, 14.3, { x: W / 2, y: H * 0.5, src: "media/app.mp4" });
  });

  // 4. REACTION POP (19 to 24 s): back at full size on the punchline, with a surprise beat
  scene("S4-punch", 19, 24, (s) => {
    tl.fromTo(ch.root, { opacity: 0, scale: 1, x: 0, y: 0 }, { opacity: 1, scale: 1, x: 0, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, 19);
    MKTC.reaction(tl, ch, at("zero", 0.05), "surprise");
    MKS.slideUpText(tl, s, at("zero", 0.1), { text: "0", x: W / 2, y: H * 0.14, size: Math.round(W * 0.3), align: "center", color: "var(--mk-accent, #ffd45c)" });
  });
  return ch;
};
