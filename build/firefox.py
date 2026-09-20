"""The Firefox surface: derive its ladder, then check what is committed. AUTHORITY.md is the authority.

Firefox asks for more values than the kit authors, and it asks differently from COSMIC. COSMIC wanted three
short lists -- eleven neutrals, nine swatches, sixteen ANSI slots -- and each was filled once. Firefox has a
design system: a primitive grey ramp of twenty slots, and about two hundred named tokens above it that resolve
through the ramp. So the surface has two jobs, and this file checks both.

  THE LADDER: the grey ramp, twenty slots where §2 has four. The kit does not interpolate sixteen new values
    into it. It SNAPS each slot to the nearest of §2's four by lightness, and the reason is robustness rather
    than economy: `browser.nova.enabled` renumbers the ramp, and under the other numbering three slots land on
    a different kit neutral. Interpolated, that would be sixteen values that are right under one numbering and
    wrong under the other. Snapped, a slot can move one step along the kit's own ladder and cannot land off it
    at all. user.js pins the pref to the numbering this was derived against; --derive prints both columns.

  THE PAIRS: a stylesheet declares what text sits on what ground, which a .ron file never did. So the checker
    does not take a table of numbers on trust -- it reads both sides out of the sheet and measures them. Change
    --toolbar-background-color and the toolbar's text pair is re-measured on the next run. Same for two grounds
    that touch: those are OKLab dE against SURFACE_FLOOR, never Lc (§0e, and they are not interchangeable).

What makes any of this checkable is one rule the sheet keeps: THE ONLY LITERAL COLOURS IN IT ARE THE --rm-*
DEFINITIONS. Every other declaration refers to those by name. So "a value nobody derived" is not a judgement
call here -- a hex outside the definition block is a defect by construction, and so is any notation that mixes
(rgba, color-mix, light-dark), because a mixed value is not an authored value and no checker can see through it.

    python3 build/firefox.py             check every value, pair and adjacency in the committed sheet
    python3 build/firefox.py --derive    the grey ladder, and how each slot was reached
    python3 build/firefox.py --coverage  which of the installed Firefox's colour tokens the sheet leaves unset
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FF = os.path.join(ROOT, 'worksafe', 'firefox')
SHEETS = [os.path.join(FF, 'chrome', 'userChrome.css'), os.path.join(FF, 'chrome', 'userContent.css')]
PREFS = os.path.join(FF, 'user.js')
INSTALLER = os.path.join(FF, 'install.sh')

PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
SEMANTIC = {'SUCCESS': '#006B54', 'WARNING': '#FCD116', 'DESTRUCTIVE': '#AF1E2D'}
FLOOR = PAL['surface_floor_dE']
# The sheet's own names for the kit's values. A --rm-* the kit does not author is a defect; so is an authored
# value that arrives under the wrong name.
ROLES = {'white': PAL['neutrals']['WHITE'], 'light': PAL['neutrals']['LIGHT'],
         'dark': PAL['neutrals']['DARK'], 'black': PAL['neutrals']['BLACK'],
         'accent': PAL['chrome']['ACCENT'], 'select': PAL['chrome']['SELECT'],
         'cursor': PAL['chrome']['CURSOR'],
         'success': SEMANTIC['SUCCESS'], 'warning': SEMANTIC['WARNING'],
         'destructive': SEMANTIC['DESTRUCTIVE'],
         # §3 reserves these two for legend on a semantic field and refuses them anywhere else. They are in the
         # sheet under their own names so the refusal is mechanical: every use has to land on a §3 ground.
         'legend-light': '#FFFFFF', 'legend-dark': '#000000'}
RESERVED = {'legend-light', 'legend-dark'}
SEMANTIC_ROLES = {'success', 'warning', 'destructive'}


# --- 1. the grey ladder ----------------------------------------------------------------------------------
# Firefox's primitive ramp, read out of the installed build and recorded here with its date, the way a pole
# member is recorded with its source. Two ramps share one set of names: the one the shipped chrome uses, and
# the one behind browser.nova.enabled. Measured 2026-09-19 from Firefox 155.0.1 (deb), file
# chrome/toolkit/skin/classic/global/design-system/tokens-shared.css in omni.ja.
FF_RAMP = {0: '#fbfbfe', 20: '#f0f0f4', 30: '#bac2ca', 50: '#bfbfc9', 60: '#8f8f9d',
           70: '#5b5b66', 80: '#23222b', 90: '#1c1b22', 100: '#15141a'}
FF_RAMP_NOVA = {0: '#fcfbff', 5: '#f7f6fb', 10: '#efedf2', 15: '#e3e2e7', 20: '#d6d5da', 25: '#c7c6cb',
                30: '#b7b6ba', 35: '#a6a4a9', 40: '#949297', 45: '#817f84', 50: '#67666a', 55: '#515054',
                60: '#3f3e42', 65: '#312f33', 70: '#252428', 75: '#1d1b1f', 80: '#171519', 85: '#131215',
                90: '#121114'}
SLOTS = sorted(set(FF_RAMP) | set(FF_RAMP_NOVA))
LADDER = ['white', 'light', 'dark', 'black']          # §2's four, lightest first


def _snap(L):
    """The kit neutral nearest this lightness. Four values, so a slot cannot land between them."""
    return min(LADDER, key=lambda r: abs(ok.lch(ROLES[r])[0] - L))


def _curve_L(slot, ramp):
    """A slot's lightness on `ramp`, interpolating in the slot number where the ramp does not define it.

    The number is the platform's own scale -- 0 lightest, 100 darkest, monotonic in both ramps -- so a slot the
    ramp skips is read off the curve rather than guessed at.
    """
    ks = sorted(ramp)
    if slot in ramp:
        return ok.lch(ramp[slot])[0]
    lo = max([k for k in ks if k < slot], default=ks[0])
    hi = min([k for k in ks if k > slot], default=ks[-1])
    if lo == hi:
        return ok.lch(ramp[lo])[0]
    a, b = ok.lch(ramp[lo])[0], ok.lch(ramp[hi])[0]
    return a + (b - a) * (slot - lo) / (hi - lo)


def greys():
    """[(slot, role, hex, nova_role)] -- the ramp in force, and what nova's numbering would have made it."""
    out = []
    for s in SLOTS:
        role = _snap(_curve_L(s, FF_RAMP))
        nova = _snap(_curve_L(s, FF_RAMP_NOVA))
        out.append((s, role, ROLES[role], nova))
    return out


