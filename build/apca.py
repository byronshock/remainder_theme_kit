"""APCA (Accessible Perceptual Contrast Algorithm) -- the perceptual contrast metric.

AUTHORITY.md 0b rejects a metric that answers the wrong question. WCAG 2.x contrast is such a
metric for this kit's purposes: it is a plain luminance RATIO, so it is

  polarity-blind  dark-on-light and light-on-dark at the same ratio do not read alike; light
                  text on a dark field needs more separation than the ratio admits,
  chroma-blind    two colors of equal luminance score 1:1 whatever their hue,
  distorted low   the +0.05 flare constant flatters near-black pairs.

APCA is polarity-aware, uses perceptual exponents rather than a ratio, and returns a signed
lightness contrast Lc: POSITIVE for dark text on a light field, NEGATIVE for the reverse.
|Lc| runs to about 106 (black on white) and 108 (white on black).

Constants are APCA 0.1.9 / W3C draft. VERIFY against the published spec before the kit makes
a conformance claim on them; the self-test below pins the two reference pairs.

    python3 build/apca.py '#1A0F14' '#F3E3E9'      text, background
    python3 build/apca.py --selftest
"""
import sys
import numpy as np

MAIN_TRC = 2.4
CO = np.array([0.2126729, 0.7151522, 0.0721750])
NORM_BG, NORM_TXT = 0.56, 0.57            # dark text on light field
REV_TXT, REV_BG = 0.62, 0.65              # light text on dark field
SCALE_BOW, SCALE_WOB = 1.14, 1.14
LO_BOW_OFFSET, LO_WOB_OFFSET = 0.027, 0.027
BLK_THRS, BLK_CLMP = 0.022, 1.414
DELTA_Y_MIN, LO_CLIP = 0.0005, 0.1


def _rgb(h):
    if isinstance(h, str):
        h = h.lstrip('#')
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
    return np.array(h, float)


def screen_y(c):
    """Estimated screen luminance: a simple power curve, not the sRGB piecewise transfer."""
    return float(np.dot((_rgb(c) / 255.0) ** MAIN_TRC, CO))


def _clamp(y):
    return y + (BLK_THRS - y) ** BLK_CLMP if y < BLK_THRS else y


def lc(text, bg):
    """Signed APCA Lc. Positive = dark text on light field; negative = light on dark."""
    yt, yb = _clamp(screen_y(text)), _clamp(screen_y(bg))
    if abs(yb - yt) < DELTA_Y_MIN:
        return 0.0
    if yb > yt:                                            # dark text on a light field
        s = (yb ** NORM_BG - yt ** NORM_TXT) * SCALE_BOW
        out = 0.0 if s < LO_CLIP else s - LO_BOW_OFFSET
    else:                                                  # light text on a dark field
        s = (yb ** REV_BG - yt ** REV_TXT) * SCALE_WOB
        out = 0.0 if s > -LO_CLIP else s + LO_WOB_OFFSET
    return out * 100.0


def polarity(text, bg):
    return 'dark-on-light' if screen_y(bg) > screen_y(text) else 'light-on-dark'


# APCA's own use-case guidance, abbreviated. Lc is a FONT-DEPENDENT threshold, which is the
# other thing a single WCAG number hides: there is no one contrast target, only a target for
# a given size and weight. The kit's UI is 12pt / ~16px at 400 weight (AUTHORITY.md 2).
GUIDANCE = [(90, 'body text, any size down to 14px/400 -- the preferred minimum'),
            (75, 'body text at 16px/400; the practical floor for sustained reading'),
            (60, 'larger or heavier text (24px/400, 16px/700); headlines'),
            (45, 'large display text, 36px+/400'),
            (30, 'non-text: icons, borders, disabled states'),
            (15, 'absolute floor; invisible below this')]


def guidance(v):
    for t, why in GUIDANCE:
        if abs(v) >= t:
            return t, why
    return 0, 'below the visibility floor'


def selftest():
    cases = [('#000000', '#FFFFFF', 106.0), ('#FFFFFF', '#000000', -108.0)]
    ok = True
    for t, b, want in cases:
        got = lc(t, b)
        good = abs(got - want) < 1.0
        ok &= good
        print(f"  {t} on {b}  Lc {got:7.2f}   expect ~{want:6.1f}  {'ok' if good else 'MISMATCH'}")
    return ok


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        print("APCA reference pairs:")
        sys.exit(0 if selftest() else 1)
    a = sys.argv[1:]
    for i in range(0, len(a) - 1, 2):
        v = lc(a[i], a[i + 1]); t, why = guidance(v)
        print(f"{a[i]} on {a[i+1]}  Lc {v:7.2f}  ({polarity(a[i], a[i+1])})  -> {t}: {why}")
