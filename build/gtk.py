"""The GTK 3 surface: record the platform, write the theme, then check what is committed. AUTHORITY.md is the
authority.

Every GTK 3 application draws with the theme the desktop names: Nemo, GIMP, Inkscape, Meld, GParted, Emacs, the GTK
file chooser, and the menus and dialogs Firefox and Chromium borrow from GTK. On COSMIC the theme GTK 3 is given is
adw-gtk3 -- a dependency of cosmic-settings, so it is on every COSMIC machine -- and it is what this theme is built
against. Three things measured off the installed build (GTK 3.24.52, adw-gtk3 6.5, Nemo 6.6.4, COSMIC, 2026-09-30)
shape it:

  NO EXPRESSION MEANS ONE ROLE. adw-gtk3 writes each state as a tint of the ink over the ground -- mix(fg, bg, 0.9)
    for a button at rest, 0.85 hovered, 0.7 pressed; alpha(currentColor, 0.1) for a hover -- and 1,493 of its
    declarations carry a colour, 412 distinct. The same mix is a button on a WHITE window and a button on a LIGHT
    tool bar. So the platform is RECORDED (build/gtk_platform.css), and every declaration is ANSWERED by reading
    its selector for three things: the surface the element sits on (the key strip, a panel, a menu, a field, an
    OSD), what the element is, and what state it is in -- and taking the kit's ground and ink for that. The theme
    is the record, answered: the same rules, the same geometry, every colour a kit value by name. A selector
    whose element the table does not know is UNCLASSIFIED and fails the gate.

  THE WINDOW KNOWS WHEN IT IS KEY. GTK 3 draws its own title bar on COSMIC and marks a window that is not key
    :backdrop, so the strip is ACCENT carrying WHITE while the window is key and LIGHT carrying BLACK when it is
    not -- and nothing else changes: the platform's rules for a window that is not key are not written, outside
    the strip, since one of them (button.flat:backdrop) reached a toggled button and left its WHITE glyph on
    the tool bar.

  THE TEXT RENDERS UNDER THE SIZE THE FLOORS ASSUME. A family named without a size renders at 10 pt, 13.3 px, and
    every floor in §0e assumes about 16. The theme sets 16 px on every window, CHOSEN as on worksafe/obsidian/,
    and weight follows the ground: every LIGHT panel carries BLACK at 700 (Lc 61.2), every WHITE field 400.

So the surface is a record, a table of answers, and the kit's own rules (CONTRIBUTING.md §8):

  THE RECORD  adw-gtk3's gtk-3.0/gtk.css as installed: --record reads it, --coverage says what an update moved.
  NAMES       every colour name GTK 3's own Adwaita and libadwaita define, as a kit value -- an application's own
              CSS reads them; Nemo's reads six -- and the theme's own rules paint only from @rm_* names, which no
              other sheet defines, so COSMIC's GTK export (a user sheet that redefines libadwaita's names) cannot
              repaint them (PLATFORM.md).
  RULES       what no platform declaration reaches: the type, the weights, a menu's frame, the sidebar lists, and
              Nemo's disk bars, rename box, split panes and floating status bar.
  GLYPHS      the check, the dash and the bullet, square and symbolic, so they carry no colour.
  DECLUTTER   §0's larger half -- motion -- as a second sheet the theme imports last (install.sh --no-declutter
              installs it empty). It names no colour.

    python3 build/gtk.py                  check every value, pair and adjacency in the committed theme
    python3 build/gtk.py --derive         the roles, the names, and what every platform expression became
    python3 build/gtk.py --write          regenerate the theme, the declutter, the glyphs and index.theme
    python3 build/gtk.py --record         re-record the platform from the installed adw-gtk3
    python3 build/gtk.py --coverage       the installed adw-gtk3 against the record (a report)
    python3 build/gtk.py --screen [DIR]   run Nemo on a display of its own with build/gtk_probe.c loaded, walk it,
                                          and report what GTK computed and what the photographs show (a report;
                                          needs Xvfb, a C compiler and GTK 3's headers; see README_GTK.md)
    python3 build/gtk.py --report FILE    the same report over a record already taken
"""
import collections, hashlib, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import ok, poles as P, apca, cosmic as C

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
GTKDIR = os.path.join(ROOT, 'worksafe', 'gtk')
THEME_DIR = os.path.join(GTKDIR, 'Remainder')
THEME = os.path.join(THEME_DIR, 'gtk-3.0', 'gtk.css')
DECLUTTER = os.path.join(THEME_DIR, 'gtk-3.0', 'remainder-declutter.css')
ASSETS = os.path.join(THEME_DIR, 'gtk-3.0', 'assets')
INDEX = os.path.join(THEME_DIR, 'index.theme')
INSTALLER = os.path.join(GTKDIR, 'install.sh')
RECORD = os.path.join(ROOT, 'build', 'gtk_platform.css')
SOURCE_THEME = '/usr/share/themes/adw-gtk3/gtk-3.0/gtk.css'
SOURCE_PACKAGE = 'adw-gtk-theme'

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
FLOOR = PAL['surface_floor_dE']
_T = C.terminal()


# --- 1. the roles -------------------------------------------------------------------------------------------
class R(str):
    """A kit role. The theme writes it as @rm_NAME; `none` is written as transparent."""
    def css(self):
        return 'transparent' if self == 'none' else '@rm_' + self.replace('-', '_')


class Keep(str):
    """Left as the platform wrote it, on purpose; the string says why."""


W, L, D, B = R('white'), R('light'), R('dark'), R('black')
A, S, CU = R('accent'), R('select'), R('cursor')
OK_, WN, DS = R('success'), R('warning'), R('destructive')
LL, LD = R('legend-light'), R('legend-dark')
RED, GREEN, YELLOW = R('red'), R('green'), R('yellow')
NONE = R('none')
CONTENT = Keep('content (§0a): information, read by its colour')
SHADOW = Keep('a real shadow (§4)')

# Every value the theme may define, and where it comes from. Nothing else may appear in the file but content.
ROLES = {
    'white': PAL['neutrals']['WHITE'], 'light': PAL['neutrals']['LIGHT'],
    'dark': PAL['neutrals']['DARK'], 'black': PAL['neutrals']['BLACK'],
    'accent': PAL['chrome']['ACCENT'], 'select': PAL['chrome']['SELECT'], 'cursor': PAL['chrome']['CURSOR'],
    'success': C.SEMANTIC['SUCCESS'], 'warning': C.SEMANTIC['WARNING'], 'destructive': C.SEMANTIC['DESTRUCTIVE'],
    'legend-light': '#FFFFFF', 'legend-dark': '#000000',
    # signal TEXT, from build/cosmic.py's ANSI normal tier -- the values worksafe/obsidian/, worksafe/zettlr/ and
    # worksafe/vscode/ use for it: DESTRUCTIVE on WHITE is Lc 68.2 and WARNING on WHITE 8.2, under any text tier
    'red': _T['red']['normal'][0], 'green': _T['green']['normal'][0], 'yellow': _T['yellow']['normal'][0],
}
SOURCE = {'white': '§2', 'light': '§2', 'dark': '§2', 'black': '§2', 'accent': '§2', 'select': '§2',
          'cursor': '§2', 'success': '§3', 'warning': '§3', 'destructive': '§3',
          'legend-light': '§3, legend only', 'legend-dark': '§3, legend only',
          'red': 'ansi normal red (build/cosmic.py)', 'green': 'ansi normal green (build/cosmic.py)',
          'yellow': 'ansi normal yellow (build/cosmic.py)'}
RESERVED = {'legend-light', 'legend-dark'}
# A signal text value capped by its gamut, with build/cosmic.py's note: recorded against the floor, not a defect.
CAPS = {hx: note for slot, row in _T.items() for tier, (hx, lc, note) in row.items() if note}
SIGNAL = {'success', 'warning', 'destructive', 'red', 'green', 'yellow'}
SEMANTIC_GROUNDS = {'success', 'warning', 'destructive'}
UI_FACE, MONO_FACE = 'Montserrat', 'IntoneMono Nerd Font Mono'
PX16 = '16px'


# --- 2. reading GTK's CSS -----------------------------------------------------------------------------------
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def split_top(s, sep=','):
    """Split at top-level separators: not inside (), [] or a quoted string."""
    out, depth, q, cur = [], 0, None, []
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in '"\'':
            q = ch
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == sep and depth == 0:
            out.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append(''.join(cur))
    return [x.strip() for x in out if x.strip()]


def parse_decls(body):
    out = []
    for d in split_top(body, ';'):
        if ':' not in d:
            continue
        p, v = d.split(':', 1)
        out.append((p.strip(), ' '.join(v.split())))
    return out


def parse_css(css):
    """GTK 3's dialect: @define-color, @import, @keyframes and flat rule blocks. Returns a list of items:
    ('define', name, value) | ('import', text) | ('keyframes', name, [(selector, decls)]) | ('rule', [sel], decls)."""
    s, i, out = COMMENT.sub('', css), 0, []
    while True:
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            return out
        if s.startswith('@define-color', i):
            j = s.index(';', i)
            name, value = s[i + len('@define-color'):j].strip().split(None, 1)
            out.append(('define', name, ' '.join(value.split())))
            i = j + 1
        elif s.startswith('@import', i):
            j = s.index(';', i)
            out.append(('import', s[i:j + 1]))
            i = j + 1
        elif s.startswith('@keyframes', i):
            j = s.index('{', i)
            name = s[i + len('@keyframes'):j].strip()
            depth, k = 1, j + 1
            while depth:
                depth += {'{': 1, '}': -1}.get(s[k], 0)
                k += 1
            inner, frames = s[j + 1:k - 1], []
            for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', inner):
                frames.append((m.group(1).strip(), parse_decls(m.group(2))))
            out.append(('keyframes', name, frames))
            i = k
        else:
            j = s.index('{', i)
            k = s.index('}', j)
            sels = split_top(' '.join(s[i:j].split()))
            out.append(('rule', sels, parse_decls(s[j + 1:k])))
            i = k + 1


# A colour, in GTK 3's grammar: a name, a literal, or one of its colour functions around them.
COLOUR_FUNCS = ('mix', 'alpha', 'shade', 'lighter', 'darker', 'rgba', 'rgb')
KEYWORDS = ('transparent', 'currentColor', 'white', 'black')
_FUNC = re.compile(r'(?<![\w-])(%s)\s*\(' % '|'.join(COLOUR_FUNCS))
_NAME = re.compile(r'@[A-Za-z_][\w]*')
_HEX = re.compile(r'#[0-9A-Fa-f]{3,8}\b')
_KW = re.compile(r'(?<![\w-])(%s)(?![\w-])' % '|'.join(KEYWORDS))
_SKIP = re.compile(r'(?<![\w-])(url|-gtk-icontheme)\s*\(')


def _close(s, i):
    """Index just past the parenthesis that closes the one opened at or after i."""
    depth, q, j = 0, None, s.index('(', i)
    while True:
        ch = s[j]
        if q:
            q = None if ch == q else q
        elif ch in '"\'':
            q = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1


def colour_tokens(value):
    """The top-level colour expressions in a value, as [(start, end, text)]: what the theme answers, one by one."""
    out, i = [], 0
    while i < len(value):
        m = _SKIP.match(value, i)
        if m:
            i = _close(value, i)
            continue
        for rx in (_FUNC, _NAME, _HEX, _KW):
            m = rx.match(value, i)
            if m:
                end = _close(value, i) if rx is _FUNC else m.end()
                out.append((i, end, value[i:end]))
                i = end
                break
        else:
            i += 1
    return out


def norm(tok):
    return re.sub(r'\s+', '', tok)


# --- 3. the record ------------------------------------------------------------------------------------------
def installed_version():
    try:
        out = subprocess.run(['pacman', '-Q', SOURCE_PACKAGE], capture_output=True, text=True).stdout.split()
        if len(out) == 2:
            return out[1]
    except OSError:
        pass
    try:
        out = subprocess.run(['dpkg-query', '-W', '-f=${Version}', SOURCE_PACKAGE], capture_output=True,
                             text=True).stdout.strip()
        return out or None
    except OSError:
        return None


RECORD_HEAD = """/* adw-gtk3 {version} (the `{package}` package), gtk-3.0/gtk.css, RECORDED by build/gtk.py --record from
   {path} on {date}, sha256 {sha}. Never hand-edited: the theme is written from it.
   adw-gtk3 is LGPL-2.1 (github.com/lassekongo83/adw-gtk3); LGPL-2.1 section 3 lets a copy be carried under the
   ordinary GPL, and this one is, version 3 or later, as the rest of build/ is. */
"""


