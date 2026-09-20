# Remainder — Windows 11

AUTHORITY.md §0 opens with "the point is to save users from Windows". This is that
sentence aimed at the machine it was written about.

It is in `elevated/` because it needs administrator, which is the first surface in
the kit that does. Everything here except one file is `HKCU` and would run
per-user; `fonts.reg` is `HKLM`, and CONTRIBUTING §1 is explicit that a residue
elevation could remove is not residue — it is removed in `elevated/` and merely
tolerated in `worksafe/`. Segoe UI in the system chrome is exactly that case, and
PLATFORM.md already records it as out of reach per-user.

```
install.cmd          double-click it; it asks Windows for administrator itself
```

## What is measured here, and what is not

This matters more on this surface than on the other three, so it is first rather
than buried.

**Measured, and gated by `build/windows.py`:** every colour value, every
text-on-ground pair's APCA Lc, every adjacency's OKLab ΔE, every pole clearance,
and every one of the five notations Windows stores colour in. All of it is
colorimetry. None of it needs Windows, and the checker exits nonzero on a defect.

**Not measured, and not gated:** that any of these registry keys exists on 24H2,
that it does what it is claimed to do, or that the install order below is the one
that survives. Those claims come from `PLATFORM.md` and this kit has no Windows
machine to put them on. `python3 build/windows.py --registry` prints them as a
table with a status against each, the way `build/firefox.py --coverage` prints the
token names it read off the installed build: a report, never a gate.

So: the colours are right, and the plumbing is inherited. If a key turns out to be
wrong, that is a `PLATFORM.md` correction — and `PLATFORM.md` is parallel in both
kits, so a key confirmed here is confirmed for De Stijl too (CONTRIBUTING §11).

## The files

| File | What it does | Generated |
|---|---|---|
| `remainder.theme` | the thirty-one legacy Win32 colour slots, the flat BLACK desktop, light mode, no transparency. Double-click applies it. | yes |
| `remainder.reg` | the same table as registry values, plus the DWM accent and its inactive pair, the eight-slot accent palette, and the motion and transparency §0 removes. | yes |
| `declutter.reg` | §0's larger half: recommendations, tips, the welcome experience, lock-screen facts, the suggestion toast, taskbar left, widgets and task view and Copilot off, search off the taskbar. **No colour at all**, and the checker proves that rather than asserting it. | no |
| `fonts.reg` | `HKLM` FontSubstitutes, Segoe UI → Montserrat. **Opt-in** (`install.cmd --fonts`), and it refuses to merge unless Montserrat is already installed. | no |
| `install.cmd` | backs up every key it will touch, then applies the above in an order that does not undo itself, then restarts the shell. `--restore DIR` puts a backup back. | no |

The two generated files are generated **and committed**, for the reason
`elevated/remainder.stylus.json` is (CONTRIBUTING §11): the file Windows reads is
not a file a person should be editing. A hand-typed ABGR DWORD is precisely the
value §8 says a checker catches more reliably than the pole test does. Regenerate
with `python3 build/windows.py --write`; the checker fails if what is committed is
not what the generator now produces.

**They are ASCII, CRLF, and carry no byte-order mark**, which is the one place this
surface departs from the kit's house style. The rest of the kit writes UTF-8 and
uses `§` freely. Windows reads a `.reg` or `.theme` without a BOM as ANSI, so a
section mark in a comment would import as mojibake — the section references in those
two files are spelled out instead, and `build/windows.py` refuses to write a
non-ASCII byte rather than leaving that to be noticed later.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| titlebar, key window | ACCENT `#773556` | WHITE — Lc −78.5 |
| titlebar, non-key window | LIGHT `#B8AEB2` | BLACK — Lc 61.3 |
| the desktop field | BLACK `#0F090C` | — §5, flat, no wallpaper |
| window backgrounds, lists, menus, tooltips | WHITE `#EFE5E9` | BLACK — Lc 91.9 |
| panels, buttons, toolbars, the scrollbar trough | LIGHT `#B8AEB2` | BLACK — Lc 61.3 |
| the selected row, the highlighted menu item | SELECT `#531537` | WHITE — Lc −87.5 |
| hover and links | ACCENT `#773556` | Lc 75.4 on the field |
| disabled | DARK `#4A4145` | Lc 48.4 on a panel |
| every border and frame | BLACK `#0F090C` | — the rule (§5) |
| the text cursor indicator | CURSOR `#007891` | — **a manual step, see below** |

