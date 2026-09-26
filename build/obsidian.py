"""The Obsidian surface: write the theme, then check what is committed. AUTHORITY.md is the authority.

Obsidian is Electron, so the whole window is a web page and a theme is a stylesheet: a folder in each
vault's .obsidian/themes/ holding theme.css and manifest.json. That makes it the Firefox surface's
nearest relative rather than VS Code's -- a theme here sets weights, sizes, radii and structure as
well as colour -- and three things measured off the installed build (the Arch `obsidian` package,
1.13.7 on electron43, 2026-09-25) shape it:

  THE WINDOW KNOWS WHEN IT IS KEY. Obsidian toggles `is-focused` on <body> with the window's focus,
    and with the default hidden frame the top 40 px is its own: the tab strips, the sidebar toggles
    and the window buttons, which the platform already paints from one pair of variables
    (--titlebar-background and its -focused twin). So this is the second surface on this desktop
    that can show key state at all (PLATFORM.md: COSMIC cannot), and it shows it the way Firefox's
    tab strip does: ACCENT carrying WHITE when key, LIGHT carrying BLACK at 700 when not.

  NEARLY EVERY STATE IS A BLEND. Obsidian derives hover, selection, the selected file, tags, the
    text selection and the scrollbars by mixing a colour with transparent (color-mix(in oklch, X N%,
    transparent)); on 1.13.7, 32 of the 302 variables that take a colour resolve to a blend, and 39
    more to #FFFFFF or #000000, which §3 reserves. A blend is not an authored value and nothing
    downstream can measure one, so the theme names an authored value for every one of them that
    paints (CONTRIBUTING.md §8) and leaves only the shadows and the modal scrim, which §4 permits.

  THE UI RENDERS UNDER THE SIZE THE FLOORS ASSUME. Every contrast floor in §0e is a function of
    text at about 16 px (§5), and Obsidian sets its chrome at 12, 13 and 15 px. A checker that
    measured those pairs at the 16 px tiers would be a false pass, which is worse than a failing
    one -- so the theme sets the chrome's text at 16 px (CHOSEN, §5), and the tiers below are the
    tiers on screen.

So the surface is one ladder and a role table, and the derivation ships here (CONTRIBUTING.md §8):

  THE RAMP   Obsidian's twelve --color-base-* slots, SNAPPED to the nearest of §2's four by lightness,
             as build/firefox.py snaps Firefox's greys -- a backstop under the role table, so that a
             variable the table does not name lands on the kit's ladder and cannot land off it.
  ROLES      every variable the theme decides, on one of the kit's values. Weight follows the ground,
             as in worksafe/firefox/: a LIGHT surface carries BLACK at 700 (Lc 61.2, the 16px/700
             tier) and a WHITE one nested in it goes back to 400 (Lc 91.8).
  TEXT       signal TEXT takes the ANSI normal tier from build/cosmic.py, as worksafe/vscode/ does:
             §3's values are grounds and marks, and DESTRUCTIVE on WHITE is Lc 68.1.
  TOKENS     the code colouring is the one worksafe/vscode/ chose (§0c): keywords and tags BLACK and
             bold, comments DARK and italic, literals ACCENT, functions SELECT.
  DECLUTTER  §0's larger half -- motion and blur -- is a CSS snippet beside the theme, not inside it, so
             it is a switch (install.sh --no-declutter) and works under any theme. It names no colour.

    python3 build/obsidian.py              check every value, pair and adjacency in the committed theme
    python3 build/obsidian.py --derive     the ramp, and the roles it may name
    python3 build/obsidian.py --write      regenerate the theme and the declutter snippet
    python3 build/obsidian.py --coverage   the installed Obsidian's variables against the theme (a report)
    python3 build/obsidian.py --screen P   what a running Obsidian actually paints, read over its
                                           DevTools port P (a report; README_OBSIDIAN.md says how)
"""
import glob, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca, cosmic as C

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OBS = os.path.join(ROOT, 'worksafe', 'obsidian')
THEME_DIR = os.path.join(OBS, 'Remainder')
THEME = os.path.join(THEME_DIR, 'theme.css')
MANIFEST = os.path.join(THEME_DIR, 'manifest.json')
SNIPPET = os.path.join(OBS, 'remainder-declutter.css')
SETTINGS = [os.path.join(OBS, 'appearance.json')]
INSTALLER = os.path.join(OBS, 'install.sh')

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
FLOOR = PAL['surface_floor_dE']
_T = C.terminal()


# --- 1. the roles ----------------------------------------------------------------------------------
class R(str):
    """A kit role. The theme writes it as var(--rm-NAME); `none` is written as transparent."""
    def css(self):
        return 'transparent' if self == 'none' else f'var(--rm-{self})'


W, L, D, B = R('white'), R('light'), R('dark'), R('black')
A, S, CU = R('accent'), R('select'), R('cursor')
OK_, WN, DS = R('success'), R('warning'), R('destructive')
LL, LD = R('legend-light'), R('legend-dark')
RED, GREEN, YELLOW = R('red'), R('green'), R('yellow')
NONE = R('none')

