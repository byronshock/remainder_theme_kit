"""The Zettlr surface: record the platform, write the theme, then check what is committed. AUTHORITY.md is the
authority.

Zettlr is Electron, so its windows are web pages, and it loads one stylesheet of the user's last in every one of
them: custom.css in its data directory, linked after all of its own. `@import` works there, so the theme is a
stylesheet of its own that custom.css imports -- install.sh writes the lines between markers -- and the declutter
is a second import beside it. Three things measured off the installed build (the CachyOS `zettlr` package, 4.8.0
on electron43, 2026-09-25) shape it:

  THERE IS NOTHING TO SET. Obsidian paints from variables; Zettlr paints from literals: 1,449 declarations that
    put a colour or a type on the screen, in 76 stylesheets across fourteen windows, and the CSS CodeMirror
    writes at run time for each of five editor themes. A theme that set variables would reach a fraction of it.
    So the platform is RECORDED (build/zettlr_platform.css, from the installed app and a running window of it),
    every recorded declaration is CLASSIFIED by role, and the theme MIRRORS each one: the same selector, one
    class higher, scoped to the windows that load it, carrying the kit's value for its role. What no declaration
    reaches -- the browser's own defaults, grounds left to show through, ink that has to follow a ground the
    mirror moved -- THE RULES set.

  THE WINDOW DOES NOT SAY WHEN IT IS KEY. Nothing in the page changes with focus, and the window buttons are
    Electron's, drawn over Zettlr's toolbar in fixed dark symbols no stylesheet reaches. So Zettlr shows no key
    state (PLATFORM.md), as COSMIC cannot, and the theme does not pretend to.

  THE UI RENDERS UNDER THE SIZE THE FLOORS ASSUME. Zettlr sets its chrome at 10 to 15 px, and every floor in §0e
    assumes about 16 (§5). So the chrome's text is set at 16 px (CHOSEN, as on worksafe/obsidian/), and what that
    costs is written down where it happens: the About window's six tabs take two rows, a few fixed-width buttons
    cut their labels short, the settings' list of pages is cut at its default width.

So the surface is a record, a role table and a mirror (CONTRIBUTING.md §8):

  THE RECORD  Zettlr's own CSS, trimmed to what paints: --record reads it out of app.asar and a running window,
              and the checker fails on any declaration no row classifies. --coverage says what an update moved.
  ROLES       every declaration on one of the kit's fifteen values: §2's seven, §3's three and their two
              legends, and build/cosmic.py's ANSI normal tier for signal text, as on worksafe/obsidian/. Weight
              follows the ground: a LIGHT panel carries BLACK at 700 (Lc 61.2), a WHITE field 400 (Lc 91.8).
  THE MIRROR  each override at its platform rule's own selector with `:root` in front, and :where(:has(...))
              naming the windows whose bundle loads that rule, so an override meant for one window reaches no
              other and still ranks exactly as the rule it answers.
  TOKENS      the code colouring worksafe/vscode/ chose (§0c): keywords and tags BLACK and bold, comments DARK
              and italic, literals ACCENT, names SELECT.
  SETTINGS    config.json pins light mode and Zettlr's own frame, which the theme is built on.
  DECLUTTER   §0's larger half -- motion and blur -- as a second stylesheet, so it is a switch
              (install.sh --no-declutter). It names no colour.

    python3 build/zettlr.py                  check every value, pair and adjacency in the committed theme
    python3 build/zettlr.py --derive         Zettlr's grey ramp snapped to §2's four, and the roles it may name
    python3 build/zettlr.py --write          regenerate the theme and the declutter from the record and the tables
    python3 build/zettlr.py --record P       re-record the platform from the installed build and a Zettlr whose
                                             DevTools port is P (it switches editor themes, and puts them back)
    python3 build/zettlr.py --coverage       the installed build's stylesheets against the record (a report)
    python3 build/zettlr.py --screen P [W]   what a running Zettlr paints, in every window or in window W: the
                                             computed styles, and the window photographed (a report; see
                                             worksafe/zettlr/README_ZETTLR.md)
"""
import base64, glob, hashlib, io, json, os, re, socket, struct, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import ok, poles as P, apca, cosmic as C

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ZET = os.path.join(ROOT, 'worksafe', 'zettlr')
THEME = os.path.join(ZET, 'remainder.css')
SNIPPET = os.path.join(ZET, 'remainder-declutter.css')
SETTINGS = os.path.join(ZET, 'config.json')
INSTALLER = os.path.join(ZET, 'install.sh')
RECORD = os.path.join(ROOT, 'build', 'zettlr_platform.css')

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
FLOOR = PAL['surface_floor_dE']
_T = C.terminal()


# --- 1. the roles -------------------------------------------------------------------------------------------
class R(str):
    """A kit role. The theme writes it as var(--rm-NAME); `none` is written as transparent."""
    def css(self):
        return 'transparent' if self == 'none' else f'var(--rm-{self})'


class Keep(str):
    """Left to the platform on purpose; the string says why."""


class InPlace(R):
    """The role, drawn into the platform's own geometry: a gradient that draws a shape keeps the shape."""


class Lit(str):
    """A keyword that is not a colour -- inherit -- written as it is."""


W, L, D, B = R('white'), R('light'), R('dark'), R('black')
A, S, CU = R('accent'), R('select'), R('cursor')
OK_, WN, DS = R('success'), R('warning'), R('destructive')
LL, LD = R('legend-light'), R('legend-dark')
RED, GREEN, YELLOW = R('red'), R('green'), R('yellow')
NONE = R('none')
INHERIT = Lit('inherit')
CONTENT = Keep('content (§0a): information, read by its colour')
SHADOW = Keep('a real shadow (§4)')
SCRIM = Keep('a scrim over content while it loads (§4)')

# Every value the theme may define, and where it comes from. Nothing else may appear in the file.
ROLES = {
    'white': PAL['neutrals']['WHITE'], 'light': PAL['neutrals']['LIGHT'],
    'dark': PAL['neutrals']['DARK'], 'black': PAL['neutrals']['BLACK'],
    'accent': PAL['chrome']['ACCENT'], 'select': PAL['chrome']['SELECT'], 'cursor': PAL['chrome']['CURSOR'],
    'success': C.SEMANTIC['SUCCESS'], 'warning': C.SEMANTIC['WARNING'], 'destructive': C.SEMANTIC['DESTRUCTIVE'],
    'legend-light': '#FFFFFF', 'legend-dark': '#000000',
    # signal TEXT and warning MARKS, from build/cosmic.py's ANSI normal tier -- the values worksafe/obsidian/ and
    # worksafe/vscode/ use for it: WARNING on WHITE is Lc 8.0, so a warning that has to be read or found is yellow
    'red': _T['red']['normal'][0], 'green': _T['green']['normal'][0], 'yellow': _T['yellow']['normal'][0],
}
SOURCE = {'white': '§2', 'light': '§2', 'dark': '§2', 'black': '§2', 'accent': '§2', 'select': '§2',
          'cursor': '§2', 'success': '§3', 'warning': '§3', 'destructive': '§3',
          'legend-light': '§3, legend only', 'legend-dark': '§3, legend only',
          'red': 'ansi normal red (build/cosmic.py)', 'green': 'ansi normal green (build/cosmic.py)',
          'yellow': 'ansi normal yellow (build/cosmic.py)'}
RESERVED = {'legend-light', 'legend-dark'}
SIGNAL = {'success', 'warning', 'destructive', 'red', 'green', 'yellow'}   # a pole here is the meaning, present
SEMANTIC_GROUNDS = {'success', 'warning', 'destructive'}
CAPS = {hx: note for slot, row in _T.items() for tier, (hx, lc, note) in row.items() if note}

# §5's type: the two faces, and the size every contrast floor in §0e assumes. Zettlr sets its chrome at 10 to 15
# px; measured at the 16 px tiers those pairs would pass on paper and not on the screen, so the chrome's text is
# set at 16 px (CHOSEN, as on worksafe/obsidian/) and the tier the checker applies is the tier on the screen.
FACES = {'ui': '"Montserrat", sans-serif', 'mono': '"Hack", monospace'}
UI, MONO = 'ui', 'mono'
PX16 = '16px'


# --- 2. Zettlr's own stylesheets, read off the installed build ---------------------------------------------
# Zettlr is webpacked: every stylesheet a window loads is a string inside that window's bundle, pushed by
# css-loader (`e.push([e.id, "...css...", ""])`) and inserted by style-loader at the end of <head> when the
# bundle runs. CodeMirror is the exception: its styles are JavaScript objects turned into CSS at run time, so
# they are read off a running window instead (record(), below). ASARS lists where each packaging keeps the app.
ASARS = ('/usr/lib/zettlr/app.asar', '/opt/Zettlr/resources/app.asar', '/usr/lib/zettlr/resources/app.asar',
         '/var/lib/flatpak/app/com.zettlr.Zettlr/current/active/files/zettlr/resources/app.asar',
         os.path.expanduser('~/.local/share/flatpak/app/com.zettlr.Zettlr/current/active/files/zettlr/resources/app.asar'))
WINDOWS = ('main_window', 'preferences', 'assets', 'about', 'error', 'log_viewer', 'onboarding', 'paste_image',
           'print', 'project_properties', 'splash_screen', 'stats', 'tag_manager', 'update')


def installed_asar():
    return next((p for p in ASARS if os.path.exists(p)), None)


def asar_index(path):
    """The asar's file index: a pickled header length, a JSON index, then the files at base + offset."""
    f = open(path, 'rb')
    _, hsize, _, jlen = struct.unpack('<4I', f.read(16))
    return json.loads(f.read(jlen)), 8 + hsize


def asar_read(path, member):
    index, base = asar_index(path)
    node = index
    for part in member.split('/'):
        node = node['files'][part]
    if node.get('unpacked'):
        return open(path + '.unpacked/' + member, 'rb').read()
    with open(path, 'rb') as f:
        f.seek(base + int(node['offset']))
        return f.read(node['size'])


_PUSH = re.compile(r'\.push\(\[\s*[A-Za-z_$][\w$]*\.id\s*,\s*')


def js_string(src, i):
    """The JavaScript string literal that starts at src[i], unescaped, and where it ends. A template
    literal's interpolations -- webpack's asset URLs -- come back as ${}."""
    q, out, j = src[i], [], i + 1
    while True:
        c = src[j]
        if c == '\\':
            n = src[j + 1]
            if n in 'ntr':
                out.append({'n': '\n', 't': '\t', 'r': '\r'}[n]); j += 2
            elif n == 'u' and src[j + 2] == '{':
                k = src.index('}', j); out.append(chr(int(src[j + 3:k], 16))); j = k + 1
            elif n == 'u':
                out.append(chr(int(src[j + 2:j + 6], 16))); j += 6
            elif n == 'x':
                out.append(chr(int(src[j + 2:j + 4], 16))); j += 4
            elif n == '\n':
                j += 2
            else:
                out.append(n); j += 2
        elif c == q:
            return ''.join(out), j + 1
        elif q == '`' and c == '$' and src[j + 1] == '{':
            depth, k = 1, j + 2
            while depth:
                depth += {'{': 1, '}': -1}.get(src[k], 0); k += 1
            out.append('${}'); j = k
        else:
            out.append(c); j += 1


def bundle_sheets(js):
    """Every stylesheet css-loader pushes in one window's bundle, in the order style-loader inserts them."""
    out = []
    for m in _PUSH.finditer(js):
        if js[m.end()] in '"\'`':
            out.append(js_string(js, m.end())[0])
    return out


# --- 3. a CSS reader: nesting flattened, @media kept -----------------------------------------------------------
# Zettlr writes some of its Vue components' styles with native nesting (`#menubar { &[data-v-..] { } }`), so a
# rule's selector is only known once its parents are resolved: `&` is the parent, and anything else is a
# descendant of it. @media and @supports wrap the rules inside them; @keyframes and @font-face paint nothing a
# theme overrides and are skipped whole.
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def split_top(s, sep=','):
    out, depth, cur, q = [], 0, '', None
    for c in s:
        if q:
            cur += c
            q = None if c == q else q
            continue
        if c in '"\'':
            q = c
        elif c in '([':
            depth += 1
        elif c in ')]':
            depth -= 1
        if c == sep and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += c
    out.append(cur)
    return [' '.join(x.split()) for x in out if x.strip()]


def _nest(parents, sel):
    if not parents:
        return split_top(sel)
    return [s.replace('&', p) if '&' in s else f'{p} {s}' for p in parents for s in split_top(sel)]


def parse_css(css):
    """[(media, selector, property, value, important)], one row per selector of a selector list."""
    css, out, n = COMMENT.sub('', css), [], None
    n = len(css)

    def skip_block(j):
        depth = 1
        while depth:
            depth += {'{': 1, '}': -1}.get(css[j], 0); j += 1
        return j

    def emit(decl, parents, media):
        if ':' not in decl or not parents:
            return
        prop, val = decl.split(':', 1)
        prop, val = prop.strip(), ' '.join(val.split())
        imp = bool(re.search(r'!\s*important$', val))
        val = re.sub(r'\s*!\s*important$', '', val)
        prop = prop if prop.startswith('--') else prop.lower()
        for s in parents:
            out.append((media, s, prop, val, imp))

    def block(i, parents, media):
        buf = ''
        while i < n:
            c = css[i]
            if c == '{':
                head, buf = buf.strip(), ''
                if head.startswith('@'):
                    kw = head.split()[0].lower()
                    if kw in ('@media', '@supports', '@container', '@layer'):
                        i = block(i + 1, parents, f'{media} and {head}' if media else head)
                    else:
                        i = skip_block(i + 1)
                    continue
                i = block(i + 1, _nest(parents, head), media)
                continue
            if c in ';}':
                emit(buf.strip(), parents, media)
                buf = ''
                i += 1
                if c == '}':
                    return i
                continue
            if c in '"\'':
                j = css.index(c, i + 1)
                buf += css[i:j + 1]; i = j + 1
                continue
            if c == '(':
                depth, j = 1, i + 1
                while depth:
                    depth += {'(': 1, ')': -1}.get(css[j], 0); j += 1
                buf += css[i:j]; i = j
                continue
            buf += c; i += 1
        return i

    block(0, [], '')
    return out


# What is recorded: every declaration that puts a colour on the screen, and the two type properties the theme
# overrides in the platform's own rules (§5). A colour is a literal, a colour function, a named colour, a
# variable, or a colour spelled inside an image (a data URI's %23rrggbb) -- CodeMirror draws its lint marks so.
HEX = re.compile(r'#[0-9A-Fa-f]{3,8}\b')
FUNC = re.compile(r'\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark)\s*\(', re.I)
DATA_HEX = re.compile(r'%23[0-9A-Fa-f]{3,8}\b')
NAMED = {'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond',
         'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral',
         'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray',
         'darkgreen', 'darkgrey', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred',
         'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise',
         'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick', 'floralwhite',
         'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow',
         'grey', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush',
         'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgray',
         'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray',
         'lightslategrey', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon',
         'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue',
         'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose',
         'moccasin', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid',
         'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink',
         'plum', 'powderblue', 'purple', 'rebeccapurple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon',
         'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey',
         'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat',
         'white', 'whitesmoke', 'yellow', 'yellowgreen',
         # CSS system colours: the platform's, and never the kit's
         'accentcolor', 'accentcolortext', 'activetext', 'buttonborder', 'buttonface', 'buttontext', 'canvas',
         'canvastext', 'field', 'fieldtext', 'graytext', 'highlight', 'highlighttext', 'linktext', 'mark',
         'marktext', 'selecteditem', 'selecteditemtext', 'visitedtext'}
PAINT = re.compile(r'^(color|background(-color|-image)?|border(-(top|right|bottom|left|block|inline)(-(start|end))?)?'
                   r'(-color)?|outline(-color)?|box-shadow|text-shadow|fill|stroke|caret-color|accent-color|'
                   r'text-decoration(-color)?|text-emphasis(-color)?|column-rule(-color)?|scrollbar-color|'
                   r'-webkit-text-fill-color|-webkit-text-stroke(-color)?|filter|content|--.*)$')
TYPE = ('font-size', 'font-family')


def colours_in(value):
    """The colours a declared value names, in the order it names them. var() references are separate."""
    bare = re.sub(r'var\([^()]*(\([^()]*\)[^()]*)*\)', ' ', value)
    found = HEX.findall(bare) + [m.group(0) + '...)' for m in FUNC.finditer(bare)] + DATA_HEX.findall(bare)
    words = re.findall(r'(?<![\w#%-])([A-Za-z][A-Za-z-]*)(?![\w-]*\()', re.sub(r'url\([^)]*\)', ' ', bare))
    found += [w for w in words if w.lower() in NAMED]
    if 'url(' in bare:                                    # a data URI spells its colours by name as well
        for u in re.findall(r'url\(([^)]*)\)', bare):
            text = urllib.parse.unquote(u)
            found += [w for w in re.findall(r'(?:fill|stroke|stop-color)\s*=\s*["\']?([A-Za-z]+)', text)
                      if w.lower() in NAMED]
    return found


def colour_vars(rows):
    """The custom properties that hold a colour: declared with one, or with a var() of one, to a fixpoint.
    A variable named for a font holds a face, even when the face is Crimson."""
    decls = {}
    for media, sel, prop, val, imp in rows:
        if prop.startswith('--') and 'font' not in prop:
            decls.setdefault(prop, []).append(val)
    found, grew = set(), True
    while grew:
        grew = False
        for name, vals in decls.items():
            if name not in found and any(colours_in(v) or set(re.findall(r'var\(\s*(--[\w-]+)', v)) & found
                                         for v in vals):
                found.add(name); grew = True
    return found


def paints(prop, value, cvars):
    """True if this declaration puts a colour of its own on the screen, directly or through a variable."""
    if not PAINT.match(prop) or (prop.startswith('--') and 'font' in prop):
        return False
    return bool(colours_in(value) or set(re.findall(r'var\(\s*(--[\w-]+)', value)) & cvars)


# The body classes Zettlr sets are its platform (darwin, win32, linux), dark and fullscreen. A selector that
# needs darwin or win32 cannot match on this platform and is not recorded; one that only excludes them --
# `body:not(.darwin)` -- can, and is.
def matches_here(sel):
    return not re.search(r'\.(darwin|win32)\b', re.sub(r':not\([^()]*\)', '', sel))


