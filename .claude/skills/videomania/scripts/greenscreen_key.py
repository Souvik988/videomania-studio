"""Clean-plate chroma keyer for green-screen talking-head footage (Video Mania).

Usage (1920x1080 input, camera locked off; a 60 fps source keeps every 2nd frame → 30 fps):
  greenscreen_key.py --src IN.mp4 --out key --preview 4 --room plate.jpg   # judge stills first
  greenscreen_key.py --src IN.mp4 --out key --range 0:930                  # one worker per range,
  greenscreen_key.py --src IN.mp4 --out key --range 930:1860               # ranges start on even
  …                                                                         # source frames
  then greenscreen_relight.py on each key/part_*.webm and concat (ffmpeg -f concat -c copy).
Built and tuned on the Shotlin promo (lime screen, shadows beside the chair, a white mic cable).

1. Build a clean plate of the empty screen: per-pixel median over frames
   where that pixel is confidently screen (the camera is locked off).
2. Per frame, alpha = 1 - k_frame / k_plate (Vlahos with a known plate,
   where k = g - max(r, b)), and pixels whose chromaticity matches the plate
   (screen in the presenter's cast shadow) are forced to screen.
3. Un-mix edge colours against the plate, so edges carry no green.

Writes presenter_rgb.mp4 + presenter_matte.mp4 at 30 fps (and an optional
VP9-alpha WebM). `--preview N` writes N test stills instead.
"""
import argparse, os, subprocess
import cv2
import numpy as np

SRC = None  # set from --src
W, H = 1920, 1080


def kval(f32):
    return f32[..., 1] - np.maximum(f32[..., 0], f32[..., 2])


def chroma(f32):
    return f32 / (f32.sum(-1, keepdims=True) + 1e-3)


