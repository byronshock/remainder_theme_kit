"""The COSMIC surface: derive its ladders, then check what is committed. AUTHORITY.md is the authority.

COSMIC asks for more values than the kit authors. Its palette has eleven neutral slots where
§2 has four, its accent picker has nine swatches, and its terminal has sixteen ANSI slots. None
of those may be filled by eye (principle 10), and none of them may be filled with a value that
reads as a signal (principle 1). So each is a ladder derived from what the kit already has:

  NEUTRALS   eleven slots, interpolated in OKLab lightness at the cast, ANCHORED so that the
             kit's own four neutrals land exactly on slots 0, 3, 8 and 10. COSMIC derives
             component colours from this ramp, so a ramp that contains §2's ladder puts more
             of what the platform paints back onto the kit's own values.

  SWATCHES   nine, and every one must be a legal accent: three hues spanning §1's working arc
             (its floor 295.4, the derived centre 323.2 that §1 chose against, and the home hue
             351.0) x three of APCA's tiers for the WHITE text an accent has to carry. The kit's
             own ACCENT and SELECT fall out as two of the nine.

  TERMINAL   sixteen slots, and here the kit's own rule sends them the other way. A terminal
             buffer is CONTENT (§0a), so the ANSI slots may use the poles -- and must, because
             the user reads red as error and green as done inside the buffer too. Each hue slot
             therefore takes the hue of the colour xterm ships in THAT slot and solves lightness
             and chroma against the kit's WHITE field. This is where Remainder parts from the
             parent kit on this surface: De Stijl paints the ANSI slots with its chrome pigments,
             which is chrome reaching into content.

    python3 build/cosmic.py              check every value in the committed .ron files
    python3 build/cosmic.py --derive     show the three ladders and how each value was reached
"""
import json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca, derive_palette as D

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
COSMIC = os.path.join(ROOT, 'worksafe', 'cosmic')
PAL = json.load(open(os.path.join(ROOT, 'palette.json')))
N, CH = PAL['neutrals'], PAL['chrome']
WHITE, LIGHT, DARK, BLACK = N['WHITE'], N['LIGHT'], N['DARK'], N['BLACK']
ACCENT, SELECT, CURSOR = CH['ACCENT'], CH['SELECT'], CH['CURSOR']
SEMANTIC = {'SUCCESS': '#006B54', 'WARNING': '#FCD116', 'DESTRUCTIVE': '#AF1E2D'}
FLOOR = PAL['surface_floor_dE']

# --- 1. the eleven neutral slots -------------------------------------------------------------
# DERIVED, given the anchors. COSMIC's ramp is eleven slots and §2's ladder is four values, so
# the four are placed on the slots nearest their own lightness and the rest interpolate between
# them. An even ramp from BLACK to WHITE was the first try and it missed DARK by dE 0.1 and
# LIGHT by dE 1.4 -- close enough to look right and wrong enough that COSMIC would paint
# surfaces at values the kit never authored. Anchoring costs an uneven step (dE 7.3 to 8.6
# against 7.8 even) and buys exactness where §2 has an opinion.
ANCHORS = {0: BLACK, 3: DARK, 8: LIGHT, 10: WHITE}


def neutrals():
    """The eleven slots as [(i, hex, note)]. Slots 0/3/8/10 ARE the kit's four neutrals."""
    ks = sorted(ANCHORS)
    Ls = {k: ok.lch(v)[0] for k, v in ANCHORS.items()}
    out = []
    for i in range(11):
        lo, hi = max(k for k in ks if k <= i), min(k for k in ks if k >= i)
        if lo == hi:
            out.append((i, ANCHORS[i], {0: 'BLACK', 3: 'DARK', 8: 'LIGHT', 10: 'WHITE'}[i]))
            continue
        L = Ls[lo] + (Ls[hi] - Ls[lo]) * (i - lo) / (hi - lo)
        out.append((i, ok.hexs(ok.from_lch(L, D.CAST, D.HOME_HUE)), ''))
    return out


