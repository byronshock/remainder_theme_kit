"""Visual QA (AUTHORITY.md principle 12): the palette as a surface, not as swatches.

Renders a mock window using every authored value in the role it actually plays, so the
question "is this pleasant to look at for eight hours" can be asked of something that looks
like a screen. SVG, so it needs nothing installed and diffs as text.

The sheet has to be true of the authority or it is worse than nothing -- it is the picture
someone checks the kit against. Three things it used to get wrong, all found by measuring it
against palette.json and §5 rather than by looking at it:

  THE DESKTOP FIELD IS BLACK, not DARK. §5 settled that: the tiling gaps ARE the rule, and at
  BLACK they are literally it -- the gap between two windows is the same value as the line the
  kit draws, dE 0.0, where a DARK field left the two dE 23.7 apart and made the claim true only
  by approximation. So there is no rule drawn around the window here. The surround is the rule.
  DARK keeps its own job in the picture, on the dock tiles §5 gives it.

  THE RULE IS 44. §5's reference width -- the 1 cm handle zone entire, since 2026-09-21; it was 22,
  half of it -- which the COSMIC theme spends as gaps (0, 44) and the all-sites sheet spends on hr.
  The sheet once drew 14.

  THE WEIGHT IS NOT DECORATION AND IS NOT DECLARED HERE EITHER. A ground whose authored floor
  is Lc 60 is APCA's 16px/700 tier and its text is 700; a ground authored at 75 or 90 is a body
  tier and its text is 400. That is read out of palette.json's contrast targets, so the picture
  cannot drift from the numbers the way it drifted before. The sheet used to draw an unselected
  panel row as BLACK on LIGHT at regular weight -- Lc 61.2 against a 400-weight floor of 75,
  which is the exact pair build/firefox.py fails a rule for.

    python3 build/qa.py [out.svg]
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = json.load(open(os.path.join(ROOT, 'palette.json')))
C = {**P['neutrals'], **P['chrome']}
M = P['measurements']
CLEARS = min(M[k]['clears'] for k in P['chrome'])          # never hardcode what the file knows
SEP = P['surface_separation']


def _target(ground):
    for pair, v in P['contrast_targets'].items():
        txt, _, bg = pair.partition('_on_')
        if bg == ground and txt in C and txt != 'CURSOR':
            return txt, v
    raise KeyError(f'no contrast target authored for text on {ground} -- '
                   f'the mock is about to invent one; add it to build/derive_palette.py')


def legend(ground):
    """The text colour the palette pairs with this ground, read from its contrast targets.

    Hardcoding this is how the mock drifted: SELECT flipped from a pale ground carrying BLACK
    to a dark ground carrying WHITE, and the picture went on drawing BLACK on it -- dark text
    on a dark field, exactly what the palette had been re-derived to avoid. The renderer must
    not hold an opinion the palette does not.
    """
    return C[_target(ground)[0]]


def weight(ground):
    """400 or 700, derived the same way and for the same reason.

    APCA's floor is a function of size and weight, so an authored floor of Lc 60 IS the
    16px/700 tier -- §2 says so in as many words for both grounds that carry it. Deriving the
    weight from the floor means the picture cannot show a lighter face than the number it was
    authored against, which is what it was doing on LIGHT.
    """
    return 700 if _target(ground)[1]['floor_lc'] <= 60 else 400


SEM = [('SUCCESS', '#006B54', '#FFFFFF'), ('WARNING', '#FCD116', '#000000'),
       ('DESTRUCTIVE', '#AF1E2D', '#FFFFFF')]
# §5 declares one UI face and one mono face. The fallback is generic on purpose: naming another
# kit's faces here would put a value in the picture this kit never chose.
UI = "Montserrat, sans-serif"
MONO = "Hack, monospace"
RULE = 44                                                  # §5's reference width
HINT = 11                                                  # §5: the key window's mark, CURSOR, a quarter of the rule
W, H = 1120, 772
o = []


def rect(x, y, w, h, fill, op=None):
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
             + (f' opacity="{op}"' if op else '') + '/>')


def text(x, y, s, fill, size=15, wt=400, mono=False):
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    o.append(f'<text x="{x}" y="{y}" font-family="{MONO if mono else UI}" font-size="{size}"'
             f' font-weight="{wt}" fill="{fill}">{s}</text>')


# --- the desktop (§5): a flat BLACK field, and the gap around the window IS the rule ----------
rect(0, 0, W, H, C['BLACK'])

DOCK = 78                                                  # §5: dock tiles stay DARK on the field
for i in range(4):
    rect(RULE, RULE + i * (DOCK + 10), DOCK, DOCK, C['DARK'])
text(RULE, H - RULE - 4, f"dock tiles DARK on the BLACK field — dE {SEP['BLACK_DARK']:.1f}   ·   "
     f"the key window's mark: CURSOR, {HINT} dp of the {RULE} dp rule (§5)",
     legend('DARK'), 11, weight('DARK'))

x0 = RULE * 2 + DOCK
y0, x1, y1 = RULE, W - RULE, H - RULE - 26
TB = 48
# §2, §5: the mock window is the key window, so it carries the mark -- CURSOR, HINT dp of the
# rule's width, drawn from the window's edge outward, the rest of the gap still BLACK.
rect(x0 - HINT, y0 - HINT, x1 - x0 + 2 * HINT, y1 - y0 + 2 * HINT, C['CURSOR'])
rect(x0, y0, x1 - x0, TB, C['ACCENT'])                     # key titlebar
text(x0 + 18, y0 + 31, 'Remainder — a palette chosen for what it is far from',
     legend('ACCENT'), 17, weight('ACCENT'))
rect(x0, y0 + TB, x1 - x0, y1 - y0 - TB, C['WHITE'])       # window field

# --- the panel, and a well on it: the kit's own separator, dE 17.1 ----------------------------
SW = 244
rect(x0, y0 + TB, SW, y1 - y0 - TB, C['LIGHT'])
wy = y0 + TB + 16
rect(x0 + 14, wy, SW - 28, 32, C['WHITE'])                 # a WHITE well on the LIGHT panel
text(x0 + 24, wy + 22, 'poles', legend('WHITE'), 14, weight('WHITE'))
rect(x0 + 24 + 40, wy + 8, 2, 18, C['CURSOR'])             # the caret, on the ground §2 measured it on
for i, r in enumerate(['Overview', 'Poles', 'Palette', 'Surfaces', 'Residue']):
    ry = wy + 62 + i * 34
    sel = r == 'Palette'
    if sel:
        rect(x0, ry - 22, SW, 32, C['SELECT'])
    text(x0 + 20, ry, r, legend('SELECT') if sel else legend('LIGHT'), 16,
         weight('SELECT') if sel else weight('LIGHT'))

cx = x0 + SW + 30
text(cx, y0 + TB + 40, 'Every chrome value clears every pole.', legend('WHITE'), 19, 700)
for i, ln in enumerate(['The hypothesis constrains hue only: at the home hue every',
                        f'chroma clears every signal by {CLEARS:.0f} degrees. Chroma and',
                        'lightness are aesthetic choices, each labelled as one.']):
    text(cx, y0 + TB + 72 + i * 24, ln, legend('WHITE'), 15, weight('WHITE'))

my = y0 + TB + 172
text(cx, my, 'python3 build/poles.py --bars', legend('WHITE'), 15, weight('WHITE'), mono=True)

bx, by = cx, my + 32                                       # buttons
for label, bg, fg, wt in (('Derive', C['ACCENT'], legend('ACCENT'), weight('ACCENT')),
                          ('Cancel', C['LIGHT'], legend('LIGHT'), weight('LIGHT')),
                          ('Delete', '#AF1E2D', '#FFFFFF', 700)):
    rect(bx, by, 112, 38, bg); text(bx + 26, by + 25, label, fg, 15, wt); bx += 130

sy = by + 74                                               # the three signals
text(cx, sy, 'The only hues in the system that mean anything:', C['BLACK'], 14, 700)
for i, (k, v, fg) in enumerate(SEM):
    b = cx + i * 200
    rect(b, sy + 16, 180, 40, v); text(b + 12, sy + 42, k, fg, 14, 700)

ly = sy + 100                                              # the authored values
for i, k in enumerate(('WHITE', 'LIGHT', 'DARK', 'BLACK', 'ACCENT', 'SELECT', 'CURSOR')):
    b = cx + i * 84
    rect(b, ly, 74, 40, C[k])
    o.append(f'<rect x="{b}" y="{ly}" width="74" height="40" fill="none" stroke="{C["BLACK"]}" '
             f'stroke-width="1" opacity="0.45"/>')          # WHITE is the field; it needs an edge
    # the sheet's own annotations sit on WHITE and take BLACK: Lc 91.8, the most the palette
    # offers on that ground. DARK would be 79.0, and a proof sheet is a poor place to spend
    # margin it is in the middle of claiming.
    text(b, ly + 56, k, C['BLACK'], 11, 400, mono=True)
    text(b, ly + 72, C[k], C['BLACK'], 11, 400, mono=True)

# --- the band (§2) -----------------------------------------------------------------------------
# The kit authors at 351.0 and RENDERS within a band around it. Hue is an angle taken from two small
# numbers, and at the cast's chroma rounding to 8 bits moves the angle by degrees. The sheet shows the
# four neutrals where they actually land, because a reader who checks one against the authority should
# find the spread here rather than think the palette has drifted.
hues = sorted((M[k]['hue'], k) for k in ('WHITE', 'LIGHT', 'DARK', 'BLACK'))
lo, hi = hues[0][0], hues[-1][0]
band_y = ly + 104
text(cx, band_y, f"authored at {P['chosen']['home_hue']:.1f}, rendered across "
                 f"{lo:.1f}-{hi:.1f} — {hi - lo:.1f} deg of 8-bit rounding, none of it authored",
     C['BLACK'], 11, 400, mono=True)
BW, BH = 520, 26
bx0 = cx
rect(bx0, band_y + 10, BW, BH, C['LIGHT'])
span = (hi - lo) or 1.0
# the authored hue first, as a full-height line, so the ticks read as sitting off it
hx = bx0 + int((P['chosen']['home_hue'] - lo) / span * (BW - 8)) + 4
rect(hx - 1, band_y + 4, 3, BH + 8, C['ACCENT'])
text(bx0 + BW + 12, band_y + 26, f"{P['chosen']['home_hue']:.1f} authored", C['ACCENT'], 11, 700)
# then where the four actually land. Labels alternate rows: WHITE and LIGHT are a tenth of a
# degree apart and their labels collided when they shared one.
for i, (hue, k) in enumerate(hues):
    px = bx0 + int((hue - lo) / span * (BW - 8)) + 4
    rect(px - 1, band_y + 10, 3, BH, C['BLACK'] if k == 'LIGHT' else C[k])
    text(px - 20, band_y + 10 + BH + 13 + (i % 2) * 13, f"{k[0]} {hue:.1f}", C['BLACK'], 9, 400, mono=True)

# --- what the picture is claiming, in the numbers it was drawn from ---------------------------
# Three short lines rather than one long one: the single line ran past the window's own right
# edge, which is a poor advertisement for a sheet about where surfaces end.
tw, _ = _target('WHITE'); tl, _ = _target('LIGHT')
for i, ln in enumerate((
        f"{tw} on WHITE  Lc {P['contrast_apca_lc'][tw + '_on_WHITE']:5.1f}  at {weight('WHITE')}",
        f"{tl} on LIGHT  Lc {P['contrast_apca_lc'][tl + '_on_LIGHT']:5.1f}  at {weight('LIGHT')}",
        f"WHITE / LIGHT  dE {SEP['WHITE_LIGHT']:5.1f}  the separator every boundary clears")):
    text(cx, ly + 186 + i * 16, ln, C['BLACK'], 11, 400, mono=True)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}">' + ''.join(o) + '</svg>')
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'qa_surface.svg')
open(out, 'w').write(svg); print('wrote', out)
