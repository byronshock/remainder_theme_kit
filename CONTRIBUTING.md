# Contributing to Remainder

`AUTHORITY.md` is the authority. This file is the procedure: what a change
carries before it lands. Principle 14 makes both binding. Every rule below
cites the section or principle it comes from; where this file and the authority
disagree, the authority is right and this file is the defect.

The kit is one hypothesis (§0a) rendered on several platforms. A change is
judged by whether the hypothesis still holds on the screen, and the judgment is
a measurement (principle 10), not an opinion.

Everything that measures the palette needs numpy and nothing else. A script
that touches images needs Pillow, and rasterising an SVG needs cairosvg; those
are imported where they are used, so the rest of `build/` runs without them.

## 1. The tier boundary (§4)

Inherited from De Stijl unchanged and binding here. It is not re-argued:
`DESTIJL_STYLE.md` §7 and §3 in the parent kit carry the argument, and
`PLATFORM.md` carries what each platform actually permits.

| Tier | Reach | Ships in |
|---|---|---|
| worksafe | per-user, no elevation: `HKCU`, `$HOME`, a browser profile | `worksafe/` |
| elevated | admin, or all-sites | `elevated/` |

- Nothing in `worksafe/` asks for a password, and an installer there backs up
  what it replaces. Per-user means reversible: `worksafe/cosmic/install.sh`
  saves every file it overwrites under `~/.local/state/remainder` on the first
  run and never overwrites that copy on a re-run.
- **What the kit does to the user's machine beyond painting it is opt-in.**
  Installing typefaces and repainting application icons are both the user's
  call, not the kit's, so both are flags (`--fonts`, `--icons`) and neither is
  the default. A surface that does either without being asked is a defect, and
  so is one that cannot be undone by selecting something else.
- **A residue that elevation could remove is not unavoidable** (§4). Before a
  defect is written into a surface's residue table, ask it: would elevation
  remove this? If yes it is not residue — it is removed in `elevated/` and
  tolerated in `worksafe/`, and the worksafe entry says which.
- Reach decides the tier where the platform is generous about privilege.
  Firefox hands an all-sites sheet to a per-profile extension, so
  `elevated/remainder.user.css` will need no elevation on that surface; it
  belongs in `elevated/` because its reach is every site.
- The kit's larger half is removal (§0), inherited verbatim and larger here
  too. A surface that sets colors and leaves the recommendations, nags, motion
  and blur in place is not done.

## 2. Chrome clears every pole (§1, principle 1)

Every color the kit authors as chrome is **clear**: its chroma is below
`C_FLOOR` (0.092), or its hue clears every pole arc by `DELTA_REQ` at its own
chroma. Nothing else is chrome.

```
python3 build/poles.py '#763555' '#FF6B6B'
```

It prints each value with its nearest pole family, the gap, and what that
chroma requires, and exits nonzero if any fails. `--bars` prints the derived
bars and the five arcs and exits zero.

Three things the test does **not** do, and the first is the one that surprises:

- **The three semantic values are not allow-listed.** They *are* the poles
  (§3), so they fail by construction — `#AF1E2D` reports 0.0° from destructive.
  That is correct output, not a defect. De Stijl exempts its §1b three; here
  the exemption would be a category error, because the test asks "is this
  chrome?" and a signal is not chrome.
- **`#FFFFFF` and `#000000` are refused by rule, not by measurement.** Both
  have zero chroma and would pass as neutrals, so §3 reserves them and
  `poles.py` enforces it. `--legend` admits them for the one permitted use —
  legend on a semantic field — and nowhere else.
- **It does not know which values are content.** §0a exempts content entirely,
  and a terminal's ANSI slots are content. A value inside a pole is a defect
  only if it is chrome, and deciding that is §3 below.

Extracting values from a surface file first:

```
grep -ohE '#[0-9A-Fa-f]{6,8}' worksafe/cosmic/remainder.ron | cut -c1-7 | sort -u | xargs python3 build/poles.py
```

Over `remainder.ron` that reports exactly three POLE lines — `#006B54`,
`#FCD116`, `#AF1E2D` — and those three are the whole expected result. A fourth
is a defect. This is a way to look; the gate is the surface's own checker (§8).

**Re-measured 2026-09-19**, after the Firefox surface landed, over every value
in `worksafe/`, `elevated/`, `palette.json` and `poles.json`, comments stripped:
**60 distinct**, of which 26 are chrome and every one clears, 3 are §3's
semantics, 17 are pole members recorded in `poles.json`, 12 are terminal ANSI
slots, and **2 are the reserved legend values**. Nothing is unexplained.