def ladder_is_monotonic(rows):
    """A ramp that is not monotonic can invert a pair: light text on what was meant to be a light ground."""
    seen = [LADDER.index(r) for _, r, _, _ in rows]
    return all(b >= a for a, b in zip(seen, seen[1:]))


# --- 2. reading the sheet --------------------------------------------------------------------------------
COMMENT = re.compile(r'/\*.*?\*/', re.S)
BLOCK = re.compile(r'([^{}]+)\{([^{}]*)\}', re.S)
HEX = re.compile(r'#[0-9A-Fa-f]{3,8}\b')
VAR = re.compile(r'var\(\s*--rm-([a-z-]+)\s*\)')
DEF = re.compile(r'--rm-([a-z-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*(?:!important\s*)?$')
# A value that is mixed, blended or chosen at render time is not an authored value, and nothing downstream can
# measure it. The sheet names none of these, and that is the rule rather than a preference.
MIXED = re.compile(r'\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark|image-set)\s*\(')
NAMED = {'aliceblue', 'aqua', 'aquamarine', 'azure', 'beige', 'black', 'blue', 'brown', 'chartreuse',
         'chocolate', 'coral', 'crimson', 'cyan', 'darkblue', 'darkgreen', 'darkred', 'fuchsia', 'gold',
         'gray', 'green', 'grey', 'indigo', 'ivory', 'khaki', 'lavender', 'lime', 'magenta', 'maroon',
         'navy', 'olive', 'orange', 'orchid', 'pink', 'plum', 'purple', 'red', 'salmon', 'sienna', 'silver',
         'snow', 'tan', 'teal', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'yellow',
         # the system colours Firefox ships in these very tokens: LinkText, SelectedItem, ThreeDShadow. A
         # theme that leaves one in has handed that value to GTK, which is not the kit and is not measured.
         'linktext', 'visitedtext', 'selecteditem', 'selecteditemtext', 'threedshadow', 'buttonface',
         'buttontext', 'canvas', 'canvastext', 'field', 'fieldtext', 'highlight', 'highlighttext',
         'graytext', 'accentcolor', 'accentcolortext', 'mark', 'marktext'}