# --- 2. the nine accent swatches -------------------------------------------------------------
# The picker's nine swatches are nine accents the user may choose, so every one has to be legal:
# clear of every pole (principle 1) and able to carry the WHITE titlebar text §2 puts on the
# accent. DERIVED: three hues x three of APCA's own tiers.
#
# The hues are §1's working arc and nothing else -- not the cursor's. If a swatch sat at the
# cursor hue and the user picked it, the accent and the text cursor would be one colour, which
# is the collision §2 solved the cursor away from in the first place.
SWATCH_HUES = [('arc floor', 295.4), ('derived centre', PAL['derived']['home_hue_derived']),
               ('home', D.HOME_HUE)]
# 60 is the floor §2 authors the titlebar against; 78 and 87 are what ACCENT and SELECT
# themselves are authored at, so the kit's own two chrome hues come back as two of the nine.
SWATCH_TIERS = [60.0, 78.0, 87.0]
# COSMIC's nine picker slots, in the order it names them. The names are the platform's; a
# swatch is a point in the arc, and none of them is the colour its slot is called.
SWATCH_SLOTS = ['accent_blue', 'accent_indigo', 'accent_purple', 'accent_pink', 'accent_red',
                'accent_orange', 'accent_yellow', 'accent_green', 'accent_warm_grey']


def swatches():
    """[(slot, hex, hue label, tier)] -- nine legal accents, darkest tier last per hue."""
    out = []
    for nm, h in SWATCH_HUES:
        for t in SWATCH_TIERS:
            hx, _ = D.solve(D.CHROME, WHITE, t, True, 'dark', h)
            out.append((hx, nm, t))
    return [(SWATCH_SLOTS[i], hx, nm, t) for i, (hx, nm, t) in enumerate(out)]


# --- 3. the sixteen terminal slots -----------------------------------------------------------
# The exemplars: the colours xterm ships in these very slots. Five of the six are realized
# members of a pole family in poles.json -- which is the point. Inside a buffer red still means
# error and green still means done, so the slot takes the pole's hue rather than avoiding it
# (§0a: content is exempt, and a syntax-coloured buffer is content).
#
# magenta is the exception and it is the interesting one: magenta is not a pole (§0d), and at
# 328.4 its realized hue lands INSIDE the kit's own working arc. The one ANSI slot with nothing
# to say is the one the kit could have authored itself.
#
# cyan's exemplar is a member of info-cyan, which poles.json demotes rather than deletes. In a
# terminal the claim it was demoted for -- "note, diagnostic" -- is exactly the claim the slot
# makes, so the slot honours it where the pole set does not.
ANSI = {'red': '#CD0000', 'green': '#00CD00', 'yellow': '#CDCD00',
        'blue': '#0000EE', 'magenta': '#CD00CD', 'cyan': '#00CDCD'}
# Two of APCA's tiers, read off its own table (build/apca.py GUIDANCE) for a ~16px/400 buffer:
#   normal  Lc 75, the practical floor for sustained reading -- the slot a user reads all day
#   bright  Lc 60, larger or bolder; bright is the slot a terminal pairs with bold
# Bright is the lighter and more saturated of the pair, as the ANSI convention has it, and the
# parent kit reached the same arrangement for the same reason: on a WHITE field the vivid end
# of a hue does not carry body text.
TIER_NORMAL, TIER_BRIGHT = 75.0, 60.0
_Lg = np.arange(0.05, 0.99, 0.0008)
_Cg = np.arange(P.C_FLOOR - 0.002, 0.40, 0.0008)


