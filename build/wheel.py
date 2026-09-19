"""The palette and the poles it avoids, on the OKLCh hue wheel (AUTHORITY.md §1, §2).

Angle is hue, radius is chroma. Drawn this way the rule is the picture: a color is clear of
the poles if it sits INSIDE the C_FLOOR disc (it carries a cast, not a hue) or INSIDE the one
wedge no signal claims. Everything else is a pole.

De Stijl's three chrome hues are plotted too, as hollow markers, because the fork's argument
(§0b) is that they land in the claimed wedges. SVG, so it needs nothing installed.

    python3 build/wheel.py [out.svg]
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
NEU, CHR, MEAS = PAL['neutrals'], PAL['chrome'], PAL['measurements']
DESTIJL = [('blue #1B3A6D', '#1B3A6D'), ('yellow #DFCC82', '#DFCC82'), ('red #D64D24', '#D64D24')]

W, H = 1240, 1210
CX, CY, RAD = 400, 452, 300
CMAX = 0.32
RFLOOR = RAD * P.C_FLOOR / CMAX
UI = "Montserrat, Nimbus Sans, Helvetica, Arial, sans-serif"
MONO = "Hack, DejaVu Sans Mono, monospace"
GROUND, INK, MUTED = PAL['neutrals']['WHITE'], PAL['neutrals']['BLACK'], PAL['neutrals']['DARK']
o = []


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')


def txt(x, y, s, fill=INK, size=13, bold=False, mono=False, anchor='start', op=1.0, halo=False):
    h = (f' stroke="{GROUND}" stroke-width="3.5" style="paint-order:stroke fill"' if halo else '')
    o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO if mono else UI}" '
             f'font-size="{size}"{" font-weight=\"bold\"" if bold else ""} fill="{fill}" '
             f'text-anchor="{anchor}"{h}{f" opacity=\"{op}\"" if op < 1 else ""}>{esc(s)}</text>')


def pt(h, r):
    """Hue h degrees, radius r -> SVG point. y is flipped so hue runs counterclockwise."""
    a = math.radians(h)
    return CX + r * math.cos(a), CY - r * math.sin(a)


def wedge(h1, h2, r0, r1, fill, op=1.0, stroke='none', sw=0):
    """Annulus sector from hue h1 to h2 (counterclockwise), radius r0..r1."""
    span = (h2 - h1) % 360
    big = 1 if span > 180 else 0
    ax, ay = pt(h1, r0); bx, by = pt(h1, r1); cx_, cy_ = pt(h2, r1); dx, dy = pt(h2, r0)
    o.append(f'<path d="M {ax:.1f},{ay:.1f} L {bx:.1f},{by:.1f} '
             f'A {r1:.1f},{r1:.1f} 0 {big} 0 {cx_:.1f},{cy_:.1f} L {dx:.1f},{dy:.1f} '
             f'A {r0:.1f},{r0:.1f} 0 {big} 1 {ax:.1f},{ay:.1f} Z" fill="{fill}"'
             f'{f" opacity=\"{op}\"" if op < 1 else ""}'
             f'{f" stroke=\"{stroke}\" stroke-width=\"{sw}\"" if sw else ""}/>')


def repr_color(h, L=0.55):
    """The most chromatic in-gamut color at hue h, for labelling a pole family."""
    for C in np.arange(0.30, 0.02, -0.005):
        v = ok.from_lch(L, float(C), h)
        if ok.in_gamut(v):
            return ok.hexs(v)
    return MUTED


o.append(f'<rect width="{W}" height="{H}" fill="{GROUND}"/>')
txt(40, 52, 'Remainder: the palette and the poles it avoids', INK, 25, True)
txt(40, 78, 'OKLCh hue wheel. Angle is hue, radius is chroma. A color is clear of the poles if it sits inside the', MUTED, 14)
txt(40, 97, 'C_FLOOR disc — a cast, not a hue — or inside the one wedge no signal has claimed.', MUTED, 14)

# --- pole wedges, from the floor outward: below the floor nothing is a pole ----------------
o.append(f'<circle cx="{CX}" cy="{CY}" r="{RAD}" fill="{GROUND}" stroke="{MUTED}" stroke-width="1" opacity="0.35"/>')
for fam, (lo, hi) in P.ARCS.items():
    mid = (lo + ((hi - lo) % 360) / 2) % 360
    wedge(lo, hi, RFLOOR, RAD, repr_color(mid), 0.92)
    lx, ly = pt(mid, RAD + 30)
    anc = 'middle' if 60 < mid < 120 or 240 < mid < 300 else ('start' if mid < 90 or mid > 270 else 'end')
    txt(lx, ly + 4, fam, INK, 14, True, anchor=anc)
    txt(lx, ly + 21, f'{lo:.0f}–{hi:.0f}°', MUTED, 12, mono=True, anchor=anc)

# --- guard bands: DELTA_MAX shaved off each end of the raw gap ----------------------------
o.append(f'<pattern id="gd" width="7" height="7" patternTransform="rotate(45)" '
         f'patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="7" '
         f'stroke="{MUTED}" stroke-width="2.5" opacity="0.45"/></pattern>')
RAW_LO, RAW_HI = P.ARCS['info-blue'][1], P.ARCS['destructive'][0]
wedge(RAW_LO, P.HOME[0], RFLOOR, RAD, 'url(#gd)')
wedge(P.HOME[1], RAW_HI, RFLOOR, RAD, 'url(#gd)')

# --- the home wedge -----------------------------------------------------------------------
wedge(P.HOME[0], P.HOME[1], RFLOOR, RAD, CHR['SELECT'], 0.22, INK, 2)
HOME_HUE = PAL['chosen']['home_hue']
hx, hy = pt(HOME_HUE, RAD + 62)
txt(hx, hy, 'the remainder', INK, 15, True, anchor='middle')
txt(hx, hy + 19, f'{P.HOME[0]:.1f}–{P.HOME[1]:.1f}°, home hue {HOME_HUE}°', MUTED, 12, mono=True, anchor='middle')
o.append(f'<line x1="{CX}" y1="{CY}" x2="{pt(HOME_HUE, RAD)[0]:.1f}" y2="{pt(HOME_HUE, RAD)[1]:.1f}" '
         f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.7"/>')

# --- the C_FLOOR disc ---------------------------------------------------------------------
o.append(f'<circle cx="{CX}" cy="{CY}" r="{RFLOOR:.1f}" fill="{GROUND}" stroke="{INK}" '
         f'stroke-width="1.5" stroke-dasharray="4 3"/>')

# --- the palette, plotted ------------------------------------------------------------------
# Every neutral shares one hue and one chroma; so does every chrome hue. On this wheel the
# whole palette is TWO points on a single radial line, and that is the design: one hue, two
# chroma levels, lightness doing all the remaining work.
def banded(h, C, colors, r=14):
    x, y = pt(h, RAD * C / CMAX)
    cid = 'c%d' % (abs(hash((h, C))) % 99999)
    o.append(f'<clipPath id="{cid}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}"/></clipPath>')
    bh = (2 * r) / len(colors)
    for i, cv in enumerate(colors):
        o.append(f'<rect x="{x-r:.1f}" y="{y-r+i*bh:.1f}" width="{2*r}" height="{bh:.2f}" '
                 f'fill="{cv}" clip-path="url(#{cid})"/>')
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="{INK}" stroke-width="2"/>')
    return x, y


def plot(hexv, label, hollow=False):
    m = ok.lch(hexv)
    r = min(RAD - 4, RAD * m[1] / CMAX)
    x, y = pt(m[2], r)
    if hollow:
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="none" stroke="{INK}" stroke-width="2.5"/>')
        o.append(f'<line x1="{x-5:.1f}" y1="{y-5:.1f}" x2="{x+5:.1f}" y2="{y+5:.1f}" stroke="{INK}" stroke-width="2"/>')
        o.append(f'<line x1="{x-5:.1f}" y1="{y+5:.1f}" x2="{x+5:.1f}" y2="{y-5:.1f}" stroke="{INK}" stroke-width="2"/>')
    else:
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{hexv}" stroke="{INK}" stroke-width="2"/>')
    return x, y


NEU_ORDER = ('WHITE', 'LIGHT', 'DARK', 'BLACK')
CHR_ORDER = ('SELECT', 'CURSOR', 'ACCENT')
nx, ny = banded(HOME_HUE, PAL['chosen']['cast_chroma'], [NEU[k] for k in NEU_ORDER])
cx2, cy2 = banded(HOME_HUE, PAL['chosen']['chrome_chroma'], [CHR[k] for k in CHR_ORDER])

txt(nx - 26, ny + 4, '4 neutrals', INK, 12, True, anchor='end', halo=True)
txt(cx2 + 26, cy2 + 5, '3 chrome hues', INK, 12, True, halo=True)
txt(CX, CY - RFLOOR + 18, f'C_FLOOR {P.C_FLOOR:.3f}', MUTED, 11, mono=True, anchor='middle', halo=True)
for lbl, v in DESTIJL:                         # label outward along the value's own hue
    m = ok.lch(v)
    x, y = plot(v, lbl, hollow=True)
    lxp, lyp = pt(m[2], RAD * m[1] / CMAX + 34)
    txt(lxp, lyp + 4, lbl, INK, 11, mono=True,
        anchor='end' if 90 < m[2] < 270 else 'start', halo=True)

# --- legend --------------------------------------------------------------------------------
LX, LY = 828, 150
txt(LX, LY, 'The bars, derived from the poles themselves', INK, 15, True)
for i, (k, v, why) in enumerate([
        ('C_FLOOR', f'{P.C_FLOOR:.3f}', 'chroma of the faintest realized pole'),
        ('DELTA_MAX', f'{P.DELTA_MAX:.0f}°', "poles' own nearest-neighbour gap"),
        ('C_REF', f'{P.C_REF:.3f}', "a signal's own median chroma"),
        ('home hue', f'{HOME_HUE}°', 'center of the widest unclaimed arc')]):
    txt(LX, LY + 26 + i * 34, k, INK, 13, True, mono=True)
    txt(LX + 96, LY + 26 + i * 34, v, INK, 13, mono=True)
    txt(LX, LY + 43 + i * 34, why, MUTED, 11)

txt(LX, LY + 180, 'Reading the wheel', INK, 15, True)
o.append(f'<circle cx="{LX+9}" cy="{LY+201}" r="9" fill="{CHR["ACCENT"]}" stroke="{INK}" stroke-width="2"/>')
txt(LX + 26, LY + 206, 'a Remainder value — clear of every pole', MUTED, 12)
o.append(f'<circle cx="{LX+9}" cy="{LY+230}" r="8" fill="none" stroke="{INK}" stroke-width="2.5"/>')
o.append(f'<line x1="{LX+4}" y1="{LY+225}" x2="{LX+14}" y2="{LY+235}" stroke="{INK}" stroke-width="2"/>')
o.append(f'<line x1="{LX+4}" y1="{LY+235}" x2="{LX+14}" y2="{LY+225}" stroke="{INK}" stroke-width="2"/>')
txt(LX + 26, LY + 235, 'a De Stijl chrome hue — lands in a pole (§0b)', MUTED, 12)
o.append(f'<rect x="{LX}" y="{LY+251}" width="18" height="14" fill="url(#gd)" stroke="{MUTED}" stroke-width="0.5"/>')
txt(LX + 26, LY + 263, f'guard band — DELTA_MAX shaved off each end', MUTED, 12)

# --- the lightness rail --------------------------------------------------------------------
# The wheel is hue and chroma, so #FFFFFF and #000000 both collapse to its center and it can
# say nothing about them. They are reserved by rule (AUTHORITY.md 3), and the ladder stops
# short of both. That is a lightness statement and it needs a lightness axis.
RX, RY, RW, RH = 846, 524, 46, 258
txt(RX, RY - 62, 'The lightness axis', INK, 15, True)
txt(RX, RY - 44, 'What the wheel cannot show: #FFFFFF and #000000 have no', MUTED, 11)
txt(RX, RY - 31, 'hue, so both collapse to its center. The ladder stops short', MUTED, 11)
txt(RX, RY - 18, 'of each, and the pole test now refuses them (\u00a73).', MUTED, 11)

for i in range(RH):                            # the home hue at cast chroma, L 1 -> 0
    Lv = 1.0 - i / RH
    v = ok.from_lch(Lv, PAL['chosen']['cast_chroma'], HOME_HUE)
    if not ok.in_gamut(v):
        v = ok.from_lch(Lv, 0.0, HOME_HUE)
    o.append(f'<rect x="{RX}" y="{RY+i}" width="{RW}" height="1.2" fill="{ok.hexs(v)}"/>')
o.append(f'<rect x="{RX}" y="{RY}" width="{RW}" height="{RH}" fill="none" stroke="{INK}" stroke-width="1.5"/>')


def rail_y(L):
    return RY + (1.0 - L) * RH


TX = RX + RW + 18
# the two reserved ends, hatched, each annotated in its own clear space
o.append(f'<rect x="{RX-7}" y="{RY-7}" width="{RW+14}" height="7" fill="url(#gd)" stroke="{INK}" stroke-width="1"/>')
o.append(f'<path d="M {TX-8},{RY+10} L {TX-16},{RY-2} L {RX+RW+6},{RY-4}" fill="none" '
         f'stroke="{MUTED}" stroke-width="1"/>')
txt(TX, RY + 14, '#FFFFFF  L 1.00', INK, 11, True, mono=True)
txt(TX, RY + 27, 'reserved: legend on a semantic field,', MUTED, 10)
txt(TX, RY + 39, 'and what an unstyled surface renders', MUTED, 10)
txt(TX, RY + 56, 'the ladder stops 0.07 below it, by', MUTED, 10)
txt(TX, RY + 68, 'choice: a field at #FFFFFF glares', MUTED, 10)

o.append(f'<rect x="{RX-7}" y="{RY+RH}" width="{RW+14}" height="7" fill="url(#gd)" stroke="{INK}" stroke-width="1"/>')
txt(TX, RY + RH + 2, '#000000  L 0.00', INK, 11, True, mono=True)
txt(TX, RY + RH + 15, 'reserved: legend on a semantic field', MUTED, 10)

for k in ('WHITE', 'LIGHT', 'DARK', 'BLACK'):
    Lv = ok.lch(NEU[k])[0]; yv = rail_y(Lv)
    o.append(f'<line x1="{RX-10}" y1="{yv:.1f}" x2="{RX+RW+8}" y2="{yv:.1f}" stroke="{INK}" stroke-width="2"/>')
    txt(RX - 14, yv + 4, k, INK, 11, True, mono=True, anchor='end')
    txt(RX - 14, yv + 16, f'L {Lv:.2f}', MUTED, 10, mono=True, anchor='end')

# --- pole strip -----------------------------------------------------------------------------
SY = 858
txt(40, SY, 'The poles: colors systems actually ship as signals', INK, 16, True)
txt(40, SY + 20, 'Each family is the hue arc its realized members span. poles.json records every member and its source.', MUTED, 12)
x = 40
for fam, d in P.POLES['families'].items():
    members = list(d['members'].items())
    txt(x, SY + 50, fam, INK, 13, True)
    txt(x, SY + 66, f'{P.ARCS[fam][0]:.1f}–{P.ARCS[fam][1]:.1f}°', MUTED, 11, mono=True)
    for j, (name, v) in enumerate(members):
        o.append(f'<rect x="{x + j*30}" y="{SY+76}" width="26" height="34" fill="{v}"/>')
    words, line, lines = d['means'].split(), '', []
    for w in words:
        if len(line + ' ' + w) > 24 and line:
            lines.append(line); line = w
        else:
            line = (line + ' ' + w).strip()
    lines.append(line)
    for li, ln in enumerate(lines[:2]):
        txt(x, SY + 126 + li * 13, ln, MUTED, 10)
    x += 197

# --- palette strip ---------------------------------------------------------------------------
PY_ = SY + 168
txt(40, PY_, 'The palette: every lightness solved, both chroma levels chosen (§0c)', INK, 16, True)
x = 40
for k in ('WHITE', 'LIGHT', 'DARK', 'BLACK', 'ACCENT', 'SELECT', 'CURSOR'):
    v = {**NEU, **CHR}[k]; m = MEAS[k]
    o.append(f'<rect x="{x}" y="{PY_+16}" width="118" height="44" fill="{v}" stroke="{INK}" stroke-width="1"/>')
    txt(x, PY_ + 76, k, INK, 12, True, mono=True)
    txt(x, PY_ + 91, v, MUTED, 11, mono=True)
    note = 'cast, no readable hue' if not m['readable'] else f"clears {m['clears']:.0f}°"
    txt(x, PY_ + 106, note, MUTED, 10)
    x += 134

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       + ''.join(o) + '</svg>')
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'poles_and_palette.svg')
open(out, 'w').write(svg); print('wrote', out)
