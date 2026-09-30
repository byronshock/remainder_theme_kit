"""The Windows surface: derive its ladders, write the files, then check what is committed.
AUTHORITY.md is the authority.

Windows asks for more values than the kit authors, and it asks for them in five notations, none
of which is a hex string. §2 has seven values; the legacy colours table has thirty-one slots and
the accent palette has eight, and none of them may be filled by eye (principle 10) or with a
value that reads as a signal (principle 1). So each is a ladder derived from what the kit already
has, and the derivation ships here beside the surface.

  COLOURS    thirty-one slots in `[Control Panel\\Colors]`, and every one lands EXACTLY on one of
             §2's seven. No interpolation: Windows' colour table is a table of ROLES, not a ramp,
             so each slot is a role assignment and the ladder is the assignment itself. The three
             bevel slots collapse onto one value on purpose -- §5 has one rule and no bevel.

  ACCENT     eight slots. Seven of them are a light-to-dark ramp Windows reads by index, and the
             eighth is a separate emphasis slot. DERIVED: the ramp's step is ACCENT-to-SELECT
             halved, repeated outward, so ACCENT lands exactly on index 3 -- the slot `AccentColor`
             mirrors -- and SELECT exactly on index 5, the slot the menus read. Nothing invents an
             endpoint: the two values §2 authors set the step and the ramp is that step repeated.

  REMOVAL    no colours at all. §0's larger half, in `declutter.reg`, and the checker's job there
             is to prove there is no colour in it rather than to derive one.

The five notations are the reason this file exists at all. `build/cosmic.py` learned that a value
the checker cannot read is a value nobody is checking, after a panel background sat unchecked
because it was written as a RON decimal triple. Windows is that problem five times over:

    15 9 12                     REG_SZ decimal triple      [Control Panel\\Colors]
    dword:00563577              DWORD, ABGR, alpha high    DWM AccentColor
    0XC4773556                  AARRGGBB, .theme           [VisualStyles] ColorizationColor
    dword:c4773556              DWORD, AARRGGBB, alpha C4  DWM ColorizationColor, ColorizationAfterglow
    hex:ae,67,88,00,...         REG_BINARY, RGBA quads     Explorer\\Accent AccentPalette
    #763555                     hex                        comments and the README

Every one of them round-trips: `dec_triple`, `abgr_dword`, `argb_theme`, `argb_dword` and
`rgba_quad` write them and `_decode` reads every one back out of every committed file --
including install.cmd, which prints two hex values in its closing instructions. A notation not
listed here appearing in this directory belongs here before it ships.

TWO BYTE ORDERS UNDER ONE REGISTRY KEY, and nothing in the value says which. `AccentColor` and
`AccentColorInactive` under DWM are ABGR; `ColorizationColor` and `ColorizationAfterglow` under
the same key are AARRGGBB, the order the .theme's [VisualStyles] value already uses and the
order Microsoft's documented default `0xC40078D7` shows. Until 2026-09-21 this file wrote the
Colorization pair ABGR, and its own checker passed them: it decoded the DWORD the same wrong
way the writer had encoded it, so the file agreed with itself and disagreed with Windows. A
checker verifies a file against its reading of a notation; it cannot verify the reading. What
caught it was the parity rule (CONTRIBUTING.md 11) -- the parent kit's theme.reg writes the
pair AARRGGBB and says so in a comment. The decoder now tells the two apart BY KEY NAME, the
same way it tells a flag from a colour.

    python3 build/windows.py              check every value in elevated/windows/
    python3 build/windows.py --derive     the two ladders, and how each value was reached
    python3 build/windows.py --write      regenerate the two generated files
    python3 build/windows.py --registry   the registry claims: what is inherited, what is unverified

WHAT THIS FILE MEASURES AND WHAT IT DOES NOT. The colour work is measured and is a gate: every
value, every pair's APCA Lc, every ΔE, every pole clearance, every notation round-trip. All of it
is colorimetry and none of it needs Windows. The REGISTRY claims are a different kind of thing --
that a key exists on 24H2 and does what PLATFORM.md says it does -- and this kit has no Windows
machine to measure them on. They are inherited from PLATFORM.md and reported by `--registry` as a
table to verify, never as a gate. That split is the same one `build/firefox.py --coverage` draws:
a report is not a gate, and saying so is cheaper than a false pass.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
WIN = os.path.join(ROOT, 'elevated', 'windows')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
N, CH = PAL['neutrals'], PAL['chrome']
WHITE, LIGHT, DARK, BLACK = N['WHITE'], N['LIGHT'], N['DARK'], N['BLACK']
ACCENT, SELECT, CURSOR = CH['ACCENT'], CH['SELECT'], CH['CURSOR']
SEMANTIC = {'SUCCESS': '#006B54', 'WARNING': '#FCD116', 'DESTRUCTIVE': '#AF1E2D'}
FLOOR = PAL['surface_floor_dE']
ROLE = {WHITE: 'WHITE', LIGHT: 'LIGHT', DARK: 'DARK', BLACK: 'BLACK',
        ACCENT: 'ACCENT', SELECT: 'SELECT', CURSOR: 'CURSOR'}

GENERATED = ('remainder.theme', 'remainder.reg')


# --- 1. the thirty-one colour slots ------------------------------------------------------------
# DERIVED, in the sense that matters: each slot is a ROLE and §2 names the value for every role
# the kit has an opinion about. Windows' table is not a ramp, so there is nothing to interpolate
# and nothing lands off the kit's own values -- which is the stronger of the two arrangements §8
# describes. What had to be decided is which role each slot plays, and that is stated per slot.
#
# Three slots deserve their reason in the open:
#   ButtonHilight/ButtonLight/ButtonFace all take LIGHT, which erases the Win95 bevel. That is
#     §5: one rule, drawn outside the field it bounds, and no second lighter line. The bevel is
#     a separator thinner than the rule, so the kit does not draw it.
#   ActiveBorder/InactiveBorder/WindowFrame all take BLACK, and Background takes BLACK too, so a
#     window's edge against the desktop is ΔE 0.0. That is §5 again: the gap IS the rule.
#   GradientActiveTitle equals ActiveTitle, which flattens the titlebar gradient. A gradient is a
#     value the kit did not author, continuously, across the one surface that carries state.
COLORS = [
    ('ActiveTitle',           ACCENT, 'key titlebar -- the one surface carrying key state'),
    ('GradientActiveTitle',   ACCENT, 'gradient end; equal to ActiveTitle, so the titlebar is flat'),
    ('TitleText',             WHITE,  'key titlebar text'),
    ('InactiveTitle',         LIGHT,  'non-key titlebar'),
    ('GradientInactiveTitle', LIGHT,  'gradient end; equal to InactiveTitle'),
    ('InactiveTitleText',     BLACK,  'non-key titlebar text'),
    ('Background',            BLACK,  'the desktop field (§5: flat BLACK, no painting)'),
    ('Window',                WHITE,  'window backgrounds, fields, lists'),
    ('WindowText',            BLACK,  'body text on the window field'),
    ('WindowFrame',           BLACK,  'the rule (§5)'),
    ('ActiveBorder',          BLACK,  'the rule, key window'),
    ('InactiveBorder',        BLACK,  'the rule, non-key window'),
    ('Menu',                  WHITE,  'menu ground'),
    ('MenuText',              BLACK,  'menu text'),
    ('MenuBar',               WHITE,  'menu bar ground'),
    ('MenuHilight',           SELECT, 'the highlighted menu item'),
    ('Hilight',               SELECT, 'selected rows and selected text'),
    ('HilightText',           WHITE,  'text on a selected row'),
    ('HotTrackingColor',      ACCENT, 'hover and links (§3: links route to ACCENT)'),
    ('ButtonFace',            LIGHT,  'panels, buttons, toolbars'),
    ('ButtonText',            BLACK,  'button text'),
    ('ButtonHilight',         LIGHT,  'bevel light edge -- equal to ButtonFace (§5: no bevel)'),
    ('ButtonLight',           LIGHT,  'bevel light edge -- equal to ButtonFace (§5: no bevel)'),
    ('ButtonShadow',          DARK,   'bevel shadow'),
    ('ButtonDkShadow',        BLACK,  'bevel outer shadow -- the rule'),
    ('ButtonAlternateFace',   LIGHT,  'alternate button face'),
    ('GrayText',              DARK,   'disabled text (§2 names this DARK\'s use)'),
    ('Scrollbar',             LIGHT,  'scrollbar trough'),
    ('AppWorkspace',          DARK,   'MDI workspace behind child windows'),
    ('InfoWindow',            WHITE,  'tooltip ground'),
    ('InfoText',              BLACK,  'tooltip text'),
]

# Every text-on-ground pair the table above states, with the APCA tier it has to reach. The
# lesson `build/firefox.py` added and §8 says to carry forward: MEASURE the pairs, do not read a
# table. A .theme file says what text sits on what ground exactly as a stylesheet does, so the
# checker reads both sides out of the assignment and measures them.
#
# The tiers are APCA's own (build/apca.py GUIDANCE) at §2's ~16px effective:
#   90 body text preferred   75 body text minimum   60 bold or large   30 non-text marks
# Windows draws its chrome at the system size and the kit does not set a weight in a .theme, so
# every pair here is read at the 400 floor for its job except the two §2 itself authors bold.
PAIRS = [
    ('TitleText',         'ActiveTitle',         60.0, 'key titlebar text, bold (§2)'),
    ('InactiveTitleText', 'InactiveTitle',       60.0, 'non-key titlebar text, bold (§2)'),
    ('WindowText',        'Window',              90.0, 'body text on the window field'),
    ('MenuText',          'Menu',                90.0, 'menu text'),
    ('MenuText',          'MenuBar',             90.0, 'menu bar text'),
    ('HilightText',       'Hilight',             75.0, 'text on a selected row'),
    ('HilightText',       'MenuHilight',         75.0, 'text on the highlighted menu item'),
    ('ButtonText',        'ButtonFace',          60.0, 'button and panel text, bold (§2)'),
    ('InfoText',          'InfoWindow',          90.0, 'tooltip text'),
    ('GrayText',          'ButtonFace',          30.0, 'disabled text on a panel -- APCA\'s disabled tier'),
    ('GrayText',          'Window',              30.0, 'disabled text on the field'),
    ('WindowText',        'Scrollbar',           60.0, 'scrollbar arrows on the trough'),
    ('HotTrackingColor',  'Window',              75.0, 'a link on the window field -- it is read'),
    ('HotTrackingColor',  'ButtonFace',          30.0, 'hover on a panel -- a mark, not a label'),
]

# Surface adjacencies the table creates that carry information. §2's SURFACE_FLOOR is ΔE 17.1.
# Rule-against-chrome is exempt for §2's stated reason, and the desktop/border pair is ΔE 0.0 by
# construction because §5 makes the gap the rule.
ADJACENT = [
    ('Window',       'ButtonFace',     'the field against a panel -- the separator §5 names'),
    ('ButtonFace',   'ButtonShadow',   'a panel against its shadow slot'),
    ('ButtonShadow', 'ButtonDkShadow', 'shadow against the rule'),
    ('Window',       'Hilight',        'a selected row against the rows around it'),
    ('AppWorkspace', 'Background',     'the MDI workspace against the desktop'),
    ('Window',       'Background',     'a window against the desktop'),
]
EXEMPT_ADJACENT = {('ActiveBorder', 'Background'): 'the gap IS the rule (§5) -- ΔE 0.0 by construction',
                   ('ActiveTitle', 'Hilight'): 'selection reads against its own rows (§2 exempts it)'}


def colors():
    """[(slot, hex, role, note)] -- the thirty-one, each on one of §2's seven."""
    return [(k, v, ROLE[v], why) for k, v, why in COLORS]


