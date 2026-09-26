"""The VS Code surface: derive its ladders, write the theme, then check what is committed.
AUTHORITY.md is the authority.

VS Code asks for more values than any surface before it -- 977 colour ids in the 1.137 registry, a
syntax-colouring vocabulary on top, and sixteen ANSI slots -- and it asks under two constraints the
kit had not met yet. Both were measured off the installed build (Flatpak com.visualstudio.code
1.137.0, 2026-09-20) and both shape the surface:

  THE PLATFORM SETS NO WEIGHT. A theme names colours and nothing else; the workbench renders its
    labels at 400 and only its section headers at 700 (`.pane-header{font-size:11px;font-weight:700}`
    in workbench.desktop.main.css). BLACK on LIGHT is Lc 61.2, which §2 authors as the 16px/700 tier
    -- so on this platform LIGHT can carry a header, an icon or a mark, and not a label a user reads.
    Every ground that carries read text here is WHITE (BLACK on it Lc 91.8), LIGHT is the ground of
    the icon strips and the tab strip, and the one rule §5 draws is the status bar: 22 px of BLACK
    with WHITE on it -- half the rule's 44 dp, at a height the platform fixes and a theme cannot
    change; recorded as residue (§4), not echoed.

  THE EDITOR SELECTION CANNOT CARRY ITS OWN TEXT. `editor.selectionForeground` is applied only under
    a high-contrast theme type (the `inline-selected-text` span is created when `isHighContrast(
    themeType)`), so outside one the selection is a fill BEHIND text that keeps its colour. §2's dark
    SELECT-with-WHITE is therefore unreachable in the editor, and the pale tint §2 measured and
    rejected is what the platform leaves: the best in-gamut tint at CHROME chroma that still clears
    the surface floor carries BLACK at Lc 63.4, and LIGHT -- an authored value -- carries it at 61.2.
    The editor selection is LIGHT, the shortfall against the body tier is the platform's, and it is
    recorded in HIGHLIGHTS below rather than hidden. The TERMINAL is different: xterm.js honours
    selectionForeground, so the terminal's selection is SELECT carrying WHITE, as §2 authors it.

So each of the platform's lists is a ladder derived from what the kit already has, and the derivation
ships here beside the surface (CONTRIBUTING.md §8):

  ROLES      most of the 977 ids are roles, and §2 names a value for every role the kit has an
             opinion about; each is a role assignment and the ladder is the assignment itself, as on
             Windows. A boundary between two surfaces is never a line (§5): every `*.border` between
             two grounds is unpainted and the tone changes instead. The OUTLINE OF A CONTROL is not a
             boundary between surfaces -- it is the control's own glyph, like a checkbox's box -- and
             takes BLACK; focus takes ACCENT.
  ANSI       the sixteen terminal slots, taken from build/cosmic.py unchanged: the same buffer, the
             same content (§0a), the same values. The normal tier also carries every piece of TEXT that
             means error, added or warning outside the buffer (a file name, a count, a message), because
             §3's FHWA values are grounds and marks, not text: DESTRUCTIVE on WHITE is Lc 68.1 and
             WARNING on WHITE is Lc 8.0, under the visibility floor. A MARK that means warning takes
             the bright yellow slot (Lc 60.1) for the same reason.
  TINTS      three pale grounds, one per semantic hue, for the fills a diff and a coverage view draw
             BEHIND code: the lightest in-gamut value at that hue, at a chroma between C_FLOOR and a
             signal's own C_REF, that still clears SURFACE_FLOOR against WHITE, chosen for the most
             BLACK-on-it contrast. Each is under the body tier and says so (--derive).
  TOKENS     the syntax colouring is CHOSEN and labelled as such (§0c). Unlike the ANSI slots there is
             no realized convention to honour -- keywords are blue in one editor and orange in the
             next -- and the kit's own arc offers no second hue at its chroma: the three arc hues at
             one lightness sit dE 4.9 and 9.5 apart, measured, under any bar the kit uses. So the
             buffer is coloured by tone and geometry (§6.8): keywords BLACK and bold, comments DARK
             and italic, literals in the kit's one hue (ACCENT), members and functions in its darker
             one (SELECT), and the three semantic hues exactly where their meaning is -- invalid,
             inserted, deleted, and the diagnostics.

Two more things this checker adds, which only a surface with this vocabulary needed:

  IT GATES ON THE PLATFORM'S DEFAULTS, RECORDED. A theme names what it names and VS Code fills the
    rest from the registry's own light defaults, 299 of which are a pole-bearing or a reserved
    literal on 1.137 -- info-blue for focus, links, badges and buttons; #FFFFFF for the editor. An
    unset id there is a Microsoft colour showing through. Those ids are recorded below with their
    date, and the gate runs on any machine; `--coverage` re-reads the live registry off the installed
    build and reports what was renamed or added since, the way build/firefox.py --coverage does.
  IT TELLS A COLOUR FROM AN OPACITY. Two ids (`editorUnnecessaryCode.opacity`,
    `minimap.foregroundOpacity`) take a colour whose only read channel is its alpha. They are left
    alone by name; everything else the theme writes is an opaque authored value or #00000000, which
    is `transparent` spelled the way this platform spells it.

    python3 build/vscode.py              check every value, pair and adjacency in the committed theme
    python3 build/vscode.py --derive     the ladders, and how each value was reached
    python3 build/vscode.py --write      regenerate worksafe/vscode/remainder/themes/remainder-color-theme.json
    python3 build/vscode.py --coverage   the installed build's registry against the theme (a report)
    python3 build/vscode.py --settings   the settings the kit sets, against the installed build (a report)
"""
import glob, json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca, cosmic as C

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
VSC = os.path.join(ROOT, 'worksafe', 'vscode')
EXT = os.path.join(VSC, 'remainder')
THEME = os.path.join(EXT, 'themes', 'remainder-color-theme.json')
MANIFEST = os.path.join(EXT, 'package.json')
SETTINGS = [os.path.join(VSC, 'settings.json'), os.path.join(VSC, 'declutter.json')]
INSTALLER = os.path.join(VSC, 'install.sh')

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
N, CH = PAL['neutrals'], PAL['chrome']
WHITE, LIGHT, DARK, BLACK = N['WHITE'], N['LIGHT'], N['DARK'], N['BLACK']
ACCENT, SELECT, CURSOR = CH['ACCENT'], CH['SELECT'], CH['CURSOR']
SEMANTIC = dict(C.SEMANTIC)
SUCCESS, WARNING, DESTRUCTIVE = SEMANTIC['SUCCESS'], SEMANTIC['WARNING'], SEMANTIC['DESTRUCTIVE']
LEGEND_LIGHT, LEGEND_DARK = '#FFFFFF', '#000000'
# `transparent`, as this platform spells it: a colour VS Code parses and does not paint. The checker
# admits this one alpha and no other.
NONE = '#00000000'
FLOOR = PAL['surface_floor_dE']


