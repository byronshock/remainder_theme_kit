"""Visual QA (AUTHORITY.md principle 9): the palette as a surface, not as swatches.

Renders a mock window using every authored value in the role it actually plays, so the
question "is this pleasant to look at for eight hours" can be asked of something that looks
like a screen. SVG, so it needs nothing installed and diffs as text.

    python3 build/qa.py [out.svg]
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = json.load(open(os.path.join(ROOT, 'palette.json')))
C = {**P['neutrals'], **P['chrome']}
M = P['measurements']
CLEARS = min(M[k]['clears'] for k in P['chrome'])          # never hardcode what the file knows


def legend(ground):
    """The text colour the palette pairs with this ground, read from its contrast targets.

    Hardcoding this is how the mock drifted: SELECT flipped from a pale ground carrying BLACK
    to a dark ground carrying WHITE, and the picture went on drawing BLACK on it -- dark text
    on a dark field, exactly what the palette had been re-derived to avoid. The renderer must
    not hold an opinion the palette does not.
    """
    for pair in P['contrast_targets']:
        txt, _, bg = pair.partition('_on_')
        if bg == ground:
            return C[txt]
    raise KeyError(f'no contrast target authored for text on {ground} -- '
                   f'the mock is about to invent one; add it to build/derive_palette.py')
SEM = [('SUCCESS', '#006B54', '#FFFFFF'), ('WARNING', '#FCD116', '#000000'),
       ('DESTRUCTIVE', '#AF1E2D', '#FFFFFF')]
UI = "Montserrat, Nimbus Sans, Helvetica, Arial, sans-serif"
MONO = "Hack, DejaVu Sans Mono, monospace"
W, H, RULE = 1000, 640, 14
o = []


def rect(x, y, w, h, fill):
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')


def text(x, y, s, fill, size=15, bold=False, mono=False):
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    o.append(f'<text x="{x}" y="{y}" font-family="{MONO if mono else UI}" font-size="{size}"'
             f'{" font-weight=\"bold\"" if bold else ""} fill="{fill}">{s}</text>')


rect(0, 0, W, H, C['DARK'])                                    # desktop
x0, y0, x1, y1 = RULE * 2, RULE * 2, W - RULE * 2, H - RULE * 2
rect(x0 - RULE, y0 - RULE, (x1 - x0) + RULE * 2, (y1 - y0) + RULE * 2, C['BLACK'])   # the rule
TB = 46
rect(x0, y0, x1 - x0, TB, C['ACCENT'])                         # key titlebar
text(x0 + 16, y0 + 29, 'Remainder — a palette chosen for what it is far from', legend('ACCENT'), 17, True)
rect(x0, y0 + TB, x1 - x0, y1 - y0 - TB, C['WHITE'])           # window field

SW = 250                                                       # sidebar
rect(x0, y0 + TB, SW, y1 - y0 - TB, C['LIGHT'])
for i, r in enumerate(['Overview', 'Poles', 'Palette', 'Surfaces', 'Residue']):
    ry = y0 + TB + 34 + i * 34
    sel = r == 'Palette'
    if sel:
        rect(x0, ry - 22, SW, 32, C['SELECT'])                 # selected row
    text(x0 + 20, ry, r, legend('SELECT') if sel else legend('LIGHT'), 16, bold=sel)

cx = x0 + SW + 30
text(cx, y0 + TB + 38, 'Every chrome value clears every pole.', legend('WHITE'), 19, True)
for i, ln in enumerate(['The hypothesis constrains hue only: at the home hue every',
                        f'chroma clears every signal by {CLEARS:.0f} degrees. Chroma and',
                        'lightness are aesthetic choices, each labelled as one.']):
    text(cx, y0 + TB + 70 + i * 24, ln, legend('WHITE'), 15)

my = y0 + TB + 168                                             # mono line + text cursor
text(cx, my, 'python3 build/poles.py --bars', legend('WHITE'), 15, mono=True)
rect(cx + 266, my - 15, 9, 21, C['CURSOR'])           # after the line, not inside it

bx, by = cx, my + 34                                           # buttons
for label, bg, fg in (('Derive', C['ACCENT'], C['WHITE']), ('Cancel', C['LIGHT'], C['BLACK']),
                      ('Delete', '#AF1E2D', '#FFFFFF')):
    rect(bx, by, 112, 38, bg); text(bx + 26, by + 25, label, fg, 15, True); bx += 130

sy = by + 78                                                   # the three signals
text(cx, sy, 'The only hues in the system that mean anything:', C['BLACK'], 14, True)
for i, (k, v, fg) in enumerate(SEM):
    b = cx + i * 200
    rect(b, sy + 16, 180, 40, v); text(b + 12, sy + 42, k, fg, 14, True)

ly = sy + 96                                                   # the authored values
for i, k in enumerate(('WHITE', 'LIGHT', 'DARK', 'BLACK', 'ACCENT', 'SELECT', 'CURSOR')):
    b = cx + i * 84
    rect(b, ly, 74, 40, C[k])
    o.append(f'<rect x="{b}" y="{ly}" width="74" height="40" fill="none" stroke="{C["BLACK"]}" '
             f'stroke-width="1" opacity="0.45"/>')          # WHITE is the field; it needs an edge
    text(b, ly + 56, k, C['BLACK'], 10, mono=True)
    text(b, ly + 70, C[k], C['DARK'], 10, mono=True)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}">' + ''.join(o) + '</svg>')
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'qa_surface.svg')
open(out, 'w').write(svg); print('wrote', out)