def record():
    raw = open(SOURCE_THEME, 'rb').read()
    head = RECORD_HEAD.format(version=installed_version() or 'unknown', package=SOURCE_PACKAGE, path=SOURCE_THEME,
                              date=time.strftime('%Y-%m-%d'), sha=hashlib.sha256(raw).hexdigest())
    open(RECORD, 'w').write(head + raw.decode())
    print(f'recorded {SOURCE_THEME} ({len(raw)} bytes) -> {os.path.relpath(RECORD, ROOT)}')


def load_record(path=RECORD):
    text = open(path).read()
    m = re.search(r'adw-gtk3 (\S+) .*?sha256 ([0-9a-f]{64})', text, re.S)
    return parse_css(text), (m.group(1) if m else None), (m.group(2) if m else None)


# --- 4. what a selector is: its context, its element, its state ---------------------------------------------
# adw-gtk3 writes each state as a tint of the ink over the ground -- mix(fg, bg, 0.9) for a button at rest, 0.85
# hovered, 0.7 pressed; alpha(currentColor, 0.1) for a hover on a list -- so no expression means one role by
# itself: the same mix is a button on a WHITE window and a button on a LIGHT tool bar. What decides the role is
# where the element sits, what it is and what state it is in. So every selector is read for those three, and the
# kit's answer for that element in that state on that ground is what the declaration becomes. A selector whose
# element this table does not know is UNCLASSIFIED rather than guessed.
_NOT = re.compile(r':not\(((?:[^()]|\([^()]*\))*)\)')
_POSITIONAL = re.compile(r':(dir\(\w+\)|nth-child\([^)]*\)|nth-last-child\([^)]*\)|first-child|last-child|'
                         r'only-child)')


def _plain(sel):
    """The selector with its negations and positional tests removed: what it matches, not where."""
    return _POSITIONAL.sub('', _NOT.sub('', sel))


def compounds(sel):
    return [c for c in re.split(r'\s*[\s>+~]\s*', _plain(sel).strip()) if c]


def states(sel):
    """Pseudo-classes of the element itself, and :backdrop and :selected from anywhere (GTK propagates both)."""
    comps = compounds(sel)
    last = comps[-1] if comps else ''
    st = set(re.findall(r':([a-z-]+)', last.replace(':drop(active)', ':drop')))
    plain = _plain(sel)
    if ':backdrop' in plain:
        st.add('backdrop')
    if re.search(r':selected|(^|[\s>])selection\b|row:selected', plain):
        st.add('in-selected')
    negated = ' '.join(_NOT.findall(sel))
    for s in ('backdrop', 'disabled', 'hover', 'active', 'checked', 'selected'):
        if re.search(r':%s\b' % s, negated) and not re.search(r':%s\b' % s, last):
            st.add('not-' + s)
    return st


def classes(sel):
    return set(re.findall(r'\.([\w-]+)', _plain(sel)))


# The surfaces a compound can establish, and the ground each one is. An element sits on the innermost surface its
# ancestors establish; an element that IS a surface paints that surface's ground.
SURFACES = [
    ('osd', r'^(tooltip)$', r'^(osd|app-notification|touch-selection|magnifier|overlay-bar)$'),
    ('strip', r'^(headerbar)$', r'^(titlebar|default-decoration)$'),
    ('panel', r'^(toolbar|menubar|statusbar|actionbar|searchbar|infobar|stacksidebar|placessidebar|tabbar|'
              r'viewswitcherbar|header|inline-toolbar)$',
     r'^(primary-toolbar|toolbar|inline-toolbar|location-bar|sidebar|navigation-sidebar|source-list|menubar|'
     r'sidebar-pane)$'),
    ('menu', r'^(menu|popover|GraniteWidgetsPopOver)$', r'^(menu|context-menu|popup)$'),
    ('field', r'^(entry|spinbutton|textview|treeview|iconview|list|flowbox|calendar|wnck-pager|'
              r'gnc-id-sheet-list)$', r'^(view|content-view)$'),
]
LISTS = {'treeview', 'iconview', 'list', 'flowbox'}      # a field that is a list takes its panel's ground


def surface_of(compound):
    """The surface a single compound establishes, or None."""
    name = re.match(r'[\w-]*', compound).group(0)
    cls = re.findall(r'\.([\w-]+)', compound)
    for kind, el, cl in SURFACES:
        if (name and re.match(el, name)) or any(re.match(cl, c) for c in cls):
            return kind
    return None


def context(sel):
    """The ground the element sits on: the innermost surface among its ancestors, WINDOW if none."""
    comps, kind = compounds(sel), 'window'
    for c in comps[:-1]:
        k = surface_of(c)
        if k:
            kind = k
    return _qualify(kind, sel)


def own_surface(sel):
    comps = compounds(sel)
    k = surface_of(comps[-1]) if comps else None
    return _qualify(k, sel) if k else None


def _qualify(kind, sel):
    if kind == 'strip' and 'selection-mode' in classes(sel):
        kind = 'selmode'
    if kind == 'strip' and 'backdrop' in states(sel):
        kind = 'strip-back'
    return kind


CONTEXT_GROUND = {'osd': B, 'selmode': S, 'strip': A, 'strip-back': L, 'panel': L, 'menu': W, 'field': W,
                  'window': W}
DARK_GROUNDS = {A, S, B, D}


def ink_on(g):
    """The text a ground carries (§2, §3): BLACK on the light two, WHITE on the dark four, the legend on a signal."""
    if g in (DS, OK_):
        return LL
    if g == WN:
        return LD
    return W if g in DARK_GROUNDS else B


def dim_on(g):
    """Disabled text (§2 names DARK): DARK on the light grounds, Lc 79.0 on WHITE and 48.4 on LIGHT -- both over
    APCA's 30 for a disabled state -- and LIGHT on the dark ones."""
    return L if g in DARK_GROUNDS or g in (DS, OK_) else D


def element(sel):
    """What the last compound is, as the table below knows it; None if it does not."""
    comps = compounds(sel)
    if not comps:
        return None
    last, anc = comps[-1], ' '.join(comps[:-1])
    name = re.match(r'[\w-]*|\*', last).group(0)
    cls = set(re.findall(r'\.([\w-]+)', last))
    if name == 'slider':
        return ('scrollbar-slider' if re.search(r'scrollbar', anc) else
                'switch-slider' if re.search(r'switch', anc) else 'scale-slider')
    if name in ('trough', 'fill', 'highlight', 'progress', 'block'):
        if re.search(r'scrollbar', anc):
            return 'scrollbar-trough'
        if name == 'block':
            return 'level-block'
        if name == 'progress' and re.search(r'entry|spinbutton', anc):
            return 'entry-progress'
        return {'trough': 'trough', 'fill': 'fill', 'highlight': 'fill', 'progress': 'fill'}[name]
    if name == 'arrow' and re.search(r'notebook\s*>?\s*header|tabs', anc + ' ' + last):
        return 'button'
    if name in ('button', 'modelbutton') or cls & {'button', 'image-button', 'text-button', 'titlebutton',
                                                    'suggested-action', 'destructive-action', 'tab-close-button'}:
        return 'button'
    if name in ('check', 'radio'):
        return 'check'
    if name in ('entry', 'spinbutton') or 'entry' in cls:
        return 'entry'
    if name in ('switch', 'spinner', 'separator', 'selection', 'rubberband', 'tab', 'menuitem', 'row', 'label',
                'image', 'arrow', 'accelerator', 'text', 'decoration', 'window', 'tooltip', 'scrollbar',
                'progressbar', 'levelbar', 'scale', 'undershoot', 'overshoot', 'junction', 'border', 'frame',
                'expander', 'marks', 'indicator', 'value', 'placeholder', 'infobar', 'flowboxchild', 'calendar',
                'cursor-handle', 'paned', 'stack', 'notebook', 'box', 'widget', 'overlay', 'dimming', 'shadow',
                'outline', 'tabbox', 'header', 'viewport', 'actionbar', 'revealer', 'combobox', 'colorswatch',
                'avatar', 'paper', 'messagedialog', 'filechooser', 'filechooserbutton', 'keycap'):
        return name
    if name in ('entry', 'spinbutton') or 'entry' in cls:
        return 'entry'
    if surface_of(last):
        return 'surface'
    if name == '' and 'background' in cls:
        return 'window'
    if name in ('*', ''):
        return 'any'
    return None


def flags(sel):
    """Classes that change the answer wherever they sit."""
    c = classes(sel)
    f = set()
    for k in ('flat', 'suggested-action', 'destructive-action', 'error', 'warning', 'success', 'osd', 'titlebutton',
              'image-button', 'circular', 'dim-label', 'subtitle', 'separator', 'rubberband', 'needs-attention',
              'close', 'linked', 'sidebar-button', 'default', 'toggle', 'combo', 'keycap', 'badge', 'accent',
              'question', 'info', 'caption', 'monospace'):
        if k in c:
            f.add(k)
    return f


# Where a selector names no surface, adw-gtk3's colour still says which one it meant: @headerbar_fg_color is ink on
# the strip wherever the rule sits. Used only when the selector itself is silent.
TOKEN_CONTEXT = [(r'@headerbar_', 'strip'), (r'@sidebar_|@secondary_sidebar_', 'panel'), (r'@popover_', 'menu'),
                 (r'@panel_', 'osd')]


class Q:
    """A selector read once: context, own surface, element, states, flags."""
    def __init__(self, sel, value=''):
        self.sel, self.ctx, self.own = sel, context(sel), own_surface(sel)
        self.el, self.st, self.fl = element(sel), states(sel), flags(sel)
        if self.ctx == 'window':
            for rx, k in TOKEN_CONTEXT:
                if re.search(rx, value):
                    self.ctx = _qualify(k, sel)
                    break

    def has(self, *st):
        return any(s in self.st for s in st)

    @property
    def disabled(self):
        return 'disabled' in self.st

    @property
    def sits_on(self):
        """The ground under the element, if it paints none."""
        if 'in-selected' in self.st and self.el not in ('selection',):
            return S
        return CONTEXT_GROUND[self.ctx]


def button_ground(q):
    """A button's own ground, by the ground it sits on and its state (README_GTK.md, the shape). None: paints none.

      rest       a raised button is the other tone of its ground, in its BLACK outline: LIGHT on WHITE, WHITE on
                 LIGHT; a flat one paints nothing
      hover      SELECT carrying WHITE (§2), wherever the button is; on the key strip BLACK, as worksafe/obsidian/
                 does it, since SELECT on ACCENT is dE 11.8
      pressed    SELECT, as hover
      checked    ACCENT carrying WHITE: a toggle that is on (§2)
      disabled   the rest ground, its label DARK
      primary    (suggested-action) ACCENT at rest, SELECT hovered
      destructive DESTRUCTIVE carrying the legend (§3), hovered too"""
    under = q.sits_on
    if q.disabled:
        if 'flat' in q.fl or under in DARK_GROUNDS:
            return None
        return L if under == W else W
    if 'destructive-action' in q.fl and q.ctx != 'osd':
        return DS
    if 'titlebutton' in q.fl or re.search(r'titlebutton', q.sel):
        if q.has('hover', 'active'):
            return DS if 'close' in q.fl else (B if under == A else S)
        return None
    if q.has('hover', 'active', 'drop'):
        return B if under in (A, S) else S
    if q.has('checked'):
        return W if under == A else A
    if 'suggested-action' in q.fl and q.ctx != 'osd':
        return A
    if 'flat' in q.fl or under in (A, S):
        return None
    if under == B:
        return D
    return L if under == W else W


INFOBAR = {'warning': WN, 'error': DS, 'question': L, 'info': L}