# --- 4. the DevTools port: how the checker reads a running Zettlr ----------------------------------------------
# Zettlr passes Chromium's switches through (`zettlr --remote-debugging-port=P`), and every window -- the main
# one and each auxiliary window -- is a target on that port. A client over a websocket, stdlib only.
class Page:
    def __init__(self, target):
        self.target = target
        hostport, path = target['webSocketDebuggerUrl'].split('://', 1)[1].split('/', 1)
        host, port = hostport.split(':')
        self.s = socket.create_connection((host, int(port)), timeout=120)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f'GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                        f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.rest, self.n = buf.split(b'\r\n\r\n', 1)[1], 0

    @property
    def window(self):
        """main_window, preferences, assets, ...: the renderer directory the target was loaded from."""
        m = re.search(r'/renderer/([a-z_]+)/', self.target.get('url', ''))
        return m.group(1) if m else self.target.get('title', '?')

    def _read(self, k):
        while len(self.rest) < k:
            self.rest += self.s.recv(1 << 20)
        out, self.rest = self.rest[:k], self.rest[k:]
        return out

    def call(self, method, **params):
        self.n += 1
        data = json.dumps({'id': self.n, 'method': method, 'params': params}).encode()
        hdr = bytearray([0x81])
        k = len(data)
        hdr += bytes([0x80 | k]) if k < 126 else (bytes([0x80 | 126]) + struct.pack('>H', k) if k < 65536
                                                  else bytes([0x80 | 127]) + struct.pack('>Q', k))
        mask = os.urandom(4)
        self.s.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        while True:
            frame = b''
            while True:
                b0, b1 = self._read(2)
                k = b1 & 0x7F
                k = struct.unpack('>H', self._read(2))[0] if k == 126 else struct.unpack('>Q', self._read(8))[0] if k == 127 else k
                frame += self._read(k)
                if b0 & 0x80:
                    break
            msg = json.loads(frame)
            if msg.get('id') == self.n:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg['result']

    def eval(self, expr):
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in r:
            raise RuntimeError(r['exceptionDetails'].get('exception', {}).get('description', r['exceptionDetails']))
        return r['result'].get('value')


def pages(port):
    targets = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
    return [Page(t) for t in targets if t.get('type') == 'page' and '/renderer/' in t.get('url', '')]


# --- 5. recording the platform ------------------------------------------------------------------------------------
# The record is the platform as this theme was built against it: every declaration the theme overrides, from
# every stylesheet any window loads, with the windows it loads in. CodeMirror numbers its scope classes in the
# order it creates them (.ͼ1, .ͼ2, ... .ͼv), and the numbers differ by window and by which editor theme came
# first, so the record spells every one of them .cm-editor -- the element they are all on.
CM_THEMES = ('berlin', 'frankfurt', 'bielefeld', 'karl-marx-stadt', 'bordeaux')
# CodeMirror mounts an extension's CSS only while the extension runs, and keeps it mounted after. Raw mode brings
# its own -- the colours of an alert's markers, found missing from the first record on screen -- so each theme is
# also read in raw mode. The modes an editor keeps for itself (readability, typewriter, distraction-free) have no
# setting here to switch; their CSS is mounted from the start, and is in the record.
CM_MODES = (('display.renderingMode', 'raw'),)
_CM_CLASS = re.compile(r'\.ͼ[0-9a-z]+')
_CM_CSS = r"""[...document.head.querySelectorAll('style')].filter(e => e.textContent.includes('.ͼ')).map(e => e.textContent).join('\n')"""


def _recordable(rows, cvars):
    out = []
    for media, sel, prop, val, imp in rows:
        if not matches_here(sel):
            continue
        face_var = prop.startswith('--') and 'font' in prop
        if paints(prop, val, cvars) or ((prop in TYPE or face_var) and val not in ('inherit', 'unset', 'initial')):
            out.append((media, sel, prop, val, imp))
    return out


def _codemirror(port, log):
    """The CSS CodeMirror mounts, in every window that has an editor, under each of Zettlr's five editor
    themes in light and dark, each in the CM_MODES too. Switching goes through Zettlr's own config API, and is put
    back afterwards."""
    found = {}
    main = next((p for p in pages(port) if p.window == 'main_window'), None)
    if main is None:
        raise SystemExit('record: no main window on that port')
    keys = ['display.theme', 'darkMode', 'autoDarkMode'] + [k for k, _ in CM_MODES]
    before = dict(zip(keys, main.eval('[' + ', '.join(f'window.config.get({json.dumps(k)})' for k in keys) + ']')))
    put = lambda k, v: main.eval(f'window.config.set({json.dumps(k)}, {json.dumps(v)})')
    put('autoDarkMode', 'off')
    main.eval("window.ipc.send('menu-provider', {command: 'click-menu-item', payload: 'menu.assets_manager'})")
    time.sleep(2)
    try:
        for theme in CM_THEMES:
            for dark in (False, True):
                put('display.theme', theme)
                put('darkMode', dark)
                for key, value in ((None, None),) + CM_MODES:
                    if key:
                        put(key, value)
                    time.sleep(1.5)
                    for p in pages(port):
                        css = p.eval(_CM_CSS) or ''
                        if css:
                            found.setdefault(p.window, []).append(css)
                    if key:
                        put(key, before[key])
                log(f'  codemirror: {theme}, {"dark" if dark else "light"}, and in ' +
                    ', '.join(f'{k} {v}' for k, v in CM_MODES))
    finally:
        for k in keys:
            put(k, before[k])
    return found


def record(port):
    """Write build/zettlr_platform.css from the installed build and a running window of it."""
    path = installed_asar()
    if not path:
        raise SystemExit('record: no Zettlr app.asar found (looked in ' + ', '.join(ASARS) + ')')
    version = json.loads(asar_read(path, 'package.json')).get('version', '?')
    log = lambda m: print(m, file=sys.stderr)
    sheets = {}                                           # content hash -> [css, windows]
    for w in WINDOWS:
        js = asar_read(path, f'.webpack/renderer/{w}/index.js').decode('utf8', 'replace')
        for css in bundle_sheets(js):
            h = hashlib.sha1(css.encode()).hexdigest()[:8]
            sheets.setdefault(h, [css, []])[1].append(w)
    cm = _codemirror(port, log)
    # Zettlr's appearance provider writes one more stylesheet at run time: <style id="system-css">, the platform's
    # accent colour -- on Linux its own green -- as two variables half its rules read.
    main = next(p for p in pages(port) if p.window == 'main_window')
    sheets['system-css'] = [main.eval("(document.getElementById('system-css') || {}).textContent || ''"),
                            list(WINDOWS)]
    parsed = {h: parse_css(css) for h, (css, ws) in sheets.items()}
    cm_parsed = {w: [parse_css(t) for t in texts] for w, texts in cm.items()}
    everything = [r for rows in parsed.values() for r in rows] + \
                 [r for texts in cm_parsed.values() for rows in texts for r in rows]
    cvars = colour_vars(everything)
    blocks = []
    for h, (css, ws) in sheets.items():
        rows = _recordable(parsed[h], cvars)
        if rows:
            blocks.append((h if h == 'system-css' else f'sheet {h}', ws, rows))
    cm_rows = {}                                          # row -> the windows that mount it, in record order
    for w, texts in cm_parsed.items():
        for rows in texts:
            for media, sel, prop, val, imp in _recordable(rows, cvars):
                row = (media, _CM_CLASS.sub('.cm-editor', sel), prop, val, imp)
                ws = cm_rows.setdefault(row, [])
                if w not in ws:
                    ws.append(w)
    cm_windows = list(cm_parsed)
    for ws in sorted({tuple(ws) for ws in cm_rows.values()}, key=lambda ws: -len(ws)):
        blocks.append(('codemirror', list(ws), [r for r, rws in cm_rows.items() if tuple(rws) == ws]))
    out = [f"""/* Zettlr {version}: the declarations the Remainder theme overrides. RECORDED by build/zettlr.py --record from
   {path} and a running window of it, {time.strftime('%Y-%m-%d')}. Never hand-edit: re-record, and let --coverage
   say what moved.

   Each block is one stylesheet as Zettlr ships it, trimmed to the declarations that put a colour on the screen
   and the two type properties the theme sets (font-size, font-family), with the windows that load it. Rules for
   body.darwin and body.win32 are left out: they cannot match on Linux. system-css is the one stylesheet Zettlr
   writes at run time, the platform's accent as two variables. CodeMirror's block is the CSS its editors
   mount under each of the five editor themes, light and dark, each in raw mode too, with every numbered scope
   class (.ͼ1, .ͼv, ...) written as .cm-editor, the element they are all on. This is Zettlr's own CSS, GPL-3.0
   like Zettlr. */"""]
    for name, ws, rows in blocks:
        where = 'every window' if len(ws) == len(WINDOWS) else ', '.join(ws)
        out.append(f'\n/* {name}: {where} */')
        for media, sel, prop, val, imp in rows:
            decl = f'{sel} {{ {prop}: {val}{" !important" if imp else ""}; }}'
            out.append(f'@media {media[7:] if media.startswith("@media ") else media} {{ {decl} }}' if media else decl)
    open(RECORD, 'w').write('\n'.join(out) + '\n')
    n = sum(len(r) for _, _, r in blocks)
    print(f'wrote {os.path.relpath(RECORD, ROOT)}: {n} declarations from '
          f'{sum(1 for b in blocks if b[0] != "codemirror")} stylesheets and CodeMirror ({", ".join(cm_windows)})')


# --- 6. the role table: every recorded declaration, classified --------------------------------------------------
# The theme overrides Zettlr's own rules at their own selectors, one class higher (THE MIRROR, below), so what it
# needs is a role for every declaration the record holds: which of the kit's values each one becomes. A
# declaration is classified by its selector, normalised -- `body`, its `.linux` and `.dark` and Vue's scoped
# `[data-v-...]` taken off -- and by what the property paints: a ground, an ink, a line, a shadow, an image, a
# variable, a size or a face. The first row that matches decides. A declaration no row matches is a defect, and
# the checker says which: the analog of NOT DERIVED BY ANY LADDER.
#
# Dark mode is not a second theme. A `body.dark` rule normalises to the same selector as its light twin and takes
# the same role, so Zettlr's dark mode paints the kit's light palette too (§2 is a light palette, and the
# installer turns dark mode off as well).
def norm(sel):
    s = re.sub(r'\[data-v-[0-9a-f]+\]', '', sel)
    s = re.sub(r':not\(\.(?:dark|darwin|win32)\)', '', s)
    s = re.sub(r'\bbody(?:\.(?:linux|dark|fullscreen))+', 'body', s)
    s = re.sub(r'^body(?=[\s>+~]|$)\s*', '', s)
    return ' '.join(s.split()) or 'body'


def prop_class(prop):
    if prop.startswith('--'):
        return 'size' if 'font-size' in prop else 'face' if 'font' in prop else 'var'
    if prop == 'font-size':
        return 'size'
    if prop == 'font-family':
        return 'face'
    if prop.startswith(('border', 'outline', 'column-rule')):
        return 'line'
    if prop in ('box-shadow', 'text-shadow', 'filter'):
        return 'shadow'
    if prop in ('background-image', 'content'):
        return 'image'
    if prop.startswith('background'):
        return 'ground'
    return 'ink'


def rule(pattern, note='', **roles):
    return (re.compile(pattern), roles, note)


# Shorthands for the rows below. `ground`, `ink`, `line`, `shadow`, `image`, `size`, `face` and `var` name the
# property class; each takes a role, NONE (transparent, or none for an image or a shadow), a Keep with its
# reason, PX16, UI or MONO.
PANEL = dict(ground=L, ink=B, size=PX16, face=UI, line=NONE)      # a LIGHT panel carries BLACK at 700 (§2)
FIELD = dict(ground=W, ink=B, size=PX16, face=UI, line=NONE)      # a WHITE field carries BLACK at 400
PICKED = dict(ground=S, ink=W)                                     # the selected row: SELECT carrying WHITE (§2)