def build_plate(path, samples=90):
    cap = cv2.VideoCapture(SRC)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stack, masks = [], []
    for j in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (j + 0.5) / samples))
        ok, f = cap.read()
        if not ok:
            continue
        f32 = f.astype(np.float32)
        k = kval(f32)
        sure = (k > 14) & (k / (f32[..., 1] + 8) > 0.14)
        sure = cv2.erode(sure.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
        stack.append(f)
        masks.append(sure)
    st = np.stack(stack).astype(np.float32)
    mk = np.stack(masks)
    st[~mk] = np.nan
    plate = np.nanmedian(st, axis=0)
    hole = np.isnan(plate[..., 0])
    plate = np.nan_to_num(plate).astype(np.uint8)
    plate = cv2.inpaint(plate, hole.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
    plate = cv2.GaussianBlur(plate, (0, 0), 3)
    cv2.imwrite(path, plate)
    return plate


def key(f, plate32, kp, cp):
    f32 = f.astype(np.float32)
    kf = kval(f32)
    # Vlahos against the plate.
    a_v = 1.0 - np.clip(kf / kp, 0, 1)
    # Screen in shadow: same chromaticity as the plate, darker or equal.
    dc = np.linalg.norm(chroma(f32) - cp, axis=-1)
    lum_f = f32.sum(-1); lum_p = plate32.sum(-1)
    s = lum_f / (lum_p + 1)
    shadow_bg = np.clip((0.035 - dc) / 0.015, 0, 1) * (s < 1.15) * (kf > 1)
    # Chroma-subsampled bleed: pixels next to an edge keep the plate's
    # brightness but lose its saturation. Close to the plate in RGB = screen.
    # Only trusted in a band around the edge (the plate is inpainted inside).
    dist = np.linalg.norm(f32 - plate32, axis=-1)
    a_d = np.clip((dist - 40.0) / 45.0, 0, 1)
    # Deep-shadow pockets the plate never saw: plainly green relative to brightness.
    kn = kf / (f32[..., 1] + 8.0)
    generic_bg = np.clip((kn - 0.12) / 0.06, 0, 1) * (kf > 3)
    base = a_v * (1 - shadow_bg) * (1 - generic_bg)
    core = cv2.erode((base > 0.5).astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
    alpha = np.where(core, 1.0, np.minimum(base, a_d))
    alpha = np.clip((alpha - 0.10) / 0.80, 0, 1)        # clip noise floor/ceiling

    # Islands and pinholes.
    hard = (alpha > 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(hard, 8)
    if n > 1:
        big = stats[1:, cv2.CC_STAT_AREA].argmax() + 1
        keep = (stats[:, cv2.CC_STAT_AREA] > 8000).astype(np.uint8)
        keep[0] = 0; keep[big] = 1
        fg = keep[lab]
    else:
        fg = hard
    inv = (1 - fg).astype(np.uint8)
    n2, lab2, stats2, _ = cv2.connectedComponentsWithStats(inv, 4)
    small = (stats2[:, cv2.CC_STAT_AREA] < 120).astype(np.uint8); small[0] = 0
    holes = small[lab2] * (dist > 40)          # never fill real screen slivers
    fg = np.maximum(fg, holes)
    near = cv2.dilate(fg, np.ones((5, 5), np.uint8)).astype(np.float32)
    alpha = np.maximum(alpha * near, holes.astype(np.float32))

    guide = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    alpha = cv2.ximgproc.guidedFilter(guide, alpha.astype(np.float32), 2, 4e-4)
    alpha = np.clip(alpha, 0, 1)
    # Drop thin detached slivers (1–3 px arcs that track the cap edge) and choke the fringe.
    solid = cv2.morphologyEx((alpha > 0.2).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    solid = cv2.dilate(solid, np.ones((3, 3), np.uint8)).astype(np.float32)
    alpha = np.clip((alpha * solid - 0.06) / 0.94, 0, 1) ** 1.25

    # Un-mix: F = (f - (1-a) P) / a where alpha is solid enough to trust; else despilled f.
    a3 = np.maximum(alpha, 0.35)[..., None]
    F = (f32 - (1 - a3) * plate32) / a3
    F = np.minimum(F, f32 * 1.15 + 10)                     # never brighter than the source edge
    F = np.where((alpha[..., None] > 0.97) | core[..., None] | (alpha[..., None] < 0.35), f32, F)
    F = np.clip(F, 0, 255)
    b, g, r = F[..., 0], F[..., 1], F[..., 2]
    # No green spill above max(r,b); no magenta from over-unmixing either.
    g = np.clip(g, 0.8 * np.minimum(r, b), np.maximum(r, b) + 4)
    F = np.stack([b, g, r], -1)
    return alpha.astype(np.float32), F.astype(np.uint8)


def ff(path, pix_in, extra):
    return subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", pix_in,
         "-s", f"{W}x{H}", "-r", "30", "-i", "-"] + extra + [path],
        stdin=subprocess.PIPE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="green-screen video")
    ap.add_argument("--room", default=None, help="background still for --preview composites")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", type=int, default=0)
    ap.add_argument("--webm", action="store_true")
    ap.add_argument("--range", default="", help="src frames a:b → <out>/part_a.webm only")
    a = ap.parse_args()
    global SRC
    SRC = a.src
    os.makedirs(a.out, exist_ok=True)

    pp = os.path.join(a.out, "plate.png")
    plate = cv2.imread(pp) if os.path.exists(pp) else build_plate(pp)
    plate32 = plate.astype(np.float32)
    kp = np.maximum(kval(plate32), 6.0)
    cp = chroma(plate32)

    if a.preview:
        cap = cv2.VideoCapture(SRC)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        room = cv2.imread(a.room) if a.room else np.full((H, W, 3), 30, np.uint8)
        room = cv2.resize(room, (W, H)).astype(np.float32)
        for j in range(a.preview):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (j + 0.5) / a.preview))
            ok, f = cap.read()
            al, rgb = key(f, plate32, kp, cp)
            for name, bgc in (("red", np.array([30, 60, 200], np.float32)), ("room", room)):
                comp = rgb * al[..., None] + bgc * (1 - al[..., None])
                cv2.imwrite(f"{a.out}/prev_{j}_{name}.jpg", comp.astype(np.uint8))
            cv2.imwrite(f"{a.out}/prev_{j}_matte.jpg", (al * 255).astype(np.uint8))
        return

    if a.range:
        s0, s1 = map(int, a.range.split(":"))
        wp = ff(f"{a.out}/part_{s0:05d}.webm", "bgra",
                ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "18", "-b:v", "0",
                 "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0"])
        cap = cv2.VideoCapture(SRC); cap.set(cv2.CAP_PROP_POS_FRAMES, s0)
        i, n = s0, 0
        while i < s1:
            ok, f = cap.read()
            if not ok:
                break
            if i % 2 == 0:
                al, rgb = key(f, plate32, kp, cp)
                wp.stdin.write(np.dstack([rgb, (al * 255 + 0.5).astype(np.uint8)]).tobytes()); n += 1
                if n % 100 == 0:
                    print("frames", n, flush=True)
            i += 1
        wp.stdin.close(); wp.wait(); print("done", n); return

    rgbp = ff(f"{a.out}/presenter_rgb.mp4", "bgr24",
              ["-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv444p"])
    mp = ff(f"{a.out}/presenter_matte.mp4", "gray",
            ["-c:v", "libx264", "-crf", "6", "-preset", "medium", "-pix_fmt", "yuv444p"])
    wp = ff(f"{a.out}/presenter.webm", "bgra",
            ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "18", "-b:v", "0",
             "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0"]) if a.webm else None
    cap = cv2.VideoCapture(SRC)
    i = n = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % 2 == 0:
            al, rgb = key(f, plate32, kp, cp)
            m8 = (al * 255 + 0.5).astype(np.uint8)
            rgbp.stdin.write(rgb.tobytes()); mp.stdin.write(m8.tobytes())
            if wp:
                wp.stdin.write(np.dstack([rgb, m8]).tobytes())
            n += 1
            if n % 150 == 0:
                print("frames", n, flush=True)
        i += 1
    for p in (rgbp, mp, wp):
        if p:
            p.stdin.close(); p.wait()
    print("done", n)


if __name__ == "__main__":
    main()
