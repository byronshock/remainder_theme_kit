"""Remainder space: project sRGB onto a ramp through the values the kit authors. AUTHORITY.md is the authority.

The parent kit's `mondrian_space.py` sends a pixel to the nearest of five pigments measured from a
painting, flat -- a poster, no shading. Remainder shipped the same shape until 2026-09-19: nearest of
its own seven values in OKLab dE, a gray guard at C_FLOOR, a 3x3 edge vote. What replaced it, and why.

NEAREST-OF-SEVEN DECIDES LIGHTNESS BY A DISTANCE HUE ALSO VOTES IN. Two regions a user reads as
light-and-dark can land on anchors that invert that order -- so the repaint costs exactly what a
dock is for: telling icons apart at a glance, and reading the shape inside each one. Measured over
six of this machine's own icons, the projection it replaces held per-pixel lightness at r 0.906 and
its ORDERING at rho 0.759: a quarter of the light-and-dark inside every icon was reassigned. A
quarter of the opaque pixels, 25.3%, came out CURSOR teal.

So the projection now keeps lightness and replaces everything else with a function of it:

    BLACK .148  ->  SELECT .308  ->  ACCENT .426  ->  LIGHT .760  ->  WHITE .931

Hue and chroma are interpolated in OKLab between those knots, indexed by the pixel's own lightness.
Neutral at both ends, the home hue through the middle: a duotone print, where the ink is the kit's.

  WHAT IT KEEPS. Lightness, per pixel: on the ramp itself output L differs from input by at most
  0.0023, which is 8-bit rounding and a tenth of a JND. Over whole icons that reads as r 0.997 and
  rho 0.994 against the source, the shortfall being the 7.8% of pixels the ends clip (below). The
  relationships BETWEEN icons survive with it -- spread in mean lightness across the six 0.286
  against the source's 0.274, where nearest-of-seven gave 0.297. And CURSOR is not on the ramp at
  all, by construction: the cursor is a LOCATOR (§2) and earns its keep by being the one thing on
  screen at that hue, which a dock that was a quarter teal was spending. The old `--anchors neutral`
  escape hatch existed for that cost; the default no longer has it.

  WHAT IT COSTS, and this is the trade. A pixel between two knots is an interpolation and NOT one of
  the seven values §2 authors -- the ramp passes through exactly 667 distinct 8-bit values, five of
  them authored. The claim "every pixel in a repainted icon is a value the kit authors" is gone, and
  the claim that replaces it is the one §1 actually sets: every value on the ramp clears every pole,
  and none is reserved (§3). `--check` proves both by sweep rather than asserting them. The poster
  doctrine goes with it: an icon keeps its shading, repainted.

DARK IS NOT A KNOT, though it is an authored neutral sitting at L .385, between SELECT and ACCENT.
Its chroma is the cast's .017, so putting it on the ramp drops chroma to near zero in the middle of
the chromatic plateau -- three interior turning points instead of one, and the share of the ramp
carrying a readable hue falls from 20.4% to 6.8%. That is a seam across the middle of every icon.
The knots are chosen so that chroma rises once and falls once.

THE RAMP TERMINATES AT BLACK AND WHITE rather than passing through them: lightness outside the
ladder's span is CLIPPED, so a source pixel at L 0 cannot come out as #000000, which §3 reserves for
legend. It is the one place the output is not the input's lightness, and it is not free -- 7.8% of
the opaque pixels across the six test icons are outside the span and come back compressed. The
alternative is rescaling each icon into the span, which is worse: it would make an icon's contrast
depend on its own range, so the same grey would land differently in two icons and the relationships
this projection exists to keep would go again.

    project(rgb) -> rgb            one colour, 0-255 floats or a hex string
    project_image(PIL.Image)       every pixel; alpha untouched
    python3 build/remainder_space.py in.png out.png [--ramp neutral]
    python3 build/remainder_space.py --check        sweep the ramp against §1 and §3

`--ramp neutral` runs the same machinery on the four-step ladder -- BLACK DARK LIGHT WHITE -- whose
chroma is the §2 cast throughout, so nothing on it carries a readable hue. It is now a preference
for a grey dock and nothing more; it is not the safer option, and the duotone is not a concession
(§0a, §0c). There is no mode that emits the seven values flat: that is what this file used to be.
"""
import json, os, sys
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
import ok, poles as P