CLASSIFY = [
    # --- every window ------------------------------------------------------------------------------------------
    rule(r'^html$', 'the root size is 16 px already, and rem reads it', size=CONTENT),
    rule(r'^body$', 'the page: BLACK on the window field, in Montserrat (§5); #000000 and white are §3\'s',
         ink=B, ground=W, face=UI, size=PX16),
    rule(r'^:root$', 'Zettlr\'s own palette variables: a backstop, so anything that reads one lands on a kit value',
         var='VARS'),
    rule(r'^\.tippy-box(\s|$)', 'tooltips: WHITE on BLACK, Lc -92.3, as on worksafe/obsidian/; a link in one is WHITE '
         'and keeps its underline', ground=B, ink=W, size=PX16),
    rule(r'^\.tippy-arrow$', 'a tooltip\'s arrow is drawn in its text colour, and is the tooltip\'s BLACK', ink=B),
    rule(r'^a$', 'links route to ACCENT (§3) and keep the underline', ink=A),
    rule(r'^\.dragger$', 'the item being dragged: a LIGHT chip carrying BLACK at 700; its shadow is a real one',
         ground=L, size=PX16, shadow=SHADOW),
    rule(r'^\.taglist .* \.tag$', 'a tag chip\'s outline: there are no lines (§5)', line=NONE),
    rule(r'::-webkit-scrollbar-thumb', 'the scrollbar: a LIGHT thumb on the field; on a panel it is DARK (the rules)',
         ground=L),
    rule(r'::-webkit-scrollbar', 'the track and its buttons are the ground they scroll', ground=NONE),
    rule(r'^div#window-content$', 'the window field', ground=W),
    rule(r'^div\.split-view div\.view\.view-border$', 'no hairline between panes: the tone changes (§5)', line=NONE),
    rule(r'^div#titlebar$', 'an auxiliary window\'s title strip: a LIGHT panel (the key state is the compositor\'s: '
         'see the rules)', **PANEL),
    rule(r'^#menubar$', 'the main window\'s top strip: a LIGHT panel, BLACK at 700', **PANEL),
    rule(r'^#menubar div\.top-level-item:hover$', 'a hover on a panel is WHITE', ground=W),
    rule(r'^div\.tab-list$', 'an auxiliary window\'s tab strip: a LIGHT panel', **PANEL),
    rule(r'^div\.tab-list button\[role="tab"\]\.active$', 'the current tab is the field\'s edge: WHITE, BLACK',
         ground=W, ink=B),
    rule(r'^div\.tab-list button\[role="tab"\]:hover$', 'a hover on a panel is WHITE', ground=W),
    rule(r'^div\.tab-list button\[role="tab"\]$', 'tabs on the strip', line=NONE, size=PX16),
    rule(r'^div#statusbar$', 'the button strip at the foot of a dialog: a LIGHT panel', **PANEL),
    rule(r'^div#statusbar button\.primary$', 'the primary button: ACCENT carrying WHITE, Lc -78.5; flat', ground=A,
         line=A, ink=W, image=NONE),
    rule(r'^div#toolbar$', 'the toolbar: a LIGHT panel, its glyphs BLACK', **PANEL),
    rule(r'^div#toolbar div\.toolbar-group span\.toolbar-label$|^\.toolbar-text$', 'toolbar labels', size=PX16),
    rule(r'^div#toolbar button:hover$|^div#toolbar button\.toolbar-overflow$',
         'a hover on a panel is WHITE', ground=W),
    rule(r'^div#toolbar button$', 'a toolbar button is its glyph: no outline, the panel\'s ground', line=NONE,
         ink=B),
    rule(r'^div#toolbar div\.three-way-toggle button\.active$', 'a toggle that is on: the field\'s WHITE, its glyph '
         'ACCENT (the rules)', ground=W),
    rule(r'^div#toolbar:window-inactive$', 'Blink never matches :window-inactive on an element; overridden anyway',
         ground=L, ink=B),
    rule(r'^div#toolbar button\.(verbose|info)-control-active$', 'the log viewer\'s level filters: on is WHITE; '
         'information has no hue (§3)', ground=W, ink=B),
    rule(r'^div#toolbar button\.warning-control-active$', 'warnings, filtered in: §3\'s WARNING with its legend',
         ground=WN, ink=LD),
    rule(r'^div#toolbar button\.error-control-active$', 'errors, filtered in: §3\'s DESTRUCTIVE with its legend',
         ground=DS, ink=LL),
    rule(r'^div\.application-menu$', 'a menu: a LIGHT frame, WHITE rows (the rules), no outline; its shadow is a '
         'real one', ground=L, ink=B, line=NONE, size=PX16, face=UI, shadow=SHADOW),
    rule(r'^div\.application-menu div\.menu-item:not\(\.separator\):not\(\.disabled\):hover$',
         'the row under the pointer: SELECT carrying WHITE (§2)', ground=S),
    rule(r'^div\.application-menu div\.menu-item\.disabled$', 'a disabled row: DARK (§2), on a WHITE row Lc 79.0',
         ink=D),
    rule(r'^div\.application-menu div\.menu-item\.separator$', 'a separator is a gap of the LIGHT frame, not a line',
         ground=NONE, line=NONE),
    rule(r'^div\.application-menu div\.menu-item div\.after-element$', 'the shortcut beside a row: DARK, Lc 79.0',
         ink=D),
    rule(r'^button\.iris-indicator canvas$', 'the pomodoro ring\'s dial: a BLACK disc; its shadow is decoration',
         var='VARS', ground=B, shadow=NONE),
    rule(r'^:root$|^body$', '', var='VARS'),

    # --- controls, in every window that has them ----------------------------------------------------------------
    rule(r'^(input|select|textarea)$', 'a control\'s outline is its own glyph, BLACK (worksafe/vscode/); a field is '
         'WHITE carrying BLACK at 400', line=B, ground=W, ink=B),
    rule(r'^button$', 'a button is LIGHT on the field and carries BLACK at 700, in its BLACK outline', line=B,
         ground=L, ink=B),
    rule(r'^label$', 'labels: Montserrat at 16 px', face=UI, size=PX16),
    rule(r'^input\[type="time"\]$', '', face=UI),
    rule(r'^label\.checkbox \.checkmark$', 'a checkbox is a WHITE box with a BLACK outline, flat', ground=W, line=B,
         image=NONE),
    rule(r'^label\.checkbox \.checkmark:after$', 'the tick: WHITE, on the ACCENT box', line=W),
    rule(r'^label\.checkbox input:checked ~ \.checkmark:after$', '', line=W),
    rule(r'^label\.checkbox input:checked ~ \.checkmark$', 'ticked: ACCENT (§2)', ground=A),
    rule(r'^label\.checkbox\.disabled input:checked ~ \.checkmark$', 'ticked and disabled: DARK, with its outline',
         ground=D, line=D),
    rule(r'^label\.checkbox\.disabled span\.checkmark$', 'disabled: the field, flat', ground=W, image=NONE),
    rule(r'^\.cb-group label\.disabled$|^\.radio-group-container label:not\(\.radio\)\.disabled$',
         'a disabled label: DARK (§2)', ink=D),
    rule(r'^\.cb-group div\.info$', 'a checkbox\'s description: DARK on the WHITE card, Lc 79.0', ink=D, size=PX16),
    rule(r'^\.radio-group-container p$', '', size=PX16),
    rule(r'^label\.radio \.toggle$', 'a radio button is a WHITE box with a BLACK outline (§5: square), flat',
         ground=W, line=B, image=NONE),
    rule(r'^label\.radio input:checked \+ \.toggle$', 'chosen: ACCENT', ground=A),
    rule(r'^label\.radio input:checked \+ \.toggle:before$', 'the dot, on the ACCENT box: WHITE', ground=W),
    rule(r'^label\.radio\.disabled input:checked ~ \.toggle$', 'chosen and disabled: DARK', ground=D, line=D),
    rule(r'^\.slider-group input\[type="?range"?\]::-webkit-slider-runnable-track$', 'the track: LIGHT, no line',
         ground=L, line=NONE),
    rule(r'^\.slider-group input\[type="?range"?\]::-webkit-slider-thumb$', 'the thumb: WHITE, BLACK outline',
         ground=W, line=B),
    rule(r'^div\.switch-group label$', '', face=UI),
    rule(r'^div\.switch-group label\.switch$', 'a switch\'s frame: its outline, BLACK', ground=B),
    rule(r'^div\.switch-group label\.switch \.toggle$', 'the track: LIGHT; the inset shading is a blend',
         ground=L, shadow=NONE),
    rule(r'^div\.switch-group label\.switch \.toggle:before$', 'the thumb: WHITE, and flat', ground=W, shadow=NONE),
    rule(r'^div\.switch-group label\.switch input:checked \+ \.toggle$', 'on: ACCENT (§2)', ground=A),
    rule(r'^div\.form-control \.input-text-button-group$', 'a text field with its reset button: WHITE, BLACK '
         'outline', ground=W, line=B, ink=B),
    rule(r'^div\.form-control \.input-text-button-group button\.input-reset-button$', 'the reset glyph in a field',
         ground=NONE, ink=B),
    rule(r'^div\.form-control p\.info$', '', size=PX16),
    rule(r'^\.progress-bar-container progress::-webkit-progress-bar$', 'a progress bar\'s track: LIGHT', ground=L),
    rule(r'^\.progress-bar-container progress(:indeterminate)?::-webkit-progress-(bar|value)$',
         'progress: ACCENT; the moving stripes are motion and a blend', ground=A, image=NONE),
    rule(r'^\.progress-bar-container \.interrupt-button:hover$', 'a hover on the field is LIGHT', ground=L),
    rule(r'^\.admonition$', '', size=PX16),
    rule(r'^\.admonition\.warning$', '§3: a warning is WARNING with its legend, and no line', ground=WN, ink=LD,
         line=NONE),
    rule(r'^\.admonition\.error$', '§3: an error is DESTRUCTIVE with its legend', ground=DS, ink=LL, line=NONE),
    rule(r'^\.admonition\.info$', 'information has no hue (§3 has three semantics, not four): LIGHT, BLACK at 700',
         ground=L, ink=B, line=NONE),
    rule(r'^div\.table-view table$', 'a table: WHITE rows, no grid (§5)', ground=W, line=NONE, size=PX16),
    rule(r'^div\.table-view table\.striped tr:nth-child\(2n\)$', 'no stripes: a LIGHT row would need 700 at every '
         'other line', ground=W),
    rule(r'^div\.table-view table thead tr', 'no grid', line=NONE),
    rule(r'^div\.table-view table tbody tr td:focus$', 'the cell being edited stays the field; focus is its '
         'ACCENT outline (the rules)', ground=W),
    rule(r'^\.selectable-list-wrapper$', 'the list\'s outline colours: there are no lines; the muted text is DARK',
         var='VARS'),
    rule(r'^\.selectable-list-wrapper \.selectable-list-footer$', 'a list\'s footer: a LIGHT panel of two glyphs, no '
         'lines', ground=L, line=NONE),
    rule(r'^\.selectable-list-wrapper \.selectable-list-container$|^\.selectable-list-wrapper div\.item$',
         'a list is WHITE rows with no lines', ground=W, line=NONE),
    rule(r'^\.selectable-list-wrapper \.selectable-list-footer \.(add|remove)$', '', ink=B),
    rule(r'^\.selectable-list-wrapper \.selectable-list-container div\.item\.selected$', '', **PICKED),
    rule(r'^\.selectable-list-wrapper \.selectable-list-container div\.item$', 'a row: WHITE, BLACK at 400',
         ground=W, ink=B, line=NONE, size=PX16),
    rule(r'^\.selectable-list-wrapper \.selectable-list-container div\.item \.info-string\.error$',
         'an error in a row: the ANSI red, Lc 75.0 on WHITE', ink=RED),
    rule(r'^\.selectable-list-wrapper \.selectable-list-container div\.item \.info-string$', 'secondary text in a '
         'list: DARK on WHITE, Lc 79.0', ink=D, size=PX16),
    rule(r'^\.selectable-list-wrapper \.selectable-list-container div\.no-items-label$', '', ink=D, size=CONTENT),
    rule(r'^div\.shortcut-wrapper kbd$', 'a key cap is WHITE on DARK, Lc -81.7, as on worksafe/vscode/', ground=D,
         ink=W, line=NONE, size=PX16),
    rule(r'^div\.shortcut-wrapper\.muted kbd$', 'a key that is not bound: a WHITE cap in a DARK outline, carrying '
         'DARK as disabled text (§2), Lc 79.0 -- DARK on LIGHT would be 48.4', ground=W, ink=D, line=D),
    rule(r'^\.shortcut-control-wrapper \.shortcut-input$', 'a shortcut field: BLACK in a BLACK outline', ink=B,
         line=B, face=UI, size=PX16),
    rule(r'^\.shortcut-control-wrapper \.shortcut-input:focus$', 'focus: ACCENT (§2)', line=A),
    rule(r'^div\.token-list$', '', face=UI, size=PX16),
    rule(r'^div\.token-list \.token$', 'a token: WHITE on DARK, Lc -81.7', ground=D, ink=W),
    rule(r'^div\.token-list \.token:hover$', 'hovered, a click removes it: §3\'s DESTRUCTIVE with its legend (the '
         'rules)', ground=DS),

    # --- the main window: the file manager ----------------------------------------------------------------------
    rule(r'^#file-manager #arrow-button$', 'the floating back button: WHITE on the panel, its glyph BLACK; the '
         'shadow is a real one', ground=W, ink=B, shadow=SHADOW),
    rule(r'^#file-tree$', 'the tree is the LIGHT panel', ground=L),
    rule(r'^#file-tree #directories-(dirs|files)-header$', 'the header over the tree: no line', line=NONE,
         size=PX16),
    rule(r'^#file-tree #directories-(dirs|files)-header \.close-all(:hover)?$', 'the collapse-all glyph',
         ground=NONE),
    rule(r'^#file-tree \.empty-tree \.info$|^#file-list \.empty-(file-list|directory)$', '', size=CONTENT),
    rule(r'^ul#workspaces-drag-list li', 'the workspace order list: no lines', line=NONE, size=CONTENT),
    rule(r'^div\.tree-item-container$', '', size=PX16),
    rule(r'^div\.tree-item-container \.tree-item\.(blue|purple|rose|red|orange|yellow|green)$', 'a colour the user '
         'gave a folder: information, left as Zettlr paints it', ink=CONTENT),
    rule(r'^div\.tree-item-container \.tree-item\.project$', 'a project is a folder; its glyph says so, and red would '
         'say error (§3)', ink=B),
    rule(r'^div\.tree-item-container \.tree-item\.(selected|active) \.display-text$', 'the current file and the '
         'current folder: SELECT carrying WHITE (§2)', **PICKED),
    rule(r'^\.tree-item \.display-text\.highlight$', 'a drop target, while something is dragged over it: ACCENT '
         'carrying WHITE', ground=A, ink=W),
    rule(r'^\.tree-item\.directory:not\(\.collapsed\)$', 'an open folder is not a surface of its own', ground=NONE),
    rule(r'^div\.list-item-wrapper div\.list-item$', 'a row in the file list: the LIGHT panel, no line', ground=L,
         line=NONE),
    rule(r'^div\.list-item-wrapper div\.list-item\.directory$', 'a folder in the list: BLACK, its glyph says so; its '
         'edge is not a line', ink=B, line=NONE),
    rule(r'^div\.list-item-wrapper div\.list-item\.active( div\.filename div\.date)?$', 'the open file\'s row: '
         'WHITE, the field\'s tone on the panel', ground=W),
    rule(r'^div\.list-item-wrapper div\.list-item\.selected( div\.filename div\.date)?$', '', **PICKED),
    rule(r'^div\.list-item-wrapper div\.list-item div\.filename div\.date$', 'the date under a name: BLACK on the '
         'panel (DARK on LIGHT is Lc 48.4)', ground=NONE, ink=B, size=PX16),
    rule(r'^div\.list-item-wrapper div\.list-item div\.filename$', '', size=PX16),
    rule(r'^div\.list-item-wrapper div\.list-item div\.meta-info \.badge\.code-indicator$', 'the code-file badge: '
         'ACCENT carrying WHITE', ground=A, ink=W),
    rule(r'^div\.list-item-wrapper div\.list-item div\.meta-info \.badge\.tag$', 'a tag\'s badge: WHITE on DARK, Lc '
         '-81.7', ground=D, ink=W, size=PX16),
    rule(r'^div\.list-item-wrapper div\.list-item div\.meta-info \.badge$', 'the other badges -- counts, the writing '
         'target -- are the row\'s own text; only dark mode gives them a ground, and the theme paints dark mode as '
         'light', ground=NONE, ink=INHERIT, size=PX16),
    rule(r'^div\.list-item-wrapper div\.list-item div\.meta-info \.badge\.tag \.color-circle$|'
         r'^\.tag-cloud \.tag \.color-circle$|^div\.popover \.badge \.color-circle$', 'the ring round a tag\'s own '
         'colour: no line; the colour inside is the user\'s', line=NONE),
    rule(r'^div\.list-item-wrapper div\.list-item div\.meta-info \.badge svg circle$', 'the writing target\'s '
         'pie, on the row itself in light mode: its track WHITE, lighter than the LIGHT row, as Zettlr\'s own ...',
         ink=W),
    rule(r'^div\.list-item-wrapper div\.list-item div\.meta-info \.badge svg path$', '... and its progress BLACK '
         '(the rules take both through the open and the selected row)', ink=B),
    rule(r'^div#global-search-pane$', '', size=PX16),
    rule(r'^div#global-search-pane (hr|div\.search-result-container)$', 'search results: no lines', line=NONE,
         size=PX16),
    rule(r'^div#global-search-pane div\.search-result-container div\.result-header \.filepath$', 'a result\'s path: '
         'BLACK on the panel', ink=B, size=PX16),
    rule(r'^div#global-search-pane div\.search-result-container div\.result-line$', '', size=PX16),
    rule(r'^div#global-search-pane div\.search-result-container div\.result-line:hover$', 'a hover on a panel is '
         'WHITE', ground=W),
    rule(r'^div#global-search-pane div\.search-result-container div\.result-line \.search-result-highlight$',
         'the matched text: BLACK, 700, underlined (the rules) -- ACCENT on LIGHT is Lc 44.8', ink=B),
    rule(r'^div#global-search-pane div\.search-result-container div\.active$', 'the chosen result', ground=S),

    # --- the main window: tabs, panes, the editor's frame --------------------------------------------------------
    rule(r'^div\.tab-container$', 'the tab strip: a LIGHT panel, no line under it', **PANEL),
    rule(r'^div\.tab-container div\[role="tab"\](:not\(:last-child\))?$', 'a tab: the panel, no lines', ground=L,
         line=NONE, size=PX16),
    rule(r'^div\.tab-container div\[role="tab"\]\.active$', 'the current tab is the field\'s edge: WHITE, and its '
         'underline would be a line between it and the field', ground=W, line=NONE),
    rule(r'^div\.tab-container div\[role="tab"\]:hover$|^div\.document-tablist-wrapper div\.scroller:hover$',
         'a hover on a panel is WHITE', ground=W),
    rule(r'^div\.tab-container div\[role="tab"\] \.(deduplicate|close)$', '', size=PX16),
    rule(r'^div\.tab-container \.dropzone$', 'where a dragged tab will land: ACCENT', ground=A),
    rule(r'^div\.document-tablist-wrapper div\.scroller(\.left|\.right)?$', 'the tab strip\'s scroll arrows: the '
         'panel, no lines', ground=L, line=NONE),
    rule(r'^\.split-pane-container( \.editor-pane)?\.border-(right|bottom)$', 'no hairline between editor panes',
         line=NONE),
    rule(r'^\.split-pane-container \.resizer:hover$', 'the resize handle, hovered: a mark, ACCENT', ground=A),
    rule(r'^\.editor-pane \.editor-container div\.dropzone$', 'the drop overlay: nothing until something is dragged '
         'over; its text WHITE for the ACCENT it will be', ground=NONE, ink=W),
    rule(r'^\.editor-pane \.editor-container div\.dropzone\.dragover$', 'a file dragged over the editor: ACCENT '
         'carrying WHITE; the glow is decoration', ground=A, shadow=NONE),
    rule(r'^\.editor-pane \.editor-container \.empty-pane$|^\.main-editor-wrapper$', 'the field', ground=W),
    rule(r'^\.main-editor-wrapper\.code-file \.cm-editor$', 'a code file: Hack (§5)', face=MONO),
    rule(r'^#sidebar$', 'the sidebar: a LIGHT panel, BLACK at 700', **PANEL),
    rule(r'^#sidebar h1$', '', size=CONTENT),
    rule(r'^#sidebar div\.toc-entry-container div\.toc-level$', 'a heading\'s level in the contents: BLACK on the '
         'panel', ink=B),
    rule(r'^#sidebar div\.toc-entry-container div\.toc-entry-active$', 'the heading the caret is under: BLACK, on '
         'SELECT (the rules)', ink=W),
    rule(r'^#sidebar div\.related-files-container div\.related-file:hover$', 'a hover on a panel is WHITE',
         ground=W),
    rule(r'^#sidebar div\.related-files-container div\.related-file span\.filename$', '', size=PX16),
    rule(r'^h2\.other-files-panel-folder-name$', '', size=PX16),
    rule(r'^\.toc-entry-container\.toc-drop-effect$', 'where a dragged heading will land: an ACCENT mark', line=A),
    rule(r'^div#references-panel h1 small\.word-count$|^div#references-list div\.csl-bib-body div\.csl-entry$', '',
         size=PX16),
    rule(r'^div#references-list div\.csl-bib-body div\.csl-entry a$', 'a link in a reference, on the panel: BLACK '
         'at 700 and underlined -- ACCENT on LIGHT is Lc 44.8', ink=B),

    # --- the main window: popovers ------------------------------------------------------------------------------
    rule(r'^\.popover-arrow\.(up|down|left|right)$', 'a popover\'s arrow is its own LIGHT ground', line=L),
    rule(r'^\.popover$', 'a popover: a LIGHT panel, no outline; its shadow is a real one', **PANEL, shadow=SHADOW),
    rule(r'^\.popover hr$', 'no line: the tone changes (§5)', line=NONE),
    rule(r'^\.popover form input(\.small)?$', '', size=CONTENT),
    rule(r'^div\.popover div\.properties-info-container$', 'file properties: BLACK on the panel', ink=B, size=PX16),
    rule(r'^div\.popover \.badge$', 'a tag badge: WHITE on DARK', ground=D, ink=W, size=PX16),
    rule(r'^div\.popover \.badge\.primary$', 'the primary badge: ACCENT carrying WHITE', ground=A, ink=W),
    rule(r'^\.color-selector \.color-swatch\.(blue|purple|rose|red|orange|yellow|green)$', 'the colours a user may '
         'give a folder: information, as Zettlr paints them', ground=CONTENT),
    rule(r'^\.color-selector \.color-swatch$', 'a swatch has no frame', line=NONE),
    rule(r'^\.color-selector \.color-swatch\.active$', 'the chosen swatch: a BLACK outline, a mark', line=B),
    rule(r'^\.icon-selector div:hover$', 'a hover on a panel is WHITE', ground=W),
    rule(r'^\.icon-selector div\.active$', 'the chosen glyph: SELECT carrying WHITE (the rules)', ground=S),
    rule(r'^div#stats-popover div#stats-counter-container svg$', 'the counter\'s ring', ink=B),
    rule(r'^\.table-generator \.row \.cell$', 'the table picker\'s cells: WHITE boxes with a BLACK outline',
         ground=W, line=B),
    rule(r'^\.table-generator \.row \.cell\.active$', 'the cells inside the chosen size: SELECT', ground=S),
    rule(r'^\.tag-cloud \.tag$', 'a tag: WHITE on DARK', ground=D, ink=W),
    rule(r'^\.tag-cloud \.tag:hover$', '...hovered: WHITE on SELECT', ground=S),
    rule(r'^p\.pomodoro-big$', '', size=CONTENT),
    rule(r'^div\.autocomplete-element div\.autocomplete-list$|^div\.autocomplete-element \.autocomplete-list$',
         'a suggestion list: WHITE rows; its shadow is a real one', ground=W, shadow=SHADOW),
    rule(r'^div\.autocomplete-element div\.autocomplete-list option\.active$', '', **PICKED),
    rule(r'^#lrt-wrapper \.lrt$', 'a finished task: §3\'s SUCCESS with its legend -- the meaning is present', ground=OK_,
         line=NONE),
    rule(r'^#lrt-wrapper \.lrt\.error$', 'a failed task: DESTRUCTIVE with its legend', ground=DS),
    rule(r'^#lrt-wrapper \.lrt\.(in-progress|aborted)$', 'a running or abandoned task: LIGHT, BLACK at 700',
         ground=L),
    rule(r'^#lrt-wrapper \.lrt \.info$', 'its detail line takes the legend of its ground (the rules)', ink=INHERIT,
         size=PX16),
    rule(r'^#lrt-wrapper \.lrt \.(title|metadata)$', '', size=PX16),
    rule(r'^div\.background-button$', 'the image viewer\'s backdrop choices: a BLACK outline', line=B),
    rule(r'^div\.background-button\.active$', '...the chosen one ACCENT', line=A),
    rule(r'^\.bg-(white|black|checker)$', 'the backdrop a user chose to inspect an image on: information',
         ground=CONTENT, var=CONTENT, image=CONTENT),

    # --- the editor: Zettlr's own stylesheet over CodeMirror ------------------------------------------------------
    rule(r'^\.cm-editor$', 'the editor: its text 1em, its ground the field', size=CONTENT, ground=W, ink=B,
         var='VARS'),
    rule(r'^\.cm-editor \.CodeMirror-overwrite \.CodeMirror-cursor$|^\.cm-editor\.cm-fat-cursor \.CodeMirror-cursor$',
         'the block caret (vim, overwrite): CURSOR', line=CU, ground=CU),
    rule(r'^\.cm-editor \.tabstop$|^\.cm-editor \.cm-snippetField$', 'a snippet\'s tab stop: LIGHT behind text',
         ground=L),
    rule(r'^\.cm-editor \.cm-snippetFieldPosition$', '', line=D),
    rule(r'^(\.cm-editor )?\.cm-(panels|statusbar)$', 'a panel: LIGHT, BLACK at 700', **PANEL),
    rule(r'^(\.cm-editor )?\.cm-tooltip$', 'a tooltip: a LIGHT panel, no outline', **PANEL),
    rule(r'^(\.cm-editor )?\.cm-formatting-bar$', 'the formatting bar: a LIGHT panel, no outline', ground=L,
         line=NONE),
    rule(r'^(\.cm-editor )?\.cm-formatting-bar \.cm-tooltip-arrow::(before|after)$', 'its arrow: its own ground',
         line=L),
    rule(r'^(\.cm-editor )?\.cm-formatting-bar button\.formatting-toolbar-button$', '', ink=B),
    rule(r'^(\.cm-editor )?\.cm-panel\.cm-panel-lint button\[aria-label="close"\]$', '', ink=B),
    rule(r'^(\.cm-editor )?\.cm-panel \.cm-button$', 'a button on a panel: a BLACK outline', line=B, size=PX16),
    rule(r'^\.cm-editor \.cm-yaml-frontmatter-start::after$', 'the label after the front matter\'s opening line',
         size=PX16, ground=L, ink=B),
    rule(r'^\.cm-editor \.footnote(-ref-label)?$', 'footnote references: at the size the floors assume', size=PX16),
    rule(r'^\.cm-editor \.heading-tag span$', '', size=CONTENT),
    rule(r'^\.cm-editor \.katex$|^\.katex|^\.cm-editor \.cm-completionIcon', 'math, and the completion list\'s '
         'glyphs', size=CONTENT, face=CONTENT),

    # --- the editor: CodeMirror's own theme, under Zettlr's five ------------------------------------------------
    rule(r'^\.cm-editor\.cm-focused$', 'the focused editor draws no outline of its own', line=NONE),
    rule(r'^\.cm-editor \.cm-scroller$', 'the note: BLACK on WHITE, Lc 91.8, in the note\'s own face', face=CONTENT,
         ground=W, ink=B),
    rule(r'^\.cm-editor \.cm-content$', 'the native caret: CURSOR (§2)', ink=CU),
    rule(r'^\.cm-editor\.cm-focused( > \.cm-scroller > \.cm-selectionLayer| \.cm-scroller \.cm-layer\.'
         r'cm-selectionLayer) \.cm-selectionBackground$|^\.cm-editor \.cm-selectionBackground$',
         'the selection: CodeMirror paints it BEHIND text that keeps its colour, so it is LIGHT -- BLACK on it Lc '
         '61.2, the platform\'s shortfall, measured (HIGHLIGHTS)', ground=L),
    rule(r'^\.cm-editor ::selection$', '', ground=L),
    rule(r'^\.cm-editor( div\.cm-table-editor-widget-wrapper table)? \.cm-content :focus ?::selection$', 'native '
         'selection in a table cell can carry its own colour: SELECT carrying WHITE (the rules)', ground=S),
    rule(r'^\.cm-editor \.cm-(cursor|dropCursor)$', 'the caret, and where a drop will land: CURSOR (§2)', line=CU),
    rule(r'^\.cm-editor \.cm-cursor-(primary|secondary)$', 'Zettlr\'s own carets: CURSOR, every one', ground=CU),
    rule(r'^\.cm-editor \.cm-(activeLine|activeLineGutter)$', 'no band under the caret\'s line: the caret is the '
         'locator (§2)', ground=NONE),
    rule(r'^\.cm-editor \.cm-content \.typewriter-active-line$', 'typewriter mode\'s band: none, for the same '
         'reason', ground=NONE, line=NONE),
    rule(r'^\.cm-editor \.cm-specialChar$', 'an invisible character, shown: an ACCENT mark', ink=A),
    rule(r'^\.cm-editor \.cm-gutters$', 'the gutter is the field, and its labels DARK, Lc 79.0', ground=W, ink=D,
         line=NONE),
    rule(r'^\.cm-editor \.cm-(footnote|heading)-gutter \.cm-gutterElement( div)?$', 'the gutter\'s labels: Hack at '
         '16 px', face=MONO, size=PX16),
    rule(r'^\.cm-editor \.cm-panels-(top|bottom)$', 'no line between a panel and the note', line=NONE),
    rule(r'^\.cm-editor \.cm-(dialog label|dialog-close|panel\.cm-search label|diagnosticSource)$', '', size=PX16),
    rule(r'^\.cm-editor \.cm-placeholder$', 'a placeholder: DARK', ink=D),
    rule(r'^\.cm-editor \.cm-highlightSpace$', 'shown whitespace: a DARK dot', ground=InPlace(D)),
    rule(r'^\.cm-editor \.cm-highlightTab$', 'a shown tab: its arrow was an image stroked grey; it is drawn by the '
         'rules', image=NONE),
    rule(r'^\.cm-editor \.cm-trailingSpace$', 'trailing whitespace: LIGHT behind it', ground=L),
    rule(r'^\.cm-editor \.cm-button(:active)?$', 'a button on a panel: WHITE, BLACK outline, flat', image=NONE,
         line=B, size=PX16),
    rule(r'^\.cm-editor \.cm-textfield$', 'a field: WHITE, BLACK outline', ground=W, line=B, size=PX16),
    rule(r'^\.cm-editor \.cm-diagnostic-error$|^\.cm-editor \.cm-lintPoint:after$', 'an error\'s mark: '
         'DESTRUCTIVE (§3)', line=DS),
    rule(r'^\.cm-editor \.cm-diagnostic-warning$|^\.cm-editor \.cm-lintPoint-warning:after$', 'a warning\'s mark: '
         'the ANSI yellow -- WARNING on WHITE is Lc 8.0, under the visibility floor', line=YELLOW),
    rule(r'^\.cm-editor \.cm-diagnostic-(info|hint)$|^\.cm-editor \.cm-lintPoint-(info|hint):after$', 'information '
         'has no hue: DARK', line=D),
    rule(r'^\.cm-editor \.cm-diagnosticAction(\.cm-ltDisableAction)?$', 'an action in a diagnostic: a button, WHITE '
         'on the LIGHT tooltip', ground=W, ink=B),
    rule(r'^\.cm-editor \.cm-lintRange-(error|warning|info|hint)$', 'the wavy underline was an image; it is a '
         'text-decoration in the mark\'s role (the rules)', image=NONE),
    rule(r'^\.cm-editor \.cm-lintRange-active$', 'the range whose diagnostic is open: LIGHT behind it, 700 (the '
         'rules)', ground=L),
    rule(r'^\.cm-editor \.cm-lint-marker-(info|warning|error)$', 'the gutter\'s markers were images; they are '
         'squares in their role (the rules)', image=NONE),
    rule(r'^\.cm-editor \.cm-panel\.cm-panel-lint ul(:focus)? \[aria-selected\]$', '', **PICKED),
    rule(r'^\.cm-editor \.cm-tooltip\.cm-tooltip-autocomplete > ul( > completion-section)?$', 'the completion '
         'list: Montserrat, no lines', face=UI, line=NONE),
    rule(r'^\.cm-editor \.cm-tooltip-autocomplete(-disabled)? ul li\[aria-selected\]$', '', **PICKED),
    rule(r'^\.cm-editor\.cm-focused \.cm-matchingBracket$', 'a matched bracket: LIGHT behind it', ground=L),
    rule(r'^\.cm-editor\.cm-focused \.cm-nonmatchingBracket$', 'an unmatched bracket is an error in the text: '
         'DESTRUCTIVE carrying its legend (the rules)', ground=DS),
    rule(r'^\.cm-editor \.cm-tooltip-section:not\(:first-child\)$', 'no line between a tooltip\'s sections',
         line=NONE),
    rule(r'^\.cm-editor( \.cm-tooltip-(above|below))? \.cm-tooltip( \.cm-tooltip)?-arrow:(before|after)$|'
         r'^\.cm-editor \.cm-tooltip \.cm-tooltip-arrow:before$', 'a tooltip\'s arrow is its own LIGHT ground',
         line=L),
    rule(r'^\.cm-editor \.cm-statusbar \.cm-statusbar-item:not\(:first-child\)$', 'no rule between status items',
         line=NONE),
    rule(r'^\.cm-editor \.cm-foldPlaceholder$', 'a folded span\'s placeholder: LIGHT carrying BLACK, no outline',
         ground=L, ink=B, line=NONE),
    rule(r'^\.cm-editor \.cm-searchMatch$', 'a search match: LIGHT behind it, 700 (the rules)', ground=L),
    rule(r'^\.cm-editor \.cm-searchMatch-selected$', '...the current one outlined in ACCENT (the rules)', ground=L),
    rule(r'^\.cm-editor \.editor-note-preview( h[1-6]| \.metadata)?$', 'a note\'s preview: at the size the floors '
         'assume, BLACK on the panel', size=PX16, ink=B),
    rule(r'^\.cm-editor \.footnote-preview-container$', '', size=PX16),
    rule(r'^\.cm-editor \.cm-readability-\d+$', 'readability mode colours each sentence by its difficulty: an '
         'analysis of the text, information', ground=CONTENT, ink=CONTENT),
    rule(r'^\.cm-editor \.admonition-wrapper\.(note|tip|important)$', 'a note, tip or important alert is furniture: '
         'LIGHT, BLACK at 700 -- information has no hue (§3)', ground=L, ink=B, line=NONE),
    rule(r'^\.cm-editor \.(note|tip|important) > :is\(', 'raw mode shows an alert as its markers, on the note: '
         'a note, tip or important one BLACK -- information has no hue (§3) ...', ink=B),
    rule(r'^\.cm-editor \.warning > :is\(', '... a warning\'s in the ANSI yellow, warning text ...', ink=YELLOW),
    rule(r'^\.cm-editor \.caution > :is\(', '... and a caution\'s in the ANSI red, the text form of DESTRUCTIVE',
         ink=RED),
    rule(r'^\.cm-editor \.admonition-wrapper\.warning$', 'a warning: WARNING with its legend', ground=WN, ink=LD,
         line=NONE),
    rule(r'^\.cm-editor \.admonition-wrapper\.caution$', 'a caution -- GitHub\'s red, "negative potential '
         'consequences": DESTRUCTIVE with its legend', ground=DS, ink=LL, line=NONE),
    rule(r'^\.cm-editor pandoc-div-mark-wrapper$', 'a pandoc div\'s marker: the field', ground=W, size=CONTENT),
    rule(r'^\.cm-editor pandoc-div-info-wrapper$', '', ground=W),
    rule(r'^\.cm-editor \.mark \.cm-pandoc-span$|^\.cm-editor \.cm-highlight$', 'marked text: LIGHT, and 700 (the '
         'rules)', ground=L),
    rule(r'^\.cm-editor \.iframe-wrapper$', 'an embedded page\'s frame: LIGHT', ground=L),
    rule(r'^\.cm-editor div\.cm-table-editor-widget-wrapper table (td|th)$', 'a table: BLACK, no grid (§5)', ink=B,
         line=NONE),
    rule(r'^\.cm-editor figure\.image-preview (\.image-size-info|figcaption|\.open-externally-button)$',
         'captions over an image: WHITE on BLACK, Lc -92.3, opaque', ground=B, ink=W, size=PX16),
    rule(r'^\.cm-editor figure\.image-preview figcaption::selection$', 'selected caption text: §2\'s selection',
         ground=S, ink=W),
    rule(r'^\.cm-editor \.code$', 'code: BLACK in Hack (§5)', ink=B, face=MONO),
    rule(r'^\.cm-editor \.cm-(keyword|control-keyword|operator-keyword|definition-keyword|module-keyword|modifier|'
         r'tag|tag-name)$', 'the code colouring (§0c, CHOSEN, as on worksafe/vscode/): keywords and tags BLACK and '
         'bold', ink=B),
    rule(r'^\.cm-editor \.cm-(comment|line-comment|block-comment|meta)$', '...comments DARK and italic', ink=D),
    rule(r'^\.cm-editor \.cm-(string|string-2|number|integer|bool|atom|null|color|unit|regexp|changed)$',
         '...literals ACCENT', ink=A),
    rule(r'^\.cm-editor \.cm-(property|property-name|attribute|attribute-name|name|class-name|type-name|type|'
         r'label-name|builtin|qualifier)$', '...members, names and types SELECT, Lc 85.8 on WHITE', ink=S),
    rule(r'^\.cm-editor \.cm-(operator|compare-operator|arithmetic-operator|self|variable|variable-2|variable-name|'
         r'deref-operator|separator|punctuation|content-span|brace|square-bracket)$', '...and the rest the base text',
         ink=B),
    rule(r'^\.cm-editor \.cm-(inserted|positive)$', 'a diff is content, and its convention is realized: inserted '
         'green, at the ANSI text tier', ink=GREEN),
    rule(r'^\.cm-editor \.cm-(deleted|negative|invalid)$', '...deleted and invalid red', ink=RED),
    rule(r'^\.cm-editor \.cm-(monospace|inline-math)$', 'inline code and math: BLACK, carried by the face', ink=B),
    rule(r'^\.cm-editor \.(citeproc-citation|code-block-line-background|inline-code-background)$', 'code and '
         'citations keep the field\'s ground and are carried by their face', ground=NONE),
    rule(r'^\.cm-editor \.(cm-escape|cm-code-mark|cm-yaml-frontmatter-(start|end)|cm-citation-(mark|at-sign|'
         r'suppress-author-flag))$', 'Markdown\'s own marks: DARK, Lc 79.0', ink=D),
    rule(r'^\.cm-editor \.cm-yaml-frontmatter-start::after$', '', ink=B, ground=L),
    rule(r'^\.cm-editor \.cm-(link|url|zkn-tag|citation-citekey)$', 'links, tags and citation keys route to ACCENT '
         '(§3), Lc 75.4 on WHITE', ink=A),
    rule(r'^\.cm-editor \.cm-(strong|emphasis)$', '', ink=B),
    rule(r'^\.cm-editor \.cm-hr$', 'a thematic break\'s marks: DARK', ink=D),
    rule(r'^\.cm-editor \.(citeproc-citation\.error|mermaid-chart\.error)$', 'a citation or a diagram that failed: '
         'the ANSI red, Lc 75.0', ink=RED),
    rule(r'^\.cm-editor \.cm-(foldPlaceholder|blockquote)$|^\.cm-editor \.blockquote-wrapper$', 'the quote bar: '
         'BLACK, at the width of §5\'s mark (the rules)', line=B),

    # --- auxiliary windows ------------------------------------------------------------------------------------
    rule(r'^\.form-container \.fieldset-category$', 'a settings category over its cards: BLACK on the LIGHT page',
         ink=B, size=PX16),
    rule(r'^\.form-container fieldset$', 'a group of settings: a WHITE card on the LIGHT page, BLACK at 400, no line',
         ground=W, ink=B, line=NONE),
    rule(r'^\.form-container fieldset \.form-header legend$|^\.form-container fieldset \.control-grid '
         r'\.control-grid-cell\.heading$', '', size=PX16),
    rule(r'^\.form-container fieldset \.form-help$', 'a help badge: WHITE on DARK', ground=D, ink=W, line=NONE,
         size=PX16),
    rule(r'^\.form-container (fieldset )?hr$', 'no line', line=NONE),
    rule(r'^\.form-field-(info-text|sub-heading|plain-text)$', 'descriptions: DARK on the card, Lc 79.0', ink=D,
         size=PX16),
    rule(r'^p#theme-selection-label$|^div#theme-container$', '', size=PX16),
    rule(r'^div#theme-container div\.theme-container-item div\.theme-mockup', 'the pictures of Zettlr\'s five editor '
         'themes: pictures of windows, content', ground=CONTENT, size=CONTENT, shadow=CONTENT),
    rule(r'^div#theme-container div\.theme-container-item div\.theme-metadata div\.selected-button$', 'the chosen '
         'theme\'s button: SELECT carrying WHITE', **PICKED),
    rule(r'^div#theme-container div\.theme-container-item div\.theme-metadata div\.not-selected-button$', 'a theme '
         'not chosen: a LIGHT button carrying BLACK at 700', ground=L, ink=B),
    rule(r'^#no-results-message$', '', size=CONTENT),
    rule(r'^\.code-editor-wrapper$', 'a code field: WHITE, BLACK outline (a control)', ground=W, line=B),
    rule(r'^\.asset-container span\.protected-info$', 'DARK on the field', ink=D),
    rule(r'^div#sil-1-1-text$|^div#error p#additional-info$|^div#about-general p#uuid$|^\.message \.details$',
         'fixed-width text: Hack (§5)', face=MONO, ink=D, size=PX16),
    rule(r'^div#project-container div\.project-box$', 'a project\'s card: LIGHT carrying BLACK at 700, no line',
         ground=L, line=NONE),
    rule(r'^div#project-container div\.project-box:hover$', 'hovered: WHITE', ground=W),
    rule(r'^div#project-container div\.project-box (h4\.project-name|p\.project-description)$', '', ink=B),
    rule(r'^#log-viewer$', 'the log: the field, BLACK', ground=W, ink=B),
    rule(r'^\.message$', 'no lines between messages', line=NONE),
    rule(r'^\.message \.expand-details$|^\.message \.message \.details \.more$', '', ink=B),
    rule(r'^\.message\.(verbose|info)$', 'a verbose or informational line: the field -- information has no hue',
         ground=W, ink=B),
    rule(r'^\.message\.(verbose|info):hover$', 'hovered: LIGHT', ground=L),
    rule(r'^\.message\.warning(:hover)?$', 'a warning: WARNING with its legend', ground=WN, ink=LD),
    rule(r'^\.message\.error(:hover)?$', 'an error: DESTRUCTIVE with its legend', ground=DS, ink=LL),
    rule(r'^#onboarding-progress span$', 'the steps to come: LIGHT', ground=L),
    rule(r'^#onboarding-progress span\.done$', 'the steps done: ACCENT', ground=A),
    rule(r'^p#version-string$', 'the version: ACCENT on WHITE, Lc 75.4', ink=A, size=CONTENT),
    rule(r'^p\.small$', '', size=PX16),
    rule(r'^\.box$', 'no outline', line=NONE),
    rule(r'^(button|select)(\.active)?$', 'the first-run window\'s buttons: ACCENT carrying WHITE', ground=A, ink=W),
    rule(r'^(button|select)(\.active)?:hover$', '...hovered SELECT', ground=S),
    rule(r'^(button|select)(:disabled|\.inactive)$', '...off: the field\'s WHITE carrying DARK (§2), Lc 79.0, as every '
         'disabled button', ground=W, ink=D),
    rule(r'^(button|select)\.inactive:hover$', '', ground=W),
    rule(r'^#print-container', 'the print preview: the document as it will print, content', ground=CONTENT,
         ink=CONTENT, line=CONTENT, face=CONTENT, size=CONTENT),
    rule(r'^div#project-lists p\.warning$', 'a warning: WARNING with its legend', ground=WN, ink=LD, line=NONE),
    rule(r'^\.export-file-list \.export-file-item( \.display-name \.relative-dirname|:not\(\.active\))$', 'a file '
         'left out of the export, and a folder\'s name: DARK on the field', ink=D, size=PX16),
    rule(r'^\.export-file-list \.export-file-item:not\(:last-child\)$', 'no lines', line=NONE),
    rule(r'^#splash-screen-wrapper #info h1$', '', size=CONTENT),
    rule(r'^div#calendar-container|^div#chart-container|^#box-plot-fsal-stats-words|^div#graph-container div#graph',
         'the writing statistics: a heat map, charts and a graph -- information', ground=CONTENT, ink=CONTENT,
         line=CONTENT, size=CONTENT, shadow=CONTENT),
    rule(r'^div#graph-container div#loading-indicator$', 'the graph\'s loading scrim', ground=SCRIM, ink=W),
    rule(r'^div#tag-manager table tr:nth-child\(2n\)$', 'no stripes', ground=W),
    rule(r'^#update #changelog', 'the release notes: text Zettlr fetches, content', size=CONTENT),
]