def element_ground(q):
    """The ground this element paints in this state, by the kit's shape; None if it paints none."""
    el, under = q.el, q.sits_on
    if el == 'button':
        return button_ground(q)
    if el in ('selection',):
        return S
    if el == 'rubberband':
        return None
    if el == 'tooltip':
        return B
    if el in ('window', 'notebook', 'paper', 'messagedialog', 'filechooser', 'calendar'):
        return 'osd' in q.fl and B or W
    if el == 'entry':
        if q.has('selected'):
            return S
        if q.ctx == 'osd':
            return D
        return L if q.disabled else W
    if el == 'check':
        if re.search(r'(^|[\s>])(menu|popover)\b.*menuitem|modelbutton', _plain(q.sel)):
            return None
        if q.disabled:
            return L
        if q.has('checked', 'indeterminate'):
            return A if under not in (A, S) else W
        return W
    if el == 'switch':
        if q.disabled:
            return L
        return A if q.has('checked') else L
    if el in ('switch-slider', 'scale-slider'):
        return L if q.disabled else W
    if el == 'trough':
        return L if q.disabled else D
    if el == 'fill':
        return D if q.disabled else (W if under in (A, S) else A)
    if el == 'level-block':
        if q.has('disabled'):
            return L
        for k, g in (('empty', D), ('low', WN), ('high', A), ('full', OK_), ('filled', A)):
            if k in classes(q.sel):
                return g
        return A
    if el == 'scrollbar-slider':
        if q.disabled:
            return None
        return (S if q.has('active') else B if q.has('hover') else D) if under not in DARK_GROUNDS else L
    if el in ('scrollbar-trough', 'scrollbar', 'separator', 'undershoot', 'overshoot', 'junction', 'border',
              'frame', 'outline', 'decoration', 'paned', 'spinner', 'label', 'image', 'arrow', 'accelerator',
              'text', 'expander', 'value', 'placeholder', 'indicator', 'marks', 'entry-progress', 'box', 'widget',
              'overlay', 'stack', 'viewport', 'revealer', 'tabbox', 'combobox', 'filechooserbutton', 'any',
              'cursor-handle'):
        if el in ('box', 'revealer', 'widget') and q.ctx == 'panel' and re.search(r'infobar', q.sel):
            for k, g in INFOBAR.items():
                if k in classes(q.sel):
                    return g
        return None
    if el == 'keycap':
        return D
    if el == 'menuitem':
        return S if q.has('hover', 'selected') and not q.disabled else None
    if el == 'tab':
        return W if q.has('checked', 'hover') else None
    if el in ('row', 'flowboxchild', 'surface', 'header', 'infobar', 'actionbar'):
        if q.has('selected') or ('in-selected' in q.st and el != 'surface'):
            return S
        own = q.own or ('panel' if el in ('header', 'infobar', 'actionbar') else None)
        if el == 'infobar':
            for k, g in INFOBAR.items():
                if k in classes(q.sel):
                    return g
        if q.has('hover') and not q.disabled:
            # a row hovered on a LIGHT panel is WHITE, its label at 700; on a WHITE list there is no fill, since
            # LIGHT would carry BLACK at 400 at Lc 61.2 (GTK 3's own Adwaita draws none; the pointer marks the row)
            return W if under in (L,) or own == 'panel' or q.ctx == 'panel' else None
        if own is None:
            return None
        g = CONTEXT_GROUND[own]
        if own == 'field':
            name = re.match(r'[\w-]*', compounds(q.sel)[-1]).group(0)
            if (name in LISTS or 'view' in classes(compounds(q.sel)[-1])) and q.ctx == 'panel':
                g = L
            if q.ctx == 'menu':
                g = None
        return g
    return None


# --- 5. what each declaration becomes -----------------------------------------------------------------------
GROUND_PROPS = {'background-color', 'background', 'background-image'}
INK_PROPS = {'color', '-gtk-icon-palette'}
LINE_PROPS = re.compile(r'^(border|outline)(-(top|right|bottom|left))?(-color)?$|^border-image(-source)?$')
SHADOW_PROPS = {'box-shadow'}
QUIET_PROPS = {'text-shadow', '-gtk-icon-shadow'}           # a shadow under text or an icon: a blend, removed
CARET_PROPS = {'caret-color', '-gtk-secondary-caret-color'}

# Selectors whose colours are content (§0a): a picture of something, read by its colour. Left as the platform
# wrote them.
CONTENT_SELECTORS = [
    (r'(^|[\s>])avatar\b', 'an avatar\'s colour is the person\'s, generated from their name'),
    (r'\.storage-bar\b', 'a disk-usage chart: each file type is its colour (GNOME Disk Usage Analyzer)'),
    (r'scale\.(temperature|warmth)\b', 'a colour-temperature scale: its trough is a picture of the temperatures'),
    (r'(^|[\s>])colorswatch\b', 'a colour swatch shows the colour it offers'),
    (r'\.checkerboard\b', 'the checkerboard behind a translucent colour, so the alpha can be seen'),
]
SCRIM_SELECTORS = [(r'(^|[\s>])dimming\b', 'a scrim over a window while a dialog is modal (§4)')]


def meaning(tok):
    t = norm(tok)
    if t == 'transparent' or re.fullmatch(r'rgba\(\d+,\d+,\d+,0(\.0*)?\)', t) or re.search(r',0(\.0*)?\)$', t) \
            and t.startswith('alpha('):
        return 'none'
    if re.search(r'@(destructive|error)_', t):
        return 'destructive'
    if '@warning_' in t:
        return 'warning'
    if '@success_' in t:
        return 'success'
    if re.fullmatch(r'#[0-9A-Fa-f]{3,8}', t):
        return 'hex'
    if re.fullmatch(r'rgba\(0,0,[06],[0-9.]+\)|alpha\(black,[0-9.]+\)|black|@\w*shade_color|'
                    r'alpha\(@\w*shade_color,[0-9.]+\)|alpha\(rgba\(0,0,0,[0-9.]+\),[0-9.]+\)', t):
        return 'shade'
    if re.search(r'@accent_(color|bg_color)', t) and not re.search(r'@(window|view|headerbar|popover)_|currentColor',
                                                                   t):
        return 'accent'
    return 'other'


def _link(q):
    return re.search(r':(link|visited)\b', q.sel) is not None


def ink(q, tok, ground=None):
    """The text or glyph colour: the ink the ground carries (§2), a signal's text where one is meant (§3)."""
    m = meaning(tok)
    g = ground if ground not in (None, NONE) else (element_ground(q) or q.sits_on)
    if m in ('destructive', 'warning', 'success'):
        if g in (DS, WN, OK_) or 'destructive-action' in q.fl:
            return ink_on(g)
        if g in DARK_GROUNDS:
            return W
        if q.disabled:
            return dim_on(g)
        return {'destructive': RED, 'warning': YELLOW, 'success': GREEN}[m]
    if _link(q) and not q.disabled:
        return A if g == W else ink_on(g)
    if q.disabled or (q.el in ('accelerator', 'placeholder') or 'dim-label' in q.fl) and g == W:
        return dim_on(g)
    if m == 'accent' and g == W and q.el != 'selection':
        return A
    return ink_on(g)


def line(q, tok):
    """A border or an outline. Surfaces draw none -- the tone changes instead (§5); a control's outline is its own
    glyph and is BLACK, as on worksafe/obsidian/ and worksafe/vscode/; focus and a drop target are ACCENT."""
    m = meaning(tok)
    if q.el == 'rubberband':
        return S
    if m == 'destructive':
        return DS
    if m == 'warning':
        return YELLOW
    if q.has('drop') and m != 'none':
        return A
    if q.el == 'entry':
        if q.has('focus') and m != 'none':
            return A
        return D if q.disabled else B
    if q.el == 'button':
        if element_ground(q) is None:
            return NONE
        return D if q.disabled else B
    if q.el in ('check', 'switch', 'switch-slider', 'scale-slider'):
        return D if q.disabled else B
    return NONE


def outline(q):
    g = element_ground(q) or q.sits_on
    return W if g in DARK_GROUNDS or g in (DS, OK_) else A


_LEN = re.compile(r'^-?[\d.]+(px|em|pt)?$')


def shadow(q, value):
    """box-shadow, one shadow at a time: a blurred one is a real shadow (§4) and stays; a hard line is a ring, an
    indicator or a highlight, and is answered as the line it draws."""
    out = []
    for sh in split_top(value):
        toks = colour_tokens(sh)
        if not toks:
            out.append((sh, None))
            continue
        a, b, t = toks[0]
        parts = [p for p in (sh[:a] + ' ' + sh[b:]).split() if p != 'inset']
        nums = [float(re.match(r'-?[\d.]+', p).group(0)) for p in parts if _LEN.match(p)]
        x, y, blur, spread = (nums + [0, 0, 0, 0])[:4]
        m = meaning(t)
        if m == 'none':
            role = NONE
        elif blur > 0:
            role = SHADOW if m == 'shade' else NONE
        elif x == 0 and y == 0:                                   # a ring
            role = A if m == 'accent' else (DS if m == 'destructive' else YELLOW if m == 'warning' else NONE)
            if role is NONE and m == 'other' and re.search(r'@(window|view)_bg_color', t):
                role = element_ground(q) or q.sits_on
        else:                                                     # a bar on one side: an indicator, or a highlight
            role = A if m == 'accent' and q.el in ('tab', 'row', 'button', 'surface', 'header') else NONE
        out.append((sh, (a, b, role)))
    return out


def answer(sel, prop, value, ground=None):
    """[(prop, new value)] for one platform declaration under one selector, and why; or None, unclassified."""
    for rx, why in CONTENT_SELECTORS:
        if re.search(rx, sel):
            return [(prop, value)], 'CONTENT: ' + why
    for rx, why in SCRIM_SELECTORS:
        if re.search(rx, sel):
            return [(prop, value)], 'SCRIM: ' + why
    q = Q(sel, value)
    if prop == 'opacity':
        v = float(value)
        if v in (0.0, 1.0):
            return [(prop, value)], 'shown or hidden, not a blend'
        g = element_ground(q) or q.sits_on
        return [(prop, '1'), ('color', (dim_on(g) if q.el in ('label',) or q.fl & {'dim-label', 'subtitle',
                                                                                     'separator'} and g in (W, L)
                                        else ink_on(g)).css())], 'opacity is a blend: 1, and the ink named'
    if prop == '-gtk-icon-effect':
        return [(prop, 'none')], 'an icon effect is a blend'
    toks = colour_tokens(value)
    if not toks:
        return [(prop, value)], ''
    if q.el is None:
        return None
    if prop in QUIET_PROPS:
        return [(prop, 'none')], 'a shadow under text is a blend'
    if prop in CARET_PROPS:
        return [(prop, CU.css())], 'the caret is CURSOR (§2)'
    if prop == '-GtkTextView-error-underline-color':
        return [(prop, DS.css())], 'a misspelling is an error, and the meaning is present (§3)'
    if prop in SHADOW_PROPS:
        parts, new = shadow(q, value), []
        for sh, hit in parts:
            if hit is None:
                new.append(sh)
            elif hit[2] is SHADOW:
                new.append(sh)
            else:
                a, b, role = hit
                if role is NONE:
                    continue
                new.append(sh[:a] + role.css() + sh[b:])
        return [(prop, ', '.join(new) or 'none')], 'shadows: real ones kept (§4), lines answered'
    if prop in INK_PROPS:
        role = ink(q, toks[0][2], ground)
    elif prop in GROUND_PROPS:
        role = None
        m = meaning(toks[0][2])
        if 'needs-attention' in q.fl and m == 'accent':
            role = A                                    # the attention dot: a nav indicator (§2)
        elif len(toks) > 1 and m == 'shade' and re.search(r'gradient', value):
            return [(prop, 'none')], 'a shadow drawn as a gradient is a blend'
        if m in ('destructive', 'warning', 'success') and q.el not in ('button',):
            role = {'destructive': DS, 'warning': WN, 'success': OK_}[m]
        if role is None:
            role = element_ground(q) or NONE
    elif LINE_PROPS.match(prop):
        role = outline(q) if prop.startswith('outline') else line(q, toks[0][2])
    else:
        return None
    if prop in INK_PROPS and len(toks) == 1 and meaning(toks[0][2]) == 'none':
        return [(prop, value)], 'an ink made transparent hides a glyph on purpose'
    new, last = [], 0
    for a, b, t in toks:
        new.append(value[last:a])
        # several colours in one value (a gradient, a list): a transparent stop stays one; a single colour is
        # the kit's to decide, so a control the platform left without an outline gets its BLACK one
        new.append(NONE.css() if len(toks) > 1 and meaning(t) == 'none' else role.css())
        last = b
    new.append(value[last:])
    return [(prop, ''.join(new))], f'{q.el} in {q.ctx}'