# --- 2. the eight accent slots -----------------------------------------------------------------
# Windows stores its accent as an eight-entry palette of RGBA quads. Seven are a light-to-dark
# ramp read by index -- index 3 is the accent Settings shows and `AccentColor` mirrors, and the
# darker indices are what the menus and the Start surface read -- and index 7 is a separate
# emphasis slot which Windows ships as an ORANGE, inside the caution pole, unrelated to the ramp.
#
# DERIVED. The step is ACCENT-to-SELECT halved, because those two sit two indices apart (3 and 5),
# and the ramp is that step repeated outward at CHROME chroma and the home hue. So the kit's own
# two chrome values land on their slots EXACTLY and nothing invents an endpoint -- the alternative
# was to stretch the ramp to the gamut edge at both ends to match the reach of Microsoft's own
# default palette, which would have made the endpoints a preference dressed as a derivation (§0c).
#
# The ramp is quieter than Windows' own by exactly the margin §2 chose: CHROME is chroma 0.100
# against a signal's 0.179, so index 0 comes out L 0.60 where Microsoft's comes out L 0.84. That
# is the kit's thesis, not a shortfall, and the consequence is recorded rather than hidden: index 0
# is a hover tint that carries dark text, not a ground for the white text index 3 carries.
#
# Every slot clears every pole by construction -- the pole test is a hue question above C_FLOOR,
# and the whole ramp sits at the home hue -- so whichever index a given Windows build reads for a
# given surface, it reads an authored value. That is the property that makes the ladder robust to
# the one thing this kit cannot verify from here (§8, and the header above).
ACCENT_MAIN, ACCENT_MENU = 3, 5          # the two indices §2's own values are anchored onto
ACCENT_SLOTS = 8