# Zettlr's own variables, and what each becomes. Every use the record holds is mirrored with its own role above;
# these values are the BACKSTOP under that, so a variable something reads at run time -- an inline style, a canvas
# drawn from a computed value -- lands on the kit's ladder too. The grey ramp is SNAPPED to the nearest of §2's
# four by lightness, as build/firefox.py snaps Firefox's greys; the rest are role assignments.
LADDER = ['white', 'light', 'dark', 'black']


def snap(hx):
    Lx = ok.lch(hx)[0]
    return R(min(LADDER, key=lambda r: abs(ok.lch(ROLES[r])[0] - Lx)))


ZETTLR_GREYS = {'--grey-0': '#f0f0f0', '--grey-1': '#dcdcdc', '--grey-2': '#c8c8c8', '--grey-3': '#787882',
                '--grey-4': '#64646e', '--grey-5': '#50505a', '--grey-6': '#464650', '--grey-7': '#282832'}
VARS = [
    (r'^--grey-\d$', None, 'Zettlr\'s grey ramp, snapped'),
    (r'^--(green|blue|purple|gold)-selection(-dark)?$', L, 'selections behind text: LIGHT'),
    (r'^--bg-error$', DS, 'an error\'s ground and its legend'), (r'^--fg-error$', LL, ''),
    (r'^--system-accent-color$', A, 'the platform accent Zettlr writes at run time -- on Linux its own green, '
     '#1CB27E, inside the success pole'), (r'^--system-accent-color-contrast$', W, ''),
    (r'^--(blue-[013]|orange-[012]|green-0|accent)$', A, 'Zettlr\'s accents: ACCENT'),
    (r'^--(green-1)$', S, ''),
    (r'^--(red-[0127])$', DS, 'Zettlr\'s reds: DESTRUCTIVE'),
    (r'^--(beige-0)$', W, 'Bielefeld\'s paper: the field'), (r'^--(beige-2|apricot)$', L, ''),
    (r'^--accent-(blue|purple|rose|red|orange|yellow|green)$', CONTENT, 'the colours a user gives a folder'),
    (r'^--zettlr-(note|tip|important)-color$', B, 'the furniture alerts: BLACK on LIGHT'),
    (r'^--zettlr-(note|tip|important)-bg$', L, ''),
    (r'^--zettlr-warning-color$', LD, 'a warning: WARNING with its legend'), (r'^--zettlr-warning-bg$', WN, ''),
    (r'^--zettlr-caution-color$', LL, 'a caution: DESTRUCTIVE with its legend'), (r'^--zettlr-caution-bg$', DS, ''),
    (r'^--selectable-list-border-color(-dark)?$', NONE, 'no lines'), (r'^--muted-color$', D, ''),
    (r'^--charcoal-black$', B, ''),
    (r'^--checker-(dark|light)$', CONTENT, 'the image viewer\'s checkerboard, which the user chose'),
    (r'^--zettlr-editor-(primary|secondary)-color$', A, 'the editor\'s accent'),
    (r'^--zettlr-editor-(scroller-color|code-color|accent-color|code-base-0[23]|code-cyan)$', B, ''),
    (r'^--zettlr-editor-(scroller-bg|code-base-[23])$', W, ''),
    (r'^--zettlr-editor-(selection-color|highlight-color|accent-bg)$', L, ''),
    (r'^--zettlr-editor-(citation-bg|code-bg)$', NONE, 'code and citations keep the field\'s ground'),
    (r'^--zettlr-editor-(citation-color|escape-color|code-base-0|code-base-1|code-base-00|code-base-01)$', D, ''),
    (r'^--zettlr-editor-(error-color|code-red)$', RED, ''),
    (r'^--zettlr-editor-code-(yellow|orange|magenta|blue)$', S, 'the code colouring (§0c): members SELECT'),
    (r'^--zettlr-editor-code-(violet|green)$', A, '...literals ACCENT'),
]
FACE_VARS = {'--zettlr-editor-font': UI, '--zettlr-editor-code-font': MONO,
             '--zettlr-editor-font-size': CONTENT}


