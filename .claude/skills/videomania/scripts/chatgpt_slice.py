"""Slice a ChatGPT transparent sticker sheet into one trimmed PNG per object (reading order).
Usage: chatgpt_slice.py sheet.png OUTDIR name1,name2,...
"""
import sys, cv2, numpy as np
src, out, names = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
a = im[..., 3]
m = cv2.dilate((a > 12).astype(np.uint8), np.ones((15, 15), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
comps = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 4000]
rows = sorted(comps, key=lambda i: (round(cen[i][1] / (im.shape[0] / 2.2)), cen[i][0]))
for name, i in zip(names, rows):
    x, y, w, h = st[i, :4]; p = 6
    crop = im[max(0, y - p):y + h + p, max(0, x - p):x + w + p].copy()
    sub = (lab[max(0, y - p):y + h + p, max(0, x - p):x + w + p] == i)
    crop[..., 3] = np.where(sub, crop[..., 3], 0)
    cv2.imwrite(f"{out}/{name}.png", crop); print(name, w, h)