def accent_ramp():
    """[(i, hex, note)] -- eight slots. Index 3 IS ACCENT and index 5 IS SELECT."""
    import derive_palette as D
    La, Ls = ok.lch(ACCENT)[0], ok.lch(SELECT)[0]
    step = (La - Ls) / (ACCENT_MENU - ACCENT_MAIN)
    out = []
    for i in range(ACCENT_SLOTS - 1):
        if i == ACCENT_MAIN:
            out.append((i, ACCENT, 'ACCENT')); continue
        if i == ACCENT_MENU:
            out.append((i, SELECT, 'SELECT')); continue
        L = La + (ACCENT_MAIN - i) * step
        out.append((i, ok.hexs(ok.from_lch(L, D.CHROME, D.HOME_HUE)), ''))
    # Index 7 is not on the ramp. Windows ships a caution-pole orange here; the kit gives it
    # ACCENT, which removes a pole from the chrome and adds no value (principle 1).
    out.append((7, ACCENT, 'emphasis slot, off the ramp -- ACCENT, where Windows ships an orange'))
    return out


# --- 3. the five notations ---------------------------------------------------------------------
# A value the checker cannot read is a value nobody is checking (§8). These are every form a
# colour takes anywhere in elevated/windows/, in both directions.
def dec_triple(hx):
    """#RRGGBB -> '15 9 12'. The [Control Panel\\Colors] notation, REG_SZ decimal."""
    return '%d %d %d' % tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))


def abgr_dword(hx):
    """#RRGGBB -> '00563577'. DWM and Explorer\\Accent store colours as ABGR with the alpha high."""
    r, g, b = (hx[i:i + 2] for i in (1, 3, 5))
    return ('00' + b + g + r).lower()


def argb_theme(hx, alpha='C4'):
    """#RRGGBB -> '0XC4773556'. [VisualStyles] ColorizationColor is AARRGGBB, not ABGR."""
    return '0X' + alpha + hx[1:].upper()


def argb_dword(hx, alpha='c4'):
    """#RRGGBB -> 'c4773556'. The DWM ColorizationColor and ColorizationAfterglow DWORDs are AARRGGBB
    too -- the same byte order as the .theme value the shell copies into them, with the C4 alpha the
    documented default carries. Not ABGR, which is what AccentColor beside them is (the header)."""
    return (alpha + hx[1:]).lower()


def rgba_quad(hx):
    """#RRGGBB -> 'ae,67,88,00'. AccentPalette is eight RGBA quads, REG_BINARY."""
    return ','.join(hx[i:i + 2].lower() for i in (1, 3, 5)) + ',00'


