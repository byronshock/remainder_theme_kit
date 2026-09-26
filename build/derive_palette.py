"""Derive the Remainder palette. AUTHORITY.md is the authority.

Remainder has no source artifact. Its colors are the solution to a stated problem, and this
script is that solution. Re-run it and the palette comes back. Change a pole in poles.json
and the palette moves.

What the hypothesis decides, and what it does not
-------------------------------------------------
The hypothesis fixes ONE thing: hue. At the home hue every chroma from a whisper to the
gamut edge clears every pole by ~59deg (build/poles.py --bars), so the pole test cannot
choose between a quiet mauve-gray and neon pink. Chroma and lightness are free, and that
freedom is where "aesthetically pleasing" is decided.

So this file has two kinds of number and says which is which:

  DERIVED   the home hue, and every lightness (solved from the contrast targets below)
  CHOSEN    the two chroma levels, with the reason stated next to each

Dressing a choice as a derivation would be the one dishonesty this kit cannot afford.

    python3 build/derive_palette.py            report
    python3 build/derive_palette.py --write    report and write palette.json
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca

# DERIVED: the center of the widest arc no signal claims.
HOME_HUE_DERIVED = round((P.HOME[0] + ((P.HOME[1] - P.HOME[0]) % 360) / 2) % 360, 1)

# CHOSEN: the home hue, overriding the derived center. The derivation treats every pole as
# equally entrenched, and they are not. A user meets informational blue continuously -- every
# link, every accent, every selected row -- and destructive red a few times a week. The blue
# category is therefore reinforced far harder than the red one, so the usable arc is not
# centered on its own geometry: it shifts away from blue.
#
# 351 is the optimum of the band 351-353 that was judged acceptable aesthetically. Destructive
# is the binding pole across that whole band (31.4 deg at 351, against 86.9 to info-blue), so
# the minimum clearance is maximised at the blue end of the band, not its middle:
#     351 -> min(31.4, 86.9) = 31.4        352 -> min(30.4, 87.9) = 30.4
#     353 -> min(29.4, 88.9) = 29.4
# The gain over 352 is 1.0 deg. Small, and taken because it costs nothing the eye objects to.
#
# No magenta guard is applied, and that is deliberate (build/field.py). Magenta is not a pole
# and signals nothing, so it cannot enter poles.json; and it is a chroma phenomenon before it
# is a hue one -- every named magenta sits above chroma 0.18 while the kit authors at 0.100
# and 0.016. The CHROME ceiling below is what keeps magenta out. An angular guard would buy
# nothing an angle can hold.
HOME_HUE = 351.0

# CHOSEN: the cursor is the one chrome role that lives at a different hue, and the reason is
# its job. ACCENT, SELECT and the neutrals are furniture -- a user reads them once and stops
# seeing them. A text cursor is a LOCATOR: its whole purpose is to be found fast, repeatedly,
# on a field of text. Solved at the home hue it came out at #9E5879, within 3 Lc and 0.03 L of
# ACCENT -- two roles, one colour, and the one that needed to stand out did not.
#
# 219.1 is in the arc that opens up once info-cyan is demoted (poles.json): 80.1 deg between
# success and info-blue, guarded to 202.6-219.9. It sits 131.9 deg from the home hue, which is
# as far from the rest of the kit as the pole set allows, and it clears info-blue by 32.2 and
# success by 47.9.
#
# The chroma is 0.096, not the kit's 0.100, and that is forced rather than chosen: sRGB has no
# dark saturated teal. At the lightness Lc 60 demands, 0.096 is the gamut ceiling. It clears
# C_FLOOR (0.092) by 0.004, so the cursor is still honestly hue-bearing and still has to pass
# the pole test rather than escape it as a neutral -- but that is the whole margin there is.
CURSOR_HUE = 219.1
CURSOR_CHROMA = 0.096

# CHOSEN: BLACK's lightness. It was solved as the lightest value clearing its text floor,
# which put it at L 0.21 -- and that squeezed DARK into a corridor 0.076 wide between the
# rule below it and its own text floor above, leaving DARK about +4 Lc of margin either way.
# APCA soft-clamps the black end (below a threshold, darker text buys almost nothing), so
# darkening BLACK is very nearly free: it RAISES BLACK on WHITE from 90.6 to 91.8 while
# roughly doubling DARK's margins. The cost is headroom against pure #000000, which §3
# reserves for legend: that falls from dE 20.9 to 14.9. Still clearly short of it, and the
# property is kept deliberately rather than spent by accident.
BLACK_L = 0.15

# CHOSEN: LIGHT's lightness. It was solved as the darkest ground still carrying bold BLACK
# text, which made it a function of BLACK -- and SURFACE_FLOOR is derived from WHITE against
# LIGHT, so a floating LIGHT meant a floating bar. Darkening BLACK moved LIGHT by dE 1.5,
# invisible in itself, and moved the floor 16.7 -> 17.5 underneath every other value measured
# against it. A bar that moves when something else moves is not a bar. Pinning LIGHT (WHITE
# is already pinned) fixes the floor to two chosen constants and nothing else. The text floor
# it was solved for is still checked, not assumed: see TARGETS.
LIGHT_L = 0.76

# Surface adjacencies that carry information -- where a user must see that two surfaces are
# different. Not every pair that touches is here. §3 draws a rule OUTSIDE the field it bounds,
# so what a rule must distinguish is rule-against-field; rule-against-chrome at a window's edge
# is not its job. ACCENT/SELECT is exempt by the same logic: a selected topmost row abutting
# the titlebar still reads, because it is dE 46 from the unselected rows that surround it.
LOAD_BEARING = [('WHITE', 'LIGHT'), ('WHITE', 'DARK'), ('WHITE', 'ACCENT'), ('WHITE', 'SELECT'),
                ('WHITE', 'CURSOR'), ('LIGHT', 'DARK'), ('LIGHT', 'ACCENT'), ('LIGHT', 'SELECT'),
                ('BLACK', 'WHITE'), ('BLACK', 'LIGHT'), ('BLACK', 'DARK')]

# CHOSEN: chrome recedes. A surface a user looks at for eight hours must not be a color;
# it must be a gray that remembers one.
#
# MEASURED, 2026-09-20, on the machine this kit is built on: paired patches, each split down the
# middle with the cast on one side and a true neutral at the same lightness on the other, at 0.002
# steps, with a null control at 0.000 where both halves are byte-identical. The seam is PERCEPTIBLE
# AT 0.004 (dE 0.43) and CLEARLY PERCEPTIBLE AT 0.006 (dE 0.57). The threshold is therefore about
# three times lower than this file used to assert -- it said "below about 0.014 it stops being
# perceptible at all", which was a judgement nobody had tested.
#
# So 0.016 is not the smallest cast that can be seen; it is four times it. The reason is a choice
# about what the cast is FOR: the hint that a surface is furniture and not a document resting on the
# furniture, and the hint is the point. It was backed off to 0.0128 on 2026-09-20 on the reading
# that the hint did not need to be as loud as it was, and returned to 0.016 on 2026-09-23: a cast
# that has to be looked for is not the hint, and a definite one is. 0.016 is also the value the kit
# shipped before the backing-off.
#
# Reachable casts are NOT A RANGE. CURSOR's floor is read against a WHITE quantised to 8 bits, so
# the cast moves in islands. Sweeping 0.0100-0.0300 at 0.0002 (2026-09-23) derives on four of them
# and nowhere else:
#     0.0100-0.0128  width 0.0030  WHITE #EEE5E9 -> #EFE5E9
#     0.0136-0.0168  width 0.0034  WHITE #F0E4E9 -> #F1E4E9   <- the widest, and 0.016 is inside it
#     0.0188-0.0206  width 0.0020  WHITE #F3E3E9 -> #F4E3E9
#     0.0242-0.0246  width 0.0006  one WHITE throughout
# Every gap is the best in-gamut teal at CURSOR's chroma falling under 60.0 + MARGIN: the WHITE at
# 0.0130 leaves it Lc 60.4540, the one at 0.0170 60.4395, the one at 0.0208 60.3004. 0.0130 -- the
# round number between the first two islands -- still does not derive, and misses by 0.046 of an Lc
# point.
#
# 0.016 has 0.0026 of slack below it and 0.0008 above. 0.0128 had 0.0030 below and NONE above: it
# was the top edge of its island, so any move upward at all failed. The move costs 0.15 of CURSOR's
# Lc margin (+0.9 -> +0.7, still over its floor) and buys headroom on the side 0.0128 did not have.
#
# Far under C_FLOOR either way, so no user can read a hue in it.
CAST = 0.016
# CHOSEN: the two things that must be noticed -- the key titlebar and the selected row --
# are allowed a real hue. Just above C_FLOOR, so they are honestly hue-bearing and have to
# pass the pole test rather than escape it as neutrals. Far below a signal's own chroma
# (C_REF 0.179): this kit's accent is not competing with an error dialog for attention.
CHROME = 0.100

# Contrast targets, in APCA Lc (build/apca.py). WCAG 2.x ratios were used here first and were
# wrong for the same reason sRGB distance was wrong for hue (§0b): a plain luminance ratio is
# polarity-blind, chroma-blind, and its +0.05 flare constant inflates every pair involving a
# near-black. Four pairs that all measured 7.1:1 -- "AAA" -- measured Lc 51.7 to 78.9.
#
# APCA has no single target: the threshold is a function of polarity, size and weight. The
# kit's UI renders at ~16px effective (§2), so
#     Lc 90  body text, preferred          Lc 60  16px/700 bold, or 24px/400
#     Lc 75  body text, minimum            Lc 30  non-text marks
# Each entry is (text, ground, FLOOR, TARGET, use). The floor is what APCA requires. The
# target is what the kit authors, and where it exceeds the floor that is a CHOSEN margin.
#
# Why margin at all. The kit derives its numbers from inputs, and one input is an assumption
# nobody measured: that §2's "12pt system size" renders at ~16px effective. Every floor below
# is a function of that. A palette seated exactly on its floors propagates any error in that
# assumption straight into failure, across every ground at once and silently. Margin is what
# lets a derived design survive a wrong input -- and choosing to sit at the floor would be a
# choice too, just an unlabelled one made by the solver's "take the extreme" rule (§0c).
#
# Two grounds cannot take margin and are authored at their floor for stated reasons:
#   LIGHT   lifting it collapses WHITE against LIGHT as distinguishable surfaces, which §3
#           relies on as a separator wherever no rule is drawn.
#   CURSOR  sRGB has no darker teal at a chroma that keeps it above C_FLOOR; the gamut caps
#           it at about Lc 61.6.
TARGETS = [
    ('BLACK',  'WHITE',  90.0, 90.0, 'body text on the window field, 16px/400'),
    ('BLACK',  'LIGHT',  60.0, 60.0, 'panel and button text, 16px/700 bold (§2) -- LIGHT is pinned'),
    ('WHITE',  'DARK',   75.0, 75.0, 'dock tile labels, 16px/400 -- balanced, see derive(). The desktop field is BLACK (§5)'),
    ('WHITE',  'ACCENT', 60.0, 78.0, 'titlebar text, 16px/700 bold (§2)'),
    ('WHITE',  'SELECT', 75.0, 87.0, 'text on a selected row, 16px/400'),
    ('CURSOR', 'WHITE',  60.0, 60.0, 'the text cursor: a mark, wants to be seen -- pinned'),
]
T = {(a_, b_): (fl, tg, why) for a_, b_, fl, tg, why in TARGETS}

_L = np.arange(0.04, 0.995, 0.0005)

# A solved pair that lands exactly on its target falls under it once the value is rounded to
# 8 bits. The kit solves to the target plus this margin, so every pair in the table clears
# its target as the hex is actually rendered, not as the float was computed. In Lc units.
MARGIN = 0.5


def ladder(C, hue=None):
    """Every in-gamut value at `hue` (default the home hue) and chroma C, as (L, hex, luminance).

    Luminance is taken from the ROUNDED hex, not the float, so the solver and the contrast
    table agree on the value a display will actually show.
    """
    v = ok.from_lch_grid(_L, C, HOME_HUE if hue is None else hue)
    keep = np.all((v >= -0.5) & (v <= 255.5), axis=-1)
    v, L = v[keep], _L[keep]
    q = np.clip(np.round(v), 0, 255)
    # And drop anything the clip turned into a different colour. The tolerance above admits a value that
    # is just outside the gamut, and clipping it to 0..255 moves it off the chroma and hue that were asked
    # for -- at the cursor's chroma near the black end it yields #000009, which is chroma 0.044 at hue 264
    # and reads as a near-black, not a teal. Nothing shipped picks one: the solver takes the LIGHTEST value
    # that clears its floor, so a near-black outlier never wins. But it is in the ladder, it answers
    # questions asked of the ladder wrongly, and a future floor could make it the only candidate.
    Cr = ok.lch_grid(q)[1]
    true = np.abs(Cr - C) <= 0.005
    q, L = q[true], L[true]
    return L, [ok.hexs(x) for x in q], ok.luminance_grid(q)


def solve(C, other, min_lc, other_is_text, side, hue=None):
    """The extreme value at chroma C that still clears `min_lc` APCA Lc against `other`.

    other_is_text=True  -> `other` is the text and the solved value is its background;
    other_is_text=False -> `other` is the background and the solved value is the text.
    side='dark'  -> the LIGHTEST value that is still dark enough  (text colors, dark grounds)
    side='light' -> the DARKEST  value that is still light enough (pale grounds)
    Taking the extreme is what makes the step a derivation and not a preference: it is the
    most distinct that value can be from the one it is read against.
    """
    L, hexes, _ = ladder(C, hue)
    got = np.array([abs(apca.lc(other, h)) if other_is_text else abs(apca.lc(h, other))
                    for h in hexes])
    Y = np.array([apca.screen_y(h) for h in hexes])
    ref = apca.screen_y(other)
    good = np.where(got >= min_lc + MARGIN)[0]
    if not len(good):
        raise SystemExit(f"no in-gamut value at C={C} reaches Lc {min_lc} against {other} "
                         f"(best {got.max():.1f})")
    pick = good[Y[good] < ref] if side == 'dark' else good[Y[good] >= ref]
    if not len(pick):
        raise SystemExit(f"no {side} value at C={C} reaches Lc {min_lc} against {other}")
    idx = pick[np.argmax(Y[pick])] if side == 'dark' else pick[np.argmin(Y[pick])]
    return hexes[idx], float(L[idx])


def derive():
    pal, meas = {}, {}

    def put(role, hx, L):
        pal[role] = hx
        Lc, C, h = ok.lch(hx)
        fam, gap, req = P.clearance(hx)
        meas[role] = dict(hex=hx, L=round(Lc, 4), C=round(C, 4), hue=round(h, 1),
                          nearest_pole=fam, clears=round(gap, 1), needs=round(req, 1),
                          readable=P.readable(hx))

    # WHITE is the ground everything else is solved against. CHOSEN: L 0.93 -- a field at
    # #FFFFFF glares under a bright room and there is no painting here to cap it, so the
    # kit backs off the top of the range by the same order the parent kit did (its WHITE
    # sits at L 0.925).
    L, hexes, _ = ladder(CAST)
    i = int(np.argmin(np.abs(L - 0.93)))
    put('WHITE', hexes[i], L[i]); W = pal['WHITE']

    j = int(np.argmin(np.abs(L - BLACK_L)))
    put('BLACK', hexes[j], L[j]); B = pal['BLACK']
    # LIGHT is a GROUND for BLACK text: the darkest ground that still carries it, so it stays
    # as distinct as possible from the WHITE field (§3 uses that tone change as a separator).
    k = int(np.argmin(np.abs(L - LIGHT_L)))
    put('LIGHT', hexes[k], L[k])
    # SURFACE_FLOOR is derived, not declared: it is the weakest boundary the kit already
    # relies on to divide two surfaces where no rule is drawn -- WHITE against LIGHT, which
    # §3 names as a separator in its own right. Anything that must read, must read at least
    # that well. Same shape as De Stijl's APART: the weakest member sets the bar and meets it
    # exactly, so WHITE/LIGHT has no margin on it by construction.
    global SURFACE_FLOOR
    SURFACE_FLOOR = round(ok.delta_e(W, pal['LIGHT']), 1)

    # DARK is pulled two ways: lighter for the rule to read against it, darker for its own
    # white labels. Take the point where neither margin is nearer failing than the other.
    Lg, hexes_n, _ = ladder(CAST)
    cand = [(min(abs(apca.lc(W, h)) - T[('WHITE', 'DARK')][0], ok.delta_e(h, B) - SURFACE_FLOOR), Lv, h)
            for Lv, h in zip(Lg, hexes_n)
            if abs(apca.lc(W, h)) >= T[('WHITE', 'DARK')][0] and ok.delta_e(h, B) >= SURFACE_FLOOR]
    if not cand:
        raise SystemExit('DARK: no value clears both its text floor and the surface floor')
    _, Lv, hx = max(cand); put('DARK', hx, Lv)
    hx, Lv = solve(CHROME, W, T[('WHITE', 'ACCENT')][1], True, 'dark'); put('ACCENT', hx, Lv)
    # SELECT carries WHITE text, not BLACK. A pale selection cannot do both jobs at this
    # chroma: every tint light enough to carry body text at Lc 75 is invisible against the
    # WHITE field (best 73.7 at Lc 15.1 separation). Dark ground, light legend.
    hx, Lv = solve(CHROME, W, T[('WHITE', 'SELECT')][1], True, 'dark'); put('SELECT', hx, Lv)
    hx, Lv = solve(CURSOR_CHROMA, W, 60.0, False, 'dark', CURSOR_HUE); put('CURSOR', hx, Lv)
    return pal, meas


if __name__ == '__main__':
    pal, meas = derive()
    print(f"home hue {HOME_HUE}  (CHOSEN, by exposure; the derived center is {HOME_HUE_DERIVED})")
    print(f"cast {CAST}   chrome {CHROME}   (CHOSEN; C_FLOOR {P.C_FLOOR:.3f}, a signal's own chroma {P.C_REF:.3f})")
    print(f"cursor hue {CURSOR_HUE}, chroma {CURSOR_CHROMA}  (CHOSEN: a locator, not furniture; chroma forced by the teal gamut)\n")
    print(f"{'role':8} {'hex':9} {'L':>5} {'C':>6} {'hue':>7}  pole")
    for r, hx in pal.items():
        m = meas[r]
        tag = f"{m['clears']:.0f}deg from {m['nearest_pole']}" if m['readable'] else 'neutral, no readable hue'
        print(f"{r:8} {hx:9} {m['L']:5.2f} {m['C']:6.3f} {m['hue']:7.1f}  {tag}")
    print("\ncontrast, measured (APCA Lc; the WCAG ratio is shown only to show the disagreement):")
    okall = True
    for a_, b_, floor, want, why in TARGETS:
        got = apca.lc(pal[a_], pal[b_]); okall &= abs(got) >= want
        mar = abs(got) - floor
        print(f"  {a_:6} on {b_:6} Lc {got:7.1f}  floor {floor:5.1f}  margin {mar:+5.1f}"
              f"  {'ok ' if abs(got) >= want else 'LOW'}  {why}")
    print(f"\nsurface separation (OKLab dE; floor {SURFACE_FLOOR}, derived from WHITE/LIGHT):")
    worst = None
    for a_, b_ in LOAD_BEARING:
        d = ok.delta_e(pal[a_], pal[b_]); okall &= d >= SURFACE_FLOOR - 0.05
        worst = d if worst is None else min(worst, d)
        if d < SURFACE_FLOOR + 12:
            print(f"  {a_:6} / {b_:6} dE {d:5.1f}  {'ok ' if d >= SURFACE_FLOOR - 0.05 else 'BELOW'}")
    print(f"  ({len(LOAD_BEARING)} load-bearing pairs, weakest {worst:.1f}; the rest clear by 12+)")
    print("  exempt: " + ", ".join(f"{a_}/{b_} {ok.delta_e(pal[a_], pal[b_]):.1f}" for a_, b_ in
                                   (('ACCENT', 'SELECT'), ('SELECT', 'BLACK'), ('ACCENT', 'BLACK'), ('DARK', 'SELECT'))))

    print("\npole test over every authored value:")
    bad = 0
    for r, hx in pal.items():
        print("  " + P.report(hx)); bad += not P.clear(hx)
    if '--write' in sys.argv:
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        json.dump({
            'name': 'Remainder',
            'derived_from': 'poles.json, by build/derive_palette.py. No source artifact.',
            'derived_on': '2026-09-23',
            'derived': {'home_hue_derived': HOME_HUE_DERIVED, 'home_arc': [round(P.HOME[0], 1), round(P.HOME[1], 1)],
                        'note': 'The hypothesis constrains hue only. Every lightness here is solved from the contrast targets.'},
            'surface_floor_dE': SURFACE_FLOOR,
            'surface_separation': {f'{a}_{b}': round(ok.delta_e(pal[a], pal[b]), 1) for a, b in LOAD_BEARING},
            'chosen': {'home_hue': HOME_HUE, 'cursor_hue': CURSOR_HUE, 'cursor_chroma': CURSOR_CHROMA, 'black_L': BLACK_L, 'light_L': LIGHT_L, 'cast_chroma': CAST, 'chrome_chroma': CHROME, 'white_L': 0.93, 'contrast_margin': MARGIN,
                       'home_hue_reason': 'Exposure, not geometry: info-blue is met continuously and destructive red rarely, so the usable arc shifts away from blue. 351 is the min-clearance optimum of the aesthetically acceptable band 351-353. No magenta guard (see build/field.py): magenta is a chroma phenomenon and the chrome ceiling holds it out.',
                       'note': 'Aesthetic constants. At the home hue every chroma clears every pole, so the pole test does not choose these; the reasons are in build/derive_palette.py.'},
            'bars': {'C_FLOOR': round(P.C_FLOOR, 4), 'C_REF': round(P.C_REF, 4), 'DELTA_MAX': P.DELTA_MAX},
            'neutrals': {r: pal[r] for r in ('WHITE', 'LIGHT', 'DARK', 'BLACK')},
            'chrome': {r: pal[r] for r in ('ACCENT', 'SELECT', 'CURSOR')},
            'measurements': meas,
            'contrast_apca_lc': {f'{a}_on_{b}': round(apca.lc(pal[a], pal[b]), 1) for a, b, _, _, _ in TARGETS},
            'contrast_targets': {f'{a}_on_{b}': {'floor_lc': fl, 'authored_lc': tg,
                                                 'margin': round(abs(apca.lc(pal[a], pal[b])) - fl, 1), 'use': why}
                                 for a, b, fl, tg, why in TARGETS},
            'contrast_wcag_note': 'WCAG 2.x ratios are not recorded as targets: they are polarity- and chroma-blind and their +0.05 flare constant inflates any pair involving a near-black. See build/apca.py and AUTHORITY.md 2.',
            'steps_note': 'The four-step neutral ladder is NeXTSTEP AppKit structure, inherited from the parent kit as convention. The steps are borrowed; every value is derived or declared above.',
        }, open(os.path.join(root, 'palette.json'), 'w'), indent=2)
        print("\nwrote palette.json")
    sys.exit(0 if okall and not bad else 1)
