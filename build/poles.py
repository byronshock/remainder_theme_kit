"""Remainder pole test. AUTHORITY.md is the authority.

The parent kit (De Stijl) asks whether a color lies ON its palette's lines. Remainder asks
the opposite question of the same machinery: how far is this color from every pole of the
realized color space? Chrome must be CLEAR of every pole. Nothing else is chrome.

A pole is not a point. It is an arc in OKLCh hue, and its reach shrinks with the candidate's
chroma: a near-neutral carries no readable hue and cannot be mistaken for a signal. So a
color is clear of the poles if EITHER
    its chroma is below C_FLOOR                          (carries no readable hue), OR
    its hue clears every pole arc by DELTA_REQ(chroma)   (reads as a different color)

Both bars are derived from the pole set, never declared:
    C_FLOOR   = chroma of the faintest realized pole. A signal shipped at that chroma is
                read as a signal; below it, no hue is doing semantic work.
    DELTA_MAX = the poles' own nearest-neighbour angular separation. If two distinct signals
                sit that far apart and users tell them apart, that much is enough.
    DELTA_REQ(C) = DELTA_MAX * min(1, C / C_REF), C_REF = median realized pole chroma.
                Full clearance is demanded of a color as saturated as the signals themselves;
                proportionally less as it fades toward the floor.

Usage: python3 build/poles.py '#8E3B6B' '#FF6B6B' ...      is it clear of every pole?
       python3 build/poles.py --bars                        show the derived bars
   or  import and call.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok

_here = os.path.dirname(os.path.abspath(__file__))
POLES = json.load(open(os.path.join(_here, '..', 'poles.json')))

# --- the pole arcs, measured from the realized members ---------------------------------
ARCS, _CHROMA = {}, []
for _fam, _d in POLES['families'].items():
    _v = [ok.lch(h) for h in _d['members'].values()]
    ARCS[_fam] = (min(x[2] for x in _v), max(x[2] for x in _v))
    _CHROMA += [x[1] for x in _v]

C_FLOOR = float(min(_CHROMA))                      # faintest realized pole
C_REF = float(np.median(_CHROMA))                  # a signal's typical chroma

# DELTA_MAX: the poles' own nearest-neighbour separation, over the arcs in hue order.
_order = sorted(ARCS.items(), key=lambda kv: kv[1][0])
_gaps = [((_order[(i + 1) % len(_order)][1][0] - hi) % 360, fam, _order[(i + 1) % len(_order)][0])
         for i, (fam, (lo, hi)) in enumerate(_order)]
DELTA_MAX = float(np.ceil(min(g for g, *_ in _gaps)))

# The widest unclaimed arc: where the kit's own hues live.
_w = max(_gaps)
HOME = ((_order[[f for f, _ in _order].index(_w[1])][1][1] + DELTA_MAX) % 360,
        (ARCS[_w[2]][0] - DELTA_MAX) % 360)        # (lo, hi) after guarding both ends


def delta_req(C):
    """Angular clearance demanded of a color at chroma C."""
    return DELTA_MAX * min(1.0, C / C_REF)


def clearance(p):
    """(family, gap, required) for the pole this color comes nearest to reading as."""
    L, C, h = ok.lch(p)
    req = delta_req(C)
    fam, gap = min(((f, ok.arcgap(h, lo, hi)) for f, (lo, hi) in ARCS.items()), key=lambda x: x[1])
    return fam, gap, req


# --- reserved values (AUTHORITY.md 3) ---------------------------------------------------
# Pure white and pure black are legend on a semantic field, as on a highway sign, and are a
# defect anywhere else. The pole test cannot catch them: both have zero chroma and pass as
# neutrals. They are reserved by rule, not by measurement, for two reasons --
#   1. they are the legend, and a legend that also appears as chrome stops being a legend;
#   2. #FFFFFF is what an unstyled surface renders. A field painted with it cannot be told
#      apart from a theme that failed to load, which is a signal the kit did not intend.
# The kit's own ladder ends short of both on purpose (WHITE L 0.93, BLACK L 0.19).
RESERVED = {'#FFFFFF': 'legend on a semantic field (also: what an unstyled surface renders)',
            '#000000': 'legend on a semantic field'}


def reserved(p):
    """Is this a value reserved for legend use (AUTHORITY.md 3)?"""
    return (p.upper() if isinstance(p, str) else '') in RESERVED


def readable(p):
    """Does this color carry a hue a user could read as a signal?"""
    return ok.lch(p)[1] >= C_FLOOR


def clear(p):
    """Is this color clear of every pole (AUTHORITY.md 1)?"""
    if not readable(p):
        return True
    _, gap, req = clearance(p)
    return gap >= req


def report(p, legend=False):
    L, C, h = ok.lch(p)
    fam, gap, req = clearance(p)
    if reserved(p) and not legend:
        return f"{p:9} RESERVED {RESERVED[p.upper()]}"
    if not readable(p):
        return f"{p:9} neutral  chroma {C:.3f} < {C_FLOOR:.3f}, carries no readable hue  (L {L:.2f}, h {h:5.1f})"
    return (f"{p:9} {'clear ' if gap >= req else 'POLE  '}  {gap:5.1f}deg from {fam:12} "
            f"needs {req:4.1f}  (L {L:.2f}, C {C:.3f}, h {h:5.1f})")


if __name__ == '__main__':
    if '--bars' in sys.argv or len(sys.argv) == 1:
        print(f"C_FLOOR   {C_FLOOR:.3f}   faintest realized pole")
        print(f"C_REF     {C_REF:.3f}   median realized pole chroma")
        print(f"DELTA_MAX {DELTA_MAX:.0f}deg     poles' own nearest-neighbour separation")
        print(f"HOME arc  {HOME[0]:.1f} -> {HOME[1]:.1f}   the widest unclaimed arc, guarded both ends")
        print("\npole arcs (OKLCh hue):")
        for f, (lo, hi) in sorted(ARCS.items(), key=lambda kv: kv[1][0]):
            print(f"  {f:12} {lo:6.1f} - {hi:6.1f}")
        sys.exit(0)
    legend = '--legend' in sys.argv      # these values ARE being authored as legend on a §3 field
    bad = 0
    for h in [a for a in sys.argv[1:] if a != '--legend']:
        print(report(h, legend))
        bad += not (clear(h) and (legend or not reserved(h)))
    sys.exit(1 if bad else 0)