KEYWORDS = {'transparent', 'currentcolor', 'inherit', 'initial', 'unset', 'revert', 'none', 'auto', 'solid',
            'dashed', 'dotted', 'bold', 'normal', 'important', 'center', 'always', 'hidden', 'block', 'flex'}


def read_sheet(path):
    """(defs, tokens, blocks, defects, named). Everything the checker knows about one stylesheet.

    `tokens` maps a platform token to the kit role it was given; `named` is every platform token the sheet
    sets at all, role or keyword. The coverage pass needs the second: a token set to `transparent` -- which is
    most of the border family, because §5 draws no line inside a window -- has been decided about just as
    firmly as one given a colour.
    """
    raw = open(path).read()
    text = COMMENT.sub(' ', raw)                       # comments quote values on purpose (CONTRIBUTING.md §8)
    defs, tokens, blocks, bad, named, seen_decl = {}, {}, [], [], set(), set()
    rel = os.path.relpath(path, ROOT)

    for m in BLOCK.finditer(text):
        sel, body = ' '.join(m.group(1).split()), m.group(2)
        decls = []
        for d in body.split(';'):
            if ':' not in d:
                continue
            prop, val = d.split(':', 1)
            prop, val = prop.strip(), val.strip()
            if not prop:
                continue
            decls.append((prop, val))
            if prop.startswith('--') and not prop.startswith('--rm-'):
                named.add(prop)
            if prop.startswith('--rm-'):
                hm = HEX.search(val)
                if hm:
                    defs.setdefault(prop[5:], hm.group(0).upper())
                    continue
            v = VAR.search(val)
            if v and prop.startswith('--'):
                # A token assigned twice IN THE SAME SELECTOR is at best noise and at worst two different
                # answers, where which one wins is a cascade question nobody wants to reason about. Across
                # two selectors it is not a duplicate at all: setting a token on `:root` and again on the
                # custom element that declares it is the only way to reach past that component's own `:host`
                # rule, and the sheet does exactly that for three of them.
                if (sel, prop) in seen_decl:
                    bad.append(f'{rel}: {sel[:40]} sets {prop} twice')
                seen_decl.add((sel, prop))
                tokens[prop] = v.group(1)
            # what is left after the var() references and the units come out
            rest = VAR.sub(' ', val).replace('!important', ' ')
            rest = re.sub(r'var\(\s*--[a-z0-9-]+\s*\)', ' ', rest)
            for hm in HEX.finditer(rest):
                bad.append(f'{rel}: {prop} carries the literal {hm.group(0)} outside the --rm-* definitions')
            for mm in MIXED.finditer(rest):
                bad.append(f'{rel}: {prop} uses {mm.group(1)}() -- a mixed value is not an authored value')
            for w in re.findall(r'[A-Za-z][A-Za-z-]{2,}', rest):
                if w.lower() in NAMED and w.lower() not in KEYWORDS:
                    bad.append(f'{rel}: {prop} names the colour "{w}" -- nothing derived it')
        blocks.append((sel, decls, rel))
    return defs, tokens, blocks, bad, named