# A decimal triple appears BARE in a .theme (`ActiveTitle=119 53 86`) and QUOTED in a .reg
# (`"ActiveTitle"="119 53 86"`), and the first draft of this file read only the bare form. That
# silently skipped all thirty-one values in remainder.reg -- the same failure as the COSMIC panel
# background, in a second notation, caught here by the checker's own output rather than by review.
_DEC = re.compile(r'^\s*"?[A-Za-z]+"?\s*=\s*"?(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})"?\s*$', re.M)
_DWORD = re.compile(r'dword:([0-9A-Fa-f]{8})')
# The two DWORDs that are AARRGGBB rather than ABGR, by NAME -- the value cannot say (the header).
_DWORD_ARGB = re.compile(r'"(?:ColorizationColor|ColorizationAfterglow)"\s*=\s*dword:([0-9A-Fa-f]{8})')
_ARGB = re.compile(r'=\s*0[Xx]([0-9A-Fa-f]{8})\b')
_BIN = re.compile(r'hex:((?:[0-9A-Fa-f]{2},?\s*\\?\s*)+)')
# The optional trailing pair is an alpha byte. Nothing in elevated/windows/ writes one --
# but build/cosmic.py carries the same allowance because the .ron files do, and a regex
# that stops at six digits does not fail on `#F1E4E9FF`, it silently matches nothing.
_HEX = re.compile(r'#([0-9A-Fa-f]{6})(?:[0-9A-Fa-f]{2})?\b')


def _decode(body):
    """Every colour in `body`, in all five notations, as [(hex, notation)].

    The caller strips comments and the values that are not colours first; see _reg_colours.
    """
    out = []
    for m in _DEC.finditer(body):
        v = [int(g) for g in m.groups()]
        if all(x <= 255 for x in v):
            out.append(('#%02X%02X%02X' % tuple(v), 'decimal triple'))
    argb = []
    for m in _DWORD_ARGB.finditer(body):
        d = m.group(1).lower()
        out.append(('#' + d[2:8].upper(), 'dword AARRGGBB'))
        argb.append(m.span(1))
    for m in _DWORD.finditer(body):
        if m.span(1) in argb:
            continue
        d = m.group(1).lower()
        out.append(('#' + (d[6:8] + d[4:6] + d[2:4]).upper(), 'dword ABGR'))
    for m in _ARGB.finditer(body):
        out.append(('#' + m.group(1)[2:].upper(), 'theme AARRGGBB'))
    for m in _BIN.finditer(body):
        by = [b for b in re.split(r'[,\s\\]+', m.group(1)) if b]
        for i in range(0, len(by) - 3, 4):
            out.append(('#' + ''.join(by[i:i + 3]).upper(), 'REG_BINARY RGBA'))
    for m in _HEX.finditer(body):
        out.append(('#' + m.group(1).upper(), 'hex'))
    return out


# Registry values that are DWORDs or REG_BINARY but are NOT colours: flags, masks, delays.
# `_decode` cannot tell a flag from an ABGR colour by looking -- dword:00000001 decodes to a
# perfectly plausible #000100 -- so the checker is told which keys are which, BY NAME.
#
# The list is a deny-list and not an allow-list on purpose, so the default for an unrecognised
# key is to read it as a colour and demand a ladder for it. That fails loudly on a key nobody
# classified, which is the safe direction: a missed colour is unchecked paint, and a flag read
# as a colour is one line in this list.
#
# UserPreferencesMask is why the REG_BINARY half exists. It is eight bytes of animation flags,
# and _BIN read `hex:90,12,03,80,10,00,00,00` as two RGBA quads -- #901203, which sits 1.6 deg
# from destructive and duly failed the pole test. A mask is not a colour and the checker now
# says so by name rather than by tolerating a pole.
NOT_A_COLOUR = re.compile(
    r'"(ColorPrevalence|EnableTransparency|AppsUseLightTheme|SystemUsesLightTheme|EnableAeroPeek|'
    r'DynamicScrollbars|MenuShowDelay|DragFullWindows|MinAnimate|UserPreferencesMask|'
    r'TaskbarAl|TaskbarDa|TaskbarMn|TaskbarSi|TaskbarGlomLevel|ShowTaskViewButton|'
    r'Start_IrisRecommendations|Start_TrackDocs|Start_TrackProgs|Start_Layout|'
    r'SubscribedContent-\d+Enabled|SubscribedContentEnabled|RotatingLockScreenEnabled|'
    r'RotatingLockScreenOverlayEnabled|SoftLandingEnabled|SilentInstalledAppsEnabled|'
    r'SystemPaneSuggestionsEnabled|ContentDeliveryAllowed|OemPreInstalledAppsEnabled|'
    r'PreInstalledAppsEnabled|PreInstalledAppsEverEnabled|FeatureManagementEnabled|'
    r'IsCortanaEnabled|ShowCopilotButton|SearchboxTaskbarMode|BingSearchEnabled|'
    r'CortanaConsent|AllowSearchToUseLocation|EnableDynamicContentInWSB|ScoobeSystemSettingEnabled|'
    r'ShellFeedsTaskbarViewMode|IconsOnly|ListviewAlphaSelect|ListviewShadow|TaskbarAnimations|'
    r'DisallowShaking|VisualFXSetting|CaretWidth|HideFileExt|LaunchTo|ServerAdminUI|'
    # `Enabled` is the notification toast's own switch and is the one generic name on this list.
    # It is listed because declutter.reg needs it; if a colour ever ships under a key called
    # exactly `Enabled`, this line is what would skip it, and it would want a narrower pattern.
    r'IsDynamicSearchBoxEnabled|Enabled)"'
    r'\s*=\s*(dword:|hex:|")')