def _cloud(hue):
    """Every in-gamut 8-bit value at `hue` whose chroma still clears C_FLOOR, with its Lc."""
    LL, CC = np.meshgrid(_Lg, _Cg, indexing='ij')
    v = ok.from_lch_grid(LL, CC, hue)
    keep = np.all((v >= -0.5) & (v <= 255.5), axis=-1)
    seen = {}
    for i, j in np.argwhere(keep):
        hx = ok.hexs(np.clip(np.round(v[i, j]), 0, 255))
        if hx in seen:
            continue
        L, C, _ = ok.lch(hx)
        if C < P.C_FLOOR:                 # below the floor it carries no hue and is not that slot
            continue
        seen[hx] = (hx, apca.lc(hx, WHITE), L, C)
    return list(seen.values())


def terminal():
    """{slot: {'normal','bright','dim'}} plus a note per value. DERIVED, per slot."""
    out = {}
    for slot, exemplar in ANSI.items():
        hue = ok.lch(exemplar)[2]
        g = _cloud(hue)
        ceiling = max(g, key=lambda t: t[1])
        row = {}
        for nm, tier in (('normal', TIER_NORMAL), ('bright', TIER_BRIGHT)):
            good = [t for t in g if t[1] >= tier]
            if good:
                best = max(good, key=lambda t: t[3])       # most saturated value in the tier
                row[nm] = (best[0], best[1], '')
            else:
                # sRGB has no value at this hue that is both hue-bearing and this legible. The
                # slot takes its ceiling and the shortfall is recorded, not hidden -- the same
                # wall CURSOR hit in §2, and for the same reason.
                row[nm] = (ceiling[0], ceiling[1],
                           f'gamut ceiling, {tier - ceiling[1]:.1f} short of the {tier:.0f} tier')
        # dim is the ANSI faint attribute. On a light field de-emphasis by lightness means
        # de-emphasis by legibility, so the kit de-emphasises by CHROMA instead: the normal
        # slot's own lightness and hue, taken down to the chroma floor. Same Lc, least hue that
        # still counts as that hue. This is the kit's own thesis (§0d) used as a dimmer.
        L = ok.lch(row['normal'][0])[0]
        dim = next((h for h in (ok.hexs(ok.from_lch(L, c, hue))
                                for c in np.arange(P.C_FLOOR, P.C_FLOOR + 0.02, 0.0005))
                    if ok.lch(h)[1] >= P.C_FLOOR), row['normal'][0])
        row['dim'] = (dim, apca.lc(dim, WHITE), "the normal slot's lightness at the chroma floor")
        out[slot] = row
    return out


# --- what the checker knows ------------------------------------------------------------------
# Every hex the two .ron files may contain, and what it is. A value in the files that is not
# here is a defect: it is a colour nobody derived.
def authored():
    reg = {WHITE: 'WHITE', LIGHT: 'LIGHT', DARK: 'DARK', BLACK: 'BLACK',
           ACCENT: 'ACCENT', SELECT: 'SELECT', CURSOR: 'CURSOR'}
    reg.update({v: k for k, v in SEMANTIC.items()})
    for i, hx, note in neutrals():
        reg.setdefault(hx, f'neutral_{i}')
    for slot, hx, nm, t in swatches():
        reg.setdefault(hx, f'swatch {slot} ({nm}, Lc {t:.0f})')
    for slot, row in terminal().items():
        for tier, (hx, lc, note) in row.items():
            reg.setdefault(hx, f'ansi {tier} {slot}')
    return reg


HEX = re.compile(r'#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?\b')
# cosmic-config writes colours as RON decimal triples, not hex: Color((0.729412, 0.678431, 0.698039)).
# HEX cannot see them, so a value installed from that tree would go unchecked -- which is how the panel
# background got in. Same rule, different notation.
RON_COLOR = re.compile(r'Color\(\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*(?:,\s*[0-9.]+\s*)?\)\)')
CONFIG = os.path.join(COSMIC, 'cosmic-config')