def block_pairs(blocks, defs):
    """Every rule that sets text and ground together, as (where, text role, ground role, weight)."""
    out = []
    for sel, decls, rel in blocks:
        text = ground = None
        weight = 400
        for prop, val in decls:
            if prop == 'font-weight':
                weight = 700 if re.search(r'\b(700|800|900|bold)\b', val) else 400
            v = VAR.search(val)
            if not v:
                continue
            if prop in ('color', 'fill'):
                text = v.group(1)
            elif prop in ('background-color', 'background'):
                ground = v.group(1)
        if text and ground:
            out.append((f'{rel}  {sel[:58]}', text, ground, weight))
    return out


# --- 3. the pairs the sheet authors by token ---------------------------------------------------------------
# Named by TOKEN, never by value: the checker reads both sides out of the sheet, so a pair cannot drift from
# the number recorded beside it. The floor is APCA's own tier for what that pair carries (build/apca.py
# GUIDANCE) -- 75 for body at 16px/400, 60 where the sheet sets 700, 30 for a mark.
PAIRS = [
    ('--text-color', '--background-color-canvas', 75, 'body text on the window field, 16px/400'),
    ('--text-color-deemphasized', '--background-color-canvas', 60, 'secondary text on the field'),
    ('--toolbar-text-color', '--toolbar-background-color', 60, 'toolbar and bookmark labels, 16px/700'),
    ('--toolbox-text-color', '--toolbox-background-color', 75, 'tab labels on the key titlebar, 16px/400'),
    ('--toolbox-text-color-inactive', '--toolbox-background-color-inactive', 60,
     'tab labels on the non-key titlebar, 16px/700'),
    ('--tab-selected-textcolor', '--tab-background-color-selected', 60, 'the current tab label, 16px/700'),
    ('--toolbar-field-text-color', '--toolbar-field-background-color', 75, 'the address field, 16px/400'),
    ('--toolbar-field-highlight-text', '--toolbar-field-highlight', 75, 'selected text in the address field'),
    ('--panel-text-color', '--panel-background-color', 60, 'menu and panel labels, 16px/700'),
    ('--menu-color', '--menu-background-color', 60, 'menu labels, 16px/700'),
    ('--menuitem-hover-color', '--menuitem-hover-background-color', 75, 'the hovered menu item'),
    ('--urlbarview-text-color-selected', '--urlbarview-background-color-selected', 75, 'the selected result row'),
    ('--urlbarview-text-color-secondary', '--panel-background-color', 45, 'the second line of a result row'),
    ('--sidebar-text-color', '--sidebar-background-color', 60, 'sidebar labels, 16px/700'),
    ('--button-text-color', '--button-background-color', 75, 'button labels, 16px/400 on a WHITE control'),
    ('--button-text-color-hover', '--button-background-color-hover', 75, 'a hovered button'),
    ('--button-text-color-active', '--button-background-color-active', 75, 'a pressed button'),
    ('--button-text-color-selected', '--button-background-color-selected', 75, 'a toggle that is on'),
    ('--button-text-color-primary', '--button-background-color-primary', 75, 'the primary button'),
    ('--button-text-color-destructive', '--button-background-color-destructive', 75,
     "§3's legend on a destructive field -- the one use #FFFFFF is permitted"),
    # Disabled text is meant to read as unavailable, so it is authored weak on purpose and measured anyway:
    # DARK on LIGHT is Lc 48.4, APCA's display-type tier, well over the 30 it allows a non-text mark and
    # nowhere near the 15 below which nothing is visible. It is the one pair in the sheet under 60.
    ('--button-text-color-disabled', '--button-background-color-disabled', 30, 'a control that cannot be used'),
    ('--text-color-disabled', '--background-color-canvas', 30, 'disabled text on the field'),
    ('--input-text-color', '--input-background-color', 75, 'what the user types, 16px/400'),
    ('--table-header-text-color', '--table-header-background-color', 60, 'a table header, 16px/700'),
    ('--urlbar-box-text-color', '--urlbar-box-background-color', 60, 'the search-mode chiclet'),
    ('--urlbar-box-text-color-hover', '--urlbar-box-background-color-hover', 75, 'the chiclet, hovered'),
    ('--text-color-list-item-hover', '--background-color-list-item-hover', 75, 'the hovered row of a list'),
    ('--text-color-accent-primary-selected', '--color-accent-primary', 75, 'text on the accent'),
    ('--card-header-text-color', '--card-background-color', 60, 'a card heading, 16px/700'),
]