def _reg_colours(body):
    """Drop the .reg lines whose value is a flag or a mask rather than a colour.

    REG_BINARY may continue across lines with a trailing backslash, so continuations are joined
    onto their key line BEFORE the filter runs -- otherwise the tail of a stripped mask survives
    as a headless run of bytes and decodes as a colour again.
    """
    joined, buf = [], ''
    for ln in body.splitlines():
        buf += ln.rstrip()
        if buf.endswith('\\'):
            buf = buf[:-1]
            continue
        joined.append(buf)
        buf = ''
    if buf:
        joined.append(buf)
    return '\n'.join(ln for ln in joined if not NOT_A_COLOUR.search(ln))


# --- 4. the two generated files ----------------------------------------------------------------
# GENERATED and COMMITTED, for the same reason elevated/remainder.stylus.json is (§11): the file
# Windows reads is not the file a person edits. Every value below is a mechanical transform of
# palette.json into one of the five notations, and a hand-typed ABGR DWORD is exactly the value
# §8 says a checker catches more reliably than the pole test does. `--write` regenerates both and
# the checker fails if what is committed is not what the generator now produces.
THEME_HEADER = """; Remainder for Windows -- the colours table. AUTHORITY.md is the authority.
; GENERATED by build/windows.py --write. Do not hand-edit: edit poles.json or the derivation.
;
; Thirty-one slots, every one on one of the seven values AUTHORITY.md sec. 2 authors. Apply it
; by double-clicking it; Settings opens on Themes with Remainder selected and applied.
;
; Applying a theme rewrites the DWM accent keys, so remainder.reg goes AFTER this file, never
; before. install.cmd does them in that order.
;
; ASCII, CRLF, and no byte-order mark, on purpose. The rest of the kit writes UTF-8 and uses
; the section mark freely; these two files are read by Windows, which takes a .reg or .theme
; without a BOM as ANSI, so a section mark in a comment would arrive as mojibake. The section
; references here are spelled out instead. build/windows.py refuses to write a non-ASCII byte.
"""

REG_HEADER = """Windows Registry Editor Version 5.00

; Remainder for Windows -- accent, personalisation, and the motion and transparency that
; AUTHORITY.md sec. 0 removes. GENERATED by build/windows.py --write. Do not hand-edit.
;
; Merge this AFTER applying remainder.theme: applying a theme rewrites the DWM accent keys.
; Sign out and back in, or run install.cmd, for the shell to re-read all of it.
;
; ASCII, CRLF, no BOM -- see remainder.theme's header for why.
"""


def _theme():
    L = [THEME_HEADER, '', '[Theme]', 'DisplayName=Remainder', '',
         '; The legacy Win32 colours table. Decimal RGB triples -- Windows reads no other',
         '; notation here, which is why build/windows.py learned this one first.',
         '[Control Panel\\Colors]']
    for slot, hx, role, why in colors():
        L.append('%s=%s' % (slot, dec_triple(hx)))
    L += ['',
          '; AUTHORITY.md sec. 5: the desktop field is a flat BLACK one. No wallpaper, no pattern -- the value',
          '; above in Background is the whole desktop, and the tiling gaps ARE the rule.',
          '[Control Panel\\Desktop]',
          'Wallpaper=',
          'TileWallpaper=0',
          'WallpaperStyle=10',
          'Pattern=',
          '',
          '; AutoColorization=0 keeps Windows from sampling a wallpaper for the accent: there is',
          '; no wallpaper, and an accent derived from a photograph is a value nobody authored.',
          '; ColorizationColor is AARRGGBB here, and so is the DWM ColorizationColor DWORD that',
          '; remainder.reg writes -- the shell copies this value into that key. AccentColor is ABGR.',
          '[VisualStyles]',
          'Path=%SystemRoot%\\resources\\themes\\Aero\\Aero.msstyles',
          'ColorStyle=NormalColor',
          'Size=NormalSize',
          'AutoColorization=0',
          'ColorizationColor=' + argb_theme(ACCENT),
          '; Light mode, and the standard theme engine -- not a contrast theme. PLATFORM.md:',
          '; forced colours strip affordances users need and read as an accessibility mode.',
          'SystemMode=Light',
          'AppMode=Light',
          'Transparency=0',
          '',
          '[MasterThemeSelector]',
          'MTSM=RJSPBS',
          '']
    return _crlf(L)