# install.sh does not only COPY colours, it WRITES two of its own, in two more notations, and neither
# lands in a file this checker would otherwise open:
#   scaling_mode: Fit((0.062745, 0.031373, 0.047059))   the --art letterbox fill, a bare RON tuple
#   bytes([0x10, 0x08, 0x0C]) * w                       the solid PNG the default background is
# Same rule as the panel background (§8): a value the checker cannot read is a value nobody is
# checking. These two are the whole set -- if a third notation appears in the installer, it belongs here.
RON_FIT = re.compile(r'Fit\(\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)\)')
PY_BYTES = re.compile(r'bytes\(\[\s*0x([0-9A-Fa-f]{2})\s*,\s*0x([0-9A-Fa-f]{2})\s*,\s*0x([0-9A-Fa-f]{2})\s*\]\)')
INSTALLER = os.path.join(COSMIC, 'install.sh')


def check_installer(reg):
    """Every colour install.sh writes itself, as opposed to copies. Returns the defect count."""
    if not os.path.isfile(INSTALLER):
        return 0
    body = open(INSTALLER, errors='ignore').read()
    vals = [('#%02X%02X%02X' % tuple(round(float(c) * 255) for c in m.groups()), 'RON Fit fill')
            for m in RON_FIT.finditer(body)]
    vals += [('#' + ''.join(m.groups()).upper(), 'PNG byte row') for m in PY_BYTES.finditer(body)]
    bad, rows = 0, []
    for hx, form in vals:
        role, note = reg.get(hx), ''
        if role is None:
            note = 'NOT DERIVED BY ANY LADDER'; bad += 1
        elif P.reserved(hx):
            # The point of writing the entry by hand: cosmic-settings would put #000000 here.
            note = 'reserved by §3 -- the installer must not write this'; bad += 1
        if not P.clear(hx) and role not in SEMANTIC:
            note = (note + ' POLE: chrome must clear every pole').strip(); bad += 1
        rows.append(f"  {hx} {form:13} {str(role):20} {note}")
    print(f"\ninstall.sh: {len(rows)} colour(s) the installer writes itself")
    for r in rows:
        print(r)
    return bad


def check_config(reg):
    """Every colour in the cosmic-config tree the installer copies. Returns the defect count."""
    if not os.path.isdir(CONFIG):
        return 0
    bad, rows = 0, []
    for root, _, files in os.walk(CONFIG):
        for fn in sorted(files):
            path = os.path.join(root, fn)
            body = re.sub(r'^\s*//.*$', '', open(path, errors='ignore').read(), flags=re.M)
            vals = [('#%02X%02X%02X' % tuple(round(float(c) * 255) for c in m.groups()), 'Color triple')
                    for m in RON_COLOR.finditer(body)]
            vals += [('#' + m.group(1).upper(), 'hex') for m in HEX.finditer(body)]
            for hx, form in vals:
                role, note = reg.get(hx), ''
                if role is None:
                    note = 'NOT DERIVED BY ANY LADDER'; bad += 1
                elif P.reserved(hx):
                    note = 'reserved, legend use only -- check the context'
                if not P.clear(hx) and role not in SEMANTIC:
                    note = (note + ' POLE: chrome must clear every pole').strip(); bad += 1
                rel = os.path.relpath(path, COSMIC)
                rows.append(f"  {hx} {form:13} {str(role):20} {rel:56} {note}")
    print(f"\ncosmic-config: {len(rows)} colour(s) in the tree install.sh copies")
    for r in rows:
        print(r)
    return bad


