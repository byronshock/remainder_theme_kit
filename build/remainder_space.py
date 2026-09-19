"""Remainder space: project sRGB onto the seven values the kit authors. AUTHORITY.md is the authority.

The parent kit's `mondrian_space.py` projects a pixel to the nearest of five pigments measured from a
painting. Remainder has no painting, so its anchors are simply its own palette: §2's four-step neutral
ladder plus the three chrome hues. A pixel goes to the nearest anchor, flat -- a poster, no shading.

    BLACK  DARK  LIGHT  WHITE        the ladder (§2)
    ACCENT  SELECT  CURSOR           the chrome hues (§2)

Two things differ from the parent kit's version, and both because this kit's own machinery is better
suited to the question:

  DISTANCE IS OKLab dE, not sRGB code values. §0b rejects sRGB distance for exactly this job: it
  reports #FF6B6B as 127 units from FHWA red when the two are the same hue. A projection that picks
  the "nearest" anchor in code values picks by a number that does not model looking at it.

  THE GRAY THRESHOLD IS C_FLOOR, not a magic constant. The parent kit sends any pixel whose sRGB
  chroma is under 28 to the nearer of black and white, so gray shading does not turn yellow. The bar
  it needed is one this kit already derives: below C_FLOOR (0.092, the chroma of the faintest realized
  pole) no hue is doing semantic work, so a pixel under it is a gray and goes to the ladder. Above it
  the pixel is carrying a hue and may go to a chrome anchor.

  And the ladder it lands on is four values deep rather than two, so gray shading survives the
  projection where the parent kit flattens it to black or white.

    project(rgb) -> rgb            one color, 0-255 floats or a hex string
    project_image(PIL.Image)       every pixel; alpha untouched
    python3 build/remainder_space.py in.png out.png [--anchors neutral]

`--anchors neutral` drops the three chrome hues and projects to the ladder alone. It exists because
putting CURSOR in an icon has a cost §2 names: the cursor is a LOCATOR, and its teal earns its keep by
being the one thing on screen at that hue. Teal in a dock icon spends some of that. The kit ships the
seven-anchor poster and records the cost rather than hiding it.
"""
import json, os, sys
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
import ok, poles as P

PAL = json.load(open(os.path.join(_here, '..', 'palette.json')))
N, CH = PAL['neutrals'], PAL['chrome']

# The ladder, dark to light. Four values where the parent kit has two, so shading survives.
LADDER = ['BLACK', 'DARK', 'LIGHT', 'WHITE']
# The chrome hues. A pixel reaches these only if it carries a hue at all (C >= C_FLOOR).
HUES = ['ACCENT', 'SELECT', 'CURSOR']
VALUES = {**N, **CH}
ANCHOR_SETS = {'all': LADDER + HUES, 'neutral': LADDER}

_LAB = {k: np.array(ok.oklab(v)) for k, v in VALUES.items()}


def anchors(which='all'):
    """(names, hexes, OKLab coordinates) for an anchor set."""
    names = ANCHOR_SETS[which]
    return names, [VALUES[n] for n in names], np.stack([_LAB[n] for n in names])


def _oklab_grid(v):
    """Float rgb array (..., 3) -> OKLab array (..., 3). ok.oklab is scalar-only."""
    lms = np.cbrt(ok.to_linear(v) @ ok.M1.T)
    return lms @ ok.M2.T


def anchor_index(p, which='all'):
    """Index into anchors(which) of the nearest anchor, in OKLab dE.

    A pixel whose chroma is under C_FLOOR carries no readable hue (§1), so it is a gray and is held
    to the ladder -- otherwise a mid gray lands on ACCENT, which is how the parent kit's gray shading
    turned yellow before it added the same guard.
    """
    p = np.atleast_2d(np.asarray(p, float))
    names, _, lab = anchors(which)
    q = _oklab_grid(p)
    d = ((q[:, None, :] - lab[None, :, :]) ** 2).sum(-1)
    if which == 'all':
        chroma = np.hypot(q[..., 1], q[..., 2])
        gray = chroma < P.C_FLOOR
        d[gray, len(LADDER):] = np.inf
    return d.argmin(1)


def poster(p, which='all'):
    """Nearest anchor, flat: a poster, no shading."""
    names, hexes, _ = anchors(which)
    idx = anchor_index(p, which)
    return np.stack([ok.rgb(hexes[i]) for i in idx])


def majority(idx, alpha=None, n=None):
    """3x3 majority vote over a 2-D index map, carried over from the parent kit's version.

    An anti-aliased edge pixel joins the anchor most of its neighbours chose instead of a third one.
    Ties keep the pixel's own choice; transparent neighbours do not vote.
    """
    H, W = idx.shape
    n = n or len(ANCHOR_SETS['all'])
    votes = np.zeros((n, H, W), int)
    valid = np.ones((H, W), bool) if alpha is None else alpha > 0
    pad_i, pad_v = np.pad(idx, 1, mode='edge'), np.pad(valid, 1, mode='constant')
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            si = pad_i[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
            sv = pad_v[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
            for k in range(n):
                votes[k] += (si == k) & sv
    best = votes.argmax(0)
    own = votes[idx, np.arange(H)[:, None], np.arange(W)[None, :]]
    return np.where(votes.max(0) > own, best, idx)


def project(p, which='all'):
    return np.clip(np.rint(poster(ok.rgb(p) if isinstance(p, str) else np.asarray(p, float), which)), 0, 255)


def project_image(im, mode='poster', clean=True, which='all'):
    """Project every pixel; alpha untouched. clean=True applies the 3x3 majority filter."""
    from PIL import Image
    if mode != 'poster':
        raise ValueError(f"remainder_space has one mode, 'poster' (got {mode!r})")
    im = im.convert('RGBA')
    a = np.asarray(im)
    H, W = a.shape[:2]
    names, hexes, _ = anchors(which)
    idx = anchor_index(a[..., :3].reshape(-1, 3), which).reshape(H, W)
    if clean:
        idx = majority(idx, a[..., 3], n=len(names))
    table = np.stack([ok.rgb(h) for h in hexes]).astype(np.uint8)
    return Image.fromarray(np.concatenate([table[idx], a[..., 3:]], -1), 'RGBA')


if __name__ == '__main__':
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    which = 'neutral' if '--anchors' in sys.argv and 'neutral' in sys.argv else 'all'
    if len(argv) < 2:
        names, hexes, _ = anchors(which)
        print(f"anchors ({which}): " + "  ".join(f'{n}={h}' for n, h in zip(names, hexes)))
        print(f"C_FLOOR {P.C_FLOOR:.4f} -- under it a pixel is a gray and is held to the ladder\n")
        for h in ('#FF0000', '#FFFF00', '#0000FF', '#00FF00', '#00FFFF', '#FF00FF',
                  '#000000', '#FFFFFF', '#808080', '#FF8000', '#4078F2'):
            print(f"  {h} -> {ok.hexs(project(h, which)[0])}")
        sys.exit()
    from PIL import Image
    project_image(Image.open(argv[0]), which=which).save(argv[1])
    print(argv[1], f'poster, anchors={which}')