# --- 6. the names applications read -------------------------------------------------------------------------
# A theme's named colours are also an interface: an application's own CSS reads @theme_bg_color and the rest, and
# Nemo's reads six of them. So the theme defines every name GTK 3's built-in Adwaita defines (the contract a GTK 3
# application was written against) and every name libadwaita, adw-gtk3 and COSMIC's own GTK export define (what
# an application written since reads), each as one of the kit's values -- and none of GNOME's palette names
# (@blue_3 and the rest), which no GTK 3 theme owes and which name poles.
NAMES = [
    ('theme_fg_color', B), ('theme_text_color', B), ('theme_bg_color', W), ('theme_base_color', W),
    ('theme_selected_bg_color', S), ('theme_selected_fg_color', W),
    ('insensitive_bg_color', W), ('insensitive_fg_color', D), ('insensitive_base_color', W),
    ('theme_unfocused_fg_color', B), ('theme_unfocused_text_color', B), ('theme_unfocused_bg_color', W),
    ('theme_unfocused_base_color', W), ('theme_unfocused_selected_bg_color', S),
    ('theme_unfocused_selected_fg_color', W), ('unfocused_insensitive_color', D),
    ('borders', NONE), ('unfocused_borders', NONE),
    ('warning_color', YELLOW), ('error_color', RED), ('success_color', GREEN),
    ('content_view_bg', W), ('text_view_bg', W),
    ('wm_title', W), ('wm_unfocused_title', B), ('wm_highlight', NONE), ('wm_borders_edge', NONE),
    ('wm_bg_a', A), ('wm_bg_b', A), ('wm_shadow', NONE), ('wm_border', NONE),
    ('wm_button_hover_color_a', B), ('wm_button_hover_color_b', B),
    ('wm_button_active_color_a', S), ('wm_button_active_color_b', S), ('wm_button_active_color_c', S),
    ('accent_bg_color', A), ('accent_fg_color', W), ('accent_color', A),
    ('destructive_bg_color', DS), ('destructive_fg_color', LL), ('destructive_color', RED),
    ('success_bg_color', OK_), ('success_fg_color', LL),
    ('warning_bg_color', WN), ('warning_fg_color', LD),
    ('error_bg_color', DS), ('error_fg_color', LL),
    ('window_bg_color', W), ('window_fg_color', B), ('view_bg_color', W), ('view_fg_color', B),
    ('headerbar_bg_color', A), ('headerbar_fg_color', W), ('headerbar_border_color', NONE),
    ('headerbar_backdrop_color', L), ('headerbar_shade_color', NONE), ('headerbar_darker_shade_color', NONE),
    ('sidebar_bg_color', L), ('sidebar_fg_color', B), ('sidebar_backdrop_color', L),
    ('sidebar_shade_color', NONE), ('sidebar_border_color', NONE),
    ('secondary_sidebar_bg_color', L), ('secondary_sidebar_fg_color', B), ('secondary_sidebar_backdrop_color', L),
    ('secondary_sidebar_shade_color', NONE), ('secondary_sidebar_border_color', NONE),
    ('card_bg_color', W), ('card_fg_color', B), ('card_shade_color', NONE),
    ('dialog_bg_color', W), ('dialog_fg_color', B),
    ('popover_bg_color', W), ('popover_fg_color', B), ('popover_shade_color', NONE),
    ('thumbnail_bg_color', W), ('thumbnail_fg_color', B),
    ('shade_color', NONE), ('scrollbar_outline_color', NONE),
    ('panel_bg_color', B), ('panel_fg_color', W),
]


# --- 7. the kit's own rules: what no platform declaration reaches ------------------------------------------
PANELS = ('toolbar', '.primary-toolbar', '.toolbar', '.inline-toolbar', '.location-bar', 'menubar', '.menubar',
          'statusbar', 'actionbar', 'searchbar', 'infobar', '.sidebar', 'placessidebar', 'stacksidebar',
          'notebook > header', 'treeview.view header button', 'headerbar', '.titlebar')
RULES = [
    ('The face and the size (§5). GTK 3 renders the desktop font at 10 pt, 13.3 px, and every floor in §0e '
     'assumes about 16 px, so the text is set at 16 px: CHOSEN, as on worksafe/obsidian/ and worksafe/zettlr/. '
     'A declared size under it is raised where it is declared (see the platform section).',
     'window, tooltip', [('font-family', f'"{UI_FACE}", sans-serif'), ('font-size', PX16)]),
    ('The caret is CURSOR everywhere (§2); a rule that names it more specifically names it CURSOR too.',
     '*', [('caret-color', CU.css()), ('-gtk-secondary-caret-color', CU.css())]),
    ('Weight follows the ground (§2): every LIGHT panel carries BLACK at 700, Lc 61.2, and the key strip WHITE at '
     '700; a WHITE field nested in one goes back to 400. A button carries its label at 700 on either face.',
     ', '.join(PANELS) + ', button', [('font-weight', 'bold')]),
    ('', 'entry, spinbutton, popover, menu, .view, textview, iconview', [('font-weight', 'normal')]),
    ('', '.sidebar .view, .sidebar treeview, .sidebar list, .sidebar row', [('font-weight', 'bold')]),
    ('A menu bar\'s items show no accelerator, but GTK builds the node: its ink is the panel\'s. Child combinators, '
     'because GTK parents a menu\'s nodes under the menu bar item that opened it.',
     'menubar > menuitem > label > accelerator, .menubar > menuitem > label > accelerator', [('color', B.css())]),
    ('A disabled label in a selected row is LIGHT on SELECT (Lc -54.8, over APCA\'s 30 for a disabled state): '
     'the platform\'s rule for a disabled label cannot see the row it is in.',
     'row:selected label:disabled, row:selected image:disabled, treeview.view:selected:disabled',
     [('color', L.css())]),
    ('A hovered row is SELECT, and its accelerator is WHITE on it with the label.',
     'menuitem:hover > label > accelerator, menuitem:selected > label > accelerator', [('color', W.css())]),
    ('The menu bar is a panel: LIGHT, BLACK at 700. adw-gtk3 paints it only in a window that is not key.',
     'menubar, .menubar', [('background-color', L.css())]),
    ('A list in a sidebar is the sidebar: LIGHT, its rows BLACK at 700, hovered WHITE, selected SELECT. adw-gtk3 '
     'says so for the sidebar layout Nemo had before 6.6 (a viewport between them); this says it for every one.',
     '.sidebar treeview.view:not(:selected), .sidebar .view:not(:selected), .sidebar list, .sidebar row:not(:selected)',
     [('background-color', L.css())]),
    ('', '.sidebar treeview.view:hover:not(:selected):not(:backdrop), .sidebar row:hover:not(:selected)',
     [('background-color', W.css())]),
    ('A menu is a LIGHT frame around WHITE rows (worksafe/obsidian/), so a separator in it is a change of '
     'tone and draws no line (§5).',
     'menu, .menu, .context-menu', [('background-color', L.css())]),
    ('', 'menu menuitem, .menu menuitem, .context-menu menuitem', [('background-color', W.css())]),
]

NEMO_RULES = [
    ('Nemo (6.6) draws the disk-usage bar under each drive in the sidebar from two style properties its own '
     'fallback sheet derives from @theme_selected_bg_color; here they are named: a DARK trough and an ACCENT '
     'fill on the LIGHT panel, a LIGHT trough and a WHITE fill on a selected row. A level, like a progress bar.',
     '.places-treeview', [('-NemoPlacesTreeView-disk-full-bg-color', D.css()),
                          ('-NemoPlacesTreeView-disk-full-fg-color', A.css())]),
    ('', '.places-treeview:selected', [('-NemoPlacesTreeView-disk-full-bg-color', L.css()),
                                        ('-NemoPlacesTreeView-disk-full-fg-color', W.css())]),
    ('The pane that is not where input goes, in a window split with F3 (Nemo\'s .nemo-inactive-pane): LIGHT, its '
     'labels at 700 -- the tone change that divides the two panes, since nothing else does (§5; issue 002), and '
     'weight following the ground (§2). adw-gtk3 and Nemo\'s own fallback both give it the window\'s ground.',
     '.nemo-window .nemo-inactive-pane .view:not(:selected), .nemo-window .nemo-inactive-pane iconview:not(:selected)',
     [('background-color', L.css()), ('font-weight', 'bold')]),
    ('The status that floats over the view when the status bar is off: a LIGHT panel, BLACK at 700.',
     '.floating-bar', [('background-color', L.css()), ('color', B.css()), ('font-weight', 'bold'),
                       ('border-color', NONE.css())]),
]


# --- 8. the writer ------------------------------------------------------------------------------------------
_RADIUS = re.compile(r'^(border(-(top|bottom)-(left|right))?-radius|-gtk-outline(-(top|bottom)-(left|right))?-radius)$')
_PT = re.compile(r'^([\d.]+)(pt|px|rem|em|%)$')


def _size_px(v):
    m = _PT.match(v)
    if not m:
        return {'smaller': 13.3, 'small': 13.3, 'x-small': 11, 'larger': 19.2, 'large': 19.2, 'x-large': 24,
                'xx-large': 32, 'medium': 16}.get(v)
    n, u = float(m.group(1)), m.group(2)
    return n * {'pt': 4 / 3, 'px': 1, 'rem': 16, 'em': 16, '%': 0.16}[u]


_GLYPH_IMAGE = re.compile(r'image\((-gtk-recolor\(url\("assets/[\w-]+\.svg"\)\)), -gtk-recolor\(url\("[^"]+\.png"\)\)\)')


def structural(prop, value):
    """What the kit changes that is not a colour, and why. None: unchanged."""
    if _GLYPH_IMAGE.search(value):
        return _GLYPH_IMAGE.sub(r'\1', value), 'the glyph is the kit\'s own square SVG; no bitmap fallback'
    if 'url("assets/' in value and '.png' in value:
        if prop == 'background-image':
            return ('image(%s)' % (L.css() if 'disabled' in value else W.css()),
                    'a slider with marks: adw-gtk3 draws a white bitmap knob; here a WHITE one, LIGHT disabled')
        return 'none', 'a bitmap of adw-gtk3\'s: the touch selection handles, not drawn'
    if _RADIUS.match(prop) and value not in ('0', '0px'):
        return '0', 'square corners, every one (PLATFORM.md COSMIC; worksafe/cosmic/remainder.ron)'
    if prop == 'font-weight':
        w = {'normal': 400, 'bold': 700}.get(value, int(value) if value.isdigit() else 400)
        if w < 400:
            return '400', 'no weight under 400: weight is safe in one direction only (§5)'
    if prop == 'font-size':
        px = _size_px(value)
        if px is not None and px < 16:
            return PX16, 'no text under the 16 px every floor assumes (§5), CHOSEN as the window\'s size is'
    return None


def keyframe(prop, value):
    """A keyframe has no selector to read, so its colours are answered by what they are: the attention dot a
    stack switcher grows (adw-gtk3's needs_attention) is ACCENT, a nav indicator (§2), on nothing."""
    toks, out, last = colour_tokens(value), [], 0
    for a, b, t in toks:
        out.append(value[last:a])
        out.append(NONE.css() if meaning(t) == 'none' else A.css() if meaning(t) == 'accent' else t)
        last = b
    out.append(value[last:])
    return ''.join(out)


def not_written(sel):
    """Selectors the theme does not carry at all, and why."""
    if re.search(r'window\.devel\b', sel):
        return 'a development build\'s striped title bar: the strip is the strip (the rules for it reach it)'
    if backdrop_only(sel):
        return 'not key, outside the strip (backdrop_only)'
    return None


def backdrop_only(sel):
    """A rule for a window that is not key, outside its strip. The kit shows key state in the strip and nowhere
    else (§2; worksafe/qt/ holds its inactive group equal to its active one for the same reason), so these are
    not written: the rules for the key window then reach both. Written, they reach further than they say --
    `button.flat:backdrop` names no :checked, so it cleared a toggled button's ACCENT and left its WHITE glyph
    on the tool bar."""
    q = Q(sel)
    return 'backdrop' in q.st and q.ctx not in ('strip-back', 'selmode') and q.own not in ('strip-back', 'selmode')


def transform(sel, decls):
    """One selector's declarations, answered: colours by role, geometry by the kit's rules. Returns
    (declarations, unclassified [(prop, value)])."""
    out, unc, ground = [], [], None
    for p, v in decls:
        if p in GROUND_PROPS and colour_tokens(v):
            r = answer(sel, p, v)
            if r:
                m = re.search(r'@rm_(\w+)', r[0][0][1])
                ground = R(m.group(1).replace('_', '-')) if m else NONE
    has_ink = any(p in INK_PROPS for p, v in decls)
    q = Q(sel)
    for p, v in decls:
        st = structural(p, v)
        if st:
            out.append((p, st[0]))
            continue
        if p == 'font-weight' and v in ('normal', '400') and q.el != 'entry' and \
                ('panel' in (q.ctx, q.own) or q.ctx == 'strip-back'):
            out.append((p, 'bold'))            # weight follows the ground (§2): 400 on a LIGHT panel is Lc 61.2
            continue
        if not colour_tokens(v) and p not in ('opacity', '-gtk-icon-effect'):
            out.append((p, v))
            continue
        r = answer(sel, p, v, ground)
        if r is None:
            unc.append((p, v))
            out.append((p, v))
            continue
        out.extend(r[0])
    if ground not in (None, NONE) and not has_ink and not any(p == 'color' for p, v in out):
        out.append(('color', ink_on(ground).css()))
    return out, unc


HEADER = """/* Remainder for GTK 3 -- the theme. GENERATED by build/gtk.py --write from build/gtk_platform.css (adw-gtk3 {ver},
   recorded {rec}) and the tables in build/gtk.py: never hand-edit; change the tables and regenerate.
   AUTHORITY.md is the authority; worksafe/gtk/README_GTK.md says what this is and what is left over.
   The only literal colours in this file are the @rm_* definitions below, and the content (§0a) that
   build/gtk.py names. */
"""