def var_role(name):
    if name in ZETTLR_GREYS:
        return snap(ZETTLR_GREYS[name])
    if name in FACE_VARS:
        return FACE_VARS[name]
    for pattern, role, _ in VARS:
        if re.match(pattern, name):
            return role
    return None


def load_record(path=RECORD):
    """[(block, media, selector, property, value, important)] from the recorded platform. A block is named with the
    windows that load it: 'sheet 74fa3733: main_window, preferences, assets'."""
    rows, block = [], None
    for line in open(path, encoding='utf8'):
        m = re.match(r'/\* ((?:sheet \w+|codemirror|system-css): [\w ,]+) \*/', line)
        if m:
            block = m.group(1)
            continue
        m = re.match(r'(?:@media (.*?) \{ )?(.+?) \{ (--[\w-]+|[a-z-]+): (.*?)( !important)?; \}( \})?$', line.rstrip('\n'))
        if m and block:
            media, sel, prop, val, imp, _ = m.groups()
            rows.append((block, f'@media {media}' if media else '', sel, prop, val, bool(imp)))
    return rows


def classify(sel, prop):
    """(role, note) for one recorded declaration, or (None, '') if no row of the table decides it."""
    n, c = norm(sel), prop_class(prop)
    if prop.startswith('--'):
        role = var_role(prop)
        if role is not None:
            return role, 'a variable: the backstop (VARS)'
    for pattern, roles, note in CLASSIFY:
        if pattern.search(n) and c in roles and roles[c] != 'VARS':
            return roles[c], note
    return None, ''


# --- 7. the mirror ---------------------------------------------------------------------------------------------
# Each recorded declaration is overridden at its own selector, one class higher: `:root` in front of it, which
# matches the same elements and outranks the platform's rule wherever both apply, whatever order the two
# stylesheets load in. So the theme's own rules win exactly where Zettlr's did, and among themselves they keep
# Zettlr's order: the value on the screen is the role of whichever platform rule would have won. A colour in a
# shorthand is written as its longhand -- `border: 1px solid #b4b4b4` becomes `border-color` -- so the override
# never resets a width or a style the platform set in the same rule.
_LONGHAND = {'border': 'border-color', 'outline': 'outline-color', 'column-rule': 'column-rule-color',
             'text-decoration': 'text-decoration-color', 'background': 'background-color'}
_COLOURISH = re.compile(r'var\(\s*--[\w-]+\s*(?:,[^()]*(?:\([^()]*\)[^()]*)*)?\)|#[0-9A-Fa-f]{3,8}\b|'
                        r'\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\([^()]*(?:\([^()]*\)[^()]*)*\)|[A-Za-z]+')


def windows_of(block):
    """The windows a recorded block loads in, from its name."""
    where = block.split(': ', 1)[1] if ': ' in block else 'every window'
    return list(WINDOWS) if where == 'every window' else [w.strip() for w in where.split(',')]


def scope(block):
    """Where a mirrored rule may apply: the windows whose bundle loads the platform's rule, and no others. The theme
    is one stylesheet that every window loads, and Zettlr's are per window, so an override of a rule only the Assets
    Manager has would otherwise reach the main window's editor too. Each window's page loads its own bundle,
    <script src="../assets/index.js">, which marks the window for good; :where() keeps the mark out of the
    specificity, so a scoped override ranks exactly as an unscoped one."""
    ws = windows_of(block)
    if set(ws) >= set(WINDOWS):
        return ''
    mark = lambda names: ', '.join(f':has(script[src="../{w}/index.js"])' for w in names)
    others = [w for w in WINDOWS if w not in ws]
    if len(others) < len(ws):                     # the shorter way to say it: every window but these
        return f':where(:not({mark(others)}))'
    return f':where({mark(ws)})'


def bump(sel, where=''):
    if sel.startswith(':root'):
        return ':root' + where + sel
    if re.match(r'html(?![\w-])', sel):
        return 'html:root' + where + sel[4:]
    return ':root' + where + ' ' + sel


def mirror_decls(prop, value, role):
    """[(property, value)] the theme writes for one platform declaration, given its role."""
    if isinstance(role, Keep):
        return []
    c = prop_class(prop)
    if c == 'size':
        return [(prop, role)]
    if c == 'face':
        return [(prop, FACES[role])]
    if isinstance(role, Lit):
        return [(_LONGHAND.get(prop, prop), str(role))]
    if isinstance(role, InPlace):
        def swap(m):
            t = m.group(0)
            if t.startswith('var(') or t.startswith('#') or '(' in t or t.lower() in NAMED:
                return R(str(role)).css()
            return t
        return [(prop, _COLOURISH.sub(swap, value))]
    if c == 'var':
        return [(prop, role.css())]
    if c == 'shadow':
        assert role == NONE, f'{prop}: a shadow is kept or removed, not recoloured'
        return [(prop, 'none')]
    if c == 'image':
        assert role == NONE, f'{prop}: an image is kept or removed; its colours cannot be var()s'
        return [(prop, 'none')]
    m = re.match(r'(border|outline)(-(top|right|bottom|left|block|inline)(-(start|end))?)?$', prop)
    if m:
        return [(f'{prop}-color', role.css())]
    out = [(_LONGHAND.get(prop, prop), role.css())]
    if prop == 'background' and re.search(r'gradient\(|url\(', value):
        out.append(('background-image', 'none'))
    return out


def mirror_rules(rows):
    """[(block, media, selector, [(property, value, important)], [notes])] in the record's order."""
    out, index = [], {}
    for block, media, sel, prop, val, imp in rows:
        role, note = classify(sel, prop)
        if role is None:
            continue
        decls = mirror_decls(prop, val, role)
        if not decls:
            continue
        key = (media, bump(sel, scope(block)))
        if key not in index:
            index[key] = len(out)
            out.append((block, media, key[1], [], []))
        entry = out[index[key]]
        for p, v in decls:
            existing = [d for d in entry[3] if d[0] == p]
            if existing:
                entry[3].remove(existing[0])
            entry[3].append((p, v, imp))
        if note and note not in entry[4]:
            entry[4].append(note)
    return out


# --- 8. the rules: what no declaration of Zettlr's reaches ------------------------------------------------------
# The mirror can only recolour what Zettlr colours. Four things it cannot reach, and these rules do: what the
# browser paints when nothing is declared (a field's #FFFFFF, a link's blue, text at #000000); grounds Zettlr
# leaves to show through, which the kit's structure needs to be LIGHT or WHITE; the ink that has to follow a
# ground the mirror moved to SELECT or ACCENT; and §5's type, weight and corners. Values are written with {role}
# placeholders; nothing else may carry a colour. `:root:root` in front outranks the mirror's one class, where a
# rule has to win over a platform rule it contradicts; !important only where an inline style is the platform's.
PANELS = ('#menubar', 'div#toolbar', 'div#titlebar', 'div.tab-list', 'div.tab-container', '#file-manager', '#sidebar',
          'div#statusbar', '.cm-editor .cm-panels', '.cm-editor .cm-tooltip', '.cm-editor .cm-formatting-bar',
          '.popover', 'div.application-menu', '.dragger', '.admonition.info', '.cm-editor .admonition-wrapper.note',
          '.cm-editor .admonition-wrapper.tip', '.cm-editor .admonition-wrapper.important',
          '#lrt-wrapper .lrt.in-progress', '#lrt-wrapper .lrt.aborted', 'div#project-container div.project-box',
          '.cm-editor .cm-foldPlaceholder', '.selectable-list-wrapper .selectable-list-footer', 'button',
          'div#global-search-pane')
FIELDS = ('input', 'textarea', 'select', 'div.application-menu div.menu-item',
          '.cm-editor .cm-tooltip-autocomplete ul li', 'div.autocomplete-list', 'div.single-search-result')
_hi = lambda sels: ', '.join(':root:root ' + s for s in sels)