# Two grounds that touch. OKLab dE against SURFACE_FLOOR -- Lc would report false collapses here (§0e).
ADJACENT = [
    ('--toolbar-field-background-color', '--toolbar-background-color', 'the address field on its toolbar'),
    ('--toolbox-background-color', '--tab-background-color-selected', 'the current tab on the strip'),
    ('--toolbox-background-color', '--tab-background-color-hover', 'a hovered tab on the strip'),
    ('--tab-background-color-selected', '--tab-background-color-hover', 'a hovered tab beside the current one'),
    ('--tab-background-color-selected', '--toolbar-background-color', 'the current tab meeting the toolbar'),
    ('--panel-background-color', '--background-color-canvas', 'a panel floating over the field'),
    ('--panel-background-color', '--panel-item-hover-bgcolor', 'the hovered row in a panel'),
    ('--panel-background-color', '--button-background-color', 'a button on a panel'),
    ('--sidebar-background-color', '--background-color-canvas', 'the sidebar against the field'),
    ('--background-color-box', '--background-color-canvas', 'a box or card on the field'),
    ('--table-header-background-color', '--table-row-background-color', 'a table header over its rows'),
    ('--background-color-canvas', '--background-color-list-item-hover', 'the hovered row of an in-window list'),
]
# The current tab meets the toolbar and is the same value by construction: a tab is the visible edge of the
# field below it, so there is nothing there to distinguish. Same shape as §2's own exempt table.
ADJACENT_EXEMPT = {('--tab-background-color-selected', '--toolbar-background-color')}


def _slot_name(s):
    """Firefox's own spelling: gray-0, gray-05, gray-10 ... gray-100."""
    return f'--color-gray-{s:02d}' if 0 < s < 10 else f'--color-gray-{s}'


def _role_of(tokens, name):
    return tokens.get(name)