def _reg():
    ramp = accent_ramp()
    palette = ''.join(rgba_quad(hx) + ',' for _, hx, _ in ramp).rstrip(',')
    L = [REG_HEADER, '',
         '; The colours table again, as registry values. The .theme file writes these when it is',
         '; applied; merging them too means the table is right even if the theme is not applied.',
         '[HKEY_CURRENT_USER\\Control Panel\\Colors]']
    for slot, hx, role, why in colors():
        L.append('"%s"="%s"' % (slot, dec_triple(hx)))
    L += ['',
          '; DWM. Two byte orders under one key, and only the key name says which: AccentColor and',
          '; AccentColorInactive are ABGR, alpha high -- #763555 is dword:' + abgr_dword(ACCENT) + '.',
          '; ColorizationColor and ColorizationAfterglow are AARRGGBB, like the .theme value the shell',
          '; copies into them, with the C4 alpha the documented default 0xC40078D7 carries -- the same',
          '; #763555 is dword:' + argb_dword(ACCENT) + '. Written ABGR until 2026-09-21; build/windows.py says why.',
          '; ColorPrevalence=1 puts the accent on title bars and borders, which is what makes the',
          '; key titlebar ACCENT. AccentColorInactive is the non-key one (PLATFORM.md names it).',
          '[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\DWM]',
          '"AccentColor"=dword:' + abgr_dword(ACCENT),
          '"AccentColorInactive"=dword:' + abgr_dword(LIGHT),
          '"ColorizationColor"=dword:' + argb_dword(ACCENT),
          '"ColorizationAfterglow"=dword:' + argb_dword(ACCENT),
          '"ColorPrevalence"=dword:00000001',
          '"EnableAeroPeek"=dword:00000000',
          '',
          '; The eight-slot accent palette: RGBA quads, REG_BINARY, light to dark. Index 3 is',
          '; ACCENT and index 5 is SELECT, exactly (build/windows.py --derive).',
          '[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent]',
          '"AccentPalette"=hex:' + palette,
          '"AccentColorMenu"=dword:' + abgr_dword(ramp[ACCENT_MENU][1]),
          '"StartColorMenu"=dword:' + abgr_dword(ramp[ACCENT_MENU][1]),
          '',
          '; Light, and transparency off system-wide. Mica and acrylic paint a surface as a blend',
          '; of two things rather than a value the kit set, which is not an authored value at all.',
          '[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize]',
          '"AppsUseLightTheme"=dword:00000001',
          '"SystemUsesLightTheme"=dword:00000001',
          '"EnableTransparency"=dword:00000000',
          '',
          '; AUTHORITY.md sec. 0, the larger half: motion. UserPreferencesMask is the conventional "adjust for best',
          '; performance" mask -- animations, fades and slides off, with the settings a user still',
          '; needs left on. MenuShowDelay=0 is the menu that opens when it is pointed at.',
          '[HKEY_CURRENT_USER\\Control Panel\\Desktop]',
          '"UserPreferencesMask"=hex:90,12,03,80,10,00,00,00',
          '"MenuShowDelay"="0"',
          '"DragFullWindows"="1"',
          '',
          '[HKEY_CURRENT_USER\\Control Panel\\Desktop\\WindowMetrics]',
          '"MinAnimate"="0"',
          '',
          '; Scrollbars always shown. A scrollbar that appears on approach is a control that is',
          '; not there until it is looked for, and the position it reports is information.',
          '[HKEY_CURRENT_USER\\Control Panel\\Accessibility]',
          '"DynamicScrollbars"=dword:00000000',
          '',
          '; Visual effects: the shell\'s own animation switches, set to match the mask above.',
          '[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced]',
          '"TaskbarAnimations"=dword:00000000',
          '"ListviewAlphaSelect"=dword:00000000',
          '"ListviewShadow"=dword:00000000',
          '"IconsOnly"=dword:00000000',
          '',
          # A bare comment, NOT a key. An earlier draft parked this note under a
          # `DWM\\.rm-note` subkey, which would have created a real registry key that does
          # nothing -- and `reg import` cannot delete a key, so the backup install.cmd takes
          # could not have removed it again. A theme does not leave litter in the registry.
          '; Square corners are per-window (DWMWA_WINDOW_CORNER_PREFERENCE) and no registry',
          '; key reaches them; PLATFORM.md records that, and this surface does not pretend',
          '; otherwise. The 1 px DWM frame and the control corner radii are out of reach at',
          '; any tier -- tolerated, never echoed (AUTHORITY.md sec. 4).',
          '']
    return _crlf(L)


def _crlf(lines):
    """Join to one CRLF-terminated string, normalising any line ending the pieces carried.

    THEME_HEADER and REG_HEADER are multi-line strings that enter the list as a single element
    each, so a plain CRLF join left their own newlines bare -- the files shipped with mixed
    endings until `file` reported "CRLF, LF line terminators" on one and not the other. A .reg
    is read line-wise and regedit tolerates it, which is exactly why it would have gone on being
    wrong. Normalising the finished text cannot regress the way a careful join can.
    """
    text = '\n'.join(lines) if not isinstance(lines, str) else lines
    return '\r\n'.join(text.replace('\r\n', '\n').replace('\r', '\n').split('\n'))


def _ascii(name, body):
    """The two generated files are ASCII and all-CRLF, or they are not written.

    Both are load-bearing on Windows and neither is visible in a diff, so both are enforced at
    the one point the bytes are produced -- which is also the point the checker compares against,
    so a file that drifted could not pass by being regenerated wrong the same way twice.
    """
    lf, crlf = body.count('\n'), body.count('\r\n')
    if lf != crlf:
        raise SystemExit('%s: %d line ending(s) are a bare LF where Windows wants CRLF. '
                         'Build the body through _crlf().' % (name, lf - crlf))
    try:
        return body.encode('ascii')
    except UnicodeEncodeError as e:
        ln = body[:e.start].count('\n') + 1
        raise SystemExit('%s line %d: %r is not ASCII. Windows reads a .reg or .theme without a '
                         'BOM as ANSI, so this would import as mojibake. Spell it out.'
                         % (name, ln, body[e.start:e.end]))


def write():
    os.makedirs(WIN, exist_ok=True)
    for name, body in (('remainder.theme', _theme()), ('remainder.reg', _reg())):
        path = os.path.join(WIN, name)
        with open(path, 'wb') as f:
            f.write(_ascii(name, body))
        print('wrote %s  (%d bytes)' % (os.path.relpath(path, ROOT), len(body)))


# --- 5. what the checker knows -----------------------------------------------------------------
def authored():
    """Every hex the committed files may contain, and what it is."""
    reg = dict(ROLE)
    reg.update({v: k for k, v in SEMANTIC.items()})
    for i, hx, note in accent_ramp():
        reg.setdefault(hx, 'accent_%d' % i)
    return reg