The two reserved values are the first reserved-legend use in the kit: `#FFFFFF`
on DESTRUCTIVE and on SUCCESS, in `worksafe/firefox/chrome/` and
`elevated/remainder.user.css` — the close button, the destructive button, and
the two ARIA states a page uses to say what it means — which is precisely the
one use §3 permits them. **The all-sites sheet added a third surface and not one
new value**: the count above was 60 before it landed and is 60 after.
`build/firefox.py` is what makes that checkable rather than a claim: the sheet
names them `--rm-legend-light` and `--rm-legend-dark`, and the checker fails if
either is ever the text side of a pair whose ground is not one of §3's three.

**The kit admits no exception at all.** The only one the authority
names is platform residue (principle 1), which is tolerated where neither tier
reaches it and never echoed (§4). There is no Remainder equivalent of De
Stijl's §1c, and an authored value that needs one needs a clause in
`AUTHORITY.md` before it needs a line here.

## 3. Content is exempt, and that is a category (§0a, principle 9)

Content may take any color, poles included. That is not a loophole to be spent
sparingly: where the meaning is real, content **must** take the pole. A chart of
error rates should be red, and a terminal's ANSI red should be red, because the
user reads red as error inside the buffer too.

So every value is one or the other, and the change says which:

- **Chrome** is furniture — read once, then unseen. It clears every pole.
- **Content** is information — read for what it says. It is exempt.

The test between them is the one §2 uses on the cursor, borrowed from De Stijl
§4b: **if removing the color makes the thing harder to find, the color is
information.** It is why the text cursor takes a second hue at 219.1° rather
than the home hue — solved at home it came out within 3 Lc and 0.03 L of
ACCENT, and a locator that looks like furniture is not a locator.

This is also the one place Remainder diverges from the parent kit on a surface
rather than on the palette: De Stijl paints the sixteen ANSI slots with its
chrome pigments, which is chrome reaching into content. Remainder solves each
slot from the hue xterm ships in that slot (`build/cosmic.py`).

## 4. Chosen or derived, and labelled either way (§0c, principles 4 and 11)

The hypothesis is a hue constraint and nothing more. Every chroma and every
lightness in the kit is an aesthetic or legibility choice, and each is labelled
as one where it is written.

- A new constant in `build/derive_palette.py` carries a `# CHOSEN:` or
  `# DERIVED:` comment with its reason, and lands in `palette.json` under
  `chosen` or `derived`. Both blocks are generated from those constants.
- A derived number states what it falls out of. `C_FLOOR` is the chroma of the
  faintest realized pole; `DELTA_MAX` is the poles' own nearest-neighbour
  separation; `SURFACE_FLOOR` is WHITE against LIGHT. None of the three is
  declared, and a fourth bar that has to be declared is not a bar.
- **Dressing a choice as a derivation is the one dishonesty this kit cannot
  afford** (§0c). It is the move §0b accuses De Stijl of, and the kit loses its
  own argument the moment it makes it.
- One number is knowingly circular and says so: the 31.4° guard is taken from
  where the settled home hue already sits (§1). Declaring that openly beats
  dressing it, and `build/sample_arc.py` reaches the same place from the other
  direction by a different method.

## 5. Two metrics, and they are not interchangeable (§0e, principle 6)

| Question | Metric | Where |
|---|---|---|
| Is this text legible on this ground? | APCA Lc, signed | `build/apca.py` |
| Are these two grounds distinguishable? | OKLab ΔE | `build/ok.py` |
| — | WCAG 2.x contrast | nowhere |

- Lc is polarity-aware and signed: positive for dark text on a light field,
  negative for the reverse. The sign is part of the measurement; report it.
- There is no single Lc target. The floor is a function of polarity, size and
  weight — 90 body preferred, 75 body minimum, 60 for 16px/700 bold or
  24px/400, 30 for non-text marks, 15 the visibility floor — and that is the
  other thing a single WCAG number hides.
- Using Lc on two grounds reports false collapses. ACCENT and DESTRUCTIVE
  measure Lc 0.0 against each other and are 31° apart in hue.
- **The kit does not pass a naive WCAG audit, and that is recorded rather than
  fixed** (§0e). WHITE on ACCENT is 7.1:1 — under AA for normal text — and
  Lc −78.5, correct for the bold titlebar text it actually carries. A change
  that moves a value to satisfy a WCAG ratio is a change in the wrong
  direction; say so and cite §0e.