def check():
    rows = greys()
    if not ladder_is_monotonic(rows):
        print('grey ladder: NOT MONOTONIC -- a slot inverts against its neighbour'); return False
    bad, notes = 0, []
    defs, tokens, blocks = {}, {}, []
    for path in SHEETS:
        if not os.path.exists(path):
            print(f'firefox: {os.path.relpath(path, ROOT)} is not committed yet'); return False
        d, t, b, defects, _ = read_sheet(path)
        for k, v in d.items():
            if k in defs and defs[k] != v:
                defects.append(f'--rm-{k} is defined twice with different values: {defs[k]} and {v}')
            defs[k] = v
        tokens.update(t); blocks += b
        for x in defects:
            notes.append(x); bad += 1

    # --- every literal in the sheet is a value the kit authors -------------------------------------------
    print(f"--rm-* definitions: {len(defs)}")
    for name in sorted(defs):
        hx, want = defs[name], ROLES.get(name)
        note = ''
        if want is None:
            note = 'NOT A ROLE THE KIT AUTHORS'; bad += 1
        elif hx != want.upper():
            note = f'does not match palette.json ({want})'; bad += 1
        elif P.reserved(hx) and name not in RESERVED:
            note = 'reserved by §3'; bad += 1
        if name not in RESERVED and name not in SEMANTIC_ROLES and not P.clear(hx):
            note = (note + ' POLE: chrome must clear every pole').strip(); bad += 1
        fam, gap, req = P.clearance(hx)
        tag = 'neutral' if not P.readable(hx) else f'{gap:5.1f}/{req:4.1f} {fam}'
        print(f"  --rm-{name:13} {hx}  {tag:26} {note}")
    for name in ROLES:
        if name not in defs:
            notes.append(f'--rm-{name} is authored by the kit and the sheet never defines it')

    # --- the grey ladder, as the sheet writes it ---------------------------------------------------------
    miss = [(s, r) for s, r, _, _ in rows if tokens.get(_slot_name(s)) != r]
    print(f"\ngrey ladder: {len(rows)} slots snapped onto §2's four")
    for s, r in miss:
        name = _slot_name(s)
        got = tokens.get(name)
        notes.append(f'{name}: ladder says {r}, sheet says {got}'); bad += 1
    if not miss:
        print(f"  every slot in the sheet is the slot the ladder derives")
    for nm, want in (('--color-white', 'white'), ('--color-black', 'black')):
        if tokens.get(nm) != want:
            notes.append(f'{nm}: §3 reserves the literal; the ramp endpoint must be {want}'); bad += 1

    # --- the pairs ----------------------------------------------------------------------------------------
    print(f"\npairs the sheet authors (APCA Lc, signed; the floor is APCA's tier for what it carries):")
    reserved_ok = set()
    for t, g, floor, why in PAIRS:
        tr, gr = _role_of(tokens, t), _role_of(tokens, g)
        if tr is None or gr is None:
            notes.append(f'{t} on {g}: the sheet does not set {t if tr is None else g}'); bad += 1
            continue
        lc = apca.lc(ROLES[tr], ROLES[gr])
        okay = abs(lc) >= floor
        bad += not okay
        if tr in RESERVED:
            if gr in SEMANTIC_ROLES:
                reserved_ok.add(tr)
            else:
                notes.append(f'{t}: §3 reserves {ROLES[tr]} for legend on a semantic field, not on {gr}')
                bad += 1
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  "
              f"{'ok ' if okay else 'LOW'}  {why}")

    # every rule block that sets both sides, measured the same way
    print(f"\npairs the rule blocks author:")
    # DARK is §2's disabled and secondary value and is authored weak on purpose: it is read as a mark, so it
    # takes APCA's 30. Everything else takes the tier for the weight the block itself sets -- 60 at 700, 75 at
    # 400 -- which is what makes "the labels are bold" a measurement and not a house style.
    for where, tr, gr, weight in block_pairs(blocks, defs):
        lc = apca.lc(ROLES[tr], ROLES[gr])
        floor = 30 if tr == 'dark' else (60 if weight == 700 else 75)
        okay = abs(lc) >= floor
        bad += not okay
        if tr in RESERVED:
            if gr in SEMANTIC_ROLES:
                reserved_ok.add(tr)
            else:
                notes.append(f'{where}: §3 reserves {ROLES[tr]} for legend on a semantic field'); bad += 1
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  /{weight}  "
              f"{'ok ' if okay else 'LOW'}  {where}")

    # --- the adjacencies ----------------------------------------------------------------------------------
    print(f"\nsurfaces that touch (OKLab dE; floor {FLOOR}, derived from WHITE against LIGHT):")
    for a, b, why in ADJACENT:
        ra, rb = _role_of(tokens, a), _role_of(tokens, b)
        if ra is None or rb is None:
            notes.append(f'{a} / {b}: the sheet does not set {a if ra is None else b}'); bad += 1
            continue
        d = ok.delta_e(ROLES[ra], ROLES[rb])
        exempt = (a, b) in ADJACENT_EXEMPT or (b, a) in ADJACENT_EXEMPT
        okay = exempt or d >= FLOOR - 0.05
        bad += not okay
        tag = 'exempt' if exempt else ('ok ' if okay else 'BELOW')
        print(f"  {ra:12} / {rb:12} dE {d:5.1f}  {tag:7} {why}")

    # --- user.js and install.sh: any colour they write themselves -----------------------------------------
    for path in (PREFS, INSTALLER):
        if not os.path.exists(path):
            continue
        body = re.sub(r'^\s*(//|#).*$', '', open(path, errors='ignore').read(), flags=re.M)
        found = sorted({m.group(0).upper() for m in HEX.finditer(body)})
        authored = {v.upper() for v in ROLES.values()}
        print(f"\n{os.path.relpath(path, ROOT)}: {len(found)} colour(s) it writes itself")
        for hx in found:
            note = '' if hx in authored else 'NOT A VALUE THE KIT AUTHORS'
            bad += bool(note)
            print(f"  {hx}  {note}")

    if notes:
        print('\nnotes:')
        for n in notes:
            print(f'  {n}')
    print(f"\nfirefox: {'every value, pair and adjacency clears' if not bad else str(bad) + ' DEFECT(S)'}")
    return bad == 0