RULES = [
    ('The page: the window field, in the light scheme whatever Zettlr tells Chromium, so the controls and '
     'scrollbars the browser draws are light too (§2 is a light palette).', 'html:root, :root body',
     [('color-scheme', 'light'), ('background-color', '{white}')]),
    ('§5: the controls take the page\'s face and the size every floor assumes; the browser gives them Arial at '
     '13.33 px.', 'button, input, select, textarea',
     [('font-family', 'var(--rm-face-ui)'), ('font-size', '16px')]),
    ('A button\'s text is BLACK: Zettlr colours its buttons only in dark mode, and the browser\'s ButtonText is #000000, '
     'which §3 reserves for legend.', 'button', [('color', '{black}')]),
    ('A field is WHITE carrying BLACK: the browser paints it #FFFFFF, which §3 reserves.',
     _hi(('input', 'select', 'textarea')), [('background-color', '{white}'), ('color', '{black}')]),
    ('', 'input::placeholder, textarea::placeholder', [('color', '{dark}'), ('opacity', '1')]),
    ('A button on a LIGHT panel is WHITE, as on worksafe/firefox/; Zettlr gives every button the same grey.',
     ', '.join(f':root:root {p} button:not(.primary)' for p in ('#sidebar', '.popover', 'div#statusbar', '.cm-editor .cm-panels',
                                                   '.cm-editor .cm-tooltip', '.selectable-list-wrapper '
                                                   '.selectable-list-footer', '#file-manager')),
     [('background-color', '{white}')]),
    ('A button that is off is DARK (§2) on the field\'s WHITE, Lc 79.0, in a DARK outline: DARK on LIGHT would be '
     'Lc 48.4.', ':root:root button:disabled', [('background-color', '{white}'), ('color', '{dark}'),
                                                ('border-color', '{dark}')]),
    ('A button hovered is SELECT carrying WHITE, as on worksafe/firefox/.',
     ':root:root button:not(:disabled):hover', [('background-color', '{select}'), ('color', '{white}')]),
    ('A strip of tabs that are glyphs -- the sidebar\'s, a popover\'s: each is its glyph on the panel, hovered '
     'WHITE, and the open one WHITE with its glyph in ACCENT, as the toolbar\'s toggle. On Linux Zettlr marks the '
     'open tab not at all.', ':root:root .system-tablist .system-tab',
     [('background-color', 'transparent'), ('border-color', 'transparent')]),
    ('', ':root:root .system-tablist .system-tab:hover', [('background-color', '{white}'), ('color', '{black}')]),
    ('', ':root:root .system-tablist .system-tab.active', [('background-color', '{white}'), ('color', '{accent}')]),
    ('Native checkboxes, radio buttons, sliders and bars: the browser\'s own blue is info-blue.',
     'input, progress', [('accent-color', '{accent}')]),
    ('Focus: ACCENT (§2).', ':focus-visible', [('outline-color', '{accent}')]),
    ('Text selected outside the editor can carry its own colour, so it is §2\'s selection.', '::selection',
     [('background-color', '{select}'), ('color', '{white}')]),
    ('In the note CodeMirror paints the selection BEHIND text that keeps its own colour (LIGHT, CLASSIFY). This '
     'Chromium hands a selection\'s ink down from the element around it, so the WHITE above reaches the note too; '
     'currentColor gives each piece of text its own ink back ...', ':root:root .cm-content ::selection',
     [('color', 'currentColor')]),
    ('... except in a table cell being edited, where the native selection shows: SELECT carrying WHITE.',
     ':root:root .cm-content :focus::selection, :root:root .cm-content :focus ::selection', [('color', '{white}')]),
    ('A misspelt word in a field: Chromium dots it in a red of its own. The kit\'s error mark is DESTRUCTIVE (Lc 68.1 '
     'on WHITE, a mark\'s tier 30), dotted at 2 px -- a wave that size is clipped by the field.', '::spelling-error',
     [('text-decoration', 'underline dotted {destructive} 2px')]),
    ('The find panel and the tooltips are chrome inside the editor, where Zettlr\'s editor selection would reach '
     'them: §2\'s selection.', ':root:root .cm-editor .cm-panels ::selection, :root:root .cm-editor .cm-tooltip '
     '::selection', [('background-color', '{select}'), ('color', '{white}')]),
    ('Weight follows the ground (§2): every LIGHT panel carries BLACK at 700, Lc 61.2 ...', _hi(PANELS),
     [('font-weight', '700')]),
    ('... and every WHITE field nested in one goes back to 400, Lc 91.8.', _hi(PANELS[:1]) and
     ', '.join(f':root:root {p} {f}' for p in PANELS for f in FIELDS[:3]) + ', ' + _hi(FIELDS[3:]),
     [('font-weight', '400')]),
    ('The current tab is the field\'s edge: WHITE, carrying BLACK at 400. In light mode Zettlr marks it only by an '
     'underline, which would be a line between the tab and its field.',
     ':root:root div.tab-container div[role="tab"].active', [('background-color', '{white}'), ('font-weight', '400')]),
    ('The pomodoro ring: Zettlr strokes it by attribute, #aaaaaa and #ff3388 whatever the phase (it passes the '
     'phase\'s colour as `colour` and the ring reads `trackColour`). A track in the field\'s tone, the time gone '
     'in ACCENT.', 'svg.progress-ring circle:first-child', [('stroke', '{white}')]),
    ('', 'svg.progress-ring circle:last-child', [('stroke', '{accent}')]),
    ('A task in the note is the browser\'s own checkbox, #FFFFFF with a grey edge. It is drawn here: a WHITE box in '
     'a BLACK outline, and ticked, ACCENT with a WHITE tick (§2), square (§5).',
     ':root:root .cm-editor input[type="checkbox"]',
     [('appearance', 'none'), ('display', 'inline-grid'), ('place-content', 'center'), ('box-sizing', 'border-box'),
      ('width', '0.875em'), ('height', '0.875em'), ('margin', '0 0.25em 0 0'), ('vertical-align', '-0.0625em'),
      ('border', '1px solid {black}'), ('background-color', '{white}')]),
    ('', ':root:root .cm-editor input[type="checkbox"]:checked',
     [('background-color', '{accent}'), ('border-color', '{accent}')]),
    ('', ':root:root .cm-editor input[type="checkbox"]:checked::after',
     [('content', '""'), ('width', '0.25em'), ('height', '0.5em'), ('border', 'solid {white}'),
      ('border-width', '0 0.125em 0.125em 0'), ('transform', 'translateY(-0.0625em) rotate(45deg)')]),
    ('A menu\'s rows touch, so the only gap in the WHITE is a separator: the LIGHT frame showing through.',
     ':root:root div.application-menu', [('padding', '5px 0')]),
    ('', ':root:root div.application-menu div.menu-item', [('margin', '0 5px')]),
    ('', ':root:root div.application-menu div.menu-item.separator', [('margin', '5px')]),
    ('A thematic break is a change of field tone, 4 px of LIGHT (§5); the browser draws a grey inset line.',
     'hr', [('border', '0'), ('height', '4px'), ('background-color', '{light}')]),
    ('The line under a selected row\'s name is WHITE with it.',
     ':root:root .selectable-list-wrapper .selectable-list-container div.item.selected .info-string',
     [('color', '{white}')]),
    ('A code field -- the Assets Manager\'s editors -- is set in Hack (§5); CodeMirror asks for `monospace`, which '
     'fontconfig answers with some other face.', ':root:root .code-editor-wrapper .cm-editor .cm-scroller',
     [('font-family', 'var(--rm-face-mono)')]),
    ('A chosen radio button is ACCENT with its WHITE dot (§2). On Linux Zettlr fills it only in dark mode, so in light '
     'mode the dot sat on the empty box.', ':root:root label.radio input:checked + .toggle',
     [('background-color', '{accent}'), ('border-color', '{accent}')]),
    ('The same for a key that is not bound: Zettlr gives its cap a ground only in dark mode, so in light mode it kept '
     'the bound key\'s DARK under its DARK text. The WHITE cap its row promises (CLASSIFY) is set here.',
     ':root:root div.shortcut-wrapper.muted kbd', [('background-color', '{white}')]),
    ('Settings: the page is a LIGHT panel and each group a WHITE card on it (§2\'s alternation, as on '
     'worksafe/obsidian/); the list of pages beside it is the field. Zettlr paints page and cards alike.',
     ':root:root div.view:has(> .form-container)', [('background-color', '{light}')]),
    ('', ':root:root .form-container .fieldset-category', [('font-weight', '700')]),
    ('A strip of tabs may wrap: at the size the floors assume and the weight a LIGHT strip needs, the About '
     'window\'s six do not fit its width. Zettlr fixes the strip at 40 px, for one row of 11 px labels, so it grows '
     'from there to hold the second row, and the page below gives up the room. The current tab is WHITE, so it goes '
     'back to 400.',
     ':root:root div.tab-list', [('flex-wrap', 'wrap'), ('height', 'auto'), ('min-height', '40px')]),
    ('', ':root:root div.tab-list button[role="tab"].active', [('font-weight', '400')]),
    ('An alert is a frame in its role with its title on the frame, and its content on a WHITE inset carrying BLACK at '
     '400 -- worksafe/obsidian/\'s callout. Zettlr pads the frame and gives every line of the alert its own line box, '
     'so the first line is the title and every other line is content.',
     ':root:root .cm-editor .admonition-wrapper .cm-line:not(:first-child)',
     [('background-color', '{white}'), ('color', '{black}'), ('font-weight', '400')]),
    ('Search across all files is a LIGHT panel like the file manager beside it, and each file\'s results a WHITE card '
     'on it (worksafe/obsidian/\'s search): Zettlr leaves the pane to show the window field through.',
     ':root:root div#global-search-pane', [('background-color', '{light}')]),
    ('', ':root:root div#global-search-pane div.single-search-result',
     [('background-color', '{white}'), ('padding', '4px'), ('margin-bottom', '8px')]),
    ('A thematic break on a LIGHT panel is WHITE: the tone change, the other way.',
     ', '.join(f':root:root {p} hr' for p in ('div#global-search-pane', '.popover', '#sidebar')),
     [('background-color', '{white}')]),
    ('A result\'s relevance, which Zettlr writes inline as grey, info-blue and green by thirds of the best match: a '
     'ranking, not a signal, so it is carried by tone on the WHITE card -- LIGHT, DARK, BLACK.',
     'div#global-search-pane cds-icon.relevancy-icon[style*="170, 170, 170"]', [('fill', '{light} !important')]),
    ('', 'div#global-search-pane cds-icon.relevancy-icon[style*="41, 117, 217"]', [('fill', '{dark} !important')]),
    ('', 'div#global-search-pane cds-icon.relevancy-icon[style*="51, 170, 51"]', [('fill', '{black} !important')]),
    ('A search field\'s clear button is the browser\'s own glyph, and Chromium draws it blue -- inside the info-blue pole, '
     'where no computed style shows it (the pixel scan found it). Drawn here instead: an x of two strokes in BLACK.',
     'input[type="search"]::-webkit-search-cancel-button',
     [('-webkit-appearance', 'none'), ('appearance', 'none'), ('width', '0.75em'), ('height', '0.75em'),
      ('cursor', 'pointer'),
      ('background', 'linear-gradient(45deg, transparent calc(50% - 1px), {black} calc(50% - 1px) calc(50% + 1px), '
                     'transparent calc(50% + 1px)), linear-gradient(-45deg, transparent calc(50% - 1px), {black} '
                     'calc(50% - 1px) calc(50% + 1px), transparent calc(50% + 1px))')]),
    ('The file manager is a LIGHT panel: Zettlr leaves it to show the window field through.',
     ':root:root #file-manager', [('background-color', '{light}')]),
    ('Menu rows are the field, on the menu\'s LIGHT frame (worksafe/obsidian/); the row under the pointer is '
     'SELECT carrying WHITE, its shortcut included.',
     ':root:root div.application-menu div.menu-item:not(.separator)', [('background-color', '{white}')]),
    ('', ':root:root div.application-menu div.menu-item:not(.separator):not(.disabled):hover, '
         ':root:root div.application-menu div.menu-item:not(.separator):not(.disabled):hover div.after-element',
     [('color', '{white}')]),
    ('A completion list is WHITE rows on its LIGHT frame, like a menu.',
     ':root:root .cm-editor .cm-tooltip-autocomplete ul li:not([aria-selected])', [('background-color', '{white}')]),
    ('Grounds the mirror moved to SELECT or ACCENT carry WHITE; the platform left their ink to inheritance.',
     ':root:root div#global-search-pane div.search-result-container div.active, :root:root .icon-selector '
     'div.active, :root:root .table-generator .row .cell.active', [('color', '{white}')]),
    ('', ':root:root #sidebar div.toc-entry-container div.toc-entry-active', [('background-color', '{select}')]),
    ('Where Zettlr renders a note as HTML in its chrome -- the preview of a linked note -- the browser\'s own marks '
     'show through: <mark> in its yellow carrying #000000, <code> in whatever face `monospace` finds. Marked text is '
     'LIGHT carrying BLACK at 700 and code is Hack, as in the editor. The print preview is the page as it will '
     'print, and keeps its own.', ':root:root mark:not(#print-container *)',
     [('background-color', '{light}'), ('color', '{black}'), ('font-weight', '700')]),
    ('On a LIGHT panel -- the preview is a tooltip -- a LIGHT mark would vanish: there it is the other tone, WHITE.',
     ':root:root :is(.cm-tooltip, .popover) mark:not(#print-container *)', [('background-color', '{white}')]),
    ('', ':root:root :is(code, pre, samp):not(#print-container *)', [('font-family', 'var(--rm-face-mono)')]),
    ('The file list\'s chips on the selected row: DARK and ACCENT are dE 11.2 and 11.8 from SELECT, under the floor, '
     'so there a chip is the field\'s WHITE carrying BLACK (dE 62.8).',
     ':root:root div.list-item-wrapper div.list-item.selected div.meta-info .badge.tag, :root:root '
     'div.list-item-wrapper div.list-item.selected div.meta-info .badge.code-indicator',
     [('background-color', '{white}'), ('color', '{black}')]),
    ('Dark mode grounds every badge alike, a tag\'s too, and later; the theme paints dark mode as light, so a tag '
     'keeps its DARK chip there.', ':root:root body.dark div.list-item-wrapper div.list-item:not(.selected) '
     'div.meta-info .badge.tag', [('background-color', '{dark}'), ('color', '{white}')]),
    ('The writing target\'s pie sits on the row itself. On the open file\'s WHITE row its track is LIGHT; on the '
     'selected row LIGHT too, and its progress the row\'s WHITE ink.',
     ':root:root div.list-item-wrapper div.list-item.active div.meta-info .badge svg circle, :root:root '
     'div.list-item-wrapper div.list-item.selected div.meta-info .badge svg circle', [('fill', '{light}')]),
    ('', ':root:root div.list-item-wrapper div.list-item.selected div.meta-info .badge svg path',
     [('fill', '{white}')]),
    ('Onboarding\'s buttons are Zettlr\'s dark blue carrying white; the mirror makes them LIGHT carrying BLACK, a '
     'button on the field. The chosen one it moves to ACCENT, whose ink Zettlr left to that white: WHITE, Lc -78.5.',
     ':root:root:where(:has(script[src="../onboarding/index.js"])) button.active', [('color', '{white}')]),
    ('... and its three sponsor buttons carry their makers\' marks as pictures, drawn white for that blue. A picture '
     'keeps its colours, so they stand on DARK, where the kit sets its own WHITE marks (Lc -81.7).',
     ':root:root:where(:has(script[src="../onboarding/index.js"])) button.image-button',
     [('background-color', '{dark}')]),
    ('A toggle that is on, in the toolbar: its glyph ACCENT on the WHITE of the field (Lc 75.4).',
     ':root:root div#toolbar div.three-way-toggle button.active', [('color', '{accent}')]),
    ('Every other toggle in a toolbar -- the log viewer\'s level filters, the sidebar\'s button -- Zettlr marks as on '
     'only on macOS; on Linux on and off look the same. The same WHITE, its label or glyph ACCENT.',
     ':root:root div#toolbar button.toggle.active', [('background-color', '{white}'), ('color', '{accent}')]),
    ('§3\'s grounds carry §3\'s legend.', ':root:root div.token-list .token:hover, :root:root .cm-editor.cm-focused '
     '.cm-nonmatchingBracket, :root:root #lrt-wrapper .lrt, :root:root #lrt-wrapper .lrt.error',
     [('color', '{legend-light}')]),
    ('', ':root:root #lrt-wrapper .lrt.in-progress, :root:root #lrt-wrapper .lrt.aborted', [('color', '{black}')]),
    ('A link on a LIGHT panel is BLACK and underlined: ACCENT on LIGHT is Lc 44.8.',
     _hi(('#sidebar a', '.popover a', '#file-manager a', '.cm-editor .cm-tooltip a')),
     [('color', '{black}'), ('text-decoration', 'underline')]),
    ('The scrollbar: its arrows are images, and a thumb on a LIGHT panel is DARK.', '::-webkit-scrollbar-button',
     [('display', 'none')]),
    ('', ', '.join(f':root:root {p} ::-webkit-scrollbar-thumb' for p in ('#file-manager', '#sidebar', '.popover',
                                                                          'div.application-menu')),
     [('background-color', '{dark}')]),
    ('§5: every corner square -- Zettlr\'s, the browser\'s, and the two its status bar writes inline.',
     '*, *::before, *::after, ::-webkit-scrollbar-thumb, ::-webkit-slider-thumb, ::-webkit-slider-runnable-track',
     [('border-radius', '0 !important')]),
    ('A slider\'s track on a LIGHT panel is DARK (dE 37.5): the LIGHT track Zettlr\'s grey becomes would vanish into '
     'the panel. On the settings\' WHITE cards it stays LIGHT.',
     ', '.join(f':root:root {p} .slider-group input[type=range]::-webkit-slider-runnable-track'
               for p in ('.popover', '#sidebar', 'div#statusbar')), [('background-color', '{dark}')]),
    ('Opacity is a blend too: text at 0.8 over its ground is a value nobody authored. Each is the value it stood '
     'for.', ':root:root div.form-control p.info, :root:root .cm-editor .cm-heading-gutter .cm-gutterElement div, '
     ':root:root .cm-editor .muted', [('opacity', '1'), ('color', '{dark}')]),
    ('A diagnostic\'s source, faded the same way, sits in the LIGHT lint panel, where DARK is Lc 48.4: it takes its '
     'row\'s ink.', ':root:root .cm-editor .cm-diagnosticSource', [('opacity', '1'), ('color', 'inherit')]),
    ('The lint panel\'s chosen diagnostic, while the list is not focused, is a ground alone in CodeMirror; the mirror '
     'makes it SELECT, so it carries WHITE.', ':root:root .cm-editor .cm-panel.cm-panel-lint ul [aria-selected]',
     [('color', '{white}')]),
    ('Distraction-free mode mutes the lines outside the caret\'s paragraph to that DARK. An alert\'s title line keeps '
     'its alert\'s ink: DARK on LIGHT is Lc 48.4, and on the semantic grounds less. Its body lines, on the WHITE '
     'inset, are muted like any other.', ':root:root .cm-editor .admonition-wrapper .cm-line.muted:first-child',
     [('color', 'inherit')]),
    ('', ':root:root .cm-editor .admonition-wrapper .cm-line.muted:not(:first-child)', [('color', '{dark}')]),
    ('', ':root:root div.tab-container div[role="tab"] .deduplicate, :root:root div#theme-container '
         'div.theme-container-item, :root:root .cm-editor .blockquote-wrapper .cm-line, :root:root .cm-editor '
         '.cm-completionIcon, :root:root .cm-editor .cm-tooltip.cm-tooltip-autocomplete > ul > completion-section',
     [('opacity', '1')]),
    ('', ':root:root .cm-editor', [('--zettlr-editor-opacity', '1')]),
    ('The code colouring\'s geometry (§0c): keywords and tags bold, comments italic.',
     ', '.join(f':root:root .cm-editor .cm-{t}' for t in ('keyword', 'control-keyword', 'operator-keyword',
                                                          'definition-keyword', 'module-keyword', 'modifier', 'tag',
                                                          'tag-name')), [('font-weight', '700')]),
    ('', ', '.join(f':root:root .cm-editor .cm-{t}' for t in ('comment', 'line-comment', 'block-comment')),
     [('font-style', 'italic')]),
    ('Links keep the underline: it is what the convention rests on, now the hue is gone (§3).',
     ':root:root .cm-editor .cm-link, :root:root .cm-editor .cm-url', [('text-decoration', 'underline')]),
    ('Marked text, search matches and the range of the diagnostic open in the lint panel sit on LIGHT, so they are '
     'set 700: the pair §2 authors, Lc 61.2. The current match is outlined in ACCENT.', ':root:root .cm-editor '
     '.cm-highlight, :root:root .cm-editor .mark .cm-pandoc-span, :root:root .cm-editor .cm-searchMatch, :root:root '
     '.cm-editor .cm-lintRange-active', [('font-weight', '700')]),
    ('', ':root:root .cm-editor .cm-searchMatch-selected', [('outline', '2px solid {accent}')]),
    ('The quote bar at the width of §5\'s mark; the quote itself is text, not faded.',
     ':root:root .cm-editor .blockquote-wrapper', [('border-left-width', '4px')]),
    ('Diagnostics: the wavy underline Zettlr drew as an image is a text-decoration in the mark\'s role -- '
     'DESTRUCTIVE for an error, the ANSI yellow for a warning (WARNING on WHITE is Lc 8.0), DARK for the rest.',
     ':root:root .cm-editor .cm-lintRange-error', [('text-decoration', 'underline wavy {destructive}'),
                                                   ('text-decoration-skip-ink', 'none')]),
    ('', ':root:root .cm-editor .cm-lintRange-warning', [('text-decoration', 'underline wavy {yellow}'),
                                                        ('text-decoration-skip-ink', 'none')]),
    ('', ':root:root .cm-editor .cm-lintRange-info, :root:root .cm-editor .cm-lintRange-hint',
     [('text-decoration', 'underline wavy {dark}'), ('text-decoration-skip-ink', 'none')]),
    ('The gutter\'s diagnostic markers were images; each is a square in its role.',
     ':root:root .cm-editor .cm-lint-marker-error', [('content', 'normal'), ('background-color', '{destructive}')]),
    ('', ':root:root .cm-editor .cm-lint-marker-warning', [('content', 'normal'), ('background-color', '{yellow}')]),
    ('', ':root:root .cm-editor .cm-lint-marker-info', [('content', 'normal'), ('background-color', '{dark}')]),
    ('Tables in the note draw no grid; the header row is LIGHT carrying BLACK at 700 (worksafe/obsidian/).',
     ':root:root .cm-editor div.cm-table-editor-widget-wrapper table th, :root:root div.table-view table thead th',
     [('background-color', '{light}'), ('font-weight', '700')]),
]

