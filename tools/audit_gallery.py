import os
from PIL import Image, ImageStat
import math

# Higher score = more "real" content (more unique colors, higher variance).
# Lower score = flat / placeholder / broken.
def score(im):
    # RGB(A) -> RGB
    rgb = im.convert('RGB')
    # Count unique colors (downsample for speed)
    small = rgb.resize((128, 128))
    colors = small.getcolors(maxcolors=128*128) or []
    n_unique = len(colors)
    # Variance (stddev) of luminance
    stat = ImageStat.Stat(rgb.convert('L'))
    stddev = stat.stddev[0]
    # Combined score
    return n_unique, round(stddev, 1)

cats = ['build', 'electronics', 'simulations', 'booth']
results = []
for cat in cats:
    d = 'docs/gallery/' + cat
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        p = os.path.join(d, fn)
        size = os.path.getsize(p)
        try:
            im = Image.open(p)
            w, h = im.size
            fmt = im.format
            n_colors, stddev = score(im)
            # Flag if n_colors < 100 (probably blank) or stddev < 8 (probably flat)
            flag = ''
            if n_colors < 200: flag += 'LOW_COLORS '
            if stddev < 10: flag += 'FLAT '
            if size < 25000: flag += 'SMALL_FILE '
        except Exception as e:
            w, h, fmt, n_colors, stddev, flag = 0, 0, 'ERR', 0, 0, str(e)
        results.append((cat, fn, size, w, h, fmt, n_colors, stddev, flag.strip()))

print('%-12s %-32s %7s %6s %5s %-6s %-5s %s' % ('cat', 'file', 'size_kb', 'colors', 'stddev', 'fmt', 'WxH', 'flag'))
print('-' * 110)
for r in sorted(results, key=lambda x: (x[0], x[8] or 'zzz')):
    cat, fn, sz, w, h, fmt, nc, sd, fl = r
    skb = sz / 1024
    flag_str = '[!] ' + fl if fl else ''
    print('%-12s %-32s %7.1f %6d %6.1f %-6s %-5s %s' % (cat, fn, skb, nc, sd, fmt, '%dx%d' % (w, h), flag_str))