Thirty-one slots, six of §2's seven values, and nothing interpolated. Windows'
colour table is a table of *roles*, not a ramp, so each slot is a role assignment
and the ladder is the assignment itself — the arrangement §8 prefers, because it
cannot land off the kit's own values.

## Four decisions worth naming

**The Win95 bevel is gone, and that is §5 rather than taste.**
`ButtonHilight`, `ButtonLight` and `ButtonFace` all take LIGHT, so the light edge
of every 3D control collapses into its face. §5 has one rule and nothing thinner
than it: a bevel is a separator lighter than the rule, and the kit does not draw
one. `ButtonShadow` stays DARK and `ButtonDkShadow` stays BLACK, so a control that
genuinely needs an edge still has the rule to draw it with.

**A window's edge against the desktop is ΔE 0.0, on purpose.** `ActiveBorder`,
`InactiveBorder`, `WindowFrame` and `Background` are all BLACK. §5: the gap *is*
the rule, so a window edge reads as its own field against the surround rather than
as a line drawn on it. §2 exempts rule-against-chrome from `SURFACE_FLOOR` for this
exact reason, and the checker prints the pair as exempt rather than passing it.

**The titlebar gradient is flattened.** `GradientActiveTitle` equals `ActiveTitle`
and `GradientInactiveTitle` equals `InactiveTitle`. A gradient is a continuous run
of values nobody authored, across the one surface in this theme that carries state.

**`HotTrackingColor` on a panel is a mark, not a label — and it is recorded, not
fixed.** ACCENT on the WHITE field measures Lc 75.4, which is APCA's body-text
minimum and is where links actually live. ACCENT on LIGHT measures **Lc 44.8**,
which clears APCA's non-text tier of 30 by +14.8 and does not reach a reading tier.
So hover on a panel reads as an indication and not as text you are meant to read at
that contrast. Moving it would mean leaving the chroma §2 chose for the accent, and
§0c is explicit that CHROME 0.100 is a choice the kit makes and keeps.

## The accent ramp

Windows stores its accent as eight RGBA quads. Seven are a light-to-dark ramp it
reads by index — index 3 is the accent Settings shows and `AccentColor` mirrors,
and the darker indices are what the menus and Start read — and index 7 is a
separate emphasis slot that Windows ships as an **orange**, inside the caution
pole. The kit gives that slot ACCENT, which removes a pole from the chrome and
adds no value.

The ramp is **derived and nothing is invented**: the step is ACCENT-to-SELECT
halved, because those two sit two indices apart, repeated outward at CHROME chroma
and the home hue.

```
python3 build/windows.py --derive
```

| idx | hex | L | WHITE on it | BLACK on it | |
|---|---|---|---|---|---|
| 0 | `#AE6788` | 0.602 | −58.3 | 35.7 | a hover tint; takes dark text |
| 1 | `#9B5677` | 0.544 | −65.9 | 28.0 | |
| 2 | `#894666` | 0.487 | −72.5 | 21.0 | |
| 3 | `#773556` | 0.428 | −78.5 | 14.5 | **ACCENT**, exactly |
| 4 | `#652546` | 0.370 | −83.5 | 8.7 | |
| 5 | `#531537` | 0.311 | −87.5 | 0.0 | **SELECT**, exactly |
| 6 | `#420328` | 0.253 | −89.8 | 0.0 | |
| 7 | `#773556` | 0.428 | −78.5 | 14.5 | emphasis slot, off the ramp |

Five of these are new values and they are the only ones this surface adds; the
kit's distinct-value count went from 60 to 65 (CONTRIBUTING §2, re-measured
2026-09-20). Every one clears destructive by about 31° where its chroma requires
10.6, so **whichever index a given Windows build reads for a given surface, it
reads an authored value.** That property is deliberate: it is what makes the ladder
robust to the one thing this kit cannot verify from here.

The ramp is quieter than Microsoft's own — index 0 lands at L 0.60 where the
default blue's lands at about L 0.84 — because it stays at the chroma §2 chose.
Stretching it to match would have meant leaving that chroma, which is a preference
dressed as a derivation (§0c). The consequence is recorded instead: index 0 is a
hover tint that carries dark text, not a ground for white text.

