"""The hue x chroma plane of the home region, with the named colors plotted (AUTHORITY.md §0c).

"Avoid magenta" is an aesthetic constraint, not a pole -- magenta signals nothing, so it has no
place in poles.json and belongs in the CHOSEN column with its reason stated. But it cannot be
answered with a hue angle alone, for two reasons this figure shows:

  1. "magenta" names two clusters ~25 deg apart -- the additive RGB primary near 328, and the
     process/ink family near 350-357. Naming one angle means picking which magenta you meant.
  2. magenta-ness needs chroma. Every named magenta sits above chroma 0.18; the kit's chrome
     is 0.100 and its neutrals 0.020. At those levels the same hues read as mauve and dusty
     rose. The neon palette an early derivation produced was a CHROMA failure (0.196-0.292),
     not a hue one.

    python3 build/field.py
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
NEU, CHO = PAL['neutrals'], PAL['chosen']
GROUND, INK, MUTED = NEU['WHITE'], NEU['BLACK'], NEU['DARK']
UI, MONO = "Montserrat, Nimbus Sans, Helvetica, Arial, sans-serif", "Hack, DejaVu Sans Mono, monospace"

H_LO, H_HI = 296.0, 26.0                       # the home end of the arc, through 360
H_SPAN = (H_HI - H_LO) % 360                   # 90 deg
C_HI = 0.34
L_AT = 0.60                                    # one lightness; the chroma story is the point

NAMED = [('#FF00FF', 'fuchsia / RGB primary', 'additive'),
         ('#DA70D6', 'orchid', 'additive'),
         ('#C71585', 'mediumvioletred', 'process'),
         ('#EC008C', 'process magenta', 'process'),
         ('#FF1493', 'deeppink', 'process')]
MARKS = [(323.2, 'current home hue', PAL['chrome']['ACCENT']),
         (352.0, 'proposed 352°', PAL['chrome']['CURSOR'])]

W, H = 1240, 760
X0, Y0, FW, FH = 150, 140, 940, 430
o = [f'<rect width="{W}" height="{H}" fill="{GROUND}"/>']


def txt(x, y, s, fill=INK, size=12, bold=False, mono=False, anchor='start', halo=False):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;')
    hl = f' stroke="{GROUND}" stroke-width="3" style="paint-order:stroke fill"' if halo else ''
    o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO if mono else UI}" font-size="{size}"'
             f'{" font-weight=\"bold\"" if bold else ""} fill="{fill}" text-anchor="{anchor}"{hl}>{s}</text>')


def fx(h):
    return X0 + FW * ((h - H_LO) % 360) / H_SPAN


def fy(C):
    return Y0 + FH * (1 - C / C_HI)


txt(40, 46, 'Where magenta is, and why an angle will not catch it', INK, 24, True)
txt(40, 72, f'The home end of the arc as a hue x chroma plane at L {L_AT:.2f}. Grey means the color is outside sRGB at that hue and chroma.', MUTED, 13)
txt(40, 91, 'Every named magenta sits above chroma 0.18. The kit authors at 0.100 and 0.020, marked. At those levels these hues are mauve.', MUTED, 13)

STEP = 2
for px in range(0, FW, STEP):                  # the field
    h = (H_LO + H_SPAN * px / FW) % 360
    for py in range(0, FH, STEP):
        C = C_HI * (1 - py / FH)
        v = ok.from_lch(L_AT, C, h)
        fill = ok.hexs(v) if ok.in_gamut(v) else '#D8D3DA'
        o.append(f'<rect x="{X0+px}" y="{Y0+py}" width="{STEP}" height="{STEP}" fill="{fill}"/>')
o.append(f'<rect x="{X0}" y="{Y0}" width="{FW}" height="{FH}" fill="none" stroke="{INK}" stroke-width="1.5"/>')

for i in range(0, int(H_SPAN) + 1, 10):        # hue axis
    x = fx((H_LO + i) % 360)
    o.append(f'<line x1="{x:.1f}" y1="{Y0+FH}" x2="{x:.1f}" y2="{Y0+FH+7}" stroke="{MUTED}" stroke-width="1"/>')
    txt(x, Y0 + FH + 21, f'{(H_LO+i)%360:.0f}°', MUTED, 10, mono=True, anchor='middle')
txt(X0 + FW / 2, Y0 + FH + 42, 'OKLCh hue', MUTED, 12, anchor='middle')

for C in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30):   # chroma axis
    y = fy(C)
    txt(X0 - 12, y + 4, f'{C:.2f}', MUTED, 10, mono=True, anchor='end')
o.append(f'<text x="{X0-64}" y="{Y0+FH/2}" font-family="{UI}" font-size="12" fill="{MUTED}" '
         f'text-anchor="middle" transform="rotate(-90 {X0-64} {Y0+FH/2})">chroma</text>')

# the two levels the kit actually authors at
for C, lab in ((CHO['chrome_chroma'], f"chrome  {CHO['chrome_chroma']:.3f}"),
               (CHO['cast_chroma'], f"neutrals  {CHO['cast_chroma']:.3f}")):
    y = fy(C)
    o.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X0+FW}" y2="{y:.1f}" stroke="{INK}" stroke-width="2.5"/>')
    txt(X0 + FW + 10, y + 4, lab, INK, 11, True, mono=True)

# the destructive pole, and its guard at the current DELTA_MAX
xp = fx(P.ARCS['destructive'][0])
o.append(f'<rect x="{xp:.1f}" y="{Y0}" width="{X0+FW-xp:.1f}" height="{FH}" fill="{INK}" opacity="0.30"/>')
txt(xp + 8, Y0 + 20, 'destructive pole', '#FFFFFF', 12, True)
txt(xp + 8, Y0 + 36, f'from {P.ARCS["destructive"][0]:.1f}°', '#FFFFFF', 10, mono=True)

for hue, lab, col in MARKS:                    # the two candidate home hues
    x = fx(hue)
    o.append(f'<line x1="{x:.1f}" y1="{Y0-14}" x2="{x:.1f}" y2="{Y0+FH}" stroke="{INK}" '
             f'stroke-width="2.5" stroke-dasharray="7 4"/>')
    txt(x, Y0 - 20, lab, INK, 12, True, anchor='middle', halo=True)

for hexv, name, grp in NAMED:                  # the named magentas
    L, C, h = ok.lch(hexv)
    x, y = fx(h), fy(C)
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{hexv}" stroke="{INK}" stroke-width="2"/>')
    txt(x + 15, y - 2, name, INK, 11, True, halo=True)
    txt(x + 15, y + 11, f'h {h:.1f}  C {C:.3f}', MUTED, 10, mono=True, halo=True)

# --- the gap between the two magenta clusters ----------------------------------------------
add = [ok.lch(v)[2] for v, _, g in NAMED if g == 'additive']
pro = [ok.lch(v)[2] for v, _, g in NAMED if g == 'process']
GAP_LO, GAP_HI = max(add), min(pro)
BY = Y0 + FH + 74
o.append(f'<rect x="{fx(GAP_LO):.1f}" y="{BY}" width="{fx(GAP_HI)-fx(GAP_LO):.1f}" height="26" '
         f'fill="{PAL["chrome"]["SELECT"]}" opacity="0.45" stroke="{INK}" stroke-width="1.2"/>')
txt((fx(GAP_LO) + fx(GAP_HI)) / 2, BY + 17, f'{(GAP_HI-GAP_LO):.1f}° between the clusters', INK, 11, True, anchor='middle')
txt(X0 - 12, BY + 17, 'if you must pick by angle:', INK, 11, True, anchor='end')
txt(X0, BY + 48, f'The only hue window clear of both magentas is {GAP_LO:.1f}–{GAP_HI:.1f}°, centered {((GAP_LO+GAP_HI)/2):.1f}° — and it is only '
                 f'{(GAP_HI-GAP_LO):.1f}° wide, so it buys about {((GAP_HI-GAP_LO)/2):.1f}° of margin either way.', MUTED, 12)
txt(X0, BY + 68, 'Holding chroma at 0.100 buys more: it puts every hue in this plane below every named magenta by a margin no angle here can match.', MUTED, 12)

open(os.path.join(ROOT, 'magenta_field.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + ''.join(o) + '</svg>')

print(f"additive cluster  {min(add):.1f}-{max(add):.1f} deg")
print(f"process cluster   {min(pro):.1f}-{max(pro):.1f} deg")
print(f"gap between them  {GAP_LO:.1f}-{GAP_HI:.1f} deg  ({GAP_HI-GAP_LO:.1f} wide), centered {((GAP_LO+GAP_HI)/2):.1f}\n")
print(f"{'hue':>7}  {'at C 0.020':>11} {'at C 0.100':>11} {'at C 0.179':>11} {'at C 0.32':>11}   clears destructive")
for h in (323.2, 328.4, 339.0, 349.7, 352.0, 356.9):
    cells = ''
    for C in (0.020, 0.100, 0.179, 0.32):
        v = ok.from_lch(L_AT, C, h)
        cells += f"{(ok.hexs(v) if ok.in_gamut(v) else '  (gamut)'):>12}"
    print(f"{h:7.1f} {cells}   {ok.arcgap(h, *P.ARCS['destructive']):5.1f}")
print("\nwrote magenta_field.svg")