## 6. Every target is a floor (§0c, principle 5)

The kit sits above its floors on purpose. One input was never measured — that
§5's "12pt system size" renders at about 16px effective — and every contrast
floor is a function of it. A palette seated exactly on its floors propagates an
error in that input into failure across every surface at once, silently.

- A new value lands with margin, and the margin is stated.
- Three pairs sit near their floor for structural reasons and not by choice:
  `BLACK on LIGHT` (+1.2, LIGHT is pinned), `BLACK on WHITE` (+1.8, already at
  APCA's preferred tier) and `CURSOR on WHITE` (+0.7, capped by the teal
  gamut). They are the first to re-measure when anything moves.
- **CURSOR is the least robust value in the kit** (§2), living on three
  simultaneous margins: +0.004 chroma over `C_FLOOR`, 0.8° inside the guard
  edge, +0.7 Lc. A change to WHITE, to the guard, or to the pole set re-checks
  it before anything else.
- `WHITE_L` and `LIGHT_L` are pinned so `SURFACE_FLOOR` cannot drift. It moved
  once already: darkening BLACK shifted LIGHT by ΔE 1.5 — invisible in itself —
  and moved the floor under every value measured against it. **A bar that moves
  when something else moves is not a bar.**

## 7. `palette.json` is generated (principle 13)

It is generated by `build/derive_palette.py` and committed, because it is the
interface every other script reads. Editing the output is a defect. So is
editing a color in `AUTHORITY.md` alone.

```
before=$(sha256sum palette.json) && python3 build/derive_palette.py --write && echo "$before" | sha256sum -c -
```

`OK` means `palette.json` is already what the derivation produces. Run it after
anything that touches `poles.json`, the derivation, or a constant — it is the
cheapest check in the repo.

Test the invariant, not the commit. `git diff --exit-code palette.json` looks
like the same check and is not: it compares against `HEAD`, so it reports a
defect for every legitimate change to the derivation that has not been
committed yet, and it reports nothing at all about whether the two agree.

**Touching `poles.json` is not a local change.** All three bars fall out of the
pole set, so adding or removing a member can move `C_FLOOR`, `DELTA_MAX` and
`C_REF`, and through them every clearance in the kit and the working arc
itself. The demotion of info-cyan is the worked example: its members and
measurements stay in the file under `demoted` with the judgement beside them,
and moving them back restores the pole with no other change (§1). A pole member
arrives with its source — which system ships it as that signal, named in the
file's `sources` — or it is not realized and does not belong there.

## 8. A surface ships with its checker

A platform asks for more values than the kit authors. COSMIC wants eleven
neutral slots where §2 has four, nine accent swatches, and sixteen ANSI slots.
None may be filled by eye (principle 10), so each is a ladder derived from what
the kit already has, and the derivation ships as code beside the surface.

```
python3 build/cosmic.py            # check every value in the committed .ron files
python3 build/cosmic.py --derive   # the three ladders, and how each value was reached
python3 build/firefox.py           # every value, text pair and adjacency in the sheet
python3 build/firefox.py --derive  # the grey ladder, under both of Firefox's numberings
python3 build/stylus.py            # the all-sites sheet: values, pairs, and what it may not paint
python3 build/stylus.py --derive   # the roles it may name, and the pairs no rule block states
```

Three are built. What a checker owes:

- **Every value in a committed surface file is traceable to a named ladder.**
  `NOT DERIVED BY ANY LADDER` is a defect, and it catches the value someone
  typed in by hand far more reliably than the pole test does.
- It knows which of its values are chrome and which are content (§3), which a
  bare pole test cannot. `remainder-term.ron` holds 23 distinct values, 12 of
  them inside a pole on purpose.
- **It reads every file the installer copies, in whatever notation that file
  uses.** `cosmic-config/` writes colors as RON decimal triples —
  `Color((0.729412, 0.678431, 0.698039))` is LIGHT — which a hex scan does not
  see at all. The panel background sat unchecked until the checker learned that
  notation. A value the checker cannot read is a value nobody is checking.
- It reads `palette.json` rather than restating it.
- It exits nonzero on a defect, so it can be run before a commit without being
  read.

A ladder that lands *on* the kit's own values where the kit has an opinion
beats one that lands near them: COSMIC's eleven-slot ramp is anchored so §2's
four neutrals fall exactly on slots 0, 3, 8 and 10. An even ramp missed DARK by
ΔE 0.1 and LIGHT by ΔE 1.4 — close enough to look right, and wrong enough that
COSMIC would paint surfaces at values the kit never authored.