def check():
    reg = authored()
    files = [f for f in ('remainder.ron', 'remainder-term.ron') if os.path.exists(os.path.join(COSMIC, f))]
    if not files:
        print('cosmic: nothing committed in worksafe/cosmic yet'); return False
    bad = 0
    for fn in files:
        text = open(os.path.join(COSMIC, fn)).read()
        body = re.sub(r'^\s*//.*$', '', text, flags=re.M)      # comments quote values on purpose
        seen = {}
        for m in HEX.finditer(body):
            seen.setdefault('#' + m.group(1).upper(), 0)
            seen['#' + m.group(1).upper()] += 1
        print(f"\n{fn}: {len(seen)} distinct values")
        for hx, n in sorted(seen.items()):
            role = reg.get(hx)
            cl, rsv = P.clear(hx), P.reserved(hx)
            note = ''
            if role is None:
                note = 'NOT DERIVED BY ANY LADDER'; bad += 1
            elif rsv:
                # §3 reserves #FFFFFF and #000000 for legend on a semantic field. In these
                # files the only legal use is the legend of a SUCCESS/WARNING/DESTRUCTIVE fill.
                note = 'reserved, legend use only -- check the context'
            # Two kinds of value are IN a pole on purpose and are not chrome: §3's three semantic
            # hues, which are the poles, and the terminal's ANSI slots, which are content (§0a).
            # Everything else in these files is chrome and must clear (principle 1).
            if not cl and role not in SEMANTIC and not str(role).startswith('ansi'):
                note = (note + ' POLE: chrome must clear every pole').strip(); bad += 1
            fam, gap, req = P.clearance(hx)
            tag = 'neutral' if not P.readable(hx) else f'{gap:5.1f}/{req:4.1f} {fam}'
            print(f"  {hx} x{n:<3} {str(role):38} {tag:24} {note}")
    bad += check_config(reg)
    bad += check_installer(reg)
    print(f"\npole test: {'every value clears' if not bad else str(bad) + ' DEFECT(S)'}")
    return bad == 0


def _print_derivations():
    print("=== eleven neutral slots: OKLab L interpolated at the cast, anchored on §2's four ===")
    prev = None
    for i, hx, note in neutrals():
        L, C, h = ok.lch(hx)
        dp = '' if prev is None else f'dE_prev {ok.delta_e(hx, prev):4.1f}'
        print(f"  neutral_{i:<2} {hx}  L {L:.4f} C {C:.4f} h {h:5.1f}  {dp:14} {note}")
        prev = hx

    print(f"\n=== nine accent swatches: 3 hues in the working arc x 3 WHITE-text tiers ===")
    for slot, hx, nm, t in swatches():
        L, C, h = ok.lch(hx)
        fam, gap, req = P.clearance(hx)
        mine = {ACCENT: '  = ACCENT', SELECT: '  = SELECT'}.get(hx, '')
        print(f"  {slot:17} {hx}  {nm:14} tier {t:4.0f}  WHITE on it Lc {apca.lc(WHITE, hx):6.1f}  "
              f"clears {gap:5.1f} (needs {req:4.1f}){mine}")

    print(f"\n=== sixteen terminal slots: the ANSI exemplar's hue, solved on the WHITE field ===")
    print(f"  {'slot':9} {'exemplar':9} {'normal':9} {'Lc':>6}   {'bright':9} {'Lc':>6}   {'dim':9} {'Lc':>6}")
    term = terminal()
    for slot, exemplar in ANSI.items():
        r = term[slot]
        print(f"  {slot:9} {exemplar:9} {r['normal'][0]:9} {r['normal'][1]:6.1f}   "
              f"{r['bright'][0]:9} {r['bright'][1]:6.1f}   {r['dim'][0]:9} {r['dim'][1]:6.1f}")
    for slot, r in term.items():
        for tier, (hx, lc, note) in r.items():
            if note and 'ceiling' in note:
                print(f"  ! {slot} {tier} {hx}: {note}")
    print("  neutral slots: normal black BLACK, normal white LIGHT, bright black DARK, "
          "bright white WHITE\n    -- §2's four-step ladder onto the four neutral ANSI slots.")
    print(f"  ANSI white as TEXT on the WHITE field is Lc {apca.lc(LIGHT, WHITE):.1f}: a light-field "
          "terminal cannot\n    make that slot read, and the kit does not pretend otherwise.")


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations()
        sys.exit(0)
    sys.exit(0 if check() else 1)
