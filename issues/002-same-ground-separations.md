# Two surfaces on the same ground touch with nothing between them

**Labels:** geometry, surfaces, cosmic, doctrine-question, open
**Implements:** AUTHORITY.md §5 (the rule; no thinner rule), §2 (surfaces must be distinguishable, `SURFACE_FLOOR`)

Raised by Byron 2026-09-29, on this machine (CachyOS, COSMIC 1.9.0, cosmic-panel
1.9.0, 3840×2160 at 1.75×).

## What was observed

The COSMIC top panel is LIGHT. A maximized window's top edge is LIGHT too — a
COSMIC header bar, which this libcosmic paints with the window background, or
Firefox's toolbar. A maximized window gets no tiling gap: cosmic-comp gives it
exactly the output's non-exclusive zone (`shell/layout/floating/mod.rs`,
`non_exclusive_zone()`), so the BLACK gap that is the rule everywhere else is
never drawn there. The two surfaces meet at **ΔE 0.0**, and the panel reads as
part of the window.

§2 requires two load-bearing surfaces to differ by at least `SURFACE_FLOOR`
(ΔE 17.1), and §5 separates surfaces either by a change of field tone or by
the rule. Here there is neither. The same failure is expected wherever the kit
gives two adjacent surfaces the same ground and the platform removes the gap.

## What was tried (2026-09-29, prototypes only, nothing committed)

Byron's target: below the panel, a gap the width of the key-window mark, 4 dp
(7 px here).

| attempt | result |
|---|---|
| panel `border_width` | draws only the inner edge on a flush panel, in the theme's `bg_divider` — derived by libcosmic as 20% of the text colour over the window background (`cosmic-theme/src/model/derivation.rs`), about LIGHT. Invisible on a LIGHT panel, and a blend the kit does not author |
| panel `margin` / `anchor_gap` on the main panel | both put space *above* a top panel and inset its ends; none below |
| a second, empty panel entry ("Rule"), BLACK, `Custom(4)` | maps, but at **1 dp** (2 px): an empty panel sizes to its content and ignores `size` and `padding`. The compositor's own 2 px window outline covers most of it |
| the same with `anchor_gap` true, `margin` 1 / 3 | **18 px (≈10 dp)** / **25 px (≈14 dp)**: 2 dp per margin step over a fixed ≈8 dp once `anchor_gap` is on. 4 dp is not reachable. The gap is transparent, so over the default photograph (§5) it shows the photograph's light ground, not BLACK |

Byron is running the `--gap 1` prototype (≈10 dp) on his own machine. The
prototype script lived in a session scratchpad and is not in the repo.

## What this issue asks for

1. **An audit.** On every surface the kit ships, list the places where two
   surfaces with the same ground touch with no rule and no tone change between
   them, and where the platform can take the gap away: maximized and fullscreen
   windows, snapped and tiled edges, panels and docks, and in-app chrome
   (toolbars against headers, sidebars against content, popups against their
   parent). Measure each pair in ΔE, the way §2 lists its load-bearing boundaries.
2. **A decision per place**, in §5's terms: a tone change (a pair that clears
   17.1), the rule at its full width, or an explicit exception recorded as chosen.
   §5 says there is no thinner rule. A 4 dp separation is the width of the
   key-window mark, not of the rule, so adopting it anywhere is a change to §5
   and needs its own paragraph there.
3. **An implementation** for the panel case that reaches the chosen width
   exactly. cosmic-panel's settings cannot (above); the candidates left are a
   small layer-shell client of the kit's own that reserves and paints the strip,
   or an upstream change to cosmic-panel. Either one ships something new and needs
   CONTRIBUTING's tier and flag rules applied.

## Open questions

- Is the separation BLACK (the rule, which the flat field makes true everywhere)
  or is it allowed to show the background, which the default photograph makes
  light?
- Does the dock (bottom, DARK tiles) have the same problem against a maximized
  window's bottom edge, or does DARK against the window's ground already clear
  the floor?
- Should `PLATFORM.md` record the cosmic-panel findings above now? They are
  platform facts, and §11 asks for them in both kits.

## Found since

- **Zettlr, 2026-09-30: the sidebar against the note.** Both were WHITE, ΔE 0.0,
  because Zettlr makes its sidebar transparent on Linux and the theme never
  answered that rule (`worksafe/zettlr/README_ZETTLR.md`). Fixed in the theme: the
  sidebar is LIGHT, the tone change §5 already names (ΔE 17.1), and
  `build/zettlr.py --screen` now reports any surface whose ground is not the one
  its table gives. One row of the audit, done; the rest of it stands.
