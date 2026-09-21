"""The Qt surface: derive its ladders, write the three scheme files, then check what is committed.
AUTHORITY.md is the authority.

Qt hands a theme a PALETTE -- twenty-one colour roles (twenty-two from Qt 6.6), in three groups (active,
inactive, disabled) -- and a widget STYLE paints every control from them. On Linux, outside Plasma, the
palette reaches a Qt application through a platform theme plugin, and the two that a user can install
and configure without elevation are qt5ct and qt6ct. Both read the same scheme file format, both
default to the Fusion style, and both were read off the installed build (qt5ct 1.5, qt6ct 0.9, on
Qt 5.15.13 and 6.4.2, COSMIC, 2026-09-21). Two things measured there shape this surface:

  FUSION DERIVES ITS CHROME FROM FOUR INPUTS. The style does not paint the palette; it paints values it
    computes from it, in Qt's own 16-bit HSV arithmetic (qcolor.cpp): every outline is Window darkened
    by 40%, a button face is Button lightened by up to (180 - grey)/6 percent and desaturated to three
    quarters, then drawn as a gradient from 124% to 102% of that, a tab page is the same value lightened
    4% more, a menu is Base lightened 8%, and so on -- twenty-odd derived values, none of them a value
    the theme set, and none the theme can prevent (qfusionstyle.cpp, identical in 5.15.13 and 6.4.2).
    So the checker here does what build/cosmic.py's README asks of a derived surface: it MODELS the
    derivation -- QColor's HSV round trips, integer factors, float32 rounding and the spec a colour is
    left in -- computes every value Fusion will paint from the committed palette, and measures each:
    clear of every pole, not reserved, and the text on it. The on-screen pass then checks the model
    against the pixels (README_QT.md).

    The Button input is chosen against that model, not against §2's table. Fed LIGHT, Fusion paints a
    face that carries BLACK at Lc 84 at its top and 63 at its bottom, and a tab page at Lc 66 -- under
    the 400-weight tier a label renders at, because this platform, like VS Code, sets no weight from a
    theme. Fed WHITE, the face clips to #FFFFFF, the reserved value (§3). Fed DARK, WHITE on the face
    reaches -70 at the top. Fed neutral_9, the COSMIC ladder's slot between LIGHT and WHITE, the face
    carries BLACK at 78 or better at every stop, the tab page at 84, the header rows at 78 -- and the
    top stop clips to a near-white the checker reports. Button is neutral_9, and --derive prints the
    four trials beside each other.

  ONE HIGHLIGHT. Qt 5 and Qt 6.4 have one role for what §2 splits into two: the selection (SELECT
    carrying WHITE) and focus (ACCENT). Highlight paints selected rows, selected text, the hovered menu
    item, the progress fill and the focus outline alike. The text-carrying uses decide it: Highlight is
    SELECT, WHITE on it Lc -87.5, and focus is a mark drawn in SELECT darkened by a quarter. From Qt 6.6
    a twenty-second role, Accent, takes what a style uses for toggles and checked marks; the qt6ct file
    carries it as ACCENT and qt6ct 0.9 accepts a 22-entry scheme on any Qt 6 (>= NColorRoles), while
    qt5ct 1.5 wants exactly 21, so the two targets are two files from one table.

The third file is a KDE colour scheme, because a Qt application that is a Flatpak on the KDE runtime
has no qt5ct inside its sandbox and reads ~/.config/kdeglobals instead (COSMIC grants every Flatpak
xdg-config/kdeglobals:ro for that reason), and because Plasma reads the same file. Same values, a third
notation -- decimal triples -- and the KDE style paints Button flat, so there the shortfall of BLACK on
LIGHT at 400 is recorded rather than moved (README_QT.md, the shape).

COSMIC exports a Qt palette of its own, derived from the COSMIC theme, when `apply_theme_global` is on
(Pop!_OS ships it on). Measured 2026-09-21 on this desktop: of its 21 active roles 4 are values the kit
authors; its Base is dE 7.3 from its Window, under the 17.1 surface floor; its HighlightedText reads at
Lc -51.8 on its Highlight where WHITE would give -78.5. `--installed` measures whatever the live config
points at, so that comparison runs on any machine. The daemon's own version marker is what lets the two
coexist: once `cosmic_qt_version=2` is in qt5ct.conf it only rewrites a scheme path that contains
"Cosmic" (libcosmic cosmic-theme/src/output/qt56ct_output.rs), so the kit's path survives every theme
change and mode switch -- PLATFORM.md carries the rest of that contract.

    python3 build/qt.py              check every value, pair, adjacency and derived value in the committed files
    python3 build/qt.py --derive     the role table, the ladders, Fusion's derivations, and the Button trials
    python3 build/qt.py --write      regenerate the three scheme files from the role table
    python3 build/qt.py --installed  the live machine: platform theme, plugins, the schemes in use, measured (a report)
"""
import glob, json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca, cosmic as C

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
QT = os.path.join(ROOT, 'worksafe', 'qt')
QT5_SCHEME = os.path.join(QT, 'qt5ct', 'colors', 'remainder.conf')
QT6_SCHEME = os.path.join(QT, 'qt6ct', 'colors', 'remainder.conf')
QT5_CONF = os.path.join(QT, 'qt5ct', 'qt5ct.conf')
QT6_CONF = os.path.join(QT, 'qt6ct', 'qt6ct.conf')
KDE_SCHEME = os.path.join(QT, 'kde', 'Remainder.colors')
INSTALLER = os.path.join(QT, 'install.sh')

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
N, CH = PAL['neutrals'], PAL['chrome']
WHITE, LIGHT, DARK, BLACK = N['WHITE'], N['LIGHT'], N['DARK'], N['BLACK']
ACCENT, SELECT, CURSOR = CH['ACCENT'], CH['SELECT'], CH['CURSOR']
SEMANTIC = dict(C.SEMANTIC)
FLOOR = PAL['surface_floor_dE']
NEUTRALS = {f'neutral_{i}': hx for i, hx, _ in C.neutrals()}
N9 = NEUTRALS['neutral_9']
# Mid is "between Button and Dark" (qpalette.h): the ladder slot nearest the midpoint of their lightness.
_slots = {i: hx for i, hx, _ in C.neutrals()}
_midL = (ok.lch(N9)[0] + ok.lch(DARK)[0]) / 2
MID = min((hx for i, hx in _slots.items() if 3 < i < 9), key=lambda hx: abs(ok.lch(hx)[0] - _midL))
MID_NAME = next(k for k, v in NEUTRALS.items() if v == MID)
MEASURED_ON = '2026-09-21'
MEASURED_FROM = 'qt5ct 1.5 / Qt 5.15.13 and qt6ct 0.9 / Qt 6.4.2, COSMIC'


# --- 1. QColor, as Qt computes it ---------------------------------------------------------------------
# Fusion's values come out of QColor::lighter/darker, setHsv/setHsl and toHsv/toRgb (qcolor.cpp, 6.4.2 and
# 5.15.13 alike): 16-bit components, hue in hundredths of a degree, float32 conversions, integer factors, and
# a colour that STAYS in whatever spec it was last set in -- lighter() on an HSV colour never touches RGB.
# Emulated here so the checker computes the bytes the style will paint rather than an approximation of them.
U = 65535
F = np.float32


def _qround(x):
    x = F(x)
    return int(x + F(0.5)) if x >= 0 else int(x - F(0.5))


def _div257(x):
    x += 128
    return (x - (x >> 8)) >> 8


def _fuzzy_null(f):
    return abs(F(f)) <= F(0.00001)


def _fuzzy_eq(a, b):
    return abs(F(a) - F(b)) * F(100000) <= min(abs(F(a)), abs(F(b)))


