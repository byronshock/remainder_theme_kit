"""Floor versus margin: the open call on where the ground roles sit (AUTHORITY.md §0c).

Every APCA target is a FLOOR. A ground that clears it is legal; everything further from its
text is also legal. Nothing measured picks a point in that range, and the solver has been
picking it silently by taking the extreme -- which for a ground carrying text is the MINIMUM
contrast end. This renders both ends so the call can be made by looking.

Only three roles are actually in play:
    LIGHT   pinned -- lifting it collapses WHITE against LIGHT as surfaces (§3 separator)
    CURSOR  pinned -- sRGB has no darker teal at the chroma that keeps it hue-bearing
    DARK, ACCENT, SELECT   free

    python3 build/compare.py
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, apca

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
CH = PAL['chosen']
CAST, CHROME, HOME = CH['cast_chroma'], CH['chrome_chroma'], CH['home_hue']
CHUE, CCHR = CH['cursor_hue'], CH['cursor_chroma']
_L = np.arange(0.04, 0.995, 0.0005)


def ladder(C, hue):
    v = ok.from_lch_grid(_L, C, hue)
    k = np.all((v >= -0.5) & (v <= 255.5), axis=-1)
    return _L[k], [ok.hexs(x) for x in np.clip(np.round(v[k]), 0, 255)]


def solve(C, hue, other, min_lc, other_is_text, side):
    L, hexes = ladder(C, hue)
    got = np.array([abs(apca.lc(other, h)) if other_is_text else abs(apca.lc(h, other)) for h in hexes])
    Y = np.array([apca.screen_y(h) for h in hexes]); ref = apca.screen_y(other)
    good = np.where(got >= min_lc + 0.5)[0]
    pick = good[Y[good] < ref] if side == 'dark' else good[Y[good] >= ref]
    i = pick[np.argmax(Y[pick])] if side == 'dark' else pick[np.argmin(Y[pick])]
    return hexes[i]


def build(dark, accent, select):
    L, hexes = ladder(CAST, HOME)
    W = hexes[int(np.argmin(np.abs(L - 0.93)))]
    B = solve(CAST, HOME, W, 90, False, 'dark')
    return {'WHITE': W, 'BLACK': B,
            'LIGHT':  solve(CAST,  HOME, B, 60, True, 'light'),
            'DARK':   solve(CAST,  HOME, W, dark, True, 'dark'),
            'ACCENT': solve(CHROME, HOME, W, accent, True, 'dark'),
            'SELECT': solve(CHROME, HOME, W, select, True, 'dark'),
            'CURSOR': solve(CCHR, CHUE, W, 60, False, 'dark')}


A = build(75, 60, 75)              # at the floor -- what the solver picks today
B = build(88, 78, 87)              # with margin -- ACCENT returns to the wine
PAIRS = [('BLACK', 'WHITE', 90, 'body text on the field', False),
         ('BLACK', 'LIGHT', 60, 'panel + button text, bold', True),
         ('WHITE', 'DARK', 75, 'dock tile labels', False),
         ('WHITE', 'ACCENT', 60, 'titlebar text, bold', False),
         ('WHITE', 'SELECT', 75, 'selected row text', False),
         ('CURSOR', 'WHITE', 60, 'the cursor mark', True)]

GR, INK, MU = A['WHITE'], A['BLACK'], A['DARK']
UI, MONO = "Nimbus Sans, Helvetica, Arial, sans-serif", "Hack, DejaVu Sans Mono, monospace"
W_, H_ = 1340, 1180
o = [f'<rect width="{W_}" height="{H_}" fill="{GR}"/>']


def t(x, y, s, fill=INK, size=12, bold=False, mono=False, anchor='start'):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;')
    o.append(f'<text x="{x:.0f}" y="{y:.0f}" font-family="{MONO if mono else UI}" font-size="{size}"'
             f'{" font-weight=\"bold\"" if bold else ""} fill="{fill}" text-anchor="{anchor}">{s}</text>')


def rect(x, y, w, h, f, stroke=None, sw=1):
    o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{f}"'
             + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>')


t(40, 50, 'The open call: at the floor, or with margin?', INK, 24, True)
t(40, 78, 'Every APCA target is a floor. Both palettes clear every one. They differ only in how much room they keep above it,', MU, 13)
t(40, 97, 'and no measurement picks that — the solver has been choosing it for you by always taking the minimum legal value.', MU, 13)
t(40, 120, 'Only DARK, ACCENT and SELECT move. LIGHT and CURSOR are pinned by hard constraints and are identical in both.', INK, 13, True)


def window(x0, y0, pal, title, sub):
    WD, HT, TB, SW = 600, 350, 48, 156
    t(x0, y0 - 40, title, INK, 18, True)
    t(x0, y0 - 20, sub, MU, 12)
    rect(x0 - 10, y0 - 10, WD + 20, HT + 20, pal['BLACK'])
    rect(x0, y0, WD, TB, pal['ACCENT'])
    t(x0 + 16, y0 + 31, 'Remainder — a key window', pal['WHITE'], 16, True)
    rect(x0, y0 + TB, WD, HT - TB, pal['WHITE'])
    rect(x0, y0 + TB, SW, HT - TB, pal['LIGHT'])
    for i, r in enumerate(['Overview', 'Poles', 'Palette', 'Surfaces']):
        ry = y0 + TB + 32 + i * 31
        if r == 'Palette':
            rect(x0, ry - 20, SW, 29, pal['SELECT'])
            t(x0 + 16, ry, r, pal['WHITE'], 13, True)
        else:
            t(x0 + 16, ry, r, pal['BLACK'], 13, True)
    cx = x0 + SW + 24
    t(cx, y0 + TB + 32, 'Every chrome value clears every pole.', pal['BLACK'], 16, True)
    t(cx, y0 + TB + 58, 'Panel and button text is bold, so it needs Lc 60.', pal['BLACK'], 12)
    t(cx, y0 + TB + 76, 'Body text on the field needs Lc 90.', pal['BLACK'], 12)
    my = y0 + TB + 112
    t(cx, my, 'python3 build/poles.py', pal['BLACK'], 13, mono=True)
    rect(cx + 172, my - 12, 9, 17, pal['CURSOR'])
    by = my + 24
    for lbl, bg, fg in (('Derive', pal['ACCENT'], pal['WHITE']), ('Cancel', pal['LIGHT'], pal['BLACK']),
                        ('Delete', '#AF1E2D', '#FFFFFF')):
        rect(cx, by, 100, 34, bg); t(cx + 20, by + 23, lbl, fg, 13, True); cx += 114
    sx = x0 + SW + 24
    for i, k in enumerate(('WHITE', 'LIGHT', 'DARK', 'BLACK', 'ACCENT', 'SELECT', 'CURSOR')):
        bx = sx + i * 60
        rect(bx, y0 + HT - 70, 52, 32, pal[k], pal['BLACK'], 1)
        t(bx, y0 + HT - 24, pal[k], MU, 8, mono=True)


window(50, 200, A, 'A — at the floor', 'what the solver picks today: the minimum legal value everywhere')
window(700, 200, B, 'B — with margin', 'DARK, ACCENT and SELECT keep room; ACCENT returns to the wine')

Y0, BX, BW = 620, 320, 660
t(40, Y0, 'Every pair under both. The bar runs 0–100 Lc; the upright notch is the floor it must clear.', INK, 14, True)
for i, (tx, bg, floor, why, pinned) in enumerate(PAIRS):
    y = Y0 + 34 + i * 54
    la, lb = abs(apca.lc(A[tx], A[bg])), abs(apca.lc(B[tx], B[bg]))
    t(40, y + 16, f'{tx} on {bg}', INK, 12, True, mono=True)
    t(40, y + 31, f'{why}{"  · pinned" if pinned else ""}', MU, 10)
    rect(BX, y + 4, BW, 27, GR, MU, 0.8)
    rect(BX + 1, y + 5, (BW - 2) * la / 100, 12, A['ACCENT'])
    rect(BX + 1, y + 18, (BW - 2) * lb / 100, 12, B['ACCENT'])
    fx = BX + BW * floor / 100
    o.append(f'<line x1="{fx:.0f}" y1="{y}" x2="{fx:.0f}" y2="{y+35}" stroke="{INK}" stroke-width="2.5"/>')
    t(fx, y - 4, f'floor {floor}', INK, 10, True, mono=True, anchor='middle')
    t(BX + BW + 14, y + 15, f'A {la:5.1f}', MU, 11, mono=True)
    t(BX + BW + 14, y + 29, f'B {lb:5.1f}', MU, 11, mono=True)
    if pinned:
        t(BX + BW + 84, y + 22, 'identical', MU, 10)

yb = Y0 + 34 + len(PAIRS) * 54 + 22
t(40, yb, 'What you are choosing', INK, 15, True)
for i, line in enumerate([
    'A is the quietest the kit can be. Every surface sits exactly at the edge of legibility — maximally recessive chrome, which is',
    '   the aesthetic §2 states. It is also the least robust: a dim screen, a bright room, or an older eye eats the whole margin.',
    'B is more legible and more durable, at the cost of a chrome that asserts itself more. The titlebar returns to #763455.',
    'Neither is more correct. Both clear every floor. This is the aesthetic call, and whichever you take gets labelled as one.']):
    t(40, yb + 24 + i * 19, line, MU, 12)

open(os.path.join(ROOT, 'floor_vs_margin.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}">' + ''.join(o) + '</svg>')
print(f"{'role':8} {'A (floor)':>10} {'B (margin)':>11}   moves")
for k in ('WHITE', 'BLACK', 'LIGHT', 'DARK', 'ACCENT', 'SELECT', 'CURSOR'):
    print(f"  {k:7} {A[k]:>10} {B[k]:>11}   {'— pinned' if A[k] == B[k] else 'yes'}")
print()
for tx, bg, floor, why, pinned in PAIRS:
    print(f"  {tx:6} on {bg:6} floor {floor:3}   A {abs(apca.lc(A[tx],A[bg])):5.1f}   B {abs(apca.lc(B[tx],B[bg])):5.1f}")
print("\nwrote floor_vs_margin.svg")
