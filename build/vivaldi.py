"""The Vivaldi surface: write the theme, then check what is committed. AUTHORITY.md is the authority.

Vivaldi draws its whole interface -- tabs, toolbars, panels, the start page, the settings window -- as one web
page, window.html, inside a Chromium that shows the web in <webview>s beneath it. A theme reaches that page two
ways, and this surface uses both. Three things measured off the installed build (the Arch `vivaldi` package,
8.2.4133.76, 2026-09-29) shape it:

  THE THEME IS FOUR COLOURS, AND THE REST IS DERIVED. A native Vivaldi theme is a JSON entry in the profile's
    Preferences: background, foreground, highlight, accent, a window colour, and switches for transparency, blur,
    a background image and "accent from the page". From the four colours Vivaldi's own script derives 43 colour
    variables for the chrome by lightening, darkening and mixing, and 30 more from the background image, and sets
    them inline on #browser; its stylesheet declares 13 more as color-mix() blends of those. Given the kit's four,
    32 of the 43 come out off the ladder -- a #C9BCC1 address field, a #000000 "intense" foreground that §3
    reserves -- so the native theme alone is near the kit and is not it. The theme is still installed: it switches off the transparency, the blur, the
    background image and the page-coloured accent, which no stylesheet reaches, and it is what shows if the
    stylesheet does not load.

  THE STYLESHEET IS AN EXPERIMENT. vivaldi://experiments > "Allow CSS modifications" (the feature VivaldiCssMods,
    stored in Local State as `vivaldi-css-mods@1`) makes Vivaldi load every .css file in the folder named at
    Settings > Appearance > Custom UI Modifications (vivaldi.appearance.css_ui_mods_directory) into window.html,
    after its own. Every derived variable is pinned there to a kit value, declared on #browser and on every
    element under it with !important: Vivaldi re-declares its variables on descendants -- the tab strip, the
    non-key header, break mode -- and a value inherited from #browser loses to one declared at the element,
    whatever its importance (PLATFORM.md Firefox). The whole stylesheet is scoped to #browser.theme-id-Remainder,
    so selecting another theme in Settings > Themes undoes it.

  THE WINDOW KNOWS WHEN IT IS KEY. #browser carries `hasfocus` or `isblurred`, so this is the fourth surface on
    this desktop that can show key state, and it shows it the way Firefox's tab strip does: the strip that holds
    the tabs is the titlebar, wherever it is -- ACCENT carrying WHITE when key, LIGHT carrying BLACK at 700 when
    not -- and so is the header above it when the tabs are at the side.

  THE UI RENDERS UNDER THE SIZE THE FLOORS ASSUME. Vivaldi writes its chrome's sizes as literals, 11.5 px in 110
    rules and 13 px in 34, and every floor in §0e assumes about 16 (§5). Its own User Interface Zoom at 140% was
    tried first and retired: it scaled icons, bars and spacing with the text. So the text alone is raised, to
    CHROME_PX (CHOSEN, below: 14 px, under the floors' 16), rule by rule from a record of Vivaldi's own sizes, and
    the checker prints what that costs against the floors rather than calling it a pass.

So the surface is a role table over a record of the platform's variables, and the derivation ships here
(CONTRIBUTING.md §8):

  THE THEME    the native entry (theme.json): §2's four as Vivaldi's four, and every switch that would put a
               value the kit did not author under the chrome, off.
  ROLES        every colour variable Vivaldi defines, on one of the kit's values, in the base scope and in each
               region that changes its ground: the key strip, the non-key window, the fields. Weight follows the
               ground, as in worksafe/firefox/: a LIGHT surface carries BLACK at 700 (Lc 61.2, the 16px/700
               tier), a WHITE one 400 (Lc 91.8), the ACCENT strip WHITE at 400 (Lc -78.5).
  SIZES        every size Vivaldi sets under CHROME_PX, recorded off the installed build (build/vivaldi_platform
               .json, by --record) and raised to it at its own selector and specificity, later in the cascade.
  RULES        what no variable reaches, found by --screen on the running window.
  SETTINGS     settings.json: the theme selected, and §0's larger half -- the tips, the nags, the promotions,
               the motion -- switched off by preference.
  DECLUTTER    motion and blur, as a second stylesheet in the same folder, so it is a switch (install.sh
               --no-declutter). It names no colour.

    python3 build/vivaldi.py              check every value, pair and adjacency in the committed theme
    python3 build/vivaldi.py --derive     the roles, the sizes, and the native theme's own derivation, measured
    python3 build/vivaldi.py --write      regenerate the stylesheet, the declutter and theme.json
    python3 build/vivaldi.py --record     re-record Vivaldi's own sizes from the installed build
    python3 build/vivaldi.py --coverage   the installed build's variables and literals against the record (a report)
    python3 build/vivaldi.py --screen P   what a running Vivaldi paints, read over its DevTools port P: every
                                          window's computed styles, and each window photographed (a report;
                                          worksafe/vivaldi/README_VIVALDI.md says how)
"""
import base64, io, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca, cosmic as C
from zettlr import Page      # the stdlib DevTools client, carried from build/zettlr.py rather than copied

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
VIV = os.path.join(ROOT, 'worksafe', 'vivaldi')
THEME = os.path.join(VIV, 'remainder.css')
SNIPPET = os.path.join(VIV, 'remainder-declutter.css')
THEME_JSON = os.path.join(VIV, 'theme.json')
SETTINGS = os.path.join(VIV, 'settings.json')
INSTALLER = os.path.join(VIV, 'install.sh')
VIVALDI_RES = '/opt/vivaldi/resources/vivaldi'

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
FLOOR = PAL['surface_floor_dE']
_T = C.terminal()


# --- 1. the roles ----------------------------------------------------------------------------------
class R(str):
    """A kit role. The stylesheet writes it as var(--rm-NAME); `none` is written as transparent."""
    def css(self):
        return 'transparent' if self == 'none' else f'var(--rm-{self})'


W, L, D, B = R('white'), R('light'), R('dark'), R('black')
A, S, CU = R('accent'), R('select'), R('cursor')
OK_, WN, DS = R('success'), R('warning'), R('destructive')
LL, LD = R('legend-light'), R('legend-dark')
RED, GREEN, YELLOW = R('red'), R('green'), R('yellow')
NONE = R('none')