def check():
    if not os.path.isdir(WIN):
        print('windows: nothing committed in elevated/windows yet'); return False
    reg, bad = authored(), 0

    # (a) the generated files are what the generator now produces. Same guard as
    #     build/stylus.py puts on the committed Stylus JSON (§11): a file a person edited by
    #     hand is a file whose values nobody derived.
    for name, body in (('remainder.theme', _theme()), ('remainder.reg', _reg())):
        path = os.path.join(WIN, name)
        if not os.path.isfile(path):
            print('  %-22s MISSING -- run build/windows.py --write' % name); bad += 1; continue
        on_disk = open(path, "rb").read()
        same = on_disk == _ascii(name, body)
        print('  %-22s %s' % (name, 'matches the generator' if same else
                              'DIFFERS FROM THE GENERATOR -- run --write'))
        bad += not same

    # (b) every value in every file, in every notation.
    files = sorted(f for f in os.listdir(WIN) if os.path.isfile(os.path.join(WIN, f)))
    for fn in files:
        raw = open(os.path.join(WIN, fn), errors='ignore').read()
        # Comments quote values on purpose, exactly as the .ron files do, so they are stripped
        # before the scan. The comment character is `;` in a .reg and a .theme and `::` in a .cmd
        # -- and NOT `#`, which is what a hex colour starts with. Stripping `^\s*#` as a comment
        # would have silently eaten any value written alone on its line, which is the same class
        # of blind spot as the notation this module exists for.
        body = re.sub(r'^\s*(;|::).*$', '', raw, flags=re.M)
        body = _reg_colours(body) if fn.endswith('.reg') else body
        seen = {}
        for hx, form in _decode(body):
            seen.setdefault((hx, form), 0)
            seen[(hx, form)] += 1
        print('\n%s: %d distinct value(s), %d notation(s)'
              % (fn, len({h for h, _ in seen}), len({f for _, f in seen})))
        for (hx, form), n in sorted(seen.items()):
            role, note = reg.get(hx), ''
            if role is None:
                note = 'NOT DERIVED BY ANY LADDER'; bad += 1
            elif P.reserved(hx):
                note = 'reserved, legend use only -- check the context'; bad += 1
            if not P.clear(hx) and role not in SEMANTIC:
                note = (note + ' POLE: chrome must clear every pole').strip(); bad += 1
            fam, gap, req = P.clearance(hx)
            tag = 'neutral' if not P.readable(hx) else '%5.1f/%4.1f %s' % (gap, req, fam)
            print('  %s x%-3d %-18s %-12s %-22s %s' % (hx, n, str(role), form, tag, note))
        if not seen:
            # declutter.reg sets no colour by design and fonts.reg sets none either. Printing the
            # absence is the point: §8 asks a checker to read every file the installer touches, and
            # a file reported as carrying nothing has been read.
            print('  (no colour in this file -- nothing here paints)')

    # (c) every pair the colours table states, measured. §8: measure pairs, do not read a table.
    tbl = {k: v for k, v, _ in COLORS}
    print('\nthe colours table: %d slots, %d pairs' % (len(COLORS), len(PAIRS)))
    for text, ground, floor_lc, why in PAIRS:
        v = apca.lc(tbl[text], tbl[ground])
        okp = abs(v) >= floor_lc
        bad += not okp
        print('  %-18s on %-18s %s on %s  Lc %7.1f  floor %4.0f  %+5.1f  %s%s'
              % (text, ground, tbl[text], tbl[ground], v, floor_lc, abs(v) - floor_lc,
                 '' if okp else 'UNDER FLOOR -- ', why))

    # (d) every adjacency the table creates, measured against SURFACE_FLOOR.
    # FLOOR - 0.05 is the tolerance build/firefox.py and build/stylus.py already use, and it is
    # rounding, not slack: palette.json rounds SURFACE_FLOOR to 17.1 where WHITE against LIGHT
    # measures 17.0565. §2 derives the bar FROM that pair, so it meets it exactly by construction
    # and a bare >= would fail the one adjacency the floor is defined by.
    print('\nadjacencies (SURFACE_FLOOR ΔE %.1f, tolerance 0.05 for the rounding in palette.json)'
          % FLOOR)
    for a, b, why in ADJACENT:
        d = ok.delta_e(tbl[a], tbl[b])
        okd = d >= FLOOR - 0.05
        bad += not okd
        print('  %-14s / %-14s ΔE %5.1f  %+5.1f  %s%s'
              % (a, b, d, d - FLOOR, '' if okd else 'UNDER FLOOR -- ', why))
    for (a, b), why in EXEMPT_ADJACENT.items():
        print('  %-14s / %-14s ΔE %5.1f  exempt: %s' % (a, b, ok.delta_e(tbl[a], tbl[b]), why))

    print('\npole test: %s' % ('every value clears' if not bad else '%d DEFECT(S)' % bad))
    return bad == 0