## Installing

Double-click `install.cmd`. It asks Windows for administrator itself, so there is
no terminal to fight and nothing to type.

```
install.cmd                    back up, apply the theme, merge the colours and the declutter
install.cmd --no-declutter     paint only; leave the recommendations and the nags in place
install.cmd --fonts            also substitute Montserrat for Segoe UI (HKLM, opt-in)
install.cmd --restore DIR      put back a backup it wrote, and exit
```

You can do all of it by hand instead — both `.reg` files merge on a double-click of
their own, and `remainder.theme` applies on a double-click of its own. The script
exists for the three things a double-click cannot do:

**It backs up what it is about to replace.** Every key it writes is exported first
to `%LOCALAPPDATA%\Remainder\state\<date>-<time>\`, one `.reg` per key, a fresh
folder per run so a re-run cannot clobber an earlier one. The worksafe installers
save what they overwrite under `~/.local/state/remainder` (CONTRIBUTING §1); this
is the elevated tier and the same courtesy applies more, not less.

*What a restore cannot do*, stated because the script states it too: `reg import`
writes the values that were saved and does not delete values that did not exist
when the backup was taken. A key Remainder created from nothing is still there
afterwards.

**It puts the steps in an order that does not undo itself.** Applying a `.theme`
rewrites the DWM accent keys, so the theme goes first and `remainder.reg` second.
Reversed, the accent is Microsoft's again and the titlebar stops carrying state.

**It restarts the shell**, so the colour table and the taskbar values are re-read
without asking you to sign out.

### Three steps no installer can do

1. **The text cursor indicator.** Settings → Accessibility → Text cursor: turn the
   indicator on, custom colour `#007891`. That is CURSOR, the one value in the kit
   at another hue — §2 gives a locator its own hue because its whole job is to be
   found fast on a field of text, and solved at the home hue it came out within
   3 Lc of ACCENT. PLATFORM.md gives a Settings path for this and no registry key.
2. **Edge's frame.** `edge://settings/appearance`, custom theme colour `#773556`.
   It is a Preferences entry rather than a registry key, so it cannot be scripted —
   PLATFORM.md records that.
3. **Sign out and back in once** if anything still looks like Windows. A few
   surfaces read their colours only at logon.

## What is out of reach

Tolerated, never echoed (§4). PLATFORM.md is the record:

- **The 1 px DWM window frame.** DWM draws it and nothing per-user thickens it, so
  §5's rule width is not reachable on this platform. The frame takes BLACK, which
  is at least the rule's colour at the wrong weight.
- **Control corner radii**, and the Terminal and Chrome tab shapes.
- **Window corners** are reachable per-window via `DWMWA_WINDOW_CORNER_PREFERENCE`
  from any process, but not from a registry key, so this surface does not attempt
  them. A helper that sets them per window would be a program rather than a theme.

## Checking it

```
python3 build/windows.py              every value, every pair, every adjacency
python3 build/windows.py --derive     the two ladders and how each value was reached
python3 build/windows.py --registry   the registry claims and their status
python3 build/windows.py --write      regenerate remainder.theme and remainder.reg
```

The checker reads **every file in this directory** — including `install.cmd`, which
prints two hex values in its closing instructions and is scanned for them — in all
five notations Windows stores colour in:

| Notation | Where |
|---|---|
| `15 9 12` decimal triple, bare and quoted | `.theme` and `.reg` colour tables |
| `dword:00563577` ABGR, alpha high | DWM and `Explorer\Accent` |
| `0XC4773556` AARRGGBB | `.theme` `[VisualStyles] ColorizationColor` |
| `hex:ae,67,88,00,…` RGBA quads | `AccentPalette`, REG_BINARY |
| `#773556` | comments, and `install.cmd`'s instructions |

`build/cosmic.py` learned this the hard way: the COSMIC panel background sat
unchecked until the checker learned to read a RON decimal triple. A value the
checker cannot read is a value nobody is checking, and Windows is that problem five
times over. Two of those notations caught something during this surface's own
build — the quoted decimal triples in `remainder.reg` were going unread, and
`UserPreferencesMask` was being decoded as a colour that failed the pole test.
Both are in the module's comments where they happened.