# Every value the theme may define, and where it comes from. Nothing else may appear in the stylesheet.
ROLES = {
    'white': PAL['neutrals']['WHITE'], 'light': PAL['neutrals']['LIGHT'],
    'dark': PAL['neutrals']['DARK'], 'black': PAL['neutrals']['BLACK'],
    'accent': PAL['chrome']['ACCENT'], 'select': PAL['chrome']['SELECT'], 'cursor': PAL['chrome']['CURSOR'],
    'success': C.SEMANTIC['SUCCESS'], 'warning': C.SEMANTIC['WARNING'], 'destructive': C.SEMANTIC['DESTRUCTIVE'],
    'legend-light': '#FFFFFF', 'legend-dark': '#000000',
    # signal TEXT, from build/cosmic.py's ANSI normal tier -- the values worksafe/obsidian/ uses for it
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


# --- 2. the native theme ------------------------------------------------------------------------------
# The entry the installer puts in vivaldi.themes.user and selects. Every key is the shape of the shipped themes
# in prefs_definitions.json (vivaldi.themes.system), 8.2.4133.76; the colours are the kit's, and each switch is
# set so that nothing Vivaldi composites shows under the chrome.
THEME_ID = 'Remainder'
NATIVE = {
    'engineVersion': 1, 'id': THEME_ID, 'name': 'Remainder', 'version': 1, 'url': '',
    'colorBg': 'light',             # the chrome: toolbars, panels, the status bar (§2)
    'colorFg': 'black',             # its text
    'colorHighlightBg': 'select',   # selected rows and selected text (§2)
    'colorAccentBg': 'accent',      # the key titlebar (§2)
    'colorWindowBg': 'white',       # what shows behind a page while it loads: the field
    'colorPosition': 'tabbar',      # "Accent Color on Tab Bar": the strip that holds the tabs is the titlebar
    'accentOnWindow': True,         # the same switch, as Vivaldi writes it for older readers
    'accentFromPage': False,        # a page's own colour on the strip would be a colour nobody here authored
    'accentSaturationLimit': 1,
    'preferSystemAccent': False,    # the desktop's accent is the desktop's, and on COSMIC it is not §2's
    'alpha': 1,                     # opaque: under 0.5 Vivaldi composites the background image through the chrome
    'blur': 0,                      # §0: no blur
    'backgroundImage': '', 'backgroundPosition': 'stretch', 'backgroundSource': '',   # nothing under the chrome
    'contrast': 0,                  # the derivation's contrast boost moves every derived value; the sheet pins them
    'radius': 0,                    # §5: square
    'transparencyTabBar': False, 'transparencyTabs': False,
}


def native():
    """The theme entry with its colours filled in, as Vivaldi stores it."""
    return {k: (ROLES[v].upper() if k.startswith('color') and k != 'colorPosition' else v) for k, v in NATIVE.items()}


# --- 3. the size ----------------------------------------------------------------------------------------
# CHOSEN (§0c, §5) by Byron, 2026-09-29, and under the floors: the chrome's text at 14 px. Vivaldi writes its sizes
# as literals -- 11.5 px in 110 rules, 13 px in 34, 10 to 12 px in 22 more (style/common.css, 8.2.4133.76) -- under a
# 13 px root on #app, and every floor in §0e assumes about 16. The first answer was Vivaldi's own UI zoom at 140%,
# the least tenth that lifts 11.5 px to 16; it scaled the icons, bars and spacing with the text, on a desktop
# already scaled to 175%, and was looked at and retired the same day (CONTRIBUTING.md §9). So the text alone is
# raised, as worksafe/obsidian/ and worksafe/zettlr/ raise theirs, and to 14 px, not 16: every size Vivaldi sets
# under CHROME_PX is RECORDED off the installed build (RECORD, by --record) and answered at its own selector, at
# its own specificity -- the scope is in :where() -- so it wins by coming later, exactly where Vivaldi's rule did,
# and never over a more specific rule of Vivaldi's that sets a larger size (an :is() scope did, and shrank the
# welcome pages' 16 px to 14); the root takes CHROME_PX too, for everything that inherits. What 14 px costs against the
# floors is measured by the checker and printed beside the pairs, and --screen checks that no text got smaller.
CHROME_PX = 14
RECORD = os.path.join(ROOT, 'build', 'vivaldi_platform.json')
SCOPE_SUBJECT = ':where(#browser.theme-id-Remainder *)'   # a descendant of the kit's #browser, at no specificity


def record():
    """{'build', 'recorded', 'sizes': [[selector list, px], ...]} -- Vivaldi's own sizes under CHROME_PX."""
    if not os.path.exists(RECORD):
        return {'build': '?', 'recorded': '?', 'sizes': []}
    return json.load(open(RECORD))


CONDITIONAL = ('@media', '@container', '@supports')


def _style_rules(css):
    """(the @media / @container conditions around it, selector list, body) for every style rule of a stylesheet,
    in order. A rule inside @keyframes, @property or @position-try is not a style rule and is not read."""
    out, stack, buf, i = [], [], '', 0
    css = COMMENT.sub('', css)
    while i < len(css):
        ch = css[i]
        if ch == '{':
            prelude, buf = ' '.join(buf.split()), ''
            if prelude.startswith('@') and prelude.split()[0] in CONDITIONAL:
                stack.append(prelude); i += 1; continue
            depth, j = 1, i + 1
            while depth:
                depth += {'{': 1, '}': -1}.get(css[j], 0); j += 1
            if not prelude.startswith('@'):
                out.append((tuple(stack), prelude, css[i + 1:j - 1]))
            i = j; continue
        if ch == '}':
            if stack:
                stack.pop()
            buf = ''
        elif ch == ';':
            buf = ''
        else:
            buf += ch
        i += 1
    return out


def small_sizes(css):
    """[[conditions, selector list, px]] for every font-size a stylesheet sets in px under CHROME_PX, in the order it
    sets them, each with the @media or @container conditions it holds under: a size Vivaldi sets for a narrow
    window only is raised for a narrow window only (taken without its condition, the welcome pages' 16 px went to
    14 wherever the window was wide)."""
    out = []
    for conds, sel, body in _style_rules(css):
        for d in re.split(r';(?![^(]*\))', body):
            if ':' not in d:
                continue
            k, v = d.split(':', 1)
            m = re.fullmatch(r'([\d.]+)px(\s*!important)?', v.strip())
            if k.strip() == 'font-size' and m and float(m.group(1)) < CHROME_PX:
                out.append([list(conds), ', '.join(_split_top(sel)), float(m.group(1))])
    return out


def _subject_scoped(sel):
    """One complex selector, matching only inside the kit's #browser at its own specificity: SCOPE_SUBJECT on its
    subject, before a pseudo-element if it ends in one."""
    depth, cut = 0, len(sel)
    for i, ch in enumerate(sel):
        depth += {'(': 1, ')': -1}.get(ch, 0)
        if depth == 0 and sel.startswith('::', i):
            cut = i
            break
    head, pseudo = sel[:cut], sel[cut:]
    if not head or head[-1] in ' >+~':
        head += '*'
    return head + SCOPE_SUBJECT + pseudo


def size_rules():
    return [(conds, ', '.join(_subject_scoped(x) for x in _split_top(sel)), px) for conds, sel, px in record()['sizes']]


# --- 4. the role table ------------------------------------------------------------------------------------
# Every variable the stylesheet decides, with its reason where the reason is not the variable's name. Declared with
# !important on #browser.theme-id-Remainder and on every element beneath it (the header says why), so a region
# changes a ground by re-declaring the variables that read it, one specificity step up.
MONTSERRAT, HACK = '"Montserrat", sans-serif', '"Hack", monospace'
BASE = '#browser.theme-id-Remainder'
VARS = [
    ('§5: the faces Vivaldi reads from variables. The interface face itself is set by rule, below.', [
        ('--monospaceFont', '"Hack"'), ('--sansSerifFont', '"Montserrat"'),
    ]),
    ('§5: every corner square. The theme sets --radius to 0; Vivaldi derives six more beside it, and '
     '--radiusRound is how it draws a pill or a circle.', [
        ('--radius', '0'), ('--radiusHalf', '0'), ('--radiusCap', '0'), ('--radiusRounded', '0'),
        ('--radiusRoundedLess', '0'), ('--radiusRound', '0'), ('--radiusWindow', '0'),
    ]),
    ('Text. BLACK on the LIGHT chrome, where the rules set it at 700 (Lc 61.2); the fields scope, below, gives '
     'secondary text DARK on WHITE (Lc 79.0). DARK on LIGHT is Lc 48.4, under every text tier, so the chrome has '
     'no secondary tone: secondary there is BLACK, and the weight is what the pair is read at.', [
        ('--colorFg', B), ('--colorFgIntense', B, 'Vivaldi derives #000000 here from BLACK, which §3 reserves'),
        ('--colorFgFaded', B), ('--colorFgFadedMore', B),
        ('--colorFgFadedMost', D, 'disabled text and the lines Vivaldi draws in it: DARK is §2\'s disabled'),
    ]),
    ('Grounds. LIGHT is the chrome; every derived shade Vivaldi lightens toward a field is WHITE, and every shade '
     'it darkens for a hover or a press is WHITE too: the other tone, which carries the BLACK the control keeps '
     '(Lc 91.8). A shade darker than LIGHT that kept BLACK would sit under every text tier.', [
        ('--colorBg', L), ('--colorBgAlphaBlur', L), ('--browserBackgroundColor', W),
        ('--colorBgDark', W, 'a toolbar button hovered'), ('--colorBgDarker', W, 'pressed, and behind a loading page'),
        ('--colorBgLight', L, 'popups and dialogs: floating, so LIGHT, as in worksafe/firefox/'),
        ('--colorBgLighter', W), ('--colorBgLightIntense', W), ('--colorBgIntense', W, 'fields: the address bar, search, inputs'),
        ('--colorBgIntenser', W), ('--colorBgInverse', W), ('--colorBgInverser', L), ('--colorBgFaded', L),
    ]),
    ('Blends Vivaldi declares in its stylesheet as color-mix() of the above. A blend is not an authored value and '
     'nothing downstream can measure one (CONTRIBUTING.md §8), so each is the kit value its use needs.', [
        ('--colorFgAlpha', L, 'a selected row whose list is not focused, and the counters on a row'),
        ('--colorBgAlpha', L), ('--colorBgAlphaHeavy', W), ('--colorBgAlphaHeavier', W),
        ('--colorHighlightBgAlpha', W, 'the open panel\'s button: WHITE, the field it opens'),
        ('--colorHighlightFgAlpha', W), ('--colorHighlightFgAlphaHeavy', B, 'a count on a SELECT row: WHITE on BLACK'),
        ('--colorAccentBgAlpha', B, 'a hovered tab on the ACCENT strip: BLACK, since SELECT is dE 11.8 from ACCENT'),
        ('--colorAccentBgAlphaHeavy', A, 'an inactive tab: Vivaldi washes the strip at 30%; here it is the strip'),
        ('--colorAccentFgAlpha', W),
        ('--colorSuccessBgAlpha', L), ('--colorWarningBgAlpha', L), ('--colorErrorBgAlpha', L),
    ]),
    ('Selection (§2): SELECT carrying WHITE, Lc -87.5.', [
        ('--colorHighlightBg', S), ('--colorHighlightBgFaded', S), ('--colorHighlightBgDark', S),
        ('--colorHighlightFg', W, 'Vivaldi derives #FFFFFF here, which §3 reserves'),
    ]),
    ('The key titlebar (§2): ACCENT carrying WHITE at 400, Lc -78.5. A hover or a press on it is BLACK.', [
        ('--colorAccentBg', A), ('--colorAccentBgAlphaBlur', A), ('--colorTabBar', A),
        ('--colorAccentBgDark', A, 'an inactive tab: the strip itself, its title WHITE (Vivaldi darkens the accent)'),
        ('--colorAccentBgDarker', B, 'pressed'), ('--colorAccentBgFaded', A),
        ('--colorAccentBgFadedMore', L, 'the keyword badge in the address field'),
        ('--colorAccentBgFadedMost', A, 'a focused search field\'s outline: focus is ACCENT (§2)'),
        ('--colorAccentBorder', A), ('--colorAccentBorderDark', A),
        ('--colorAccentFg', W, 'Vivaldi derives #FFFFFF here'), ('--colorAccentFgFaded', W),
    ]),
    ('Lines. §5 draws no rule thinner than the rule: a boundary inside the window is a change of tone -- WHITE '
     'against LIGHT, dE 17.1 -- and draws nothing. The one that stays is the scrollbar\'s thumb, which is a mark.', [
        ('--colorBorder', NONE), ('--colorBorderSubtle', NONE), ('--colorBorderDisabled', NONE),
        ('--colorBorderIntense', D, 'the scrollbar thumb: DARK, Lc 79.0 on WHITE and 48.4 on LIGHT'),
    ]),
    ('The kit\'s own: the ground of a button, the other tone from what it sits on -- WHITE on the chrome, LIGHT on a '
     'field (the fields scope). Vivaldi has no variable for it; it fills a button with a gradient.', [
        ('--rmButtonBg', W),
    ]),
    ('§3: the three semantic grounds, each with its legend -- the one place #FFFFFF and #000000 may appear.', [
        ('--colorSuccessBg', OK_), ('--colorSuccessFg', LL), ('--colorWarningBg', WN), ('--colorWarningFg', LD),
        ('--colorErrorBg', DS), ('--colorErrorFg', LL),
    ]),
    ('The image-derived set, which the engine sets always and a stylesheet reads only under a transparent strip or '
     'the unified style; the theme turns both off, so these are a backstop. --colorImageFg and its three siblings '
     'are left undeclared on purpose: Vivaldi reads the tab strip\'s text as var(--colorImageFg, '
     'var(--colorAccentFg)), and declaring one would take the strip\'s text away from the accent.', None),
]
IMAGE_POSITIONS = ('Center', 'Top', 'Right', 'Bottom', 'Left')
IMAGE_SUFFIXES = {'Fg': B, 'FgAlpha': B, 'FgAlphaHeavy': B, 'Bg': L, 'BgAlpha': L, 'BgAlphaHeavy': L}


def _image_decls():
    return [(f'--colorImage{pos}{suf}', role) for pos in IMAGE_POSITIONS for suf, role in IMAGE_SUFFIXES.items()]


def _vars():
    for title, decls in VARS:
        yield title, (_image_decls() if decls is None else decls)


# Regions that change the ground, each re-declaring what reads it. A scope's selectors are written with the scope
# and its every descendant, so a variable a region re-declares cannot be undone by an inherited one. They are
# listed lowest first, each outranking the one before it wherever both can match, and the checker proves it.
# The strip: the header, the tab bar wherever it is, and the window's own title bar, which auto-hide moves out of the
# header to slide it over the page -- found on this machine's own profile, 2026-09-29, where it stayed LIGHT.
STRIP = ':is(#header, .tabbar-wrapper, #titlebar)'
NONKEY = (f'{BASE}.isblurred',)
NONKEY_TAB = (f'{BASE}.isblurred {STRIP} .tab.active',)
KEY_STRIP = (f'{BASE}.hasfocus.color-behind-tabs-on {STRIP}',)
KEY_TAB = (f'{BASE}.hasfocus.color-behind-tabs-on {STRIP} .tab.active',)
# #browser carries nothing that says a window is private; the address toolbar holds Vivaldi's own indicator, which a
# private window renders whether or not that toolbar is shown, so the window is found by it.
PRIVATE_STRIP = (f'{BASE}.hasfocus.color-behind-tabs-on:has(.UrlBar-PrivateWindowIndicator) {STRIP}',)
# A field outranks the key strip it may sit in -- the address field is on the strip when the tabs are at the side --
# so its qualifier is the base's, repeated: the same element, more steps of specificity, nothing else matched.
FIELDS = (f'#browser{BASE}.theme-id-Remainder.theme-id-Remainder.theme-id-Remainder :is(.UrlBar-AddressField, .SearchField, '
          '.SpeedDialView-SearchField, .dashboard-widget, .vivaldi-settings .settings-content, '
          '.manager-content, input, textarea, select)',)
SCOPES = [
    ('non-key', NONKEY, None,
     'A window that is not key: its strip is LIGHT carrying BLACK at 700 (§2), and nothing in it is ACCENT.', [
         ('--colorAccentBg', L), ('--colorAccentBgAlphaBlur', L), ('--colorTabBar', L), ('--colorAccentBgFaded', L),
         ('--colorAccentBorder', L), ('--colorAccentBorderDark', L), ('--colorAccentBgFadedMost', L),
         ('--colorAccentFg', B), ('--colorAccentFgFaded', B),
         ('--colorAccentBgDark', L), ('--colorAccentBgDarker', W),
         ('--colorAccentBgAlpha', W), ('--colorAccentBgAlphaHeavy', L),
     ]),
    ('non-key tab', NONKEY_TAB, 'non-key',
     'The current tab of a non-key window is the other tone, WHITE, so it still reads on the LIGHT strip (dE 17.1).', [
         ('--colorBg', W), ('--colorBgDark', L), ('--colorAccentBgAlpha', L),
     ]),
    ('key strip', KEY_STRIP, None,
     'The strip that holds the tabs, and the header when the tabs are at the side: ACCENT carrying WHITE. Its '
     'ground is the accent wherever Vivaldi paints it with the background instead; a hover is BLACK.', [
         ('--colorBg', A), ('--colorBgAlphaBlur', A),
         ('--colorFg', W), ('--colorFgFaded', W), ('--colorFgFadedMore', W), ('--colorFgIntense', W),
         ('--colorBgDark', B), ('--colorBgDarker', B), ('--colorBgAlphaHeavy', B), ('--colorBgAlphaHeavier', B),
     ]),
    ('private strip', PRIVATE_STRIP, 'key strip',
     'A private window. Vivaldi\'s own private theme says so with a violet chrome, a hue carrying a state, which §6.8 '
     'gives to no chrome hue; its indicator sits in the address toolbar, which a layout can hide. Here the key strip '
     'is BLACK instead of ACCENT -- the state carried by tone, which §6.8 permits -- and carries WHITE at 400 (Lc '
     '-92.3); a hover is DARK. BLACK and not DARK: DARK is dE 9.2 from ACCENT, under the floor, so a private window '
     'would not read as a different one. Not key, a private window is LIGHT like every other: key state is the one '
     'the strip carries first.', [
         ('--colorTabBar', B), ('--colorAccentBg', B), ('--colorAccentBgAlphaBlur', B), ('--colorBg', B),
         ('--colorBgAlphaBlur', B), ('--colorAccentBgDark', B), ('--colorAccentBgAlphaHeavy', B),
         ('--colorAccentBgFaded', B), ('--colorAccentBgAlpha', D), ('--colorBgDark', D), ('--colorBgDarker', D),
         ('--colorBgAlphaHeavy', D), ('--colorBgAlphaHeavier', D),
     ]),
    ('key tab', KEY_TAB, 'key strip',
     'The current tab on the key strip is the toolbar\'s LIGHT, and carries BLACK at 700 like the toolbar.', [
         ('--colorBg', L), ('--colorBgAlphaBlur', L), ('--colorAccentFg', B), ('--colorAccentFgFaded', B),
         ('--colorFg', B), ('--colorFgFaded', B), ('--colorFgFadedMore', B), ('--colorFgIntense', B),
         ('--colorBgDark', W), ('--colorBgDarker', W), ('--colorAccentBgAlpha', W),
     ]),
    ('fields', FIELDS, None,
     'A field is WHITE: its text 400, secondary text DARK (Lc 79.0), a hover the other tone, LIGHT. On the strip '
     'Vivaldi paints the address field in the accent\'s dark shade with the accent\'s own text until it is focused; '
     'here it is a field there too, as worksafe/firefox/\'s urlbar is.', [
         ('--colorBg', W), ('--colorFg', B), ('--colorFgIntense', B), ('--colorFgFaded', D), ('--colorFgFadedMore', D),
         ('--colorBgDark', L), ('--colorBgDarker', L), ('--colorBorderIntense', L), ('--rmButtonBg', L),
         ('--colorAccentBgDark', W), ('--colorAccentBgDarker', W), ('--colorAccentFg', B), ('--colorAccentFgFaded', D),
     ]),
]

# Rules for what no variable reaches. Values are written with {role} placeholders; nothing else may carry a colour.
RULES = [
    ('§5: the interface face. Vivaldi names system-ui; the kit names Montserrat, in its Medium and ExtraBold cuts.',
     f'{BASE}, {BASE} :is(button, input, textarea, select)', [('font-family', f'{MONTSERRAT} !important')]),
    ('Weight follows the ground (§2): the LIGHT chrome carries BLACK at 700, Lc 61.2.',
     f'{BASE} :is(.mainbar, #footer, #panels-container, .toolbar-statusbar)', [('font-weight', '700')]),
    ('...and the strip goes bold when the window goes non-key.',
     f'{BASE}.isblurred {STRIP}', [('font-weight', '700')]),
    ('The current tab carries BLACK at 700 in both states: on LIGHT when the window is key, where 700 is the tier, '
     'and on WHITE when not, where it costs nothing -- weight is safe in one direction only (AUTHORITY.md §5).',
     f'{BASE} {STRIP} .tab.active', [('font-weight', '700')]),
    ('The window\'s title bar takes its text from the strip it is part of. Under auto-hide it sits in a wrapper '
     'outside the strip and inherits that wrapper\'s colour, BLACK, onto ACCENT.',
     f'{BASE} #titlebar', [('color', 'var(--colorFg)')]),
    ('The window buttons sit on the strip and take its ground; Vivaldi gives them a black wash of their own.',
     f'{BASE} .window-buttongroup button', [('background-color', 'transparent'), ('opacity', '1')]),
    ('', f'{BASE} .window-buttongroup button:hover', [('background-color', 'var(--colorBgDark)')]),
    ('§3: closing a window is the one destructive act on the strip, and its legend is #FFFFFF.',
     f'{BASE} .window-buttongroup button.window-close:hover',
     [('background-color', '{destructive}'), ('color', '{legend-light}'), ('fill', '{legend-light}')]),
    ('§5: no line where the panel bar meets the page; Vivaldi draws one in a black wash.',
     f'{BASE} #panels-container', [('border-color', 'transparent')]),
    ('Opacity is a blend: a title at 0.8 over its ground is a value nobody authored. A disabled label is DARK (§2), '
     'not faded.', f'{BASE} :is(.dashboard-widget-header .title, .zoom-percent)', [('opacity', '1')]),
    ('', f'{BASE} .zoom-percent.disabled', [('color', '{dark}')]),
    ('A field carries its text at 400 wherever it sits, the bold toolbar included: BLACK on WHITE is Lc 91.8.',
     f'{BASE} :is(.UrlBar-AddressField, .SearchField, input, textarea, select)', [('font-weight', '400')]),
    ('A side panel is LIGHT, as worksafe/firefox/\'s sidebar and worksafe/obsidian/\'s docks are, and its labels BLACK '
     'at 700; its title too, which Vivaldi sets large and light. Its fields are WHITE, the ones Vivaldi leaves '
     'transparent to edit a bookmark in place included; no line where the panel meets the page.',
     f'{BASE} #panels-container :is(h1, h2, h3)', [('font-weight', '700')]),
    ('', f'{BASE} #panels-container :is(input[type=text], input[type=search], input:not([type]), textarea)',
     [('background-color', 'var(--colorBgIntense)')]),
    ('', f'{BASE} :is(#panels-container, .panel-group)', [('border-color', 'transparent')]),
    ('A drop-down is a field: WHITE, flat. Vivaldi fills it with a gradient.',
     f'{BASE} select', [('background-image', 'none'), ('background-color', 'var(--colorBgIntense)')]),
    ('A box or a radio button is a control, and its outline is its own glyph: BLACK, as on worksafe/zettlr/ and '
     'worksafe/obsidian/ -- without it a box is WHITE on a WHITE page. Vivaldi insets a black wash in it.',
     f'{BASE} :is(input[type=checkbox], input[type=radio])',
     [('border', '1px solid {black}'), ('box-shadow', 'none')]),
    ('A field set in a card or on a settings page is WHITE on WHITE, so it takes its outline, the control\'s own glyph, '
     'BLACK. The address and search fields sit on the chrome and read by their tone alone, as worksafe/firefox/\'s do.',
     f'{BASE} :is(.dashboard-widget, .vivaldi-settings .settings-content, .dialog-content, .modal-wrapper) '
     ':is(input[type=text], input[type=number], input[type=url], input[type=email], input[type=password], '
     'input[type=search], input:not([type]), textarea, select)',
     [('border', '1px solid {black}'), ('box-shadow', 'none'), ('padding-inline', '4px')]),
    ('A box or a radio button that is on is a toggle, and §2 gives toggles ACCENT; its tick is WHITE (Lc -78.5).',
     f'{BASE} :is(input[type=checkbox], input[type=radio]):checked',
     [('background-color', '{accent}'), ('border-color', '{accent}'), ('color', '{white}')]),
    ('Settings: the list of pages is a LIGHT panel, its labels BLACK at 700, and the page itself the WHITE field; '
     'the page open is the selected row, SELECT carrying WHITE (§2).',
     f'{BASE} .vivaldi-settings .settings-sidebar', [('font-weight', '700')]),
    ('', f'{BASE} .vivaldi-settings .settings-sidebar .button-category.category-selected',
     [('background-color', '{select}'), ('color', '{white}'), ('fill', '{white}')]),
    ('The tabs of a tabbed card -- Library and Editor in Settings > Themes, a widget\'s views -- sit on LIGHT: '
     'BLACK at 700, where Vivaldi fades the ones not chosen to DARK at 400 (Lc 48.4).',
     f'{BASE} .TabbedView-List button', [('color', 'var(--colorFg)'), ('font-weight', '700')]),
    ('The first-run pages mark the pages already read with BLACK at 0.3, a blend: here they are DARK, and a page not '
     'yet read is its BLACK outline alone.',
     f'{BASE} .welcome-navigation .nav-page:not(.nav-page-completed, .nav-page-active)', [('background-color', 'transparent')]),
    ('', f'{BASE} .welcome-navigation .nav-page.nav-page-completed', [('background-color', '{dark}')]),
    ('No line around a badge (§5).', f'{BASE} .button-badge', [('border-color', 'transparent')]),
    ('§5: no hairline under the strip, and no shading inside the bookmark glyph: both are black washes.',
     f'{BASE} #tabs-tabbar-container', [('box-shadow', 'none !important')]),
    ('', f'{BASE} .add-bookmark-shadow', [('fill', 'none')]),
    ('A page that is bookmarked fills the glyph: solid, in the glyph\'s own colour, where Vivaldi fills it with a '
     'black wash at 0.3.', f'{BASE} .BookmarkButton .button-on .bookmark-outline, {BASE} .button-on .bookmark-outline',
     [('fill', 'currentColor')]),
    ('A close button sits on its ground with none of its own, where Vivaldi gives it a black wash; hovered, it takes '
     'the hover of that ground -- WHITE on the current tab, BLACK on the key strip.',
     f'{BASE} .close', [('background-color', 'transparent')]),
    ('', f'{BASE} .close:hover', [('background-color', 'var(--colorBgDark)')]),
    ('Buttons are flat (§5). Vivaldi fills them with a gradient between two of its shades -- a run of values nobody '
     'authored -- and draws a line round them. A button is the other tone from its ground and carries BLACK at 700: '
     'on a field that is BLACK on LIGHT, Lc 61.2, and on the chrome BLACK on WHITE, where 700 costs nothing.',
     f'{BASE} :is(.toolbar-default .button-toolbar > button, input[type=button], input[type=submit], '
     'input[type=reset], button.button-default, .SwitchToTab)',
     [('background-image', 'none'), ('background-color', 'var(--rmButtonBg)'), ('border-color', 'transparent'),
      ('box-shadow', 'none'), ('font-weight', '700')]),
    ('The default action is ACCENT carrying WHITE, Lc -78.5 (§2), as in worksafe/firefox/.',
     f'{BASE} :is(input.primary, button.primary, .button-toolbar.primary > button)',
     [('background-image', 'none'), ('background-color', '{accent}'), ('color', '{white}'), ('border-color', 'transparent')]),
    ('§2: the caret is CURSOR, the locator, in every field of the interface. On WHITE it is Lc 60.7.',
     f'{BASE} :is(input, textarea, [contenteditable])', [('caret-color', '{cursor}')]),
    ('The start page is a page of cards, as Settings is on worksafe/obsidian/: the page LIGHT, and each card -- the '
     'search field, a widget, a speed dial\'s tile -- WHITE on it. Vivaldi paints the page WHITE and the cards '
     'WHITE or LIGHT, and a widget WHITE at 0.65 over the page: a blend nobody authored.',
     f'{BASE} :is(.startpage, .startpage-navigation)', [('background-color', '{light}'), ('box-shadow', 'none')]),
    ('', f'{BASE} :is(.dashboard-widget, .SpeedDial--Icon .favicon, .SpeedDial--Thumbnail .thumbnail-image, '
         '.SpeedDial-Add-Button)', [('background-color', '{white}')]),
    ('Text straight on the LIGHT page -- a tile\'s title, the page\'s own navigation -- is BLACK at 700.',
     f'{BASE} :is(.startpage-navigation, .SpeedDial .thumbnail-title, .SpeedDial-Add-Button)', [('font-weight', '700')]),
    ('The active page in the navigation is marked by a line in ACCENT, a nav indicator (§2).',
     f'{BASE} .startpage-navigation button.active', [('box-shadow', 'inset 0 -3px 0 0 {accent}')]),
    ('Opacity is a blend: the widget\'s provider line at 0.7. Secondary text on a card is DARK (Lc 79.0).',
     f'{BASE} .dashboard-widget :is(.provider, .updated, .subtitle), {BASE} .dashboard-widget .provider *',
     [('opacity', '1'), ('color', 'var(--colorFgFaded)')]),
    ('An empty panel\'s prompt, and a first-run page\'s text, at full strength, not a fraction of it.',
     f'{BASE} :is(.NotesEditor-EmptyPlaceholder, .cards-container .card-text p)', [('opacity', '1')]),
]

# The larger half (§0), shipped as a second stylesheet in the same folder so it is a switch
# (install.sh --no-declutter), and so it works under any theme. It carries no colour at all, and the checker proves it.
DECLUTTER_RULES = [
    ('Blur: the frost Vivaldi puts behind floating panels and the unified chrome, from two variables it derives '
     'from the theme\'s blur.', '#browser, #browser *', [
         ('--backgroundBlur', 'none !important'), ('--unifiedBlur', 'none !important')]),
    ('Motion: every transition and animation Vivaldi writes, zeroed. 0.01 ms rather than 0, so every '
     'transitionend and animationend still fires and nothing waiting on one is stranded; one iteration, so a '
     'spinner stops rather than spins. vivaldi.theme.use_animation (settings.json) stops the ones its script drives.',
     '#browser *, #browser *::before, #browser *::after', [
         ('transition-duration', '0.01ms !important'), ('transition-delay', '0s !important'),
         ('animation-duration', '0.01ms !important'), ('animation-delay', '0s !important'),
         ('animation-iteration-count', '1 !important'), ('scroll-behavior', 'auto !important')]),
    ('Blur: anything else that frosts what is behind it.', '#browser, #browser *', [
        ('backdrop-filter', 'none !important')]),
]

# Variables Vivaldi defines that the table leaves to it on purpose, with the reason -- for --coverage and the gate.
LEFT_UNSET = {
    '--colorImageFg': 'undeclared on purpose: the strip reads var(--colorImageFg, var(--colorAccentFg)) (§4 above)',
    '--colorImageBg': 'the same', '--colorImageBgAlpha': 'the same', '--colorImageBgAlphaHeavy': 'the same',
    '--stackColorBg': 'a colour the user gave a tab stack: information (§3\'s test)',
    '--stackColorBgAlpha': 'the same', '--stackColorFg': 'the same',
    '--flagColor': 'a flag the user put on a message: information',
    '--colorCalendarBg': 'a calendar\'s own colour, the user\'s: information',
    '--colorCalendarBgAlpha': 'the same', '--colorCalendarFg': 'the same', '--colorCalendarFgAlpha': 'the same',
    '--currentAlpha': 'currentColor at an alpha, on a progress mark: follows whatever text it sits in',
    '--currentAlphaLow': 'the same', '--currentAlphaHigh': 'the same',
    '--borderStyle': 'a dashed outline in --colorFgIntense, which the table sets',
    '--badgeBorder': 'resolves through --colorBg or --colorAccentBg, which the table sets',
    '--HighlightColor': 'the address field\'s emphasised text: resolves through --colorAccentFg or --colorFgIntense',
    '--LowlightColor': 'the rest of the address: resolves through --colorAccentFgFaded or --colorFgFadedMost',
}
CONTENT = {'--stackColorBg', '--stackColorBgAlpha', '--stackColorFg', '--flagColor', '--colorCalendarBg',
           '--colorCalendarBgAlpha', '--colorCalendarFg', '--colorCalendarFgAlpha'}


# --- 5. the platform's variables, recorded ----------------------------------------------------------------
# ENGINE: the 74 colour variables Vivaldi's theme engine sets inline on #browser, with the values it derived from
# the kit's own four (theme.json selected, stylesheet off), read off a running 8.2.4133.76 window, 2026-09-29.
# The gate does not need the values -- the table pins every one -- but they are what the native theme alone
# paints, and --derive measures them. SHEET: the colour variables style/common.css declares on #browser, as its
# expression over the engine's. With both, the gate runs on a machine with no Vivaldi, and --coverage re-reads the
# installed build for what was renamed or added since.
ENGINE = {
    '--colorFg': '#10080c', '--colorFgIntense': '#000000', '--colorFgFaded': '#3d3739', '--colorFgFadedMore': '#544e50',
    '--colorFgFadedMost': '#766e71', '--colorBg': '#baadb2', '--colorBgAlphaBlur': '#baadb2', '--colorBgDark': '#b3a6ab',
    '--colorBgDarker': '#ab9fa3', '--colorBgLight': '#bfb2b7', '--colorBgLighter': '#d3c6cb',
    '--colorBgLightIntense': '#c4b7bc', '--colorBgIntense': '#c9bcc1', '--colorBgIntenser': '#d3c6cb',
    '--colorBgInverse': '#b5a8ad', '--colorBgInverser': '#a79a9f', '--colorBgFaded': '#ab9fa3',
    '--colorHighlightBg': '#521436', '--colorHighlightBgFaded': '#814060', '--colorHighlightBgDark': '#3c0023',
    '--colorHighlightFg': '#ffffff', '--colorAccentBg': '#763555', '--colorAccentBgAlphaBlur': '#763555',
    '--colorAccentBgDark': '#632444', '--colorAccentBgDarker': '#48082c', '--colorAccentBgFaded': '#5e3046',
    '--colorAccentBgFadedMore': '#8e4b6b', '--colorAccentBgFadedMost': '#b16a8b', '--colorAccentBorder': '#763555',
    '--colorAccentBorderDark': '#6a2a4a', '--colorAccentFg': '#ffffff', '--colorAccentFgFaded': '#d3c8cd',
    '--colorBorder': '#a2959a', '--colorBorderDisabled': '#b3a6ab', '--colorBorderSubtle': '#a89ba0',
    '--colorBorderIntense': '#8f8287', '--colorSuccessBg': '#06a700', '--colorSuccessFg': '#ffffff',
    '--colorWarningBg': '#ffcc00', '--colorWarningFg': '#000000', '--colorErrorBg': '#c64539',
    '--colorErrorFg': '#ffffff', '--colorTabBar': 'var(--colorAccentBg)', '--browserBackgroundColor': '#F1E4E9',
    **{f'--colorImage{pos}{suf}': v for pos in IMAGE_POSITIONS for suf, v in (
        ('Fg', 'rgb(0 0 0)'), ('FgAlpha', 'rgb(0 0 0 / 0.6)'), ('FgAlphaHeavy', 'rgb(0 0 0 / 0.05)'),
        ('Bg', 'rgb(248 242 244)'), ('BgAlpha', 'rgb(248 242 244 / 0.55)'), ('BgAlphaHeavy', 'rgb(248 242 244 / 0.35)'))},
}
SHEET = {
    '--colorFgAlpha': 'color-mix(in srgb, var(--colorFg), transparent 90%)',
    '--colorBgAlpha': 'color-mix(in srgb, var(--colorBg), transparent 10%)',
    '--colorBgAlphaHeavy': 'color-mix(in srgb, var(--colorBg), transparent 35%)',
    '--colorBgAlphaHeavier': 'color-mix(in srgb, var(--colorBg), transparent 75%)',
    '--colorHighlightBgAlpha': 'color-mix(in srgb, var(--colorHighlightBg), transparent 90%)',
    '--colorHighlightFgAlpha': 'color-mix(in srgb, var(--colorHighlightFg), transparent 50%)',
    '--colorHighlightFgAlphaHeavy': 'color-mix(in srgb, var(--colorHighlightFg), transparent 75%)',
    '--colorAccentBgAlpha': 'color-mix(in srgb, var(--colorAccentBgFadedMost), transparent 50%)',
    '--colorAccentBgAlphaHeavy': 'color-mix(in srgb, var(--colorAccentBgFadedMost), transparent 70%)',
    '--colorAccentFgAlpha': 'color-mix(in srgb, var(--colorAccentFg), transparent 85%)',
    '--colorSuccessBgAlpha': 'color-mix(in srgb, var(--colorSuccessBg), transparent 90%)',
    '--colorWarningBgAlpha': 'color-mix(in srgb, var(--colorWarningBg), transparent 90%)',
    '--colorErrorBgAlpha': 'color-mix(in srgb, var(--colorErrorBg), transparent 90%)',
}
PLATFORM = {**ENGINE, **SHEET}


# --- 6. what the checker measures ------------------------------------------------------------------------
# Text on ground, by variable, in a context (the scopes that apply, lowest first), with APCA's tier for what it
# carries (build/apca.py GUIDANCE): 75 for text read at 400, 60 at 700, 30 for a mark, 15 to be visible. Both sides
# are resolved out of the committed stylesheet over the recorded platform, the way the browser resolves them.
PAIRS = [
    ('--colorFg', '--colorBg', (), 60, 'a toolbar, panel or status-bar label, 700'),
    ('--colorFgFaded', '--colorBg', (), 60, 'secondary text on the chrome: BLACK, 700'),
    ('--colorFg', '--colorBgDark', (), 60, 'a hovered button on the chrome'),
    ('--colorFg', '--colorBgLight', (), 60, 'a popup\'s or dialog\'s label, 700'),
    ('--colorFg', '--rmButtonBg', (), 60, 'a button on the chrome: WHITE, 700'),
    ('--colorFg', '--rmButtonBg', ('fields',), 60, 'a button on a field: LIGHT, 700'),
    ('--colorFgFadedMost', '--colorBg', (), 30, 'disabled text: no text tier applies (APCA exempts it); a mark\'s'),
    ('--colorFg', '--colorBgIntense', ('fields',), 75, 'what the user types, 400'),
    ('--colorAccentFg', '--colorAccentBgDark', ('key strip', 'fields'), 75, 'the address on the strip: BLACK on WHITE'),
    ('--colorAccentFgFaded', '--colorAccentBgDark', ('key strip', 'fields'), 75, 'the rest of the address, DARK'),
    ('--colorFgFaded', '--colorBgIntense', ('fields',), 75, 'a placeholder, secondary text on a field'),
    ('--colorFg', '--colorBgDark', ('fields',), 60, 'a hovered row on a field: LIGHT, so its text goes 700'),
    ('--colorHighlightFg', '--colorHighlightBg', (), 75, 'a selected row, selected text, 400'),
    ('--colorAccentFg', '--colorTabBar', ('key strip',), 75, 'a tab on the key strip, 400'),
    ('--colorFg', '--colorTabBar', ('key strip',), 75, 'the strip\'s own labels: the workspace button'),
    ('--colorAccentFg', '--colorTabBar', ('key strip', 'private strip'), 75, 'a tab on a private window\'s key strip'),
    ('--colorAccentFg', '--colorAccentBgAlpha', ('key strip', 'private strip'), 75, 'a hovered tab there: DARK'),
    ('--colorAccentFg', '--colorAccentBgAlpha', ('key strip',), 75, 'a hovered tab: WHITE on BLACK'),
    ('--colorFg', '--colorBgDark', ('key strip',), 75, 'a hovered button on the key strip'),
    ('--colorAccentFg', '--colorTabBar', ('non-key',), 60, 'a tab on the non-key strip, 700'),
    ('--colorAccentFg', '--colorBg', ('key strip', 'key tab'), 60, 'the current tab on the key strip: LIGHT, 700'),
    ('--colorFg', '--colorBg', ('key strip', 'key tab'), 60, 'the same, where Vivaldi reads the foreground'),
    ('--colorAccentFg', '--colorBg', ('non-key', 'non-key tab'), 60, 'the current tab when not key: WHITE, 700'),
    ('--colorFg', '--colorBg', ('key strip',), 75, 'the header\'s title when the tabs are at the side'),
    ('--colorAccentFg', '--colorAccentBgAlpha', ('non-key',), 60, 'a hovered tab there, 700'),
    ('--colorAccentFg', '--colorAccentBg', (), 75, 'text on an ACCENT ground'),
    ('--colorSuccessFg', '--colorSuccessBg', (), 60, '§3\'s legend on success'),
    ('--colorWarningFg', '--colorWarningBg', (), 60, '§3\'s legend on warning'),
    ('--colorErrorFg', '--colorErrorBg', (), 60, '§3\'s legend on destructive'),
    ('--colorHighlightFg', '--colorHighlightFgAlphaHeavy', (), 75, 'a count on a selected row'),
    ('--colorBorderIntense', '--colorBg', (), 15, 'the scrollbar thumb on the chrome: visible'),
    ('--colorBorderIntense', '--colorBgIntense', ('fields',), 15, 'the scrollbar thumb on a field: visible'),
]
# Grounds that touch. OKLab dE against SURFACE_FLOOR, never Lc (§0e).
ADJACENT = [   # (ground, its context, ground, its context, what meets what)
    ('--colorTabBar', ('key strip',), '--colorBg', (), 'the key strip over the toolbar'),
    ('--colorTabBar', ('non-key',), '--colorBg', ('non-key',), 'the non-key strip over the toolbar'),
    ('--colorBg', (), '--colorBgIntense', ('fields',), 'a field on the chrome: the address bar'),
    ('--colorBg', ('key strip',), '--colorBgIntense', ('key strip', 'fields'), 'the address field on the key strip'),
    ('--colorBg', (), '--browserBackgroundColor', (), 'the page area against the chrome'),
    ('--colorBg', (), '--colorBgDark', (), 'a hovered button on the chrome'),
    ('--colorBgIntense', ('fields',), '--colorBgDark', ('fields',), 'a hovered row on a field'),
    ('--colorBgIntense', ('fields',), '--colorHighlightBg', ('fields',), 'the selected row on a field'),
    ('--colorBg', (), '--colorHighlightBgAlpha', (), 'the open panel\'s button on the panel bar'),
    ('--colorTabBar', ('key strip',), '--colorAccentBgAlpha', ('key strip',), 'a hovered tab on the key strip'),
    ('--colorTabBar', ('key strip', 'private strip'), '--colorBg', (), 'a private window\'s key strip over the toolbar'),
    ('--colorTabBar', ('key strip', 'private strip'), '--colorAccentBgAlpha', ('key strip', 'private strip'),
     'a hovered tab on a private window\'s strip'),
    ('--colorTabBar', ('key strip', 'private strip'), '--colorBg', ('key strip', 'private strip', 'key tab'),
     'the current tab on a private window\'s strip'),
    ('--colorTabBar', ('key strip', 'private strip'), '--colorTabBar', ('key strip',),
     'a private window against a normal one, both key: the state the tone carries'),
    ('--colorTabBar', ('key strip',), '--colorBg', ('key strip', 'key tab'), 'the current tab on the key strip'),
    ('--colorTabBar', ('non-key',), '--colorBg', ('non-key', 'non-key tab'), 'the current tab on the non-key strip'),
    ('--colorBg', (), '--colorBgLight', (), 'a popup over the chrome: the same tone, parted by its shadow (§4)'),
    ('--colorBg', (), '--rmButtonBg', (), 'a button on the chrome'),
    ('--colorBgIntense', ('fields',), '--rmButtonBg', ('fields',), 'a button on a field'),
]
ADJACENT_EXEMPT = {
    'the non-key strip over the toolbar': 'non-key, the strip and the toolbar are one LIGHT panel, as '
                                          'worksafe/firefox/\'s are: the strip carries no state then',
    'a popup over the chrome: the same tone, parted by its shadow (§4)':
        'a floating surface is parted from what it floats over by a real shadow, which §4 keeps, and not by a tone',
}
LEGEND_GROUNDS = SEMANTIC_GROUNDS


# --- 7. writing ------------------------------------------------------------------------------------------
HEADER = """/* Remainder for Vivaldi -- the interface stylesheet. GENERATED by build/vivaldi.py --write: never hand-edit;
   change the role table there and regenerate. AUTHORITY.md is the authority; worksafe/vivaldi/README_VIVALDI.md
   says what each part is for and what is left over. Worksafe tier: a file in the folder Vivaldi loads interface
   stylesheets from (Settings > Appearance > Custom UI Modifications), which needs vivaldi://experiments >
   "Allow CSS modifications"; install.sh sets both. Scoped to the Remainder theme: select another in Settings >
   Themes and this stylesheet paints nothing. Checked by build/vivaldi.py, against Vivaldi 8.2.4133.76 (the Arch
   package), 2026-09-29.

   THE ONLY LITERAL COLOURS IN THIS FILE ARE THE --rm-* DEFINITIONS BELOW. Everything else refers to them by
   name, so a value nobody derived cannot get in, and the checker can prove it (CONTRIBUTING.md §8). */
"""
SNIPPET_HEADER = """/* Remainder for Vivaldi -- the declutter (AUTHORITY.md §0): motion and blur, removed. GENERATED by
   build/vivaldi.py --write: never hand-edit. A second file in the same folder as the theme, so install.sh
   --no-declutter can leave it out; it works under any theme, and carries no colour. */
"""


def _fmt(v):
    """A declared value: a role, or a literal whose {role} placeholders become var(--rm-*)."""
    if isinstance(v, R):
        return v.css()
    out = v
    for k in sorted(ROLES, key=len, reverse=True):
        out = out.replace('{' + k + '}', R(k).css())
    return out.replace('{none}', 'transparent')


def _decl_lines(decls, indent='  ', important=False):
    out = []
    for d in decls:
        name, value = d[0], _fmt(d[1])
        note = d[2] if len(d) > 2 else ''
        if important and not value.endswith('!important'):
            value += ' !important'
        line = f'{indent}{name}: {value};'
        if note:
            line += f'   /* {note} */'
        out.append(line)
    return out


def _comment(text, indent=''):
    if not text:
        return []
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > 104:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    if len(lines) == 1:
        return [f'{indent}/* {lines[0]} */']
    return [f'{indent}/* {lines[0]}'] + [f'{indent}   {l}' for l in lines[1:-1]] + [f'{indent}   {lines[-1]} */']


def _split_top(sel):
    """A selector list split at its top-level commas -- never inside :is() or a quoted value."""
    out, depth, quote, cur = [], 0, '', ''
    for ch in sel:
        if quote:
            quote = '' if ch == quote else quote
        elif ch in '"\'':
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            out.append(cur.strip()); cur = ''; continue
        cur += ch
    out.append(cur.strip())
    return [s for s in out if s]


# A theme preview in Settings > Themes is a picture of another theme, painted from that theme's own variables on the
# preview: information, like worksafe/zettlr/'s pictures of its editor themes (§0a). No pin reaches into one, and
# :where() keeps the exclusion out of the specificity, so every scope still ranks as the checker measures it.
NOT_PREVIEW = ':where(:not(.ThemePreview-Browser, .ThemePreview-Browser *))'


def _scoped(sels):
    """Each selector, and every element under it that is not part of a theme preview."""
    out = []
    for s in sels:
        for one in _split_top(s):
            out += [one, f'{one} *{NOT_PREVIEW}']
    return out


def theme_text():
    out = [HEADER.rstrip('\n'), '', BASE + ' {']
    out += _comment('§2 and §3: the values the stylesheet may name, each checked against palette.json. The three '
                    'signal-text values are build/cosmic.py\'s ANSI normal tier.', '  ')
    for name in ROLES:
        out.append(f'  --rm-{name}: {ROLES[name]};')
    out.append('}')
    out.append('')
    out += _comment('THE ROLE TABLE: every colour variable Vivaldi defines, on #browser and on every element under it.')
    out.append(',\n'.join(_scoped([BASE])) + ' {')
    first = True
    for title, decls in _vars():
        if not first:
            out.append('')
        first = False
        out += _comment(title, '  ')
        out += _decl_lines(decls, important=True)
    out.append('}')
    for name, sels, parent, note, decls in SCOPES:
        out.append('')
        out += _comment(f'Scope "{name}". {note}')
        out.append(',\n'.join(_scoped(sels)) + ' {')
        out += _decl_lines(decls, important=True)
        out.append('}')
    out.append('')
    out += _comment(f'THE SIZES (§5): the chrome\'s text at {CHROME_PX} px, CHOSEN and under the 16 every floor assumes; '
                    'build/vivaldi.py section 3 says why. The root, for everything that inherits; then every size '
                    f'Vivaldi sets under {CHROME_PX} px, at its own selector, recorded off {record()["build"]} on '
                    f'{record()["recorded"]} (build/vivaldi_platform.json), with Vivaldi\'s size beside it.')
    out.append(BASE + ' {')
    out.append(f'  font-size: {CHROME_PX}px;')
    out.append('}')
    for conds, sel, px in size_rules():
        ind = '  ' * len(conds)
        out += [f'{"  " * k}{c} {{' for k, c in enumerate(conds)]
        out.append(',\n'.join(ind + x for x in _split_top(sel)) + ' {')
        out.append(f'{ind}  font-size: {CHROME_PX}px;   /* {px:g} px */')
        out.append(f'{ind}}}')
        out += [f'{"  " * k}}}' for k in reversed(range(len(conds)))]
    for note, sel, decls in RULES:
        out.append('')
        out += _comment(note)
        out.append(',\n'.join(_split_top(sel)) + ' {')
        out += _decl_lines(decls)
        out.append('}')
    return '\n'.join(out) + '\n'


def snippet_text():
    out = [SNIPPET_HEADER.rstrip('\n')]
    for note, sel, decls in DECLUTTER_RULES:
        out.append('')
        out += _comment(note)
        out.append(',\n'.join(_split_top(sel)) + ' {')
        out += _decl_lines(decls)
        out.append('}')
    return '\n'.join(out) + '\n'


def theme_json_text():
    return json.dumps(native(), indent=2) + '\n'


def write():
    os.makedirs(VIV, exist_ok=True)
    for path, text in ((THEME, theme_text()), (SNIPPET, snippet_text()), (THEME_JSON, theme_json_text())):
        open(path, 'w').write(text)
        print(f'wrote {os.path.relpath(path, ROOT)}: {len(text.splitlines())} lines')


# --- 8. resolving, the way the browser does -------------------------------------------------------------
# Every variable the table decides is declared at every element in its scope, so an element's value is the base
# table overlaid with each scope that matches it, in the order the specificity check below proves they rank.
_VAR = re.compile(r'var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\)[^()]*)*))?\)')


def _env(context=()):
    env = dict(PLATFORM)
    for name, hx in ROLES.items():
        env[f'--rm-{name}'] = hx
    for _, decls in _vars():
        for d in decls:
            env[d[0]] = _fmt(d[1])
    for sname, sels, parent, note, decls in SCOPES:
        if sname in context:
            for d in decls:
                env[d[0]] = _fmt(d[1])
    return env


def chain(scope):
    """The scopes that apply inside `scope`, its ancestors first."""
    out = []
    while scope:
        out.insert(0, scope)
        scope = next(x for x in SCOPES if x[0] == scope)[2]
    return tuple(out)


def resolve(name, context=()):
    env = _env(context)
    if name not in env:
        return None
    value = env[name]
    for _ in range(40):
        m = _VAR.search(value)
        if not m:
            break
        ref = env.get(m.group(1))
        if ref is None:
            ref = m.group(2) if m.group(2) is not None else '??'
        value = value[:m.start()] + ref + value[m.end():]
    return value.strip()


_NAMED = {'white': '#FFFFFF', 'black': '#000000'}


def colour(value):
    """(hex, alpha) for a value that is one colour, or None. A blend is reported at alpha 0.5, never a kit value."""
    if value is None:
        return None
    v = value.strip()
    if v.lower() == 'transparent':
        return ('#000000', 0.0)
    if v.lower() in _NAMED:
        return (_NAMED[v.lower()], 1.0)
    m = re.fullmatch(r'#([0-9a-fA-F]{6})', v)
    if m:
        return ('#' + m.group(1).upper(), 1.0)
    m = re.fullmatch(r'#([0-9a-fA-F]{3})', v)
    if m:
        return ('#' + ''.join(c * 2 for c in m.group(1)).upper(), 1.0)
    m = re.fullmatch(r'rgba?\((.*)\)', v)
    if m:
        p = [x for x in re.split(r'[ ,/]+', m.group(1)) if x]
        return (ok.hexs([float(x) for x in p[:3]]).upper(), float(p[3]) if len(p) > 3 else 1.0)
    if v.startswith(('color-mix(', 'hsl(')):
        return ('#000000', 0.5)
    return None


def role_of(hx):
    return next((k for k, v in ROLES.items() if v.upper() == hx.upper()), None)


def specificity(sel):
    """(ids, classes, types) of one complex selector. :is() and :not() take their most specific argument,
    :where() none."""
    ids = cls = typ = 0
    i = 0
    while i < len(sel):
        m = re.match(r':(is|not|where|has)\(', sel[i:])
        if m:
            depth, j = 1, i + len(m.group(0))
            while depth:
                depth += {'(': 1, ')': -1}.get(sel[j], 0); j += 1
            inner = sel[i + len(m.group(0)):j - 1]
            if m.group(1) != 'where':
                best = max((specificity(s) for s in _split_top(inner)), default=(0, 0, 0))
                ids, cls, typ = ids + best[0], cls + best[1], typ + best[2]
            i = j
            continue
        m = re.match(r'#[\w-]+|\.[\w-]+|\[[^\]]*\]|::[\w-]+|:[\w-]+(\([^)]*\))?|[a-zA-Z][\w-]*|\*|.', sel[i:])
        tok = m.group(0)
        if tok.startswith('#'):
            ids += 1
        elif tok.startswith(('.', '[')) or (tok.startswith(':') and not tok.startswith('::')):
            cls += 1
        elif tok.startswith('::') or re.fullmatch(r'[a-zA-Z][\w-]*', tok):
            typ += 1
        i += len(tok)
    return (ids, cls, typ)


# --- 9. the checker --------------------------------------------------------------------------------------
COMMENT = re.compile(r'/\*.*?\*/', re.S)
HEX = re.compile(r'#[0-9A-Fa-f]{3,8}\b')
MIXED = re.compile(r'\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark|image-set)\s*\(')
NAMED = {'white', 'black', 'red', 'blue', 'green', 'gray', 'grey', 'yellow', 'orange', 'purple', 'pink',
         'silver', 'cyan', 'magenta', 'teal', 'navy', 'maroon', 'lime', 'olive', 'aqua', 'fuchsia',
         'highlight', 'highlighttext', 'canvas', 'canvastext', 'buttontext', 'buttonface', 'selecteditem',
         'selecteditemtext', 'linktext', 'visitedtext', 'graytext', 'accentcolor', 'accentcolortext', 'field',
         'fieldtext', 'mark', 'marktext'}
# a hex that is a selector (an id) rather than a colour: `#header`, `#browser`, `#footer` would never match HEX,
# but an id made of hex digits would; none does in 8.2.4133.76, and the checker says so if one ever appears
SELECTOR_IDS = re.compile(r'#(?:browser|header|footer|main|tabs-tabbar-container|panels-container|webview-container|switch|app|modal-bg)\b')


def _jsonc(text):
    strip = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.S)
    s = strip.sub(lambda m: m.group(1) or '', text)
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', s) or '{}')