def _block(sels, decls):
    body = ''.join(f'  {p}: {v};\n' for p, v in decls)
    return ',\n'.join(sels) + ' {\n' + body + '}\n'


def _comment(text):
    import textwrap
    return ''.join('/* ' + l + ' */\n' for l in textwrap.wrap(text, 112)) if text else ''


def theme_text():
    items, ver, sha = load_record()
    rec = re.search(r'on (\d{4}-\d{2}-\d{2})', open(RECORD).read())
    out = [HEADER.format(ver=ver, rec=rec.group(1) if rec else '?')]
    out.append('\n/* --- the kit\'s values (AUTHORITY.md §2, §3; the signal text from build/cosmic.py) --- */\n')
    for k, hx in ROLES.items():
        out.append(f'@define-color rm_{k.replace("-", "_")} {hx};\n')
    out.append('\n/* --- the names applications read, each one of the kit\'s values --- */\n')
    for k, r in NAMES:
        out.append(f'@define-color {k} {r.css()};\n')
    out.append('\n/* --- the platform, answered: adw-gtk3\'s own rules, every colour by role --- */\n')
    for it in items:
        if it[0] == 'keyframes':
            _, name, frames = it
            body = ''
            for fsel, decls in frames:
                d = [(p, keyframe(p, v)) for p, v in decls]
                body += '  ' + _block([fsel], d).replace('\n', '\n  ').rstrip() + '\n'
            out.append(f'@keyframes {name} {{\n{body}}}\n')
        elif it[0] == 'rule':
            _, sels, decls = it
            groups = collections.OrderedDict()
            for sel in sels:
                if not_written(sel):
                    continue
                d, _u = transform(sel, decls)
                groups.setdefault(tuple(d), []).append(sel)
            for d, ss in groups.items():
                if d:
                    out.append(_block(ss, list(d)))
    out.append('\n/* --- the kit\'s rules: what no platform declaration reaches --- */\n')
    for note, sel, decls in RULES + NEMO_RULES:
        out.append(_comment(note))
        out.append(_block([s.strip() for s in split_top(sel)], decls))
    out.append('\n/* §0\'s larger half, motion removed: a file of its own, so it is a switch (install.sh --no-declutter). */\n')
    out.append('@import url("remainder-declutter.css");\n')
    return ''.join(out)


DECLUTTER_HEAD = """/* Remainder for GTK 3 -- the declutter (AUTHORITY.md §0): motion removed. GENERATED by build/gtk.py --write:
   every rule of the platform's that animates or transitions, answered at its own selector, so it wins by coming
   later. It names no colour. install.sh --no-declutter installs an empty file in its place. */
"""


def declutter_text():
    items, _, _ = load_record()
    out = [DECLUTTER_HEAD]
    seen = []
    for it in items:
        if it[0] != 'rule':
            continue
        _, sels, decls = it
        d = []
        if any(p.startswith('transition') for p, v in decls):
            d.append(('transition', 'none'))
        if any(p.startswith('animation') for p, v in decls):
            d.append(('animation', 'none'))
        if d:
            seen.append((sels, d))
    for sels, d in seen:
        out.append(_block(sels, d))
    return ''.join(out)


INDEX_TEXT = """[Desktop Entry]
Type=X-GNOME-Metatheme
Name=Remainder
Comment=Remainder for GTK 3: adw-gtk3's rules, every colour answered by role (build/gtk.py)
Encoding=UTF-8

[X-GNOME-Metatheme]
GtkTheme=Remainder
"""

# The three glyphs a check box and a radio button draw. Symbolic: GTK paints them in the element's ink, so the
# files carry no colour at all. Square, as every corner is (the bullet included).
GLYPHS = {
    'check-symbolic.svg': '<path d="M3.5 8.5 6.5 11.5 12.5 4.5" fill="none" stroke-width="2"/>',
    'dash-symbolic.svg': '<rect x="3" y="7" width="10" height="2"/>',
    'bullet-symbolic.svg': '<rect x="5" y="5" width="6" height="6"/>',
}


def glyph_text(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
            + body.replace('stroke-width', 'stroke="#bebebe" stroke-width') + '</svg>\n')


def write():
    os.makedirs(ASSETS, exist_ok=True)
    open(THEME, 'w').write(theme_text())
    open(DECLUTTER, 'w').write(declutter_text())
    open(INDEX, 'w').write(INDEX_TEXT)
    for name, body in GLYPHS.items():
        open(os.path.join(ASSETS, name), 'w').write(glyph_text(body))
    print(f'wrote {os.path.relpath(THEME, ROOT)}, {os.path.relpath(DECLUTTER, ROOT)}, {os.path.relpath(INDEX, ROOT)}, '
          f'{len(GLYPHS)} glyphs')



# --- 8b. the gate -------------------------------------------------------------------------------------------
# The shape, as pairs: every ink the theme puts on a ground, at the tier the weight it renders at demands. GTK 3
# lets a theme set weight, so LIGHT carries BLACK at 700 wherever it is a ground for text (the rules), and every
# WHITE field goes back to 400.
PAIRS = [
    (B, W, 75, 'the window, a view, a list, a field, a menu row, a dialog: BLACK at 400'),
    (B, L, 60, 'a LIGHT panel at 700: menu bar, tool bar, sidebar, status bar, column headers, tab strip, the '
               'strip of a window that is not key, the inactive pane of a split'),
    (W, A, 60, 'the key strip\'s title at 700; its buttons\' glyphs'),
    (W, A, 75, 'the primary button, a toggled button, a checked box\'s tick: WHITE at 400 clears the body tier too'),
    (W, S, 75, 'a selected row, selected text, a hovered button or menu row'),
    (W, B, 75, 'a tooltip; a hovered button on the key strip; an OSD'),
    (W, D, 75, 'a key cap; an entry on an OSD'),
    (D, W, 75, 'an accelerator, a placeholder, a dim label: DARK at 400'),
    (A, W, 75, 'a link, underlined (§3), and the flat primary button\'s label'),
    (RED, W, 75, 'error text, an entry marked in error'),
    (GREEN, W, 75, 'success text'),
    (YELLOW, W, 75, 'warning text, at the ANSI yellow\'s gamut cap (build/cosmic.py)'),
    (LL, DS, 60, 'a destructive button, an error bar, the close button hovered: §3\'s legend'),
    (LL, OK_, 60, 'a success bar: §3\'s legend'),
    (LD, WN, 60, 'a warning bar: §3\'s legend'),
    (D, W, 30, 'disabled text on WHITE (APCA\'s tier for a disabled state)'),
    (D, L, 30, 'disabled text on LIGHT, and a disabled glyph on a panel'),
    (L, A, 30, 'disabled text on the key strip'),
    (CU, W, 60, 'the caret: §2\'s own pair and its own floor'),
    (A, W, 30, 'focus, a nav indicator, a toggle\'s fill, a progress fill, a drop target: marks'),
    (A, L, 30, 'the same marks on a panel: the disk bar\'s fill in the sidebar, the zoom slider\'s fill'),
    (B, W, 30, 'a control\'s outline and glyph on the field'),
    (B, L, 30, 'a control\'s outline and glyph on a panel'),
    (D, W, 30, 'a trough, a scrollbar\'s thumb, the disk bar\'s trough'),
    (D, L, 30, 'the same on a panel'),
    (S, W, 30, 'a rubber band\'s outline'),
    (DS, W, 30, 'an error\'s mark: an entry\'s outline, a misspelling\'s underline'),
    (YELLOW, W, 30, 'a warning\'s mark: an entry\'s outline'),
]
# Grounds that touch with nothing drawn between them, and must read as two (§2's SURFACE_FLOOR). No line is
# drawn between surfaces: the tone changes instead (§5).
ADJACENT = [
    (W, L, 'a view against the sidebar, the tool bar, the status bar, the inactive pane; a menu row against its '
           'frame; a button against the window'),
    (L, A, 'the tool bar or menu bar against the key strip'),
    (W, A, 'a field in the key strip'),
    (S, W, 'a selected row among the others'),
    (S, L, 'a selected row in the sidebar'),
    (A, W, 'the primary button, a toggled button, a checked box on the field'),
    (A, L, 'a toggled button on a panel'),
    (D, W, 'a trough on the field'),
    (D, L, 'a trough on a panel'),
    (B, W, 'a tooltip over the window'),
]
EXEMPT_ADJACENT = {('S', 'A'): 'ACCENT/SELECT: selection reads against the rows around it (§2)'}


# The names Nemo 6.6's own sheets read (nemo-style-fallback.css, -fallback-mandatory.css, -application.css, at
# the 6.6.4 tag): each must be one the theme defines, or Nemo's own rules resolve to nothing.
NEMO_NAMES = ('theme_bg_color', 'theme_fg_color', 'theme_selected_bg_color', 'theme_selected_fg_color',
              'theme_unfocused_bg_color', 'borders')


def check_names(text, errs):
    defined = dict(re.findall(r'@define-color\s+(\w+)\s+([^;]+);', text))
    for k, hx in ROLES.items():
        n = 'rm_' + k.replace('-', '_')
        if defined.get(n, '').upper() != hx.upper():
            errs.append(f'@define-color {n} is {defined.get(n)!r}, palette says {hx}')
    for k, r in NAMES:
        if defined.get(k) != r.css():
            errs.append(f'@define-color {k} is {defined.get(k)!r}, the names table says {r.css()}')
    for k in NEMO_NAMES:
        if k not in defined:
            errs.append(f'@{k} is read by Nemo\'s own sheets and the theme does not define it')
    extra = set(defined) - {'rm_' + k.replace('-', '_') for k in ROLES} - {k for k, _ in NAMES}
    for k in sorted(extra):
        errs.append(f'@define-color {k} is in the theme and in no table')
    return defined


