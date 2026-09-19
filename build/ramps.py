"""Every hue in the guarded arc, and the tonal ramp each one gives (AUTHORITY.md §1, §2).

x is hue across the guarded arc; y is lightness. The kit's palette is one vertical slice of
this field: one hue, two chroma levels, lightness doing all the remaining work. Drawn this way
you can see what the kit would have looked like at any other hue the guard admits, and where
the gamut runs out.

The guard is the one implied by the settled home hue: 351 sits 31.4 deg clear of destructive,
and the same 31.4 applied to info-blue's upper edge puts the arc's low end at 295.4. So the
home hue is the arc's UPPER EDGE, not its centre -- a consequence of deriving the guard from
where the palette already sits.

    python3 build/ramps.py
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
N, C_, M = PAL['neutrals'], PAL['chrome'], PAL['measurements']
CAST, CHROME = PAL['chosen']['cast_chroma'], PAL['chosen']['chrome_chroma']
HOME = PAL['chosen']['home_hue']

HI = HOME
GUARD = (P.ARCS['destructive'][0] - HOME) % 360
LO = (P.ARCS['info-blue'][1] + GUARD) % 360
SPAN = (HI - LO) % 360

L_TOP, L_BOT = 0.97, 0.10
GROUND, INK, MUTED = N['WHITE'], N['BLACK'], N['DARK']
OOG = '#CFC6CB'                                   # outside sRGB at this hue and chroma
UI, MONO = "Nimbus Sans, Helvetica, Arial, sans-serif", "Hack, DejaVu Sans Mono, monospace"

W, H = 1240, 1000
X0, PW = 150, 940
PANELS = [('chrome  chroma %.3f' % CHROME, CHROME, 150, 250,
           [('ACCENT', C_['ACCENT']), ('SELECT', C_['SELECT']), ('CURSOR', C_['CURSOR'])]),
          ('neutrals  chroma %.3f' % CAST, CAST, 470, 250,
           [('WHITE', N['WHITE']), ('LIGHT', N['LIGHT']), ('DARK', N['DARK']), ('BLACK', N['BLACK'])])]
o = [f'<rect width="{W}" height="{H}" fill="{GROUND}"/>']


def txt(x, y, s, fill=INK, size=12, bold=False, mono=False, anchor='start', halo=False):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;')
    hl = f' stroke="{GROUND}" stroke-width="3" style="paint-order:stroke fill"' if halo else ''
    o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO if mono else UI}" font-size="{size}"'
             f'{" font-weight=\"bold\"" if bold else ""} fill="{fill}" text-anchor="{anchor}"{hl}>{s}</text>')


def hx(h):
    return X0 + PW * ((h - LO) % 360) / SPAN


txt(40, 48, 'Every hue the guard admits, and the ramp it gives', INK, 24, True)
txt(40, 74, f'x is hue across the guarded arc {LO:.1f}–{HI:.1f}° ({SPAN:.1f}°, guard {GUARD:.1f}° at each end). y is lightness.', MUTED, 13)
txt(40, 93, 'The palette is one vertical slice: one hue, two chroma levels, lightness doing the rest. Grey means outside sRGB.', MUTED, 13)

for title, chroma, PY_, PH, marks in PANELS:
    txt(X0, PY_ - 12, title, INK, 14, True, mono=True)
    STEP = 2
    for px in range(0, PW, STEP):
        h = (LO + SPAN * px / PW) % 360
        for py in range(0, PH, STEP):
            L = L_TOP - (L_TOP - L_BOT) * py / PH
            v = ok.from_lch(L, chroma, h)
            o.append(f'<rect x="{X0+px}" y="{PY_+py}" width="{STEP}" height="{STEP}" '
                     f'fill="{ok.hexs(v) if ok.in_gamut(v) else OOG}"/>')
    o.append(f'<rect x="{X0}" y="{PY_}" width="{PW}" height="{PH}" fill="none" stroke="{INK}" stroke-width="1.5"/>')

    def ly(L):
        return PY_ + PH * (L_TOP - L) / (L_TOP - L_BOT)

    placed = []                                    # stagger labels that would collide
    for role, v in marks:
        L = ok.lch(v)[0]; y = ly(L)
        off = 0
        while any(abs((y + off) - q) < 22 for q in placed):
            off += 22
        placed.append(y + off)
        o.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X0+PW}" y2="{y:.1f}" stroke="{INK}" '
                 f'stroke-width="1.6" stroke-dasharray="6 4" opacity="0.75"/>')
        txt(X0 - 12, y + off + 4, role, INK, 11, True, mono=True, anchor='end')
        txt(X0 - 12, y + off + 16, f'L {L:.2f}', MUTED, 9, mono=True, anchor='end')
        if off:
            o.append(f'<line x1="{X0-10}" y1="{y+off:.1f}" x2="{X0}" y2="{y:.1f}" '
                     f'stroke="{MUTED}" stroke-width="0.8"/>')
        o.append(f'<rect x="{hx(HOME)-9:.1f}" y="{y-9:.1f}" width="18" height="18" fill="{v}" '
                 f'stroke="{INK}" stroke-width="2"/>')
    for i in range(0, int(SPAN) + 1, 5):           # hue axis
        x = hx((LO + i) % 360)
        o.append(f'<line x1="{x:.1f}" y1="{PY_+PH}" x2="{x:.1f}" y2="{PY_+PH+6}" stroke="{MUTED}" stroke-width="1"/>')
        txt(x, PY_ + PH + 19, f'{(LO+i)%360:.0f}°', MUTED, 9, mono=True, anchor='middle')
    x = hx(HOME)
    o.append(f'<line x1="{x:.1f}" y1="{PY_-6}" x2="{x:.1f}" y2="{PY_+PH}" stroke="{INK}" stroke-width="2.5"/>')
    txt(x, PY_ - 12, f'the palette, {HOME}°', INK, 11, True, anchor='end', halo=True)

# --- discrete ramps: the actual swatches at sampled hues ------------------------------------
RY = 800
txt(40, RY - 16, 'The same thing as swatches: the kit’s four neutral steps and three chrome steps, at six hues across the arc', INK, 14, True)
SAMPLE = [LO + SPAN * i / 5 for i in range(6)]
CW, GAP = 132, 20
for i, h in enumerate(SAMPLE):
    x = 150 + i * (CW + GAP)
    is_home = abs(((h - HOME + 180) % 360) - 180) < 0.6
    txt(x + CW / 2, RY + 4, f'{h % 360:.1f}°', INK, 12, True, mono=True, anchor='middle')
    if is_home:
        txt(x + CW / 2, RY + 18, 'the palette', INK, 10, True, anchor='middle')
    for j, (role, chroma, Lv) in enumerate(
            [('WHITE', CAST, ok.lch(N['WHITE'])[0]), ('LIGHT', CAST, ok.lch(N['LIGHT'])[0]),
             ('DARK', CAST, ok.lch(N['DARK'])[0]), ('BLACK', CAST, ok.lch(N['BLACK'])[0]),
             ('ACCENT', CHROME, ok.lch(C_['ACCENT'])[0]), ('SELECT', CHROME, ok.lch(C_['SELECT'])[0]),
             ('CURSOR', CHROME, ok.lch(C_['CURSOR'])[0])]):
        v = ok.from_lch(Lv, chroma, h)
        y = RY + 26 + j * 22
        o.append(f'<rect x="{x}" y="{y}" width="{CW}" height="20" '
                 f'fill="{ok.hexs(v) if ok.in_gamut(v) else OOG}" stroke="{INK}" stroke-width="{2 if is_home else 0.6}"/>')
        if i == 0:
            txt(x - 10, y + 14, role, INK, 10, True, mono=True, anchor='end')
        txt(x + 5, y + 14, ok.hexs(v) if ok.in_gamut(v) else 'out of gamut',
            N['WHITE'] if Lv < 0.55 else N['BLACK'], 9, mono=True)

open(os.path.join(ROOT, 'arc_ramps.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + ''.join(o) + '</svg>')
print(f"guarded arc {LO:.1f} - {HI:.1f}  ({SPAN:.1f} deg, guard {GUARD:.1f})")
print(f"home hue {HOME} sits at the UPPER EDGE of its own guarded arc\n")
print(f"{'hue':>7}  " + '  '.join(f'{r:>9}' for r in ('WHITE', 'LIGHT', 'DARK', 'BLACK', 'ACCENT', 'SELECT', 'CURSOR')))
for h in SAMPLE:
    cells = []
    for role, chroma in (('WHITE', CAST), ('LIGHT', CAST), ('DARK', CAST), ('BLACK', CAST),
                         ('ACCENT', CHROME), ('SELECT', CHROME), ('CURSOR', CHROME)):
        Lv = ok.lch({**N, **C_}[role])[0]
        v = ok.from_lch(Lv, chroma, h % 360)
        cells.append(f"{(ok.hexs(v) if ok.in_gamut(v) else '   --   '):>9}")
    print(f"{h%360:7.1f}  " + '  '.join(cells))
print("\nwrote arc_ramps.svg")


# --- standalone swatch table, at a size you can actually read -------------------------------
def table(path=None, cols=6):
    """The same sampling as the figure above, big enough to compare values by eye."""
    roles = [('WHITE', CAST), ('LIGHT', CAST), ('DARK', CAST), ('BLACK', CAST),
             ('ACCENT', CHROME), ('SELECT', CHROME), ('CURSOR', CHROME)]
    hues = [(LO + SPAN * i / (cols - 1)) % 360 for i in range(cols)]
    LBLW, CW, RH_, HDR, SPLIT = 168, 170, 56, 172, 30   # SPLIT: air between the two groups
    Wt = LBLW + cols * CW + 40
    Ht = HDR + len(roles) * RH_ + SPLIT + 96
    g = [f'<rect width="{Wt}" height="{Ht}" fill="{GROUND}"/>']

    def t(x, y, s, fill=INK, size=12, bold=False, mono=False, anchor='start'):
        s = str(s).replace('&', '&amp;').replace('<', '&lt;')
        g.append(f'<text x="{x:.0f}" y="{y:.0f}" font-family="{MONO if mono else UI}" font-size="{size}"'
                 f'{" font-weight=\"bold\"" if bold else ""} fill="{fill}" text-anchor="{anchor}">{s}</text>')

    t(30, 46, 'The palette at six hues across the guarded arc', INK, 22, True)
    t(30, 72, f'Every column is a complete palette. Only the hue differs; every lightness and both chroma levels are held.', MUTED, 12)
    t(30, 90, f'Guarded arc {LO:.1f}–{HI:.1f}°. The kit authors the last column.', MUTED, 12)

    for i, h in enumerate(hues):
        x = LBLW + i * CW
        home = abs(((h - HOME + 180) % 360) - 180) < 0.6
        t(x + CW / 2 - 4, HDR - 34, f'{h:.1f}°', INK, 15, True, mono=True, anchor='middle')
        if home:
            t(x + CW / 2 - 4, HDR - 16, 'the palette', INK, 11, True, anchor='middle')
        for j, (role, chroma) in enumerate(roles):
            Lv = ok.lch({**N, **C_}[role])[0]
            v = ok.from_lch(Lv, chroma, h)
            good = ok.in_gamut(v)
            y = HDR + j * RH_ + (SPLIT if j >= 4 else 0)
            g.append(f'<rect x="{x}" y="{y}" width="{CW-8}" height="{RH_-8}" '
                     f'fill="{ok.hexs(v) if good else OOG}" stroke="{INK}" '
                     f'stroke-width="{2.5 if home else 0.7}"/>')
            fg = N['WHITE'] if Lv < 0.55 else N['BLACK']
            t(x + 12, y + 30, ok.hexs(v) if good else 'out of gamut', fg, 14, True, mono=True)
    for j, (role, chroma) in enumerate(roles):
        Lv = ok.lch({**N, **C_}[role])[0]
        y = HDR + j * RH_ + (SPLIT if j >= 4 else 0)
        t(LBLW - 16, y + 26, role, INK, 14, True, mono=True, anchor='end')
        t(LBLW - 16, y + 41, f'L {Lv:.2f}  C {chroma:.3f}', MUTED, 10, mono=True, anchor='end')
        if j == 4:
            g.append(f'<line x1="18" y1="{y-6}" x2="{Wt-22}" y2="{y-6}" stroke="{INK}" '
                     f'stroke-width="1" stroke-dasharray="5 4" opacity="0.6"/>')
            t(18, y - 12, 'chrome — hue-bearing, must clear every pole', MUTED, 10)
            t(18, HDR - 12, 'neutrals — below C_FLOOR, a cast rather than a hue', MUTED, 10)
    yb = HDR + len(roles) * RH_ + SPLIT
    t(30, yb + 26, 'ACCENT and CURSOR read nearly the same in every column: same chroma, same ground, near-identical thresholds.', MUTED, 12)
    t(30, yb + 44, 'The neutral rows barely move across 55 degrees of hue — at chroma 0.020 the cast is almost hue-independent.', MUTED, 12)
    path = path or os.path.join(ROOT, 'arc_swatches.svg')
    open(path, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wt}" height="{Ht}" '
                          f'viewBox="0 0 {Wt} {Ht}">' + ''.join(g) + '</svg>')
    return path


if '--table' in sys.argv or True:
    print('wrote', table())