**A ladder that cannot land off the kit's values beats one that has to be right.**
Firefox's grey ramp is twenty slots and it is *renumbered* under
`browser.nova.enabled`, so an interpolated ladder would be sixteen invented
values that are correct under one numbering and wrong under the other. Snapping
each slot to the nearest of §2's four instead means a slot can move one step
along the kit's own ladder when the pref flips and cannot leave it. Where the
platform's own scale is stable, anchor and interpolate; where it moves, snap.

Three things the second checker added, and each is worth carrying to the next
surface:

- **The sheet keeps one invariant so the checker can be mechanical.** The only
  literal colours in `userChrome.css` and `userContent.css` are twelve `--rm-*`
  definitions; every other declaration refers to those by name. So "a value
  nobody derived" stops being a judgement call — a hex outside that block is a
  defect by construction. So is any notation that mixes (`rgba`, `color-mix`,
  `light-dark`, an alpha hex) or any CSS named or system colour, because a mixed
  value is not an authored value and nothing downstream can measure one.
- **It measures pairs rather than reading a table.** A stylesheet says what text
  sits on what ground, which a `.ron` file never did, so the checker reads both
  sides out of the file and measures them — including the `font-weight` the rule
  sets, which picks the APCA tier. That is how the non-key titlebar and the
  status panel were caught sitting at Lc 61.2 with no weight on them; a
  hand-written table would have recorded 61.2 and called it authored.
- **It reads the platform's vocabulary off the machine.** `--coverage` pulls the
  token names out of the installed build's `omni.ja`, because Firefox renames
  tokens most releases and a renamed token is how a strip silently falls back to
  a Mozilla colour. It is a report, not a gate: it needs Firefox installed, and
  an unset token is a question rather than always a defect.

And one the third checker added, which only a surface with this reach needs:

- **It enforces the exemption rather than relying on it.** The other two
  surfaces cannot touch content, because chrome is all they reach.
  `elevated/remainder.user.css` reaches everything, so `build/stylus.py` fails if
  any rule gives an authored colour to an `img`, `video`, `canvas`, `picture`,
  `svg`, `iframe`, `embed`, `object`, `source` or `audio`. Restoring one —
  `color: inherit`, `filter: none` — is not painting it, and a selector that
  names a content tag only inside `:not()` is not painting it either, so `:not()`
  is stripped before the check: excluding them is that rule's whole job. §0a
  stops being a promise in a comment and becomes a thing that fails.

**The icon theme has a checker too, and it is a different shape.** Its output is
never committed and never redistributed (§4), and its values are not a ladder, so
there is no file to scan. What must hold is the bar itself: *every value the
projection can emit* clears §1 and is not reserved by §3.

```
python3 build/remainder_space.py --check   # sweep the ramp, both sets of knots
```

It reports 0 breaching, 0 reserved, 0 outside sRGB, each knot reproduced
bit-for-bit, the worst lightness error, and the angular slack at the narrowest
point of the readable band. A generated surface owes the same proof as a
committed one — it just cannot be checked by reading a file, so the check is a
sweep of what the generator is capable of rather than an audit of what it did.

## 9. Measure, don't eyeball (principle 10)

A new value lands with its measurement beside it: the number, what produced it,
the date, and the machine where the machine matters. Nothing arrives as "looks
right".

- **Lc is stated with its pair and its sign** — WHITE on ACCENT is Lc −78.5 —
  never alone.
- **ΔE is stated with its pair** — WHITE/LIGHT is ΔE 17.1.
- **A clearance is stated with the pole it clears and what that chroma
  requires** — 31.1° from destructive, needs 10.5. The requirement is a
  function of the value's own chroma, so a bare degree figure does not say
  whether it passed.
- Values the whole kit depends on go in `palette.json`, which is generated —
  so they go in the constant that produces them. Values the authority names go
  in `AUTHORITY.md`. Platform facts go in `PLATFORM.md` (§11).
- **Failed trials are kept, dated, with what they produced.** The record is why
  no one tries them twice:

| Tried | Produced | Retired because |
|---|---|---|
| maximise chroma inside the arc | `#FD8BFF`, `#9400FB` | clear of every pole and unusable (§0c) |
| guard the arc at `DELTA_MAX` = 19° | admitted `#6A69AA`, `#A1576B` | a discrimination threshold is not an identification boundary (§1) |
| a pale selection tint | Lc 73.7 at ΔE 15.1 | failed both ways at once (§2) |
| solving `BLACK_L` | L 0.21 | squeezed DARK into a corridor 0.076 wide (§2) |
| an even eleven-slot COSMIC ramp | DARK off by ΔE 0.1, LIGHT by 1.4 | the platform would paint unauthored values (§8) |
| WCAG 2.x contrast | four pairs identical at "AAA 7.1:1" | APCA separates them Lc 51.7 to 78.9; two were display-type only (§0e) |

A value with no measurement beside it is a guess, and the next person cannot
tell it from a measured one.

## 10. QA every build visually (principle 12)

```
python3 build/qa.py
```

It renders the palette as a surface rather than as swatches — a mock window
using every authored value in the role it actually plays — so "is this pleasant
to look at for eight hours" can be asked of something that looks like a screen.
SVG, so it needs nothing installed and diffs as text. The raster beside it is
not committed (§11).

On a surface that installs, the proof sheet is not enough: the theme a toolkit
builds is not the theme that was imported. COSMIC derives surfaces no file
records, so those values exist only on the screen. On COSMIC the pass is
non-interactive:

```
cosmic-settings appearance export ~/.local/state/remainder/before.ron
sh worksafe/cosmic/install.sh
cosmic-screenshot --interactive=false --modal=false --notify=false
```

Sample the regions out of the PNG and run the samples back through
`build/poles.py`. Sampling needs Pillow; the pole test needs only numpy.

**Regions, never the whole frame.** A screen-wide histogram averages chrome
together with content, and content is exempt (§0a) — one maximised application
drawing its own white can put the authored share under 10% while every piece of
chrome on the screen is exactly right. Sample the panel, the dock, the gaps and
the window fields separately, and say which is which. Measured 2026-09-19 on a
3840×2160 @ 150% COSMIC desktop: whole-frame, 9.7% of pixels were an authored
value; by region, the panel was 96.6% exactly LIGHT, the gaps 100% exactly
BLACK, and nothing in either was inside a pole.

What the pass is looking for: no hue in chrome that reads as a signal (§1); the
three semantic hues present only where the meaning is (§3); one rule, the same
width everywhere, carrying no state (§5); the cursor findable at a glance on a
field of text (§2); and the removal done (§0) — no recommendations, no nags, no
motion, no blur.

## 11. Generated, ignored, and parallel files

| File | Rule |
|---|---|
| `palette.json` | generated **and committed**; guarded by the check in §7 |
| `elevated/remainder.stylus.json` | generated **and committed**; guarded by `build/stylus.py` |
| `arc_ramps.svg`, `magenta_field.svg` | pixel-grid renders of several MB; regenerate, never commit |
| `*.png` | rasters of the committed SVGs. The SVG is the artifact; a PNG beside it is a second copy that goes stale silently |
| the icon theme | built at install time into `~/.local/share/icons/remainder` from the icons that machine already has. The user's own brands in the user's own paint; the kit has no license to redistribute anybody's brand art (§4) |
| `references/` | reading, not kit material |
| `__pycache__/` | always |

The small figures **are** committed — `poles_and_palette.svg`, `arc_guards.svg`,
`arc_swatches.svg`, `floor_vs_margin.svg`, `qa_surface.svg` — because each
documents a decision cheaply and each is reproducible by a command named in the
README.

`elevated/remainder.stylus.json` is the second generated file that ships, for
the parent kit's reason: Stylus imports its own JSON and balks at `*.user.css`,
so the import file has to ship. `elevated/remainder.user.css` is the source.
After editing the sheet: bump `@version`, add the change to the header's
changelog with what it fixed, run `python3 build/stylus_json.py`, and commit both
files together. `build/stylus.py` checks all three of those: that the committed
JSON is what the generator now produces, and that the `@version` in the header
has a line beneath it saying what it changed. One field is compared out —
`installDate` is a timestamp taken at generation, so the file is byte-stable
between edits and not between runs.

**`PLATFORM.md` is parallel in both kits.** It records facts about platforms,
and platforms do not have opinions about either palette. Change it in both, or
it is out of date in one. Keep color out of it — a registry key belongs there,
the value written to it does not.

## 12. License

Two licenses, split by what the file is; a file's license follows the directory
it lands in.

| Covers | License | Text |
|---|---|---|
| `build/`, `elevated/`, `worksafe/` | GNU GPL v3.0 or later | `LICENSE` |
| `AUTHORITY.md`, `PLATFORM.md`, `poles.json`, `palette.json`, the figures, `README.md`, this file | CC BY-SA 4.0 | `LICENSE-CC-BY-SA` |