# --- 1. the ladders --------------------------------------------------------------------------------
# ANSI: taken from build/cosmic.py, not re-derived. Same slots, same content, same values.
_T = C.terminal()
ANSI = {slot: {tier: _T[slot][tier][0] for tier in ('normal', 'bright')} for slot in _T}
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = (ANSI[s]['normal'] for s in ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan'))
BRED, BGREEN, BYELLOW, BBLUE, BMAGENTA, BCYAN = (ANSI[s]['bright'] for s in ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan'))
# The gamut caps cosmic.py records, carried here so a pair that lands on one is reported as capped and
# not as a defect the value could have avoided: yellow's normal slot cannot reach the 75 tier.
CAPS = {hx: note for slot, row in _T.items() for tier, (hx, lc, note) in row.items() if note}
NEUTRALS = {f'neutral_{i}': hx for i, hx, _ in C.neutrals()}
N5, N7 = NEUTRALS['neutral_5'], NEUTRALS['neutral_7']


def tint(hue):
    """The pale ground for a semantic hue: DERIVED.

    The lightest 8-bit value at `hue` whose chroma keeps it readable as that hue (>= C_FLOOR) and no
    louder than a signal (<= C_REF), that still clears SURFACE_FLOOR against WHITE, taking the one that
    carries BLACK best. It is a fill drawn behind code -- a diff's inserted line, an uncovered branch --
    so the code's own colour has to survive on it; and it is under the body tier by construction, for
    the reason §2 rejected a pale selection: nothing at or under a signal's chroma is both dE 17.1 from
    WHITE and a body ground. The shortfall is printed by --derive and is the platform's, not a choice.
    """
    Lg = np.arange(0.60, 0.97, 0.0005)
    best = None
    for Cc in np.arange(P.C_FLOOR, P.C_REF + 1e-9, 0.002):
        v = ok.from_lch_grid(Lg, Cc, hue)
        keep = np.all((v >= -0.5) & (v <= 255.5), axis=-1)
        for x in np.clip(np.round(v[keep]), 0, 255):
            hx = ok.hexs(x)
            Lq, Cq, _ = ok.lch(hx)
            if Cq < P.C_FLOOR or Cq > P.C_REF + 0.005 or ok.delta_e(hx, WHITE) < FLOOR - 0.05:
                continue
            lc = apca.lc(BLACK, hx)
            if best is None or lc > best[0]:
                best = (lc, hx)
    return best[1]


TINTS = {k: tint(ok.lch(v)[2]) for k, v in SEMANTIC.items()}
TSUCCESS, TWARNING, TDESTRUCTIVE = TINTS['SUCCESS'], TINTS['WARNING'], TINTS['DESTRUCTIVE']


def chart_orange():
    """charts.orange: DERIVED the way an ANSI slot is. VS Code ships #EA5C00 in this slot and the kit
    has no orange -- caution is a pole and §3 authors three semantics, not four -- so the slot takes
    the hue the platform ships and solves lightness and chroma against WHITE at the normal tier, as
    build/cosmic.py does for xterm's slots. Charts are content (§0a). The other five chart slots
    reuse the ANSI normals, which are values the kit already has."""
    hue = ok.lch('#EA5C00')[2]
    g = C._cloud(hue)
    good = [t for t in g if t[1] >= C.TIER_NORMAL]
    return max(good, key=lambda t: t[3])[0]


ORANGE = chart_orange()


def authored():
    """Every hex the committed theme may contain, and which ladder it came from."""
    reg = {WHITE: 'WHITE', LIGHT: 'LIGHT', DARK: 'DARK', BLACK: 'BLACK',
           ACCENT: 'ACCENT', SELECT: 'SELECT', CURSOR: 'CURSOR',
           SUCCESS: 'SUCCESS', WARNING: 'WARNING', DESTRUCTIVE: 'DESTRUCTIVE',
           LEGEND_LIGHT: 'LEGEND_LIGHT', LEGEND_DARK: 'LEGEND_DARK', NONE: 'NONE'}
    for slot, row in ANSI.items():
        for tier, hx in row.items():
            reg.setdefault(hx, f'ansi {tier} {slot}')
    for k, hx in TINTS.items():
        reg.setdefault(hx, f'tint {k}')
    reg.setdefault(ORANGE, 'chart orange')
    reg.setdefault(N5, 'neutral_5')
    reg.setdefault(N7, 'neutral_7')
    return reg


# Values that are content or a signal, by ladder: a pole in one of these is the meaning being present.
# Everything else in the theme is chrome and must clear (principle 1).
def is_content(name):
    return name.startswith(('ansi ', 'tint ', 'chart ')) or name in SEMANTIC or name.startswith('LEGEND')


# --- 2. the role table -----------------------------------------------------------------------------
# Every id the theme decides, on one of the values above, with its reason where the reason is not the
# id's name. Grouped by the part of the workbench it paints. Where a group's shape is decided by one
# of the two platform constraints in the header, the group says which.
W, L, D, B, A, S, CU = WHITE, LIGHT, DARK, BLACK, ACCENT, SELECT, CURSOR
OK_, WN, DS, LL, LD = SUCCESS, WARNING, DESTRUCTIVE, LEGEND_LIGHT, LEGEND_DARK
TS, TW, TD = TSUCCESS, TWARNING, TDESTRUCTIVE

COLORS = [
    # -- the base: what everything else falls back to -------------------------------------------------
    ('foreground', B, 'text'),
    ('strongForeground', B, ''),
    ('descriptionForeground', D, 'secondary text; DARK on WHITE is Lc 79.0'),
    ('disabledForeground', D, '§2 names DARK as disabled text'),
    ('errorForeground', RED, 'error TEXT takes the ANSI normal red: DESTRUCTIVE on WHITE is Lc 68.1, under the body tier'),
    ('icon.foreground', B, 'icons are marks'),
    ('focusBorder', A, 'focus is ACCENT (§2)'),
    ('selection.background', L, 'text selected outside the editor keeps its colour; the fill is LIGHT (HIGHLIGHTS)'),
    ('widget.border', NONE, 'a floating widget is delineated by its shadow, which §4 permits as real'),
    ('sash.hoverBorder', A, 'the drag handle, on hover: a mark'),
    ('progressBar.background', A, ''),
    ('toolbar.hoverBackground', L, 'an icon button, hovered: BLACK glyph on LIGHT'),
    ('toolbar.activeBackground', L, 'pressed: the icon keeps its colour, so the ground stays pale'),
    ('toolbar.hoverOutline', NONE, ''),
    ('actionBar.toggledBackground', L, ''),
    ('surface.background', W, ''),
    ('surface.foreground', B, ''),
    ('surface.border', NONE, ''),
    ('browser.border', NONE, ''),
    ('badge.background', D, 'a count badge: WHITE on DARK, Lc -81.7'),
    ('badge.foreground', W, ''),
    ('profileBadge.background', D, ''),
    ('profileBadge.foreground', W, ''),
    ('banner.background', D, ''),
    ('banner.foreground', W, ''),
    ('banner.iconForeground', W, ''),
    ('textLink.foreground', A, 'links route to ACCENT (§3); Lc 75.4 on WHITE, the body minimum'),
    ('textLink.activeForeground', S, ''),
    ('textPreformat.foreground', B, 'inline code: the face changes (Hack), the ground does not'),
    ('textPreformat.background', NONE, ''),
    ('textPreformat.border', NONE, ''),
    ('textCodeBlock.background', NONE, 'a code block in a hover: the face carries it'),
    ('textBlockQuote.background', NONE, ''),
    ('textBlockQuote.border', B, 'the quote bar is a rule, at the width the platform draws it'),
    ('textSeparator.foreground', B, 'an hr in rendered text: the rule'),
    ('scrollbar.shadow', NONE, 'a flat 6 px grey, not a real shadow -- §5: no line thinner than the rule'),
    ('scrollbarSlider.background', L, 'the slider is a surface on the field: dE 17.1'),
    ('scrollbarSlider.hoverBackground', D, ''),
    ('scrollbarSlider.activeBackground', B, ''),
    ('keybindingLabel.background', D, 'a key cap, 11px/400: WHITE on DARK rather than BLACK on LIGHT'),
    ('keybindingLabel.foreground', W, ''),
    ('keybindingLabel.border', NONE, ''),
    ('keybindingLabel.bottomBorder', NONE, ''),
    ('keybindingTable.headerBackground', L, ''),
    ('keybindingTable.rowsBackground', NONE, ''),

    # -- controls: the outline of a control is its glyph and takes BLACK; focus takes ACCENT ----------
    ('input.background', W, ''),
    ('input.foreground', B, 'what the user types, Lc 91.8'),
    ('input.border', B, 'the well\'s own outline -- a control glyph, not a separator between surfaces'),
    ('input.placeholderForeground', D, ''),
    ('inputOption.activeBackground', A, 'a toggle that is on: ACCENT carrying WHITE (§2)'),
    ('inputOption.activeForeground', W, ''),
    ('inputOption.activeBorder', A, ''),
    ('inputOption.hoverBackground', L, ''),
    ('inputValidation.errorBackground', DS, '§3: a destructive ground with the light legend'),
    ('inputValidation.errorForeground', LL, ''),
    ('inputValidation.errorBorder', DS, ''),
    ('inputValidation.warningBackground', WN, '§3: a warning ground with the dark legend, Lc 81.7'),
    ('inputValidation.warningForeground', LD, ''),
    ('inputValidation.warningBorder', WN, ''),
    ('inputValidation.infoBackground', D, 'information has no hue (§3 has three semantics): tone, DARK with WHITE'),
    ('inputValidation.infoForeground', W, ''),
    ('inputValidation.infoBorder', D, ''),
    ('dropdown.background', W, ''),
    ('dropdown.listBackground', W, ''),
    ('dropdown.foreground', B, ''),
    ('dropdown.border', B, 'control glyph'),
    ('checkbox.background', W, ''),
    ('checkbox.foreground', B, 'the tick'),
    ('checkbox.border', B, 'control glyph'),
    ('checkbox.selectBackground', W, ''),
    ('checkbox.selectBorder', B, ''),
    ('checkbox.disabled.background', L, ''),
    ('checkbox.disabled.foreground', D, ''),
    ('radio.activeBackground', A, ''),
    ('radio.activeForeground', W, ''),
    ('radio.activeBorder', A, ''),
    ('radio.inactiveBackground', W, ''),
    ('radio.inactiveForeground', B, ''),
    ('radio.inactiveBorder', B, ''),
    ('radio.inactiveHoverBackground', L, ''),
    ('button.background', A, 'the primary button: WHITE on ACCENT, Lc -78.5'),
    ('button.foreground', W, ''),
    ('button.hoverBackground', S, 'hover on the accent is SELECT, as in worksafe/firefox/'),
    ('button.border', NONE, ''),
    ('button.separator', W, ''),
    ('button.secondaryBackground', D, 'a secondary button: WHITE on DARK (Lc -81.7), because BLACK on LIGHT at 400 is not a label tier here'),
    ('button.secondaryForeground', W, ''),
    ('button.secondaryHoverBackground', B, ''),
    ('button.secondaryBorder', NONE, ''),
    ('extensionButton.background', D, ''),
    ('extensionButton.foreground', W, ''),
    ('extensionButton.hoverBackground', B, ''),
    ('extensionButton.border', NONE, ''),
    ('extensionButton.separator', W, ''),
    ('extensionButton.prominentBackground', A, ''),
    ('extensionButton.prominentForeground', W, ''),
    ('extensionButton.prominentHoverBackground', S, ''),

    # -- the title bar: the key/non-key surface (PLATFORM.md: window.titleBarStyle custom) -----------
    ('titleBar.activeBackground', A, 'the key titlebar (§2); WHITE on it Lc -78.5 at the 400 the platform renders'),
    ('titleBar.activeForeground', W, ''),
    ('titleBar.inactiveBackground', W, 'non-key: WHITE carrying DARK. LIGHT with BLACK is the bold pair and the platform cannot bold it'),
    ('titleBar.inactiveForeground', D, ''),
    ('titleBar.border', NONE, ''),
    ('menubar.selectionBackground', S, ''),
    ('menubar.selectionForeground', W, ''),
    ('menubar.selectionBorder', NONE, ''),
    ('commandCenter.background', W, 'a WHITE well on the titlebar'),
    ('commandCenter.foreground', B, ''),
    ('commandCenter.border', B, 'control glyph; on the non-key WHITE titlebar it is what shows the well'),
    ('commandCenter.activeBackground', W, ''),
    ('commandCenter.activeForeground', B, ''),
    ('commandCenter.activeBorder', A, ''),
    ('commandCenter.inactiveBorder', D, 'the non-key window\'s controls go DARK with its title'),
    ('commandCenter.inactiveForeground', D, ''),
    ('commandCenter.debuggingBackground', W, ''),

    # -- menus -------------------------------------------------------------------------------------------
    ('menu.background', W, ''),
    ('menu.foreground', B, ''),
    ('menu.selectionBackground', S, 'the highlighted item: SELECT carrying WHITE (§2)'),
    ('menu.selectionForeground', W, ''),
    ('menu.selectionBorder', NONE, ''),
    ('menu.separatorBackground', NONE, 'a separator row with nothing drawn in it is a gap, and a gap is how §5 separates'),
    ('menu.border', NONE, ''),

    # -- the activity bar: icons only, so LIGHT carries it -----------------------------------------------
    ('activityBar.background', L, 'icons are marks: BLACK on LIGHT is Lc 61.2, far over the 30 a mark needs'),
    ('activityBar.foreground', B, ''),
    ('activityBar.inactiveForeground', D, 'DARK on LIGHT, Lc 48.4: a mark'),
    ('activityBar.activeBackground', W, 'the active item is a WHITE well that joins the WHITE sidebar beside it'),
    ('activityBar.activeBorder', A, ''),
    ('activityBar.activeFocusBorder', A, ''),
    ('activityBar.border', NONE, ''),
    ('activityBar.dropBorder', B, ''),
    ('activityBarBadge.background', A, ''),
    ('activityBarBadge.foreground', W, ''),
    ('activityErrorBadge.background', DS, ''),
    ('activityErrorBadge.foreground', LL, ''),
    ('activityWarningBadge.background', WN, ''),
    ('activityWarningBadge.foreground', LD, ''),
    ('activityBarTop.background', L, ''),
    ('activityBarTop.foreground', B, ''),
    ('activityBarTop.inactiveForeground', D, ''),
    ('activityBarTop.activeBackground', W, ''),
    ('activityBarTop.activeBorder', A, ''),
    ('activityBarTop.dropBorder', B, ''),
    ('modernActivityBar.background', L, ''),
    ('modernActivityBar.inactiveBackground', L, ''),
    ('modernActivityBar.activeBackground', W, ''),
    ('modernActivityBar.activeForeground', B, ''),
    ('modernActivityBar.hoverBackground', S, ''),
    ('modernActivityBar.hoverForeground', W, ''),
    ('modernActivityBar.border', NONE, ''),
    ('modernActivityBarItem.activeBackground', W, ''),
    ('modernActivityBarItem.activeForeground', B, ''),
    ('modernActivityBarItem.hoverBackground', S, ''),
    ('modernActivityBarItem.hoverForeground', W, ''),

    # -- the sidebar: a WHITE field, because its lists are read ---------------------------------------
    ('sideBar.background', W, 'lists carry read text at 400, so the ground is WHITE'),
    ('sideBar.foreground', B, ''),
    ('sideBar.border', NONE, 'no line between the sidebar and the editor: both are WHITE and the content marks the join (ADJACENT_EXEMPT)'),
    ('sideBar.dropBackground', L, ''),
    ('sideBarTitle.background', W, 'the view title is 11px/400 (measured), so it stays on WHITE'),
    ('sideBarTitle.foreground', B, ''),
    ('sideBarTitle.border', NONE, ''),
    ('sideBarSectionHeader.background', L, 'section headers render 11px/700 (workbench.desktop.main.css), which is the tier BLACK on LIGHT carries'),
    ('sideBarSectionHeader.foreground', B, ''),
    ('sideBarSectionHeader.border', NONE, ''),
    ('sideBarStickyScroll.background', W, ''),
    ('sideBarStickyScroll.border', NONE, ''),
    ('sideBarActivityBarTop.border', NONE, ''),

    # -- lists and trees ---------------------------------------------------------------------------------
    ('list.activeSelectionBackground', S, 'the selected row: SELECT carrying WHITE (§2)'),
    ('list.activeSelectionForeground', W, ''),
    ('list.activeSelectionIconForeground', W, ''),
    ('list.inactiveSelectionBackground', S, 'the same when the list is not focused; focus is shown by the outline'),
    ('list.inactiveSelectionForeground', W, ''),
    ('list.inactiveSelectionIconForeground', W, ''),
    ('list.hoverBackground', L, 'hover is a LIGHT tint here, not SELECT: extension webviews use this id as a static ground and set it alone, so their text inherits `foreground` -- measured 2026-09-21, BLACK on SELECT in a chat panel'),
    ('list.hoverForeground', B, 'follows: BLACK on LIGHT, Lc 61.2, a fill under text that keeps its colour (HIGHLIGHTS)'),
    ('list.focusBackground', NONE, 'a focused, unselected row is marked by its outline'),
    ('list.focusForeground', B, ''),
    ('list.focusOutline', A, ''),
    ('list.focusAndSelectionOutline', W, 'on a SELECT row an ACCENT outline is dE 11.8 away; WHITE reads'),
    ('list.inactiveFocusBackground', NONE, ''),
    ('list.inactiveFocusOutline', D, ''),
    ('list.highlightForeground', A, 'the matched characters of a filter, on a WHITE row'),
    ('list.focusHighlightForeground', W, 'the same on the SELECT row'),
    ('list.deemphasizedForeground', D, ''),
    ('list.errorForeground', RED, 'a file with errors: the ANSI normal red carries text at Lc 75.0'),
    ('list.warningForeground', YELLOW, 'a file with warnings: the ANSI normal yellow, at its gamut cap'),
    ('list.invalidItemForeground', RED, ''),
    ('list.dropBackground', L, ''),
    ('list.dropBetweenBackground', B, 'the insertion line while dragging: a mark'),
    ('list.filterMatchBackground', NONE, ''),
    ('list.filterMatchBorder', B, 'a match is boxed, not filled, so its text keeps Lc 91.8'),
    ('listFilterWidget.background', W, ''),
    ('listFilterWidget.outline', B, ''),
    ('listFilterWidget.noMatchesOutline', DS, ''),
    ('tree.indentGuidesStroke', NONE, '§5: no line thinner than the rule; indentation is read from the indent'),
    ('tree.inactiveIndentGuidesStroke', NONE, ''),
    ('tree.tableColumnsBorder', NONE, ''),
    ('tree.tableOddRowsBackground', NONE, ''),

    # -- editor groups and tabs --------------------------------------------------------------------------
    ('editorGroupHeader.tabsBackground', L, 'the tab strip is a LIGHT panel; the tabs on it are WHITE'),
    ('editorGroupHeader.tabsBorder', NONE, ''),
    ('editorGroupHeader.noTabsBackground', W, ''),
    ('editorGroupHeader.border', NONE, ''),
    ('editorGroup.border', NONE, ''),
    ('editorGroup.dropBackground', L, ''),
    ('editorGroup.emptyBackground', L, 'an empty group is a LIGHT panel'),
    ('editorGroup.focusedEmptyBorder', A, ''),
    ('editorGroup.dropIntoPromptBackground', D, ''),
    ('editorGroup.dropIntoPromptForeground', W, ''),
    ('editorGroup.dropIntoPromptBorder', NONE, ''),
    ('tab.activeBackground', W, 'the active tab is the visible edge of the field below it'),
    ('tab.activeForeground', B, ''),
    ('tab.activeBorderTop', A, 'a 2 px mark, which is what tells the active tab from the others'),
    ('tab.activeBorder', NONE, ''),
    ('tab.inactiveBackground', W, 'inactive tabs are WHITE too, with DARK labels (Lc 79.0): LIGHT would put their labels at 61.3'),
    ('tab.inactiveForeground', D, ''),
    ('tab.border', NONE, 'the tabs are one WHITE band; §5 draws no line between them'),
    ('tab.hoverBackground', S, ''),
    ('tab.hoverForeground', W, ''),
    ('tab.hoverBorder', NONE, ''),
    ('tab.unfocusedActiveBackground', W, ''),
    ('tab.unfocusedActiveForeground', D, ''),
    ('tab.unfocusedActiveBorderTop', D, ''),
    ('tab.unfocusedActiveBorder', NONE, ''),
    ('tab.unfocusedInactiveBackground', W, ''),
    ('tab.unfocusedInactiveForeground', D, ''),
    ('tab.unfocusedHoverBackground', S, ''),
    ('tab.unfocusedHoverForeground', W, ''),
    ('tab.unfocusedHoverBorder', NONE, ''),
    ('tab.activeModifiedBorder', D, 'unsaved: the platform swaps the close glyph for a dot (geometry); the bar is tone'),
    ('tab.inactiveModifiedBorder', D, ''),
    ('tab.unfocusedActiveModifiedBorder', D, ''),
    ('tab.unfocusedInactiveModifiedBorder', D, ''),
    ('tab.lastPinnedBorder', NONE, ''),
    ('tab.dragAndDropBorder', A, ''),
    ('tab.selectedBackground', W, ''),
    ('tab.selectedForeground', B, ''),
    ('tab.selectedBorderTop', D, ''),
    ('modernEditorTab.activeBackground', W, ''),
    ('modernEditorTab.activeForeground', B, ''),
    ('modernEditorTab.activeHoverBackground', W, ''),
    ('modernEditorTab.hoverBackground', S, ''),
    ('modernEditorTab.hoverForeground', W, ''),
    ('modernEditorTab.inactiveBackground', W, ''),
    ('modernEditorTab.activeActionBackground', NONE, ''),
    ('modernEditorTab.activeHoverActionBackground', NONE, ''),
    ('modernEditorTab.hoverActionBackground', NONE, ''),
    ('modernEditorTab.selectedActionBackground', NONE, ''),
    ('modernTab.activeBackground', W, ''),
    ('modernTab.activeForeground', B, ''),
    ('modernTab.hoverBackground', S, ''),
    ('modernTab.hoverForeground', W, ''),
    ('sideBySideEditor.horizontalBorder', NONE, ''),
    ('sideBySideEditor.verticalBorder', NONE, ''),
    ('multiDiffEditor.background', W, ''),
    ('multiDiffEditor.border', NONE, ''),
    ('multiDiffEditor.headerBackground', L, 'a file header row (HIGHLIGHTS)'),
    ('breadcrumb.background', W, ''),
    ('breadcrumb.foreground', D, ''),
    ('breadcrumb.focusForeground', B, ''),
    ('breadcrumb.activeSelectionForeground', B, ''),
    ('breadcrumbPicker.background', W, ''),

    # -- the editor --------------------------------------------------------------------------------------
    ('editor.background', W, ''),
    ('editor.foreground', B, 'body text, Lc 91.8'),
    ('editorPane.background', W, ''),
    ('editorGutter.background', W, ''),
    ('editor.border', NONE, ''),
    ('editorLineNumber.foreground', D, 'line numbers: DARK on WHITE, Lc 79.0'),
    ('editorLineNumber.activeForeground', B, ''),
    ('editorLineNumber.dimmedForeground', D, ''),
    ('editorActiveLineNumber.foreground', B, ''),
    ('editorCursor.foreground', CU, 'the locator (§2): the one value at another hue'),
    ('editorCursor.background', W, 'text under a block cursor'),
    ('editorMultiCursor.primary.foreground', CU, ''),
    ('editorMultiCursor.primary.background', W, ''),
    ('editorMultiCursor.secondary.foreground', CU, ''),
    ('editorMultiCursor.secondary.background', W, ''),
    ('editor.compositionBorder', B, 'the IME composition underline: a mark'),
    ('editor.selectionBackground', L, 'the platform constraint in the header: a fill behind text that keeps its colour'),
    ('editor.inactiveSelectionBackground', L, 'a boundary reads or is not drawn; focus is shown by the caret'),
    ('editor.selectionForeground', NONE, 'honoured only under a high-contrast theme type; left unpainted so nothing depends on it'),
    ('editor.selectionHighlightBackground', NONE, 'other occurrences of the selection are boxed, not filled'),
    ('editor.selectionHighlightBorder', B, ''),
    ('editor.wordHighlightBackground', NONE, ''),
    ('editor.wordHighlightBorder', B, 'a read occurrence'),
    ('editor.wordHighlightStrongBackground', NONE, ''),
    ('editor.wordHighlightStrongBorder', A, 'a write occurrence'),
    ('editor.wordHighlightTextBackground', NONE, ''),
    ('editor.wordHighlightTextBorder', D, ''),
    ('editor.findMatchBackground', NONE, 'the current match is the selection; its box is ACCENT'),
    ('editor.findMatchBorder', A, ''),
    ('editor.findMatchForeground', NONE, ''),
    ('editor.findMatchHighlightBackground', NONE, ''),
    ('editor.findMatchHighlightBorder', B, 'the other matches, boxed'),
    ('editor.findMatchHighlightForeground', NONE, ''),
    ('editor.findRangeHighlightBackground', NONE, ''),
    ('editor.findRangeHighlightBorder', D, ''),
    ('editor.hoverHighlightBackground', NONE, 'the hover widget itself says what is hovered'),
    ('editor.lineHighlightBackground', NONE, 'no current-line band: the caret is the locator (§2)'),
    ('editor.lineHighlightBorder', NONE, ''),
    ('editor.inactiveLineHighlightBackground', NONE, ''),
    ('editor.rangeHighlightBackground', NONE, ''),
    ('editor.rangeHighlightBorder', B, ''),
    ('editor.symbolHighlightBackground', NONE, ''),
    ('editor.symbolHighlightBorder', B, ''),
    ('editor.foldBackground', NONE, 'a fold shows its own marker'),
    ('editor.foldPlaceholderForeground', D, ''),
    ('editor.linkedEditingBackground', NONE, ''),
    ('editor.snippetTabstopHighlightBackground', NONE, ''),
    ('editor.snippetTabstopHighlightBorder', B, ''),
    ('editor.snippetFinalTabstopHighlightBackground', NONE, ''),
    ('editor.snippetFinalTabstopHighlightBorder', A, ''),
    ('editor.placeholder.foreground', D, ''),
    ('editorWhitespace.foreground', N7, 'rendered whitespace wants to be faint: neutral_7 is Lc 40 on WHITE, over the 30 a mark needs, where LIGHT is 28.5'),
    ('editorRuler.foreground', N7, 'a column ruler the user asked for, at the least visible mark'),
    ('editorIndentGuide.background1', N7, 'declutter.json turns guides off (§5); a user who turns them on gets a mark, not a Microsoft grey'),
    ('editorIndentGuide.activeBackground1', D, ''),
    ('editorIndentGuide.background', N7, ''),
    ('editorIndentGuide.activeBackground', D, ''),
    ('editorIndentGuide.background2', NONE, ''), ('editorIndentGuide.background3', NONE, ''),
    ('editorIndentGuide.background4', NONE, ''), ('editorIndentGuide.background5', NONE, ''),
    ('editorIndentGuide.background6', NONE, ''),
    ('editorIndentGuide.activeBackground2', NONE, ''), ('editorIndentGuide.activeBackground3', NONE, ''),
    ('editorIndentGuide.activeBackground4', NONE, ''), ('editorIndentGuide.activeBackground5', NONE, ''),
    ('editorIndentGuide.activeBackground6', NONE, ''),
    ('editorBracketHighlight.foreground1', B, 'bracket pairs by nesting depth: three tones, the kit\'s one hue and no other'),
    ('editorBracketHighlight.foreground2', A, ''),
    ('editorBracketHighlight.foreground3', S, ''),
    ('editorBracketHighlight.foreground4', NONE, ''), ('editorBracketHighlight.foreground5', NONE, ''),
    ('editorBracketHighlight.foreground6', NONE, ''),
    ('editorBracketHighlight.unexpectedBracket.foreground', RED, 'an unmatched bracket is an error: meaning present'),
    ('editorBracketMatch.background', NONE, ''),
    ('editorBracketMatch.border', B, 'the matching pair, boxed'),
    ('editorBracketMatch.foreground', NONE, ''),
    ('editorBracketPairGuide.background1', B, ''), ('editorBracketPairGuide.background2', A, ''),
    ('editorBracketPairGuide.background3', S, ''), ('editorBracketPairGuide.background4', NONE, ''),
    ('editorBracketPairGuide.background5', NONE, ''), ('editorBracketPairGuide.background6', NONE, ''),
    ('editorBracketPairGuide.activeBackground1', B, ''), ('editorBracketPairGuide.activeBackground2', A, ''),
    ('editorBracketPairGuide.activeBackground3', S, ''), ('editorBracketPairGuide.activeBackground4', NONE, ''),
    ('editorBracketPairGuide.activeBackground5', NONE, ''), ('editorBracketPairGuide.activeBackground6', NONE, ''),
    ('editorCodeLens.foreground', D, ''),
    ('editorInlayHint.foreground', D, 'an inlay hint is told from code by tone, DARK against BLACK'),
    ('editorInlayHint.background', NONE, ''),
    ('editorInlayHint.parameterForeground', D, ''),
    ('editorInlayHint.parameterBackground', NONE, ''),
    ('editorInlayHint.typeForeground', D, ''),
    ('editorInlayHint.typeBackground', NONE, ''),
    ('editorGhostText.foreground', D, ''),
    ('editorGhostText.background', NONE, ''),
    ('editorGhostText.border', NONE, ''),
    ('editorLink.activeForeground', A, ''),
    ('editorUnnecessaryCode.border', NONE, ''),
    ('editorError.foreground', DS, 'the error squiggle: a mark, DESTRUCTIVE on WHITE Lc 68.1'),
    ('editorError.background', NONE, ''),
    ('editorError.border', NONE, ''),
    ('editorWarning.foreground', BYELLOW, 'the warning squiggle: WARNING on WHITE is Lc 8.0, invisible; the ANSI bright yellow is 60.2'),
    ('editorWarning.background', NONE, ''),
    ('editorWarning.border', NONE, ''),
    ('editorInfo.foreground', D, 'information has no hue: DARK'),
    ('editorInfo.background', NONE, ''),
    ('editorInfo.border', NONE, ''),
    ('editorHint.foreground', D, ''),
    ('editorHint.border', NONE, ''),
    ('editorUnicodeHighlight.border', BYELLOW, 'a confusable character: a warning mark'),
    ('editorUnicodeHighlight.background', NONE, ''),
    ('editorLightBulb.foreground', A, 'an action offered: ACCENT, like a toggle'),
    ('editorLightBulbAutoFix.foreground', A, ''),
    ('editorLightBulbAi.foreground', D, ''),
    ('editorGutter.addedBackground', OK_, 'the diff gutter: added is SUCCESS, deleted DESTRUCTIVE, modified has no hue and takes DARK'),
    ('editorGutter.modifiedBackground', D, ''),
    ('editorGutter.deletedBackground', DS, ''),
    ('editorGutter.addedSecondaryBackground', TS, ''),
    ('editorGutter.modifiedSecondaryBackground', L, ''),
    ('editorGutter.deletedSecondaryBackground', TD, ''),
    ('editorGutter.foldingControlForeground', B, ''),
    ('editorGutter.commentRangeForeground', D, ''),
    ('editorGutter.commentGlyphForeground', B, ''),
    ('editorGutter.commentDraftGlyphForeground', D, ''),
    ('editorGutter.commentUnresolvedGlyphForeground', B, ''),
    ('editorGutter.itemGlyphForeground', B, ''),
    ('editorGutter.itemBackground', L, ''),
    ('editorOverviewRuler.background', NONE, ''),
    ('editorOverviewRuler.border', NONE, ''),
    ('editorOverviewRuler.addedForeground', OK_, ''),
    ('editorOverviewRuler.deletedForeground', DS, ''),
    ('editorOverviewRuler.modifiedForeground', D, ''),
    ('editorOverviewRuler.errorForeground', DS, ''),
    ('editorOverviewRuler.warningForeground', BYELLOW, ''),
    ('editorOverviewRuler.infoForeground', D, ''),
    ('editorOverviewRuler.findMatchForeground', B, ''),
    ('editorOverviewRuler.rangeHighlightForeground', A, ''),
    ('editorOverviewRuler.selectionHighlightForeground', D, ''),
    ('editorOverviewRuler.wordHighlightForeground', D, ''),
    ('editorOverviewRuler.wordHighlightStrongForeground', A, ''),
    ('editorOverviewRuler.wordHighlightTextForeground', D, ''),
    ('editorOverviewRuler.bracketMatchForeground', B, ''),
    ('editorOverviewRuler.commonContentForeground', N7, ''),
    ('editorOverviewRuler.currentContentForeground', D, ''),
    ('editorOverviewRuler.incomingContentForeground', A, ''),
    ('editorOverviewRuler.commentForeground', D, ''),
    ('editorOverviewRuler.commentDraftForeground', D, ''),
    ('editorOverviewRuler.commentUnresolvedForeground', D, ''),
    ('editorOverviewRuler.inlineChatInserted', OK_, ''),
    ('editorOverviewRuler.inlineChatRemoved', DS, ''),
    ('editorStickyScroll.background', W, 'sticky lines sit on WHITE and are delineated by their shadow (§4)'),
    ('editorStickyScrollGutter.background', W, ''),
    ('editorStickyScroll.border', NONE, ''),
    ('editorStickyScrollHover.background', L, 'hover on a sticky line (HIGHLIGHTS)'),
    ('minimap.background', W, ''),
    ('minimap.selectionHighlight', L, ''),
    ('minimap.selectionOccurrenceHighlight', D, ''),
    ('minimap.findMatchHighlight', B, ''),
    ('minimap.errorHighlight', DS, ''),
    ('minimap.warningHighlight', BYELLOW, ''),
    ('minimap.infoHighlight', D, ''),
    ('minimap.chatEditHighlight', A, ''),
    ('minimapGutter.addedBackground', OK_, ''),
    ('minimapGutter.modifiedBackground', D, ''),
    ('minimapGutter.deletedBackground', DS, ''),
    ('minimapSlider.background', L, 'the slider is a surface, and opaque: the region under it is the one on screen'),
    ('minimapSlider.hoverBackground', L, ''),
    ('minimapSlider.activeBackground', L, ''),
    ('editorMinimap.inlineChatInserted', OK_, ''),

    # -- editor widgets: find, suggest, hover, peek, marker navigation -------------------------------
    ('editorWidget.background', W, 'a widget on the field carries read text; its shadow delineates it'),
    ('editorWidget.foreground', B, ''),
    ('editorWidget.border', NONE, ''),
    ('editorWidget.resizeBorder', A, ''),
    ('editorSuggestWidget.background', W, ''),
    ('editorSuggestWidget.foreground', B, ''),
    ('editorSuggestWidget.border', NONE, ''),
    ('editorSuggestWidget.highlightForeground', A, ''),
    ('editorSuggestWidget.focusHighlightForeground', W, ''),
    ('editorSuggestWidget.selectedBackground', S, ''),
    ('editorSuggestWidget.selectedForeground', W, ''),
    ('editorSuggestWidget.selectedIconForeground', W, ''),
    ('editorSuggestWidget.focusOutline', NONE, ''),
    ('editorSuggestWidgetStatus.foreground', D, ''),
    ('editorHoverWidget.background', W, ''),
    ('editorHoverWidget.foreground', B, ''),
    ('editorHoverWidget.border', NONE, ''),
    ('editorHoverWidget.highlightForeground', A, ''),
    ('editorHoverWidget.statusBarBackground', L, 'the hover\'s footer row (HIGHLIGHTS)'),
    ('editorActionList.background', W, ''),
    ('editorActionList.foreground', B, ''),
    ('editorActionList.focusBackground', S, ''),
    ('editorActionList.focusForeground', W, ''),
    ('editorMarkerNavigation.background', W, ''),
    ('editorMarkerNavigationError.background', DS, 'the widget\'s frame'),
    ('editorMarkerNavigationError.headerBackground', TD, 'the header carries the message in BLACK, so it is the tint'),
    ('editorMarkerNavigationWarning.background', BYELLOW, ''),
    ('editorMarkerNavigationWarning.headerBackground', TW, ''),
    ('editorMarkerNavigationInfo.background', D, ''),
    ('editorMarkerNavigationInfo.headerBackground', L, ''),
    ('peekView.border', A, 'the peek is an inset window: its frame and title are the key titlebar'),
    ('peekViewTitle.background', A, ''),
    ('peekViewTitleLabel.foreground', W, ''),
    ('peekViewTitleDescription.foreground', W, ''),
    ('peekViewEditor.background', W, ''),
    ('peekViewEditorGutter.background', W, ''),
    ('peekViewEditorStickyScroll.background', W, ''),
    ('peekViewEditorStickyScrollGutter.background', W, ''),
    ('peekViewEditor.matchHighlightBackground', NONE, ''),
    ('peekViewEditor.matchHighlightBorder', B, ''),
    ('peekViewResult.background', W, ''),
    ('peekViewResult.fileForeground', B, ''),
    ('peekViewResult.lineForeground', D, ''),
    ('peekViewResult.matchHighlightBackground', L, 'no border id here, so the match is a LIGHT fill (HIGHLIGHTS)'),
    ('peekViewResult.selectionBackground', S, ''),
    ('peekViewResult.selectionForeground', W, ''),
    ('editorCommentsWidget.rangeBackground', L, ''),
    ('editorCommentsWidget.rangeActiveBackground', L, ''),
    ('editorCommentsWidget.replyInputBackground', W, ''),
    ('editorCommentsWidget.resolvedBorder', OK_, 'resolved is done: SUCCESS'),
    ('editorCommentsWidget.unresolvedBorder', D, ''),
    ('commentsView.resolvedIcon', OK_, ''),
    ('commentsView.unresolvedIcon', D, ''),

    # -- diff, merge, inline edits -----------------------------------------------------------------------
    ('diffEditor.insertedLineBackground', TS, 'a line added: the SUCCESS tint behind BLACK code'),
    ('diffEditor.removedLineBackground', TD, ''),
    ('diffEditor.insertedTextBackground', NONE, 'the changed words inside the line are boxed in the signal itself'),
    ('diffEditor.removedTextBackground', NONE, ''),
    ('diffEditor.insertedTextBorder', OK_, ''),
    ('diffEditor.removedTextBorder', DS, ''),
    ('diffEditor.diagonalFill', L, ''),
    ('diffEditor.border', NONE, ''),
    ('diffEditor.move.border', D, ''),
    ('diffEditor.moveActive.border', A, ''),
    ('diffEditor.unchangedRegionBackground', D, 'a collapsed region reads as a tile: WHITE on DARK'),
    ('diffEditor.unchangedRegionForeground', W, ''),
    ('diffEditor.unchangedCodeBackground', NONE, ''),
    ('diffEditorGutter.insertedLineBackground', TS, ''),
    ('diffEditorGutter.removedLineBackground', TD, ''),
    ('diffEditorOverview.insertedForeground', OK_, ''),
    ('diffEditorOverview.removedForeground', DS, ''),
    ('merge.currentHeaderBackground', L, 'the legacy conflict headers carry the marker line in BLACK; the sides are told apart by the markers (geometry)'),
    ('merge.currentContentBackground', NONE, ''),
    ('merge.incomingHeaderBackground', L, ''),
    ('merge.incomingContentBackground', NONE, ''),
    ('merge.commonHeaderBackground', L, ''),
    ('merge.commonContentBackground', NONE, ''),
    ('merge.border', NONE, ''),
    ('mergeEditor.change.background', NONE, ''),
    ('mergeEditor.change.word.background', L, ''),
    ('mergeEditor.changeBase.background', NONE, ''),
    ('mergeEditor.changeBase.word.background', L, ''),
    ('mergeEditor.conflict.unhandledFocused.border', A, ''),
    ('mergeEditor.conflict.unhandledUnfocused.border', D, ''),
    ('mergeEditor.conflict.handledFocused.border', OK_, 'handled is done: SUCCESS'),
    ('mergeEditor.conflict.handledUnfocused.border', OK_, ''),
    ('mergeEditor.conflict.unhandled.minimapOverViewRuler', D, ''),
    ('mergeEditor.conflict.handled.minimapOverViewRuler', OK_, ''),
    ('mergeEditor.conflictingLines.background', TW, 'lines in conflict: a hazard, the WARNING tint'),
    ('mergeEditor.conflict.input1.background', NONE, ''),
    ('mergeEditor.conflict.input2.background', NONE, ''),
    ('inlineEdit.gutterIndicator.background', L, ''),
    ('inlineEdit.gutterIndicator.primaryBackground', A, ''),
    ('inlineEdit.gutterIndicator.primaryBorder', A, ''),
    ('inlineEdit.gutterIndicator.primaryForeground', W, ''),
    ('inlineEdit.gutterIndicator.secondaryBackground', D, ''),
    ('inlineEdit.gutterIndicator.secondaryBorder', D, ''),
    ('inlineEdit.gutterIndicator.secondaryForeground', W, ''),
    ('inlineEdit.gutterIndicator.successfulBackground', OK_, ''),
    ('inlineEdit.gutterIndicator.successfulBorder', OK_, ''),
    ('inlineEdit.gutterIndicator.successfulForeground', LL, ''),
    ('inlineEdit.modifiedBackground', TS, ''),
    ('inlineEdit.modifiedBorder', OK_, ''),
    ('inlineEdit.modifiedChangedLineBackground', TS, ''),
    ('inlineEdit.modifiedChangedTextBackground', NONE, ''),
    ('inlineEdit.originalBackground', TD, ''),
    ('inlineEdit.originalBorder', DS, ''),
    ('inlineEdit.originalChangedLineBackground', TD, ''),
    ('inlineEdit.originalChangedTextBackground', NONE, ''),
    ('inlineEdit.tabWillAcceptModifiedBorder', A, ''),
    ('inlineEdit.tabWillAcceptOriginalBorder', A, ''),
    ('inlineChatDiff.inserted', TS, ''),
    ('inlineChatDiff.removed', TD, ''),
    ('interactive.activeCodeBorder', A, ''),
    ('interactive.inactiveCodeBorder', D, ''),

    # -- the panel, the terminal, output ---------------------------------------------------------------
    ('panel.background', W, 'the panel carries read text (problems, output, the terminal): WHITE'),
    ('panel.border', NONE, 'no line to the editor above: WHITE meets WHITE (ADJACENT_EXEMPT)'),
    ('panel.dropBorder', B, ''),
    ('panelTitle.activeForeground', B, ''),
    ('panelTitle.inactiveForeground', D, ''),
    ('panelTitle.activeBorder', A, ''),
    ('panelTitle.border', NONE, ''),
    ('panelTitleBadge.background', A, ''),
    ('panelTitleBadge.foreground', W, ''),
    ('panelInput.border', B, ''),
    ('panelSection.border', NONE, ''),
    ('panelSection.dropBackground', L, ''),
    ('panelSectionHeader.background', L, '11px/700, like the sidebar\'s'),
    ('panelSectionHeader.foreground', B, ''),
    ('panelSectionHeader.border', NONE, ''),
    ('panelStickyScroll.background', W, ''),
    ('panelStickyScroll.border', NONE, ''),
    ('outputView.background', W, ''),
    ('outputViewStickyScroll.background', W, ''),
    ('terminal.background', W, ''),
    ('terminal.foreground', B, 'BLACK on WHITE, Lc 91.8 -- worksafe/cosmic/remainder-term.ron\'s pair'),
    ('terminal.selectionBackground', S, 'xterm.js honours selectionForeground, so the terminal has §2\'s selection: SELECT carrying WHITE'),
    ('terminal.selectionForeground', W, ''),
    ('terminal.inactiveSelectionBackground', S, ''),
    ('terminal.border', NONE, ''),
    ('terminal.dropBackground', L, ''),
    ('terminal.findMatchBackground', NONE, ''),
    ('terminal.findMatchBorder', A, ''),
    ('terminal.findMatchHighlightBackground', NONE, ''),
    ('terminal.findMatchHighlightBorder', B, ''),
    ('terminal.hoverHighlightBackground', NONE, ''),
    ('terminal.initialHintForeground', D, ''),
    ('terminal.tab.activeBorder', A, ''),
    ('terminalCursor.foreground', CU, '§2 names the terminal cursor as CURSOR\'s use'),
    ('terminalCursor.background', W, ''),
    ('terminal.ansiBlack', B, '§2\'s four-step ladder onto the four neutral ANSI slots (build/cosmic.py)'),
    ('terminal.ansiRed', RED, ''), ('terminal.ansiGreen', GREEN, ''), ('terminal.ansiYellow', YELLOW, ''),
    ('terminal.ansiBlue', BLUE, ''), ('terminal.ansiMagenta', MAGENTA, ''), ('terminal.ansiCyan', CYAN, ''),
    ('terminal.ansiWhite', L, ''),
    ('terminal.ansiBrightBlack', D, ''),
    ('terminal.ansiBrightRed', BRED, ''), ('terminal.ansiBrightGreen', BGREEN, ''), ('terminal.ansiBrightYellow', BYELLOW, ''),
    ('terminal.ansiBrightBlue', BBLUE, ''), ('terminal.ansiBrightMagenta', BMAGENTA, ''), ('terminal.ansiBrightCyan', BCYAN, ''),
    ('terminal.ansiBrightWhite', W, ''),
    ('terminalCommandDecoration.defaultBackground', D, ''),
    ('terminalCommandDecoration.successBackground', OK_, ''),
    ('terminalCommandDecoration.errorBackground', DS, ''),
    ('terminalCommandGuide.foreground', D, ''),
    ('terminalOverviewRuler.border', NONE, ''),
    ('terminalOverviewRuler.cursorForeground', CU, ''),
    ('terminalOverviewRuler.findMatchForeground', B, ''),
    ('terminalStickyScroll.background', W, ''),
    ('terminalStickyScroll.border', NONE, ''),
    ('terminalStickyScrollHover.background', L, ''),
    ('terminalSymbolIcon.aliasForeground', B, 'suggestion icons are glyphs'), ('terminalSymbolIcon.argumentForeground', B, ''),
    ('terminalSymbolIcon.branchForeground', B, ''), ('terminalSymbolIcon.commitForeground', B, ''),
    ('terminalSymbolIcon.fileForeground', B, ''), ('terminalSymbolIcon.flagForeground', B, ''),
    ('terminalSymbolIcon.folderForeground', B, ''), ('terminalSymbolIcon.inlineSuggestionForeground', D, ''),
    ('terminalSymbolIcon.methodForeground', B, ''), ('terminalSymbolIcon.optionForeground', B, ''),
    ('terminalSymbolIcon.optionValueForeground', B, ''), ('terminalSymbolIcon.pullRequestDoneForeground', B, ''),
    ('terminalSymbolIcon.pullRequestForeground', B, ''), ('terminalSymbolIcon.remoteForeground', B, ''),
    ('terminalSymbolIcon.stashForeground', B, ''), ('terminalSymbolIcon.symbolText', B, ''),
    ('terminalSymbolIcon.symbolicLinkFileForeground', B, ''), ('terminalSymbolIcon.symbolicLinkFolderForeground', B, ''),
    ('terminalSymbolIcon.tagForeground', B, ''),

    # -- the status bar: the rule (§5) --------------------------------------------------------------------
    ('statusBar.background', B, '22 px of BLACK carrying WHITE (Lc -92.3): the one rule this surface draws, at the height the platform fixes -- half the rule\'s 44 dp'),
    ('statusBar.foreground', W, ''),
    ('statusBar.border', NONE, ''),
    ('statusBar.focusBorder', W, ''),
    ('statusBar.noFolderBackground', B, ''),
    ('statusBar.noFolderForeground', W, ''),
    ('statusBar.noFolderBorder', NONE, ''),
    ('statusBar.debuggingBackground', S, 'a mode, not a signal: tone on the rule'),
    ('statusBar.debuggingForeground', W, ''),
    ('statusBar.debuggingBorder', NONE, ''),
    ('statusBarItem.hoverBackground', D, ''),
    ('statusBarItem.hoverForeground', W, ''),
    ('statusBarItem.activeBackground', D, ''),
    ('statusBarItem.compactHoverBackground', D, ''),
    ('statusBarItem.focusBorder', W, ''),
    ('statusBarItem.prominentBackground', D, ''),
    ('statusBarItem.prominentForeground', W, ''),
    ('statusBarItem.prominentHoverBackground', B, ''),
    ('statusBarItem.prominentHoverForeground', W, ''),
    ('statusBarItem.remoteBackground', A, ''),
    ('statusBarItem.remoteForeground', W, ''),
    ('statusBarItem.remoteHoverBackground', S, ''),
    ('statusBarItem.remoteHoverForeground', W, ''),
    ('statusBarItem.errorBackground', DS, '§3: the destructive ground and its legend, on the rule'),
    ('statusBarItem.errorForeground', LL, ''),
    ('statusBarItem.errorHoverBackground', DS, ''),
    ('statusBarItem.errorHoverForeground', LL, ''),
    ('statusBarItem.warningBackground', WN, ''),
    ('statusBarItem.warningForeground', LD, ''),
    ('statusBarItem.warningHoverBackground', WN, ''),
    ('statusBarItem.warningHoverForeground', LD, ''),
    ('statusBarItem.offlineBackground', D, 'offline is a state without a §3 hue: tone'),
    ('statusBarItem.offlineForeground', W, ''),
    ('statusBarItem.offlineHoverBackground', D, ''),
    ('statusBarItem.offlineHoverForeground', W, ''),

    # -- quick input, notifications, settings, welcome ---------------------------------------------------
    ('quickInput.background', W, ''),
    ('quickInput.foreground', B, ''),
    ('quickInputTitle.background', L, 'the title row carries its text in quickInput.foreground, so it is the pale ground (HIGHLIGHTS)'),
    ('quickInputList.focusBackground', S, ''),
    ('quickInputList.focusForeground', W, ''),
    ('quickInputList.focusIconForeground', W, ''),
    ('quickInputList.focusHighlightForeground', W, ''),
    ('quickInput.list.focusBackground', S, ''),
    ('pickerGroup.foreground', A, ''),
    ('pickerGroup.border', NONE, ''),
    ('notifications.background', W, ''),
    ('notifications.foreground', B, ''),
    ('notifications.border', NONE, ''),
    ('notificationCenter.border', NONE, ''),
    ('notificationToast.border', NONE, ''),
    ('notificationCenterHeader.background', D, ''),
    ('notificationCenterHeader.foreground', W, ''),
    ('notificationLink.foreground', A, ''),
    ('notificationsErrorIcon.foreground', DS, ''),
    ('notificationsWarningIcon.foreground', BYELLOW, ''),
    ('notificationsInfoIcon.foreground', D, ''),
    ('problemsErrorIcon.foreground', DS, 'the problems view\'s icons: the same marks as the squiggles'),
    ('problemsWarningIcon.foreground', BYELLOW, ''),
    ('problemsInfoIcon.foreground', D, ''),
    ('settings.headerForeground', B, ''),
    ('settings.modifiedItemIndicator', A, 'the modified-setting bar: a mark'),
    ('settings.dropdownBackground', W, ''), ('settings.dropdownForeground', B, ''),
    ('settings.dropdownBorder', B, ''), ('settings.dropdownListBorder', B, ''),
    ('settings.checkboxBackground', W, ''), ('settings.checkboxForeground', B, ''), ('settings.checkboxBorder', B, ''),
    ('settings.textInputBackground', W, ''), ('settings.textInputForeground', B, ''), ('settings.textInputBorder', B, ''),
    ('settings.numberInputBackground', W, ''), ('settings.numberInputForeground', B, ''), ('settings.numberInputBorder', B, ''),
    ('settings.focusedRowBackground', NONE, ''),
    ('settings.focusedRowBorder', A, ''),
    ('settings.rowHoverBackground', NONE, ''),
    ('settings.headerBorder', NONE, ''),
    ('settings.sashBorder', NONE, ''),
    ('settings.settingsHeaderHoverForeground', A, ''),
    ('welcomePage.background', W, ''),
    ('welcomePage.tileBackground', W, ''),
    ('welcomePage.tileBorder', B, 'a tile is a button: its outline is its glyph'),
    ('welcomePage.tileHoverBackground', L, ''),
    ('welcomePage.progress.background', L, ''),
    ('welcomePage.progress.foreground', A, ''),
    ('walkThrough.embeddedEditorBackground', W, ''),
    ('walkthrough.stepTitle.foreground', B, ''),
    ('search.resultsInfoForeground', D, ''),
    ('searchEditor.findMatchBackground', NONE, ''),
    ('searchEditor.findMatchBorder', B, ''),
    ('searchEditor.textInputBorder', B, ''),
    ('simpleFindWidget.sashBorder', NONE, ''),
    ('profiles.sashBorder', NONE, ''),
    ('extensionBadge.remoteBackground', A, ''),
    ('extensionBadge.remoteForeground', W, ''),
    ('extensionIcon.preReleaseForeground', D, ''),
    ('extensionIcon.privateForeground', D, ''),
    ('extensionIcon.sponsorForeground', B, ''),
    ('extensionIcon.starForeground', B, 'a rating star is a mark, not a signal'),
    ('extensionIcon.verifiedForeground', B, ''),
    ('mcpIcon.starForeground', B, ''),
    ('ports.iconRunningProcessForeground', OK_, 'running is healthy: SUCCESS'),

    # -- symbols: the suggest widget's glyphs, on the token scheme below --------------------------------
    ('symbolIcon.classForeground', A, 'types take the literal hue in bold in the buffer; their glyph takes the hue'),
    ('symbolIcon.interfaceForeground', A, ''), ('symbolIcon.structForeground', A, ''),
    ('symbolIcon.enumeratorForeground', A, ''), ('symbolIcon.typeParameterForeground', A, ''),
    ('symbolIcon.moduleForeground', A, ''), ('symbolIcon.namespaceForeground', A, ''), ('symbolIcon.packageForeground', A, ''),
    ('symbolIcon.stringForeground', A, ''), ('symbolIcon.numberForeground', A, ''), ('symbolIcon.constantForeground', A, ''),
    ('symbolIcon.enumeratorMemberForeground', A, ''), ('symbolIcon.colorForeground', A, ''), ('symbolIcon.unitForeground', A, ''),
    ('symbolIcon.functionForeground', S, 'functions, methods, constructors and events are SELECT in the buffer'),
    ('symbolIcon.methodForeground', S, ''), ('symbolIcon.constructorForeground', S, ''), ('symbolIcon.eventForeground', S, ''),
    ('symbolIcon.variableForeground', B, ''), ('symbolIcon.fieldForeground', B, ''), ('symbolIcon.propertyForeground', B, ''),
    ('symbolIcon.keyForeground', B, ''), ('symbolIcon.keywordForeground', B, ''), ('symbolIcon.operatorForeground', B, ''),
    ('symbolIcon.objectForeground', B, ''), ('symbolIcon.arrayForeground', B, ''), ('symbolIcon.booleanForeground', B, ''),
    ('symbolIcon.nullForeground', B, ''), ('symbolIcon.referenceForeground', B, ''), ('symbolIcon.fileForeground', B, ''),
    ('symbolIcon.folderForeground', B, ''),
    ('symbolIcon.snippetForeground', D, ''), ('symbolIcon.textForeground', D, ''),

    # -- debug ---------------------------------------------------------------------------------------------
    ('debugToolBar.background', L, 'icons'),
    ('debugToolBar.border', NONE, ''),
    ('debugIcon.breakpointForeground', DS, 'a breakpoint means stop: DESTRUCTIVE'),
    ('debugIcon.breakpointDisabledForeground', D, ''),
    ('debugIcon.breakpointUnverifiedForeground', D, ''),
    ('debugIcon.breakpointCurrentStackframeForeground', A, ''),
    ('debugIcon.breakpointStackframeForeground', D, ''),
    ('debugIcon.startForeground', OK_, 'start and continue mean go: SUCCESS'),
    ('debugIcon.continueForeground', OK_, ''),
    ('debugIcon.restartForeground', OK_, ''),
    ('debugIcon.pauseForeground', B, ''),
    ('debugIcon.stopForeground', DS, ''),
    ('debugIcon.disconnectForeground', DS, ''),
    ('debugIcon.stepOverForeground', B, ''), ('debugIcon.stepIntoForeground', B, ''),
    ('debugIcon.stepOutForeground', B, ''), ('debugIcon.stepBackForeground', B, ''),
    ('debugConsole.errorForeground', RED, ''),
    ('debugConsole.warningForeground', YELLOW, ''),
    ('debugConsole.infoForeground', D, ''),
    ('debugConsole.sourceForeground', D, ''),
    ('debugConsoleInputIcon.foreground', D, ''),
    ('debugExceptionWidget.background', TD, ''),
    ('debugExceptionWidget.border', DS, ''),
    ('debugTokenExpression.name', B, ''), ('debugTokenExpression.value', B, ''),
    ('debugTokenExpression.string', A, ''), ('debugTokenExpression.number', A, ''),
    ('debugTokenExpression.boolean', B, ''), ('debugTokenExpression.type', A, ''),
    ('debugTokenExpression.error', RED, ''),
    ('debugView.exceptionLabelBackground', DS, ''),
    ('debugView.exceptionLabelForeground', LL, ''),
    ('debugView.stateLabelBackground', D, ''),
    ('debugView.stateLabelForeground', W, ''),
    ('debugView.valueChangedHighlight', A, ''),
    ('editor.stackFrameHighlightBackground', L, 'the line being executed: the gutter arrow locates it, the band is tone (HIGHLIGHTS)'),
    ('editor.focusedStackFrameHighlightBackground', L, ''),
    ('editor.inlineValuesBackground', L, ''),
    ('editor.inlineValuesForeground', B, ''),

    # -- git, testing, charts, the graph -------------------------------------------------------------------
    ('gitDecoration.addedResourceForeground', GREEN, 'added and untracked are new content: the ANSI normal green carries the name at Lc 75.3'),
    ('gitDecoration.untrackedResourceForeground', GREEN, ''),
    ('gitDecoration.deletedResourceForeground', RED, ''),
    ('gitDecoration.stageDeletedResourceForeground', RED, ''),
    ('gitDecoration.conflictingResourceForeground', RED, ''),
    ('gitDecoration.modifiedResourceForeground', B, 'modified has no §3 hue; the M badge carries it (geometry)'),
    ('gitDecoration.stageModifiedResourceForeground', B, ''),
    ('gitDecoration.renamedResourceForeground', B, ''),
    ('gitDecoration.submoduleResourceForeground', B, ''),
    ('gitDecoration.ignoredResourceForeground', D, ''),
    ('git.blame.editorDecorationForeground', D, ''),
    ('testing.iconPassed', OK_, ''), ('testing.iconFailed', DS, ''), ('testing.iconErrored', DS, ''),
    ('testing.iconQueued', D, ''), ('testing.iconUnset', D, ''), ('testing.iconSkipped', D, ''),
    ('testing.iconPassed.retired', D, ''), ('testing.iconFailed.retired', D, ''), ('testing.iconErrored.retired', D, ''),
    ('testing.iconQueued.retired', D, ''), ('testing.iconUnset.retired', D, ''), ('testing.iconSkipped.retired', D, ''),
    ('testing.runAction', A, ''),
    ('testing.peekBorder', DS, ''),
    ('testing.peekHeaderBackground', TD, ''),
    ('testing.messagePeekBorder', D, ''),
    ('testing.messagePeekHeaderBackground', L, ''),
    ('testing.message.error.badgeBackground', DS, ''),
    ('testing.message.error.badgeBorder', DS, ''),
    ('testing.message.error.badgeForeground', LL, ''),
    ('testing.message.error.lineBackground', TD, ''),
    ('testing.message.info.decorationForeground', D, ''),
    ('testing.message.info.lineBackground', NONE, ''),
    ('testing.coveredBackground', TS, ''), ('testing.coveredBorder', OK_, ''),
    ('testing.coveredGutterBackground', OK_, ''), ('testing.coveredMinimapBackground', OK_, ''),
    ('testing.uncoveredBackground', TD, ''), ('testing.uncoveredBorder', DS, ''),
    ('testing.uncoveredGutterBackground', DS, ''), ('testing.uncoveredMinimapBackground', DS, ''),
    ('testing.uncoveredBranchBackground', TD, ''),
    ('testing.coverCountBadgeBackground', D, ''),
    ('testing.coverCountBadgeForeground', W, ''),
    ('charts.foreground', B, 'charts are content (§0a): the five hue slots reuse the ANSI normals, orange is solved from the platform\'s own exemplar'),
    ('charts.lines', D, ''),
    ('charts.red', RED, ''), ('charts.green', GREEN, ''), ('charts.yellow', YELLOW, ''),
    ('charts.blue', BLUE, ''), ('charts.purple', MAGENTA, ''), ('charts.orange', ORANGE, ''),
    ('chart.line', D, ''), ('chart.axis', B, ''), ('chart.guide', L, ''),
    ('scmGraph.foreground1', B, 'the graph\'s five lines are tones and the kit\'s hue: a branch is not a signal'),
    ('scmGraph.foreground2', A, ''), ('scmGraph.foreground3', S, ''),
    ('scmGraph.foreground4', D, ''), ('scmGraph.foreground5', N5, ''),
    ('scmGraph.historyItemRefColor', A, ''),
    ('scmGraph.historyItemRemoteRefColor', S, ''),
    ('scmGraph.historyItemBaseRefColor', D, ''),
    ('scmGraph.historyItemHoverAdditionsForeground', GREEN, ''),
    ('scmGraph.historyItemHoverDeletionsForeground', RED, ''),
    ('scmGraph.historyItemHoverDefaultLabelBackground', D, ''),
    ('scmGraph.historyItemHoverDefaultLabelForeground', W, ''),
    ('scmGraph.historyItemHoverLabelForeground', W, ''),
    ('markdownAlert.caution.foreground', RED, ''),
    ('markdownAlert.warning.foreground', YELLOW, ''),
    ('markdownAlert.tip.foreground', GREEN, ''),
    ('markdownAlert.important.foreground', A, ''),
    ('markdownAlert.note.foreground', D, ''),

    # -- notebooks -------------------------------------------------------------------------------------------
    ('notebook.editorBackground', W, ''),
    ('notebook.cellEditorBackground', W, ''),
    ('notebook.cellBorderColor', NONE, ''),
    ('notebook.cellHoverBackground', NONE, ''),
    ('notebook.selectedCellBackground', NONE, ''),
    ('notebook.selectedCellBorder', A, 'the selected cell is framed, not filled'),
    ('notebook.focusedCellBackground', NONE, ''),
    ('notebook.focusedCellBorder', A, ''),
    ('notebook.focusedEditorBorder', A, ''),
    ('notebook.inactiveFocusedCellBorder', D, ''),
    ('notebook.inactiveSelectedCellBorder', D, ''),
    ('notebook.cellInsertionIndicator', A, ''),
    ('notebook.cellStatusBarItemHoverBackground', L, ''),
    ('notebook.cellToolbarSeparator', NONE, ''),
    ('notebook.outputContainerBackgroundColor', W, ''),
    ('notebook.outputContainerBorderColor', NONE, ''),
    ('notebook.symbolHighlightBackground', L, ''),
    ('notebookScrollbarSlider.background', L, ''),
    ('notebookScrollbarSlider.hoverBackground', D, ''),
    ('notebookScrollbarSlider.activeBackground', B, ''),
    ('notebookStatusErrorIcon.foreground', DS, ''),
    ('notebookStatusRunningIcon.foreground', D, ''),
    ('notebookStatusSuccessIcon.foreground', OK_, ''),
    ('notebookEditorOverviewRuler.runningCellForeground', D, ''),

    # -- chat, agents, inline chat: the UI stays themed for a user who turns the features back on -----------
    ('chat.requestBackground', W, 'the user\'s own message: WHITE with a DARK outline, since its text is the base foreground'),
    ('chat.requestBorder', D, ''),
    ('chat.requestBubbleBackground', W, ''),
    ('chat.requestBubbleHoverBackground', L, ''),
    ('chat.requestCodeBorder', D, ''),
    ('chat.slashCommandBackground', D, ''),
    ('chat.slashCommandForeground', W, ''),
    ('chat.avatarBackground', L, ''),
    ('chat.avatarForeground', B, ''),
    ('chat.checkpointSeparator', D, ''),
    ('chat.editedFileForeground', B, ''),
    ('chat.findMatchBackground', L, ''),
    ('chat.findMatchHighlightBackground', L, ''),
    ('chat.inputWorkingBorderColor1', A, ''), ('chat.inputWorkingBorderColor2', S, ''), ('chat.inputWorkingBorderColor3', L, ''),
    ('chat.linesAddedForeground', GREEN, ''),
    ('chat.linesRemovedForeground', RED, ''),
    ('chat.statusBackground', L, ''),
    ('chat.thinkingShimmer', D, ''),
    ('chat.dictationActiveMicGlow', A, ''), ('chat.voiceGlowBaseColor', A, ''),
    ('chat.voiceListeningGlow', A, ''), ('chat.voiceSpeakingGlow', A, ''),
    ('inlineChat.background', W, ''), ('inlineChat.foreground', B, ''), ('inlineChat.border', NONE, ''),
    ('inlineChatInput.background', W, ''), ('inlineChatInput.border', B, ''),
    ('inlineChatInput.focusBorder', A, ''), ('inlineChatInput.placeholderForeground', D, ''),
    ('agents.background', W, ''),
    ('agentsBadge.background', A, ''), ('agentsBadge.foreground', W, ''),
    ('agentsUnreadBadge.background', A, ''), ('agentsUnreadBadge.foreground', W, ''),
    ('agentsBottomPanel.border', NONE, ''), ('agentsCard.border', NONE, ''),
    ('agentsChatInput.background', W, ''), ('agentsChatInput.border', B, ''),
    ('agentsChatInput.focusBorder', A, ''), ('agentsChatInput.foreground', B, ''),
    ('agentsChatInput.placeholderForeground', D, ''),
    ('agentsGradient.tintColor', A, ''),
    ('agentsNewSessionButton.background', D, ''), ('agentsNewSessionButton.foreground', W, ''),
    ('agentsNewSessionButton.border', NONE, ''), ('agentsNewSessionButton.hoverBackground', B, ''),
    ('agentsPanel.background', W, ''), ('agentsPanel.foreground', B, ''), ('agentsPanel.border', NONE, ''),
    ('agentsUpdateButton.downloadedBackground', D, ''), ('agentsUpdateButton.downloadingBackground', D, ''),
    ('agentsVoice.speakingBackground', L, ''), ('agentsVoice.speakingForeground', B, ''),
    ('agentFeedbackEditorWidget.background', W, ''), ('agentFeedbackEditorWidget.border', NONE, ''),
    ('agentFeedbackInputWidget.border', B, ''),
    ('agentSessionReadIndicator.foreground', D, ''),
    ('agentSessionSelectedBadge.border', W, ''), ('agentSessionSelectedUnfocusedBadge.border', D, ''),
    ('agentStatusIndicator.background', L, ''),
    ('activeSessionView.background', W, ''), ('activeSessionView.foreground', B, ''),
    ('inactiveSessionView.background', W, ''), ('inactiveSessionView.foreground', D, ''),
]

# Two ids whose colour is read only for its alpha. Not painted, not derived, left to the platform by name.
OPACITY_IDS = ('editorUnnecessaryCode.opacity', 'minimap.foregroundOpacity')
# Ids the theme leaves unset on purpose, and why -- for --coverage, which would otherwise list them.
LEFT_UNSET = {
    'widget.shadow': 'a real shadow (§4)', 'scrollbar.shadow': 'set to NONE above',
    'editorStickyScroll.shadow': 'a real shadow (§4)', 'sideBarStickyScroll.shadow': 'a real shadow (§4)',
    'panelStickyScroll.shadow': 'a real shadow (§4)', 'diffEditor.unchangedRegionShadow': 'a real shadow (§4)',
    'inlineChat.shadow': 'a real shadow (§4)', 'listFilterWidget.shadow': 'a real shadow (§4)',
    'contrastBorder': 'a high-contrast theme type\'s outline; null in a light theme',
    'contrastActiveBorder': 'the same',
    # Null by default, and on Linux the workbench never draws the window border they colour (updateWindowBorder
    # returns early there). The window's edge is the compositor's: on COSMIC the gap is the rule (§5), and the
    # 2 px outline COSMIC draws around every window is its own -- measured 2026-09-20 on a native window and on
    # this one alike, and not a value a theme reaches.
    'window.activeBorder': 'null by default; the compositor owns the window edge',
    'window.inactiveBorder': 'the same',
}


# --- 3. the syntax colouring: CHOSEN, and labelled (§0c) --------------------------------------------
# What a token class LOOKS like is decided by tone and geometry, and the reasons are in the header.
# Each entry is (name, scopes, fg, fontStyle). fg None inherits the editor foreground.
TOKENS = [
    ('comments: DARK and italic. DARK on WHITE is Lc 79.0, over the body tier, so a comment is quieter and still read',
     ['comment', 'punctuation.definition.comment', 'comment.block.documentation'], D, 'italic'),
    ('keywords, storage and control flow: BLACK and bold -- weight, not hue',
     ['keyword', 'keyword.control', 'storage', 'storage.type', 'storage.modifier', 'keyword.operator.new',
      'keyword.operator.expression', 'keyword.operator.cast', 'keyword.operator.sizeof', 'keyword.operator.alignof',
      'keyword.operator.typeid', 'keyword.operator.alignas', 'keyword.operator.instanceof', 'keyword.operator.logical.python',
      'keyword.operator.wordlike', 'keyword.operator.noexcept', 'keyword.other.using', 'keyword.other.directive.using',
      'keyword.other.operator', 'entity.name.operator', 'constant.language', 'variable.language',
      'storage.modifier.import.java', 'storage.modifier.package.java', 'variable.language.wildcard.java',
      'meta.preprocessor', 'entity.name.function.preprocessor', 'meta.structure.dictionary.key.python'], B, 'bold'),
    ('operators and punctuation: the base text',
     ['keyword.operator', 'punctuation', 'meta.brace', 'meta.template.expression', 'meta.embedded', 'source.groovy.embedded',
      'string meta.image.inline.markdown', 'variable.legacy.builtin.python', 'entity.name.label',
      'keyword.operator.quantifier.regexp'], B, ''),
    ('literals -- strings, numbers, characters, regular expressions, units, colours: the kit\'s one hue, ACCENT, Lc 75.4 on WHITE',
     ['string', 'constant.numeric', 'constant.character', 'constant.other', 'string.regexp', 'constant.regexp',
      'keyword.other.unit', 'keyword.operator.plus.exponent', 'keyword.operator.minus.exponent', 'variable.other.enummember',
      'variable.other.constant', 'support.constant.property-value', 'support.constant.font-name', 'support.constant.media-type',
      'support.constant.media', 'constant.other.color.rgb-value', 'constant.other.rgb-value', 'support.constant.color',
      'meta.preprocessor.string', 'meta.preprocessor.numeric', 'constant.sha.git-rebase', 'markup.inline.raw', 'markup.raw',
      'support.constant.math', 'support.constant.dom', 'support.constant.json', 'constant.other.option'], A, ''),
    ('the structure inside a literal -- escapes, regexp groups and classes, template punctuation: the darker wine',
     ['constant.character.escape', 'punctuation.definition.template-expression.begin', 'punctuation.definition.template-expression.end',
      'punctuation.section.embedded', 'punctuation.definition.group.regexp', 'punctuation.definition.group.assertion.regexp',
      'punctuation.definition.character-class.regexp', 'punctuation.character.set.begin.regexp', 'punctuation.character.set.end.regexp',
      'keyword.operator.negation.regexp', 'support.other.parenthesis.regexp', 'constant.character.character-class.regexp',
      'constant.other.character-class.set.regexp', 'constant.other.character-class.regexp', 'constant.character.set.regexp',
      'keyword.operator.or.regexp', 'keyword.control.anchor.regexp'], S, ''),
    ('types, classes, interfaces, namespaces: the literal hue in bold',
     ['entity.name.type', 'entity.name.class', 'entity.name.namespace', 'entity.name.scope-resolution', 'entity.other.inherited-class',
      'support.type', 'support.class', 'entity.other.attribute', 'meta.type.cast.expr', 'meta.type.new.expr',
      'punctuation.separator.namespace.ruby', 'storage.type.numeric.go', 'storage.type.byte.go', 'storage.type.boolean.go',
      'storage.type.string.go', 'storage.type.uintptr.go', 'storage.type.error.go', 'storage.type.rune.go', 'storage.type.cs',
      'storage.type.generic.cs', 'storage.type.modifier.cs', 'storage.type.variable.cs', 'storage.type.annotation.java',
      'storage.type.generic.java', 'storage.type.java', 'storage.type.object.array.java', 'storage.type.primitive.array.java',
      'storage.type.primitive.java', 'storage.type.token.java', 'storage.type.groovy', 'storage.type.annotation.groovy',
      'storage.type.parameters.groovy', 'storage.type.generic.groovy', 'storage.type.object.array.groovy',
      'storage.type.primitive.array.groovy', 'storage.type.primitive.groovy'], A, 'bold'),
    ('functions, methods, members, attributes and property names: SELECT, Lc 85.8 -- read against BLACK by tone',
     ['entity.name.function', 'support.function', 'entity.name.method', 'support.constant.handlebars',
      'source.powershell variable.other.member', 'entity.name.operator.custom-literal', 'entity.other.attribute-name',
      'support.type.property-name', 'support.type.vendored.property-name', 'support.type.property-name.json',
      'meta.object-literal.key', 'source.css variable', 'source.coffee.embedded', 'support.function.git-rebase',
      'entity.other.attribute-name.class.css', 'source.css entity.other.attribute-name.class', 'entity.other.attribute-name.id.css',
      'entity.other.attribute-name.parent-selector.css', 'entity.other.attribute-name.parent.less',
      'source.css entity.other.attribute-name.pseudo-class', 'entity.other.attribute-name.pseudo-element.css',
      'source.css.less entity.other.attribute-name.id', 'entity.other.attribute-name.scss', 'entity.name.selector'], S, ''),
    ('variables and parameters: the base text',
     ['variable', 'variable.parameter', 'meta.definition.variable.name', 'support.variable', 'entity.name.variable',
      'constant.other.placeholder'], B, ''),
    ('tags in markup are structure: BLACK and bold, like keywords',
     ['entity.name.tag', 'punctuation.definition.tag', 'punctuation.section.embedded.begin.php',
      'punctuation.section.embedded.end.php'], B, 'bold'),
    ('markup: headings bold, emphasis by style, quotes DARK, links ACCENT and underlined (§3 keeps the underline)',
     ['markup.heading', 'punctuation.definition.heading', 'markup.bold', 'strong'], B, 'bold'),
    ('', ['markup.italic', 'emphasis'], None, 'italic'),
    ('', ['markup.underline'], None, 'underline'),
    ('', ['markup.strikethrough'], None, 'strikethrough'),
    ('', ['markup.quote'], D, 'italic'),
    ('', ['markup.underline.link', 'string.other.link', 'markup.link', 'constant.other.reference.link.markdown'], A, 'underline'),
    ('', ['punctuation.definition.list.begin.markdown', 'punctuation.definition.quote.begin.markdown', 'markup.list'], B, 'bold'),
    ('a diff is content, and its convention is realized: inserted is green, deleted is red -- at the ANSI text tier',
     ['markup.inserted', 'meta.diff.header.to-file'], GREEN, ''),
    ('', ['markup.deleted', 'meta.diff.header.from-file'], RED, ''),
    ('changed has no §3 hue: tone', ['markup.changed'], D, ''),
    ('', ['meta.diff.header', 'meta.diff.index'], B, 'bold'),
    ('', ['meta.diff.range', 'punctuation.definition.range.diff'], D, ''),
    ('invalid is an error: the meaning is present', ['invalid', 'invalid.illegal'], RED, ''),
    ('deprecated: still there, not to be used', ['invalid.deprecated'], D, 'strikethrough'),
]

SEMANTIC_TOKENS = {
    'comment': {'foreground': D, 'fontStyle': 'italic'},
    'keyword': {'foreground': B, 'fontStyle': 'bold'},
    'modifier': {'foreground': B, 'fontStyle': 'bold'},
    'operator': {'foreground': B},
    'string': {'foreground': A}, 'number': {'foreground': A}, 'regexp': {'foreground': A},
    'enumMember': {'foreground': A}, 'newOperator': {'foreground': B, 'fontStyle': 'bold'},
    'stringLiteral': {'foreground': A}, 'numberLiteral': {'foreground': A}, 'customLiteral': {'foreground': A},
    'type': {'foreground': A, 'fontStyle': 'bold'}, 'class': {'foreground': A, 'fontStyle': 'bold'},
    'interface': {'foreground': A, 'fontStyle': 'bold'}, 'enum': {'foreground': A, 'fontStyle': 'bold'},
    'struct': {'foreground': A, 'fontStyle': 'bold'}, 'typeParameter': {'foreground': A, 'fontStyle': 'bold'},
    'namespace': {'foreground': A, 'fontStyle': 'bold'},
    'function': {'foreground': S}, 'method': {'foreground': S}, 'macro': {'foreground': S},
    'decorator': {'foreground': S}, 'property': {'foreground': S}, 'member': {'foreground': S},
    'variable': {'foreground': B}, 'parameter': {'foreground': B}, 'label': {'foreground': B},
    'event': {'foreground': S},
    '*.deprecated': {'foreground': D, 'fontStyle': 'strikethrough'},
}


# --- 4. what the checker measures ------------------------------------------------------------------
# Text on ground, by id, with APCA's tier for what it carries and the reason (build/apca.py GUIDANCE):
# 75 for text a user reads at the 400 the platform renders, 60 where the CSS renders 700 or the text is
# a short label on a mark's ground, 30 for a mark. Both sides are read out of the committed theme.
PAIRS = [
    ('editor.foreground', 'editor.background', 75, 'body text in the editor, 400'),
    ('foreground', 'editor.background', 75, 'the base text'),
    ('descriptionForeground', 'editor.background', 75, 'secondary text'),
    ('disabledForeground', 'editor.background', 30, 'disabled text: a mark'),
    ('errorForeground', 'editor.background', 75, 'error text, read'),
    ('editorLineNumber.foreground', 'editorGutter.background', 75, 'line numbers'),
    ('editorLineNumber.activeForeground', 'editorGutter.background', 75, 'the current line number'),
    ('editorCursor.foreground', 'editor.background', 60, 'the caret: §2\'s own pair and its own floor'),
    ('editorWhitespace.foreground', 'editor.background', 30, 'rendered whitespace: a mark'),
    ('editorRuler.foreground', 'editor.background', 30, 'a column ruler: a mark'),
    ('editorIndentGuide.background1', 'editor.background', 30, 'an indent guide, if turned on: a mark'),
    ('editorError.foreground', 'editor.background', 30, 'the error squiggle: a mark'),
    ('editorWarning.foreground', 'editor.background', 30, 'the warning squiggle: a mark'),
    ('editorInfo.foreground', 'editor.background', 30, 'the info squiggle: a mark'),
    ('editorGutter.addedBackground', 'editorGutter.background', 30, 'the added-lines bar in the gutter'),
    ('editorGutter.deletedBackground', 'editorGutter.background', 30, 'the deleted-lines mark'),
    ('editorGutter.modifiedBackground', 'editorGutter.background', 30, 'the modified-lines bar'),
    ('editorCodeLens.foreground', 'editor.background', 75, 'a code lens is read'),
    ('editorInlayHint.foreground', 'editor.background', 75, 'an inlay hint is read'),
    ('editorGhostText.foreground', 'editor.background', 75, 'an inline suggestion is read before it is accepted'),
    ('editorLink.activeForeground', 'editor.background', 75, 'a link in the editor'),
    ('textLink.foreground', 'editor.background', 75, 'a link in rendered text'),
    ('editorBracketHighlight.foreground2', 'editor.background', 75, 'a bracket at depth 2'),
    ('editorBracketHighlight.foreground3', 'editor.background', 75, 'a bracket at depth 3'),
    ('editorBracketHighlight.unexpectedBracket.foreground', 'editor.background', 75, 'an unmatched bracket'),
    ('editorWidget.foreground', 'editorWidget.background', 75, 'the find widget'),
    ('editorSuggestWidget.foreground', 'editorSuggestWidget.background', 75, 'a suggestion row'),
    ('editorSuggestWidget.selectedForeground', 'editorSuggestWidget.selectedBackground', 75, 'the selected suggestion'),
    ('editorSuggestWidget.highlightForeground', 'editorSuggestWidget.background', 75, 'the matched letters of a suggestion'),
    ('editorHoverWidget.foreground', 'editorHoverWidget.background', 75, 'a hover'),
    ('editorActionList.focusForeground', 'editorActionList.focusBackground', 75, 'the focused code action'),
    ('peekViewTitleLabel.foreground', 'peekViewTitle.background', 75, 'the peek title on its ACCENT bar'),
    ('peekViewResult.fileForeground', 'peekViewResult.background', 75, 'a peek result'),
    ('peekViewResult.lineForeground', 'peekViewResult.background', 75, 'a peek result\'s line'),
    ('peekViewResult.selectionForeground', 'peekViewResult.selectionBackground', 75, 'the selected peek result'),
    ('sideBar.foreground', 'sideBar.background', 75, 'the sidebar\'s lists, 400'),
    ('sideBarTitle.foreground', 'sideBarTitle.background', 75, 'the view title, 11px/400 (measured)'),
    ('sideBarSectionHeader.foreground', 'sideBarSectionHeader.background', 60, 'a section header, 11px/700 (measured in workbench.desktop.main.css)'),
    ('panelSectionHeader.foreground', 'panelSectionHeader.background', 60, 'a panel section header, 11px/700'),
    ('list.activeSelectionForeground', 'list.activeSelectionBackground', 75, 'the selected row'),
    ('list.inactiveSelectionForeground', 'list.inactiveSelectionBackground', 75, 'the selected row of an unfocused list'),
    ('list.highlightForeground', 'sideBar.background', 75, 'filter matches on a row'),
    ('list.focusHighlightForeground', 'list.activeSelectionBackground', 75, 'filter matches on the selected row'),
    ('list.errorForeground', 'sideBar.background', 75, 'a file with errors'),
    ('list.warningForeground', 'sideBar.background', 75, 'a file with warnings'),
    ('list.deemphasizedForeground', 'sideBar.background', 75, 'a de-emphasised row'),
    ('gitDecoration.addedResourceForeground', 'sideBar.background', 75, 'an added file'),
    ('gitDecoration.deletedResourceForeground', 'sideBar.background', 75, 'a deleted file'),
    ('gitDecoration.ignoredResourceForeground', 'sideBar.background', 30, 'an ignored file: de-emphasised'),
    ('activityBar.foreground', 'activityBar.background', 30, 'an activity icon: a mark'),
    ('activityBar.inactiveForeground', 'activityBar.background', 30, 'an inactive activity icon'),
    ('activityBarBadge.foreground', 'activityBarBadge.background', 60, 'a badge count, 9px/600 (measured)'),
    ('activityErrorBadge.foreground', 'activityErrorBadge.background', 60, '§3\'s light legend on a destructive badge'),
    ('activityWarningBadge.foreground', 'activityWarningBadge.background', 60, '§3\'s dark legend on a warning badge'),
    ('badge.foreground', 'badge.background', 60, 'a count badge, 11px/400: a short label on DARK'),
    ('titleBar.activeForeground', 'titleBar.activeBackground', 75, 'the key window\'s title, at the 400 the platform renders'),
    ('titleBar.inactiveForeground', 'titleBar.inactiveBackground', 75, 'the non-key window\'s title'),
    ('commandCenter.foreground', 'commandCenter.background', 75, 'the command centre'),
    ('menubar.selectionForeground', 'menubar.selectionBackground', 75, 'the open menu\'s title'),
    ('menu.foreground', 'menu.background', 75, 'a menu item'),
    ('menu.selectionForeground', 'menu.selectionBackground', 75, 'the highlighted menu item'),
    ('tab.activeForeground', 'tab.activeBackground', 75, 'the active tab\'s label'),
    ('tab.inactiveForeground', 'tab.inactiveBackground', 75, 'an inactive tab\'s label'),
    ('tab.hoverForeground', 'tab.hoverBackground', 75, 'a hovered tab'),
    ('tab.unfocusedActiveForeground', 'tab.unfocusedActiveBackground', 75, 'the active tab of an unfocused group'),
    ('tab.activeBorderTop', 'editorGroupHeader.tabsBackground', 30, 'the active tab\'s bar against the strip'),
    ('breadcrumb.foreground', 'breadcrumb.background', 75, 'a breadcrumb'),
    ('breadcrumb.focusForeground', 'breadcrumb.background', 75, 'the focused breadcrumb'),
    ('panelTitle.activeForeground', 'panel.background', 75, 'the active panel title, 11px'),
    ('panelTitle.inactiveForeground', 'panel.background', 75, 'an inactive panel title'),
    ('terminal.foreground', 'terminal.background', 75, 'the terminal'),
    ('terminal.selectionForeground', 'terminal.selectionBackground', 75, 'selected text in the terminal -- §2\'s selection, reachable here'),
    ('terminalCursor.foreground', 'terminal.background', 60, 'the terminal cursor'),
    ('terminal.initialHintForeground', 'terminal.background', 75, 'the terminal\'s first-run hint'),
    ('statusBar.foreground', 'statusBar.background', 75, 'the status bar, 12px on the rule'),
    ('statusBar.debuggingForeground', 'statusBar.debuggingBackground', 75, 'the status bar while debugging'),
    ('statusBar.noFolderForeground', 'statusBar.noFolderBackground', 75, 'the status bar with no folder open'),
    ('statusBarItem.hoverForeground', 'statusBarItem.hoverBackground', 75, 'a hovered status item'),
    ('statusBarItem.prominentForeground', 'statusBarItem.prominentBackground', 75, 'a prominent status item'),
    ('statusBarItem.remoteForeground', 'statusBarItem.remoteBackground', 75, 'the remote indicator'),
    ('statusBarItem.errorForeground', 'statusBarItem.errorBackground', 75, '§3\'s legend on a destructive item'),
    ('statusBarItem.warningForeground', 'statusBarItem.warningBackground', 75, '§3\'s legend on a warning item'),
    ('statusBarItem.offlineForeground', 'statusBarItem.offlineBackground', 75, 'the offline item'),
    ('button.foreground', 'button.background', 75, 'the primary button, at 400'),
    ('button.secondaryForeground', 'button.secondaryBackground', 75, 'the secondary button'),
    ('extensionButton.prominentForeground', 'extensionButton.prominentBackground', 75, 'the Install button'),
    ('extensionButton.foreground', 'extensionButton.background', 75, 'an extension button'),
    ('input.foreground', 'input.background', 75, 'what the user types'),
    ('input.placeholderForeground', 'input.background', 75, 'a placeholder'),
    ('inputOption.activeForeground', 'inputOption.activeBackground', 30, 'a toggle that is on: a glyph'),
    ('inputValidation.errorForeground', 'inputValidation.errorBackground', 75, '§3\'s legend on a destructive message'),
    ('inputValidation.warningForeground', 'inputValidation.warningBackground', 75, '§3\'s legend on a warning message'),
    ('inputValidation.infoForeground', 'inputValidation.infoBackground', 75, 'an informational message: tone'),
    ('dropdown.foreground', 'dropdown.background', 75, 'a dropdown'),
    ('checkbox.foreground', 'checkbox.background', 30, 'the tick: a glyph'),
    ('radio.activeForeground', 'radio.activeBackground', 30, 'the selected radio: a glyph'),
    ('quickInput.foreground', 'quickInput.background', 75, 'the command palette'),
    ('quickInputList.focusForeground', 'quickInputList.focusBackground', 75, 'the focused palette row'),
    ('pickerGroup.foreground', 'quickInput.background', 75, 'a palette group label'),
    ('keybindingLabel.foreground', 'keybindingLabel.background', 60, 'a key cap, 11px'),
    ('notifications.foreground', 'notifications.background', 75, 'a notification'),
    ('notificationCenterHeader.foreground', 'notificationCenterHeader.background', 75, 'the notification centre header'),
    ('notificationLink.foreground', 'notifications.background', 75, 'a link in a notification'),
    ('notificationsWarningIcon.foreground', 'notifications.background', 30, 'the warning icon: a mark'),
    ('settings.headerForeground', 'editor.background', 75, 'a settings header'),
    ('settings.modifiedItemIndicator', 'editor.background', 30, 'the modified-setting bar: a mark'),
    ('walkthrough.stepTitle.foreground', 'welcomePage.background', 75, 'a walkthrough title'),
    ('debugConsole.errorForeground', 'panel.background', 75, 'an error in the debug console'),
    ('debugConsole.warningForeground', 'panel.background', 75, 'a warning in the debug console'),
    ('debugConsole.infoForeground', 'panel.background', 75, 'an info line in the debug console'),
    ('debugView.exceptionLabelForeground', 'debugView.exceptionLabelBackground', 75, 'the exception label'),
    ('debugView.stateLabelForeground', 'debugView.stateLabelBackground', 75, 'the debug state label'),
    ('debugIcon.breakpointForeground', 'editorGutter.background', 30, 'a breakpoint: a mark'),
    ('debugIcon.startForeground', 'debugToolBar.background', 30, 'the start glyph on the toolbar'),
    ('debugIcon.stopForeground', 'debugToolBar.background', 30, 'the stop glyph'),
    ('debugIcon.stepOverForeground', 'debugToolBar.background', 30, 'a step glyph'),
    ('testing.iconPassed', 'sideBar.background', 30, 'a passed test: a mark'),
    ('testing.iconFailed', 'sideBar.background', 30, 'a failed test: a mark'),
    ('testing.message.error.badgeForeground', 'testing.message.error.badgeBackground', 75, 'the test error badge'),
    ('diffEditor.unchangedRegionForeground', 'diffEditor.unchangedRegionBackground', 75, 'a collapsed region\'s label'),
    ('chat.slashCommandForeground', 'chat.slashCommandBackground', 75, 'a slash command chip'),
    ('chat.avatarForeground', 'chat.avatarBackground', 60, 'an avatar initial: a glyph'),
    ('chat.linesAddedForeground', 'editor.background', 75, 'a lines-added count'),
    ('charts.red', 'editor.background', 75, 'a chart series, read against the field'),
    ('charts.orange', 'editor.background', 75, 'the orange chart series'),
    ('scmGraph.foreground5', 'sideBar.background', 30, 'the fifth graph line: a mark'),
    ('markdownAlert.warning.foreground', 'editor.background', 75, 'a markdown warning alert\'s title'),
    ('editorMarkerNavigationWarning.background', 'editor.background', 30, 'the warning navigation frame: a mark'),
    ('editorUnicodeHighlight.border', 'editor.background', 30, 'the confusable-character box: a mark'),
]

# Fills under text that keeps its own colour, and the text's tier on them. Tier 60 is APCA's for a
# short block, a headline or 16px/700; here it is the platform's ceiling, for the reason in the header:
# the editor cannot recolour selected text, so no fill behind BLACK code can be both dE 17.1 from WHITE
# and a body ground. Recorded, measured, not hidden.
HIGHLIGHTS = [
    ('editor.selectionBackground', 'editor.foreground', 'the editor selection'),
    ('editor.inactiveSelectionBackground', 'editor.foreground', 'the selection of an unfocused editor'),
    ('selection.background', 'foreground', 'text selected outside the editor'),
    ('list.hoverBackground', 'list.hoverForeground', 'the hovered row: a tint, because extension webviews use the id as one'),
    ('editorStickyScrollHover.background', 'editor.foreground', 'a hovered sticky line'),
    ('terminalStickyScrollHover.background', 'terminal.foreground', 'a hovered sticky terminal line'),
    ('peekViewResult.matchHighlightBackground', 'peekViewResult.fileForeground', 'a match in a peek result'),
    ('editorHoverWidget.statusBarBackground', 'editorHoverWidget.foreground', 'the hover\'s footer'),
    ('quickInputTitle.background', 'quickInput.foreground', 'the palette\'s title row'),
    ('multiDiffEditor.headerBackground', 'editor.foreground', 'a file header in a multi-diff'),
    ('editor.stackFrameHighlightBackground', 'editor.foreground', 'the line being executed'),
    ('editor.inlineValuesBackground', 'editor.inlineValuesForeground', 'an inline debug value'),
    ('diffEditor.insertedLineBackground', 'editor.foreground', 'code on an inserted line'),
    ('diffEditor.removedLineBackground', 'editor.foreground', 'code on a removed line'),
    ('mergeEditor.conflictingLines.background', 'editor.foreground', 'code on a conflicting line'),
    ('editorMarkerNavigationError.headerBackground', 'editor.foreground', 'the error navigation header'),
    ('editorMarkerNavigationWarning.headerBackground', 'editor.foreground', 'the warning navigation header'),
    ('editorMarkerNavigationInfo.headerBackground', 'editor.foreground', 'the info navigation header'),
    ('testing.coveredBackground', 'editor.foreground', 'covered code'),
    ('testing.uncoveredBackground', 'editor.foreground', 'uncovered code'),
    ('merge.currentHeaderBackground', 'editor.foreground', 'a legacy conflict header'),
    ('chat.findMatchBackground', 'foreground', 'a find match in chat'),
]

# Two grounds that touch and carry information. OKLab dE against SURFACE_FLOOR, never Lc (§0e).
ADJACENT = [
    ('activityBar.background', 'sideBar.background', 'the activity bar against the sidebar'),
    ('activityBar.activeBackground', 'activityBar.background', 'the active activity item on its bar'),
    ('activityBarBadge.background', 'activityBar.background', 'a badge on the activity bar'),
    ('sideBarSectionHeader.background', 'sideBar.background', 'a section header on the sidebar'),
    ('list.activeSelectionBackground', 'sideBar.background', 'the selected row against the rows around it'),
    ('list.hoverBackground', 'sideBar.background', 'the hovered row'),
    ('badge.background', 'sideBar.background', 'a count badge on the sidebar'),
    ('editorGroupHeader.tabsBackground', 'tab.activeBackground', 'the tab strip against the active tab'),
    ('editorGroupHeader.tabsBackground', 'editor.background', 'the tab strip against the editor'),
    ('tab.hoverBackground', 'tab.inactiveBackground', 'a hovered tab beside its neighbours'),
    ('editorGroup.emptyBackground', 'editor.background', 'an empty group beside a full one'),
    ('titleBar.activeBackground', 'editorGroupHeader.tabsBackground', 'the key titlebar against the tab strip'),
    ('titleBar.inactiveBackground', 'editorGroupHeader.tabsBackground', 'the non-key titlebar against the tab strip'),
    ('titleBar.activeBackground', 'titleBar.inactiveBackground', 'key against non-key: the state the titlebar carries'),
    ('commandCenter.background', 'titleBar.activeBackground', 'the command centre on the key titlebar'),
    ('menu.background', 'titleBar.activeBackground', 'a menu dropping from the key titlebar'),
    ('menu.selectionBackground', 'menu.background', 'the highlighted item'),
    ('statusBar.background', 'editor.background', 'the rule under the editor'),
    ('statusBar.background', 'panel.background', 'the rule under the panel'),
    ('statusBar.debuggingBackground', 'editor.background', 'the rule while debugging'),
    ('statusBarItem.hoverBackground', 'statusBar.background', 'a hovered item on the rule'),
    ('statusBarItem.remoteBackground', 'statusBar.background', 'the remote indicator on the rule'),
    ('editor.selectionBackground', 'editor.background', 'the selection on the field'),
    ('scrollbarSlider.background', 'editor.background', 'the slider on the field'),
    ('minimapSlider.background', 'minimap.background', 'the minimap slider'),
    ('terminal.selectionBackground', 'terminal.background', 'the terminal selection'),
    ('terminalCommandDecoration.defaultBackground', 'terminal.background', 'a command decoration'),
    ('button.background', 'notifications.background', 'the primary button on a notification'),
    ('button.secondaryBackground', 'notifications.background', 'the secondary button on a notification'),
    ('inputOption.activeBackground', 'input.background', 'a toggle that is on, in the input'),
    ('inputValidation.errorBackground', 'input.background', 'an error message under an input'),
    ('inputValidation.warningBackground', 'input.background', 'a warning message under an input'),
    ('inputValidation.infoBackground', 'input.background', 'an info message under an input'),
    ('quickInputList.focusBackground', 'quickInput.background', 'the focused palette row'),
    ('quickInputTitle.background', 'quickInput.background', 'the palette title row'),
    ('editorSuggestWidget.selectedBackground', 'editorSuggestWidget.background', 'the selected suggestion'),
    ('editorActionList.focusBackground', 'editorActionList.background', 'the focused code action'),
    ('peekViewTitle.background', 'peekViewEditor.background', 'the peek title against its editor'),
    ('peekViewResult.selectionBackground', 'peekViewResult.background', 'the selected peek result'),
    ('diffEditor.insertedLineBackground', 'editor.background', 'an inserted line on the field'),
    ('diffEditor.removedLineBackground', 'editor.background', 'a removed line on the field'),
    ('diffEditor.insertedLineBackground', 'diffEditor.removedLineBackground', 'an inserted line under a removed one'),
    ('diffEditor.unchangedRegionBackground', 'editor.background', 'a collapsed region on the field'),
    ('mergeEditor.conflictingLines.background', 'editor.background', 'a conflicting line on the field'),
    ('testing.coveredBackground', 'editor.background', 'covered code on the field'),
    ('testing.uncoveredBackground', 'editor.background', 'uncovered code on the field'),
    ('keybindingLabel.background', 'quickInput.background', 'a key cap on the palette'),
    ('notificationCenterHeader.background', 'notifications.background', 'the notification centre header'),
    ('statusBarItem.errorBackground', 'statusBar.background', 'a destructive item on the rule'),
    ('statusBarItem.warningBackground', 'statusBar.background', 'a warning item on the rule'),
    ('debugToolBar.background', 'editor.background', 'the debug toolbar over the editor'),
    ('welcomePage.tileHoverBackground', 'welcomePage.background', 'a hovered tile'),
    ('chat.slashCommandBackground', 'editor.background', 'a slash command chip'),
]
# Joins the theme leaves unmarked, and why. The first is the shape of this surface: three fields that
# each carry read text at 400, which on this platform makes each of them WHITE; §5 permits no line
# thinner than the rule and the platform draws none wider than 1 px, so the join is unmarked and the
# content marks it. The status bar is the one rule drawn.
ADJACENT_EXEMPT = {
    ('sideBar.background', 'editor.background'): 'WHITE meets WHITE: both carry read text at 400 (the header)',
    ('panel.background', 'editor.background'): 'the same, at the panel',
    ('tab.activeBackground', 'tab.inactiveBackground'): 'the tabs are one WHITE band; the active one carries the ACCENT bar and a BLACK label against DARK',
    ('editorWidget.background', 'editor.background'): 'a floating widget is delineated by its shadow (§4)',
    ('editorSuggestWidget.background', 'editor.background'): 'the same',
    ('editorHoverWidget.background', 'editor.background'): 'the same',
    ('quickInput.background', 'editor.background'): 'the same',
    ('notifications.background', 'editor.background'): 'the same',
    ('menu.background', 'editor.background'): 'the same',
    ('editorStickyScroll.background', 'editor.background'): 'the same',
    ('peekViewResult.background', 'peekViewEditor.background'): 'two fields inside one ACCENT frame; the content tells them apart',
    ('minimapSlider.background', 'minimapSlider.hoverBackground'): 'the slider does not change on hover: an opaque DARK band would hide the minimap under it',
    ('button.hoverBackground', 'button.background'): 'hover is a change over time, not a boundary: §2\'s own exempt pair (ACCENT/SELECT, dE 11.8), which worksafe/firefox/ uses for the same hover',
    ('input.background', 'editorWidget.background'): 'the well is edged by its own outline (input.border, BLACK), not by a tone change',
}
# The two legend values may appear only as the text of these pairs (§3): a light legend on DESTRUCTIVE or
# SUCCESS, a dark one on WARNING. Anywhere else is a defect the checker fails.
LEGEND_PAIRS = {
    'activityErrorBadge.foreground': 'activityErrorBadge.background',
    'activityWarningBadge.foreground': 'activityWarningBadge.background',
    'inputValidation.errorForeground': 'inputValidation.errorBackground',
    'inputValidation.warningForeground': 'inputValidation.warningBackground',
    'statusBarItem.errorForeground': 'statusBarItem.errorBackground',
    'statusBarItem.errorHoverForeground': 'statusBarItem.errorHoverBackground',
    'statusBarItem.warningForeground': 'statusBarItem.warningBackground',
    'statusBarItem.warningHoverForeground': 'statusBarItem.warningHoverBackground',
    'debugView.exceptionLabelForeground': 'debugView.exceptionLabelBackground',
    'testing.message.error.badgeForeground': 'testing.message.error.badgeBackground',
    'inlineEdit.gutterIndicator.successfulForeground': 'inlineEdit.gutterIndicator.successfulBackground',
}
# An id given a semantic, ANSI, tint or chart value should say so in its name. This is a note, not a
# gate -- the role table assigns by hand, as Windows' does -- and it catches the slip where a chrome id is
# handed a signal.
MEANING = re.compile(r'error|warning|success|fail|pass|delet|remov|insert|added|untracked|cover|conflict|ansi|'
                     r'chart|invalid|breakpoint|stop|start|restart|continue|running|resolved|caution|tip|'
                     r'exception|unexpected|uncovered|alert|linesAdded|linesRemoved|additions|deletions|'
                     r'original|modified|disconnect|noMatches|unicodeHighlight|testing\.peek|handled', re.I)


# --- 5. the platform's defaults, recorded --------------------------------------------------------------
# Read off the installed build's workbench.desktop.main.js -- `se("id",{light:...,dark:...},...)` is the
# minified registerColor, the terminal slots are a table, and the git extension contributes its own --
# on 2026-09-20 from Flatpak com.visualstudio.code 1.137.0 (commit 645f29cc). Every id below defaults, in
# a light theme, to a literal inside a pole or to one of §3's two reserved values, so leaving it unset
# paints a Microsoft colour. The theme must decide each. `--coverage` re-reads the live build.
DEFAULTS_IN_A_POLE = (  # 203 ids
    'activityBarBadge.background', 'activityErrorBadge.background', 'activityWarningBadge.background',
    'agentsBadge.background', 'agentsChatInput.focusBorder', 'agentsGradient.tintColor',
    'agentsUnreadBadge.background', 'banner.iconForeground', 'button.background', 'charts.blue',
    'charts.green', 'charts.orange', 'charts.red', 'charts.yellow', 'chat.dictationActiveMicGlow',
    'chat.editedFileForeground', 'chat.findMatchHighlightBackground', 'chat.inputWorkingBorderColor1',
    'chat.linesAddedForeground', 'chat.linesRemovedForeground', 'chat.requestCodeBorder',
    'chat.slashCommandForeground', 'chat.voiceGlowBaseColor', 'commentsView.unresolvedIcon',
    'debugConsole.errorForeground', 'debugConsole.infoForeground', 'debugConsole.warningForeground',
    'debugExceptionWidget.border', 'debugIcon.breakpointCurrentStackframeForeground',
    'debugIcon.breakpointForeground', 'debugIcon.breakpointStackframeForeground',
    'debugIcon.continueForeground', 'debugIcon.disconnectForeground', 'debugIcon.pauseForeground',
    'debugIcon.restartForeground', 'debugIcon.startForeground', 'debugIcon.stepBackForeground',
    'debugIcon.stepIntoForeground', 'debugIcon.stepOutForeground', 'debugIcon.stepOverForeground',
    'debugIcon.stopForeground', 'debugTokenExpression.boolean', 'debugTokenExpression.error',
    'debugTokenExpression.number', 'debugTokenExpression.string', 'debugTokenExpression.type',
    'debugView.exceptionLabelBackground', 'debugView.valueChangedHighlight',
    'diffEditor.insertedTextBackground', 'diffEditor.moveActive.border',
    'diffEditor.removedTextBackground', 'editor.findMatchHighlightBackground',
    'editor.inlineValuesBackground', 'editor.rangeHighlightBackground',
    'editor.stackFrameHighlightBackground', 'editor.symbolHighlightBackground',
    'editor.wordHighlightStrongBackground', 'editorActionList.focusBackground',
    'editorActiveLineNumber.foreground', 'editorBracketHighlight.foreground1',
    'editorBracketHighlight.foreground2', 'editorBracketHighlight.foreground3',
    'editorBracketMatch.background', 'editorCommentsWidget.unresolvedBorder', 'editorError.foreground',
    'editorGutter.addedBackground', 'editorGutter.deletedBackground', 'editorGutter.modifiedBackground',
    'editorHoverWidget.highlightForeground', 'editorInfo.foreground', 'editorLightBulb.foreground',
    'editorLightBulbAi.foreground', 'editorLightBulbAutoFix.foreground',
    'editorLineNumber.activeForeground', 'editorOverviewRuler.findMatchForeground',
    'editorOverviewRuler.infoForeground', 'editorOverviewRuler.warningForeground',
    'editorSuggestWidget.highlightForeground', 'editorUnicodeHighlight.border',
    'editorWarning.foreground', 'errorForeground', 'extensionBadge.remoteBackground',
    'extensionButton.prominentBackground', 'extensionIcon.preReleaseForeground',
    'extensionIcon.starForeground', 'extensionIcon.verifiedForeground', 'focusBorder',
    'gitDecoration.conflictingResourceForeground', 'gitDecoration.deletedResourceForeground',
    'gitDecoration.modifiedResourceForeground', 'gitDecoration.renamedResourceForeground',
    'gitDecoration.stageDeletedResourceForeground', 'gitDecoration.stageModifiedResourceForeground',
    'gitDecoration.submoduleResourceForeground', 'gitDecoration.untrackedResourceForeground',
    'inlineChatInput.focusBorder', 'inlineEdit.gutterIndicator.primaryBorder',
    'inlineEdit.gutterIndicator.successfulBackground', 'inlineEdit.gutterIndicator.successfulBorder',
    'inlineEdit.originalBorder', 'inputOption.activeBorder', 'inputValidation.errorBorder',
    'inputValidation.infoBorder', 'inputValidation.warningBorder', 'list.activeSelectionBackground',
    'list.errorForeground', 'list.filterMatchBackground', 'list.focusOutline',
    'list.highlightForeground', 'list.invalidItemForeground', 'list.warningForeground',
    'listFilterWidget.noMatchesOutline', 'markdownAlert.caution.foreground',
    'markdownAlert.note.foreground', 'markdownAlert.tip.foreground', 'markdownAlert.warning.foreground',
    'mcpIcon.starForeground', 'menu.selectionBackground', 'mergeEditor.change.background',
    'mergeEditor.change.word.background', 'mergeEditor.changeBase.word.background',
    'mergeEditor.conflict.unhandled.minimapOverViewRuler',
    'mergeEditor.conflict.unhandledFocused.border', 'mergeEditor.conflict.unhandledUnfocused.border',
    'mergeEditor.conflictingLines.background', 'minimap.findMatchHighlight', 'minimap.infoHighlight',
    'minimap.warningHighlight', 'minimapGutter.addedBackground', 'minimapGutter.deletedBackground',
    'minimapGutter.modifiedBackground', 'notebook.cellInsertionIndicator', 'notebook.focusedCellBorder',
    'notebook.focusedEditorBorder', 'notebookEditorOverviewRuler.runningCellForeground',
    'notebookStatusErrorIcon.foreground', 'notebookStatusSuccessIcon.foreground',
    'notificationLink.foreground', 'notificationsErrorIcon.foreground',
    'notificationsInfoIcon.foreground', 'notificationsWarningIcon.foreground',
    'panelTitleBadge.background', 'peekView.border', 'peekViewEditor.matchHighlightBackground',
    'peekViewResult.matchHighlightBackground', 'peekViewResult.selectionBackground',
    'pickerGroup.foreground', 'ports.iconRunningProcessForeground', 'problemsErrorIcon.foreground',
    'problemsInfoIcon.foreground', 'problemsWarningIcon.foreground', 'radio.activeBorder',
    'sash.hoverBorder', 'scmGraph.foreground1', 'scmGraph.foreground3',
    'scmGraph.historyItemBaseRefColor', 'scmGraph.historyItemHoverDeletionsForeground',
    'scmGraph.historyItemRefColor', 'settings.focusedRowBorder', 'statusBar.background',
    'statusBar.debuggingBackground', 'statusBarItem.offlineBackground',
    'statusBarItem.remoteBackground', 'symbolIcon.classForeground', 'symbolIcon.enumeratorForeground',
    'symbolIcon.enumeratorMemberForeground', 'symbolIcon.eventForeground', 'symbolIcon.fieldForeground',
    'symbolIcon.interfaceForeground', 'symbolIcon.variableForeground', 'tab.activeModifiedBorder',
    'tab.selectedBorderTop', 'terminal.ansiBlue', 'terminal.ansiBrightBlue', 'terminal.ansiBrightGreen',
    'terminal.ansiBrightRed', 'terminal.ansiBrightYellow', 'terminal.ansiGreen', 'terminal.ansiRed',
    'terminal.ansiYellow', 'terminal.findMatchHighlightBackground',
    'terminalCommandDecoration.errorBackground', 'terminalCommandDecoration.successBackground',
    'terminalOverviewRuler.findMatchForeground', 'terminalSymbolIcon.argumentForeground',
    'terminalSymbolIcon.flagForeground', 'terminalSymbolIcon.optionForeground',
    'terminalSymbolIcon.optionValueForeground', 'testing.coveredBackground', 'testing.iconErrored',
    'testing.iconFailed', 'testing.iconPassed', 'testing.message.error.badgeBackground',
    'testing.message.error.badgeBorder', 'testing.messagePeekBorder', 'testing.peekBorder',
    'testing.runAction', 'testing.uncoveredBackground', 'textBlockQuote.border',
    'textLink.activeForeground', 'textLink.foreground', 'textPreformat.foreground',
    'welcomePage.progress.foreground',
)

DEFAULTS_RESERVED = (  # 96 ids
    'activeSessionView.background', 'activityBar.activeBorder', 'activityBar.dropBorder',
    'activityBar.foreground', 'activityErrorBadge.foreground', 'activityWarningBadge.foreground',
    'agentsChatInput.background', 'agentsNewSessionButton.background', 'agentsPanel.background',
    'banner.foreground', 'breadcrumb.background', 'chat.thinkingShimmer', 'checkbox.background',
    'dropdown.background', 'editor.background', 'editor.compositionBorder',
    'editor.inlineValuesForeground', 'editorActionList.focusForeground',
    'editorBracketHighlight.foreground4', 'editorBracketHighlight.foreground5',
    'editorBracketHighlight.foreground6', 'editorBracketPairGuide.activeBackground1',
    'editorBracketPairGuide.activeBackground2', 'editorBracketPairGuide.activeBackground3',
    'editorBracketPairGuide.activeBackground4', 'editorBracketPairGuide.activeBackground5',
    'editorBracketPairGuide.activeBackground6', 'editorBracketPairGuide.background1',
    'editorBracketPairGuide.background2', 'editorBracketPairGuide.background3',
    'editorBracketPairGuide.background4', 'editorBracketPairGuide.background5',
    'editorBracketPairGuide.background6', 'editorCursor.foreground',
    'editorGroupHeader.noTabsBackground', 'editorGutter.background',
    'editorIndentGuide.activeBackground2', 'editorIndentGuide.activeBackground3',
    'editorIndentGuide.activeBackground4', 'editorIndentGuide.activeBackground5',
    'editorIndentGuide.activeBackground6', 'editorIndentGuide.background2',
    'editorIndentGuide.background3', 'editorIndentGuide.background4', 'editorIndentGuide.background5',
    'editorIndentGuide.background6', 'editorMarkerNavigation.background',
    'editorMultiCursor.primary.foreground', 'editorMultiCursor.secondary.foreground',
    'editorPane.background', 'editorStickyScroll.background', 'editorStickyScrollGutter.background',
    'editorSuggestWidget.selectedForeground', 'extensionIcon.privateForeground',
    'inlineChatInput.background', 'input.background', 'inputOption.activeForeground',
    'list.activeSelectionForeground', 'menu.background', 'menu.selectionForeground',
    'multiDiffEditor.background', 'notebook.editorBackground', 'panel.background',
    'panelStickyScroll.background', 'peekViewTitleLabel.foreground', 'quickInputList.focusForeground',
    'radio.activeForeground', 'scmGraph.historyItemHoverLabelForeground', 'settings.checkboxBackground',
    'settings.dropdownBackground', 'settings.numberInputBackground', 'settings.textInputBackground',
    'statusBar.debuggingForeground', 'statusBar.focusBorder', 'statusBar.foreground',
    'statusBar.noFolderForeground', 'statusBarItem.errorHoverForeground', 'statusBarItem.focusBorder',
    'statusBarItem.hoverForeground', 'statusBarItem.offlineHoverForeground',
    'statusBarItem.prominentForeground', 'statusBarItem.prominentHoverForeground',
    'statusBarItem.remoteHoverForeground', 'statusBarItem.warningHoverForeground', 'strongForeground',
    'surface.background', 'tab.activeBackground', 'tab.unfocusedActiveBackground', 'terminal.ansiBlack',
    'terminalCommandDecoration.defaultBackground', 'testing.message.error.badgeForeground',
    'textPreformat.background', 'textSeparator.foreground', 'walkthrough.stepTitle.foreground',
    'welcomePage.progress.background', 'welcomePage.tileBorder',
)
MUST_SET = tuple(sorted(set(DEFAULTS_IN_A_POLE) | set(DEFAULTS_RESERVED)))
RECORDED_ON, RECORDED_FROM = '2026-09-20', 'Flatpak com.visualstudio.code 1.137.0 (645f29cc)'


# --- 6. reading and writing ----------------------------------------------------------------------------
_JSONC_STRIP = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.S)


def jsonc(text):
    """VS Code reads its theme and settings files as JSON with comments and trailing commas; so does this."""
    s = _JSONC_STRIP.sub(lambda m: m.group(1) or '', text)
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    return json.loads(s)


THEME_HEADER = """// Remainder for VS Code -- the colour theme. AUTHORITY.md is the authority.
// GENERATED by build/vscode.py --write. Do not hand-edit: edit poles.json, the derivation, or the role
// table in build/vscode.py, and regenerate. build/vscode.py fails if this file is not what it produces.
//
// Every value is one of §2's seven, §3's three and their two legend values, the sixteen ANSI slots from
// build/cosmic.py, three pale semantic tints, one chart orange solved from the platform's own exemplar,
// two slots of the COSMIC neutral ladder, or #00000000 -- which is `transparent`, as VS Code spells it.
// Nothing here is a blend and nothing carries an alpha but that one.
//
// The shape: read text sits on WHITE; LIGHT carries the icon strips, the tab strip and the headers
// the platform renders bold; the key titlebar is ACCENT; selection is SELECT carrying WHITE wherever the
// platform lets the text follow the ground, and LIGHT where it does not (the editor); hover is a LIGHT tint,
// because extension webviews paint list.hoverBackground alone and let the text inherit `foreground`;
// the caret is CURSOR; the status bar is the rule at the 22 px the platform fixes, half its 44 dp width.
// No line is drawn between surfaces.
"""


def _theme_text():
    colors = {}
    for cid, hx, _ in COLORS:
        if cid in colors and colors[cid] != hx:
            raise SystemExit(f'{cid} is assigned twice, differently: {colors[cid]} and {hx}')
        colors[cid] = hx
    tokens = []
    for name, scopes, fg, style in TOKENS:
        settings = {}
        if fg:
            settings['foreground'] = fg
        if style:
            settings['fontStyle'] = style
        entry = {'scope': list(scopes), 'settings': settings}
        if name:
            entry = {'name': name, **entry}
        tokens.append(entry)
    body = {
        '$schema': 'vscode://schemas/color-theme',
        'name': 'Remainder',
        'type': 'light',
        'semanticHighlighting': True,
        'colors': colors,
        'tokenColors': tokens,
        'semanticTokenColors': SEMANTIC_TOKENS,
    }
    return THEME_HEADER + json.dumps(body, indent=2, ensure_ascii=False) + '\n'


def write():
    os.makedirs(os.path.dirname(THEME), exist_ok=True)
    text = _theme_text()
    with open(THEME, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'wrote {os.path.relpath(THEME, ROOT)}  ({len(text)} bytes, {len(jsonc(text)["colors"])} colours)')


HEX6 = re.compile(r'#[0-9A-Fa-f]{6}\b')


def _norm(v):
    return v.upper() if isinstance(v, str) else v


# --- 7. the checker ---------------------------------------------------------------------------------------
def check():
    if not os.path.isfile(THEME):
        print('vscode: worksafe/vscode/remainder/themes/remainder-color-theme.json is not committed -- run --write')
        return False
    reg, bad, notes = authored(), 0, []
    on_disk = open(THEME, encoding='utf-8').read()
    same = on_disk == _theme_text()
    print(f'  {os.path.relpath(THEME, ROOT)}')
    print(f'    {"matches the generator" if same else "DIFFERS FROM THE GENERATOR -- run build/vscode.py --write"}')
    bad += not same
    try:
        man = json.load(open(MANIFEST))
        path = man['contributes']['themes'][0]['path']
        ui = man['contributes']['themes'][0]['uiTheme']
        okm = os.path.normpath(os.path.join(EXT, path)) == os.path.normpath(THEME) and ui == 'vs'
        print(f'  package.json: {man["publisher"]}.{man["name"]} {man["version"]}, uiTheme {ui}, path {path}'
              f'{"" if okm else "  -- DOES NOT POINT AT THE THEME, or is not a light theme"}')
        bad += not okm
    except Exception as e:
        notes.append(f'package.json: {e}'); bad += 1

    theme = jsonc(on_disk)
    colors = {k: _norm(v) for k, v in theme['colors'].items()}

    # (a) every value is a value some ladder derived; the one alpha admitted is #00000000
    seen = {}
    for cid, hx in colors.items():
        seen.setdefault(hx, []).append(cid)
    print(f'\n  colours: {len(colors)} ids on {len(seen)} distinct values')
    for hx, ids in sorted(seen.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        name, note = reg.get(hx), ''
        if name is None:
            if re.fullmatch(r'#[0-9A-F]{8}', hx) and hx[7:] != '00':
                note = 'ALPHA: a mixed value is not an authored value'
            else:
                note = 'NOT DERIVED BY ANY LADDER'
            bad += 1
        elif name == 'NONE':
            note = 'not painted'
        elif not is_content(name) and not P.clear(hx):
            note = 'POLE: chrome must clear every pole'; bad += 1
        fam, gap, req = P.clearance(hx) if hx != NONE else ('', 0, 0)
        tag = ('' if hx == NONE else 'reserved (§3)' if P.reserved(hx) else
               'neutral' if not P.readable(hx) else f'{gap:5.1f}/{req:4.1f} {fam}')
        print(f'    {hx:10} x{len(ids):<4} {str(name):24} {tag:26} {note}')
    for cid in OPACITY_IDS:
        if cid in colors:
            notes.append(f'{cid} is an opacity, not a colour, and the theme painted it'); bad += 1

    # (b) the platform's defaults, recorded: every id that would otherwise paint a pole or a reserved literal
    missing = [cid for cid in MUST_SET if cid not in colors]
    print(f'\n  the platform\'s light defaults ({RECORDED_FROM}, {RECORDED_ON}): {len(MUST_SET)} ids default to a '
          f'pole or a reserved literal; the theme decides {len(MUST_SET) - len(missing)}')
    for cid in missing:
        notes.append(f'{cid}: unset, and its light default is a pole or a reserved literal'); bad += 1

    # (c) the legend values, only where §3 permits them
    legend_of = {SUCCESS: LEGEND_LIGHT, DESTRUCTIVE: LEGEND_LIGHT, WARNING: LEGEND_DARK}
    for cid, hx in colors.items():
        if hx in (LEGEND_LIGHT, LEGEND_DARK):
            ground = colors.get(LEGEND_PAIRS.get(cid, ''), None)
            if ground is None or legend_of.get(ground) != hx:
                notes.append(f'{cid}: §3 reserves {hx} for legend on a semantic field, and this is not one'); bad += 1

    # (d) the pairs, measured
    def val(cid):
        return colors.get(cid)
    print(f'\n  pairs the theme states ({len(PAIRS)}; APCA Lc, signed):')
    for t, g, floor, why in PAIRS:
        tv, gv = val(t), val(g)
        if tv is None or gv is None or tv == NONE or gv == NONE:
            notes.append(f'{t} on {g}: {"unset" if tv is None or gv is None else "unpainted"}'); bad += 1
            continue
        lc = apca.lc(tv, gv)
        okay = abs(lc) >= floor
        capped = not okay and tv in CAPS and abs(lc) >= floor - 1.0
        bad += not (okay or capped)
        tag = 'ok ' if okay else 'cap' if capped else 'LOW'
        print(f'    {reg.get(tv, tv):14} on {reg.get(gv, gv):14} Lc {lc:7.1f}  floor {floor:3.0f}  {abs(lc) - floor:+5.1f}  {tag}  {why}')
        if capped:
            print(f'      capped: {CAPS[tv]}')

    print(f'\n  fills under text that keeps its own colour ({len(HIGHLIGHTS)}; tier 60 -- the platform\'s ceiling, see the header):')
    for g, t, why in HIGHLIGHTS:
        tv, gv = val(t), val(g)
        if tv is None or gv is None or tv == NONE or gv == NONE:
            notes.append(f'{t} on {g}: {"unset" if tv is None or gv is None else "unpainted"}'); bad += 1
            continue
        lc = apca.lc(tv, gv)
        okay = abs(lc) >= 60
        bad += not okay
        print(f'    {reg.get(tv, tv):14} on {reg.get(gv, gv):18} Lc {lc:7.1f}  {"ok " if okay else "LOW"}  {why}')

    # (e) adjacencies
    print(f'\n  surfaces that touch ({len(ADJACENT)}; OKLab dE, floor {FLOOR}, tolerance 0.05 for the rounding in palette.json):')
    for a, b, why in ADJACENT:
        av, bv = val(a), val(b)
        if av is None or bv is None or av == NONE or bv == NONE:
            notes.append(f'{a} / {b}: {"unset" if av is None or bv is None else "unpainted"}'); bad += 1
            continue
        d = ok.delta_e(av, bv)
        okay = d >= FLOOR - 0.05
        bad += not okay
        print(f'    {reg.get(av, av):14} / {reg.get(bv, bv):14} dE {d:5.1f}  {d - FLOOR:+5.1f}  {"ok " if okay else "BELOW"}  {why}')
    for (a, b), why in ADJACENT_EXEMPT.items():
        av, bv = val(a), val(b)
        d = ok.delta_e(av, bv) if av and bv and NONE not in (av, bv) else 0.0
        print(f'    {reg.get(av, av):14} / {reg.get(bv, bv):14} dE {d:5.1f}  exempt: {why}')

    # (f) the syntax colouring: every foreground a ladder value, measured on the editor field
    print(f'\n  tokens ({len(TOKENS)} scope groups, {len(SEMANTIC_TOKENS)} semantic kinds; on WHITE, floor 75):')
    styles = {'', 'bold', 'italic', 'underline', 'strikethrough'}
    for entry in theme['tokenColors']:
        fg = _norm(entry['settings'].get('foreground'))
        st = entry['settings'].get('fontStyle', '')
        if fg is not None and fg not in reg:
            notes.append(f'token {entry.get("name", entry["scope"][0])}: {fg} NOT DERIVED BY ANY LADDER'); bad += 1
        if not set(st.split()) <= styles:
            notes.append(f'token {entry.get("name", entry["scope"][0])}: fontStyle {st!r}'); bad += 1
    tok_values = {}
    for entry in theme['tokenColors']:
        fg = _norm(entry['settings'].get('foreground'))
        if fg:
            tok_values.setdefault(fg, set()).update(entry['settings'].get('fontStyle', '400').split())
    for k, v in theme['semanticTokenColors'].items():
        fg = _norm(v.get('foreground') if isinstance(v, dict) else v)
        if fg and fg not in reg:
            notes.append(f'semantic token {k}: {fg} NOT DERIVED BY ANY LADDER'); bad += 1
        if fg:
            tok_values.setdefault(fg, set()).update((v.get('fontStyle', '400') if isinstance(v, dict) else '400').split())
    for fg, st in sorted(tok_values.items(), key=lambda kv: -abs(apca.lc(kv[0], WHITE))):
        lc = apca.lc(fg, WHITE)
        okay = abs(lc) >= 75 or (fg in CAPS and abs(lc) >= 74)
        bad += not okay
        print(f'    {reg.get(fg, fg):18} Lc {lc:6.1f}  {"ok " if okay else "LOW"}  {", ".join(sorted(st))}')

    # (g) a signal on an id whose name does not say so -- a note, never a gate
    for cid, hx in colors.items():
        name = reg.get(hx, '')
        if is_content(name) and not MEANING.search(cid) and not cid.startswith(('terminal.ansi', 'charts.')):
            notes.append(f'note: {cid} takes {name}, and its name carries no meaning -- check it is content or a signal')

    # (h) the settings files carry no colour, and the installer writes none
    keys = {}
    for path in SETTINGS:
        if not os.path.isfile(path):
            notes.append(f'{os.path.relpath(path, ROOT)} is missing'); bad += 1; continue
        raw = open(path, encoding='utf-8').read()
        try:
            d = jsonc(raw)
        except Exception as e:
            notes.append(f'{os.path.relpath(path, ROOT)}: does not parse as JSONC: {e}'); bad += 1; continue
        body = _JSONC_STRIP.sub(lambda m: m.group(1) or '', raw)
        hexes = sorted(set(HEX6.findall(body)))
        for k in d:
            if k in keys:
                notes.append(f'{k} is set in both {keys[k]} and {os.path.basename(path)}'); bad += 1
            keys[k] = os.path.basename(path)
        print(f'\n  {os.path.relpath(path, ROOT)}: {len(d)} settings, {len(hexes)} colour(s)'
              + (' -- A SETTINGS FILE PAINTS NOTHING' if hexes else ''))
        bad += bool(hexes)
    if keys.get('workbench.colorTheme') != 'settings.json':
        notes.append('settings.json does not select the theme (workbench.colorTheme)'); bad += 1
    if os.path.isfile(INSTALLER):
        body = re.sub(r'^\s*#.*$', '', open(INSTALLER, errors='ignore').read(), flags=re.M)
        found = sorted({h.upper() for h in HEX6.findall(body)})
        print(f'  {os.path.relpath(INSTALLER, ROOT)}: {len(found)} colour(s) it writes itself')
        for hx in found:
            note = '' if hx in reg else 'NOT A VALUE THE KIT AUTHORS'
            bad += bool(note)
            print(f'    {hx}  {note}')

    if notes:
        print('\n  notes:')
        for n in notes:
            print(f'    {n}')
    print(f'\nvscode: {"every value, pair and adjacency clears" if not bad else str(bad) + " DEFECT(S)"}')
    return bad == 0


# --- 8. the installed build: a report, never a gate ----------------------------------------------------------
BUNDLES = [
    os.path.expanduser('~/.local/share/flatpak/app/com.visualstudio.code/current/active/files/extra/vscode/resources/app'),
    '/var/lib/flatpak/app/com.visualstudio.code/current/active/files/extra/vscode/resources/app',
    '/usr/share/code/resources/app', '/usr/lib/code/resources/app', '/opt/visual-studio-code/resources/app',
    '/snap/code/current/usr/share/code/resources/app', '/usr/share/codium/resources/app',
    os.path.expanduser('~/.local/share/flatpak/app/com.vscodium.codium/current/active/files/share/codium/resources/app'),
]
# The minified registerColor: `(var=)?se("id",{light:...,dark:...,hcDark:...,hcLight:...},localize(...))`.
# The wrapper's name is whatever the bundler chose for this build; `se` is 1.137's. If a later build renames
# it, --coverage finds no registry and says so, which is the right failure.
_REG = re.compile(r'(?:(\w+)=)?\b(se)\("([a-zA-Z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*)",'
                  r'(\{[^{}]*\}|[A-Za-z_$][\w$]*|null|qe\.[a-z]+|"#[0-9A-Fa-f]{6,8}")')
_ANSI_TABLE = re.compile(r'"(terminal\.ansi[A-Za-z]+)":\{index:\d+,defaults:\{light:("[^"]+")')


def _bundle():
    return next((b for b in BUNDLES if os.path.isfile(os.path.join(b, 'package.json'))), None)


def registry(bundle):
    """{id: (light default as written, the variable it was bound to)} and {var: id}, off the workbench bundle."""
    js = open(os.path.join(bundle, 'out', 'vs', 'workbench', 'workbench.desktop.main.js'), encoding='utf8', errors='replace').read()
    reg, var2id = {}, {}
    for m in _REG.finditer(js):
        var, cid, d = m.group(1), m.group(3), m.group(4)
        if var:
            var2id[var] = cid
        if d.startswith('{'):
            lm = re.search(r'light:((?:qe\.fromHex\("[^"]+"\)(?:\.transparent\([^)]*\))?)|[^,}]+)', d)
            light = lm.group(1).strip() if lm else 'null'
        else:
            light = d
        reg[cid] = light
    for m in _ANSI_TABLE.finditer(js):
        reg[m.group(1)] = m.group(2)
    for p in glob.glob(os.path.join(bundle, 'extensions', '*', 'package.json')):
        try:
            for c in (json.load(open(p)).get('contributes', {}) or {}).get('colors', []) or []:
                v = (c.get('defaults') or {}).get('light')
                reg[c['id']] = f'"{v}"' if isinstance(v, str) and v.startswith('#') else (v or 'null')
        except Exception:
            pass
    return reg, var2id


def _literal(v):
    m = re.fullmatch(r'"?(#[0-9A-Fa-f]{6})(?:[0-9A-Fa-f]{2})?"?', v or '')
    if m:
        return m.group(1).upper()
    return {'qe.white': '#FFFFFF', 'qe.black': '#000000'}.get(v)


def coverage():
    bundle = _bundle()
    if not bundle:
        print('coverage: no VS Code found at ' + ', '.join(BUNDLES)); return True
    ver = json.load(open(os.path.join(bundle, 'package.json'))).get('version', '?')
    reg, var2id = registry(bundle)
    if not reg:
        print(f'coverage: {bundle}: no colour registry found -- the minified registerColor is no longer `se(`'); return True
    theme = {k: _norm(v) for k, v in jsonc(open(THEME, encoding='utf-8').read())['colors'].items()} if os.path.isfile(THEME) else {}

    def resolve(cid, depth=0):
        """('set'|'pole'|'reserved'|'neutral'|'blend'|'null'|'opacity', through) for what the id paints."""
        if cid in theme:
            return 'set', cid
        if cid in OPACITY_IDS:
            return 'opacity', cid
        v = reg.get(cid)
        if v is None or v == 'null':
            return 'null', cid
        lit = _literal(v)
        if lit:
            if len(v.strip('"')) == 9 and not v.strip('"').endswith('FF') and not v.strip('"').lower().endswith('ff'):
                return 'blend', cid          # a literal with an alpha paints a mix
            return ('reserved' if P.reserved(lit) else 'pole' if P.readable(lit) and not P.clear(lit) else 'neutral'), cid
        if re.fullmatch(r'[A-Za-z_$][\w$]*', v) and v in var2id and depth < 8:
            return resolve(var2id[v], depth + 1)
        if v == '(none)':
            return 'null', cid
        return 'blend', cid

    kinds = {}
    for cid in reg:
        k, through = resolve(cid)
        kinds.setdefault(k, []).append((cid, through))
    n_set = len([c for c in reg if c in theme])
    n_ref = len([1 for c, t in kinds.get('set', []) if c != t])
    print(f'{bundle}\nVS Code {ver}: {len(reg)} colour ids in the registry; the theme sets {n_set} directly and '
          f'{n_ref} more resolve through one it sets.\n')
    live_must = sorted(c for k in ('pole', 'reserved') for c, _ in kinds.get(k, []))
    print(f'UNSET, AND THE DEFAULT IS A POLE OR A RESERVED LITERAL ({len(live_must)}) -- a Microsoft colour showing through:')
    for c in live_must:
        print(f'  {c}   {reg[c]}')
    new = sorted(c for c in live_must if c not in MUST_SET)
    gone = sorted(c for c in MUST_SET if c not in reg)
    print(f'\nagainst the list recorded on {RECORDED_ON} from {RECORDED_FROM}: {len(new)} new, {len(gone)} renamed or removed')
    for c in new:
        print(f'  new:  {c}')
    for c in gone:
        print(f'  gone: {c}')
    blends = sorted(c for c, _ in kinds.get('blend', []))
    shadows = [c for c in blends if 'hadow' in c or c in LEFT_UNSET]
    print(f'\nUNSET AND BLENDING ({len(blends)}) -- each paints a mix of two values rather than a value. '
          f'{len(shadows)} are shadows or listed in LEFT_UNSET, which §4 permits as real; the rest:')
    for c in blends:
        if c not in shadows:
            print(f'  {c}   {reg[c]}')
    neutral = sorted(c for c, _ in kinds.get('neutral', []))
    print(f'\nUNSET, A NEUTRAL LITERAL ({len(neutral)}) -- a grey the kit did not author:')
    for c in neutral:
        print(f'  {c}   {reg[c]}')
    print(f'\nunset and null (paints nothing): {len(kinds.get("null", []))};  opacities left to the platform: {len(kinds.get("opacity", []))}')
    stale = sorted(c for c in theme if c not in reg)
    print(f'ids the theme sets that this build does not register ({len(stale)}): ' + (', '.join(stale) if stale else 'none'))
    return True


def _default_in(js, start):
    """The `default:` at depth 1 of the object starting at js[start], which is `{`. Nested objects -- an
    `items:{...}` or an `enumDescriptions` -- carry defaults of their own, so the first `default:` in a flat
    window is not always this key's; walking the braces is."""
    depth, i, n = 0, start, len(js)
    while i < n:
        c = js[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return ''
        elif depth == 1 and js.startswith('default:', i):
            m = re.match(r'default:(\[[^\]]*\]|"[^"]*"|[^,}]+)', js[i:i + 400])
            return m.group(1) if m else ''
        i += 1
    return ''


def settings_report():
    bundle = _bundle()
    if not bundle:
        print('settings: no VS Code found at ' + ', '.join(BUNDLES)); return True
    ver = json.load(open(os.path.join(bundle, 'package.json'))).get('version', '?')
    js = open(os.path.join(bundle, 'out', 'vs', 'workbench', 'workbench.desktop.main.js'), encoding='utf8', errors='replace').read()
    ext_props = {}
    for p in glob.glob(os.path.join(bundle, 'extensions', '*', 'package.json')):
        try:
            conf = (json.load(open(p)).get('contributes', {}) or {}).get('configuration', {})
        except Exception:
            continue
        for c in (conf if isinstance(conf, list) else [conf]):
            for k, v in (c.get('properties') or {}).items():
                ext_props[k] = (os.path.basename(os.path.dirname(p)), v.get('default'))
    print(f'VS Code {ver} at {bundle}\nthe settings the kit sets, and whether this build registers them -- a report, not a gate:\n')
    for path in SETTINGS:
        if not os.path.isfile(path):
            continue
        d = jsonc(open(path, encoding='utf-8').read())
        print(f'  {os.path.relpath(path, ROOT)}')
        for k, v in d.items():
            where, default = '', ''
            m = re.search(r'"' + re.escape(k) + r'":\{', js)
            if m:
                where, default = 'workbench', _default_in(js, m.end() - 1)
            elif k in ext_props:
                where, default = ext_props[k][0], json.dumps(ext_props[k][1])
            elif k.startswith('editor.') and re.search(r'\(\d+,"' + re.escape(k[7:].split('.')[0]) + r'",', js):
                where = 'editor option'
                m2 = re.search(r'\(\d+,"' + re.escape(k[7:].split('.')[0]) + r'",([^,]+),', js)
                default = m2.group(1) if m2 else ''
            elif f'"{k}"' in js:
                where = 'workbench'
            print(f'    {"present" if where else "ABSENT "} {k:56} = {json.dumps(v):16} {where:14} shipped default {default}')
    return True


def _print_derivations():
    print('=== the tints: the pale ground of each semantic hue, solved against WHITE (build/vscode.py tint) ===')
    print(f'  the lightest in-gamut value at the FHWA hue, chroma between C_FLOOR {P.C_FLOOR:.3f} and C_REF {P.C_REF:.3f},')
    print(f'  that clears SURFACE_FLOOR {FLOOR} against WHITE, taking the one that carries BLACK best:')
    for k, hx in TINTS.items():
        L, Cc, h = ok.lch(hx)
        print(f'    tint {k:12} {hx}  L {L:.3f} C {Cc:.3f} h {h:5.1f}  dE(WHITE) {ok.delta_e(hx, WHITE):5.1f}  '
              f'BLACK on it Lc {apca.lc(BLACK, hx):5.1f}  ({apca.lc(BLACK, hx) - 75:+.1f} against the body tier: the platform\'s cost)')
    print(f'    inserted against removed, which abut in a hunk: dE {ok.delta_e(TSUCCESS, TDESTRUCTIVE):.1f}')
    print('\n=== charts.orange: the platform\'s own #EA5C00, solved as an ANSI slot is ===')
    L, Cc, h = ok.lch(ORANGE)
    fam, gap, req = P.clearance(ORANGE)
    print(f'    {ORANGE}  L {L:.3f} C {Cc:.3f} h {h:5.1f}  Lc {apca.lc(ORANGE, WHITE):5.1f} on WHITE  '
          f'{gap:.1f} from {fam}: inside the pole on purpose -- content (§0a)')
    print('\n=== the ANSI slots: build/cosmic.py, unchanged ===')
    for slot, row in ANSI.items():
        print(f'    {slot:8} normal {row["normal"]}  bright {row["bright"]}')
    print(f'    plus BLACK, LIGHT, DARK, WHITE on the four neutral slots. Caps: {len(CAPS)} value(s) at a gamut ceiling.')
    print('\n=== the two COSMIC ladder slots used: neutral_5 (the fifth graph line), neutral_7 (whitespace, rulers, guides) ===')
    for nm, hx in (('neutral_5', N5), ('neutral_7', N7)):
        print(f'    {nm} {hx}  Lc {apca.lc(hx, WHITE):5.1f} on WHITE')
    print('\n=== the syntax colouring: tone and geometry (CHOSEN, §0c) ===')
    print('  the arc offers no second hue at CHROME 0.1: the three arc hues at one lightness, solved text-on-WHITE at Lc 75, are')
    import derive_palette as D
    trio = [D.solve(D.CHROME, WHITE, 75.0, False, 'dark', h)[0] for h in (295.4, PAL['derived']['home_hue_derived'], D.HOME_HUE)]
    print(f'    {trio[0]} (295.4), {trio[1]} (323.2), {trio[2]} (351.0): dE {ok.delta_e(trio[0], trio[1]):.1f}, '
          f'{ok.delta_e(trio[1], trio[2]):.1f}, {ok.delta_e(trio[0], trio[2]):.1f} apart -- and the last is ACCENT to dE {ok.delta_e(trio[2], ACCENT):.1f}')
    for name, scopes, fg, style in TOKENS:
        if name:
            v = fg or BLACK
            print(f'    {authored().get(v, v):14} {style or "regular":13} Lc {apca.lc(v, WHITE):5.1f}  {name[:96]}')
    n = {}
    for cid, hx, _ in COLORS:
        n[hx] = n.get(hx, 0) + 1
    print(f'\n=== the role table: {len(COLORS)} ids on {len(n)} values ===')
    for hx, c in sorted(n.items(), key=lambda kv: -kv[1]):
        print(f'    {authored().get(hx, hx):24} {c:4}')


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--write' in sys.argv:
        write(); sys.exit(0)
    if '--coverage' in sys.argv:
        sys.exit(0 if coverage() else 1)
    if '--settings' in sys.argv:
        sys.exit(0 if settings_report() else 1)
    sys.exit(0 if check() else 1)