def _exclusive(a, b):
    """Two scopes whose selectors can never match one element: one is a key window's, the other not."""
    fa, fb = ' '.join(a), ' '.join(b)
    return ('.hasfocus' in fa and '.isblurred' in fb) or ('.isblurred' in fa and '.hasfocus' in fb)


def check():
    bad, notes = 0, []

    def fail(msg):
        nonlocal bad
        bad += 1
        notes.append(msg)

    # --- the committed files are what the tables produce ---------------------------------------------
    for path, want in ((THEME, theme_text()), (SNIPPET, snippet_text()), (THEME_JSON, theme_json_text())):
        if not os.path.exists(path):
            print(f'vivaldi: {os.path.relpath(path, ROOT)} is not committed yet -- run --write'); return False
        if open(path).read() != want:
            fail(f'{os.path.relpath(path, ROOT)} is not what the tables produce: run --write, or move the edit into '
                 'build/vivaldi.py')
    sn = COMMENT.sub(' ', open(SNIPPET).read())
    found = HEX.findall(sn) + [m.group(1) for m in MIXED.finditer(sn)] + \
        [w for w in re.findall(r'[A-Za-z][A-Za-z-]{2,}', sn) if w.lower() in NAMED] + re.findall(r'var\(--rm-', sn)
    for f in found:
        fail(f'{os.path.relpath(SNIPPET, ROOT)} names a colour ({f}): the declutter paints nothing')
    print(f'{os.path.relpath(SNIPPET, ROOT)}: no colour, {len(DECLUTTER_RULES)} rules')

    # --- every literal colour is an --rm-* definition, and every definition is a value the kit authors ---
    text = open(THEME).read()
    body = COMMENT.sub(' ', text)
    defs = {m.group(1): m.group(2).upper() for m in re.finditer(r'--rm-([a-z-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;', body)}
    print(f'\n--rm-* definitions: {len(defs)}')
    for name, hx in defs.items():
        want = ROLES.get(name)
        tag = ''
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
        print(f'  --rm-{name:13} {hx}  {kind:40} {SOURCE[name]}{cap} {tag}')
    rest = re.sub(r'--rm-[a-z-]+\s*:\s*#[0-9A-Fa-f]{6}\s*;', ' ', body)
    rest = SELECTOR_IDS.sub(' ', rest)
    rest = re.sub(r'var\(\s*--[\w-]+\s*\)', ' ', rest)
    for m in HEX.finditer(rest):
        fail(f'the literal {m.group(0)} outside the --rm-* definitions')
    for m in MIXED.finditer(rest):
        fail(f'{m.group(1)}() -- a mixed value is not an authored value')
    for sel, decls in re.findall(r'([^{}]+)\{([^{}]*)\}', rest):
        for d in decls.split(';'):
            if ':' not in d:
                continue
            prop, val = d.split(':', 1)
            for w in re.findall(r'[A-Za-z][A-Za-z-]{2,}', val):
                if w.lower() in NAMED:
                    fail(f'{prop.strip()} names the colour "{w}" -- nothing derived it')

    # --- the native theme: Vivaldi's four and its window colour are the kit's -------------------------------
    nat = native()
    print(f'\n{os.path.relpath(THEME_JSON, ROOT)}: the native theme')
    for k in ('colorBg', 'colorFg', 'colorHighlightBg', 'colorAccentBg', 'colorWindowBg'):
        r = role_of(nat[k])
        if not r or r in RESERVED:
            fail(f'theme.json {k} is {nat[k]}, not a kit value')
        print(f'  {k:18} {nat[k]}  {r}')
    for k, want in (('accentFromPage', False), ('alpha', 1), ('blur', 0), ('backgroundImage', ''),
                    ('transparencyTabBar', False), ('transparencyTabs', False), ('radius', 0),
                    ('colorPosition', 'tabbar'), ('contrast', 0)):
        if nat[k] != want:
            fail(f'theme.json {k} is {nat[k]!r}: the checker measured the surface with {want!r}')
    chrome = {n: colour(v) for n, v in ENGINE.items() if not n.startswith('--colorImage') and 'var(' not in v}
    legend = sum(1 for n, c in chrome.items() if re.search(r'(Success|Warning|Error)Fg$', n) and role_of(c[0]) in RESERVED)
    on = sum(1 for n, c in chrome.items() if c[1] == 1 and role_of(c[0]) and role_of(c[0]) not in RESERVED)
    print(f'  alone, the engine derives {len(chrome)} colour variables for the chrome from these: {on} on the ladder, '
          f'{legend} §3\'s legends, {len(chrome) - on - legend} off it (--derive lists them); the stylesheet pins every '
          'one')

    # --- the scopes rank as the resolver assumes -------------------------------------------------------------
    print('\nscopes, lowest first (each must outrank every one before it that can match the same element -- a key '
          'window\'s and a non-key window\'s cannot -- or the browser resolves them differently):')
    ranked = [('base', [BASE])] + [(name, sels) for name, sels, *_ in SCOPES]
    for i, (name, sels) in enumerate(ranked):
        lo = min(specificity(x) for x in _scoped(sels))
        under = [n for n, ss in ranked[:i] if not _exclusive(sels, ss) and max(specificity(x) for x in _scoped(ss)) >= lo]
        bad += bool(under)
        print(f'  {name:14} {lo}' + (f'  DOES NOT OUTRANK {", ".join(under)}' if under else ''))

    # --- the sizes: every one Vivaldi sets under CHROME_PX is answered, from the record -------------------------
    rec = record()
    if not rec['sizes']:
        fail(f'{os.path.relpath(RECORD, ROOT)} is missing or empty: run --record with Vivaldi installed')
    by = {}
    for _, _, px in rec['sizes']:
        by[px] = by.get(px, 0) + 1
    print(f"\nsizes: the chrome's text at {CHROME_PX} px (CHOSEN, under the 16 the floors assume); "
          f"{len(rec['sizes'])} of Vivaldi's own under it ({sum(1 for c, _, _ in rec['sizes'] if c)} under a @media or "
          f"@container condition, kept), recorded off {rec['build']} on {rec['recorded']}: "
          + ', '.join(f'{n} at {px:g} px' for px, n in sorted(by.items(), reverse=True)))
    for _, sel, _ in size_rules():
        for x in _split_top(sel):
            if SCOPE_SUBJECT not in x:
                fail(f'a size rule reaches outside the kit\'s #browser: {x[:80]}')

    # --- every colour variable, resolved under the theme, in every context ------------------------------------
    contexts = [()] + [chain(s[0]) for s in SCOPES] + [('key strip', 'fields'), ('non-key', 'fields')]
    counts, offl = {}, []
    names = sorted(n for n in set(PLATFORM) | {d[0] for _, ds in _vars() for d in ds if d[0].startswith('--rm')}
                   if n not in LEFT_UNSET)
    for ctx in contexts:
        for n in names:
            c = colour(resolve(n, ctx))
            if c is None:
                continue
            hx, a = c
            if a == 0:
                kind = 'transparent'
            elif a < 1:
                kind = 'BLEND'
            elif role_of(hx):
                kind = 'legend' if role_of(hx) in RESERVED else role_of(hx)
            elif n in CONTENT:
                kind = 'content'
            else:
                kind = 'OFF THE LADDER'
            if ctx == ():
                counts[kind] = counts.get(kind, 0) + 1
            if kind in ('BLEND', 'OFF THE LADDER'):
                offl.append((n, ctx, hx, a, kind))
            if kind == 'legend' and not re.search(r'--color(Success|Warning|Error)Fg$', n):
                offl.append((n, ctx, hx, a, 'LEGEND OFF A SEMANTIC GROUND'))
    print(f"\nevery colour variable Vivaldi 8.2 defines, resolved under the stylesheet ({len(names)}, in "
          f"{len(contexts)} contexts; {len(LEFT_UNSET)} left to Vivaldi by name):")
    for k in sorted(counts, key=lambda k: -counts[k]):
        print(f'  {counts[k]:4}  {k}')
    for n, ctx, hx, a, kind in offl:
        fail(f'{n} in {ctx or "base"} resolves to {hx} at alpha {a:g}: {kind}')

    # --- the pairs ------------------------------------------------------------------------------------------
    print("\npairs (APCA Lc, signed; the floor is APCA's tier for what the pair carries):")
    for t, g, ctx, floor, why in PAIRS:
        tc, gc = colour(resolve(t, ctx)), colour(resolve(g, ctx))
        if not tc or not gc or tc[1] < 1 or gc[1] < 1:
            fail(f'{t} on {g} ({ctx or "base"}): one side does not resolve to an opaque value'); continue
        lc = apca.lc(tc[0], gc[0])
        good = abs(lc) >= floor
        bad += not good
        tr, gr = role_of(tc[0]) or tc[0], role_of(gc[0]) or gc[0]
        if tr in RESERVED and gr not in LEGEND_GROUNDS:
            fail(f'{t}: §3 reserves {tc[0]} for legend on a semantic ground, not on {gr}')
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  {'ok ' if good else 'LOW'}  "
              f"{'+'.join(ctx) or 'base':18} {why}")

    at = next(t for t, why in apca.GUIDANCE if f'{CHROME_PX}px/400' in why)
    short = [(t, g, ctx, why, apca.lc(colour(resolve(t, ctx))[0], colour(resolve(g, ctx))[0]))
             for t, g, ctx, floor, why in PAIRS if floor == 75]
    short = [x for x in short if abs(x[4]) < at]
    print(f"\nat the size on screen, {CHROME_PX} px -- recorded, not gated: CHROME_PX is a choice made under the floors. "
          f"build/apca.py asks Lc {at} of text at {CHROME_PX}px/400, where the pairs above were measured at 16px/400's "
          f"75; {len(short)} of the 400-weight pairs sit under it. Its table names no tier for {CHROME_PX}px/700, so "
          "the 700 pairs are left at 16px/700's 60 and are not claimed:")
    for t, g, ctx, why, lc in short:
        tr, gr = role_of(colour(resolve(t, ctx))[0]), role_of(colour(resolve(g, ctx))[0])
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  {at - abs(lc):4.1f} short  {'+'.join(ctx) or 'base':18} {why}")

    # --- the rules that set both sides --------------------------------------------------------------------
    print("\npairs the rule blocks author:")
    for note, sel, decls in RULES:
        d = {k: _fmt(v) for k, v, *_ in decls}
        fg, bg = d.get('color'), d.get('background-color')
        if not fg or not bg or 'var(--rm-' not in fg or 'var(--rm-' not in bg:
            continue
        tr, gr = _VAR.search(fg).group(1)[5:], _VAR.search(bg).group(1)[5:]
        weight = 700 if re.search(r'\b(700|bold)\b', d.get('font-weight', '')) else 400
        lc = apca.lc(ROLES[tr], ROLES[gr])
        floor = 60 if weight == 700 else 75
        good = abs(lc) >= floor
        bad += not good
        if tr in RESERVED and gr not in LEGEND_GROUNDS:
            fail(f'{sel[:50]}: §3 reserves {ROLES[tr]} for legend on a semantic ground, not on {gr}')
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  /{weight}  {'ok ' if good else 'LOW'}  {sel[-60:]}")

    # --- the adjacencies ------------------------------------------------------------------------------------
    print(f"\nsurfaces that touch (OKLab dE; floor {FLOOR}, derived from WHITE against LIGHT):")
    for a, actx, b, bctx, why in ADJACENT:
        ca, cb = colour(resolve(a, actx)), colour(resolve(b, bctx))
        dE = ok.delta_e(ca[0], cb[0])
        exempt = ADJACENT_EXEMPT.get(why)
        good = exempt or dE >= FLOOR - 0.05
        bad += not good
        print(f"  {role_of(ca[0]):12} / {role_of(cb[0]):12} dE {dE:5.1f}  {'exempt' if exempt else ('ok ' if good else 'BELOW')}  "
              f"{why}")

    # --- the files the installer copies that are not the theme: no colour in either ---------------------------
    for path in (SETTINGS, INSTALLER):
        if not os.path.exists(path):
            fail(f'{os.path.relpath(path, ROOT)} is not committed'); continue
        raw = open(path, errors='ignore').read()
        raw = re.sub(r'^\s*#.*$', '', raw, flags=re.M) if path.endswith('.sh') else COMMENT.sub(' ', re.sub(r'//[^\n]*', '', raw))
        found = sorted({m.group(0).upper() for m in HEX.finditer(raw)} - {'#BROWSER'})
        print(f"\n{os.path.relpath(path, ROOT)}: {len(found)} colour(s) it writes itself")
        for hx in found:
            fail(f'{os.path.relpath(path, ROOT)} carries {hx}')
    if os.path.exists(SETTINGS):
        try:
            _jsonc(open(SETTINGS).read())
        except ValueError as e:
            fail(f'{os.path.relpath(SETTINGS, ROOT)} does not parse once its comments are stripped: {e}')

    if notes:
        print('\nnotes:')
        for n in notes:
            print(f'  {n}')
    print(f"\nvivaldi: {'every value, pair and adjacency clears' if not bad else str(bad) + ' DEFECT(S)'}")
    return bad == 0