Contributing is agreeing to those terms for what you contribute. Both are
copyleft: a derivative is shared under the same license. Color values are not
copyrightable; what is licensed is the documents and code that express them.

**The kit ships no fonts.** §5 declares two typefaces and `install.sh --fonts`
fetches them from the projects themselves at a pinned tag — Hack v3.003 from
`source-foundry/Hack` (MIT), Montserrat v7.222 from `JulietaUla/Montserrat`
(SIL OFL 1.1), the repository its own `OFL.txt` names — verifying each file
against a SHA-256 recorded in the installer and installing the license beside
the faces. A file whose checksum does not match is not installed, and the
installer says so rather than carrying on.

Adding or moving a font means re-recording those checksums from the
authoritative download, in the same commit, with the date. A vendored copy is
worse than a fetch: its provenance is whatever the person who added it had to
hand. Measured 2026-09-19, the four Hack faces that were vendored here matched
the v3.003 release byte for byte and the four Montserrat faces did not match
the repository its license names.

**The kit ships no artwork either, and the rule is the same one.** §5 permits
photographs as content, and the installer fetches one — Art Institute of
Chicago 1938.454, *Jar with Peonies and lid*, which the museum publishes as
public domain under its Open Access policy — from the museum's own IIIF
endpoint at a pinned width, against a SHA-256 recorded in the installer, with
the credit line written beside the file the way a font licence is written
beside the faces. An unverified image is not installed and the background falls
back to the flat BLACK field.

Three things this rule is load-bearing about:

- **The image is never committed and never modified.** It is fetched at install
  time like the fonts and the icon theme (§11). Cropping a museum photograph to
  suit a screen, or recolouring it toward the palette, would make the kit the
  author of something it did not make and would break the provenance the credit
  file asserts. `scaling_mode: Fit` exists so the screen adapts to the object
  rather than the reverse.
- **A work arrives with its rights checked at the source, not inferred.** The
  AIC API reports `is_public_domain: true` and no copyright notice for 1938.454,
  checked 2026-09-19; the credit file records the object page and the museum's
  terms. "It came up in an open-access search" is not a rights check.
- **Content is exempt from §1 and is not evidence for it** (§3). The two glazes
  measuring into the home arc and the cursor gap is why *this* object and not
  another, and it is recorded in the installer with the date. It is not a
  clearance the kit claims, and no value sampled from it enters the palette.

Remainder is derived from the De Stijl theme kit, CC BY-SA 4.0 for its design
documents and GPL-3.0-or-later for its code. Work carried over says so where it
lands: `build/stylus_json.py` is carried with paths renamed, and `PLATFORM.md`
is seeded from that kit's §7.

## 13. The form of a change

- Issues are files: `issues/NNN-slug.md`, titled, with `**Labels:**` and
  `**Implements:** AUTHORITY.md §…` beneath, then what was observed, dated,
  with the numbers.
- A change that alters a rule edits `AUTHORITY.md` in the same commit as the
  thing that proves it. The authority is not brought up to date afterwards from
  memory.
- A change to a color edits `poles.json` or the derivation — never
  `palette.json`, and never a value in `AUTHORITY.md` alone (principle 13).
- A commit subject names the surface or the section it touches; the body says
  what was measured.

Before it lands:

- the pole test passes over every chrome value the change authors, and every
  value it puts inside a pole is content (§3) or one of §3's three;
- regenerating leaves `palette.json` byte-identical (§7);
- the surface's checker exits zero, and nothing reports `NOT DERIVED BY ANY
  LADDER`;
- every new number is labelled chosen or derived, with its measurement, date
  and machine beside it;
- text is measured in Lc with its pair and sign, surfaces in ΔE with theirs,
  and nothing is measured in WCAG;
- the margin over each floor is stated, and CURSOR is re-checked if anything it
  stands on moved;
- the build has been looked at (`build/qa.py`), and on a surface that installs,
  looked at on the screen;
- nothing generated is committed except `palette.json` and the Stylus JSON, and
  no font and no icon is committed at all;
- anything the change does to the user's machine beyond painting it is behind a
  flag, off by default, and undoable;
- a font the installer fetches is pinned to a tag and verified against a
  checksum recorded from the authoritative download, dated;
- a `PLATFORM.md` change is in both kits;
- the tier the change ships in matches the privilege and the reach it needs.