# --- 4. what the installed Firefox asks for ----------------------------------------------------------------
# COSMIC's checker needs no COSMIC: its slots are a fixed list. Firefox's token vocabulary is not fixed -- it
# is renamed most releases, and a renamed token is how a strip silently falls back to a Mozilla colour. So the
# coverage pass reads the vocabulary out of the build that is installed, and it is a report rather than a gate:
# it needs Firefox on the machine, and a token the sheet leaves unset is a question, not always a defect.
# Every *.tokens.css in either archive, found rather than listed. The list was a fixed one first and it
# missed the whole in-content component family -- which is how the selected item of an about: page's nav went
# out at color-mix(currentColor 8%), a value no ladder produced, and was caught by eye on the screen instead
# of by this file. A checker that enumerates what is there cannot miss a file that was added.
OMNI = ('/usr/lib/firefox/omni.ja', '/usr/lib/firefox/browser/omni.ja')
# A token whose own default blends (color-mix, an alpha primitive, rgba) does not paint a value -- it paints a
# blend of two. Leaving one unset is not the same kind of omission as leaving a plain token unset, so the
# report separates them.
BLENDS = re.compile(r'color-mix\(|-alpha-|rgba?\(|hsla\(')
COLOURISH = re.compile(r'^--(?!color-(?:blue|cyan|gray|green|orange|pink|purple|red|violet|yellow)-)'
                       r'[a-z0-9-]*(color|outline|shadow|fill|accent)[a-z0-9-]*$')


def _read_omni(jar, member):
    """One file out of an omni.ja.

    Python's zipfile refuses these: Firefox ships them with the archive optimised and data ahead of the
    central directory, which is a valid jar to Firefox and a bad magic number to zipfile. unzip reads them
    with a warning, so it is the fallback and not the other way round.
    """
    import subprocess, zipfile
    try:
        return zipfile.ZipFile(jar).read(member).decode('utf8', 'replace')
    except Exception:
        pass
    try:
        r = subprocess.run(['unzip', '-p', jar, member], capture_output=True, timeout=60)
        return r.stdout.decode('utf8', 'replace') if r.returncode == 0 or r.stdout else ''
    except Exception:
        return ''


def _is_token_file(n):
    # Two spellings, and taking only the first one is how the design system's own file got left out of the
    # first version of this: the per-component files are `*.tokens.css` and the foundation is
    # `design-system/tokens-shared.css`.
    return n.endswith('.tokens.css') or re.search(r'design-system/tokens-[a-z]+\.css$', n) is not None


def _token_files(jar):
    """Every token file inside one omni.ja."""
    import subprocess, zipfile
    try:
        return [n for n in zipfile.ZipFile(jar).namelist() if _is_token_file(n)]
    except Exception:
        pass
    try:
        r = subprocess.run(['unzip', '-Z1', jar], capture_output=True, timeout=60)
        return [l for l in r.stdout.decode('utf8', 'replace').splitlines() if _is_token_file(l)]
    except Exception:
        return []