PAL = json.load(open(os.path.join(_here, '..', 'palette.json')))
VALUES = {**PAL['neutrals'], **PAL['chrome']}

# The knots, in lightness order. Both ramps start at BLACK and end at WHITE; see the header for why
# DARK is on one and not the other, and why CURSOR is on neither.
RAMPS = {'duotone': ['BLACK', 'SELECT', 'ACCENT', 'LIGHT', 'WHITE'],
         'neutral': ['BLACK', 'DARK', 'LIGHT', 'WHITE']}


def knots(which='duotone'):
    """(names, lightnesses, OKLab coordinates) of a ramp's knots, ascending in L."""
    names = RAMPS[which]
    lab = np.stack([np.array(ok.oklab(VALUES[n])) for n in names])
    return names, lab[:, 0], lab


def ramp(L, which='duotone'):
    """Lightness -> float rgb on the ramp. The whole projection is this function.

    Interpolation is in OKLab, not OKLCh: the knots at either end are near-neutrals whose hue angle
    is noise, and interpolating that angle would swing the tint of everything near BLACK and WHITE.
    """
    _, kL, klab = knots(which)
    Lc = np.clip(np.asarray(L, float), kL[0], kL[-1])            # terminate, do not pass through (§3)
    lab = np.stack([np.interp(Lc, kL, klab[:, c]) for c in range(3)], -1)
    return np.clip(ok.from_lab_grid(lab), 0, 255)                # in gamut by --check; this is the 8-bit clamp


def project(p, which='duotone'):
    v = ok.rgb(p) if isinstance(p, str) else np.asarray(p, float)
    return np.rint(ramp(ok.lch_grid(np.atleast_2d(v))[0], which))


def project_image(im, which='duotone'):
    """Project every pixel; alpha untouched.

    No edge filter. The parent kit's 3x3 majority vote existed to stop an anti-aliased pixel landing
    on a third anchor its neighbours did not choose -- an artifact of quantising. The ramp is a
    continuous function of lightness, so an anti-aliased edge comes out as the same smooth edge and
    there is nothing to vote on.
    """
    from PIL import Image
    a = np.asarray(im.convert('RGBA'))
    out = np.rint(ramp(ok.lch_grid(a[..., :3].astype(float))[0], which)).astype(np.uint8)
    return Image.fromarray(np.concatenate([out, a[..., 3:]], -1), 'RGBA')


