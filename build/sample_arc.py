"""Walk the unclaimed arc and show what each guard would admit (AUTHORITY.md §1).

DELTA_MAX does two jobs: it sets the clearance a color must have from every pole, and it
sets the guard shaved off each end of the raw unclaimed gap to get the publishable home arc.
The second job is the weaker of the two -- DELTA_MAX is derived from how far apart two
adjacent SIGNALS sit, which is a discrimination threshold, and the guard needs an
identification boundary. Category boundaries are wider than the spread of shipped exemplars.

This samples the raw gap continuously so the question can be answered by looking: at which
hue does the color stop reading as blue, and at which does it start reading as red?

    python3 build/sample_arc.py            report + arc_guards.svg
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
NEU = PAL['neutrals']

LO, HI = P.ARCS['info-blue'][1], P.ARCS['destructive'][0]      # 264.1 -> 22.4
SPAN = (HI - LO) % 360
HOME_HUE = PAL['chosen']['home_hue']

# Candidate guards, all derived from the same pole set, differing only in which statistic of
# the adjacent-signal gaps is taken. The minimum is the current choice and the weakest: it is
# the one place two signals are packed tightest, so it is the least representative of how wide
# a color category actually runs.
_order = sorted(P.ARCS.items(), key=lambda kv: kv[1][0])
_gaps = sorted(g for g in [((_order[(i + 1) % len(_order)][1][0] - hi) % 360)
                           for i, (f, (lo, hi)) in enumerate(_order)] if g < 100)
GUARDS = [('minimum  (current)', float(np.ceil(min(_gaps)))),
          ('median', float(np.ceil(np.median(_gaps)))),
          ('maximum', float(np.ceil(max(_gaps))))]

# The three settings that matter: the kit's two chrome roles, and the worst case (a color as
# saturated as the signals themselves, where DELTA_REQ is at its maximum).
ROWS = [('ACCENT  L 0.42, C 0.100', 0.42, 0.100),
        ('SELECT  L 0.71, C 0.100', 0.71, 0.100),
        ('worst case  L 0.55, C 0.179', 0.55, 0.179)]


def at(L, C, h):
    """In-gamut color at (L, C, h), chroma reduced only as far as the gamut forces."""
    for c in np.arange(C, 0.0, -0.004):
        v = ok.from_lch(L, float(c), h)
        if ok.in_gamut(v):
            return ok.hexs(v), float(c)
    return ok.hexs(ok.from_lch(L, 0.0, h)), 0.0


print(f"raw unclaimed gap  {LO:.1f} -> {HI:.1f}   ({SPAN:.1f} deg)")
print(f"adjacent-signal gaps, sorted: {', '.join(f'{g:.1f}' for g in _gaps)}\n")
print(f"{'guard':22} {'shaved':>7}  {'home arc':>18} {'span':>7}   edge colors (L 0.55, C 0.100)")
for name, g in GUARDS:
    a, b = (LO + g) % 360, (HI - g) % 360
    ea, _ = at(0.55, 0.100, a); eb, _ = at(0.55, 0.100, b)
    print(f"{name:22} {g:6.0f}°  {a:7.1f} -> {b:5.1f} {(b-a)%360:6.1f}°   {ea}  {eb}")

print(f"\nthe palette sits at {HOME_HUE}°, the center of the raw gap — every guard keeps it.\n")
print(f"{'hue':>7}  {'ACCENT':>9} {'SELECT':>9} {'worst':>9}   clears   nearest pole")
for i in range(0, int(SPAN) + 1, 6):
    h = (LO + i) % 360
    cells = ' '.join(f'{at(L, C, h)[0]:>9}' for _, L, C in ROWS)
    hx, _ = at(0.55, 0.100, h)
    fam, gap, req = P.clearance(hx)
    mark = '  <- home hue' if abs(i - SPAN / 2) < 3 else ''
    print(f"{h:7.1f}  {cells}   {gap:5.1f}   {fam}{mark}")

# --- the figure -----------------------------------------------------------------------------
W, X0, SW = 1240, 140, 1040
RH, RGAP, Y0 = 62, 16, 150
H = Y0 + len(ROWS) * (RH + RGAP) + 190
GROUND, INK, MUTED = NEU['WHITE'], NEU['BLACK'], NEU['DARK']
UI, MONO = "Montserrat, Nimbus Sans, Helvetica, Arial, sans-serif", "Hack, DejaVu Sans Mono, monospace"
o = [f'<rect width="{W}" height="{H}" fill="{GROUND}"/>']


def txt(x, y, s, fill=INK, size=12, bold=False, mono=False, anchor='start', halo=False):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;')
    hl = f' stroke="{GROUND}" stroke-width="3" style="paint-order:stroke fill"' if halo else ''
    o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO if mono else UI}" font-size="{size}"'
             f'{" font-weight=\"bold\"" if bold else ""} fill="{fill}" text-anchor="{anchor}"{hl}>{s}</text>')


def hx_of(deg):
    return X0 + SW * deg / SPAN


txt(40, 46, 'What each guard admits', INK, 24, True)
txt(40, 72, f'The raw unclaimed gap, {LO:.1f}° to {HI:.1f}°, walked continuously. A guard shaves its width off each end;', MUTED, 13)
txt(40, 91, 'what remains is the publishable home arc. The question the numbers cannot answer: where does it stop reading as blue,', MUTED, 13)
txt(40, 110, 'and where does it start reading as red?', MUTED, 13)

for r, (label, L, C) in enumerate(ROWS):
    y = Y0 + r * (RH + RGAP)
    for px in range(SW):
        h = (LO + SPAN * px / SW) % 360
        o.append(f'<rect x="{X0+px}" y="{y}" width="1.4" height="{RH}" fill="{at(L, C, h)[0]}"/>')
    o.append(f'<rect x="{X0}" y="{y}" width="{SW}" height="{RH}" fill="none" stroke="{INK}" stroke-width="1"/>')
    txt(X0 - 10, y + RH / 2 + 4, label.split('  ')[0], INK, 12, True, mono=True, anchor='end')
    txt(X0 - 10, y + RH / 2 + 18, label.split('  ', 1)[1], MUTED, 10, mono=True, anchor='end')

BY = Y0 + len(ROWS) * (RH + RGAP)
for i in range(0, int(SPAN) + 1, 10):                          # hue axis
    x = hx_of(i)
    o.append(f'<line x1="{x:.1f}" y1="{BY-8}" x2="{x:.1f}" y2="{BY}" stroke="{MUTED}" stroke-width="1"/>')
    txt(x, BY + 13, f'{(LO+i)%360:.0f}°', MUTED, 10, mono=True, anchor='middle')

xh = hx_of((HOME_HUE - LO) % 360)                              # the palette's own hue
o.append(f'<line x1="{xh:.1f}" y1="{Y0-10}" x2="{xh:.1f}" y2="{BY}" stroke="{INK}" stroke-width="2.5" stroke-dasharray="6 4"/>')
txt(xh, Y0 - 18, f'the palette — home hue {HOME_HUE}°', INK, 12, True, anchor='middle', halo=True)

for gi, (name, g) in enumerate(GUARDS):                        # candidate guard boundaries
    yb = BY + 40 + gi * 40
    xa, xb = hx_of(g), hx_of(SPAN - g)
    o.append(f'<rect x="{X0}" y="{yb}" width="{xa-X0:.1f}" height="22" fill="url(#h{gi})" stroke="{MUTED}" stroke-width="0.8"/>')
    o.append(f'<rect x="{xb:.1f}" y="{yb}" width="{X0+SW-xb:.1f}" height="22" fill="url(#h{gi})" stroke="{MUTED}" stroke-width="0.8"/>')
    o.append(f'<rect x="{xa:.1f}" y="{yb}" width="{xb-xa:.1f}" height="22" fill="{PAL["chrome"]["SELECT"]}" opacity="0.3" stroke="{INK}" stroke-width="1.2"/>')
    o.append(f'<pattern id="h{gi}" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
             f'<line x1="0" y1="0" x2="0" y2="6" stroke="{MUTED}" stroke-width="2" opacity="0.5"/></pattern>')
    txt(X0 - 10, yb + 15, f'{name}', INK, 11, True, anchor='end')
    txt((xa + xb) / 2, yb + 15, f'{(SPAN-2*g):.0f}° arc  —  guard {g:.0f}°', INK, 11, True, mono=True, anchor='middle')

txt(40, H - 34, 'Hatched = shaved off by that guard. Tinted = what it publishes as authorable. Every guard keeps the palette;', MUTED, 12)
txt(40, H - 16, 'they differ only in how much of the arc they hand to whoever authors the next value.', MUTED, 12)

out = os.path.join(ROOT, 'arc_guards.svg')
open(out, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                     + ''.join(o) + '</svg>')
print(f"\nwrote {out}")