# --- 6. the registry claims: a report, never a gate --------------------------------------------
# Inherited from PLATFORM.md, which is theme-independent and parallel in both kits. This kit has
# no Windows machine, so NOTHING below is measured here. It is printed as a table to verify on the
# machine, the way build/firefox.py --coverage prints the token names it read off the build: a
# report is not a gate, and saying so is cheaper than a false pass.
CLAIMS = [
    ('remainder.theme', 'double-click applies it; Settings opens on Themes', 'PLATFORM.md', 'unverified'),
    ('DWM AccentColor', 'ABGR DWORD; the key titlebar', 'PLATFORM.md', 'unverified'),
    ('DWM ColorizationColor', 'AARRGGBB DWORD, alpha C4 -- not ABGR like AccentColor',
     'the documented default 0xC40078D7; the parent kit writes it the same way',
     'unverified -- written ABGR until 2026-09-21, and the checker could not tell'),
    ('DWM AccentColorInactive', 'the non-key titlebar', 'PLATFORM.md names this key', 'unverified'),
    ('DWM ColorPrevalence', '1 = accent on title bars and borders', 'PLATFORM.md', 'unverified'),
    ('Hilight / HotTrackingColor', 'legacy Win32 honours them', 'PLATFORM.md names both', 'unverified'),
    ('Explorer\\Accent AccentPalette', '8 RGBA quads; index 3 is the accent Settings shows',
     'Microsoft default palette #0078D7 sits at index 3', 'unverified, and the ladder is built '
     'so every index is legal whichever one is read'),
    ('Personalize EnableTransparency', '0 = mica and acrylic off', 'PLATFORM.md', 'unverified'),
    ('Accessibility DynamicScrollbars', '0 = scrollbars always shown', 'PLATFORM.md', 'unverified'),
    ('UserPreferencesMask 90 12 03 80', 'the "best performance" mask; animation off',
     'convention, not PLATFORM.md', 'unverified -- the weakest claim here'),
    ('HKLM FontSubstitutes', 'Segoe UI -> Montserrat in system chrome',
     'PLATFORM.md lists it as the elevated-only reach', 'unverified'),
    ('Text cursor indicator colour', 'Settings > Accessibility > Text cursor',
     'PLATFORM.md gives a Settings path and NO registry key', 'a README step, like the Edge frame'),
    ('Window corner radius', 'DWMWA_WINDOW_CORNER_PREFERENCE, per window',
     'PLATFORM.md: no per-user key reaches it', 'out of reach -- not attempted'),
    ('Control corner radii, 1 px DWM frame', 'not reachable at any tier',
     'PLATFORM.md "Cannot reach per-user"', 'residue, tolerated and not echoed (§4)'),
]


def registry_report():
    print('The registry claims behind elevated/windows/. NONE of this is measured here:')
    print('this kit has no Windows machine, and colour is the only thing build/windows.py gates.\n')
    print('  %-32s %-46s %s' % ('key or file', 'what it is claimed to do', 'status'))
    for key, does, src, status in CLAIMS:
        print('  %-32s %-46s %s' % (key, does, status))
        print('  %-32s   source: %s' % ('', src))
    print('\nVerify on the machine, then record what you find in PLATFORM.md -- which is parallel')
    print('in both kits, so a key confirmed here is confirmed for De Stijl too (CONTRIBUTING §11).')


def _print_derivations():
    print('=== thirty-one colour slots: each a ROLE, every one on one of §2\'s seven ===')
    for slot, hx, role, why in colors():
        L, C, h = ok.lch(hx)
        print('  %-22s %s  %-7s %-14s %s' % (slot, hx, role, dec_triple(hx), why))
    print('\n  Distinct values used: %d of §2\'s 7. Nothing is interpolated: Windows\' table is a'
          % len({h for _, h, _, _ in colors()}))
    print('  table of roles, so the ladder IS the assignment and it cannot land off the kit.')

    print('\n=== eight accent slots: the ACCENT-to-SELECT step, repeated outward ===')
    La, Ls = ok.lch(ACCENT)[0], ok.lch(SELECT)[0]
    print('  step = (L(ACCENT) %.4f - L(SELECT) %.4f) / %d = %.4f\n'
          % (La, Ls, ACCENT_MENU - ACCENT_MAIN, (La - Ls) / (ACCENT_MENU - ACCENT_MAIN)))
    print('  %-3s %-8s %-8s %-14s %-12s %8s %8s  %s'
          % ('idx', 'hex', 'L', 'RGBA quad', 'ABGR dword', 'WHITEon', 'BLACKon', 'note'))
    for i, hx, note in accent_ramp():
        L, C, h = ok.lch(hx)
        fam, gap, req = P.clearance(hx)
        print('  %-3d %-8s %-8.4f %-14s %-12s %8.1f %8.1f  %s'
              % (i, hx, L, rgba_quad(hx), abgr_dword(hx), apca.lc(WHITE, hx), apca.lc(BLACK, hx),
                 note or 'clears %.1f, needs %.1f' % (gap, req)))
    print('\n  Index 0 carries WHITE at Lc %.1f -- under the 60 tier, so it is a hover tint that'
          % apca.lc(WHITE, accent_ramp()[0][1]))
    print('  takes dark text (BLACK on it is Lc %.1f), not a ground for white text. Recorded'
          % apca.lc(BLACK, accent_ramp()[0][1]))
    print('  rather than fixed: stretching the ramp to reach Microsoft\'s lightness would have')
    print('  meant leaving the chroma §2 chose, and CHROME 0.100 is the whole point (§0c).')

    print('\n=== the five notations, round-tripped (the two DWORD byte orders side by side) ===')
    print('  %-8s %-9s %-12s %-12s %-12s %-14s' % ('role', 'hex', 'decimal', 'ABGR dword', 'ARGB dword', 'RGBA quad'))
    for hx in (ACCENT, SELECT, LIGHT, BLACK, WHITE, CURSOR):
        print('  %-8s %-9s %-12s %-12s %-12s %-14s' % (ROLE[hx], hx, dec_triple(hx), abgr_dword(hx),
                                                       argb_dword(hx), rgba_quad(hx)))


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--registry' in sys.argv:
        registry_report(); sys.exit(0)
    if '--write' in sys.argv:
        write(); sys.exit(0)
    sys.exit(0 if check() else 1)