class Q:
    """A QColor: spec in {'rgb','hsv','hsl'} and three 16-bit components in that spec."""
    __slots__ = ('spec', 'c')

    def __init__(self, spec, c):
        self.spec, self.c = spec, tuple(int(v) for v in c)

    @classmethod
    def hex(cls, h):
        return cls('rgb', tuple(int(h[i:i + 2], 16) * 0x101 for i in (1, 3, 5)))

    # -- conversions -------------------------------------------------------------------------------------
    def to_rgb(self):
        if self.spec == 'rgb':
            return self
        if self.spec == 'hsv':
            h, s, v = self.c
            if s == 0 or h == U:
                return Q('rgb', (v, v, v))
            hf = F(0) if h == 36000 else F(h) / F(6000)
            s, v = F(s) / F(U), F(v) / F(U)
            i = int(hf)
            f = hf - F(i)
            p = v * (F(1) - s)
            if i & 1:
                q = v * (F(1) - s * f)
                r, g, b = {1: (q, v, p), 3: (p, q, v), 5: (v, p, q)}[i]
            else:
                t = v * (F(1) - s * (F(1) - f))
                r, g, b = {0: (v, t, p), 2: (p, v, t), 4: (t, p, v)}[i]
            return Q('rgb', (_qround(r * F(U)), _qround(g * F(U)), _qround(b * F(U))))
        h, s, l = self.c
        if s == 0 or h == U:
            return Q('rgb', (l, l, l))
        if l == 0:
            return Q('rgb', (0, 0, 0))
        hf = F(0) if h == 36000 else F(h) / F(36000)
        s, l = F(s) / F(U), F(l) / F(U)
        t2 = l * (F(1) + s) if l < F(0.5) else l + s - l * s
        t1 = F(2) * l - t2
        out = []
        for t3 in (hf + F(1) / F(3), hf, hf - F(1) / F(3)):
            if t3 < 0:
                t3 += F(1)
            elif t3 > 1:
                t3 -= F(1)
            six = t3 * F(6)
            if six < 1:
                v = _qround((t1 + (t2 - t1) * six) * F(U))
            elif t3 * F(2) < 1:
                v = _qround(t2 * F(U))
            elif t3 * F(3) < 2:
                v = _qround((t1 + (t2 - t1) * (F(2) / F(3) - t3) * F(6)) * F(U))
            else:
                v = _qround(t1 * F(U))
            out.append(0 if v == 1 else v)
        return Q('rgb', tuple(out))

    def to_hsv(self):
        if self.spec == 'hsv':
            return self
        r, g, b = (F(c) / F(U) for c in self.to_rgb().c)
        mx, mn = max(r, g, b), min(r, g, b)
        d = mx - mn
        v = _qround(mx * F(U))
        if _fuzzy_null(d):
            return Q('hsv', (U, 0, v))
        s = _qround((d / mx) * F(U))
        if _fuzzy_eq(r, mx):
            h = (g - b) / d
        elif _fuzzy_eq(g, mx):
            h = F(2) + (b - r) / d
        else:
            h = F(4) + (r - g) / d
        h = h * F(60)
        if h < 0:
            h += F(360)
        return Q('hsv', (_qround(h * F(100)), s, v))

    # -- the 8-bit accessors Fusion reads ----------------------------------------------------------------
    def rgb8(self):
        return tuple(_div257(c) for c in self.to_rgb().c)

    def hexs(self):
        return '#%02X%02X%02X' % self.rgb8()

    def hue8(self):
        h = self.to_hsv().c[0]
        return -1 if h == U else h // 100

    def sat8(self):
        return _div257(self.to_hsv().c[1])

    def val8(self):
        return _div257(self.to_hsv().c[2])

    def gray(self):
        r, g, b = self.rgb8()
        return (r * 11 + g * 16 + b * 5) // 32

    # -- the operations ----------------------------------------------------------------------------------
    def lighter(self, factor):
        if factor <= 0:
            return self
        if factor < 100:
            return self.darker(10000 // factor)
        h, s, v = self.to_hsv().c
        v = (factor * v) // 100
        if v > U:
            s = max(0, s - (v - U))
            v = U
        return Q('hsv', (h, s, v)).convert(self.spec)

    def darker(self, factor):
        if factor <= 0:
            return self
        if factor < 100:
            return self.lighter(10000 // factor)
        h, s, v = self.to_hsv().c
        return Q('hsv', (h, s, (v * 100) // factor)).convert(self.spec)

    def convert(self, spec):
        if spec == self.spec:
            return self
        return self.to_rgb() if spec == 'rgb' else self.to_hsv() if spec == 'hsv' else self

    @staticmethod
    def from_hsv8(h, s, v):
        return Q('hsv', (U if h == -1 else (h % 360) * 100, s * 0x101, v * 0x101))

    @staticmethod
    def from_hsl8(h, s, l):
        return Q('hsl', (U if h == -1 else (h % 360) * 100, s * 0x101, l * 0x101))


def merged(a, b, factor=50):
    """Fusion's mergedColors: per channel, 8-bit, integer."""
    ra, rb = a.rgb8(), b.rgb8()
    return Q('rgb', tuple(((x * factor) // 100 + (y * (100 - factor)) // 100) * 0x101 for x, y in zip(ra, rb)))


def selftest():
    """Values Qt documents or that follow from its arithmetic; a wrong emulation fails here first."""
    # 65535 * 100 / 200 = 32767 in 16 bits, which qt_div_257 rounds to 127, not 128: Qt's own arithmetic.
    assert Q.hex('#FF0000').darker(200).hexs() == '#7F0000'
    assert Q.hex('#FFFFFF').darker(200).hexs() == '#7F7F7F'
    assert Q.hex('#808080').lighter(200).hexs() == '#FFFFFF'
    assert Q.hex('#EFE5E9').hexs() == '#EFE5E9' and Q.hex('#0F090C').to_hsv().to_rgb().hexs() == '#0F090C'
    assert Q.hex('#773556').lighter(100).hexs() == '#773556'
    return True


# --- 2. what Fusion paints from the palette (qfusionstyle.cpp, 5.15.13 == 6.4.2 in every constant) -----
def fusion(pal):
    """[(name, Q, what it paints, (text role on it, tier) or None)] for the active group `pal` {role: hex}."""
    win, base, btn, hi, txt, wtxt = (Q.hex(pal[r]) for r in ('Window', 'Base', 'Button', 'Highlight', 'Text', 'WindowText'))
    outline = win.darker(140)
    # buttonColor(): lighten by up to (180 - grey)/6 percent, then three quarters of the saturation, in 8-bit HSV
    bc = btn.lighter(100 + max(1, int((180 - btn.gray()) / 6)))
    bc = Q.from_hsv8(bc.hue8(), int(bc.sat8() * 0.75), bc.val8())
    rest = bc.darker(104)
    hio = hi.darker(125)
    if hio.val8() > 160:
        hio = Q.from_hsl8(hio.hue8(), hio.sat8(), 160)
    tab = bc.lighter(104)
    groove = Q.from_hsv8(bc.hue8(), min(255, bc.sat8()), min(255, int(bc.val8() * 0.9)))
    hdr_top, hdr_bot = bc.lighter(104), bc.darker(102)
    pro = hi.darker(140)
    # the default button of a dialog: its face is mixed a tenth toward the highlighted outline lightened 30%
    dbc = merged(bc, hio.lighter(130), 90)
    drest = dbc.darker(104)
    out = [
        ('outline', outline, 'every frame: edits, views, group boxes, tab panes, buttons, combo boxes', None),
        ('frame pen', outline.lighter(108), 'PE_Frame: a scroll area or view frame', None),
        ('tab/checkbox pen', outline.lighter(110), 'the tab widget border and the check box outline', None),
        ('disabled outline', outline.lighter(115), 'a disabled button\'s outline', None),
        ('soft shadow', win.darker(120), 'the line under a menu bar or tool bar', None),
        ('menu border', win.darker(160), 'the 1 px border of a menu', None),
        ('menu field', base.lighter(108), 'the ground of every menu: Base lightened 8%', ('Text', 75)),
        ('tool bar top', win.lighter(104), 'the top of a tool bar or menu bar (a gradient down to Window)', ('WindowText', 75)),
        ('button face top', rest.lighter(124), 'a push button or combo box at rest, its top stop', ('ButtonText', 75)),
        ('button face mid', merged(rest.lighter(124), rest.lighter(102)), 'the same face where its label sits', ('ButtonText', 75)),
        ('button face bottom', rest.lighter(102), 'the same face, its bottom stop', ('ButtonText', 75)),
        ('button hovered top', bc.lighter(124), 'a hovered button, top', ('ButtonText', 75)),
        ('button hovered bottom', bc.lighter(102), 'a hovered button, bottom', ('ButtonText', 75)),
        ('button pressed', bc.darker(110), 'a pressed or checked button: a toggle that is on, its label short (tier 60)', ('ButtonText', 60)),
        ('default button top', drest.lighter(124), 'a dialog\'s default button (OK), its top stop: the face mixed a tenth toward the highlight', ('ButtonText', 75)),
        ('default button mid', merged(drest.lighter(124), drest.lighter(102)), 'the default button where its label sits', ('ButtonText', 75)),
        ('default button bottom', drest.lighter(102), 'the default button, its last pixel row, under the label (tier 60): the mix toward the highlight darkens the face by a stop', ('ButtonText', 60)),
        ('progress fill top', hi.lighter(120), 'the progress bar\'s fill, top: Highlight lightened 20%', ('HighlightedText', 75)),
        ('progress fill bottom', hi, 'the progress bar\'s fill, bottom: Highlight itself', ('HighlightedText', 75)),
        ('tab page', tab, 'the tab widget pane, and the ground its page\'s labels sit on', ('WindowText', 75)),
        ('selected tab top', tab.lighter(104), 'the selected tab, top', ('WindowText', 75)),
        ('unselected tab', tab.darker(108), 'an unselected tab (85% of its height) -- SHORTFALL, recorded: 1.1 under the tier, and no lighter input keeps the resting face off #FFFFFF', ('WindowText', 75)),
        ('unselected tab bottom', tab.darker(116), 'an unselected tab, the last 15%', ('WindowText', 60)),
        ('header top', hdr_top, 'a table header section, top', ('ButtonText', 75)),
        ('header bottom', hdr_bot, 'a table header section, bottom', ('ButtonText', 75)),
        ('header last row', hdr_bot.darker(104), 'a table header section, its last pixel row', None),
        ('scroll groove', bc.darker(107), 'the scrollbar groove', None),
        ('scroll groove inner', bc.darker(105), 'the scrollbar groove, inner stops', None),
        ('scroll slider top', bc.lighter(108), 'the scrollbar slider, top', None),
        ('scroll slider bottom', bc, 'the scrollbar slider, bottom', None),
        ('slider groove dark', groove.darker(110), 'the slider groove', None),
        ('slider groove light', groove.lighter(110), 'the slider groove, light stop', None),
        ('check box top', base.darker(115), 'the top 15% of an unchecked box', None),
        ('check mark', txt.darker(120), 'the tick, on the Base-coloured box', ('Base', 30)),
        ('check box pressed', merged(base, wtxt, 85), 'a box while pressed', None),
        ('highlighted outline', hio, 'the focus frame, the focused edit\'s frame, the default button\'s outline', ('Base', 30)),
        ('menubar pressed outline', hi.darker(125), 'the open menu title\'s outline', None),
        ('progress outline', pro if pro.gray() < outline.gray() else outline, 'the progress bar\'s outline', None),
    ]
    return out


# What Fusion paints as a BLEND -- an alpha over whatever is beneath -- and which the palette cannot reach.
# Listed so the on-screen pass knows what it is looking at; none is an authored value and none is measured
# as one (§4: tolerated, never echoed).
FUSION_BLENDS = [
    ('inner contrast line', 'white at 30/255, inside every button, tab and frame'),
    ('light shade / dark shade', 'white at 90/255 and black at 60/255: grip dots, tool bar edges'),
    ('top shadow', 'black at 18/255 inside edits and boxes'),
    ('focus rect', 'the highlighted outline at 80/255, when focus came from the keyboard'),
    ('soft highlight', 'the highlighted outline at 40/255 inside a focused edit'),
    ('scrollbar edge', 'the outline at 180/255 and 40/255'),
    ('arrows', 'WindowText at 160/255'),
    ('tab widget shadow line', 'black at 15/255 under a tab pane'),
    ('group box interior', 'fusion_groupbox.png, a faint tint over the ground: measured #DBD3D6 over the #DED6D9 tab page, 2026-09-21'),
    ('rounded edges', 'every outline is antialiased over its ground: #C4BDBF where #ABA4A6 meets #DED6D9 at half cover'),
]


# --- 3. the role table: QPalette::ColorRole, in enum order (qpalette.h) --------------------------------
ROLES = ['WindowText', 'Button', 'Light', 'Midlight', 'Dark', 'Mid', 'Text', 'BrightText', 'ButtonText',
         'Base', 'Window', 'Shadow', 'Highlight', 'HighlightedText', 'Link', 'LinkVisited',
         'AlternateBase', 'NoRole', 'ToolTipBase', 'ToolTipText', 'PlaceholderText']
ACCENT_ROLE = 'Accent'   # Qt 6.6+: the twenty-second, qt6ct only
W, L, D, B, A, S = WHITE, LIGHT, DARK, BLACK, ACCENT, SELECT

ACTIVE = [
    ('WindowText', B, 'labels, check boxes, group titles, tab labels, the status bar: BLACK on WHITE, Lc 91.9'),
    ('Button', N9, 'CHOSEN against Fusion\'s derivation (the header): the ladder slot between LIGHT and WHITE, whose rendered face carries BLACK at 78 or better at every stop'),
    ('Light', W, 'the 3D ladder, lighter than Button: WHITE. Fusion draws it only as a menu separator\'s light line, invisible on the menu field'),
    ('Midlight', N9, 'between Button and Light -- the ladder has no slot between neutral_9 and WHITE, so it is Button'),
    ('Dark', D, 'darker than Button: DARK. A sunken frame\'s dark line, where an application draws one'),
    ('Mid', MID, f'between Button and Dark: {MID_NAME}, the ladder slot nearest the midpoint of their lightness'),
    ('Text', B, 'what the user types and reads in a field or a view: BLACK on WHITE, Lc 91.9'),
    ('BrightText', W, 'a text colour that contrasts with Dark: WHITE'),
    ('ButtonText', B, 'a button\'s label, on the face Fusion paints (measured against it, not against Button)'),
    ('Base', W, 'fields, views, lists (§2): WHITE'),
    ('Window', W, 'the window, dialogs, tool bars, the status bar: WHITE, because every label on it is read at the 400 the platform renders'),
    ('Shadow', B, 'the darkest of the 3D ladder: BLACK'),
    ('Highlight', S, 'selected rows and text, the hovered menu item, the progress fill, focus: SELECT (the header)'),
    ('HighlightedText', W, 'WHITE on SELECT, Lc -87.5'),
    ('Link', A, 'links route to ACCENT (§3); Lc 75.4 on WHITE, the body minimum'),
    ('LinkVisited', A, 'visited is not a state the kit colours; worksafe/firefox/ sends it to ACCENT too'),
    ('AlternateBase', W, 'no alternating rows: a band lighter than LIGHT is not a tone change (§5) and LIGHT cannot carry read text at 400'),
    ('NoRole', W, 'unassigned by definition; WHITE so that nothing that reads it by mistake paints a foreign value'),
    ('ToolTipBase', W, 'a tooltip carries read text: WHITE, and QCommonStyle frames it in ToolTipText'),
    ('ToolTipText', B, 'BLACK; the 1 px frame around the tip is drawn in this too -- a control glyph'),
    ('PlaceholderText', D, 'DARK on WHITE, Lc 78.9'),
]
# The inactive group is the active one: focus is shown by the caret and the key window\'s mark (§2, §5), not
# by greying a selection in a window that is not key. Qt also draws tooltips from this group.
INACTIVE = [(r, v, 'as active') for r, v, _ in ACTIVE]
# Disabled: text goes to DARK (§2 names DARK as disabled text) and a selection loses its hue -- DARK carrying
# WHITE, Lc -81.7 -- so a disabled state is tone, not hue (§6.8). Grounds do not change.
_dis = {'WindowText': (D, 'disabled text: DARK on WHITE, Lc 78.9'), 'Text': (D, 'the same in a field'),
        'ButtonText': (D, 'a disabled button\'s label, on the face Fusion paints with a lighter outline'),
        'Highlight': (D, 'a disabled selection loses its hue: DARK, carrying WHITE'),
        'HighlightedText': (W, 'WHITE on DARK, Lc -81.7'),
        'Link': (D, 'a disabled link is disabled text'), 'LinkVisited': (D, 'the same'),
        'PlaceholderText': (D, 'the same DARK as the disabled text beside it'),
        'ToolTipText': (B, 'a tooltip is never disabled; kept'), 'BrightText': (W, 'as active')}
DISABLED = [(r, _dis[r][0], _dis[r][1]) if r in _dis else (r, v, 'as active') for r, v, _ in ACTIVE]
ACCENT_ACTIVE, ACCENT_INACTIVE, ACCENT_DISABLED = A, A, D
FONT_GENERAL, FONT_FIXED = 'Montserrat', 'Hack'   # §5; the size is 12 pt there too


def group(rows):
    return {r: v for r, v, _ in rows}


# --- 4. the KDE colour scheme: the same values in KColorScheme's sets ----------------------------------
# kcolorscheme.cpp maps sets onto QPalette: View -> Base/Text, Window -> Window/WindowText, Button ->
# Button/ButtonText, Selection -> Highlight/HighlightedText, Tooltip -> ToolTip*, View's InactiveText ->
# PlaceholderText, its LinkText/VisitedText -> Link/LinkVisited, and Selection's background -> Accent. The
# semantic text roles take the ANSI normal slots from build/cosmic.py, as build/vscode.py does for text that
# means error, added or warning: DESTRUCTIVE on WHITE is Lc 68.2 and WARNING on WHITE 8.2, under any text
# tier, and a Negative TEXT is text. On the dark sets (Selection, Complementary) no hue reaches the text
# tier -- the three tints of build/vscode.py measure -59 to -86 on SELECT -- so semantic text there is WHITE
# and the row's other marks carry the meaning.
_T = C.terminal()
RED, YELLOW, GREEN = _T['red']['normal'][0], _T['yellow']['normal'][0], _T['green']['normal'][0]
CAPS = {hx: note for slot, row in _T.items() for tier, (hx, lc, note) in row.items() if note}


def _set(bg, alt, fg, inactive, active, link, visited, neg, neu, pos, focus, hover):
    return {'BackgroundNormal': bg, 'BackgroundAlternate': alt, 'ForegroundNormal': fg,
            'ForegroundInactive': inactive, 'ForegroundActive': active, 'ForegroundLink': link,
            'ForegroundVisited': visited, 'ForegroundNegative': neg, 'ForegroundNeutral': neu,
            'ForegroundPositive': pos, 'DecorationFocus': focus, 'DecorationHover': hover}


KDE_SETS = {
    # bg, alt, fg, inactive, active, link, visited, negative, neutral, positive, focus, hover
    'View': _set(W, W, B, D, A, A, A, RED, YELLOW, GREEN, A, D),
    'Window': _set(W, W, B, D, A, A, A, RED, YELLOW, GREEN, A, D),
    # Button: the KDE styles paint it FLAT and render its label at 400, so this is where LIGHT fails as a ground:
    # BLACK on it is Lc 61.3, the 16px/700 pair, and nothing else the set names reads on it either -- ACCENT 45,
    # DARK 48, the ANSI red 47. DARK carrying WHITE is Lc -81.7, the pair build/vscode.py gives its secondary
    # button for the same reason, so the set is DARK and every text role on it is WHITE; the ACCENT focus mark
    # is WHITE too (ACCENT on DARK is Lc -7) and hover is LIGHT (-48). Fusion is the other way round: it
    # lightens whatever it is fed, so its Button is neutral_9 (the header) -- one role, two styles, two answers.
    'Button': _set(D, D, W, W, W, W, W, W, W, W, W, L),
    # Selection: a focus frame around a selected row is WHITE, as build/vscode.py's list.focusAndSelectionOutline
    # is: ACCENT on SELECT is dE 11.7 and Lc -8, invisible as a mark. Semantic text on it is WHITE (above).
    'Selection': _set(S, S, W, W, W, W, W, W, W, W, W, L),
    'Tooltip': _set(W, W, B, D, A, A, A, RED, YELLOW, GREEN, A, D),
    # Complementary is the dark register KDE uses for a lock screen or an OSD: dock tiles, WHITE on DARK. Nothing
    # lighter than WHITE exists to de-emphasise inactive text with (LIGHT on DARK is Lc -48), so it is WHITE too.
    'Complementary': _set(D, D, W, W, W, W, W, W, W, W, W, L),
    # Header is the title and tool bar band (Plasma 5.24+): WHITE with BLACK, as the tool bars are on Fusion.
    'Header': _set(W, W, B, D, A, A, A, RED, YELLOW, GREEN, A, D),
}
KDE_HEADER_INACTIVE = dict(KDE_SETS['Header'])
# The disabled effect: KColorScheme derives disabled text by mixing the text into its ground (ContrastFade),
# so the amount is SOLVED so that mix(BLACK, WHITE, a) lands nearest DARK -- a derived value the checker
# measures. Intensity and colour effects are off, so a disabled ground stays what it was.
def _mix(a, b, t):
    return '#%02X%02X%02X' % tuple(round((x / 255 + (y / 255 - x / 255) * t) * 255) for x, y in zip(ok.rgb(a), ok.rgb(b)))


def kde_disabled_amount():
    best = min((round(t, 3) for t in np.arange(0.10, 0.60, 0.005)), key=lambda t: ok.delta_e(_mix(B, W, t), D))
    return best, _mix(B, W, best)


KDE_DISABLED_AMOUNT, KDE_DISABLED_TEXT = kde_disabled_amount()
KDE_EFFECTS = {
    'ColorEffects:Disabled': [('Enable', 'true'), ('IntensityEffect', '0'), ('IntensityAmount', '0'),
                              ('ColorEffect', '0'), ('ColorAmount', '0'), ('Color', 'RGB:' + D),
                              ('ContrastEffect', '1'), ('ContrastAmount', f'{KDE_DISABLED_AMOUNT:g}')],
    'ColorEffects:Inactive': [('Enable', 'false'), ('ChangeSelectionColor', 'false'), ('IntensityEffect', '0'),
                              ('IntensityAmount', '0'), ('ColorEffect', '0'), ('ColorAmount', '0'),
                              ('Color', 'RGB:' + L), ('ContrastEffect', '0'), ('ContrastAmount', '0')],
}
# The window manager's title bar, where a decoration reads it (KWin): §2's key and non-key titlebars.
KDE_WM = [('activeBackground', A), ('activeForeground', W), ('activeBlend', A),
          ('inactiveBackground', L), ('inactiveForeground', B), ('inactiveBlend', L)]
KDE_GENERAL = [('ColorScheme', 'Remainder'), ('Name', 'Remainder'), ('shadeSortColumn', 'false')]
KDE_KDE = [('contrast', '4')]   # the platform default; KColorScheme's shades are derived from it (residue)
KDE_SET_ORDER = ['Button', 'Complementary', 'Header', 'Header][Inactive', 'Selection', 'Tooltip', 'View', 'Window']


def _rgb_triple(hx):
    return ','.join(str(int(round(float(c)))) for c in ok.rgb(hx))


# --- 5. the registry: every value a committed file may contain, and which ladder it came from ----------
def authored():
    reg = {WHITE: 'WHITE', LIGHT: 'LIGHT', DARK: 'DARK', BLACK: 'BLACK',
           ACCENT: 'ACCENT', SELECT: 'SELECT', CURSOR: 'CURSOR'}
    reg.update({v: k for k, v in SEMANTIC.items()})
    for k, hx in NEUTRALS.items():
        reg.setdefault(hx, k)
    for slot, row in _T.items():
        for tier, (hx, lc, note) in row.items():
            reg.setdefault(hx, f'ansi {tier} {slot}')
    return reg


def is_content(name):
    return name.startswith('ansi ') or name in SEMANTIC


# --- 6. writing -----------------------------------------------------------------------------------------
def _argb(hx):
    return '#FF' + hx[1:].upper()


def qtct_text(with_accent):
    """The qt5ct/qt6ct scheme: three comma-separated lists of #AARRGGBB, one per QPalette::ColorRole, in enum
    order. qt5ct 1.5 requires exactly NColorRoles (21 on Qt 5.15); qt6ct 0.9 accepts >= NColorRoles and,
    on Qt >= 6.6, an Accent as the twenty-second."""
    n = 22 if with_accent else 21
    head = (f"# Remainder for {'qt6ct' if with_accent else 'qt5ct'} -- the colour scheme. AUTHORITY.md is the authority.\n"
            "# GENERATED by build/qt.py --write. Do not hand-edit: edit poles.json, the derivation, or the role table\n"
            "# in build/qt.py, and regenerate. build/qt.py fails if this file is not what it produces.\n"
            "#\n"
            f"# {n} values per group, in QPalette::ColorRole order: WindowText, Button, Light, Midlight, Dark, Mid, Text,\n"
            "# BrightText, ButtonText, Base, Window, Shadow, Highlight, HighlightedText, Link, LinkVisited, AlternateBase,\n"
            "# NoRole, ToolTipBase, ToolTipText, PlaceholderText"
            + (", Accent (Qt 6.6+; qt6ct 0.9 takes the first 21 on 6.4)" if with_accent else "") + ".\n"
            "# Every value is one of section 2's seven, two slots of the COSMIC neutral ladder (build/cosmic.py), or\n"
            "# nothing else; every alpha is FF. The style paints what it derives from these -- build/qt.py --derive.\n\n")
    rows = []
    for name, g, acc in (('active', ACTIVE, ACCENT_ACTIVE), ('disabled', DISABLED, ACCENT_DISABLED),
                         ('inactive', INACTIVE, ACCENT_INACTIVE)):
        vals = [_argb(v) for _, v, _ in g] + ([_argb(acc)] if with_accent else [])
        rows.append(f'{name}_colors=' + ', '.join(vals))
    return head + '[ColorScheme]\n' + '\n'.join(rows) + '\n'


def kde_text():
    """The KDE colour scheme, KConfig ini with decimal triples. Installed to ~/.local/share/color-schemes and
    merged, group by group, into ~/.config/kdeglobals by install.sh."""
    out = ["# Remainder -- the KDE colour scheme. AUTHORITY.md is the authority.",
           "# GENERATED by build/qt.py --write. Do not hand-edit; build/qt.py fails if this is not what it produces.",
           "# Read by KColorScheme (Plasma, the KDE platform theme, and KDE applications in a Flatpak, which read",
           "# ~/.config/kdeglobals). Values are decimal triples, the notation the platform uses.", ""]
    for g, kv in KDE_EFFECTS.items():
        out.append(f'[{g}]')
        out += [f'{k}={_rgb_triple(v[4:]) if v.startswith("RGB:") else v}' for k, v in kv]
        out.append('')
    for name in KDE_SET_ORDER:
        d = KDE_HEADER_INACTIVE if name == 'Header][Inactive' else KDE_SETS[name]
        out.append(f'[Colors:{name}]')
        out += [f'{k}={_rgb_triple(v)}' for k, v in d.items()]
        out.append('')
    out.append('[General]')
    out += [f'{k}={v}' for k, v in KDE_GENERAL]
    out.append('')
    out.append('[KDE]')
    out += [f'{k}={v}' for k, v in KDE_KDE]
    out.append('')
    out.append('[WM]')
    out += [f'{k}={_rgb_triple(v)}' for k, v in KDE_WM]
    out.append('')
    return '\n'.join(out)


def write():
    for path, text in ((QT5_SCHEME, qtct_text(False)), (QT6_SCHEME, qtct_text(True)), (KDE_SCHEME, kde_text())):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print(f'wrote {os.path.relpath(path, ROOT)}  ({len(text)} bytes)')


# --- 7. reading, in each file's notation ----------------------------------------------------------------
_ARGB = re.compile(r'#([0-9A-Fa-f]{2})([0-9A-Fa-f]{6})\b')
_HEX6 = re.compile(r'#[0-9A-Fa-f]{6}\b')


def read_qtct(path):
    """{group: [(alpha, '#RRGGBB'), ...]} from a qt5ct/qt6ct scheme, comments stripped."""
    groups = {}
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith(('#', ';', '[')):
            continue
        k, _, v = line.partition('=')
        if k.strip().endswith('_colors'):
            vals = [x.strip() for x in v.split(',') if x.strip()]
            parsed = []
            for x in vals:
                m = _ARGB.fullmatch(x)
                parsed.append((m.group(1).upper(), '#' + m.group(2).upper()) if m else (None, x))
            groups[k.strip()[:-7]] = parsed
    return groups


def read_ini(path):
    """{group: [(key, value)]} for a KConfig / QSettings ini, comments stripped, order kept."""
    out, cur = {}, None
    for line in open(path, encoding='utf-8', errors='replace'):
        s = line.rstrip('\n')
        if not s.strip() or s.lstrip().startswith(('#', ';')):
            continue
        if s.startswith('['):
            cur = s.strip()[1:-1]
            out.setdefault(cur, [])
            continue
        k, _, v = s.partition('=')
        out.setdefault(cur, []).append((k.strip(), v.strip()))
    return out


def _triple(v):
    m = re.fullmatch(r'\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*', v or '')
    return '#%02X%02X%02X' % tuple(int(x) for x in m.groups()) if m else None


# --- 8. what the checker measures -----------------------------------------------------------------------
# Text on ground, both read out of the committed scheme, at APCA's tier for what the widget renders.
PAIRS = [
    ('WindowText', 'Window', 75, 'a label on the window, 400'),
    ('Text', 'Base', 75, 'text in a field or view'),
    ('HighlightedText', 'Highlight', 75, 'a selected row or selected text'),
    ('Link', 'Base', 75, 'a link in a view'),
    ('Link', 'Window', 75, 'a link on the window'),
    ('LinkVisited', 'Base', 75, 'a visited link'),
    ('PlaceholderText', 'Base', 75, 'a placeholder'),
    ('ToolTipText', 'ToolTipBase', 75, 'a tooltip'),
    ('BrightText', 'Dark', 75, 'BrightText where a style puts it on Dark'),
    ('Dark', 'Window', 30, 'a sunken frame\'s dark line: a mark'),
    ('Shadow', 'Window', 30, 'a shadow line: a mark'),
]
DISABLED_PAIRS = [
    ('WindowText', 'Window', 30, 'disabled text: de-emphasised, a mark tier (as build/vscode.py holds disabledForeground)'),
    ('Text', 'Base', 30, 'disabled text in a field'),
    ('HighlightedText', 'Highlight', 75, 'a disabled selection still carries its text'),
]
# Two grounds that touch and carry information: OKLab dE against SURFACE_FLOOR (§0e).
ADJACENT = [
    ('Highlight', 'Base', 'the selected row against the rows around it'),
    ('Highlight', 'Window', 'the highlighted menu item against the window'),
    ('ToolTipBase', 'Highlight', 'a tooltip over a selection'),
]
ADJACENT_EXEMPT = {
    ('Base', 'Window'): 'WHITE meets WHITE: a field is edged by the outline Fusion draws (a control glyph), not by a tone change',
    ('ToolTipBase', 'Window'): 'the tooltip is framed in ToolTipText by QCommonStyle',
    ('AlternateBase', 'Base'): 'no alternating band is drawn (the role table)',
    ('Button', 'Window'): 'Fusion paints the face, not Button; the face is measured under derived values',
}
DISABLED_ADJACENT = [('Highlight', 'Base', 'a disabled selection against the field')]
KDE_TEXT_KEYS = [('ForegroundNormal', 75, 'text'), ('ForegroundInactive', 75, 'inactive text, placeholders'),
                 ('ForegroundActive', 75, 'active text'), ('ForegroundLink', 75, 'a link'),
                 ('ForegroundVisited', 75, 'a visited link'), ('ForegroundNegative', 75, 'text that means error'),
                 ('ForegroundNeutral', 75, 'text that means warning'), ('ForegroundPositive', 75, 'text that means done'),
                 ('DecorationFocus', 30, 'the focus frame: a mark'), ('DecorationHover', 30, 'the hover frame: a mark')]


def _tag(hx):
    if P.reserved(hx):
        return 'reserved (§3)'
    fam, gap, req = P.clearance(hx)
    return 'neutral' if not P.readable(hx) else f'{gap:5.1f}/{req:4.1f} {fam}'


def check():
    reg, bad, notes = authored(), 0, []
    selftest()
    missing = [p for p in (QT5_SCHEME, QT6_SCHEME, KDE_SCHEME) if not os.path.isfile(p)]
    if missing:
        print('qt: not committed yet: ' + ', '.join(os.path.relpath(p, ROOT) for p in missing) + ' -- run --write')
        return False

    # (a) the generated files are what the generator produces
    for path, text in ((QT5_SCHEME, qtct_text(False)), (QT6_SCHEME, qtct_text(True)), (KDE_SCHEME, kde_text())):
        same = open(path, encoding='utf-8').read() == text
        print(f'  {os.path.relpath(path, ROOT)}: {"matches the generator" if same else "DIFFERS FROM THE GENERATOR -- run build/qt.py --write"}')
        bad += not same

    # (b) the qt5ct and qt6ct schemes: counts, alphas, every value a ladder value, chrome clears
    schemes = {}
    for label, path, n in (('qt5ct', QT5_SCHEME, 21), ('qt6ct', QT6_SCHEME, 22)):
        g = read_qtct(path)
        schemes[label] = g
        print(f'\n  {label}: {os.path.relpath(path, ROOT)}')
        for grp in ('active', 'inactive', 'disabled'):
            vals = g.get(grp, [])
            okn = len(vals) == n
            print(f'    {grp:9} {len(vals)} values{"" if okn else f" -- {label} needs exactly {n} (qt5ct: == NColorRoles; qt6ct: NColorRoles with Accent)"}')
            bad += not okn
            for i, (alpha, hx) in enumerate(vals):
                role = ROLES[i] if i < len(ROLES) else ACCENT_ROLE
                if alpha != 'FF':
                    notes.append(f'{label} {grp} {role}: alpha {alpha} -- a blend is not an authored value'); bad += 1
                name = reg.get(hx)
                if name is None:
                    notes.append(f'{label} {grp} {role}: {hx} NOT DERIVED BY ANY LADDER'); bad += 1
                elif P.reserved(hx):
                    notes.append(f'{label} {grp} {role}: {hx} is reserved (§3)'); bad += 1
                elif not is_content(name) and not P.clear(hx):
                    notes.append(f'{label} {grp} {role}: {hx} POLE: chrome must clear every pole'); bad += 1
        seen = {}
        for grp, vals in g.items():
            for _, hx in vals:
                seen[hx] = seen.get(hx, 0) + 1
        print(f'    {len(seen)} distinct values:')
        for hx, cnt in sorted(seen.items(), key=lambda kv: -kv[1]):
            print(f'      {hx} x{cnt:<3} {str(reg.get(hx)):12} {_tag(hx)}')
    # the two files agree on the twenty-one they share, and only the Accent differs
    for grp in ('active', 'inactive', 'disabled'):
        a5, a6 = [h for _, h in schemes['qt5ct'].get(grp, [])], [h for _, h in schemes['qt6ct'].get(grp, [])]
        if a5 != a6[:21]:
            notes.append(f'{grp}: the qt5ct and qt6ct schemes differ on the twenty-one roles they share'); bad += 1

    # (c) the pairs and adjacencies, read out of the qt6ct file (the qt5ct one is the same twenty-one)
    act = {ROLES[i]: hx for i, (_, hx) in enumerate(schemes['qt6ct']['active'][:21])}
    dis = {ROLES[i]: hx for i, (_, hx) in enumerate(schemes['qt6ct']['disabled'][:21])}
    acc = schemes['qt6ct']['active'][21][1] if len(schemes['qt6ct']['active']) > 21 else None
    print(f'\n  pairs the palette states ({len(PAIRS)} active, {len(DISABLED_PAIRS)} disabled; APCA Lc, signed):')
    for grp, table in (('active', PAIRS), ('disabled', DISABLED_PAIRS)):
        pal = act if grp == 'active' else dis
        for t, gd, floor, why in table:
            lc = apca.lc(pal[t], pal[gd])
            okay = abs(lc) >= floor
            bad += not okay
            print(f'    {grp:8} {reg.get(pal[t], pal[t]):10} on {reg.get(pal[gd], pal[gd]):10} Lc {lc:7.1f}  floor {floor:3.0f}  {abs(lc) - floor:+5.1f}  {"ok " if okay else "LOW"}  {why}')
    print(f'\n  surfaces that touch (OKLab dE, floor {FLOOR}):')
    for a, b, why in ADJACENT:
        d = ok.delta_e(act[a], act[b])
        okay = d >= FLOOR - 0.05
        bad += not okay
        print(f'    {reg.get(act[a], act[a]):10} / {reg.get(act[b], act[b]):10} dE {d:5.1f}  {d - FLOOR:+5.1f}  {"ok " if okay else "BELOW"}  {why}')
    for a, b, why in DISABLED_ADJACENT:
        d = ok.delta_e(dis[a], dis[b])
        okay = d >= FLOOR - 0.05
        bad += not okay
        print(f'    {reg.get(dis[a], dis[a]):10} / {reg.get(dis[b], dis[b]):10} dE {d:5.1f}  {d - FLOOR:+5.1f}  {"ok " if okay else "BELOW"}  {why} (disabled)')
    for (a, b), why in ADJACENT_EXEMPT.items():
        print(f'    {reg.get(act[a], act[a]):10} / {reg.get(act[b], act[b]):10} dE {ok.delta_e(act[a], act[b]):5.1f}  exempt: {why}')
    if acc is not None:
        print(f'    Accent (Qt 6.6+): {reg.get(acc, acc)}, dE {ok.delta_e(acc, act["Highlight"]):.1f} from Highlight -- §2\'s own exempt pair')

    # (d) what Fusion paints from these: derived, and measured
    print(f'\n  Fusion\'s derived values ({MEASURED_FROM}; the model in build/qt.py fusion()):')
    print(f'    {"":24} {"value":8} {"nearest":12} {"dE":>5}  {"pole":22} text on it')
    for name, q, where, text in fusion(act):
        hx = q.hexs()
        near = min(reg, key=lambda a: ok.delta_e(a, hx))
        note = ''
        transient = name.startswith(('button hovered', 'button pressed', 'check box pressed'))
        if P.reserved(hx) and not transient:
            note = 'RESERVED: the style paints #FFFFFF or #000000 on a resting ground -- move the input'; bad += 1
        elif P.reserved(hx):
            note = 'reserved, for the duration of a hover: the top stop clips (the header) -- recorded, not a ground'
        elif not P.clear(hx):
            note = 'POLE: a derived chrome value reads as a signal -- move the input'; bad += 1
        elif ok.delta_e(hx, '#FFFFFF') < 3 or ok.delta_e(hx, '#000000') < 3:
            note = f'near a reserved value (dE {min(ok.delta_e(hx, "#FFFFFF"), ok.delta_e(hx, "#000000")):.1f}): the style\'s clipping, recorded'
        tv = ''
        if text:
            role, tier = text
            side = act[role]
            lc = apca.lc(side, hx) if role in ('Text', 'WindowText', 'ButtonText', 'HighlightedText') else apca.lc(hx, side)
            okay = abs(lc) >= tier
            recorded = not okay and 'SHORTFALL' in where and abs(lc) >= tier - 1.5
            bad += not (okay or recorded)
            tv = f'{role if role in ("Text", "WindowText", "ButtonText", "HighlightedText") else "on " + role:11} Lc {lc:6.1f} floor {tier:2}  {"ok " if okay else "REC" if recorded else "LOW"}'
        print(f'    {name:24} {hx:8} {reg.get(near, near):12} {ok.delta_e(hx, near):5.1f}  {_tag(hx):22} {tv}  {note}')
    print(f'    and {len(FUSION_BLENDS)} blends the palette does not reach (--derive lists them)')

    # (e) the KDE scheme: every triple a ladder value, the pairs per set, the derived disabled text
    kde = read_ini(KDE_SCHEME)
    print(f'\n  {os.path.relpath(KDE_SCHEME, ROOT)}: {len(kde)} groups')
    kvals = {}
    for grp, kv in kde.items():
        for k, v in kv:
            hx = _triple(v)
            if hx is None:
                if re.search(r'\d+\s*,\s*\d+', v):
                    notes.append(f'kde [{grp}] {k}: {v!r} is not a triple the checker can read'); bad += 1
                continue
            kvals[hx] = kvals.get(hx, 0) + 1
            name = reg.get(hx)
            if name is None:
                notes.append(f'kde [{grp}] {k}: {hx} NOT DERIVED BY ANY LADDER'); bad += 1
            elif P.reserved(hx):
                notes.append(f'kde [{grp}] {k}: {hx} is reserved (§3)'); bad += 1
            elif not is_content(name) and not P.clear(hx):
                notes.append(f'kde [{grp}] {k}: {hx} POLE'); bad += 1
            elif is_content(name) and not re.search(r'Negative|Neutral|Positive', k):
                notes.append(f'kde [{grp}] {k}: takes {name}, a content value, on a key that carries no meaning'); bad += 1
    for hx, cnt in sorted(kvals.items(), key=lambda kv: -kv[1]):
        print(f'    {hx} x{cnt:<3} {str(reg.get(hx)):18} {_tag(hx)}')
    print(f'    pairs per set (fg on BackgroundNormal; tier 75 for text, 30 for a mark):')
    for grp, kv in kde.items():
        if not grp.startswith('Colors:'):
            continue
        d = dict(kv)
        bg = _triple(d.get('BackgroundNormal'))
        for k, tier, why in KDE_TEXT_KEYS:
            fg = _triple(d.get(k))
            if fg is None or bg is None:
                continue
            lc = apca.lc(fg, bg)
            okay = abs(lc) >= tier or (fg in CAPS and abs(lc) >= tier - 1.0)
            bad += not okay
            print(f'      {grp[7:]:16} {k:18} {reg.get(fg, fg):10} on {reg.get(bg, bg):8} Lc {lc:7.1f}  floor {tier:2}  {abs(lc) - tier:+5.1f}  {"ok " if okay else "LOW"}  {why}')
    eff = dict(kde.get('ColorEffects:Disabled', []))
    amt = float(eff.get('ContrastAmount', 'nan'))
    dt = _mix(B, W, amt) if amt == amt else None
    if dt:
        print(f'    disabled text, derived by KColorScheme: mix(BLACK, WHITE, {amt:g}) = {dt}, dE {ok.delta_e(dt, D):.2f} from DARK, Lc {apca.lc(dt, W):.1f} on WHITE'
              f'{"" if eff.get("ContrastEffect") == "1" and eff.get("IntensityEffect") == "0" and eff.get("ColorEffect") == "0" else "  -- EFFECTS ARE NOT fade-only"}')
        bad += not (eff.get('ContrastEffect') == '1' and eff.get('IntensityEffect') == '0' and eff.get('ColorEffect') == '0')
    gen = dict(kde.get('General', []))
    if gen.get('ColorScheme') != 'Remainder':
        notes.append('kde [General] ColorScheme is not Remainder'); bad += 1

    # (f) the conf fragments carry no colour and select the scheme, the style, the type
    for label, path in (('qt5ct', QT5_CONF), ('qt6ct', QT6_CONF)):
        if not os.path.isfile(path):
            notes.append(f'{os.path.relpath(path, ROOT)} is missing'); bad += 1; continue
        ini = read_ini(path)
        body = '\n'.join(v for kv in ini.values() for _, v in kv)
        hexes = sorted(set(_HEX6.findall(body)))
        app = dict(ini.get('Appearance', []))
        fonts = dict(ini.get('Fonts', []))
        iface = dict(ini.get('Interface', []))
        probs = []
        if app.get('style') != 'Fusion':
            probs.append('style is not Fusion (the derivations modelled are Fusion\'s)')
        if app.get('custom_palette') != 'true':
            probs.append('custom_palette is not true')
        if not app.get('color_scheme_path', '').endswith(f'{label}/colors/remainder.conf'):
            probs.append(f'color_scheme_path does not point at {label}/colors/remainder.conf')
        for k in ('icon_theme', 'standard_dialogs'):
            if k in app:
                probs.append(f'{k} is set: the installer preserves the user\'s (the role table)')
        for k, fam in (('general', FONT_GENERAL), ('fixed', FONT_FIXED)):
            v = fonts.get(k, '').strip('"')
            if not v.startswith(fam + ',12,'):
                probs.append(f'[Fonts] {k} is not {fam} at 12 pt (§5)')
        if iface.get('gui_effects') != '@Invalid()':
            probs.append('[Interface] gui_effects is not @Invalid() -- motion is §0\'s larger half')
        print(f'\n  {os.path.relpath(path, ROOT)}: {sum(len(v) for v in ini.values())} keys, {len(hexes)} colour(s)'
              + (' -- A CONF FRAGMENT PAINTS NOTHING' if hexes else '') + ('' if not probs else '\n    ' + '\n    '.join(probs)))
        bad += bool(hexes) + len(probs)

    # (g) the installer writes no colour of its own
    if os.path.isfile(INSTALLER):
        body = re.sub(r'^\s*#.*$', '', open(INSTALLER, errors='ignore').read(), flags=re.M)
        found = sorted({h.upper() for h in _HEX6.findall(body)})
        print(f'  {os.path.relpath(INSTALLER, ROOT)}: {len(found)} colour(s) it writes itself')
        for hx in found:
            note = '' if hx in reg else 'NOT A VALUE THE KIT AUTHORS'
            bad += bool(note)
            print(f'    {hx}  {note}')

    if notes:
        print('\n  notes:')
        for n_ in notes:
            print(f'    {n_}')
    print(f'\nqt: {"every value, pair, adjacency and derived value clears" if not bad else str(bad) + " DEFECT(S)"}')
    return bad == 0


# --- 9. the live machine: a report, never a gate ----------------------------------------------------------
QT_LIBDIRS = ['/usr/lib/x86_64-linux-gnu', '/usr/lib64', '/usr/lib', '/usr/lib/aarch64-linux-gnu']


def _cfg():
    return os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')


def installed():
    print(f'the live machine, {MEASURED_ON if False else "now"}: a report, not a gate\n')
    print(f'  QT_QPA_PLATFORMTHEME = {os.environ.get("QT_QPA_PLATFORMTHEME", "(unset)")}   XDG_CURRENT_DESKTOP = {os.environ.get("XDG_CURRENT_DESKTOP", "(unset)")}')
    for major in (5, 6):
        libs = [p for d in QT_LIBDIRS for p in glob.glob(os.path.join(d, f'libQt{major}Core.so.{major}.*.*'))]
        ver = sorted(os.path.basename(p).split('.so.')[1] for p in libs)
        plug = [p for d in QT_LIBDIRS for p in glob.glob(os.path.join(d, f'qt{major}', 'plugins', 'platformthemes', '*.so'))]
        print(f'  Qt {major}: {", ".join(ver) if ver else "not installed"}; platform themes: {", ".join(sorted(os.path.basename(p)[3:-3] for p in plug)) or "none"}')
    reg = authored()
    for ct in ('qt5ct', 'qt6ct'):
        conf = os.path.join(_cfg(), ct, f'{ct}.conf')
        print(f'\n  {conf}: {"present" if os.path.isfile(conf) else "absent"}')
        if not os.path.isfile(conf):
            continue
        ini = read_ini(conf)
        app = dict(ini.get('Appearance', []))
        fonts = dict(ini.get('Fonts', []))
        for k in ('style', 'custom_palette', 'color_scheme_path', 'icon_theme', 'standard_dialogs', 'cosmic_qt_version'):
            print(f'    {k:18} = {app.get(k, "(unset)" + (" -> Fusion" if k == "style" else ""))}')
        for k in ('general', 'fixed'):
            print(f'    [Fonts] {k:10} = {fonts.get(k, "(unset)")}')
        print(f'    [Interface] gui_effects = {dict(ini.get("Interface", [])).get("gui_effects", "(unset: the platform default effects)")}')
        path = os.path.expandvars(app.get('color_scheme_path', '').replace('~', os.path.expanduser('~')))
        if app.get('custom_palette') != 'true' or not path:
            print('    no custom palette: the style\'s own default palette is in use'); continue
        if not os.path.isfile(path):
            print(f'    the scheme it points at is missing: {path}'); continue
        g = read_qtct(path)
        act = g.get('active', [])
        print(f'    the scheme in use: {path} ({len(act)} active values{"" if len(act) >= 21 else " -- FEWER THAN 21: the loader refuses it and falls back"})')
        auth = sum(1 for _, hx in act if hx in reg)
        print(f'      {auth} of {len(act)} active roles are values the kit authors')
        pal = {ROLES[i]: hx for i, (_, hx) in enumerate(act[:21])}
        for t, gd, floor, why in PAIRS[:8]:
            if t in pal and gd in pal:
                lc = apca.lc(pal[t], pal[gd])
                print(f'      {t:16} on {gd:14} {pal[t]} on {pal[gd]}  Lc {lc:7.1f}  floor {floor}  {"ok " if abs(lc) >= floor else "LOW"}')
        for a, b, why in ADJACENT[:1] + [('Base', 'Window', 'the field against the window')]:
            d = ok.delta_e(pal[a], pal[b])
            print(f'      {a:16} /  {b:14} dE {d:5.1f}  {"ok " if d >= FLOOR or (a, b) == ("Base", "Window") and d < 1 else "BELOW the surface floor" if d < FLOOR else "ok "}')
    kg = os.path.join(_cfg(), 'kdeglobals')
    print(f'\n  {kg}: {"present" if os.path.isfile(kg) else "absent"}')
    if os.path.isfile(kg):
        ini = read_ini(kg)
        gen = dict(ini.get('General', []))
        print(f'    [General] ColorScheme = {gen.get("ColorScheme", "(unset)")}; [KDE] widgetStyle = {dict(ini.get("KDE", [])).get("widgetStyle", "(unset)")}')
        for grp in ('Colors:View', 'Colors:Selection', 'Colors:Button'):
            d = dict(ini.get(grp, []))
            fg, bg = _triple(d.get('ForegroundNormal')), _triple(d.get('BackgroundNormal'))
            if fg and bg:
                print(f'    {grp:16} {fg} on {bg}  Lc {apca.lc(fg, bg):7.1f}  {"authored" if fg in reg and bg in reg else "not the kit\'s values"}')
    for d in (os.path.expanduser('~/.local/share/color-schemes'),):
        if os.path.isdir(d):
            print(f'  {d}: ' + ', '.join(sorted(os.listdir(d))))
    tk = os.path.join(_cfg(), 'cosmic', 'com.system76.CosmicTk', 'v1', 'apply_theme_global')
    sysd = '/usr/share/cosmic/com.system76.CosmicTk/v1/apply_theme_global'
    val = open(tk).read().strip() if os.path.isfile(tk) else (open(sysd).read().strip() + ' (the system default)') if os.path.isfile(sysd) else '(no COSMIC)'
    print(f'\n  COSMIC apply_theme_global = {val}')
    ov = os.path.expanduser('~/.local/share/flatpak/overrides/global')
    if os.path.isfile(ov):
        print(f'  flatpak overrides/global: ' + open(ov).read().strip().replace('\n', ' | '))
    return True


# --- 10. --derive ----------------------------------------------------------------------------------------
def _print_derivations():
    reg = authored()
    print(f'=== the role table: QPalette::ColorRole in enum order, active group ({MEASURED_FROM}) ===')
    for r, v, why in ACTIVE:
        print(f'  {r:16} {v}  {reg[v]:10} {why}')
    print(f'  {ACCENT_ROLE:16} {ACCENT_ACTIVE}  {reg[ACCENT_ACTIVE]:10} Qt 6.6+ only, the qt6ct file: what a style uses for toggles and checked marks')
    print('\n=== disabled: what changes ===')
    for r, v, why in DISABLED:
        if why != 'as active':
            print(f'  {r:16} {v}  {reg[v]:10} {why}')
    print('\n=== the Button trials: what Fusion paints from four inputs (build/qt.py fusion()) ===')
    print(f'  {"input":10} {"buttonColor":12} {"face top":9} {"mid":9} {"bottom":9} {"tab page":9}  BLACK on top/mid/bottom/page   WHITE on top/bottom')
    for nm, v in (('LIGHT', LIGHT), ('WHITE', WHITE), ('DARK', DARK), ('neutral_9', N9)):
        pal = dict(group(ACTIVE), Button=v)
        f = {n_: q.hexs() for n_, q, _, _ in fusion(pal)}
        btn = Q.hex(v)
        bc = btn.lighter(100 + max(1, int((180 - btn.gray()) / 6)))
        bc = Q.from_hsv8(bc.hue8(), int(bc.sat8() * 0.75), bc.val8()).hexs()
        print(f'  {nm:10} {bc:12} {f["button face top"]:9} {f["button face mid"]:9} {f["button face bottom"]:9} {f["tab page"]:9}  '
              f'{apca.lc(BLACK, f["button face top"]):5.1f} {apca.lc(BLACK, f["button face mid"]):5.1f} {apca.lc(BLACK, f["button face bottom"]):5.1f} {apca.lc(BLACK, f["tab page"]):5.1f}   '
              f'{apca.lc(WHITE, f["button face top"]):6.1f} {apca.lc(WHITE, f["button face bottom"]):6.1f}'
              + ('   <- reserved: the top clips to #FFFFFF' if P.reserved(f["button face top"]) else ''))
    print(f'  Button is neutral_9 ({N9}): the only input whose face carries BLACK at the 400 tier at every stop.')
    print('\n=== everything Fusion derives from the committed palette ===')
    for name, q, where, text in fusion(group(ACTIVE)):
        hx = q.hexs()
        near = min(reg, key=lambda a: ok.delta_e(a, hx))
        L_, C_, h_ = ok.lch(hx)
        print(f'  {name:24} {hx}  L {L_:.3f} C {C_:.4f}  nearest {reg[near]:10} dE {ok.delta_e(hx, near):4.1f}  {where}')
    print('  blends, unreachable by a palette:')
    for n_, w in FUSION_BLENDS:
        print(f'    {n_:26} {w}')
    print('\n=== the KDE scheme ===')
    print(f'  disabled text: ContrastFade at {KDE_DISABLED_AMOUNT:g} -> mix(BLACK, WHITE) = {KDE_DISABLED_TEXT}, dE {ok.delta_e(KDE_DISABLED_TEXT, DARK):.2f} from DARK (SOLVED for the nearest landing)')
    print(f'  semantic text: the ANSI normal slots red {RED} (Lc {apca.lc(RED, WHITE):.1f}), yellow {YELLOW} ({apca.lc(YELLOW, WHITE):.1f}, at its cap), green {GREEN} ({apca.lc(GREEN, WHITE):.1f}) on WHITE;')
    print(f'  on SELECT the tints of build/vscode.py would read: ' + ', '.join(f'{k} {apca.lc(v, SELECT):.1f}' for k, v in (('red', '#FF9E9B'), ('green', '#4FFFD1'), ('yellow', '#FFD841'))) + ' -- so semantic text on a dark set is WHITE')
    print(f'  [WM]: key {ACCENT} carrying {WHITE}; non-key {LIGHT} carrying {BLACK} -- read by KWin, not by COSMIC; unverified here')
    n = {}
    for _, v, _ in ACTIVE + INACTIVE + DISABLED:
        n[v] = n.get(v, 0) + 1
    print(f'\n=== the three groups: {len(ACTIVE) * 3} slots on {len(n)} values ===')
    for hx, c in sorted(n.items(), key=lambda kv: -kv[1]):
        print(f'  {reg[hx]:12} {hx} {c:3}')


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--write' in sys.argv:
        write(); sys.exit(0)
    if '--installed' in sys.argv:
        sys.exit(0 if installed() else 1)
    sys.exit(0 if check() else 1)