# --- 10. the installed build: a report, never a gate ---------------------------------------------------------
def _read(member):
    path = os.path.join(VIVALDI_RES, member)
    return open(path, encoding='utf8', errors='replace').read() if os.path.exists(path) else None


def engine_names(bundle):
    """The variables the theme engine derives: the keys of the objects its six colour functions return."""
    i = bundle.find('colorBgAlphaBlur:e.alpha(')
    if i < 0:
        return set()
    lo = bundle.rfind('function m(e,t,n)', 0, i)
    hi = min(x for x in (bundle.find('function O(e)', i), bundle.find('forTheme:', i)) if x > 0)
    return set('--' + k for k in re.findall(r'\b(color[A-Z]\w*):', bundle[lo:hi]))


def sheet_vars(css):
    """{name: [(selector, value)]} for every custom property style/common.css declares."""
    css = COMMENT.sub('', css)
    out = {}
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        for d in re.split(r';(?![^(]*\))', body):
            if ':' in d:
                k, v = d.split(':', 1)
                if k.strip().startswith('--'):
                    out.setdefault(k.strip(), []).append((' '.join(sel.split()), ' '.join(v.split())))
    return out


def coverage():
    css, bundle = _read('style/common.css'), _read('bundle.js')
    if css is None or bundle is None:
        print(f'coverage: no Vivaldi interface at {VIVALDI_RES} (the deb, rpm and Arch packages put it there)')
        return True
    live_engine = engine_names(bundle)
    decl = sheet_vars(css)
    print(f'{VIVALDI_RES}: {len(live_engine)} engine variables, {len(decl)} custom properties in style/common.css\n')
    rec_engine = {n for n in ENGINE if not n.startswith('--colorImage') and n not in ('--colorTabBar', '--browserBackgroundColor')}
    print('the engine against the record:')
    for n in sorted(live_engine - rec_engine):
        print(f'  NEW    {n}: the table does not pin it')
    for n in sorted(rec_engine - live_engine):
        print(f'  GONE   {n}: recorded, and no longer derived')
    if live_engine == rec_engine:
        print('  the same', len(rec_engine), 'variables')
    colourish = re.compile(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|color-mix\(|var\(--color|\b(white|black|transparent)\b')
    on_browser = {n: v for n, rows in decl.items() for sel, v in rows if sel == '#browser' and colourish.search(v)}
    print('\nstyle/common.css\'s colour variables on #browser against the record:')
    for n in sorted(set(on_browser) - set(SHEET) - set(LEFT_UNSET)):
        print(f'  NEW    {n}: {on_browser[n][:80]}')
    for n in sorted(set(SHEET) - set(on_browser)):
        print(f'  GONE   {n}')
    for n in sorted(set(SHEET) & set(on_browser)):
        if on_browser[n] != SHEET[n]:
            print(f'  MOVED  {n}: {on_browser[n][:80]}')
    used = set(re.findall(r'var\(\s*(--color[\w-]+)', COMMENT.sub('', css)))
    pinned = {d[0] for _, decls in _vars() for d in decls}
    loose = sorted(used - pinned - set(LEFT_UNSET) - set(on_browser) - live_engine)
    print(f'\ncolour variables style/common.css reads that nothing defines (a fallback, or set by script elsewhere): '
          f'{len(loose)}')
    for n in loose:
        print(f'  {n}')
    live = [(tuple(c), sel, px) for c, sel, px in small_sizes(css)]
    rec = [(tuple(c), sel, px) for c, sel, px in record()['sizes']]
    added, gone = [x for x in live if x not in rec], [x for x in rec if x not in live]
    print(f"\nsizes under {CHROME_PX} px against the record ({record()['build']}): {len(live)} in the installed build, "
          f"{len(rec)} recorded" + ('' if added or gone else ', the same'))
    for c, sel, px in added:
        print(f"  NEW    {px:g} px  {' '.join(c) + ' ' if c else ''}{sel[:90]}")
    for c, sel, px in gone:
        print(f"  GONE   {px:g} px  {' '.join(c) + ' ' if c else ''}{sel[:90]}")
    if added or gone:
        print('  -- run --record, then --write')
    body = COMMENT.sub('', css)
    lits = {'hex': len(HEX.findall(body)), 'rgb/hsl': len(re.findall(r'\b(?:rgba?|hsla?)\(', body)),
            'color-mix': body.count('color-mix(')}
    print(f'\nliterals in style/common.css, which no variable reaches -- --screen finds the ones that paint: '
          + ', '.join(f'{k} {v}' for k, v in lits.items()))
    return True


# --- 11. the screen: what the running app paints -----------------------------------------------------------------
# A stylesheet is not what the window shows: Vivaldi's own literals, its inline styles and its blends all still
# apply. So this asks a running Vivaldi, over the DevTools port, what every visible element of every interface
# window computed -- the main windows and the settings window, which are all window.html -- and reports each painted
# value off the ladder and each text pair under the tier its own computed size, at the UI zoom, and weight demand.
# Then it photographs each window and reads the pixels for what no computed style can see. A report, not a gate.
# What counts as content (§0a): a page in a webview, a site's favicon and a speed dial's picture, a colour the user
# gave a tab stack or a calendar, and the brand art on the start page.
CONTENT_SELECTORS = ('.webpageview:not(.internal) webview', 'img', 'canvas', 'video', 'iframe', 'picture',
                     '.favicon', '.thumbnail-image', '.thumbnail-favicon', '[class*="stack-color"]', '.color1',
                     '.color2', '.color3', '.color4', '.color5', '.color6', '.color7', '.color8', '.color9',
                     '.flag-color', '[class*="calendar-color"]', '.ExtensionIcon', '.profile-picture-wrapper',
                     '.ThemePreview-Browser')
PROBE = r"""(() => {
  const out = [];
  const CONTENT = __CONTENT__;
  const parse = s => { if (!s) return null;
    let m = s.match(/color\(srgb ([^)]+)\)/);
    if (m) { const p = m[1].split(/[ \/]+/).filter(Boolean).map(Number); return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
    m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const hex = c => '#' + c.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();
  const up = e => e.parentElement || (e.parentNode && e.parentNode.host) || null;
  const name = el => { let s = el.tagName.toLowerCase(); if (el.id && el.id.length < 30) s += '#' + el.id;
    const cls = (typeof el.className === 'string' ? el.className : '').trim().split(/\s+/).filter(c => c && c.length < 40).slice(0, 3);
    return cls.length ? s + '.' + cls.join('.') : s; };
  const where = el => { const p = []; for (let e = el; e && e.id !== 'browser' && p.length < 4; e = up(e)) p.unshift(name(e)); return p.join(' > '); };
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
        disabled: !!el.closest('.disabled, :disabled, [aria-disabled=true]'),
        family: cs.fontFamily.split(',').map(f => f.trim().replace(/["']/g, ''))[0],
        sample: [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').slice(0, 30)});
    if (cs.backgroundImage !== 'none' && !content) out.push({prop: 'background-image', value: cs.backgroundImage.slice(0, 100), where: where(el)});
    if (cs.boxShadow !== 'none') out.push({prop: 'box-shadow', value: cs.boxShadow.slice(0, 100), where: where(el)});
    if (cs.backdropFilter && cs.backdropFilter !== 'none') out.push({prop: 'backdrop-filter', value: cs.backdropFilter, where: where(el)});
  }
  const b = document.getElementById('browser');
  return {browser: b ? b.className : '', records: out};
})()"""


def _probe_js():
    return PROBE.replace('__CONTENT__', json.dumps(', '.join(CONTENT_SELECTORS)))


def windows(port):
    """Every Vivaldi interface window on the DevTools port: window.html, whatever the window is showing."""
    targets = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
    return [Page(t) for t in targets if t.get('type') in ('app', 'page') and t.get('url', '').endswith('/window.html')]


def ui_zoom(page):
    try:
        return page.eval('new Promise(r => vivaldi.zoom.getVivaldiUIZoom(r))') or 1
    except RuntimeError:
        return 1


def parsed_rules(page, path=THEME):
    """(rules the running browser parses out of the committed file, rules the file holds -- a @media block and each
    rule in it counted). A string or a bracket left open ends a stylesheet where it happens and says nothing, so the
    count is the check."""
    text = open(path, encoding='utf8').read()
    want = COMMENT.sub('', text).count('{')
    got = page.eval('((t) => { const s = new CSSStyleSheet(); s.replaceSync(t); const n = rs => [...rs].reduce((a, r) => '
                    'a + 1 + (r.cssRules ? n(r.cssRules) : 0), 0); return n(s.cssRules); })(' + json.dumps(text) + ')')
    return got, want


def screen(port, brief=False):
    pages = windows(port)
    if not pages:
        print(f'screen: no Vivaldi interface window on port {port}'); return False
    got, want = parsed_rules(pages[0])
    print(f"{os.path.relpath(THEME, ROOT)}: the browser parses {got} of its {want} rules"
          f"{'' if got == want else ' -- EVERYTHING AFTER THE FIRST FAILURE IS DROPPED'}")
    loaded = pages[0].eval("[...document.querySelectorAll('link[rel=stylesheet]')].some(l => l.href.includes('css-mods'))")
    print(f"the custom-UI stylesheet is {'loaded' if loaded else 'NOT LOADED: is the experiment on, and the folder set?'}\n")
    for page in pages:
        report(page, page.eval(_probe_js()), ui_zoom(page), brief)
        size_report(page, ui_zoom(page))
        pixel_report(page)
    return True


def report(page, shot, zoom, brief=False):
    recs = shot['records']
    cls = shot['browser'].split()
    state = ('KEY' if 'hasfocus' in cls else 'not key') + (', settings' if 'is-settingspage' in cls else '')
    theme = next((c for c in cls if c.startswith('theme-id-')), 'no theme id')
    print(f"=== {page.target.get('title', '?')[:50]}: {state}, {theme}, UI zoom {zoom:g}, {len(recs)} painted values\n")
    content = [r for r in recs if r.get('content')]
    recs = [r for r in recs if not r.get('content')]
    print(f"content, left as Vivaldi paints it (§0a): {len(content)} values in {len({r['where'] for r in content})} elements\n")
    by = {}
    for r in recs:
        if r['prop'] in ('box-shadow', 'backdrop-filter', 'background-image'):
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
    print(f'\ntext pairs as painted (the floor is the tier for the weight the element computed -- a glyph\'s, or '
          f'disabled text\'s, is the mark tier; SMALL is under CHROME_PX, {CHROME_PX} px, at the UI zoom, {zoom:g})'
          + (', the ones to look at:' if brief else ':'))
    pairs = {}
    glyph = lambda r: ' > svg' in r['where'] or r['where'].startswith('svg')
    for r in recs:
        if r['prop'] == 'text':
            k = (r['value'], r['ground'], 'glyph' if glyph(r) or r.get('disabled') else r['weight'] >= 600,
                 round(r['size'] * zoom, 1), r['opacity'] < 1 or r['alpha'] < 1)
            pairs.setdefault(k, []).append(r)
    for (t, g, tier, size, faded), rs in sorted(pairs.items(), key=lambda kv: -len(kv[1])):
        lc = apca.lc(t, g)
        floor = 30 if tier == 'glyph' else 60 if tier else 75
        low = abs(lc) < floor
        flag = ('cap' if low and t.upper() in CAPS else 'LOW' if low else 'FADED' if faded else
                'SMALL' if size < CHROME_PX - 0.05 and tier != 'glyph' else 'ok')
        weight = 'mark' if tier == 'glyph' else '700' if tier else '400'
        if brief and flag == 'ok':
            continue
        print(f"  {role_of(t) or t:12} on {role_of(g) or g:12} Lc {lc:6.1f} {size:5}px/{weight:5} "
              f"{flag:5} {len(rs):4}x  e.g. {rs[0]['sample'][:22]!r} {rs[0]['where'][-60:]}")
    faces = {}
    for r in recs:
        if r['prop'] == 'text' and not glyph(r):
            faces.setdefault(r['family'], []).append(r)
    print('\nfaces: ' + ', '.join(f"{f} {len(rs)}x" for f, rs in sorted(faces.items(), key=lambda kv: -len(kv[1]))))
    for extra in ('background-image', 'box-shadow', 'backdrop-filter'):
        rs = [r for r in recs if r['prop'] == extra]
        if rs:
            print(f"\n{extra}: {len(rs)} element(s), e.g. {rs[0]['value'][:90]} on {rs[0]['where'][-60:]}")
    print()


# The sizes are answered at Vivaldi's own selectors, one step up, and a selector can also match an element Vivaldi
# sizes larger by another rule of lower rank: the kit's 14 px would then shrink it. So --screen reads every text's
# size with the interface stylesheet switched off and on, and names any that got smaller.
SHRINK = r"""(() => {
  const link = [...document.querySelectorAll('link[rel=stylesheet]')].find(l => l.href.includes('css-mods'));
  if (!link) return null;
  const els = [...document.querySelectorAll('#browser *')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
  const size = () => els.map(e => parseFloat(getComputedStyle(e).fontSize));
  const on = size(); link.disabled = true; const off = size(); link.disabled = false; size();
  const name = e => e.tagName.toLowerCase() + ((typeof e.className === 'string' && e.className) ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  const shrank = []; let under = 0;
  els.forEach((e, i) => { if (on[i] < off[i] - 0.01) shrank.push([name(e), off[i], on[i], e.textContent.trim().slice(0, 24)]);
                          if (on[i] < __PX__ - 0.01 && e.getBoundingClientRect().width > 0) under++; });
  return {count: els.length, shrank, under};
})()"""


def size_report(page, zoom):
    got = page.eval(SHRINK.replace('__PX__', str(CHROME_PX / (zoom or 1))))
    if got is None:
        print('sizes: the interface stylesheet is not loaded\n'); return
    print(f"sizes: {got['count']} texts; {len(got['shrank'])} smaller under the kit than under Vivaldi alone, "
          f"{got['under']} under {CHROME_PX} px")
    for where, off, on, sample in got['shrank'][:12]:
        print(f"  SHRANK  {off:g} -> {on:g} px  {sample!r}  {where[:70]}")
    print()


# The computed styles cannot see what Chromium draws itself -- a native control, a scrollbar, an emoji -- nor what a
# picture carries. So --screen photographs each window and reads its pixels, as build/zettlr.py does: a pixel with
# a readable hue must fall in a family the kit paints and be no more chromatic than the kit's own member of it (a
# blend of two kit values gains at most 0.0074, so FAMILY_SLACK is twice that). Content is left out, as above.
FAMILIES = {'home': ('accent', 'select'), 'cursor': ('cursor',), 'success': ('success',), 'warning': ('warning',),
            'destructive': ('destructive',), 'red': ('red',), 'green': ('green',), 'yellow': ('yellow',)}
HUE_REACH = {'home': 20, 'cursor': 20}
FAMILY_SLACK = 0.015
_AT = r"""((x, y) => { const e = document.elementFromPoint(x, y); if (!e) return '';
  const p = []; for (let n = e; n && p.length < 3; n = n.parentElement) {
    const cls = (typeof n.className === 'string' ? n.className : '').trim().split(/\s+/).filter(c => c && c.length < 40).slice(0, 2);
    p.unshift(n.tagName.toLowerCase() + (n.id && n.id.length < 30 ? '#' + n.id : '') + (cls.length ? '.' + cls.join('.') : '')); }
  return p.join(' > '); })"""


def pixels(page, top=8):
    import numpy as np
    from PIL import Image
    shot = base64.b64decode(page.call('Page.captureScreenshot', format='png')['data'])
    im = np.asarray(Image.open(io.BytesIO(shot)).convert('RGB')).astype(float)
    dpr = page.eval('devicePixelRatio') or 1
    _, chroma, hue = ok.lch_grid(im)
    hued = chroma >= P.C_FLOOR
    rects = page.eval(f"[...document.querySelectorAll({json.dumps(', '.join(CONTENT_SELECTORS))})].map(e => {{ "
                      "const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })") or []
    # A picture is drawn a little outside its layout box -- the address field's favicon two pixels left of it,
    # measured 2026-09-29 -- so each is left out with two pixels to spare on every side.
    for x0, y0, x1, y1 in rects:
        hued[max(0, int(y0 * dpr) - 2):max(0, int(y1 * dpr) + 3), max(0, int(x0 * dpr) - 2):max(0, int(x1 * dpr) + 3)] = False
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
    return {f: n for f, n in on.items() if n}, lines, shot


def pixel_report(page, save=None):
    try:
        on, lines, shot = pixels(page)
    except ImportError:
        print('pixels: Pillow or numpy is not installed, so the photograph is not read\n')
        return
    if save:
        open(save, 'wb').write(shot)
    print('pixels, the window photographed (content left out): '
          + (f'{len(lines)} cluster(s) to look at' if lines else "every readable hue is one the kit paints"))
    for line in lines:
        print(line)
    if on:
        print('  hues on screen by family (a signal\'s must carry its meaning): '
              + ', '.join(f'{f} {n}' for f, n in on.items()))
    print()


def write_record():
    css = _read('style/common.css')
    if css is None:
        print(f'record: no Vivaldi interface at {VIVALDI_RES}'); return False
    import subprocess
    try:
        build = subprocess.run(['vivaldi', '--version'], capture_output=True, text=True).stdout.split()[1]
    except (OSError, IndexError):
        build = '?'
    import datetime
    out = {'build': build, 'recorded': datetime.date.today().isoformat(),
           'note': 'Vivaldi\'s own font-size declarations under CHROME_PX, read off resources/vivaldi/style/common.css '
                   'by build/vivaldi.py --record: selectors and sizes only. Never hand-edit.',
           'sizes': small_sizes(css)}
    open(RECORD, 'w').write(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(f"wrote {os.path.relpath(RECORD, ROOT)}: {len(out['sizes'])} sizes under {CHROME_PX} px, off {build}")
    return True


def _print_derivations():
    print("=== the roles the stylesheet may name, and nothing else ===")
    for name, hx in ROLES.items():
        fam, gap, req = P.clearance(hx)
        tag = ('reserved for legend (§3)' if name in RESERVED else
               'a pole by construction: the meaning, present' if name in SIGNAL and P.readable(hx) and gap < req else
               'neutral, no readable hue' if not P.readable(hx) else f'clears {gap:.1f}deg from {fam}, needs {req:.1f}')
        print(f"  --rm-{name:13} {hx}  {tag:44} {SOURCE[name]}")
    rec = record()
    print(f"\n=== the size (CHOSEN, under the floors) ===\n  the chrome's text at {CHROME_PX} px; the root and "
          f"{len(rec['sizes'])} of Vivaldi's own sizes raised to it (recorded off {rec['build']}, {rec['recorded']}):")
    for px in sorted({px for _, _, px in rec['sizes']}, reverse=True):
        print(f"    {px:5g} px  {sum(1 for _, _, x in rec['sizes'] if x == px):4} declarations")
    print("\n=== what the native theme alone paints: the engine's derivation from the kit's four, against the table ===")
    for n, v in ENGINE.items():
        c = colour(v)
        pinned = colour(resolve(n))
        if c is None or pinned is None:
            continue
        r = role_of(c[0]) if c[1] == 1 else None
        dE = ok.delta_e(c[0], pinned[0]) if c[1] == 1 and pinned[1] == 1 else float('nan')
        label = ('transparent' if pinned[1] == 0 else role_of(pinned[0]) or pinned[0])
        print(f"  {n:34} {v:24} {'on ' + r if r and r not in RESERVED else 'OFF' if c[1] == 1 else 'blend':12} "
              f"-> {label:12} dE {dE:5.1f}")


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--write' in sys.argv:
        write(); sys.exit(0)
    if '--record' in sys.argv:
        sys.exit(0 if write_record() else 1)
    if '--coverage' in sys.argv:
        sys.exit(0 if coverage() else 1)
    if '--screen' in sys.argv:
        sys.exit(0 if screen(sys.argv[sys.argv.index('--screen') + 1], '--brief' in sys.argv) else 1)
    sys.exit(0 if check() else 1)