def check(which='duotone', n=200001):
    """Sweep the ramp and hold it to §1 and §3. Returns (report lines, ok).

    The sweep is over the ramp's own span, which is the only place it varies: every lightness below
    BLACK's is BLACK and every one above WHITE's is WHITE, and that is asserted rather than sampled.
    """
    names, kL, klab = knots(which)
    Ls = np.linspace(kL[0], kL[-1], n)
    raw = ok.from_lab_grid(np.stack([np.interp(Ls, kL, klab[:, c]) for c in range(3)], -1))
    q = np.rint(ramp(Ls, which))
    hexes = sorted({ok.hexs(v) for v in q})
    breach = [h for h in hexes if not P.clear(h)]
    res = [h for h in hexes if P.reserved(h)]
    # How many distinct 8-bit values the ramp passes through, EXACTLY -- not as sampled. Every
    # channel is monotone non-decreasing along it (asserted here), so each one crosses each of its
    # rounding thresholds exactly once and the curve visits 1 + sum of the per-channel byte spans.
    # A sweep can only undercount this: 611 values at 20k samples, 664 at 200k, 667 at 2M.
    mono = bool((np.diff(q, axis=0) >= 0).all())
    n_values = int(1 + (q[-1] - q[0]).sum()) if mono else len(hexes)
    L, C, h = ok.lch_grid(q)
    err = np.abs(L - Ls).max()
    rd = C >= P.C_FLOOR
    # §3: the clip terminates the ramp. Past either end it must give that end's authored value and
    # nothing else -- this is what keeps #000000 and #FFFFFF off a repainted icon.
    ends = [ok.hexs(v) for v in ramp(np.array([-9.0, -1.0, 0.0, kL[0]]), which)] + \
           [ok.hexs(v) for v in ramp(np.array([kL[-1], 1.0, 2.0, 9.0]), which)]
    held = all(e.upper() == VALUES[names[0]].upper() for e in ends[:4]) and \
           all(e.upper() == VALUES[names[-1]].upper() for e in ends[4:])
    drift = [(nm, ok.hexs(ramp(np.array([ok.lch(VALUES[nm])[0]]), which)[0]), VALUES[nm]) for nm in names]
    slack = min((P.clearance(x)[1] - P.clearance(x)[2] for x in {ok.hexs(v) for v in q[rd]}), default=float('nan'))
    exact = sum(1 for _, g, a in drift if g.upper() == a.upper())
    good = not breach and not res and held and mono and exact == len(names) and err < 0.005
    r = [f"ramp {which}: " + ' -> '.join(f'{nm} {VALUES[nm]} L{l:.3f}' for nm, l in zip(names, kL)),
         f"  distinct values emitted   {n_values:5d}   {exact} of them authored, exactly"
         f"{'' if mono else '   (SAMPLED: the ramp is not monotone, so this is a floor)'}",
         f"  breaching a pole (§1)     {len(breach):5d}   {', '.join(breach[:6])}",
         f"  reserved for legend (§3)  {len(res):5d}   {', '.join(res)}",
         f"  outside sRGB before clip  {int((~np.all((raw >= -0.5) & (raw <= 255.5), -1)).sum()):5d}",
         f"  clip holds past both ends {'  yes' if held else '   NO'}   "
         f"L<{kL[0]:.3f} -> {ends[0]}, L>{kL[-1]:.3f} -> {ends[-1]}",
         f"  worst |L_out - L_in|      {err:7.5f}   8-bit rounding; a JND is ~0.02",
         (f"  carries a readable hue    {rd.mean() * 100:4.1f}%   L {L[rd].min():.3f}-{L[rd].max():.3f}, "
          f"hue {h[rd].min():.1f}-{h[rd].max():.1f}, {slack:.1f}deg of slack" if rd.any()
          else f"  carries a readable hue     0.0%   nothing on it reaches C_FLOOR {P.C_FLOOR:.4f}")]
    for nm, got, want in drift:
        r.append(f"  at {nm:6} L{ok.lch(want)[0]:.4f}  ramp gives {got}  authored {want}  "
                 + ('exact' if got.upper() == want.upper() else 'DRIFT'))
    return r, good


if __name__ == '__main__':
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    which = 'neutral' if '--ramp' in sys.argv and 'neutral' in sys.argv else 'duotone'
    if '--check' in sys.argv:
        bad = 0
        for w in RAMPS:
            lines, good = check(w)
            print('\n'.join(lines) + '\n')
            bad += not good
        sys.exit(1 if bad else 0)
    if len(argv) < 2:
        names, kL, _ = knots(which)
        print(f"ramp ({which}): " + " -> ".join(f'{n}={VALUES[n]}' for n in names))
        print(f"lightness is kept and clipped to [{kL[0]:.3f}, {kL[-1]:.3f}]; hue and chroma are a function of it\n")
        for h in ('#FF0000', '#FFFF00', '#0000FF', '#00FF00', '#00FFFF', '#FF00FF',
                  '#000000', '#FFFFFF', '#808080', '#FF8000', '#4078F2'):
            print(f"  {h} -> {ok.hexs(project(h, which)[0])}")
        sys.exit()
    from PIL import Image
    project_image(Image.open(argv[0]), which).save(argv[1])
    print(argv[1], f'ramp={which}')