def check():
    errs, notes = [], []
    # 1. the files are what the tables produce
    for path, want in ((THEME, theme_text()), (DECLUTTER, declutter_text()), (INDEX, INDEX_TEXT)):
        have = open(path).read() if os.path.exists(path) else None
        if have != want:
            errs.append(f'{os.path.relpath(path, ROOT)} is not what the tables produce: run --write')
    for name, body in GLYPHS.items():
        f = os.path.join(ASSETS, name)
        if not os.path.exists(f) or open(f).read() != glyph_text(body):
            errs.append(f'glyph {name} is not what the table produces')
        elif re.search(r'fill="#|fill:\s*#', open(f).read()):
            errs.append(f'glyph {name} names a fill colour: it must be symbolic')
    text = open(THEME).read()
    check_names(text, errs)
    # 2. every platform declaration answered
    items, ver, sha = load_record()
    unc = []
    for it in items:
        if it[0] == 'rule':
            for sel in it[1]:
                unc += [(sel, p, v) for p, v in transform(sel, it[2])[1]]
    for sel, p, v in unc:
        errs.append(f'NOT CLASSIFIED BY ANY ROW: {sel} {{ {p}: {v} }}')
    # 3. every value in the theme's rules a kit name, transparent, or content left as it was on purpose
    kept, blends = collections.Counter(), []
    body = parse_css(text)
    for it in body:
        if it[0] != 'rule':
            continue
        for sel in it[1]:
            content = any(re.search(rx, sel) for rx, _ in CONTENT_SELECTORS + SCRIM_SELECTORS)
            for p, v in it[2]:
                for a, b, t in colour_tokens(v):
                    t = norm(t)
                    if t == 'transparent' or re.fullmatch(r'@rm_\w+', t):
                        continue
                    if content:
                        kept['content'] += 1
                        continue
                    if p == 'box-shadow' and meaning(t) == 'shade':
                        kept['shadow'] += 1
                        continue
                    errs.append(f'{sel} {{ {p}: {v} }}: {t} is not a kit value')
                roles = {norm(t) for a, b, t in colour_tokens(v)} - {'transparent'}
                if len(roles) > 1 and not content and p != 'box-shadow':
                    errs.append(f'{sel} {{ {p}: {v} }}: a gradient between two values is a blend')
                elif len(roles) == 1 and 'transparent' in v and re.search(r'gradient', v) and not content:
                    blends.append((sel, p))
                if p == 'opacity' and 0 < float(v) < 1 and not content:
                    errs.append(f'{sel} {{ opacity: {v} }}: an opacity is a blend')
                if p == 'font-size' and (_size_px(v) or 99) < 16:
                    errs.append(f'{sel} {{ font-size: {v} }}: under the 16 px the floors assume')
                if p == 'font-weight' and v not in ('normal', 'bold') and v.isdigit() and int(v) < 400:
                    errs.append(f'{sel} {{ font-weight: {v} }}: under 400')
                if _RADIUS.match(p) and v not in ('0', '0px'):
                    errs.append(f'{sel} {{ {p}: {v} }}: every corner is square')
                if '@rm_legend' in v and p == 'color':
                    g = element_ground(Q(sel)) or Q(sel).sits_on
                    grounds = {m for m in re.findall(r'@rm_(\w+)', ' '.join(x for q, x in it[2]
                                                                            if q in GROUND_PROPS))}
                    if g not in (DS, OK_, WN) and not grounds & {'destructive', 'success', 'warning'}:
                        errs.append(f'{sel}: §3\'s legend on a ground that is not one of §3\'s three')
    # 4. the values: chrome clears every pole; the signals are the signals; the legends are legend
    for k, hx in ROLES.items():
        if k in RESERVED or k in SIGNAL:
            continue
        if not P.clear(hx):
            errs.append(f'{k} {hx}: {P.report(hx)}')
    # 5. the pairs and the adjacencies
    for ink_, gr, need, why in PAIRS:
        lc = apca.lc(ROLES[ink_], ROLES[gr])
        if abs(lc) < need:
            if ROLES[ink_] in CAPS:
                notes.append(f'{ink_} on {gr}: Lc {lc:.1f} under {need}, at its gamut cap -- {CAPS[ROLES[ink_]]}')
            else:
                errs.append(f'{ink_} on {gr}: Lc {lc:.1f} under {need} -- {why}')
    for a_, b_, why in ADJACENT:
        de = ok.delta_e(ROLES[a_], ROLES[b_])
        if de < FLOOR - 0.05:
            errs.append(f'{a_}/{b_}: dE {de:.1f} under the surface floor {FLOOR} -- {why}')
    # 6. the declutter names no colour
    if colour_tokens(COMMENT.sub('', open(DECLUTTER).read())):
        errs.append('the declutter names a colour')
    print(f'build/gtk.py: the GTK 3 theme against adw-gtk3 {ver} (recorded, sha256 {sha[:12]})')
    print(f'  {sum(1 for i in items if i[0] == "rule")} platform rules, every declaration answered; '
          f'{len(unc)} unclassified')
    print(f'  left as the platform wrote them: {kept["content"]} content values (§0a), {kept["shadow"]} real '
          f'shadows (§4); {len(blends)} gradients from one kit value to nothing (an indicator\'s soft edge)')
    print(f'  {len(PAIRS)} pairs, {len(ADJACENT)} adjacencies measured')
    for ink_, gr, need, why in PAIRS:
        print(f'    {ink_:>12} on {gr:<12} Lc {apca.lc(ROLES[ink_], ROLES[gr]):6.1f}  (floor {need})')
    for a_, b_, why in ADJACENT:
        print(f'    {a_:>12} / {b_:<12} dE {ok.delta_e(ROLES[a_], ROLES[b_]):5.1f}  (floor {FLOOR})')
    for n in notes:
        print('  RECORDED', n)
    for e in errs:
        print('  DEFECT', e)
    print('gtk: every declaration answered; every value, pair and adjacency clears' if not errs
          else f'gtk: {len(errs)} defects')
    return not errs


# --- 9. the screen: what a running application computed ----------------------------------------------------
# build/gtk_probe.c, loaded into the application, writes each window's CSS node tree with the style GTK computed
# for every node and the stylesheet line each value came from. Read here, measured here.
PROBE_C = os.path.join(ROOT, 'build', 'gtk_probe.c')
_RGB = re.compile(r'rgba?\((\d+),(\d+),(\d+)(?:,([\d.]+))?\)')
_PROPLINE = re.compile(r'^(\s*)([-a-z]+): (.*); /\* (.*?) \*/$')
TEXT_NODES = {'label', 'entry', 'text', 'accelerator', 'treeview', 'iconview', 'textview', 'spinbutton',
              'calendar', 'cellview'}
INHERITED = {'color', 'font-size', 'font-weight', 'font-family'}


class Node:
    __slots__ = ('decl', 'depth', 'props', 'kids', 'parent', 'hidden')

    def __init__(self, decl, depth, parent):
        self.decl, self.depth, self.parent = decl, depth, parent
        self.props, self.kids = {}, []
        self.hidden = decl.startswith('[')

    @property
    def name(self):
        return re.match(r'\[?([\w-]*)', self.decl).group(1)

    def get(self, prop):
        """A property's computed value: its own, or an inherited one from the nearest ancestor that sets it."""
        n = self
        while n:
            if prop in n.props:
                return n.props[prop]
            if prop not in INHERITED:
                return None
            n = n.parent
        return None

    def path(self):
        out, n = [], self
        while n:
            out.append(n.decl.split(':')[0].strip('[]'))
            n = n.parent
        return ' > '.join(reversed(out))

    def paint(self):
        """The ground this node paints, as an (r, g, b) if opaque, else None."""
        for p in ('background-color', 'background-image'):
            v = self.props.get(p)
            if not v:
                continue
            for m in _RGB.finditer(v[0]):
                a = float(m.group(4)) if m.group(4) else 1.0
                if a > 0.99:
                    return tuple(int(x) for x in m.group(1, 2, 3))
        return None

    def ground(self):
        n = self
        while n:
            g = n.paint()
            if g:
                return g, n
            n = n.parent
        return None, None


def parse_tree(text):
    """One %%css block: indentation is depth (two spaces a level), a property line belongs to the node above it."""
    root, stack = None, []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _PROPLINE.match(line)
        if m:
            if stack:
                stack[-1].props[m.group(2)] = (m.group(3), m.group(4))
            continue
        depth = (len(line) - len(line.lstrip(' '))) // 2
        while stack and stack[-1].depth >= depth:
            stack.pop()
        node = Node(line.strip(), depth, stack[-1] if stack else None)
        if node.parent:
            node.parent.kids.append(node)
        else:
            root = node
        stack.append(node)
    return root


def parse_probe(path):
    """[(record label, window title, window type, root Node, [widget lines])], every record in the file."""
    out, cur, win = [], None, None
    lines = open(path).read().split('\n')
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('%%record'):
            cur = l.split(' ', 2)[1]
        elif l.startswith('%%window'):
            parts = l.split(' ', 6)
            win = {'type': parts[1], 'title': parts[6] if len(parts) > 6 else '', 'widgets': [], 'state': None}
        elif l.startswith('%%state'):
            win = dict(win, state=l.split(' ', 1)[1], widgets=[])
        elif l.startswith('W ') and win is not None:
            win['widgets'].append(l)
        elif l == '%%css':
            j = lines.index('%%endcss', i)
            out.append((cur, win.get('state'), win['title'], win['type'], parse_tree('\n'.join(lines[i + 1:j])),
                        list(win['widgets'])))
            i = j
        i += 1
    return out


def _hex(rgb):
    return '#%02X%02X%02X' % rgb


def role_of(rgb):
    hx = _hex(rgb)
    for k, v in ROLES.items():
        if v.upper() == hx:
            return k
    return None


def tier(size_px, weight):
    """The Lc a text needs at its rendered size and weight (build/apca.py's guidance; §0e)."""
    if weight >= 700:
        return 60 if size_px >= 16 else 75
    if size_px >= 24:
        return 60
    return 75 if size_px >= 16 else 90


def _px(v):
    m = re.match(r'([\d.]+)px', v or '')
    return float(m.group(1)) if m else 16.0


def _weight(v):
    try:
        return int(re.match(r'\d+', v).group(0))
    except (TypeError, AttributeError):
        return {'bold': 700, 'normal': 400}.get(v, 400)


def _disabled(n):
    """Disabled text is held to APCA's 30, the tier it names for a disabled state (build/apca.py)."""
    while n:
        if ':disabled' in n.decl:
            return True
        n = n.parent
    return False


def _tail(path, k=4):
    return ' > '.join(re.sub(r'#\w+|\[\d+/\d+\]', '', x) for x in path.split(' > ')[-k:])


def measure_tree(root, where):
    """Every painted value off the ladder, and every text pair under its tier, in one computed tree."""
    off, pairs = [], []
    stack = [root]
    while stack:
        n = stack.pop()
        stack.extend(n.kids)
        if n.hidden:
            continue
        for p, (v, src) in n.props.items():
            if p in ('box-shadow', 'text-shadow', '-gtk-icon-shadow') and 'px' in v:
                continue                                                      # judged by build/gtk.py, not here
            for m in _RGB.finditer(v):
                a = float(m.group(4)) if m.group(4) else 1.0
                if a == 0:
                    continue
                rgb = tuple(int(x) for x in m.group(1, 2, 3))
                if a < 1 or role_of(rgb) is None:
                    off.append((where, n.path(), p, m.group(0), src))
        glyph = n.name == 'image' or n.name in ('check', 'radio', 'arrow', 'expander', 'spinner')
        if n.name in TEXT_NODES or glyph or re.search(r'\.(title|subtitle)\b', n.decl):
            col = n.get('color')
            g, gn = n.ground()
            if not col or not g:
                continue
            cm = _RGB.search(col[0])
            if not cm:
                continue
            ink = tuple(int(x) for x in cm.group(1, 2, 3))
            size, weight = _px((n.get('font-size') or ('16px', ''))[0]), _weight((n.get('font-weight') or ('400', ''))[0])
            lc = apca.lc(_hex(ink), _hex(g))
            need = 30 if _disabled(n) or glyph else tier(size, weight)   # a glyph is a mark (§0e): 30
            if abs(lc) < need:
                pairs.append((where, n.path(), _hex(ink), role_of(ink), _hex(g), role_of(g), round(lc, 1), need,
                              size, weight, col[1]))
    return off, pairs


def screen_report(path):
    recs = parse_probe(path)
    offs, pairs = collections.OrderedDict(), collections.OrderedDict()
    for label, state, title, typ, root, widgets in recs:
        where = f'{title or typ}' + (f' [{state}]' if state else '')
        o, p = measure_tree(root, where)
        for x in o:
            offs.setdefault((_tail(x[1]), x[2], x[3]), x)
        for x in p:
            pairs.setdefault((_tail(x[1]), x[2], x[4]), x)
    print(f'{len(recs)} trees read from {path}')
    print(f'\nOFF THE LADDER ({len(offs)}): a painted value that is not one of the kit\'s')
    for (where, npath, p, v, src) in offs.values():
        print(f'  {v:22s} {p:24s} {src:22s} {npath[-110:]}  [{where}]')
    print(f'\nUNDER ITS TIER ({len(pairs)}): text whose Lc on its ground is under what its size and weight need')
    for (where, npath, ink, ir, g, gr, lc, need, size, weight, src) in pairs.values():
        print(f'  {ink} ({ir}) on {g} ({gr})  Lc {lc:6.1f} < {need}  {size:.0f}px/{weight}  ink {src}  '
              f'{npath[-90:]}  [{where}]')
    return offs, pairs


# The photograph: what the computed styles cannot see -- what GTK draws itself, a glyph's colour, a picture. The
# method is build/zettlr.py's: a readable hue (chroma at C_FLOOR or more) must belong to a family the kit paints --
# the home hue, CURSOR's, a signal's -- and be no more chromatic than the kit's own member of it, since a blend of
# two kit values gains at most 0.0074. Content is left out: the file views (every icon in them is the file's) and
# any image larger than a symbolic one.
FAMILIES = {'home': ('accent', 'select'), 'cursor': ('cursor',), 'success': ('success', 'green'),
            'warning': ('warning', 'yellow'), 'destructive': ('destructive', 'red')}
HUE_REACH = {'home': 20, 'cursor': 20}
FAMILY_SLACK = 0.015
CONTENT_WIDGETS = re.compile(r'^Nemo(Icon|List|Compact)View|\.nemo-window-pane .*treeview')


def _widgets(lines):
    out = []
    for l in lines:
        parts = l.split(' ', 8)
        if len(parts) < 9:
            continue
        _, depth, typ, x, y, w, h, flags, path = parts
        out.append((typ, int(x), int(y), int(w), int(h), path))
    return out