# The larger half (§0), shipped as a stylesheet of its own beside the theme, so it is a switch -- install.sh
# --no-declutter leaves it out of custom.css -- and so that it works under any theme. It names no colour, and the
# checker proves it.
DECLUTTER_RULES = [
    ('Motion: every transition and animation Zettlr runs -- the file list sliding, the pomodoro ring, the '
     'splash screen, tooltips fading, the caret blinking -- at 0.01 ms rather than 0, so every transitionend and '
     'animationend still fires and nothing waiting on one is stranded; one iteration, so a spinner stops rather '
     'than spins. !important because the pomodoro ring writes its transition inline.',
     '*, *::before, *::after', [
         ('transition-duration', '0.01ms !important'), ('transition-delay', '0s !important'),
         ('animation-duration', '0.01ms !important'), ('animation-delay', '0s !important'),
         ('animation-iteration-count', '1 !important'), ('scroll-behavior', 'auto !important')]),
    ('Blur: nothing frosts what is behind it.', '*', [('backdrop-filter', 'none !important')]),
]


# --- 9. writing ---------------------------------------------------------------------------------------------------
HEADER = """/* Remainder for Zettlr -- the theme. GENERATED by build/zettlr.py --write: never hand-edit; change the role table
   there and regenerate. AUTHORITY.md is the authority; worksafe/zettlr/README_ZETTLR.md says what each part is for
   and what is left over. Worksafe tier: a file beside Zettlr's own custom.css, which imports it.
   Checked by build/zettlr.py against Zettlr {version}, recorded in build/zettlr_platform.css.

   THE ONLY LITERAL COLOURS IN THIS FILE ARE THE --rm-* DEFINITIONS BELOW. Everything else refers to them by name,
   so a value nobody derived cannot get in, and the checker can prove it (CONTRIBUTING.md §8). */
"""


def _fmt(v):
    if isinstance(v, R):
        return v.css()
    out = str(v)
    for k in sorted(ROLES, key=len, reverse=True):
        out = out.replace('{' + k + '}', R(k).css())
    return out


def _comment(text, indent=''):
    if not text:
        return []
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > 108:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    if len(lines) == 1:
        return [f'{indent}/* {lines[0]} */']
    return [f'{indent}/* {lines[0]}'] + [f'{indent}   {l}' for l in lines[1:-1]] + [f'{indent}   {lines[-1]} */']


def _block(sel, decls, indent=''):
    out = [indent + (',\n' + indent).join(split_top(sel)) + ' {']
    for d in decls:
        prop, value = d[0], d[1]
        imp = len(d) > 2 and d[2]
        out.append(f'{indent}  {prop}: {_fmt(value)}{" !important" if imp else ""};')
    out.append(indent + '}')
    return out


def recorded_version():
    m = re.search(r'Zettlr (\S+):', open(RECORD, encoding='utf8').read(300))
    return m.group(1) if m else '?'


def theme_text():
    out = [HEADER.format(version=recorded_version()).rstrip('\n'), '', ':root {']
    out += _comment('§2 and §3: the values the theme may name, each checked against palette.json. The three '
                    'signal-text values are build/cosmic.py\'s ANSI normal tier. And §5\'s two faces.', '  ')
    for name in ROLES:
        out.append(f'  --rm-{name}: {ROLES[name]};')
    for name, face in FACES.items():
        out.append(f'  --rm-face-{name}: {face};')
    out.append('}')
    out.append('')
    out += _comment('THE MIRROR. Every declaration Zettlr makes that puts a colour on the screen, or a face or a '
                    'size the kit sets, overridden at its own selector one class higher, in its own order, with '
                    'its role. Grouped by the stylesheet it comes from, as build/zettlr_platform.css records it.')
    last, said = None, None
    for block, media, sel, decls, notes in mirror_rules(load_record()):
        if block != last:
            out += ['', f'/* --- {block} --- */']
            last, said = block, None
        note = '; '.join(n for n in notes if n)
        if note and note != said:
            out += _comment(note)
            said = note
        if media:
            out.append(f'{media} {{')
            out += _block(sel, decls, '  ')
            out.append('}')
        else:
            out += _block(sel, decls)
    out.append('')
    out += _comment('THE RULES: what no declaration of Zettlr\'s reaches.')
    for note, sel, decls in RULES:
        out.append('')
        out += _comment(note)
        out += _block(sel, decls)
    return '\n'.join(out) + '\n'


SNIPPET_HEADER = """/* Remainder for Zettlr -- the declutter (AUTHORITY.md §0): motion and blur, removed. GENERATED by build/zettlr.py
   --write: never hand-edit. Imported by custom.css after the theme, unless install.sh --no-declutter; it works
   under any theme, and carries no colour. */
"""


def snippet_text():
    out = [SNIPPET_HEADER.rstrip('\n')]
    for note, sel, decls in DECLUTTER_RULES:
        out.append('')
        out += _comment(note)
        out += _block(sel, decls)
    return '\n'.join(out) + '\n'


def write():
    os.makedirs(ZET, exist_ok=True)
    for path, text in ((THEME, theme_text()), (SNIPPET, snippet_text())):
        open(path, 'w').write(text)
        print(f'wrote {os.path.relpath(path, ROOT)}: {len(text.splitlines())} lines')


# --- 10. the screen: what the running app paints ----------------------------------------------------------------
# A theme is not what the window shows: the browser's own defaults, inline styles and anything the record missed
# still apply. So this asks a running Zettlr, over the DevTools port, what every visible element computed -- the
# way worksafe/obsidian/'s probe asks Obsidian -- in every window, into every shadow root (Zettlr's icons are
# Clarity web components), and reports each painted value off the ladder and each text pair under the tier its
# own computed size and weight demand. A report, not a gate: it needs a window.
# What the screen report counts as content (§0a) rather than chrome, as CLASSIFY does: math, diagrams, the
# statistics' charts, the print preview, the pictures of the editor themes, the image viewer's backdrops, the
# colours a user gave a folder or a tag, and readability mode's analysis. A value off the ladder inside one of these
# is information, and the report lists it apart.
CONTENT_SELECTORS = ('.katex', 'math', '.mermaid-chart', '#print-container', 'div#calendar-container',
                     'div#chart-container', '#box-plot-fsal-stats-words', 'div#graph-container',
                     'div#theme-container div.theme-mockup', '.bg-white', '.bg-black', '.bg-checker',
                     '.tree-item.blue', '.tree-item.purple', '.tree-item.rose', '.tree-item.red', '.tree-item.orange',
                     '.tree-item.yellow', '.tree-item.green', '.color-swatch', '.color-circle',
                     '[class*="cm-readability-"]', 'img', 'iframe', 'canvas')
PROBE = r"""(() => {
  const out = [];
  const CONTENT = __CONTENT__;
  const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const hex = c => '#' + c.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();
  const up = e => e.parentElement || (e.parentNode && e.parentNode.host) || null;
  const name = el => { let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id;
    const cls = (el.getAttribute('class') || '').trim().split(/\s+/).filter(c => c && !c.startsWith('ͼ')).slice(0, 3);
    return cls.length ? s + '.' + cls.join('.') : s; };
  const where = el => { const p = []; for (let e = el; e && e !== document.body && p.length < 4; e = up(e)) p.unshift(name(e)); return p.join(' > '); };
  const opacity = el => { let o = 1; for (let e = el; e; e = up(e)) o *= parseFloat(getComputedStyle(e).opacity); return o; };
  const ground = el => { const chain = []; for (let e = el; e; e = up(e)) chain.push(e);
    let g = [255, 255, 255]; for (const e of chain.reverse()) { const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c[3] > 0) g = g.map((v, i) => c[i] * c[3] + v * (1 - c[3])); } return g; };
  const SHAPES = new Set(['path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse']);
  const all = []; const walk = root => { for (const el of root.querySelectorAll('*')) { all.push(el); if (el.shadowRoot) walk(el.shadowRoot); } };
  walk(document);
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || r.bottom < 0 || r.right < 0 || r.top > innerHeight || r.left > innerWidth) continue;
    const op = opacity(el);
    if (op <= 0) continue;
    let content = false;
    for (let e = el; e && !content; e = up(e)) content = e.matches && e.matches(CONTENT);
    const rec = (prop, c, extra) => { if (c && c[3] > 0) out.push(Object.assign({prop, value: hex(c), alpha: c[3], opacity: op, where: where(el), content}, extra || {})); };
    rec('background', parse(cs.backgroundColor));
    for (const s of ['Top', 'Right', 'Bottom', 'Left'])
      if (parseFloat(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none') rec('border', parse(cs['border' + s + 'Color']));
    if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) rec('outline', parse(cs.outlineColor));
    if (el instanceof SVGElement && SHAPES.has(el.tagName.toLowerCase()))
      for (const p of ['fill', 'stroke']) rec(p, parse(cs[p]), {ground: hex(ground(el))});
    if ([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
      rec('text', parse(cs.color), {ground: hex(ground(el)), size: parseFloat(cs.fontSize), weight: parseInt(cs.fontWeight),
        family: cs.fontFamily.split(',').map(f => f.trim().replace(/["']/g, ''))[0],
        sample: [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').slice(0, 30)});
    if (cs.backgroundImage !== 'none') out.push({prop: 'background-image', value: cs.backgroundImage.slice(0, 100), where: where(el)});
    if (cs.boxShadow !== 'none') out.push({prop: 'box-shadow', value: cs.boxShadow.slice(0, 100), where: where(el)});
    if (cs.backdropFilter && cs.backdropFilter !== 'none') out.push({prop: 'backdrop-filter', value: cs.backdropFilter, where: where(el)});
    if (el.tagName === 'INPUT' && ['checkbox', 'radio', 'range'].includes(el.type) && cs.appearance !== 'none')
      out.push({prop: 'native-control', value: el.type, where: where(el)});
  }
  return {body: document.body.className, focused: document.hasFocus(), records: out};
})()"""


def role_of(hx):
    return next((k for k, v in ROLES.items() if v.upper() == hx.upper()), None)


def probe_js():
    return PROBE.replace('__CONTENT__', json.dumps(', '.join(CONTENT_SELECTORS)))


def parsed_rules(page, path=THEME):
    """(rules the running browser parses out of the committed file, rules the file holds). A string or a bracket
    left open ends a stylesheet where it happens and says nothing, so the count is the check."""
    text = open(path, encoding='utf8').read()
    bare = COMMENT.sub('', text)
    want = bare.count('{') - len(re.findall(r'@media', bare))
    got = page.eval('((t) => { const s = new CSSStyleSheet(); s.replaceSync(t); return s.cssRules.length; })('
                    + json.dumps(text) + ')')
    return got, want


def screen(port, only=None):
    first = True
    for page in pages(port):
        if only and only not in page.window:
            continue
        if first:
            got, want = parsed_rules(page)
            print(f"{os.path.relpath(THEME, ROOT)}: the browser parses {got} of its {want} rules"
                  f"{'' if got == want else ' -- EVERYTHING AFTER THE FIRST FAILURE IS DROPPED'}\n")
            first = False
        report(page.window, page.eval(probe_js()))
        pixel_report(page)
    return True


# The computed styles cannot see what Chromium draws itself -- a search field's clear glyph, a misspelling's dots,
# a native control, an emoji -- nor what a picture carries. So --screen also photographs each window and reads its
# pixels. A pixel with a readable hue (chroma at or over poles.C_FLOOR) must fall in a family the kit paints -- the
# hue of ACCENT and SELECT, CURSOR's, a signal's -- and be no more chromatic than the kit's own member of it: a blend
# of two kit values gains at most 0.0074, so FAMILY_SLACK is twice that. The first test found the search field's
# blue glyph; the second, Chromium's own red under a misspelling. Content is left out, as above.
FAMILIES = {'home': ('accent', 'select'), 'cursor': ('cursor',), 'success': ('success',), 'warning': ('warning',),
            'destructive': ('destructive',), 'red': ('red',), 'green': ('green',), 'yellow': ('yellow',)}
HUE_REACH = {'home': 20, 'cursor': 20}                  # degrees either side of the family's hue; a signal's is 12
FAMILY_SLACK = 0.015
_AT = r"""((x, y) => { const e = document.elementFromPoint(x, y); if (!e) return '';
  const p = []; for (let n = e; n && p.length < 3; n = n.parentElement) {
    const cls = (n.getAttribute('class') || '').trim().split(/\s+/).filter(c => c && !c.startsWith('ͼ')).slice(0, 2);
    p.unshift(n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (cls.length ? '.' + cls.join('.') : '')); }
  return p.join(' > '); })"""