# Every value the theme may define, and where it comes from. Nothing else may appear in the file.
ROLES = {
    'white': PAL['neutrals']['WHITE'], 'light': PAL['neutrals']['LIGHT'],
    'dark': PAL['neutrals']['DARK'], 'black': PAL['neutrals']['BLACK'],
    'accent': PAL['chrome']['ACCENT'], 'select': PAL['chrome']['SELECT'], 'cursor': PAL['chrome']['CURSOR'],
    'success': C.SEMANTIC['SUCCESS'], 'warning': C.SEMANTIC['WARNING'], 'destructive': C.SEMANTIC['DESTRUCTIVE'],
    'legend-light': '#FFFFFF', 'legend-dark': '#000000',
    # signal TEXT, from build/cosmic.py's ANSI normal tier -- the same values worksafe/vscode/ uses for it
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


# --- 2. the ramp -----------------------------------------------------------------------------------
# Obsidian's own neutral ramp, read out of app.css in the installed obsidian.asar and recorded with its
# date, as build/firefox.py records Firefox's: `.theme-light { --color-base-00 ... --color-base-100 }`,
# 1.13.7, 2026-09-25. Twelve slots where §2 has four; each is SNAPPED to the nearest kit neutral by
# lightness, so a slot the role table does not reach still lands on the kit's ladder.
OBS_RAMP = {'00': '#ffffff', '05': '#fcfcfc', '10': '#fafafa', '20': '#f6f6f6', '25': '#efefef',
            '30': '#e4e4e4', '35': '#dadada', '40': '#bdbdbd', '50': '#ababab', '60': '#707070',
            '70': '#5c5c5c', '100': '#222222'}
LADDER = ['white', 'light', 'dark', 'black']


def ramp():
    """[(slot, platform hex, kit role)], lightest first."""
    out = []
    for slot, hx in OBS_RAMP.items():
        Lx = ok.lch(hx)[0]
        out.append((slot, hx, min(LADDER, key=lambda r: abs(ok.lch(ROLES[r])[0] - Lx))))
    return out


# --- 3. the role table -----------------------------------------------------------------------------
# Every variable the theme decides, with its reason where the reason is not the variable's name. A value
# is a role (written var(--rm-...)) or a literal that carries no colour. Declared on
# `body.theme-light, body.theme-dark`: one specificity step over the platform's own `.theme-light`, and
# on the dark class as well, because §2 is a light palette and a vault switched to dark mode should still
# get the kit rather than half of it (the installer also selects light mode).
MONTSERRAT, HACK = '"Montserrat"', '"Hack"'
VARS = [
    ('§5: the type. The faces go in the theme\'s own slots, so a face the user picks in Settings still wins.', [
        ('--font-interface-theme', MONTSERRAT), ('--font-text-theme', MONTSERRAT),
        ('--font-monospace-theme', HACK),
    ]),
    ('§5: the chrome at the size every floor assumes (CHOSEN; see the header). Obsidian ships 12, 13 and 15 px.', [
        ('--font-ui-smaller', '16px'), ('--font-ui-small', '16px'), ('--font-ui-medium', '16px'),
        ('--font-smallest', '1em'), ('--font-smaller', '1em'), ('--font-small', '1em'),
    ]),
    ('§5: two weights, 400 and 700 -- the ones every checker measures against. Montserrat is installed in its '
     'Medium and ExtraBold cuts only, so these render at 500 and 800, the safe direction (AUTHORITY.md §5).', [
        ('--font-thin', '400'), ('--font-extralight', '400'), ('--font-light', '400'),
        ('--font-normal', '400'), ('--font-medium', '400'),
        ('--font-semibold', '700'), ('--font-bold', '700'), ('--font-extrabold', '700'), ('--font-black', '700'),
        ('--bold-modifier', '300'), ('--nav-heading-weight', '700'), ('--nav-heading-weight-hover', '700'),
        ('--nav-tag-weight', '700'), ('--vault-profile-font-weight', '700'), ('--titlebar-text-weight', '700'),
    ]),
    ('§5: every corner square.', [
        (v, '0') for v in ('--radius-s', '--radius-m', '--radius-l', '--radius-xl', '--input-radius', '--button-radius',
                           '--checkbox-radius', '--tab-radius', '--tab-radius-active', '--tab-curve', '--toggle-radius',
                           '--toggle-thumb-radius', '--slider-thumb-radius', '--image-radius', '--callout-radius',
                           '--code-radius', '--menu-radius', '--modal-radius', '--nav-item-radius',
                           '--clickable-icon-radius', '--scrollbar-radius', '--pill-radius', '--tag-radius',
                           '--swatch-radius', '--status-bar-radius', '--metadata-property-radius',
                           '--metadata-property-radius-hover', '--metadata-property-radius-focus',
                           '--footnote-radius', '--bases-cards-radius', '--bases-embed-border-radius',
                           '--bases-table-container-border-radius', '--bases-table-cell-radius-active',
                           '--bases-table-cell-radius-focus', '--table-selection-border-radius',
                           '--list-bullet-radius', '--nav-tag-radius', '--vault-profile-radius',
                           '--search-input-radius', '--embed-action-radius', '--tab-switcher-preview-radius',
                           '--canvas-controls-radius')
    ]),
    ('The grounds Obsidian frosts. Removing the frost is the declutter snippet\'s job (§0); what shows through '
     'once it is gone is an authored value.', [
        ('--blur-background', L), ('--raised-background', L), ('--workspace-background-translucent', W),
        ('--embed-actions-background', W, 'the buttons that float on an embed'),
    ]),
    ('The ramp (§2), snapped: the backstop under everything below.', None),     # filled from ramp()
    ('§3 reserves #FFFFFF and #000000; these two are the ramp\'s endpoints, which Obsidian spells white and black.', [
        ('--mono-0', W), ('--mono-100', B),
    ]),
    ('Opacity is a blend too: an icon at 0.85 over its ground is a value nobody authored.', [
        ('--icon-opacity', '1'), ('--icon-opacity-hover', '1'), ('--icon-opacity-active', '1'),
        ('--link-unresolved-opacity', '1'), ('--toggle-thumb-opacity-active', '1'),
        ('--slider-thumb-opacity-active', '1'),
    ]),
    ('Surfaces. WHITE is the field -- the note, fields, lists -- and LIGHT the panels around it (§2). A hover is '
     'the other tone: LIGHT on the field here, WHITE on a panel (the panel scope below).', [
        ('--background-primary', W), ('--background-primary-alt', W, 'code blocks and embeds: the face carries them, not a ground'),
        ('--background-secondary', L), ('--background-secondary-alt', L),
        ('--background-modifier-hover', L, 'a fill under text that keeps its colour: BLACK on LIGHT, Lc 61.2 (HIGHLIGHTS)'),
        ('--background-modifier-active-hover', L),
        ('--background-modifier-form-field', W), ('--background-modifier-form-field-hover', W),
        ('--background-modifier-message', B, 'notices and tooltips: WHITE on BLACK, Lc -92.3'),
        ('--background-modifier-error', DS), ('--background-modifier-error-hover', DS),
        ('--background-modifier-warning', WN), ('--background-modifier-warning-hover', WN),
        ('--background-modifier-success', OK_),
        ('--interactive-normal', L, 'a button on the field is LIGHT, carrying BLACK at 700 (§2)'),
        ('--interactive-hover', S, 'hovered, it is SELECT carrying WHITE, as in worksafe/firefox/'),
        ('--interactive-accent', A), ('--interactive-accent-hover', S),
        ('--color-accent', A), ('--color-accent-1', A), ('--color-accent-2', S),
        ('--modal-background', W), ('--modal-sidebar-background', W), ('--settings-background', L),
        ('--setting-items-background', W, 'a group of settings is a WHITE card on the LIGHT page'),
        ('--prompt-background', W), ('--suggestion-background', W), ('--search-result-background', W),
        ('--menu-background', L, 'a menu is a LIGHT frame and its rows are WHITE (worksafe/firefox/)'),
        ('--ribbon-background', L), ('--ribbon-background-collapsed', L), ('--status-bar-background', L),
        ('--tab-container-background', L), ('--tab-background-active', W, 'the active tab is the visible edge of the field below it'),
        ('--tab-switcher-background', L), ('--titlebar-background', L), ('--titlebar-background-focused', A),
        ('--file-header-background', W), ('--file-header-background-focused', W),
        ('--canvas-background', W), ('--canvas-dot-pattern', L), ('--canvas-color', L),
        ('--pdf-background', W), ('--pdf-page-background', W), ('--pdf-sidebar-background', W),
        ('--drag-item-background', W), ('--drag-ghost-background', B), ('--drag-ghost-text-color', W),
        ('--flair-background', L), ('--dropdown-background', L), ('--dropdown-background-hover', S),
        ('--lightbox-background', B), ('--lightbox-titlebar-color', W),
    ]),
    ('Text.', [
        ('--text-normal', B), ('--text-muted', D, 'DARK on WHITE is Lc 79.0; on a panel it is BLACK (the panel scope)'),
        ('--text-faint', D), ('--text-on-accent', W), ('--text-on-accent-inverted', B),
        ('--text-accent', A), ('--text-accent-hover', S),
        ('--text-error', RED, 'error TEXT takes the ANSI normal red: DESTRUCTIVE on WHITE is Lc 68.1'),
        ('--text-warning', YELLOW, 'warning text: the ANSI normal yellow, at its gamut cap'),
        ('--text-success', GREEN),
        ('--text-selection', L, 'CodeMirror paints the selection BEHIND text that keeps its colour (HIGHLIGHTS)'),
        ('--text-highlight-bg', L, '==marked== text: LIGHT, and the rule block sets it 700'),
        ('--highlight-mix-blend-mode', 'normal'),
        ('--caret-color', CU, 'the caret (§2): Lc 60.7 on WHITE'),
    ]),
    ('Borders: there are none. §5 has no line thinner than the rule, so where Obsidian drew a hairline the tone '
     'changes instead. The outline of a control is not a boundary between surfaces -- it is the control\'s own '
     'glyph, like a checkbox\'s box -- and takes BLACK, as in worksafe/vscode/; focus takes ACCENT.', [
        ('--background-modifier-border', NONE), ('--background-modifier-border-hover', NONE),
        ('--background-modifier-border-focus', A),
        ('--divider-color', NONE), ('--divider-color-hover', A, 'the resize handle, while it is dragged: a mark'),
        ('--tab-outline-color', NONE), ('--tab-divider-color', NONE), ('--titlebar-border-color', NONE),
        ('--status-bar-border-color', NONE), ('--modal-border-color', NONE), ('--prompt-border-color', NONE),
        ('--menu-border-color', NONE), ('--metadata-border-color', NONE), ('--metadata-divider-color', NONE),
        ('--footnote-divider-color', NONE), ('--setting-items-border-color', NONE),
        ('--code-border-color', NONE), ('--table-border-color', NONE), ('--table-header-border-color', NONE),
        ('--table-add-button-border-color', NONE), ('--bases-embed-border-color', NONE),
        ('--pill-border-color', B), ('--pill-border-color-hover', A),
        ('--input-shadow', 'inset 0 0 0 1px {black}'), ('--input-shadow-hover', 'inset 0 0 0 1px {black}'),
        ('--swatch-shadow', 'inset 0 0 0 1px {black}'),
        ('--bases-cards-shadow', 'none'), ('--bases-cards-shadow-hover', 'none'),
        ('--embed-block-shadow-hover', 'none'),
        ('--hr-color', L, 'a thematic break is a change of field tone, 4 px of LIGHT (§5)'), ('--hr-thickness', '4px'),
        ('--blockquote-border-color', B, 'the quote bar, at the width of §5\'s mark'), ('--blockquote-border-thickness', '4px'),
        ('--embed-border-start', '4px solid {accent}'),
        ('--indentation-guide-color', NONE, '§5: indentation is read from the indent'),
        ('--indentation-guide-color-active', NONE),
    ]),
    ('Icons are marks.', [
        ('--icon-color', B), ('--icon-color-hover', B), ('--icon-color-focused', B),
        ('--icon-color-active', A, 'a toggle that is on: an ACCENT glyph'),
        ('--collapse-icon-color', D), ('--collapse-icon-color-collapsed', A),
        ('--nav-collapse-icon-color', B), ('--nav-collapse-icon-color-collapsed', B),
        ('--search-icon-color', D), ('--search-clear-button-color', D),
        ('--embed-action-color', B),
    ]),
    ('The file list and the other lists on a panel: BLACK at 700 on LIGHT, the current file SELECT carrying WHITE.', [
        ('--nav-item-color', B), ('--nav-item-color-hover', B), ('--nav-item-color-active', W),
        ('--nav-item-color-selected', W), ('--nav-item-color-highlighted', A),
        ('--nav-item-background-hover', W), ('--nav-item-background-active', S), ('--nav-item-background-selected', S),
        ('--nav-heading-color', B), ('--nav-heading-color-hover', B), ('--nav-heading-color-collapsed', B),
        ('--nav-heading-color-collapsed-hover', B),
        ('--nav-tag-color', B), ('--nav-tag-color-hover', B), ('--nav-tag-color-active', W),
        ('--vault-profile-color', B), ('--vault-profile-color-hover', B),
        ('--status-bar-text-color', B),
    ]),
    ('The titlebar and the tabs. LIGHT strips carry BLACK at 700; the key window\'s top strip is ACCENT carrying '
     'WHITE (the titlebar scope); the active tab is WHITE carrying BLACK at 400.', [
        ('--titlebar-text-color', B), ('--titlebar-text-color-focused', W),
        ('--tab-text-color', B), ('--tab-text-color-active', B), ('--tab-text-color-focused', B),
        ('--tab-text-color-focused-active', B), ('--tab-text-color-focused-active-current', B),
        ('--tab-text-color-focused-highlighted', B),
    ]),
    ('Links route to ACCENT (§3), and keep the underline. An unresolved link is DARK, dashed.', [
        ('--link-color', A), ('--link-color-hover', S), ('--link-external-color', A),
        ('--link-external-color-hover', S), ('--link-unresolved-color', D),
        ('--link-unresolved-decoration-color', D), ('--link-unresolved-decoration-style', 'dashed'),
        ('--tag-color', A), ('--tag-color-hover', S), ('--tag-background', NONE),
        ('--tag-background-hover', NONE), ('--tag-border-color', NONE), ('--tag-border-color-hover', NONE),
        ('--tag-padding-x', '0', 'a tag has no pill behind it, so the pill\'s padding reads as stray space'),
        ('--tag-padding-y', '0'),
    ]),
    ('Controls. A checkbox is a BLACK box; ticked, an ACCENT one with a WHITE tick. A toggle that is on is ACCENT (§2).', [
        ('--checkbox-color', A), ('--checkbox-color-hover', S), ('--checkbox-marker-color', W),
        ('--checkbox-border-color', B), ('--checkbox-border-color-hover', A), ('--checklist-done-color', D),
        ('--toggle-thumb-color', W), ('--slider-thumb-background', W), ('--slider-thumb-background-hover', W),
        ('--slider-thumb-border-color', B), ('--slider-track-background', L), ('--slider-fill-background', A),
        ('--slider-thumb-border-width', '1px'),
        ('--input-placeholder-color', D), ('--input-date-separator', D),
        ('--table-drag-handle-color', D), ('--table-drag-handle-color-active', W),
        ('--table-drag-handle-background-active', A), ('--table-selection', L),
        ('--table-selection-border-color', A), ('--table-add-button-background', NONE),
        ('--scrollbar-bg', NONE), ('--scrollbar-thumb-bg', L), ('--scrollbar-active-thumb-bg', D),
    ]),
    ('The note.', [
        ('--heading-formatting', D), ('--list-marker-color', D), ('--list-marker-color-hover', B),
        ('--list-marker-color-collapsed', A), ('--blockquote-color', 'inherit'),
        ('--table-header-background', L, 'the header row: LIGHT carrying BLACK at 700'),
        ('--table-header-color', B), ('--table-row-background-hover', NONE),
        ('--metadata-label-text-color', D), ('--metadata-label-text-color-hover', B),
        ('--metadata-input-text-color', B),
        ('--metadata-property-background-hover', NONE, 'no fill: on LIGHT an ACCENT tag measured Lc 44.8'),
        ('--metadata-property-background-active', W), ('--metadata-label-background-active', L),
        ('--metadata-input-background-active', W, 'a field: the caret needs WHITE (§2)'),
        ('--metadata-property-box-shadow-hover', 'none'),
        ('--pill-color', B), ('--pill-color-hover', B), ('--pill-color-remove', D),
        ('--pill-color-remove-hover', A), ('--pill-background', NONE), ('--pill-background-hover', NONE),
        ('--footnote-id-color', D), ('--footnote-id-color-no-occurrences', D),
        ('--footnote-input-background-active', W),
        ('--code-bracket-background', L),
    ]),
    ('The code colouring (§0c, CHOSEN): the scheme worksafe/vscode/ uses, by tone and geometry.', [
        ('--code-background', W), ('--code-normal', B), ('--code-comment', D, 'italic (the rule block)'),
        ('--code-keyword', B, 'bold'), ('--code-tag', B, 'bold'), ('--code-operator', B),
        ('--code-punctuation', B), ('--code-property', B, 'variables and parameters are the base text'),
        ('--code-string', A), ('--code-value', A), ('--code-important', A),
        ('--code-function', S, 'functions and methods: SELECT, Lc 85.8 on WHITE'),
    ]),
    ('Callouts. §3\'s three where their meaning is, and nothing else: a callout that is not an error, a '
     'warning or a success is furniture and carries its meaning in its title.', [
        ('--callout-default', L), ('--callout-info', L), ('--callout-todo', L), ('--callout-summary', L),
        ('--callout-important', L), ('--callout-tip', L), ('--callout-question', L),
        ('--callout-example', L), ('--callout-quote', L),
        ('--callout-bug', DS), ('--callout-error', DS), ('--callout-fail', DS),
        ('--callout-warning', WN), ('--callout-success', OK_),
        ('--callout-title-color', B), ('--callout-border-width', '0px'), ('--callout-blend-mode', 'normal'),
        ('--callout-padding', '0 4px 4px 4px'), ('--callout-title-padding', '4px 8px'),
        ('--callout-content-padding', '0 12px'), ('--callout-content-background', W),
    ]),
    ('The graph is drawn from these at load. Its tag and attachment colours are information, not chrome (§3\'s '
     'own test: remove them and a node is harder to find), and are left to the platform with the canvas labels '
     'and the sync avatars.', [
        ('--graph-line', L), ('--graph-node', D), ('--graph-node-unresolved', L),
        ('--graph-node-focused', A), ('--graph-text', B),
    ]),
    ('Bases.', [
        ('--bases-table-header-background', L), ('--bases-table-header-background-hover', W),
        ('--bases-table-header-color', B), ('--bases-table-group-background', L),
        ('--bases-table-summary-background', W), ('--bases-table-summary-background-hover', L),
        ('--bases-table-cell-background-active', W), ('--bases-table-cell-background-disabled', L),
        ('--bases-table-cell-background-selected', L), ('--bases-table-row-background-hover', L),
        ('--bases-cards-background', W), ('--bases-cards-container-background', L),
        ('--bases-cards-cover-background', L), ('--bases-group-heading-property-color', D),
        ('--bases-filter-input-background', W),
    ]),
]

# Variables re-declared inside a region, because a custom property is computed where it is declared: a
# value set on body and read through var() further down carries body's answer, whatever the region
# redefines. So a region that changes a ground re-declares everything that reads it.
PANELS = ('.workspace-split.mod-sidedock', '.workspace-ribbon', '.status-bar', '.workspace-tab-header-container',
          '.sidebar-toggle-button', '.titlebar', '.vertical-tab-content', '.menu', '.callout-title',
          '.modal-sidebar-inner', '.workspace-sidedock-vault-profile')
FIELDS = ('.search-result-file-match', '.menu-item', '.setting-items', '.vertical-tab-header',
          'input', 'textarea', '.search-input-container', '.suggestion-container', '.prompt')
KEY = ('body.is-focused .workspace-tabs.mod-top > .workspace-tab-header-container',
       'body.is-focused .sidebar-toggle-button', 'body.is-focused .titlebar')
KEY_TAB = ('body.is-focused .workspace-tabs.mod-top > .workspace-tab-header-container .workspace-tab-header.is-active',)
SCOPES = [
    ('panel', PANELS, None,
     'A panel is LIGHT, so what the field scope makes LIGHT it makes WHITE, and its read text is BLACK at 700.', [
         ('--background-modifier-hover', W), ('--background-modifier-active-hover', W),
         ('--interactive-normal', W, 'a button on a panel is WHITE, as in worksafe/firefox/'),
         ('--text-muted', B), ('--text-faint', B), ('--nav-item-background-hover', W),
         ('--scrollbar-thumb-bg', D), ('--scrollbar-active-thumb-bg', B),
     ]),
    ('field', FIELDS, 'panel',
     'A field nested in a panel goes back to the field\'s values.', [
         ('--background-modifier-hover', L), ('--background-modifier-active-hover', L),
         ('--interactive-normal', L), ('--text-muted', D), ('--text-faint', D),
         ('--scrollbar-thumb-bg', L), ('--scrollbar-active-thumb-bg', D),
     ]),
    ('key', KEY, 'panel',
     'The key window\'s titlebar (§2): ACCENT carrying WHITE. A hovered tab or button on it is BLACK, not '
     'SELECT, which is dE 11.8 from ACCENT and would not read as a separate surface (worksafe/firefox/).', [
         ('--tab-container-background', A), ('--titlebar-background', A),
         ('--tab-text-color-focused', W), ('--tab-text-color-focused-highlighted', W),
         ('--icon-color', W), ('--icon-color-hover', W), ('--icon-color-focused', W),
         ('--background-modifier-hover', B), ('--background-modifier-active-hover', B),
     ]),
    ('key tab', KEY_TAB, 'key',
     'The active tab on the key strip is the field\'s edge, WHITE, so its glyphs are BLACK again.', [
         ('--icon-color', B), ('--icon-color-hover', B), ('--icon-color-focused', B),
         ('--background-modifier-hover', L), ('--background-modifier-active-hover', L),
     ]),
]

# Rules for what no variable reaches. Values are written with {role} placeholders; nothing else may carry a
# colour. !important only where the platform's own selector outranks a theme's.
RULES = [
    ('The page itself.', 'body.theme-light, body.theme-dark', [('color-scheme', 'light')]),
    ('Weight follows the ground (§2): every panel carries BLACK at 700, Lc 61.2.',
     ', '.join(PANELS), [('font-weight', '700')]),
    ('...and every field nested in one goes back to 400, Lc 91.8.',
     ', '.join(FIELDS), [('font-weight', '400')]),
    ('The key window\'s strip carries WHITE at 400: Lc -78.5, over the body tier.',
     ', '.join(KEY), [('font-weight', '400')]),
    ('The active tab is WHITE: 400.',
     '.workspace-tab-header.is-active', [('font-weight', '400')]),
    ('The window buttons sit on the titlebar, so they take its ground in both states.',
     '.is-hidden-frameless:not(.is-fullscreen) .titlebar-button-container.mod-right',
     [('background-color', 'var(--titlebar-background)')]),
    ('', 'body.is-focused.is-hidden-frameless:not(.is-fullscreen) .titlebar-button-container.mod-right',
     [('background-color', '{accent}')]),
    ('The window buttons\' glyphs follow the titlebar\'s text.',
     '.titlebar-button', [('color', 'var(--icon-color)')]),
    ('§3: closing a window is the one destructive act in the titlebar, and its legend is #FFFFFF.',
     '.mod-linux .titlebar-button.mod-close:hover', [('color', '{legend-light}')]),
    ('The current tab of a sidebar strip is the panel below it: LIGHT, in both states.',
     '.mod-sidedock .workspace-tab-header-container .workspace-tab-header.is-active',
     [('background-color', '{light}'), ('box-shadow', 'none'), ('--icon-color', '{black}'),
      ('--icon-color-hover', '{black}'), ('--icon-color-focused', '{black}')]),
    ('The active tab\'s ears: Obsidian draws them with a shadow from --tab-curve, which is 0.',
     '.workspace-tab-header-container .workspace-tab-header::before, .workspace-tab-header-container .workspace-tab-header::after',
     [('display', 'none')]),
    ('Hovered tabs on a LIGHT strip are WHITE, like every hover on a panel.',
     '.workspace-tab-header-container .workspace-tab-header:not(.is-active):hover .workspace-tab-header-inner',
     [('background-color', 'var(--background-modifier-hover)')]),
    ('The selected row is SELECT carrying WHITE (§2) -- in the palette and the quick switcher, and in menus.',
     '.suggestion-item.is-selected, .menu-item.selected:not(.is-disabled):not(.is-label)',
     [('background-color', '{select}'), ('color', '{white}'), ('--text-muted', '{white}'),
      ('--text-faint', '{white}'), ('--icon-color', '{white}'), ('--text-accent', '{white}'),
      ('--interactive-accent', '{white}')]),
    ('', '.suggestion-item.is-selected *, .menu-item.selected:not(.is-disabled):not(.is-label) *',
     [('color', 'inherit')]),
    ('Menu rows are the field, on the menu\'s LIGHT frame.',
     '.menu-item:not(.is-label)', [('background-color', '{white}')]),
    ('', '.menu-separator', [('border-color', 'transparent'), ('margin', '4px 0')]),
    ('The current file, the selection, and a row being dragged: SELECT carrying WHITE, glyphs included.',
     '.tree-item-self.is-active .tree-item-icon, .tree-item-self.is-selected .tree-item-icon, '
     '.tree-item-self.is-active .collapse-icon, .tree-item-self.is-selected .collapse-icon',
     [('color', '{white}')]),
    ('A button hovered is SELECT carrying WHITE; the primary one hovered is SELECT too (worksafe/firefox/).',
     'button:not(.clickable-icon):not(.mod-cta):not(.mod-warning):hover',
     [('--text-color', '{white}'), ('color', '{white}')]),
    ('§5: every corner square, the radio button\'s included; Obsidian writes its circle as a literal.',
     'input[type="radio"]', [('border-radius', '0')]),
    ('A destructive button is §3\'s own ground with the light legend, never a tint of it.',
     'button.mod-destructive, button.mod-warning, button.mod-destructive.mod-cta',
     [('background-color', '{destructive}'), ('--text-color', '{legend-light}'), ('color', '{legend-light}')]),
    ('A dropdown is a button: its arrow was a data URI stroked #000, which §3 reserves; it is drawn here from '
     'two gradients in the label\'s own colour.',
     '.dropdown',
     [('background-image', 'linear-gradient(45deg, transparent 50%, {black} 50%), '
                           'linear-gradient(135deg, {black} 50%, transparent 50%)'),
      ('background-position', 'calc(100% - 15px) 55%, calc(100% - 10px) 55%'),
      ('background-size', '5px 5px, 5px 5px'), ('background-repeat', 'no-repeat'),
      ('background-blend-mode', 'normal')]),
    ('', '.dropdown:hover',
     [('color', '{white}'),
      ('background-image', 'linear-gradient(45deg, transparent 50%, {white} 50%), '
                           'linear-gradient(135deg, {white} 50%, transparent 50%)')]),
    ('A toggle: LIGHT with a WHITE thumb and the control\'s BLACK outline; on, ACCENT (§2).',
     '.checkbox-container',
     [('background-color', '{light}'), ('box-shadow', 'inset 0 0 0 1px {black}')]),
    ('', '.checkbox-container.is-enabled', [('background-color', '{accent}'), ('box-shadow', 'none')]),
    ('Notices and tooltips: WHITE on BLACK. Obsidian writes their text as the literal #FAFAFA.',
     '.notice, .tooltip, .cm-tooltip.cm-tooltip-docstring, .cm-tooltip.cm-completionInfo',
     [('color', '{white}')]),
    ('', '.tooltip.mod-error', [('color', '{legend-light}')]),
    ('==Marked== text sits on LIGHT, so it is set 700 -- the pair §2 authors, Lc 61.2.',
     '.cm-highlight, .markdown-rendered mark, .search-result-file-matched-text',
     [('font-weight', '700'), ('color', '{black}')]),
    ('Text selected outside the editor can carry its own colour, so it is §2\'s selection.',
     '.markdown-rendered ::selection, .markdown-preview-view ::selection, input::selection, textarea::selection',
     [('background-color', '{select}'), ('color', '{white}')]),
    ('The code colouring\'s geometry.', '.token.keyword, .cm-keyword, .token.tag, .cm-tag',
     [('font-weight', '700')]),
    ('', '.token.comment, .token.prolog, .token.doctype, .token.cdata, .cm-comment', [('font-style', 'italic')]),
    ('A diff is content, and its convention is realized: inserted green, deleted red, at the ANSI text tier.',
     '.token.inserted', [('color', '{green}')]),
    ('', '.token.deleted', [('color', '{red}')]),
    ('Callouts: a frame in the callout\'s colour, the title on it, and the content on a WHITE inset. The title '
     'carries BLACK on LIGHT, and §3\'s legend on a semantic frame.',
     '.callout', [('background-color', 'var(--callout-color)'), ('mix-blend-mode', 'normal')]),
    ('', '.callout-title', [('background-color', 'var(--callout-color)'), ('color', 'var(--callout-title-color)')]),
    ('', '.callout-icon .svg-icon, .callout-fold .svg-icon', [('color', 'var(--callout-title-color)')]),
    ('', '.callout-content', [('background-color', '{white}'), ('padding-block', '4px')]),
    ('', '.callout[data-callout="warning"], .callout[data-callout="caution"], .callout[data-callout="attention"]',
     [('--callout-title-color', '{legend-dark}')]),
    ('', '.callout[data-callout="danger"], .callout[data-callout="error"], .callout[data-callout="bug"], '
         '.callout[data-callout="failure"], .callout[data-callout="fail"], .callout[data-callout="missing"], '
         '.callout[data-callout="success"], .callout[data-callout="check"], .callout[data-callout="done"]',
     [('--callout-title-color', '{legend-light}')]),
    ('A button carries BLACK on LIGHT on the field, so its label is 700; on a panel it is WHITE, where 700 '
     'costs nothing -- weight is safe in one direction only (AUTHORITY.md §5).',
     'button:not(.clickable-icon)', [('font-weight', '700')]),
    ('A disabled control is DARK (§2), not faded: an icon at 0.4 over its ground is a blend.',
     ".clickable-icon[aria-disabled='true']", [('opacity', '1'), ('color', '{dark}')]),
    ('A key cap is WHITE on DARK, Lc -81.7, as in worksafe/vscode/; on the selected row, WHITE on BLACK.',
     'kbd', [('background-color', '{dark}'), ('color', '{white}')]),
    ('', '.suggestion-item.is-selected kbd, .menu-item.selected kbd', [('background-color', '{black}')]),
    ('A file\'s type, beside its name: at the chrome\'s size and in its case, where Obsidian set it 9 px and '
     'upper case.', '.nav-file-tag', [('font-size', 'var(--font-ui-smaller)'), ('text-transform', 'none')]),
    ('Settings: the page is a LIGHT panel and each group of settings a WHITE card on it (§2\'s alternation); '
     'the list of pages beside it is WHITE. Obsidian paints the page WHITE, which put the cards on their own ground.',
     '.vertical-tab-content', [('background-color', 'var(--settings-background)')]),
    ('The page\'s title strip fades into the page with a blurred shadow in the page\'s own colour: a gradient of '
     'values nobody authored. It is the page\'s ground, so it needs no edge at all.',
     '.setting-page-titlebar', [('box-shadow', 'none')]),
    ('A popout window\'s title is its titlebar\'s text at full strength, not 0.85 of it.',
     '.titlebar-text', [('opacity', '1')]),
    ('The status bar floats over the field; it is a panel with no rule of its own.',
     '.status-bar', [('border', '0')]),
]

# The larger half (§0), shipped as a CSS snippet beside the theme rather than inside it, so that it is a
# switch -- Settings > Appearance > CSS snippets, or install.sh --no-declutter -- and so that it works under any
# theme. It carries no colour at all, and the checker proves it.
DECLUTTER_VARS = [
    ('Motion: the transitions Obsidian drives from its own durations.', [
        ('--anim-duration-superfast', '0ms'), ('--anim-duration-fast', '0ms'),
        ('--anim-duration-moderate', '0ms'), ('--anim-duration-slow', '0ms'),
    ]),
    ('Blur: Obsidian frosts its menus, its prompts and its floating toolbars with backdrop-filter.', [
        ('--blur-s', 'none'), ('--blur-m', 'none'), ('--blur-l', 'none'), ('--raised-blur', 'none'),
        ('--embed-actions-blur', 'none'), ('--menu-backdrop-filter', 'none'),
        ('--prompt-backdrop-filter', 'none'), ('--suggestion-backdrop-filter', 'none'),
        ('--blur-brightness', '1'), ('--blur-saturation', '1'),
    ]),
]
DECLUTTER_RULES = [
    ('Motion: the durations Obsidian writes as literals, which are most of them (66 of 85 on 1.13.7), zeroed. '
     '0.01 ms rather than 0, so every transitionend and animationend still fires and nothing waiting on one is '
     'stranded; one iteration, so a spinner stops rather than spins. The caret stops blinking with the rest, as '
     'worksafe/vscode/ sets it solid.',
     '*, *::before, *::after', [
         ('transition-duration', '0.01ms !important'), ('transition-delay', '0s !important'),
         ('animation-duration', '0.01ms !important'), ('animation-delay', '0s !important'),
         ('animation-iteration-count', '1 !important'), ('scroll-behavior', 'auto !important')]),
    ('Blur: anything else that frosts what is behind it -- a catch-all under the variables above, which reach '
     'most of it.', '*', [('backdrop-filter', 'none !important')]),
]


# Left to the platform on purpose, with the reason -- for --coverage, which would otherwise list them.
LEFT_UNSET = {
    '--background-modifier-cover': 'the modal scrim: a real shadow (§4), as in worksafe/firefox/',
    '--background-modifier-box-shadow': 'a real shadow (§4)',
    '--canvas-color-1': 'a label the user assigned a canvas card: information (§3\'s test)',
    '--canvas-color-2': 'the same', '--canvas-color-3': 'the same', '--canvas-color-4': 'the same',
    '--canvas-color-5': 'the same', '--canvas-color-6': 'the same',
    '--graph-node-tag': 'a node type in the graph: information', '--graph-node-attachment': 'the same',
    '--sync-avatar-color-1': 'a collaborator\'s colour: information', '--sync-avatar-color-2': 'the same',
    '--sync-avatar-color-3': 'the same', '--sync-avatar-color-4': 'the same', '--sync-avatar-color-5': 'the same',
    '--sync-avatar-color-6': 'the same', '--sync-avatar-color-7': 'the same', '--sync-avatar-color-8': 'the same',
    '--sync-avatar-color-current-user': 'transparent by default',
    '--color-red': 'the content palette the three above resolve through', '--color-orange': 'the same',
    '--color-yellow': 'the same', '--color-green': 'the same', '--color-cyan': 'the same',
    '--color-blue': 'the same', '--color-purple': 'the same', '--color-pink': 'the same',
    '--accent-h': 'the accent\'s parts; every variable Obsidian derives from them is set above',
    '--accent-s': 'the same', '--accent-l': 'the same',
}
# Information, not chrome, and left to the platform on purpose: remove one and the thing it marks is harder to
# find (§3's test). A pole among these is content taking a pole, which §0a permits.
CONTENT = ({f'--canvas-color-{i}' for i in range(1, 7)} | {f'--sync-avatar-color-{i}' for i in range(1, 9)}
           | {'--graph-node-tag', '--graph-node-attachment'}
           | {f'--color-{h}' for h in ('red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'pink')})
# §4 permits real shadows and the scrim; those two may resolve to a blend.
BLENDS_PERMITTED = {'--background-modifier-cover', '--background-modifier-box-shadow'}


# --- 4. the platform's variables, recorded ---------------------------------------------------------
# Every declaration a colour variable needs to resolve, read off `body { }` and `.theme-light { }` in
# app.css inside the installed obsidian.asar: the Arch `obsidian` package 1.13.7, 2026-09-25. 302 of
# Obsidian's 873 body variables take a colour. With this table the gate runs on a machine with no
# Obsidian, and --coverage re-reads the installed build to report what was renamed or added since.
PLATFORM = {
    '--accent-h': '258',
    '--accent-l': '66%',
    '--accent-s': '88%',
    '--background-modifier-active-hover': 'color-mix(in oklch, var(--interactive-accent) 10%, transparent)',
    '--background-modifier-border': 'var(--color-base-30)',
    '--background-modifier-border-focus': 'var(--color-base-40)',
    '--background-modifier-border-hover': 'var(--color-base-35)',
    '--background-modifier-box-shadow': 'rgba(0, 0, 0, 0.1)',
    '--background-modifier-cover': 'rgba(220, 220, 220, 0.4)',
    '--background-modifier-error': 'var(--color-red)',
    '--background-modifier-error-hover': 'var(--color-red)',
    '--background-modifier-form-field': 'var(--color-base-00)',
    '--background-modifier-form-field-hover': 'var(--background-modifier-form-field)',
    '--background-modifier-hover': 'color-mix(in oklch, var(--mono-100) 6.7%, transparent)',
    '--background-modifier-message': 'color-mix(in oklch, black 90%, transparent)',
    '--background-modifier-success': 'var(--color-green)',
    '--background-modifier-warning': 'var(--color-orange)',
    '--background-modifier-warning-hover': 'var(--color-orange)',
    '--background-primary': 'var(--color-base-00)',
    '--background-primary-alt': 'var(--color-base-10)',
    '--background-secondary': 'var(--color-base-20)',
    '--background-secondary-alt': 'var(--color-base-05)',
    '--bases-cards-background': 'var(--background-primary)',
    '--bases-cards-container-background': 'transparent',
    '--bases-cards-cover-background': 'var(--background-primary-alt)',
    '--bases-embed-border-color': 'var(--background-modifier-border)',
    '--bases-filter-input-background': 'var(--background-modifier-form-field)',
    '--bases-group-heading-property-color': 'var(--text-muted)',
    '--bases-table-border-color': 'var(--table-border-color)',
    '--bases-table-cell-background-active': 'var(--background-primary)',
    '--bases-table-cell-background-disabled': 'var(--background-primary-alt)',
    '--bases-table-cell-background-selected': 'var(--table-selection)',
    '--bases-table-group-background': 'var(--background-primary-alt)',
    '--bases-table-header-background': 'var(--background-primary)',
    '--bases-table-header-background-hover': 'var(--background-modifier-hover)',
    '--bases-table-header-color': 'var(--text-muted)',
    '--bases-table-row-background-hover': 'var(--table-row-background-hover)',
    '--bases-table-summary-background': 'var(--background-primary)',
    '--bases-table-summary-background-hover': 'var(--background-modifier-hover)',
    '--blockquote-background-color': 'transparent',
    '--blockquote-border-color': 'var(--interactive-accent)',
    '--callout-bug': 'var(--color-red)',
    '--callout-content-background': 'transparent',
    '--callout-default': 'var(--color-blue)',
    '--callout-error': 'var(--color-red)',
    '--callout-example': 'var(--color-purple)',
    '--callout-fail': 'var(--color-red)',
    '--callout-important': 'var(--color-cyan)',
    '--callout-info': 'var(--color-blue)',
    '--callout-question': 'var(--color-orange)',
    '--callout-quote': '#9e9e9e',
    '--callout-success': 'var(--color-green)',
    '--callout-summary': 'var(--color-cyan)',
    '--callout-tip': 'var(--color-cyan)',
    '--callout-todo': 'var(--color-blue)',
    '--callout-warning': 'var(--color-orange)',
    '--canvas-background': 'var(--background-primary)',
    '--canvas-card-label-color': 'var(--text-faint)',
    '--canvas-color': '#c0c0c0',
    '--canvas-color-1': 'var(--color-red)',
    '--canvas-color-2': 'var(--color-orange)',
    '--canvas-color-3': 'var(--color-yellow)',
    '--canvas-color-4': 'var(--color-green)',
    '--canvas-color-5': 'var(--color-cyan)',
    '--canvas-color-6': 'var(--color-purple)',
    '--canvas-dot-pattern': 'var(--color-base-30)',
    '--caret-color': 'var(--text-normal)',
    '--checkbox-border-color': 'var(--text-faint)',
    '--checkbox-border-color-hover': 'var(--text-muted)',
    '--checkbox-color': 'var(--interactive-accent)',
    '--checkbox-color-hover': 'var(--interactive-accent-hover)',
    '--checkbox-marker-color': 'var(--background-primary)',
    '--checklist-done-color': 'var(--text-muted)',
    '--code-background': 'var(--background-primary-alt)',
    '--code-border-color': 'var(--background-modifier-border)',
    '--code-bracket-background': 'var(--background-modifier-hover)',
    '--code-comment': 'var(--text-faint)',
    '--code-function': 'var(--color-yellow)',
    '--code-important': 'var(--color-orange)',
    '--code-keyword': 'var(--color-pink)',
    '--code-normal': 'var(--text-normal)',
    '--code-operator': 'var(--color-red)',
    '--code-property': 'var(--color-cyan)',
    '--code-punctuation': 'var(--text-muted)',
    '--code-string': 'var(--color-green)',
    '--code-tag': 'var(--color-red)',
    '--code-value': 'var(--color-purple)',
    '--collapse-icon-color': 'var(--text-faint)',
    '--collapse-icon-color-collapsed': 'var(--text-accent)',
    '--color-accent': 'hsl(var(--accent-h), var(--accent-s), var(--accent-l))',
    '--color-accent-1': 'hsl(calc(var(--accent-h) - 1), calc(var(--accent-s) * 1.01), calc(var(--accent-l) * 1.075))',
    '--color-accent-2': 'hsl(calc(var(--accent-h) - 3), calc(var(--accent-s) * 1.02), calc(var(--accent-l) * 1.15))',
    '--color-base-00': '#ffffff',
    '--color-base-05': '#fcfcfc',
    '--color-base-10': '#fafafa',
    '--color-base-100': '#222222',
    '--color-base-20': '#f6f6f6',
    '--color-base-25': '#efefef',
    '--color-base-30': '#e4e4e4',
    '--color-base-35': '#dadada',
    '--color-base-40': '#bdbdbd',
    '--color-base-50': '#ababab',
    '--color-base-60': '#707070',
    '--color-base-70': '#5c5c5c',
    '--color-blue': '#086ddd',
    '--color-cyan': '#00bfbc',
    '--color-green': '#08b94e',
    '--color-orange': '#ec7500',
    '--color-pink': '#d53984',
    '--color-purple': '#7852ee',
    '--color-red': '#e93147',
    '--color-yellow': '#e0ac00',
    '--divider-color': 'var(--background-modifier-border)',
    '--divider-color-hover': 'var(--interactive-accent)',
    '--drag-ghost-background': 'rgba(0, 0, 0, 0.85)',
    '--drag-ghost-text-color': '#fff',
    '--drag-item-background': 'var(--background-primary)',
    '--dropdown-background': 'var(--interactive-normal)',
    '--dropdown-background-hover': 'var(--interactive-hover)',
    '--dropdown-icon-background': 'transparent',
    '--embed-action-color': 'var(--text-normal)',
    '--embed-actions-background': 'color-mix(in srgb, var(--background-primary) 80%, transparent)',
    '--file-header-background': 'var(--background-primary)',
    '--file-header-background-focused': 'var(--background-primary)',
    '--flair-background': 'var(--interactive-normal)',
    '--flair-color': 'var(--text-normal)',
    '--footnote-divider-color': 'var(--metadata-divider-color)',
    '--footnote-divider-color-active': 'var(--metadata-divider-color-focus)',
    '--footnote-id-color': 'var(--text-muted)',
    '--footnote-id-color-no-occurrences': 'var(--text-faint)',
    '--footnote-input-background': 'var(--metadata-input-background)',
    '--footnote-input-background-active': 'var(--metadata-input-background-active)',
    '--graph-line': 'var(--color-base-35, var(--background-modifier-border-focus))',
    '--graph-node': 'var(--text-muted)',
    '--graph-node-attachment': 'var(--color-yellow)',
    '--graph-node-focused': 'var(--text-accent)',
    '--graph-node-tag': 'var(--color-green)',
    '--graph-node-unresolved': 'var(--text-faint)',
    '--graph-text': 'var(--text-normal)',
    '--heading-formatting': 'var(--text-faint)',
    '--hr-color': 'var(--background-modifier-border)',
    '--icon-color': 'var(--text-muted)',
    '--icon-color-active': 'var(--text-accent)',
    '--icon-color-focused': 'var(--text-normal)',
    '--icon-color-hover': 'var(--text-muted)',
    '--indentation-guide-color': 'color-mix(in oklch, var(--mono-100) 12%, transparent)',
    '--indentation-guide-color-active': 'color-mix(in oklch, var(--mono-100) 30%, transparent)',
    '--input-date-separator': 'var(--text-faint)',
    '--input-placeholder-color': 'var(--text-faint)',
    '--interactive-accent': 'var(--color-accent-1)',
    '--interactive-accent-hover': 'var(--color-accent-2)',
    '--interactive-hover': 'var(--color-base-10)',
    '--interactive-normal': 'var(--color-base-00)',
    '--lightbox-background': 'black',
    '--lightbox-titlebar-color': 'white',
    '--link-color': 'var(--text-accent)',
    '--link-color-hover': 'var(--text-accent-hover)',
    '--link-external-color': 'var(--text-accent)',
    '--link-external-color-hover': 'var(--text-accent-hover)',
    '--link-unresolved-color': 'var(--text-accent)',
    '--link-unresolved-decoration-color': 'color-mix(in oklch, var(--interactive-accent) 30%, transparent)',
    '--list-marker-color': 'var(--text-faint)',
    '--list-marker-color-collapsed': 'var(--text-accent)',
    '--list-marker-color-hover': 'var(--text-muted)',
    '--menu-background': 'var(--background-secondary)',
    '--menu-border-color': 'var(--background-modifier-border-hover)',
    '--metadata-background': 'transparent',
    '--metadata-border-color': 'var(--background-modifier-border)',
    '--metadata-divider-color': 'var(--background-modifier-border)',
    '--metadata-divider-color-focus': 'transparent',
    '--metadata-divider-color-hover': 'transparent',
    '--metadata-input-background': 'transparent',
    '--metadata-input-background-active': 'var(--background-modifier-hover)',
    '--metadata-input-background-hover': 'transparent',
    '--metadata-input-text-color': 'var(--text-normal)',
    '--metadata-label-background': 'transparent',
    '--metadata-label-background-active': 'var(--background-modifier-hover)',
    '--metadata-label-background-hover': 'transparent',
    '--metadata-label-text-color': 'var(--text-muted)',
    '--metadata-label-text-color-hover': 'var(--text-muted)',
    '--metadata-property-background': 'transparent',
    '--metadata-property-background-active': 'var(--background-modifier-hover)',
    '--metadata-property-background-hover': 'transparent',
    '--modal-background': 'var(--background-primary)',
    '--modal-border-color': 'var(--color-base-40, var(--background-modifier-border-focus))',
    '--modal-sidebar-background': 'var(--modal-background)',
    '--mono-0': 'white',
    '--mono-100': 'black',
    '--nav-collapse-icon-color': 'var(--collapse-icon-color)',
    '--nav-collapse-icon-color-collapsed': 'var(--text-faint)',
    '--nav-heading-color': 'var(--text-normal)',
    '--nav-heading-color-collapsed': 'var(--text-faint)',
    '--nav-heading-color-collapsed-hover': 'var(--text-muted)',
    '--nav-heading-color-hover': 'var(--text-normal)',
    '--nav-indentation-guide-color': 'var(--indentation-guide-color)',
    '--nav-item-background-active': 'var(--background-modifier-hover)',
    '--nav-item-background-hover': 'var(--background-modifier-hover)',
    '--nav-item-background-selected': 'color-mix(in oklch, var(--color-accent) 15%, transparent)',
    '--nav-item-color': 'var(--text-muted)',
    '--nav-item-color-active': 'var(--text-normal)',
    '--nav-item-color-highlighted': 'var(--text-accent)',
    '--nav-item-color-hover': 'var(--text-normal)',
    '--nav-item-color-selected': 'var(--text-normal)',
    '--nav-tag-background': 'transparent',
    '--nav-tag-color': 'var(--text-faint)',
    '--nav-tag-color-active': 'var(--text-muted)',
    '--nav-tag-color-hover': 'var(--text-muted)',
    '--pdf-background': 'var(--background-primary)',
    '--pdf-page-background': 'var(--background-primary)',
    '--pdf-sidebar-background': 'var(--background-primary)',
    '--pill-background': 'transparent',
    '--pill-background-hover': 'transparent',
    '--pill-border-color': 'var(--background-modifier-border)',
    '--pill-border-color-hover': 'var(--background-modifier-border-hover)',
    '--pill-color': 'var(--text-muted)',
    '--pill-color-hover': 'var(--text-normal)',
    '--pill-color-remove': 'var(--text-faint)',
    '--pill-color-remove-hover': 'var(--text-accent)',
    '--prompt-background': 'var(--background-primary)',
    '--prompt-border-color': 'var(--color-base-40, var(--background-modifier-border-focus))',
    '--ribbon-background': 'var(--background-secondary)',
    '--ribbon-background-collapsed': 'var(--background-primary)',
    '--scrollbar-active-thumb-bg': 'color-mix(in oklch, var(--mono-100) 20%, transparent)',
    '--scrollbar-bg': 'transparent',
    '--scrollbar-thumb-bg': 'color-mix(in oklch, var(--mono-100) 10%, transparent)',
    '--search-clear-button-color': 'var(--text-muted)',
    '--search-icon-color': 'var(--text-muted)',
    '--search-result-background': 'var(--background-primary)',
    '--setting-group-heading-color': 'var(--text-normal)',
    '--setting-items-background': 'var(--background-primary-alt)',
    '--setting-items-border-color': 'var(--background-modifier-border)',
    '--settings-background': 'var(--modal-background)',
    '--slider-fill-background': 'var(--interactive-accent)',
    '--slider-thumb-background': 'white',
    '--slider-thumb-background-hover': 'white',
    '--slider-thumb-border-color': 'var(--background-modifier-border-hover)',
    '--slider-track-background': 'var(--background-modifier-border-hover)',
    '--status-bar-background': 'var(--background-secondary)',
    '--status-bar-border-color': 'var(--divider-color)',
    '--status-bar-text-color': 'var(--text-muted)',
    '--suggestion-background': 'var(--background-primary)',
    '--sync-avatar-color-1': 'var(--color-red)',
    '--sync-avatar-color-2': 'var(--color-orange)',
    '--sync-avatar-color-3': 'var(--color-yellow)',
    '--sync-avatar-color-4': 'var(--color-green)',
    '--sync-avatar-color-5': 'var(--color-cyan)',
    '--sync-avatar-color-6': 'var(--color-blue)',
    '--sync-avatar-color-7': 'var(--color-purple)',
    '--sync-avatar-color-8': 'var(--color-pink)',
    '--sync-avatar-color-current-user': 'transparent',
    '--tab-background-active': 'var(--background-primary)',
    '--tab-container-background': 'var(--background-secondary)',
    '--tab-divider-color': 'var(--background-modifier-border-hover)',
    '--tab-outline-color': 'var(--divider-color)',
    '--tab-switcher-background': 'var(--background-secondary)',
    '--tab-text-color': 'var(--text-faint)',
    '--tab-text-color-active': 'var(--text-muted)',
    '--tab-text-color-focused': 'var(--text-muted)',
    '--tab-text-color-focused-active': 'var(--text-muted)',
    '--tab-text-color-focused-active-current': 'var(--text-normal)',
    '--tab-text-color-focused-highlighted': 'var(--text-accent)',
    '--table-add-button-background': 'transparent',
    '--table-add-button-border-color': 'var(--background-modifier-border)',
    '--table-background': 'transparent',
    '--table-border-color': 'var(--background-modifier-border)',
    '--table-column-alt-background': 'var(--table-background)',
    '--table-drag-handle-background': 'transparent',
    '--table-drag-handle-background-active': 'var(--table-selection-border-color)',
    '--table-drag-handle-color': 'var(--text-faint)',
    '--table-drag-handle-color-active': 'var(--text-on-accent)',
    '--table-header-background': 'var(--table-background)',
    '--table-header-border-color': 'var(--table-border-color)',
    '--table-header-color': 'var(--text-normal)',
    '--table-row-alt-background': 'var(--table-background)',
    '--table-row-alt-background-hover': 'var(--table-background)',
    '--table-row-background-hover': 'var(--table-background)',
    '--table-selection': 'color-mix(in oklch, var(--color-accent) 10%, transparent)',
    '--table-selection-border-color': 'var(--interactive-accent)',
    '--tag-background': 'color-mix(in oklch, var(--interactive-accent) 10%, transparent)',
    '--tag-background-hover': 'color-mix(in oklch, var(--interactive-accent) 20%, transparent)',
    '--tag-border-color': 'color-mix(in oklch, var(--interactive-accent) 15%, transparent)',
    '--tag-border-color-hover': 'color-mix(in oklch, var(--interactive-accent) 15%, transparent)',
    '--tag-color': 'var(--text-accent)',
    '--tag-color-hover': 'var(--text-accent)',
    '--text-accent': 'var(--color-accent)',
    '--text-accent-hover': 'var(--color-accent-2)',
    '--text-error': 'var(--color-red)',
    '--text-faint': 'var(--color-base-50)',
    '--text-highlight-bg': 'rgba(255, 208, 0, 0.4)',
    '--text-muted': 'var(--color-base-70)',
    '--text-normal': 'var(--color-base-100)',
    '--text-on-accent': 'white',
    '--text-on-accent-inverted': 'black',
    '--text-selection': 'color-mix(in oklch, var(--interactive-accent) 20%, transparent)',
    '--text-success': 'var(--color-green)',
    '--text-warning': 'var(--color-orange)',
    '--titlebar-background': 'var(--background-secondary)',
    '--titlebar-background-focused': 'var(--background-secondary-alt)',
    '--titlebar-border-color': 'var(--background-modifier-border)',
    '--titlebar-text-color': 'var(--text-muted)',
    '--titlebar-text-color-focused': 'var(--text-normal)',
    '--toggle-thumb-color': 'white',
    '--vault-profile-color': 'var(--text-normal)',
    '--vault-profile-color-hover': 'var(--vault-profile-color)',
    '--workspace-background-translucent': 'color-mix(in oklch, var(--mono-0) 60%, transparent)',
}


# --- 5. what the checker measures ------------------------------------------------------------------
# Text on ground, by variable, in a scope, with APCA's tier for what it carries (build/apca.py GUIDANCE):
# 75 for text read at 400, 60 at 700, 30 for a mark. Both sides are resolved out of the committed theme
# over the recorded platform, the way the browser resolves them.
PAIRS = [
    ('--text-normal', '--background-primary', None, 75, 'the note, 400'),
    ('--text-muted', '--background-primary', None, 75, 'secondary text on the field, 400'),
    ('--text-faint', '--background-primary', None, 75, 'faint text on the field: DARK, read'),
    ('--text-accent', '--background-primary', None, 75, 'accent text on the field'),
    ('--link-color', '--background-primary', None, 75, 'a link, underlined'),
    ('--link-unresolved-color', '--background-primary', None, 75, 'an unresolved link, dashed'),
    ('--tag-color', '--background-primary', None, 75, 'a tag'),
    ('--text-error', '--background-primary', None, 75, 'error text'),
    ('--text-success', '--background-primary', None, 75, 'success text'),
    ('--text-warning', '--background-primary', None, 75, 'warning text: the ANSI yellow, at its gamut cap'),
    ('--code-normal', '--code-background', None, 75, 'code'),
    ('--code-comment', '--code-background', None, 75, 'a comment, italic'),
    ('--code-string', '--code-background', None, 75, 'a literal'),
    ('--code-function', '--code-background', None, 75, 'a function'),
    ('--caret-color', '--background-primary', None, 60, 'the caret: §2\'s own pair and its own floor'),
    ('--checklist-done-color', '--background-primary', None, 75, 'a task that is done, struck through'),
    ('--metadata-label-text-color', '--background-primary', None, 75, 'a property\'s name'),
    ('--input-placeholder-color', '--background-modifier-form-field', 'field', 75, 'a placeholder'),
    ('--text-normal', '--background-modifier-form-field', 'field', 75, 'what the user types'),
    ('--text-normal', '--background-secondary', 'panel', 60, 'a panel\'s labels, 700'),
    ('--text-muted', '--background-secondary', 'panel', 60, 'a panel\'s secondary labels, 700'),
    ('--nav-item-color', '--background-secondary', 'panel', 60, 'a file in the list, 700'),
    ('--nav-item-color-active', '--nav-item-background-active', 'panel', 75, 'the current file'),
    ('--nav-item-color-hover', '--nav-item-background-hover', 'panel', 60, 'a hovered file, 700'),
    ('--status-bar-text-color', '--status-bar-background', 'panel', 60, 'the status bar, 700'),
    ('--tab-text-color', '--tab-container-background', 'panel', 60, 'a tab on a LIGHT strip, 700'),
    ('--tab-text-color-focused', '--tab-container-background', 'panel', 60, 'the same, window key'),
    ('--tab-text-color-focused', '--tab-container-background', 'key', 75, 'a tab on the key titlebar, 400'),
    ('--tab-text-color-focused-active', '--tab-background-active', 'key', 75, 'the active tab, 400'),
    ('--tab-text-color-active', '--tab-background-active', 'panel', 75, 'the active tab, window not key'),
    ('--icon-color', '--titlebar-background', 'key', 30, 'a glyph on the key titlebar'),
    ('--icon-color', '--background-modifier-hover', 'key', 30, 'a glyph on a hovered button there'),
    ('--icon-color', '--tab-background-active', 'key tab', 30, 'a glyph on the active tab'),
    ('--titlebar-text-color', '--titlebar-background', 'panel', 60, 'the non-key titlebar, 700'),
    ('--titlebar-text-color-focused', '--titlebar-background-focused', 'key', 60, 'the key titlebar'),
    ('--icon-color', '--background-secondary', 'panel', 30, 'a glyph on a panel'),
    ('--icon-color', '--background-primary', None, 30, 'a glyph on the field'),
    ('--icon-color-active', '--background-modifier-active-hover', None, 30, 'a toggle that is on, on the field'),
    ('--icon-color-active', '--background-modifier-active-hover', 'panel', 30, 'the same, on a panel'),
    ('--text-on-accent', '--interactive-accent', None, 75, 'the primary button, 400'),
    ('--text-normal', '--interactive-normal', None, 60, 'a button on the field: LIGHT, 700'),
    ('--text-normal', '--interactive-normal', 'panel', 75, 'a button on a panel: WHITE'),
    ('--text-on-accent', '--interactive-hover', None, 75, 'a hovered button: SELECT carrying WHITE'),
    ('--text-normal', '--menu-background', 'panel', 60, 'a menu label on the frame, 700'),
    ('--text-normal', '--modal-background', None, 75, 'a dialog'),
    ('--text-muted', '--setting-items-background', 'field', 75, 'a setting\'s description'),
    ('--text-normal', '--settings-background', 'panel', 60, 'a settings heading, 700'),
    ('--table-header-color', '--table-header-background', None, 60, 'a table header, 700'),
    ('--callout-title-color', '--callout-default', None, 60, 'a callout\'s title, 700'),
    ('--checkbox-marker-color', '--checkbox-color', None, 30, 'the tick: a glyph'),
    ('--checkbox-border-color', '--background-primary', None, 30, 'the box: a glyph'),
    ('--toggle-thumb-color', '--interactive-accent', None, 30, 'a toggle\'s thumb, on'),
    ('--scrollbar-thumb-bg', '--background-primary', None, 15, 'the scrollbar on the field: visible'),
    ('--scrollbar-thumb-bg', '--background-secondary', 'panel', 15, 'the scrollbar on a panel: visible'),
    ('--drag-ghost-text-color', '--drag-ghost-background', None, 75, 'a row being dragged'),
    ('--lightbox-titlebar-color', '--lightbox-background', None, 75, 'the image viewer\'s title'),
]
# Fills under text that keeps its own colour, and the text's tier on them. CodeMirror paints the selection
# and the hover behind the text, so no fill can be both dE 17.1 from WHITE and a body ground at 400 -- the
# pale-selection trial §2 records. The shortfall is the platform's, measured and not hidden (as in
# build/vscode.py HIGHLIGHTS).
HIGHLIGHTS = [
    ('--text-selection', '--text-normal', None, 'the editor\'s selection'),
    ('--background-modifier-hover', '--text-normal', None, 'a hovered row on the field'),
    ('--table-selection', '--text-normal', None, 'selected table cells'),
    ('--code-bracket-background', '--code-normal', None, 'a matched bracket'),
]
# Grounds that touch. OKLab dE against SURFACE_FLOOR, never Lc (§0e).
ADJACENT = [
    ('--background-primary', '--background-secondary', None, 'the note against a sidebar'),
    ('--background-primary', '--ribbon-background', None, 'the note against the ribbon'),
    ('--background-primary', '--status-bar-background', None, 'the status bar floating over the note'),
    ('--tab-container-background', '--tab-background-active', None, 'the active tab on a LIGHT strip'),
    ('--tab-container-background', '--tab-background-active', 'key', 'the active tab on the key strip'),
    ('--titlebar-background-focused', '--titlebar-background', None, 'key against non-key: the state it carries'),
    ('--tab-container-background', '--background-modifier-hover', 'key', 'a hovered tab on the key strip'),
    ('--background-secondary', '--nav-item-background-hover', 'panel', 'a hovered file'),
    ('--background-secondary', '--nav-item-background-active', 'panel', 'the current file'),
    ('--background-primary', '--background-modifier-hover', None, 'a hovered row on the field'),
    ('--menu-background', '--background-primary', None, 'a menu\'s frame against its rows'),
    ('--settings-background', '--setting-items-background', None, 'a settings card on its page'),
    ('--modal-sidebar-background', '--settings-background', None, 'the settings list against the page'),
    ('--background-primary', '--interactive-normal', None, 'a button on the field'),
    ('--background-secondary', '--interactive-normal', 'panel', 'a button on a panel'),
    ('--background-primary', '--table-header-background', None, 'a table header over its rows'),
    ('--background-primary', '--callout-default', None, 'a callout\'s frame on the note'),
    ('--background-primary', '--callout-warning', None, 'a warning callout\'s frame'),
    ('--background-primary', '--callout-error', None, 'a destructive callout\'s frame'),
    ('--background-primary', '--callout-success', None, 'a success callout\'s frame'),
    ('--background-primary', '--hr-color', None, 'a thematic break'),
    ('--background-primary', '--text-selection', None, 'the selection on the field'),
    ('--background-primary', '--background-modifier-message', None, 'a notice over the note'),
    ('--background-primary', '--checkbox-color', None, 'a ticked box'),
    ('--background-secondary', '--scrollbar-thumb-bg', 'panel', 'the scrollbar on a panel'),
    ('--background-primary', '--scrollbar-thumb-bg', None, 'the scrollbar on the field'),
]
ADJACENT_EXEMPT = {}
# The two legend values may appear only on §3's grounds. The pairs the rules author are checked in check().
LEGEND_GROUNDS = SEMANTIC_GROUNDS


# --- 6. writing ------------------------------------------------------------------------------------
HEADER = """/* Remainder for Obsidian -- the theme. GENERATED by build/obsidian.py --write: never hand-edit; change the
   role table there and regenerate. AUTHORITY.md is the authority; worksafe/obsidian/README_OBSIDIAN.md says
   what each part is for and what is left over. Worksafe tier: a folder in each vault's .obsidian/themes/.
   Checked by build/obsidian.py, against Obsidian 1.13.7 (the Arch package, electron43), 2026-09-25.

   THE ONLY LITERAL COLOURS IN THIS FILE ARE THE --rm-* DEFINITIONS BELOW. Everything else refers to them by
   name, so a value nobody derived cannot get in, and the checker can prove it (CONTRIBUTING.md §8). */
"""


def _fmt(v):
    """A declared value: a role, or a literal whose {role} placeholders become var(--rm-*)."""
    if isinstance(v, R):
        return v.css()
    out = v
    for k in sorted(ROLES, key=len, reverse=True):
        out = out.replace('{' + k + '}', R(k).css())
    return out.replace('{none}', 'transparent')


def _decl_lines(decls, indent='  '):
    out = []
    for d in decls:
        name, value = d[0], d[1]
        note = d[2] if len(d) > 2 else ''
        line = f'{indent}{name}: {_fmt(value)};'
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


def theme_text():
    out = [HEADER.rstrip('\n'), '', 'body.theme-light, body.theme-dark {']
    out += _comment('§2 and §3: the values the theme may name, each checked against palette.json. The three '
                    'signal-text values are build/cosmic.py\'s ANSI normal tier.', '  ')
    for name in ROLES:
        out.append(f'  --rm-{name}: {ROLES[name]};')
    for title, decls in VARS:
        out.append('')
        out += _comment(title, '  ')
        if decls is None:
            decls = [(f'--color-base-{slot}', R(role), f'{hx} in 1.13.7') for slot, hx, role in ramp()]
        out += _decl_lines(decls)
    out.append('}')
    for name, sels, parent, note, decls in SCOPES:
        out.append('')
        out += _comment(f'Scope "{name}". {note}')
        out.append(',\n'.join(sels) + ' {')
        out += _decl_lines(decls)
        out.append('}')
    for note, sel, decls in RULES:
        out.append('')
        out += _comment(note)
        out.append(sel.replace(', ', ',\n') + ' {')
        out += _decl_lines(decls)
        out.append('}')
    return '\n'.join(out) + '\n'


SNIPPET_HEADER = """/* Remainder for Obsidian -- the declutter (AUTHORITY.md §0): motion and blur, removed. GENERATED by
   build/obsidian.py --write: never hand-edit. A CSS snippet, installed into each vault's .obsidian/snippets/ and
   switched on in Settings > Appearance > CSS snippets; it works under any theme, and carries no colour. */
"""


def snippet_text():
    out = [SNIPPET_HEADER.rstrip('\n'), '', 'body.theme-light, body.theme-dark {']
    first = True
    for title, decls in DECLUTTER_VARS:
        if not first:
            out.append('')
        first = False
        out += _comment(title, '  ')
        out += _decl_lines(decls)
    out.append('}')
    for note, sel, decls in DECLUTTER_RULES:
        out.append('')
        out += _comment(note)
        out.append(sel.replace(', ', ',\n') + ' {')
        out += _decl_lines(decls)
        out.append('}')
    return '\n'.join(out) + '\n'


def write():
    os.makedirs(THEME_DIR, exist_ok=True)
    for path, text in ((THEME, theme_text()), (SNIPPET, snippet_text())):
        open(path, 'w').write(text)
        print(f'wrote {os.path.relpath(path, ROOT)}: {len(text.splitlines())} lines')


# --- 7. resolving, the way the browser does ----------------------------------------------------------
_VAR = re.compile(r'var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\)[^()]*)*))?\)')


def _base_env():
    env = dict(PLATFORM)
    for name, hx in ROLES.items():
        env[f'--rm-{name}'] = hx
    for title, decls in VARS:
        if decls is None:
            decls = [(f'--color-base-{slot}', R(role)) for slot, hx, role in ramp()]
        for d in decls:
            env[d[0]] = _fmt(d[1])
    return env


def _scope_env(scope):
    """{name: (value, declaring scope)} -- where each variable is declared, seen from inside `scope`."""
    chain = []
    s = scope
    while s:
        row = next(x for x in SCOPES if x[0] == s)
        chain.append(row)
        s = row[2]
    decl = {k: (v, None) for k, v in _base_env().items()}
    for row in reversed(chain):
        for d in row[4]:
            decl[d[0]] = (_fmt(d[1]), row[0])
    return decl


def resolve(name, scope=None, _depth=0):
    """The value `name` computes to in `scope`. A custom property is computed where it is declared, so a
    reference inside a body-level declaration resolves at body even when read from inside a scope."""
    decl = _scope_env(scope)
    if name not in decl:
        return None
    value, where = decl[name]
    for _ in range(40):
        m = _VAR.search(value)
        if not m:
            break
        ref = resolve(m.group(1), where, _depth + 1)
        if ref is None:
            ref = m.group(2) if m.group(2) is not None else '??'
        value = value[:m.start()] + ref + value[m.end():]
    return value.strip()


_NAMED = {'white': '#FFFFFF', 'black': '#000000'}


def colour(value):
    """(hex, alpha) for a value that is one colour, or None. Blends are resolved to (hex of the colour, alpha)."""
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
        return ('#000000', 0.5)      # a blend or a derived value: never one of the kit's
    return None


def role_of(hx):
    return next((k for k, v in ROLES.items() if v.upper() == hx.upper()), None)


# --- 8. the checker ----------------------------------------------------------------------------------
COMMENT = re.compile(r'/\*.*?\*/', re.S)
HEX = re.compile(r'#[0-9A-Fa-f]{3,8}\b')
MIXED = re.compile(r'\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark|image-set)\s*\(')
NAMED = {'white', 'black', 'red', 'blue', 'green', 'gray', 'grey', 'yellow', 'orange', 'purple', 'pink',
         'silver', 'cyan', 'magenta', 'teal', 'navy', 'maroon', 'lime', 'olive', 'aqua', 'fuchsia',
         'highlight', 'highlighttext', 'canvas', 'canvastext', 'buttontext', 'buttonface', 'selecteditem',
         'selecteditemtext', 'linktext', 'visitedtext', 'graytext', 'accentcolor', 'accentcolortext', 'field',
         'fieldtext', 'mark', 'marktext'}



def check():
    bad, notes = 0, []

    def fail(msg):
        nonlocal bad
        bad += 1
        notes.append(msg)

    # --- the committed file is what the table produces --------------------------------------------
    if not os.path.exists(THEME):
        print(f'obsidian: {os.path.relpath(THEME, ROOT)} is not committed yet -- run --write'); return False
    text = open(THEME).read()
    if text != theme_text():
        fail(f'{os.path.relpath(THEME, ROOT)} is not what the role table produces: run --write, or move the edit '
             'into build/obsidian.py')
    if not os.path.exists(SNIPPET) or open(SNIPPET).read() != snippet_text():
        fail(f'{os.path.relpath(SNIPPET, ROOT)} is not what the declutter table produces: run --write')
    else:
        sn = COMMENT.sub(' ', open(SNIPPET).read())
        found = HEX.findall(sn) + [m.group(1) for m in MIXED.finditer(sn)] + \
            [w for w in re.findall(r'[A-Za-z][A-Za-z-]{2,}', sn) if w.lower() in NAMED] + re.findall(r'var\(--rm-', sn)
        for f in found:
            fail(f'{os.path.relpath(SNIPPET, ROOT)} names a colour ({f}): the declutter paints nothing')
        print(f'{os.path.relpath(SNIPPET, ROOT)}: no colour, {sum(len(d) for _, d in DECLUTTER_VARS)} variables, '
              f'{len(DECLUTTER_RULES)} rules')

    # --- every literal colour is an --rm-* definition, and every definition is a value the kit authors ---
    body = COMMENT.sub(' ', text)
    defs = {}
    for m in re.finditer(r'--rm-([a-z-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;', body):
        defs[m.group(1)] = m.group(2).upper()
    print(f'--rm-* definitions: {len(defs)}')
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

    # --- the ramp ---------------------------------------------------------------------------------------
    rows = ramp()
    order = [LADDER.index(r) for _, _, r in rows]
    if order != sorted(order):
        fail('the ramp is not monotonic: a slot inverts against its neighbour')
    print(f"\nthe ramp: {len(rows)} slots snapped onto §2's four, monotonic")

    # --- every colour variable, resolved under the theme -------------------------------------------------
    names = sorted(n for n in PLATFORM if colour(resolve(n)) is not None)
    counts, off = {}, []
    for n in names:
        hx, a = colour(resolve(n))
        if a == 0:
            kind = 'transparent'
        elif a < 1:
            kind = 'blend (permitted, §4)' if n in BLENDS_PERMITTED else 'BLEND'
        elif role_of(hx):
            kind = role_of(hx)
            if kind in RESERVED:
                kind = 'legend'
        elif n in CONTENT:
            kind = 'content'
        else:
            kind = 'OFF THE LADDER'
        counts[kind] = counts.get(kind, 0) + 1
        if kind in ('BLEND', 'OFF THE LADDER'):
            off.append((n, hx, a, kind))
    for sname, *_ in SCOPES:
        for d in next(x for x in SCOPES if x[0] == sname)[4]:
            c = colour(resolve(d[0], sname))
            if c and 0 < c[1] < 1 or c and c[1] == 1 and not role_of(c[0]):
                off.append((f'{d[0]} in "{sname}"', c[0], c[1], 'OFF THE LADDER'))
    print(f"\nevery colour variable Obsidian 1.13.7 defines, resolved under the theme ({len(names)}):")
    for k in sorted(counts, key=lambda k: -counts[k]):
        print(f'  {counts[k]:4}  {k}')
    for n, hx, a, kind in off:
        fail(f'{n} resolves to {hx} at alpha {a:g}: {kind}')
    legend_vars = [n for n in names if (colour(resolve(n)) or ('', 0))[0] in ('#FFFFFF', '#000000')
                   and (colour(resolve(n)) or ('', 0))[1] == 1]

    # --- the pairs ------------------------------------------------------------------------------------------
    print("\npairs (APCA Lc, signed; the floor is APCA's tier for what the pair carries):")
    for t, g, scope, floor, why in PAIRS:
        tc, gc = colour(resolve(t, scope)), colour(resolve(g, scope))
        if not tc or not gc or tc[1] < 1 or gc[1] < 1:
            fail(f'{t} on {g} ({scope or "body"}): one side does not resolve to an opaque value'); continue
        lc = apca.lc(tc[0], gc[0])
        good = abs(lc) >= floor
        cap = tc[0] in CAPS and abs(lc) >= floor - 1.0
        if not good and not cap:
            bad += 1
        tr, gr = role_of(tc[0]) or tc[0], role_of(gc[0]) or gc[0]
        if tr in RESERVED and gr not in LEGEND_GROUNDS:
            fail(f'{t}: §3 reserves {tc[0]} for legend on a semantic ground, not on {gr}')
        flag = 'ok ' if good else ('cap' if cap else 'LOW')
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  {flag}  {scope or 'body':8} {why}")

    print("\nfills under text that keeps its colour (the platform's shortfall, measured):")
    for g, t, scope, why in HIGHLIGHTS:
        tc, gc = colour(resolve(t, scope)), colour(resolve(g, scope))
        lc = apca.lc(tc[0], gc[0])
        print(f"  {role_of(tc[0]):12} on {role_of(gc[0]) or gc[0]:12} Lc {lc:7.1f}  {why}")

    # --- the rules that set both sides --------------------------------------------------------------------
    print("\npairs the rule blocks author:")
    for note, sel, decls in RULES:
        d = {k: _fmt(v) for k, v in decls}
        fg = d.get('color') or d.get('--text-color')
        bg = d.get('background-color')
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
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  /{weight}  {'ok ' if good else 'LOW'}  {sel[:60]}")

    # --- the adjacencies ------------------------------------------------------------------------------------
    print(f"\nsurfaces that touch (OKLab dE; floor {FLOOR}, derived from WHITE against LIGHT):")
    for a, b, scope, why in ADJACENT:
        ca, cb = colour(resolve(a, scope)), colour(resolve(b, scope))
        dE = ok.delta_e(ca[0], cb[0])
        exempt = (a, b) in ADJACENT_EXEMPT
        good = exempt or dE >= FLOOR - 0.05
        bad += not good
        print(f"  {role_of(ca[0]):12} / {role_of(cb[0]):12} dE {dE:5.1f}  {'exempt' if exempt else ('ok ' if good else 'BELOW')}  "
              f"{scope or 'body':8} {why}")

    # --- the files the installer copies that are not the theme: no colour in any of them --------------------
    for path in [MANIFEST, INSTALLER] + SETTINGS:
        if not os.path.exists(path):
            fail(f'{os.path.relpath(path, ROOT)} is not committed'); continue
        raw = re.sub(r'^\s*#.*$', '', open(path, errors='ignore').read(), flags=re.M)
        found = sorted({m.group(0).upper() for m in HEX.finditer(raw)})
        print(f"\n{os.path.relpath(path, ROOT)}: {len(found)} colour(s) it writes itself")
        for hx in found:
            fail(f'{os.path.relpath(path, ROOT)} carries {hx}')

    if notes:
        print('\nnotes:')
        for n in notes:
            print(f'  {n}')
    print(f"\nobsidian: {'every value, pair and adjacency clears' if not bad else str(bad) + ' DEFECT(S)'}")
    return bad == 0


# --- 9. the installed build: a report, never a gate -----------------------------------------------------
def _asars():
    """Every obsidian.asar this machine would load, newest first. Obsidian loads an obsidian-X.Y.Z.asar it
    downloaded into its config directory over the one the package installed, when that one is newer."""
    cfg = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    found = sorted(glob.glob(os.path.join(cfg, 'obsidian', 'obsidian-*.asar')), reverse=True)
    found += sorted(glob.glob(os.path.expanduser('~/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian-*.asar')),
                    reverse=True)
    for p in ('/usr/lib/obsidian/obsidian.asar', '/opt/Obsidian/resources/obsidian.asar',
              '/var/lib/flatpak/app/md.obsidian.Obsidian/current/active/files/obsidian/resources/obsidian.asar',
              os.path.expanduser('~/.local/share/flatpak/app/md.obsidian.Obsidian/current/active/files/obsidian/resources/obsidian.asar')):
        if os.path.exists(p):
            found.append(p)
    return found


def asar_read(path, member):
    """One file out of an asar archive: a pickled header length, a JSON index, then the files."""
    f = open(path, 'rb')
    _, hsize, _, jlen = struct.unpack('<4I', f.read(16))
    index, base = json.loads(f.read(jlen)), 8 + hsize
    node = index
    for part in member.split('/'):
        node = node['files'][part]
    if node.get('unpacked'):
        return open(path + '.unpacked/' + member, 'rb').read()
    f.seek(base + int(node['offset']))
    return f.read(node['size'])


def platform_vars(css):
    """The body and .theme-light custom properties of an app.css, as the browser would merge them."""
    css = COMMENT.sub('', css)
    env = {}
    for want in ('body', '.theme-light'):
        for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
            if ' '.join(sel.split()) != want:
                continue
            for d in re.split(r';(?![^(]*\))', body):
                if ':' in d:
                    k, v = d.split(':', 1)
                    if k.strip().startswith('--'):
                        env[k.strip()] = ' '.join(v.split())
    return env


def coverage():
    found = _asars()
    if not found:
        print('coverage: no obsidian.asar found (looked in the config directory, /usr/lib/obsidian, /opt/Obsidian, '
              'and the Flatpak roots)'); return True
    path = found[0]
    live = platform_vars(asar_read(path, 'app.css').decode('utf8', 'replace'))
    version = json.loads(asar_read(path, 'package.json')).get('version', '?')
    print(f'{path}: Obsidian {version}, {len(live)} body variables\n')
    changed = [n for n in PLATFORM if n in live and live[n] != PLATFORM[n]]
    gone = [n for n in PLATFORM if n not in live]
    set_by_theme = {d[0] for _, decls in VARS if decls for d in decls} | {f'--color-base-{s}' for s in OBS_RAMP}
    kinds = {'shadow': [], 'mask': [], 'triple': [], 'other': []}
    for n in sorted(set(live) - set(PLATFORM)):
        v = live[n]
        if not (re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|color-mix\(|\b(white|black)\b', v) or
                re.search(r'var\(--(color|background|text|interactive|mono)-', v)):
            continue
        kind = ('mask' if 'mask' in n else 'shadow' if 'shadow' in n else
                'triple' if n.endswith(('-rgb', '-hsl')) else 'other')
        kinds[kind].append(n)
    print('COMPOUND AND COLOUR-BEARING -- a colour inside a longer value, which the recorded table does not hold:')
    for kind, why in (('shadow', 'shadows and focus rings; a real shadow is §4\'s, a ring resolves through --background-modifier-border-focus'),
                      ('mask', 'alpha masks: they cut, and paint nothing'),
                      ('triple', 'deprecated r, g, b and h, s, l triples, kept for old themes and plugins'),
                      ('other', 'the rest')):
        names = kinds[kind]
        if not names:
            continue
        print(f'  {kind} ({len(names)}): {why}')
        for n in names:
            print(f'    {n}{"   (set)" if n in set_by_theme else ""}: {live[n][:100]}')
    unset = [n for n in sorted(PLATFORM) if n not in set_by_theme and n not in LEFT_UNSET
             and colour(resolve(n)) is not None]
    print(f'\nUNSET, RESOLVING THROUGH THE TABLE ({len(unset)}) -- each lands on a kit value by way of a variable the '
          'theme does set; the gate checks where:')
    for n in unset:
        hx, a = colour(resolve(n))
        print(f'  {n:48} -> {"transparent" if a == 0 else role_of(hx) or hx}')
    return True


# --- 10. the screen: what the running app paints ------------------------------------------------------------
# A theme is not what the window shows: the platform's own selectors, its literals and its blends all
# still apply. So this asks a running Obsidian, over the DevTools protocol, what every visible element
# computed -- the way worksafe/firefox/'s Marionette probe asked Firefox -- and reports each painted value
# and each text pair as the screen has it. A report, not a gate: it needs a window.
PROBE = r"""(() => {
  const out = [];
  const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const hex = c => '#' + c.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();
  const name = el => { let s = el.tagName.toLowerCase();
    const cls = (el.getAttribute('class') || '').trim().split(/\s+/).filter(Boolean).slice(0, 3);
    return cls.length ? s + '.' + cls.join('.') : s; };
  const where = el => { const p = []; for (let e = el; e && e !== document.body && p.length < 3; e = e.parentElement) p.unshift(name(e)); return p.join(' > '); };
  const opacity = el => { let o = 1; for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
  const ground = el => { const chain = []; for (let e = el; e; e = e.parentElement) chain.push(e);
    let g = [255, 255, 255]; for (const e of chain.reverse()) { const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c[3] > 0) g = g.map((v, i) => c[i] * c[3] + v * (1 - c[3])); } return g; };
  const SHAPES = new Set(['path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse']);
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || r.bottom < 0 || r.right < 0 || r.top > innerHeight || r.left > innerWidth) continue;
    const op = opacity(el);
    const rec = (prop, c, extra) => { if (c && c[3] > 0 && op > 0) out.push(Object.assign({prop, value: hex(c), alpha: c[3], opacity: op, where: where(el)}, extra || {})); };
    rec('background', parse(cs.backgroundColor));
    for (const s of ['Top', 'Right', 'Bottom', 'Left'])
      if (parseFloat(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none') rec('border', parse(cs['border' + s + 'Color']));
    if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) rec('outline', parse(cs.outlineColor));
    if (el instanceof SVGElement && SHAPES.has(el.tagName.toLowerCase()))
      for (const p of ['fill', 'stroke']) rec(p, parse(cs[p]), {ground: hex(ground(el))});
    if ([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
      rec('text', parse(cs.color), {ground: hex(ground(el)), size: parseFloat(cs.fontSize),
        weight: parseInt(cs.fontWeight), family: cs.fontFamily.split(',').map(f => f.trim().replace(/["']/g, '')).find(f => f && f !== '??'),
        sample: [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').slice(0, 30)});
    if (cs.boxShadow !== 'none') out.push({prop: 'box-shadow', value: cs.boxShadow.slice(0, 120), where: where(el)});
    if (cs.backdropFilter && cs.backdropFilter !== 'none') out.push({prop: 'backdrop-filter', value: cs.backdropFilter, where: where(el)});
  }
  return {body: document.body.className, records: out};
})()"""


def windows(port):
    """Every Obsidian window on the DevTools port: the main one, and each popout -- where Settings opens by
    default on 1.13.7 (settingsPopoutWindow), as an about:blank page the main window fills."""
    import urllib.request
    targets = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
    return [t for t in targets if t.get('type') == 'page' and
            (t['url'].startswith('app://obsidian.md') or 'Obsidian' in t.get('title', ''))]


def _cdp(page):
    """A DevTools client over a websocket, stdlib only: enough to evaluate an expression in one window."""
    import base64, socket
    hostport, path = page['webSocketDebuggerUrl'].split('://', 1)[1].split('/', 1)
    host, p = hostport.split(':')
    s = socket.create_connection((host, int(p)), timeout=60)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f'GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
               f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
    buf = b''
    while b'\r\n\r\n' not in buf:
        buf += s.recv(4096)
    rest = [buf.split(b'\r\n\r\n', 1)[1]]

    def read(k):
        while len(rest[0]) < k:
            rest[0] += s.recv(1 << 20)
        out, rest[0] = rest[0][:k], rest[0][k:]
        return out

    def send(data):
        n = len(data)
        hdr = bytearray([0x81])
        hdr += bytes([0x80 | n]) if n < 126 else (bytes([0x80 | 126]) + struct.pack('>H', n) if n < 65536
                                                  else bytes([0x80 | 127]) + struct.pack('>Q', n))
        mask = os.urandom(4)
        s.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def evaluate(expr):
        send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                         'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}).encode())
        while True:
            data = b''
            while True:
                b0, b1 = read(2)
                n = b1 & 0x7F
                n = struct.unpack('>H', read(2))[0] if n == 126 else struct.unpack('>Q', read(8))[0] if n == 127 else n
                data += read(n)
                if b0 & 0x80:
                    break
            msg = json.loads(data)
            if msg.get('id') == 1:
                return msg['result']['result'].get('value')
    return evaluate


def screen(port):
    for page in windows(port):
        _screen_one(page)
    return True


def _screen_one(page):
    evaluate = _cdp(page)
    shot = evaluate(PROBE)
    recs = shot['records']
    key = 'is-focused' in shot['body'].split()
    print(f"=== {page['title']}: window {'KEY' if key else 'not key'}, {len(recs)} painted values\n")
    by = {}
    for r in recs:
        if r['prop'] in ('box-shadow', 'backdrop-filter'):
            continue
        k = (r['prop'], r['value'], r['alpha'] < 1)
        by.setdefault(k, []).append(r)
    off = 0
    print('painted values that are not the kit\'s (content is exempt; check each is content):')
    for (prop, hx, blend), rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        role = role_of(hx)
        if role and not blend:
            continue
        off += len(rs)
        print(f"  {prop:10} {hx}{' blend' if blend else '      '} {len(rs):4}x  e.g. {rs[0]['where'][-80:]}")
    print(f'\n{sum(len(v) for k, v in by.items() if role_of(k[1]) and not k[2])} values on the kit\'s ladder, {off} off it')
    print('\ntext pairs as painted (the floor is the tier for the weight and size the element computed):')
    pairs = {}
    for r in recs:
        if r['prop'] != 'text':
            continue
        k = (r['value'], r['ground'], r['weight'] >= 600, round(r['size']), r['opacity'] < 1 or r['alpha'] < 1)
        pairs.setdefault(k, []).append(r)
    for (t, g, bold, size, faded), rs in sorted(pairs.items(), key=lambda kv: -len(kv[1])):
        lc = apca.lc(t, g)
        floor = 60 if bold else 75
        flag = 'ok ' if abs(lc) >= floor and not faded and size >= 16 else 'LOW' if abs(lc) < floor else 'SMALL' if size < 16 else 'FADED'
        print(f"  {role_of(t) or t:12} on {role_of(g) or g:12} Lc {lc:6.1f} {size:3}px/{'700' if bold else '400'} "
              f"{flag:5} {len(rs):4}x  e.g. {rs[0]['sample'][:24]!r} {rs[0]['where'][-50:]}")
    for extra in ('box-shadow', 'backdrop-filter'):
        rs = [r for r in recs if r['prop'] == extra]
        if rs:
            print(f"\n{extra}: {len(rs)} element(s), e.g. {rs[0]['value'][:90]} on {rs[0]['where'][-60:]}")
    print()


def _print_derivations():
    print("=== the ramp: Obsidian's twelve neutral slots, each SNAPPED to the nearest of §2's four by lightness ===")
    for slot, hx, role in ramp():
        print(f"  --color-base-{slot:3}  {hx}  L {ok.lch(hx)[0]:.4f}  ->  {role:6} {ROLES[role]}  dE {ok.delta_e(hx, ROLES[role]):5.1f}")
    print("\n=== the roles the theme may name, and nothing else ===")
    for name, hx in ROLES.items():
        fam, gap, req = P.clearance(hx)
        tag = ('reserved for legend (§3)' if name in RESERVED else
               'a pole by construction: the meaning, present' if name in SIGNAL and P.readable(hx) and gap < req else
               'neutral, no readable hue' if not P.readable(hx) else f'clears {gap:.1f}deg from {fam}, needs {req:.1f}')
        print(f"  --rm-{name:13} {hx}  {tag:44} {SOURCE[name]}")


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--write' in sys.argv:
        write(); sys.exit(0)
    if '--coverage' in sys.argv:
        sys.exit(0 if coverage() else 1)
    if '--screen' in sys.argv:
        sys.exit(0 if screen(sys.argv[sys.argv.index('--screen') + 1]) else 1)
    sys.exit(0 if check() else 1)