def coverage():
    defs, files = {}, 0
    for jar in OMNI:
        if not os.path.exists(jar):
            continue
        for f in _token_files(jar):
            body = _read_omni(jar, f)
            if not body:
                continue
            files += 1
            for m in re.finditer(r'^\s*(--[a-z0-9-]+)\s*:([^;]*);', body, re.M):
                defs.setdefault(m.group(1), []).append(m.group(2))
    if not defs:
        print('coverage: no Firefox found at ' + ' or '.join(OMNI)); return True
    setprops = set()
    for path in SHEETS:
        if os.path.exists(path):
            setprops |= read_sheet(path)[4]
    colour = sorted(n for n in defs if COLOURISH.match(n))
    unset = [n for n in colour if n not in setprops]
    mixed = [n for n in unset if any(BLENDS.search(v) for v in defs[n])]
    plain = [n for n in unset if n not in set(mixed)]
    print(f"{files} *.tokens.css files in the installed Firefox define {len(defs)} tokens;")
    print(f"{len(colour)} of them take a colour, and the sheet decides {len(colour) - len(unset)} of those.\n")
    print(f"UNSET AND BLENDING ({len(mixed)}) -- each of these paints a mix of two values rather than a value,")
    print("so where one paints a surface the sheet has to name an authored value instead. Shadows and the")
    print("modal scrim are the exception §4 allows as real:")
    for n in mixed:
        print(f"  {n}")
    print(f"\nUNSET, PLAIN ({len(plain)}) -- a token that resolves through another the sheet does set, a")
    print("geometry token the name pattern caught, or a strip painting itself a Mozilla colour. The third")
    print("kind is what the screen pass in CONTRIBUTING.md §10 is for -- sample the region and run the")
    print("sample back through build/poles.py:")
    for n in plain:
        print(f"  {n}")
    return True


def _print_derivations():
    rows = greys()
    print("=== the grey ramp: twenty slots where §2 has four, each SNAPPED to the nearest by lightness ===")
    print("Snapped rather than interpolated so the ladder survives browser.nova.enabled, which renumbers the")
    print("ramp. Under nova three slots land on a different kit neutral -- and none can land off the ladder.\n")
    print(f"  {'slot':>6}  {'in force':9} {'L':>7}  -> {'kit':6} {'hex':9} {'dE':>5}   {'under nova':10} {'L':>7} -> kit")
    for s, role, hx, nova in rows:
        L = _curve_L(s, FF_RAMP)
        src = FF_RAMP.get(s, '(curve)')
        nL = _curve_L(s, FF_RAMP_NOVA)
        nsrc = FF_RAMP_NOVA.get(s, '(curve)')
        flag = '' if role == nova else '   <-- moves one step'
        print(f"  gray-{s:<3d} {src:9} {L:7.4f}  -> {role:6} {hx:9} {ok.delta_e(hx, FF_RAMP.get(s, hx)):5.1f}"
              f"   {nsrc:10} {nL:7.4f} -> {nova}{flag}")
    print(f"\n  monotonic: {ladder_is_monotonic(rows)}")
    print("  --color-white and --color-black are the ramp's endpoints and §3 reserves both literals, so they")
    print("  take WHITE and BLACK: a field painted #FFFFFF cannot be told from a theme that failed to load.")

    print("\n=== the roles the sheet may name, and nothing else ===")
    for name in sorted(ROLES):
        hx = ROLES[name]
        fam, gap, req = P.clearance(hx)
        tag = ('reserved for legend (§3)' if name in RESERVED else
               'a pole by construction (§3)' if name in SEMANTIC_ROLES else
               'neutral, no readable hue' if not P.readable(hx) else f'clears {gap:.1f}deg from {fam}, needs {req:.1f}')
        print(f"  --rm-{name:13} {hx}  {tag}")


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    if '--coverage' in sys.argv:
        sys.exit(0 if coverage() else 1)
    sys.exit(0 if check() else 1)
