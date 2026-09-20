"""Colorimetry for Remainder: sRGB <-> OKLab/OKLCh, contrast. AUTHORITY.md is the authority.

The kit measures in OKLCh because its whole claim is about what a color *reads as*, and
reading is hue and chroma, not code value. sRGB Euclidean distance -- the metric the parent
kit uses for a different question -- calls #FF6B6B 127 units from FHWA red while its hue gap
is 0 degrees. It is exactly red. See AUTHORITY.md 0b.
"""
import numpy as np

M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
               [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553,  0.7936177850, -0.0040720468],
               [1.9779984951, -2.4285922050,  0.4505937099],
               [0.0259040371,  0.7827717662, -0.8086757660]])


def rgb(h):
    """Hex or triple -> float rgb 0-255."""
    if isinstance(h, str):
        h = h.lstrip('#')
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
    return np.array(h, float)


def hexs(v):
    return '#%02X%02X%02X' % tuple(int(round(x)) for x in np.clip(v, 0, 255))


def to_linear(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def from_linear(c):
    c = np.asarray(c, float)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - 0.055)


def oklab(p):
    lms = np.cbrt(M1 @ to_linear(rgb(p)))
    return M2 @ lms


def lch(p):
    """(L, C, h degrees) in OKLCh."""
    L, a, b = oklab(p)
    return float(L), float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a)) % 360)


def from_lch(L, C, h):
    """OKLCh -> float rgb 0-255. May land outside the gamut; check with in_gamut."""
    a, b = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    lms = np.linalg.solve(M2, np.array([L, a, b])) ** 3
    return from_linear(np.linalg.solve(M1, lms))


def in_gamut(v, tol=0.5):
    return bool(np.all(v >= -tol) and np.all(v <= 255 + tol))


def luminance(p):
    return float(np.dot(to_linear(rgb(p)), [0.2126, 0.7152, 0.0722]))


def contrast(p, q):
    """WCAG 2.1 contrast ratio."""
    a, b = sorted((luminance(p), luminance(q)))
    return (b + 0.05) / (a + 0.05)


def arcgap(h, lo, hi):
    """Angular distance from hue h to the arc [lo, hi] (degrees, wrapping). 0 if inside."""
    span = (hi - lo) % 360
    if (h - lo) % 360 <= span:
        return 0.0
    return float(min((lo - h) % 360, (h - hi) % 360))


# --- vectorised forms: the derivation searches ~10^6 lattice points --------------------
def from_lab_grid(lab):
    """OKLab array (..., 3) -> float rgb array (..., 3). May land outside the gamut.

    The rectangular form, for work that interpolates: a straight line between two colours is a
    line in OKLab, not in OKLCh. Interpolating C and h instead swings the hue of a near-neutral,
    whose angle is noise -- BLACK and WHITE differ by 4.6 degrees of a hue neither one carries.
    """
    lms = (np.asarray(lab, float) @ np.linalg.inv(M2).T) ** 3
    return from_linear(lms @ np.linalg.inv(M1).T)


def from_lch_grid(L, C, h):
    """Arrays of (L, C, h) -> float rgb array (..., 3). Same math as from_lch."""
    L, C, h = np.broadcast_arrays(np.asarray(L, float), np.asarray(C, float), np.asarray(h, float))
    return from_lab_grid(np.stack([L, C * np.cos(np.radians(h)), C * np.sin(np.radians(h))], axis=-1))


def lch_grid(v):
    """Float rgb array (..., 3) -> (L, C, h) arrays."""
    lms = np.cbrt(to_linear(v) @ M1.T)
    lab = lms @ M2.T
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    return L, np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360


def luminance_grid(v):
    return to_linear(v) @ np.array([0.2126, 0.7152, 0.0722])


def contrast_grid(Y, y):
    """WCAG ratio between an array of relative luminances and one scalar luminance."""
    hi, lo = np.maximum(Y, y), np.minimum(Y, y)
    return (hi + 0.05) / (lo + 0.05)


def delta_e(a, b):
    """OKLab colour difference, x100 for readable units. ~2 is a JND on a large field.

    This is the SURFACE metric. APCA Lc (build/apca.py) is the TEXT metric: it measures
    lightness contrast only, so two surfaces that differ in chroma read as Lc 0 while being
    plainly different to look at. Using Lc to judge whether two grounds are distinguishable
    reports false collapses -- do not.
    """
    return float(np.linalg.norm(np.array(oklab(a)) - np.array(oklab(b)))) * 100.0