def photo_check(shot, windows, top=6):
    """[(line)] for one photograph and the windows recorded with it: [(origin, size, widget lines)]."""
    from PIL import Image
    im = np.asarray(Image.open(shot).convert('RGB')).astype(float)
    H, Wd = im.shape[:2]
    _, chroma, hue = ok.lch_grid(im)                      # ok.lch_grid takes 0-255, as ok.rgb gives
    mask = np.zeros(chroma.shape, bool)
    for (ox, oy), (ww, wh), widgets in windows:
        mask[max(0, oy):min(H, oy + wh), max(0, ox):min(Wd, ox + ww)] = True
        for typ, x, y, w, h, path in widgets:
            if CONTENT_WIDGETS.search(typ + ' ' + path) or (typ == 'GtkImage' and max(w, h) > 32):
                mask[max(0, oy + y):max(0, oy + y + h), max(0, ox + x):max(0, ox + x + w)] = False
    hued = (chroma >= P.C_FLOOR) & mask
    ceiling = np.full(chroma.shape, -1.0)
    for fam, roles in FAMILIES.items():
        for role in roles:
            _, c0, h0 = ok.lch(ROLES[role])
            near = np.abs((hue - h0 + 180) % 360 - 180) <= HUE_REACH.get(fam, 12)
            ceiling = np.where(near, np.maximum(ceiling, c0 + FAMILY_SLACK), ceiling)
    lines, fams = [], {}
    for fam, roles in FAMILIES.items():
        if fam == 'home':
            continue
        n = 0
        for role in roles:
            _, c0, h0 = ok.lch(ROLES[role])
            n += int((hued & (np.abs((hue - h0 + 180) % 360 - 180) <= HUE_REACH.get(fam, 12))).sum())
        if n:
            fams[fam] = n
    if fams:
        lines.append('hues on screen outside the home family, which must be where their meaning is: '
                     + ', '.join(f'{f} {n} px' for f, n in fams.items()))
    for what, m in (("off the kit's hues", hued & (ceiling < 0)),
                    ("more chromatic than the kit's own", hued & (ceiling >= 0) & (chroma > ceiling))):
        ys, xs = np.nonzero(m)
        if not len(xs):
            continue
        cells, first, counts = np.unique((ys // 40) * 100000 + xs // 40, return_index=True, return_counts=True)
        for i in np.argsort(-counts)[:top]:
            x, y = int(xs[first[i]]), int(ys[first[i]])
            r, g, b = (int(v) for v in im[y, x])
            where = next((f'{typ} {path.split(" ")[-1]}' for (ox, oy), _, ws in windows
                          for typ, wx, wy, w, h, path in reversed(ws)
                          if ox + wx <= x < ox + wx + w and oy + wy <= y < oy + wy + h), '?')
            lines.append(f'{counts[i]:6} px {what} near ({x},{y}), e.g. #{r:02X}{g:02X}{b:02X} hue {hue[y, x]:5.1f} '
                         f'C {chroma[y, x]:.3f}  {where[-90:]}')
    return lines


def photo_report(record_path, shots_dir, names):
    """Each state's photograph against the windows its record holds (the k-th rest record is the k-th state)."""
    recs, cur, k = [], None, -1
    for l in open(record_path).read().split('\n'):
        if l.startswith('%%record rest'):
            k += 1
            cur = []
            recs.append(cur)
        elif l.startswith('%%record'):
            cur = None
        elif l.startswith('%%window') and cur is not None:
            p = l.split(' ', 6)
            cur.append([(int(p[2]), int(p[3])), (int(p[4]), int(p[5])), []])
        elif l.startswith('W ') and cur:
            cur[-1][2].append(l)
    total = 0
    print('\nPHOTOGRAPHED: every readable hue in the chrome, against the kit\'s families (content left out)')
    for name, wins in zip(names, recs):
        shot = os.path.join(shots_dir, name + '.png')
        if not os.path.exists(shot):
            continue
        lines = photo_check(shot, [(o, sz, _widgets(ws)) for o, sz, ws in wins])
        total += len(lines)
        for line in lines:
            print(f'  {name:18s} {line}')
    if not total:
        print('  every readable hue in every state is one the kit paints')
    return total


# --- 10. the pass: an application on a display of its own, walked --------------------------------------------
# Nothing here touches the user's desktop: a virtual X display (Xvfb), a session bus of its own with no portals
# (so no desktop service answers for the application), settings in memory (GSETTINGS_BACKEND=memory, so nothing is
# written to dconf), and a profile directory that holds the theme -- a link to worksafe/gtk/Remainder, so the pass
# is of the committed files -- the user's fonts and fontconfig, and a folder of sample files. GTK 3 on X draws its
# own title bar only when a compositing window manager says it supports _GTK_FRAME_EXTENTS, so a stand-in claims
# that (--qa-wm); nothing composites, so a shadow's transparent margin photographs black and is not the theme's.
QA_DISPLAY = ':77'
SAMPLE_DIRS = ('Desktop', 'Documents', 'Downloads', 'Music', 'Pictures', 'Projects', 'Public', 'Templates', 'Videos')
SAMPLE_FILES = {'notes.txt': 'hi\n', 'data.csv': 'a,b\n1,2\n', 'script.sh': '#!/bin/sh\necho hi\n',
                'README.md': '# readme\n', '.hidden': ''}


def _gsetting(key, default):
    try:
        v = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', key], capture_output=True,
                           text=True, timeout=5).stdout.strip().strip("'")
        return v or default
    except (OSError, subprocess.TimeoutExpired):
        return default


def qa_env(qa):
    """The profile: every path under qa/, nothing written outside it."""
    home = os.path.expanduser('~')
    for d in ('data/themes', 'config/gtk-3.0', 'files', 'dbus-services', 'shots'):
        os.makedirs(os.path.join(qa, d), exist_ok=True)
    links = {os.path.join(qa, 'data/themes/Remainder'): os.path.abspath(THEME_DIR),
             os.path.join(qa, 'data/fonts'): os.path.join(home, '.local/share/fonts'),
             os.path.join(qa, 'config/fontconfig'): os.path.join(home, '.config/fontconfig')}
    for link, target in links.items():
        if os.path.islink(link):
            os.unlink(link)
        if os.path.exists(target):
            os.symlink(target, link)
    open(os.path.join(qa, 'config/gtk-3.0/settings.ini'), 'w').write(
        '[Settings]\ngtk-theme-name=Remainder\ngtk-icon-theme-name=%s\ngtk-font-name=%s 12\n'
        % (_gsetting('icon-theme', 'Adwaita'), UI_FACE))
    for d in SAMPLE_DIRS:
        os.makedirs(os.path.join(qa, 'files', d), exist_ok=True)
    for f, body in SAMPLE_FILES.items():
        open(os.path.join(qa, 'files', f), 'w').write(body)
    for svc in ('org.gtk.vfs.Daemon', 'org.gtk.vfs.Metadata', 'org.gtk.vfs.UDisks2VolumeMonitor'):
        src = f'/usr/share/dbus-1/services/{svc}.service'
        if os.path.exists(src):
            open(os.path.join(qa, 'dbus-services', svc + '.service'), 'w').write(open(src).read())
    sock = f'/tmp/gtkqa-{os.getuid()}'
    os.makedirs(sock, exist_ok=True)
    open(os.path.join(qa, 'session.conf'), 'w').write(f"""<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <type>session</type>
  <keep_umask/>
  <listen>unix:tmpdir={sock}</listen>
  <servicedir>{os.path.join(qa, 'dbus-services')}</servicedir>
  <policy context="default"><allow send_destination="*" eavesdrop="true"/><allow eavesdrop="true"/><allow own="*"/></policy>
</busconfig>
""")


def qa_wm():
    """Stand in for a compositing, EWMH window manager on the QA display, and nothing more (see above)."""
    import ctypes, ctypes.util
    X = ctypes.CDLL(ctypes.util.find_library('X11'))
    vp, ul, c = ctypes.c_void_p, ctypes.c_ulong, ctypes
    X.XOpenDisplay.restype = vp; X.XOpenDisplay.argtypes = [c.c_char_p]
    X.XDefaultRootWindow.restype = ul; X.XDefaultRootWindow.argtypes = [vp]
    X.XInternAtom.restype = ul; X.XInternAtom.argtypes = [vp, c.c_char_p, c.c_int]
    X.XCreateSimpleWindow.restype = ul
    X.XCreateSimpleWindow.argtypes = [vp, ul, c.c_int, c.c_int, c.c_uint, c.c_uint, c.c_uint, ul, ul]
    X.XSetSelectionOwner.argtypes = [vp, ul, ul, ul]
    X.XChangeProperty.argtypes = [vp, ul, ul, ul, c.c_int, c.c_int, c.c_void_p, c.c_int]
    X.XFlush.argtypes = [vp]
    d = X.XOpenDisplay(QA_DISPLAY.encode())
    root = X.XDefaultRootWindow(d)
    w = X.XCreateSimpleWindow(d, root, 0, 0, 1, 1, 0, 0, 0)
    atom = lambda n: X.XInternAtom(d, n, 0)
    X.XSetSelectionOwner(d, atom(b'_NET_WM_CM_S0'), w, 0)
    wid = (ul * 1)(w)
    for target in (root, w):
        X.XChangeProperty(d, target, atom(b'_NET_SUPPORTING_WM_CHECK'), atom(b'WINDOW'), 32, 0, wid, 1)
    X.XChangeProperty(d, w, atom(b'_NET_WM_NAME'), atom(b'UTF8_STRING'), 8, 0, b'gtkqa', 5)
    hints = [b'_GTK_FRAME_EXTENTS', b'_NET_WM_STATE', b'_NET_ACTIVE_WINDOW', b'_NET_SUPPORTING_WM_CHECK',
             b'_NET_WM_MOVERESIZE', b'_GTK_SHOW_WINDOW_MENU', b'_NET_WM_STATE_FOCUSED']
    arr = (ul * len(hints))(*[atom(h) for h in hints])
    X.XChangeProperty(d, root, atom(b'_NET_SUPPORTED'), atom(b'ATOM'), 32, 0, arr, len(hints))
    X.XFlush(d)
    while True:
        time.sleep(3600)


class Input:
    """Pointer and keys on the QA display through XTest. It opens QA_DISPLAY by name and never the session's
    $DISPLAY, which is the user's own desktop."""
    ALIAS = {'ctrl': 'Control_L', 'shift': 'Shift_L', 'alt': 'Alt_L', 'super': 'Super_L', 'esc': 'Escape',
             'enter': 'Return'}

    def __init__(self):
        import ctypes, ctypes.util
        self.c = ctypes
        X = self.X = ctypes.CDLL(ctypes.util.find_library('X11'))
        T = self.T = ctypes.CDLL(ctypes.util.find_library('Xtst'))
        vp, ul = ctypes.c_void_p, ctypes.c_ulong
        X.XOpenDisplay.restype = vp; X.XOpenDisplay.argtypes = [ctypes.c_char_p]
        X.XStringToKeysym.restype = ul; X.XStringToKeysym.argtypes = [ctypes.c_char_p]
        X.XKeysymToKeycode.restype = ctypes.c_ubyte; X.XKeysymToKeycode.argtypes = [vp, ul]
        X.XSync.argtypes = [vp, ctypes.c_int]
        X.XSetInputFocus.argtypes = [vp, ul, ctypes.c_int, ul]
        T.XTestFakeMotionEvent.argtypes = [vp, ctypes.c_int, ctypes.c_int, ctypes.c_int, ul]
        T.XTestFakeButtonEvent.argtypes = [vp, ctypes.c_uint, ctypes.c_int, ul]
        T.XTestFakeKeyEvent.argtypes = [vp, ctypes.c_uint, ctypes.c_int, ul]
        self.d = X.XOpenDisplay(QA_DISPLAY.encode())
        if not self.d:
            raise SystemExit(f'cannot open the QA display {QA_DISPLAY}')

    def cm_owned(self):
        X, c = self.X, self.c
        X.XInternAtom.restype = c.c_ulong; X.XInternAtom.argtypes = [c.c_void_p, c.c_char_p, c.c_int]
        X.XGetSelectionOwner.restype = c.c_ulong; X.XGetSelectionOwner.argtypes = [c.c_void_p, c.c_ulong]
        return X.XGetSelectionOwner(self.d, X.XInternAtom(self.d, b'_NET_WM_CM_S0', 0)) != 0

    def _sync(self):
        self.X.XSync(self.d, 0)
        time.sleep(0.15)

    def focus(self):
        self.X.XSetInputFocus(self.d, 1, 1, 0)        # PointerRoot: keys go to the window under the pointer
        self._sync()

    def move(self, x, y):
        self.T.XTestFakeMotionEvent(self.d, -1, int(x), int(y), 0)
        self._sync()

    def click(self, x, y, button=1):
        self.move(x, y)
        self.T.XTestFakeButtonEvent(self.d, button, 1, 0); self._sync()
        self.T.XTestFakeButtonEvent(self.d, button, 0, 0); self._sync()

    def key_window(self, title):
        """Make the toplevel whose name is `title` the key window, and every other one not: _NET_WM_STATE_FOCUSED
        on it and off the rest, which is how GTK 3 on X learns focus from a window manager that advertises it."""
        c, X = self.c, self.X
        vp, ul = c.c_void_p, c.c_ulong
        X.XDefaultRootWindow.restype = ul; X.XDefaultRootWindow.argtypes = [vp]
        X.XInternAtom.restype = ul; X.XInternAtom.argtypes = [vp, c.c_char_p, c.c_int]
        X.XQueryTree.argtypes = [vp, ul, c.POINTER(ul), c.POINTER(ul), c.POINTER(c.POINTER(ul)), c.POINTER(c.c_uint)]
        X.XFetchName.argtypes = [vp, ul, c.POINTER(c.c_char_p)]
        X.XChangeProperty.argtypes = [vp, ul, ul, ul, c.c_int, c.c_int, c.c_void_p, c.c_int]
        root = X.XDefaultRootWindow(self.d)
        r, p, kids, n = ul(), ul(), c.POINTER(ul)(), c.c_uint()
        X.XQueryTree(self.d, root, c.byref(r), c.byref(p), c.byref(kids), c.byref(n))
        state, focused, atom_t = (X.XInternAtom(self.d, b'_NET_WM_STATE', 0),
                                  X.XInternAtom(self.d, b'_NET_WM_STATE_FOCUSED', 0), X.XInternAtom(self.d, b'ATOM', 0))
        for i in range(n.value):
            nm = c.c_char_p()
            X.XFetchName(self.d, kids[i], c.byref(nm))
            if not nm.value:
                continue
            on = nm.value.decode(errors='replace') == title
            arr = (ul * 1)(focused)
            X.XChangeProperty(self.d, kids[i], state, atom_t, 32, 0, arr, 1 if on else 0)
        self._sync()

    def key(self, combo):
        codes = [self.X.XKeysymToKeycode(self.d, self.X.XStringToKeysym(self.ALIAS.get(k.lower(), k).encode()))
                 for k in combo.split('+')]
        for k in codes:
            self.T.XTestFakeKeyEvent(self.d, k, 1, 0); self._sync()
        for k in reversed(codes):
            self.T.XTestFakeKeyEvent(self.d, k, 0, 0); self._sync()


# The states walked, by keyboard where Nemo has a key for it, since a key reaches the same place on any screen
# size. Each is recorded (every window's computed tree) and photographed. Hover, press and the rest of a widget's
# states are put on every widget by the probe itself (SIGUSR2), and the window's not-key state with them.
APP_TITLE = 'files'                # Nemo titles its window after the folder, and the pass opens one called files
HOME_POINTER = (1000, 746)         # over the main window's status bar, which no dialog the walk opens covers
M = ('move', HOME_POINTER)
NEMO_WALK = [
    ('rest', []),
    ('selected', [('key', 'Home')]),
    ('rename', [('key', 'F2')]),
    ('context-menu', [('key', 'Escape'), ('key', 'shift+F10')]),
    ('menu-bar', [('key', 'Escape'), ('key', 'F10')]),
    ('menu-hover', [('key', 'Down'), ('key', 'Down')]),
    ('list-view', [('key', 'Escape'), ('key', 'Escape'), ('key', 'ctrl+2')]),
    ('compact-view', [('key', 'ctrl+3')]),
    ('location-entry', [('key', 'ctrl+1'), ('key', 'ctrl+l')]),
    ('split', [('key', 'Escape'), ('key', 'F3')]),
    ('tabs', [('key', 'F3'), ('key', 'ctrl+t')]),
    ('search', [('key', 'ctrl+w'), ('key', 'ctrl+f')]),
    ('hidden-files', [('key', 'Escape'), ('key', 'ctrl+h')]),
    ('no-statusbar', [('key', 'ctrl+h'), ('key', 'ctrl+slash')]),
    ('not-key', [('key', 'ctrl+slash'), ('key-window', 'nothing')]),
    ('connect-to-server', [('key-window', APP_TITLE), M, ('key', 'F10'), ('key', 'Down'), ('key', 'Down'),
                           ('key', 'Down'), ('key', 'Down'), ('key', 'Down'), ('key', 'Return'),
                           ('key-window', 'Connect to Server')]),
    ('properties', [('key-window', APP_TITLE), M, ('key', 'Home'), ('key', 'alt+Return'),
                    ('key-window', 'files Properties')]),
    ('preferences', [('key-window', APP_TITLE), M, ('key', 'F10'), ('key', 'Right'), ('key', 'Up'),
                     ('key', 'Return'), ('key-window', 'File Management Preferences')]),
]


def _sh(cmd, **kw):
    return subprocess.run(cmd, shell=False, capture_output=True, text=True, **kw)


def _pids(pattern):
    """PIDs whose command line STARTS with pattern: an unanchored match finds the shell running the search."""
    out = _sh(['pgrep', '-f', '^' + pattern]).stdout.split()
    return [int(p) for p in out if int(p) != os.getpid()]


def screen(qa, app='nemo', walk=None):
    """Run the pass: build the profile, the display and the probe, start the application, walk it, report."""
    import shutil, signal
    qa = os.path.abspath(qa)
    qa_env(qa)
    probe_so, record_path = os.path.join(qa, 'libremainderprobe.so'), os.path.join(qa, 'probe.txt')
    cflags = _sh(['pkg-config', '--cflags', '--libs', 'gtk+-3.0']).stdout.split()
    r = _sh(['cc', '-shared', '-fPIC', '-O2', '-Wall', '-o', probe_so, PROBE_C] + cflags)
    if r.returncode:
        raise SystemExit('the probe did not compile:\n' + r.stderr)
    if not _pids(f'Xvfb {QA_DISPLAY}'):
        subprocess.Popen(['setsid', '-f', 'Xvfb', QA_DISPLAY, '-screen', '0', '1600x1000x24', '-nolisten', 'tcp'])
        time.sleep(1.5)
    if not _pids(f'{sys.executable} {os.path.abspath(__file__)} --qa-wm'):
        subprocess.Popen(['setsid', '-f', sys.executable, os.path.abspath(__file__), '--qa-wm'])
    for _ in range(60):                  # this module takes seconds to import: wait until the stand-in owns the display
        if Input().cm_owned():
            break
        time.sleep(0.5)
    else:
        raise SystemExit('the stand-in window manager did not start: GTK would draw no title bar')
    for p in _pids(f'{app} --geometry'):
        os.kill(p, signal.SIGTERM)
    if os.path.exists(record_path):
        os.remove(record_path)
    for f in os.listdir(os.path.join(qa, 'shots')):
        os.remove(os.path.join(qa, 'shots', f))
    env = {k: v for k, v in os.environ.items() if k not in ('WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS',
                                                             'GTK_THEME', 'GTK_MODULES', 'GTK_DEBUG')}
    env.update(DISPLAY=QA_DISPLAY, GDK_BACKEND='x11', GSETTINGS_BACKEND='memory', GTK_CSD='1', NO_AT_BRIDGE='1',
               GTK_USE_PORTAL='0', XDG_DATA_HOME=os.path.join(qa, 'data'),
               XDG_CONFIG_HOME=os.path.join(qa, 'config'), GTK_DEBUG='interactive', GTK_MODULES=probe_so,
               REMAINDER_PROBE_OUT=record_path)
    log = open(os.path.join(qa, 'app.log'), 'w')
    subprocess.Popen(['setsid', '-f', 'dbus-run-session', '--config-file', os.path.join(qa, 'session.conf'), '--',
                      app, '--geometry=1100x720+40+30', os.path.join(qa, 'files')], env=env, stdout=log, stderr=log)
    time.sleep(6)
    pids = _pids(f'{app} --geometry')
    if not pids:
        raise SystemExit(f'{app} did not start; see {qa}/app.log')
    pid, inp = pids[0], Input()
    inp.move(*HOME_POINTER)
    inp.focus()
    inp.key_window(APP_TITLE)

    def snap(name):
        if not _pids(f'{app} --geometry'):
            raise ProcessLookupError(f'{app} exited before "{name}"; see {qa}/app.log')
        os.kill(pid, signal.SIGUSR1)
        time.sleep(1.2)
        _sh(['import', '-display', QA_DISPLAY, '-window', 'root', os.path.join(qa, 'shots', name + '.png')])

    walked = 0
    try:
        for name, steps in (walk or NEMO_WALK):
            for kind, arg in steps:
                if kind == 'key':
                    inp.key(arg)
                elif kind == 'move':
                    inp.move(*arg)
                elif kind == 'key-window':
                    inp.key_window(arg)
                time.sleep(0.5)
            time.sleep(0.8)
            snap(name)
            walked += 1
    except ProcessLookupError as e:
        print('WALK STOPPED:', e)
    if _pids(f'{app} --geometry'):
        inp.key('Escape')
        os.kill(pid, signal.SIGUSR2)
    size = -1
    for _ in range(120):                       # the sweep restyles every widget five times over: wait for it to end
        time.sleep(2)
        now = os.path.getsize(record_path)
        if now == size and open(record_path, 'rb').read()[-6:] == b'%%end\n':
            break
        size = now
    for p in _pids(f'{app} --geometry'):
        os.kill(p, signal.SIGTERM)
    print(f'walked {walked} of {len(walk or NEMO_WALK)} states of {app}; photographs in {qa}/shots\n')
    out = screen_report(record_path)
    photo_report(record_path, os.path.join(qa, 'shots'), [n for n, _ in (walk or NEMO_WALK)][:walked])
    return out


def derive():
    print('the values the theme may name (the only literal colours in it, with the content below):')
    for k, hx in ROLES.items():
        print(f'  @rm_{k.replace("-", "_"):14s} {hx}  {SOURCE[k]}')
    print('\nthe names applications read, as kit values:')
    for k, r in NAMES:
        print(f'  @{k:36s} {r.css()}')
    items, ver, sha = load_record()
    answers, dropped = collections.Counter(), collections.Counter()
    for it in items:
        if it[0] != 'rule':
            continue
        for sel in it[1]:
            why = not_written(sel)
            if why:
                dropped[why] += 1
                continue
            for p, v in it[2]:
                if not colour_tokens(v):
                    continue
                r = answer(sel, p, v)
                if r:
                    new = ' '.join(x[1] for x in r[0])
                    for tok in sorted(set(re.findall(r'@rm_\w+|transparent', new))) or ['(kept)']:
                        answers[(norm(colour_tokens(v)[0][2]) if colour_tokens(v) else v, tok)] += 1
    print(f'\nselectors not written ({sum(dropped.values())}):')
    for why, n in dropped.items():
        print(f'  {n:4d}  {why}')
    print(f'\nevery platform expression, and what it became across all its selectors (adw-gtk3 {ver}):')
    by = collections.defaultdict(list)
    for (expr, tok), n in answers.items():
        by[expr].append(f'{tok.replace("@rm_", "")} {n}')
    for expr in sorted(by, key=lambda e: -sum(int(x.rsplit(' ', 1)[1]) for x in by[e])):
        print(f'  {expr[:60]:60s} -> {", ".join(by[expr])}')
    print('\nthe content left as the platform wrote it (§0a):')
    for rx, why in CONTENT_SELECTORS + SCRIM_SELECTORS:
        print(f'  {rx:32s} {why}')


def coverage():
    """The installed adw-gtk3 against the record: the same file, or which rules an update added or dropped."""
    if not os.path.exists(SOURCE_THEME):
        print(f'{SOURCE_THEME} is not installed: nothing to compare (the gate runs on the record)')
        return
    raw = open(SOURCE_THEME, 'rb').read()
    items, ver, sha = load_record()
    now = hashlib.sha256(raw).hexdigest()
    print(f'recorded adw-gtk3 {ver} sha256 {sha[:12]}; installed {installed_version()} sha256 {now[:12]}')
    if now == sha:
        print('the installed build is the recorded one')
        return
    rec = {(tuple(i[1]), tuple(i[2])) for i in items if i[0] == 'rule'}
    inst = {(tuple(i[1]), tuple(i[2])) for i in parse_css(raw.decode()) if i[0] == 'rule'}
    print(f'{len(inst - rec)} rules new or changed in the installed build, {len(rec - inst)} gone; re-record with '
          f'--record, --write, and look at what the gate says')
    for sels, decls in list(inst - rec)[:40]:
        print('  +', ', '.join(sels)[:110])


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--record' in a:
        record()
    elif '--derive' in a:
        derive()
    elif '--coverage' in a:
        coverage()
    elif '--write' in a:
        write()
    elif '--qa-wm' in a:
        qa_wm()
    elif '--screen' in a:
        i = a.index('--screen')
        screen(a[i + 1] if len(a) > i + 1 else os.path.join(os.environ.get('TMPDIR', '/tmp'), 'remainder-gtk-qa'))
    elif '--report' in a:
        rec = a[a.index('--report') + 1]
        screen_report(rec)
        photo_report(rec, os.path.join(os.path.dirname(rec), 'shots'), [n for n, _ in NEMO_WALK])
    else:
        sys.exit(0 if check() else 1)