def pixels(page, top=8):
    """The window photographed: {family: pixels} for the kit's hues on screen, and the clusters of pixels off the
    kit's hues or more chromatic than its own, as lines. Needs Pillow, to read the photograph."""
    from PIL import Image
    shot = base64.b64decode(page.call('Page.captureScreenshot', format='png')['data'])
    im = np.asarray(Image.open(io.BytesIO(shot)).convert('RGB')).astype(float)
    dpr = page.eval('devicePixelRatio') or 1
    _, chroma, hue = ok.lch_grid(im)
    hued = chroma >= P.C_FLOOR
    rects = page.eval(f"[...document.querySelectorAll({json.dumps(', '.join(CONTENT_SELECTORS))})].map(e => {{ "
                      "const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })") or []
    for x0, y0, x1, y1 in rects:
        hued[max(0, int(y0 * dpr)):max(0, int(y1 * dpr) + 1), max(0, int(x0 * dpr)):max(0, int(x1 * dpr) + 1)] = False
    ceiling, on = np.full(chroma.shape, -1.0), {}
    for fam, roles in FAMILIES.items():
        for role in roles:
            _, c0, h0 = ok.lch(ROLES[role])
            near = np.abs((hue - h0 + 180) % 360 - 180) <= HUE_REACH.get(fam, 12)
            ceiling = np.where(near, np.maximum(ceiling, c0 + FAMILY_SLACK), ceiling)
            on[fam] = on.get(fam, 0) + int((hued & near).sum())
    lines = []
    for what, mask in (("off the kit's hues", hued & (ceiling < 0)),
                       ("more chromatic than the kit's own", hued & (ceiling >= 0) & (chroma > ceiling))):
        ys, xs = np.nonzero(mask)
        if not len(xs):
            continue
        cells, first, counts = np.unique((ys // 40) * 100000 + xs // 40, return_index=True, return_counts=True)[0:3]
        for i in np.argsort(-counts)[:top]:
            x, y = int(xs[first[i]]), int(ys[first[i]])
            r, g, b = (int(v) for v in im[y, x])
            lines.append(f"  {counts[i]:6} px {what} near ({x},{y}), e.g. #{r:02X}{g:02X}{b:02X} hue {hue[y, x]:5.1f} "
                         f"C {chroma[y, x]:.3f}  {page.eval(f'{_AT}({x / dpr}, {y / dpr})')}")
    return {f: n for f, n in on.items() if n}, lines


def pixel_report(page):
    try:
        on, lines = pixels(page)
    except ImportError:
        print('pixels: Pillow is not installed, so the photograph is not read\n')
        return
    print('pixels, the window photographed (content left out): '
          + (f'{len(lines)} cluster(s) to look at' if lines else "every readable hue is one the kit paints"))
    for line in lines:
        print(line)
    if on:
        print('  hues on screen by family (a signal\'s must carry its meaning): '
              + ', '.join(f'{f} {n}' for f, n in on.items()))
    print()


def report(window, shot):
    recs = shot['records']
    print(f"=== {window}: body.{shot['body'] or '-'}, {len(recs)} painted values\n")
    content = [r for r in recs if r.get('content')]
    recs = [r for r in recs if not r.get('content')]
    print(f"content, left as Zettlr paints it (§0a): {len(content)} values in "
          f"{len({r['where'] for r in content})} elements\n")
    by = {}
    for r in recs:
        if r['prop'] in ('box-shadow', 'backdrop-filter', 'background-image', 'native-control'):
            continue
        by.setdefault((r['prop'], r['value'], r['alpha'] < 1), []).append(r)
    off = 0
    print("painted values that are not the kit's (content is exempt; check each is content):")
    for (prop, hx, blend), rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if role_of(hx) in RESERVED:
            rs = [r for r in rs if role_of(r.get('ground', '')) not in SEMANTIC_GROUNDS]
            if not rs:
                continue
            prop = f'{prop} (§3 reserves it)'
        elif role_of(hx) and not blend:
            continue
        off += len(rs)
        print(f"  {prop:10} {hx}{' blend' if blend else '      '} {len(rs):4}x  e.g. {rs[0]['where'][-90:]}")
    print(f"\n{sum(len(v) for k, v in by.items() if role_of(k[1]) and not k[2])} values on the kit's ladder, {off} off it")
    print('\ntext pairs as painted (the floor is the tier for the weight and size the element computed; text drawn '
          'inside an icon is a glyph, at the tier of marks):')
    pairs = {}
    glyph = lambda r: ' > svg' in r['where'] or r['where'].startswith('svg')
    for r in recs:
        if r['prop'] == 'text':
            k = (r['value'], r['ground'], 'glyph' if glyph(r) else r['weight'] >= 600, round(r['size']),
                 r['opacity'] < 1 or r['alpha'] < 1)
            pairs.setdefault(k, []).append(r)
    for (t, g, tier, size, faded), rs in sorted(pairs.items(), key=lambda kv: -len(kv[1])):
        lc = apca.lc(t, g)
        floor = 30 if tier == 'glyph' else 60 if tier else 75
        low = abs(lc) < floor                           # a slot at its gamut cap is the gate's 'cap', not a defect
        flag = ('cap' if low and t.upper() in CAPS else 'LOW' if low else 'FADED' if faded else
                'SMALL' if size < 16 and tier != 'glyph' else 'ok')
        weight = 'glyph' if tier == 'glyph' else '700' if tier else '400'
        print(f"  {role_of(t) or t:12} on {role_of(g) or g:12} Lc {lc:6.1f} {size:3}px/{weight:5} "
              f"{flag:5} {len(rs):4}x  e.g. {rs[0]['sample'][:22]!r} {rs[0]['where'][-60:]}")
    faces = {}
    for r in recs:
        if r['prop'] == 'text' and not glyph(r):
            faces.setdefault(r['family'], []).append(r)
    print('\nfaces: ' + ', '.join(f"{f} {len(rs)}x" for f, rs in sorted(faces.items(), key=lambda kv: -len(kv[1]))))
    for extra in ('native-control', 'background-image', 'box-shadow', 'backdrop-filter'):
        rs = [r for r in recs if r['prop'] == extra]
        if rs:
            print(f"\n{extra}: {len(rs)} element(s), e.g. {rs[0]['value'][:90]} on {rs[0]['where'][-60:]}")
    print()



# --- 11. what the checker measures ---------------------------------------------------------------------------
# The pairs this surface authors, by role: text on its ground at the tier it renders at, and marks at theirs. The
# weight follows the ground (THE RULES): a LIGHT panel carries 700, so BLACK on LIGHT is measured at the 16px/700
# tier. `--screen` measures the same pairs as the running app paints them, per element.
PAIRS = [
    (B, W, 75, 'the note, a field, a menu row, a settings card: BLACK at 400'),
    (B, L, 60, 'a LIGHT panel\'s labels at 700: menubar, toolbar, tabs, file manager, sidebar, status bar, popovers'),
    (W, S, 75, 'the current file, a selected row, the chosen result, a hovered button'),
    (D, W, 75, 'descriptions, placeholders, Markdown\'s marks, the gutter\'s labels, comments'),
    (A, W, 75, 'links, tags, citation keys, literals in code'),
    (S, W, 75, 'members, names and types in code'),
    (RED, W, 75, 'error text: a citation that failed to resolve, a diff\'s deletions, a caution\'s markers'),
    (GREEN, W, 75, 'inserted text in a diff'),
    (YELLOW, W, 75, 'warning text: a warning\'s markers, in the ANSI yellow at its gamut cap'),
    (W, B, 75, 'tooltips, captions over an image'),
    (W, D, 75, 'badges, key caps, tokens'),
    (W, A, 75, 'the primary button, a code badge, a drop target'),
    (LD, WN, 75, 'a warning, carrying §3\'s legend'),
    (LL, DS, 75, 'an error, and a hover whose click removes: §3\'s legend'),
    (LL, OK_, 75, 'a finished task: §3\'s legend'),
    (CU, W, 60, 'the caret: §2\'s own pair and its own floor'),
    (A, W, 30, 'a toggle that is on: its glyph'),
    (A, L, 30, 'the pomodoro ring\'s time gone, on the toolbar; the current match\'s outline'),
    (DS, W, 30, 'an error\'s mark: the wavy underline, the gutter square, the diagnostic\'s bar, a misspelling'),
    (YELLOW, W, 30, 'a warning\'s mark'),
    (D, W, 30, 'an informational mark'),
    (B, L, 30, 'a glyph on a panel'),
    (B, W, 30, 'a control\'s outline, a glyph on the field'),
    (D, L, 15, 'the scrollbar\'s thumb on a panel: visible'),
    (L, W, 15, 'the scrollbar\'s thumb on the field: visible'),
]
# Fills under text that keeps its own colour, and the text's tier on them. CodeMirror paints the selection, the
# matches and the marks BEHIND the text, so no fill can be both dE 17.1 from WHITE and a body ground at 400 -- the
# pale-selection trial §2 records. Marked text is set 700; the selection is the platform's shortfall, measured and
# not hidden (as in build/obsidian.py HIGHLIGHTS).
HIGHLIGHTS = [
    (L, B, 'the editor\'s selection'),
    (L, B, '==marked== text, search matches and the open diagnostic\'s range, set 700'),
]
# Grounds that touch. OKLab dE against SURFACE_FLOOR, never Lc (§0e).
ADJACENT = [
    (W, L, 'the note against every panel; a card on the settings page; a menu row on its frame; the active tab'),
    (L, S, 'the current file on the file manager; the heading the caret is under, on the sidebar'),
    (W, S, 'a selected row among WHITE rows'),
    (L, A, 'the primary button on the button strip; a drop target on a panel'),
    (W, A, 'a ticked box on the field'),
    (W, D, 'a badge or a key cap on the field'),
    (L, D, 'a badge on a panel'),
    (W, B, 'a tooltip over the note'),
    (L, B, 'a tooltip over a panel'),
    (W, WN, 'a warning on the field'),
    (W, DS, 'an error on the field'),
    (W, OK_, 'a finished task on the field'),
]
LEGEND_GROUNDS = SEMANTIC_GROUNDS


# --- 12. the checker ---------------------------------------------------------------------------------------------
MIXED = re.compile(r'\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark|image-set)\s*\(')


def _values(css):
    """[(selector, property, value)] of every declaration, comments stripped: what the scans read."""
    out = []
    for media, sel, prop, val, imp in parse_css(css):
        out.append((sel, prop, val))
    return out


def check():
    bad, notes = 0, []

    def fail(msg):
        nonlocal bad
        bad += 1
        notes.append(msg)

    rel = lambda path: os.path.relpath(path, ROOT)
    if not os.path.exists(RECORD):
        print(f'zettlr: {rel(RECORD)} is not recorded yet -- run --record P'); return False
    rows = load_record()
    print(f'{rel(RECORD)}: Zettlr {recorded_version()}, {len(rows)} declarations in '
          f'{len({r[0] for r in rows})} blocks')

    # --- the committed files are what the tables produce -----------------------------------------------------
    for path, text in ((THEME, theme_text()), (SNIPPET, snippet_text())):
        if not os.path.exists(path):
            fail(f'{rel(path)} is not committed: run --write')
        elif open(path).read() != text:
            fail(f'{rel(path)} is not what the tables produce: run --write, or move the edit into build/zettlr.py')

    # --- the file parses as written: an unterminated string or bracket ends the stylesheet there, silently -------
    text_now = open(THEME).read() if os.path.exists(THEME) else ''
    for n, line in enumerate(COMMENT.sub(lambda m: '\n' * m.group(0).count('\n'), text_now).splitlines(), 1):
        if line.count('"') % 2 or line.count("'") % 2:
            fail(f'{rel(THEME)}:{n}: a quote left open -- the browser drops the rest of the file: {line.strip()[:80]}')
    for sel, prop, val in _values(text_now):
        for a, b in ('()', '[]'):
            if sel.count(a) != sel.count(b):
                fail(f'{rel(THEME)}: a bracket left open in "{sel[:80]}"')

    # --- every recorded declaration has a role ----------------------------------------------------------------
    kinds, unclassified = {}, []
    for block, media, sel, prop, val, imp in rows:
        role, note = classify(sel, prop)
        if role is None:
            unclassified.append(f'{sel} {{ {prop}: {val} }}')
            continue
        k = ('left to the platform' if isinstance(role, Keep) else 'inherit' if isinstance(role, Lit)
             else 'a size' if prop_class(prop) == 'size' else 'a face' if prop_class(prop) == 'face'
             else 'none' if role == NONE else role)
        kinds[k] = kinds.get(k, 0) + 1
    print(f'\nevery recorded declaration, and what it becomes ({len(rows) - len(unclassified)} classified):')
    for k in sorted(kinds, key=lambda k: -kinds[k]):
        print(f'  {kinds[k]:5}  {k}')
    for u in unclassified:
        fail(f'NOT CLASSIFIED BY ANY ROW: {u}')

    # --- every literal colour is an --rm-* definition, and every definition is a value the kit authors -----------
    text = open(THEME).read() if os.path.exists(THEME) else theme_text()
    body = COMMENT.sub(' ', text)
    defs = dict((m.group(1), m.group(2).upper()) for m in re.finditer(r'--rm-([a-z-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;', body))
    print(f'\n--rm-* definitions: {len(defs)}')
    for name, hx in defs.items():
        want, tag = ROLES.get(name), ''
        if want is None:
            tag = 'NOT A ROLE THE KIT AUTHORS'; bad += 1
        elif hx != want.upper():
            tag = f'does not match its source ({want})'; bad += 1
        elif P.reserved(hx) and name not in RESERVED:
            tag = 'reserved by §3'; bad += 1
        elif name not in RESERVED and name not in SIGNAL and not P.clear(hx):
            tag = 'POLE: chrome must clear every pole'; bad += 1
        fam, gap, req = P.clearance(hx)
        kind = ('reserved for legend (§3)' if name in RESERVED else
                'a pole by construction: the meaning, present' if name in SIGNAL and P.readable(hx) and gap < req else
                'neutral, no readable hue' if not P.readable(hx) else f'{gap:5.1f}/{req:4.1f} {fam}')
        cap = f'  [{CAPS[hx]}]' if hx in CAPS else ''
        print(f'  --rm-{name:13} {hx}  {kind:44} {SOURCE[name]}{cap} {tag}')
    literal = 0
    for sel, prop, val in _values(text):
        if prop.startswith('--rm-'):
            continue
        for h in HEX.findall(val) + DATA_HEX.findall(val):
            fail(f'{sel[:60]} {{ {prop} }}: the literal {h} outside the --rm-* definitions'); literal += 1
        for m in MIXED.finditer(val):
            fail(f'{sel[:60]} {{ {prop} }}: {m.group(1)}() -- a mixed value is not an authored value'); literal += 1
        words = re.findall(r'(?<![\w#%-])([A-Za-z][A-Za-z-]*)(?![\w-]*\()', re.sub(r'var\([^)]*\)|"[^"]*"', ' ', val))
        for w in words:
            if w.lower() in NAMED:
                fail(f'{sel[:60]} {{ {prop} }}: names the colour "{w}" -- nothing derived it'); literal += 1
    print(f'literal colours outside the definitions: {literal}')

    # --- the pairs and the adjacencies ------------------------------------------------------------------------------
    print("\npairs this surface authors (APCA Lc, signed; the floor is the tier for what the pair carries):")
    for ink, ground, floor, why in PAIRS:
        lc = apca.lc(ROLES[ink], ROLES[ground])
        good = abs(lc) >= floor
        cap = ROLES[ink] in CAPS and abs(lc) >= floor - 1.0
        bad += not good and not cap
        if ink in RESERVED and ground not in LEGEND_GROUNDS:
            fail(f'{ink} on {ground}: §3 reserves {ROLES[ink]} for legend on a semantic ground')
        print(f"  {ink:12} on {ground:12} Lc {lc:7.1f}  floor {floor:3.0f}  {'ok ' if good else 'cap' if cap else 'LOW'}  {why}")
    print("\nfills under text that keeps its colour (the platform's shortfall, measured):")
    for ground, ink, why in HIGHLIGHTS:
        print(f"  {ink:12} on {ground:12} Lc {apca.lc(ROLES[ink], ROLES[ground]):7.1f}  {why}")
    print("\npairs the mirror authors in one rule (a LIGHT ground carries 700, so its tier is 60):")
    seen = {}
    for block, media, sel, decls, notes_ in mirror_rules(rows):
        d = {p_: v for p_, v, imp in decls}
        fg, bg = d.get('color'), d.get('background-color')
        if not fg or not bg or 'var(--rm-' not in fg or 'var(--rm-' not in bg:
            continue
        t, g = fg[9:-1], bg[9:-1]
        seen.setdefault((t, g), []).append(sel)
    for (t, g), sels in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        lc = apca.lc(ROLES[t], ROLES[g])
        floor = 60 if g == 'light' else 75
        good = abs(lc) >= floor
        bad += not good
        if t in RESERVED and g not in LEGEND_GROUNDS:
            fail(f'{sels[0][:60]}: §3 reserves {ROLES[t]} for legend on a semantic ground, not on {g}')
        print(f"  {t:12} on {g:12} Lc {lc:7.1f}  floor {floor:3.0f}  {'ok ' if good else 'LOW'}  {len(sels):3}x  e.g. {sels[0][:52]}")
    print(f"\nsurfaces that touch (OKLab dE; floor {FLOOR}, derived from WHITE against LIGHT):")
    for a, b, why in ADJACENT:
        dE = ok.delta_e(ROLES[a], ROLES[b])
        good = dE >= FLOOR - 0.05
        bad += not good
        print(f"  {a:12} / {b:12} dE {dE:5.1f}  {'ok ' if good else 'BELOW'}  {why}")

    # --- the files the installer writes that are not the theme: no colour in any of them ---------------------------
    for path in (SETTINGS, INSTALLER, SNIPPET):
        if not os.path.exists(path):
            fail(f'{rel(path)} is not committed'); continue
        raw = open(path, errors='ignore').read()
        if path == SNIPPET:
            raw = COMMENT.sub(' ', raw)
            found = [h for sel, prop, val in _values(raw) for h in HEX.findall(val) + [m.group(1) for m in MIXED.finditer(val)]
                     + [w for w in re.findall(r'[A-Za-z][A-Za-z-]{2,}', val) if w.lower() in NAMED]]
        else:
            raw = re.sub(r'^\s*(#|//).*$', '', raw, flags=re.M)
            found = sorted({m.group(0).upper() for m in HEX.finditer(raw)})
        print(f"\n{rel(path)}: {len(found)} colour(s) it writes itself")
        for f in found:
            fail(f'{rel(path)} carries {f}')

    if notes:
        print('\nnotes:')
        for n in notes:
            print(f'  {n}')
    print(f"\nzettlr: {'every declaration classified; every value, pair and adjacency clears' if not bad else str(bad) + ' DEFECT(S)'}")
    return bad == 0


# --- 13. the installed build: a report, never a gate --------------------------------------------------------------
def coverage():
    """The installed build's stylesheets against the record: what was added, changed or dropped since. CodeMirror's
    CSS and the run-time stylesheet need a running window, so they are re-read by --record, not here."""
    path = installed_asar()
    if not path:
        print('coverage: no Zettlr app.asar found (looked in ' + ', '.join(ASARS) + ')'); return True
    version = json.loads(asar_read(path, 'package.json')).get('version', '?')
    live, seen = [], set()
    for w in WINDOWS:
        js = asar_read(path, f'.webpack/renderer/{w}/index.js').decode('utf8', 'replace')
        for css in bundle_sheets(js):
            h = hashlib.sha1(css.encode()).hexdigest()[:8]
            if h not in seen:
                seen.add(h)
                live += parse_css(css)
    cvars = colour_vars(live) | {'--system-accent-color', '--system-accent-color-contrast'}
    now = {(m, s_, p_, v, i) for m, s_, p_, v, i in _recordable(live, cvars)}
    was = {(m, s_, p_, v, i) for b, m, s_, p_, v, i in load_record() if b.startswith('sheet ')}
    print(f'{path}: Zettlr {version}; recorded against {recorded_version()}\n')
    added, gone = sorted(now - was), sorted(was - now)
    print(f'declarations in the installed build the record does not hold ({len(added)}):')
    for m, s_, p_, v, i in added:
        role, _ = classify(s_, p_)
        print(f"  {s_[:70]} {{ {p_}: {v[:40]} }}  -> {role if role is not None else 'NOT CLASSIFIED'}")
    print(f'\ndeclarations the record holds that the installed build no longer makes ({len(gone)}):')
    for m, s_, p_, v, i in gone:
        print(f'  {s_[:70]} {{ {p_}: {v[:40]} }}')
    if added or gone:
        print('\nre-record (--record P), classify anything new, and --write.')
    return True


def _print_derivations():
    print("=== Zettlr's grey ramp, each SNAPPED to the nearest of §2's four by lightness (the backstop) ===")
    for name, hx in ZETTLR_GREYS.items():
        role = snap(hx)
        print(f"  {name:8} {hx}  L {ok.lch(hx)[0]:.4f}  ->  {role:6} {ROLES[role]}  dE {ok.delta_e(hx, ROLES[role]):5.1f}")
    print("\n=== the roles the theme may name, and nothing else ===")
    for name, hx in ROLES.items():
        fam, gap, req = P.clearance(hx)
        tag = ('reserved for legend (§3)' if name in RESERVED else
               'a pole by construction: the meaning, present' if name in SIGNAL and P.readable(hx) and gap < req else
               'neutral, no readable hue' if not P.readable(hx) else f'clears {gap:.1f}deg from {fam}, needs {req:.1f}')
        print(f"  --rm-{name:13} {hx}  {tag:44} {SOURCE[name]}")
    print("\n=== §5's faces ===")
    for name, face in FACES.items():
        print(f"  --rm-face-{name:5} {face}")


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--coverage' in sys.argv:
        sys.exit(0 if coverage() else 1)
    if '--record' in sys.argv:
        record(sys.argv[sys.argv.index('--record') + 1]); sys.exit(0)
    if '--write' in sys.argv:
        write(); sys.exit(0)
    if '--screen' in sys.argv:
        i = sys.argv.index('--screen')
        only = sys.argv[i + 2] if len(sys.argv) > i + 2 else None
        sys.exit(0 if screen(sys.argv[i + 1], only) else 1)
    sys.exit(0 if check() else 1)
