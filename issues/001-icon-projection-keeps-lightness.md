# The icon projection decided lightness by a distance hue voted in

**Labels:** icons, projection, doctrine-change, measured
**Implements:** AUTHORITY.md §4 (application icons), §1 (the poles), §3 (reserved values)

Observed 2026-09-19 on this machine (Pop!_OS, Linux 7.1.5-76070105; icon chain
`Cosmic, Pop, Pop-Extra, pop-os-branding, Adwaita, hicolor`), over six icons the
machine actually ships: `firefox`, `org.gnome.Nautilus`, `libreoffice-writer`,
`com.system76.CosmicFiles`, `org.gnome.Calculator`, `steam`, each rendered at
256px and repainted whole.

## What was observed

`build/remainder_space.py` sent each pixel to the **nearest of the seven values
§2 authors** in OKLab ΔE, flat, with a gray guard at `C_FLOOR` and a 3×3 edge
vote. Every pixel in a repainted icon was therefore a value AUTHORITY.md names —
a strong claim, and the wrong one to optimise for. Nearest-anchor distance lets
**hue vote on a pixel's lightness**, so:

- per-pixel lightness survived at r **0.906**, and its *ordering* at ρ **0.759**
  — about a quarter of the light-and-dark inside every icon reassigned;
- **25.30%** of opaque pixels came back CURSOR teal `#007891`, spending across a
  whole dock the one hue §2 keeps for a locator;
- the spread in mean lightness across the six moved from the source's **0.274**
  to **0.297** — contrast between icons that the art does not have.

An icon is read by its shape, its shading, and which icon is lighter than which.
All three are what the projection was spending.

## Candidates measured

Ten decolorisation strategies, all held to the same bar: no emitted value may
read as a signal (§1) or be reserved (§3). `unclear` counts distinct emitted
values failing `poles.clear()` or reserved; it must be 0.

| candidate | L r | ρ | spread | CURSOR% | values | authored | unclear |
|---|---|---|---|---|---|---|---|
| source (the art itself) | 1.000 | 1.000 | 0.274 | 0.00 | 15837 | 0 | 9436 |
| S1 nearest of 7 — **was shipped** | 0.906 | 0.759 | 0.297 | 25.30 | 7 | 7 | 0 |
| S1b S1 minus CURSOR | 0.910 | 0.687 | 0.321 | 0.00 | 6 | 6 | 0 |
| S2 neutral ladder | 0.897 | 0.664 | 0.321 | 0.00 | 4 | 4 | 0 |
| S3 S1, lightness weighted ×3 | 0.928 | 0.806 | 0.304 | 20.39 | 7 | 7 | 0 |
| **S4 duotone ramp — chosen** | **0.997** | **0.994** | **0.286** | **0.00** | 568 | 5 | 0 |
| S4b duotone, flattened | 0.897 | 0.662 | 0.321 | 0.00 | 4 | 3 | 0 |
| S5 hue compressed into the home arc | 1.000 | 0.994 | 0.274 | 0.00 | 4479 | 0 | **2** |
| S6 ladder + one ACCENT spot | 0.807 | 0.735 | 0.277 | 0.00 | 5 | 5 | 0 |
| S7 quantile ladder | 0.779 | 0.794 | 0.385 | 0.00 | 4 | 4 | 0 |
| S8 quantile duotone | 0.779 | 0.794 | 0.386 | 0.00 | 4 | 3 | 0 |

The source row is the art as brand: 9436 of its values sit inside a pole, which
is not a defect — content is exempt (§0a, principle 9). Repainted as chrome they
must clear, and every candidate but S5 does. **S5 is excluded on §1**: folding
the hue circle into the home arc keeps the source's chroma, and two values land
unclear. The quantile strategies (S7, S8) spend each icon's whole ladder and so
*invent* dock contrast — spread 0.385 against the source's 0.274.

## What was chosen, and what it costs

S4: **keep lightness exactly, make hue and chroma a function of it**, along a
ramp whose knots are values §2 authors, ordered by L —

    BLACK .148 → SELECT .308 → ACCENT .426 → LIGHT .760 → WHITE .931

Neutral at both ends, the home hue through the middle: a duotone. DARK is *not*
a knot though its lightness falls inside the span; at the cast's chroma .017 it
would collapse chroma in the middle of the chromatic plateau — three interior
turning points instead of one, the readable share falling 20.4% → 6.8%, a seam
across the middle of every icon. Interpolation is in OKLab, not OKLCh: the end
knots are near-neutrals whose hue angle is noise.

**The cost is the claim.** A pixel between two knots is an interpolation and not
one of the seven. The ramp passes through exactly **667** distinct 8-bit values
(exact, not sampled: every channel is monotone along it, so the count is
1 + Σ per-channel byte span), **five** of them authored. "Every pixel in a
repainted icon is a value the kit authors" is withdrawn. The bar that remains is
the one §1 actually sets — every value on the ramp clears every pole, none is
reserved — and it is proven by sweep, not asserted:

```
python3 build/remainder_space.py --check
```

which reports 0 breaching, 0 reserved, 0 outside sRGB, each knot reproduced
bit-for-bit, worst |L_out − L_in| 0.0023 (8-bit rounding; a JND is ~0.02), and
the readable band at L 0.294–0.455, hue 350.1–352.1, **20.0° of slack** where
10.5° is required.

The ramp **terminates at** BLACK and WHITE rather than passing through them, so
a source pixel at L 0 cannot come out `#000000`. That clip is the one place the
output is not the input's lightness and it is not free: **7.8%** of opaque pixels
across the six are outside the span and come back compressed. Rescaling each icon
into the span instead would make its contrast depend on its own range — the same
grey landing differently in two icons — which is the relationship this projection
exists to keep.

The 3×3 majority vote is gone with the quantiser it was fixing. A ramp is a
continuous function of lightness, so an anti-aliased edge comes out as the same
edge and there is nothing to vote on.

## Changed

- `build/remainder_space.py` — rewritten as the ramp; `--check` added.
  `ANCHOR_SETS`/`anchor_index`/`poster`/`majority` removed, `RAMPS`/`knots`/`ramp`
  in their place.
- `build/ok.py` — `from_lab_grid` added (the rectangular form, for interpolation);
  `from_lch_grid` now calls it. `palette.json` regenerates byte-identical.
- `build/icon_theme.py` — `--anchors all|neutral` → `--ramp duotone|neutral`.
- `worksafe/cosmic/install.sh` — `--icons` / `--icons-neutral` unchanged as flags;
  their text and the question they ask now describe the ramp.
- `AUTHORITY.md` §4, `README.md` — the withdrawn claim and the one replacing it.

`--icons-neutral` survives as a preference for a grey dock, not as an escape
hatch: its original reason was that CURSOR in a dock icon spends the locator, and
the duotone reaches CURSOR never.
