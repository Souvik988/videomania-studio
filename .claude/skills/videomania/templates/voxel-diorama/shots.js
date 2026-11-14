// The shot list. This file is the whole film: the kit turns it into pictures. See README.md for every field.
// Times are seconds from the start of the film and come from the voiceover's word times.
window.SHOTS = {
  size: [1920, 1080], duration: 20,
  palette: { voice: "#e11d2e", voice2: "#ff6a1a", accent: "#19c8b9" },
  shots: [
    { id: "s1", t0: 0, t1: 3.2, set: "studio", cam: { preset: "wide-orbit" }, focus: "mani",
      cast: [{ who: "mani", at: "stage-left", pose: "idle" }, { who: "bit", at: "stage-right", pose: "idle" }],
      screen: { kind: "timeline" },
      type: { x: 0.06, y: 0.1, w: 0.5 },
      lines: [[["Every", 0.35], ["AI", 0.6], ["video", 0.8], ["\n"], ["looks", 1.15], ["the", 1.4]]],
      type3d: [{ text: "SAME.", t: 1.7, at: [12.5, 5.2, 13.5], size: 4.6, ry: 0.36, anim: "slam" }],
      out: "dots" },

    { id: "s2", t0: 3.2, t1: 5.8, set: "studio", cam: { preset: "hero-push", on: "mani" }, focus: "mani",
      cast: [{ who: "mani", at: "stage-left", pose: "talk" }],
      type: { x: 0.58, y: 0.3, w: 0.38 },
      lines: [[["It's", 3.5], ["not", 3.7], ["the", 3.9], ["\n"], ["MODEL.", 4.2, "punch"]]],
      out: "whip" },

    { id: "s3", t0: 5.8, t1: 8.6, set: "studio", cam: { preset: "dolly", on: "stage" }, focus: "mani",
      cast: [{ who: "mani", at: "stage-left", pose: "point" }, { who: "bit", at: "stage-right", pose: "happy" }],
      type: { x: 0.06, y: 0.08, w: 0.5 },
      lines: [[["It's", 6.05], ["the", 6.25], ["missing", 6.5, "accent"]]],
      type3d: [{ text: "CREW.", t: 6.95, at: [11, 10.6, 3], size: 5, ry: -0.12, anim: "swing" }],
      out: "pixelate" },

    { id: "s4", t0: 8.6, t1: 11.4, set: "city-night", cam: { preset: "dolly", on: "street" }, focus: "mani", lens: { aperture: 0.4 },
      cast: [{ who: "mani", at: "street-left", pose: "cheer" }, { who: "bit", at: "street-right", pose: "jump" }],
      type: { x: 0.06, y: 0.08, w: 0.5 },
      lines: [[["Depth,", 8.9], ["built", 9.15], ["in", 9.35], ["layers.", 9.6, "accent"]]],
      type3d: [{ text: "2.5D", t: 10.0, at: [9.5, 12.4, 0], size: 6, color: "#ff6a1a", anim: "rise" }],
      out: "whip" },

    { id: "s5", t0: 11.4, t1: 13.8, set: "studio", cam: { preset: "monitor-push" }, focus: "screen",
      screen: { kind: "code", lines: ["01 producer", "02 director", "03 storyboard", "04 art director", "05 animator", "06 editor", "07 sound", "08 critic", "09 teacher"] },
      type: { x: 0.05, y: 0.08, w: 0.4, size: 0.9 },
      lines: [[["9", 11.65, "num"], ["jobs.", 11.95]], [["One", 12.75], ["page", 12.95], ["each.", 13.15, "accent"]]],
      out: "mosaic" },

    { id: "s6", t0: 13.8, t1: 16.6, set: "void", cam: { preset: "void-centre", on: "bit" }, focus: "bit",
      cast: [{ who: "bit", at: "centre-right", pose: "jump" }],
      type: { x: 0.07, y: 0.16, w: 0.5 },
      lines: [[["47", 14.1, "num"], ["engines.", 14.45]], [["10876", 15.2, "num"], ["\n"], ["moves", 15.6], ["in", 15.75], ["its", 15.85], ["pocket.", 16.0, "accent"]]],
      out: "mosaic" },

    { id: "s7", t0: 16.6, t1: 20, set: "studio", cam: { preset: "two-shot", from: [-4, 6.6, 36], to: [-1.5, 6.2, 33], look: [1.5, 5.6, 8.5] }, focus: "mani",
      cast: [{ who: "mani", at: [-9, 0, 8], pose: "point", enter: "hop" }, { who: "bit", at: [-2.5, 0, 9.5], pose: "happy" }],
      props: [{ id: "skill", kind: "doc", at: [-15.5, 8.5, 4], t: 16.8, scale: 0.8 }],
      type: { x: 0.6, y: 0.14, w: 0.37 },
      lines: [[["Your", 16.9], ["idea.", 17.15, "accent"], ["\n"], ["Our", 17.7], ["\n"], ["CREW.", 18.0, "punch"], ["\n"], ["made with Video Mania", 18.7, "soft"]]],
      out: "cut" },
  ],
};
