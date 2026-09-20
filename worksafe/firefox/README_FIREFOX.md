# Remainder — Firefox

Firefox draws its own chrome and hands the whole of it to a per-profile
stylesheet, so every strip gets an exact value. It is also the one surface on
this desktop that can show key/non-key state at all: `PLATFORM.md` records that
this libcosmic paints header bars with the window background, so every native
window reads as non-key. Everything here is per profile, no sudo.

```
sh worksafe/firefox/install.sh          # Firefox closed; asks one question, then start Firefox
```

Measured on **Firefox 155.0.1** (deb) on COSMIC, 2026-09-19.

| File | What it does |
|---|---|
| `user.js` | prefs, read at every start: enables the stylesheets; Firefox draws its own titlebar so the tab strip can be the key one; compact density; square bottom corners; scrollbars always shown; reduced motion; light; Montserrat and Hack; and the §0 declutter — sponsored tiles at their source, urlbar suggestions, trending, weather, promos, "what's new", hover previews, recommendations, and the two machine-learning features 155 turns on by default. |
| `chrome/userChrome.css` | the chrome. The only literal colours in it are the twelve `--rm-*` definitions; every other declaration refers to those by name, which is what makes `build/firefox.py` able to prove there is nothing else in there. |
| `chrome/userContent.css` | the pages Firefox itself draws — new tab, home, blank, the `about:` pages. Web pages are untouched: content is exempt (§0a) and the all-sites sheet is a different tier. |
| `install.sh` | finds the profile this Firefox install opens, backs up what it replaces into `~/.local/state/remainder`, copies the three files in. Refuses while Firefox is running, and refuses under `sudo`. |
| `install.sh --ublock` | the same, plus uBlock Origin from addons.mozilla.org into the profile's own `extensions/`, with `extensions.autoDisableScopes` narrowed to 14 so a profile-directory extension starts enabled instead of asking. §0: advertisements are noise. Off by default, and the question defaults to **no** — see below. |
| `install.sh --stylus` | the same, plus Stylus, which loads `elevated/remainder.user.css` — the kit's all-sites sheet. Sideloading puts the extension in the profile; importing the sheet is a manual step and always will be, because Stylus imports through its own UI. |
| `install.sh --style` | print the file to import and exit. Writes nothing, asks nothing, does not need Firefox closed. |

## The shape of it

| Surface | Value | Text |
|---|---|---|
| tab strip, key window | ACCENT `#763555` | WHITE, 400 — Lc −78.5 |
| tab strip, non-key window | LIGHT `#BAADB2` | BLACK, 700 — Lc 61.2 |
| the current tab | LIGHT `#BAADB2` | BLACK, 700 |
| a hovered tab | BLACK `#10080C` | WHITE, 400 — Lc −92.3 |
| toolbars, bookmarks bar | LIGHT `#BAADB2` | BLACK, 700 |
| address and search fields | WHITE `#F1E4E9` | BLACK, 400 — Lc 91.8 |
| menus, panels, the results list | LIGHT `#BAADB2` | BLACK, 700 |
| buttons on a panel | WHITE `#F1E4E9` | BLACK, 400 |
| hover, and the selected row | SELECT `#521436` | WHITE, 400 — Lc −87.5 |
| pressed | BLACK `#10080C` | WHITE |
| a toggle that is on | ACCENT `#763555` | WHITE |
| focus ring, links | ACCENT `#763555` | — links keep the underline (§3) |
| the caret | CURSOR `#007891` | Lc 60.7 on WHITE |
| disabled | its own ground | DARK `#4B4045` |

Every nesting alternates WHITE and LIGHT, ΔE 17.1 — the separator §5 names and
the floor §2 derives from it. Nothing draws a line: §5 has no rule thinner than
the rule, so where Firefox drew a hairline the tone changes instead.

## Three decisions worth naming

**The labels on LIGHT are bold, and that is a measurement.** BLACK on LIGHT is
Lc 61.2, which is APCA's 16px/700 tier and not its 16px/400 one. So every LIGHT
surface carries 700 and every WHITE one nested in it goes back to 400 — the
weight changes exactly where the ground changes. `build/firefox.py` reads the
weight out of each rule block and picks the floor from it, which is how the
non-key titlebar and the status panel were caught sitting at 61.2 with no weight
set on them.

**A hovered tab is BLACK, not SELECT.** SELECT is the kit's hover everywhere
else, and on the ACCENT tab strip it is ΔE 11.8 from the ground — under the 17.1
floor, so it would not read as a separate surface at all. BLACK is ΔE 29.0. It
also darkens where the current tab lightens, so a hovered tab cannot be mistaken
for the selected one.

**Private browsing keeps Firefox's own mark.** §8 carries state by the three
semantic hues when the meaning is present and otherwise by tone and geometry.
Private browsing is not success, warning or destructive, and the kit has exactly
two tones far enough from ACCENT to repaint a whole strip with — BLACK and
WHITE. BLACK is spent on hover, and WHITE would read as a selected tab the width
of the window. So the state stays on Firefox's mask mark and its label, which is
geometry, and the sheet only makes sure the mark reads on both strips.

## The ladder

Firefox's design system bottoms out in a grey ramp of twenty slots where §2 has
four, and about two hundred named tokens resolve through it. The kit **snaps**
each slot to the nearest of §2's four by lightness rather than interpolating
sixteen new values into it, and the reason is `browser.nova.enabled`: it
renumbers the ramp, and under the other numbering three slots land on a
different kit neutral. Interpolated, those would be sixteen values that are
right under one numbering and wrong under the other. Snapped, a slot can move
one step along the kit's own ladder and cannot land off it.

```
python3 build/firefox.py --derive      # the ramp, both numberings, and where each slot lands
python3 build/firefox.py               # every value, pair and adjacency in the sheet
python3 build/firefox.py --coverage    # which of the installed Firefox's colour tokens are unset
```

`--coverage` reads the token vocabulary out of the installed build's `omni.ja`,
because that vocabulary is renamed most releases and a renamed token is exactly
how a strip falls back to a Mozilla colour. Of the 386 colour tokens the 21 `*.tokens.css`
files define, the sheet decides **258**; of the eleven unset ones whose default
blends, six remain, and all six are shadows or the modal scrim.

## Reached, measured

Sampled by region from a `cosmic-screenshot` of two running windows — one key on
`about:preferences`, one not — at 3840×2160 and 150%, 2026-09-19. The distinct
values over 3% of any region are `#521436 #763555 #BAADB2 #F1E4E9`, and
`build/poles.py` exits zero on all four:

| Region | Authored | Modal |
|---|---|---|
| tab strip, key window | 100.0% | ACCENT, 100.0% |
| tab strip, non-key window | 98.8% | LIGHT, 99% |
| the current tab | 94.2% | LIGHT, 93% |
| the toolbar, key / non-key | 89.8% / 89.6% | LIGHT, 90% / 89% |
| the address field | 87.2% | WHITE, 78% |
| the content field | 100.0% | WHITE, 100% |
| `about:preferences`, the page ground | 99.9% | WHITE, 100% |
| `about:preferences`, a card | 98.7% | LIGHT, 97% |
| the page nav's selected item | 85.8% | SELECT, 76% |
| the gap above the window | 100.0% | BLACK, 100% |

Regions, never the whole frame: a screen-wide histogram averages chrome together
with content, and content is exempt (§0a). The remainder in every region under
100% is glyph and icon antialiasing — the address field reads lowest because it
is mostly placeholder text — which is the same residue the COSMIC pass records.

**The pass found one defect the checker could not.** The selected item of an
`about:` page's navigation measured `#E7D6DE`, which is ACCENT at 8% over the
WHITE field and a value no ladder produced: Firefox paints it
`color-mix(in srgb, currentColor 8%, transparent)`. Two things had to change. The
sheet now names SELECT there, like every other selected row. And it has to name
it **on the custom element**, because a component's own `*.tokens.css` declares
its tokens on `:root, :host` and the `:host` half lands on the element itself,
where it beats a value inherited from `:root` whatever the origin — importance
does not cross inheritance. `build/firefox.py --coverage` now enumerates every
`*.tokens.css` in the installed build rather than reading a fixed list, and it
separates the tokens whose own default blends from the rest, so the next one of
these is a line of output instead of a thing to notice by eye.

**The popups are measured too, by asking the chrome rather than photographing
it.** XUL menus need a click that Wayland will not let a script synthesise, and a
headless chrome screenshot does not composite a popup even when it is open. But
the cascade has already run by then, and `getComputedStyle` is its answer — for
"did the menu actually get LIGHT", the computed value *is* the measurement, and a
better one than counting pixels: exact, no window needed, and it names the
element that lost instead of averaging a region. Firefox's own Marionette socket
opens the menu (`PanelUI.show()` in chrome context) and reads the styles back.

Measured that way with the app menu open, 2026-09-19:

| Element | Ground | Text | Weight | Radius |
|---|---|---|---|---|
| the application menu panel | LIGHT | BLACK | 700 | 0 |
| a panelview inside it | LIGHT | BLACK | 700 | 0 |
| a menu item | WHITE | BLACK | 400 | 0 |
| the overflow panel | LIGHT | BLACK | 700 | 0 |
| the urlbar results list | LIGHT | BLACK | 700 | 0 |
| the page context menu | LIGHT | BLACK | 700 | 0 |

It found three things a screenshot could not have. The outer `panel` element
computed **WHITE text on a transparent ground** — invisible on anything the kit
paints, and waiting for the first child that did not get BLACK explicitly. Menu
items computed **weight 600**, a tier APCA does not define and the kit never
authored, because Firefox declares `.subviewbutton { font-weight: 600 }` *on the
item*. And every popup computed the platform **sans-serif** rather than §5's
Montserrat.

All three are the same rule, the one `PLATFORM.md` records for `:host`: **a
declared value beats an inherited one, however important the inherited one was.**
`:root` can hand a face and a weight down the tree and any element that declares
its own wins anyway. Three declarations on the popups fixed all three.

A menu item is WHITE on the panel's LIGHT for the reason the sidebar's tree is:
it is a list on a panel, and BLACK on WHITE is Lc 91.8 where BLACK on LIGHT is
61.2. The panel is the frame; the rows are the field.

## Residue

- **Shadows and scrims.** Firefox derives some surfaces by alpha-mixing —
  `color-mix(in srgb, currentColor N%, transparent)` and the
  `--color-*-alpha-*` primitives. A mixed value is not an authored value and no
  checker can see through one, so the sheet names an authored value wherever
  such a mix painted a *surface*. What is left is exactly six tokens —
  `--background-color-overlay`, `--panel-box-shadow` and the four
  `--box-shadow-color-*` — and §4 inherits real shadows as permitted.
  `--coverage` lists them, so the set is checked rather than remembered.
- **A brand-new profile shows Firefox's terms notice**, which dims the whole
  window at 75% black. A first capture of a fresh profile measures LIGHT × 0.25
  and ACCENT × 0.25, not LIGHT and ACCENT. That is the modal scrim above and not
  a defect in the sheet; `termsofuse.bypassNotification` gets past it for a QA
  profile. The kit's own `user.js` does not set it — accepting terms is not
  something a theme does on a user's behalf.
- **Favicons and tab-group colours.** Both are information, not chrome. A
  favicon is a brand and §4 leaves a brand its own art; a tab-group colour is a
  label the user assigned, and §3's own test says so — remove it and the group
  is harder to find. Firefox's nine group colours are left as they are.
- **The dock icon while Firefox runs** is Firefox's own, not the kit's: a
  running Wayland window supplies its icon directly.
- **GTK dialogs** (the file picker) are GTK's.
- **Page content** keeps its own colours, by design.

## Importing it: the JSON, not the CSS

Stylus reads its own JSON export cleanly and balks at a `*.user.css` file, so the
kit ships both and they do different jobs:

| File | What it is |
|---|---|
| `elevated/remainder.user.css` | the **source**. A person edits this one. |
| `elevated/remainder.stylus.json` | **what you import.** Generated from the source by `build/stylus_json.py`, and committed, because the import has to work on a machine that is not running the generator (`CONTRIBUTING.md` §11). |

Stylus › Manage › Import, and choose the JSON. `sh install.sh --style` prints its
path and exits without writing anything.

The parent kit also carries a `--style-css` fallback that serves the `.user.css`
over localhost so Stylus can offer its own install page. That is deliberately not
here. It exists because a `.user.css` *can* be installed that way, not because it
is the better route — it needs a server, a port and a browser window to go right,
where the JSON needs a file picker. One way in, and it is the easy one.

After editing the sheet: bump `@version`, add a line to the header changelog
saying what it fixed, run `python3 build/stylus_json.py`, and commit both files
together. `build/stylus.py` fails if the committed JSON is not what the generator
now produces, or if the `@version` has no line beneath it — so the two files
cannot drift apart quietly.

## The other half, and where the caret went

`elevated/remainder.user.css` is built, and `build/stylus.py` checks it. Firefox
hands an all-sites sheet to a per-profile extension, so it needs no elevation on
this surface — it belongs in `elevated/` because its reach is every site, not
because of its privilege (`CONTRIBUTING.md` §1).

**The caret is there now.** §2 gives CURSOR one job — a locator, found fast and
repeatedly on a field of text — and this sheet stops at the chrome's own fields
and the `about:` pages, because the kit cannot measure the ground of a page it
has never seen. The all-sites sheet can: every field it paints is WHITE or
LIGHT, and CURSOR measures Lc 60.7 on the first and 30.2 on the second, over
APCA's floor for a mark on both. So the caret is CURSOR on every field a user
types in, and the ground under it is one the kit chose.

## Why the fonts are not fetched here

`worksafe/cosmic/install.sh` pins Hack and Montserrat to a tag and verifies each
file against a SHA-256 recorded in it (`CONTRIBUTING.md` §12). One installer owns
those checksums; a second copy would be a second thing to keep true. This
installer only reports whether the faces are on the machine and prints the one
command that installs them.

## Why uBlock defaults to no

The COSMIC installer's two questions default to yes: the fonts are the faces §5
declares, and the icons are the machine's own art reprojected. uBlock Origin is
another project's program. §0 holds that advertisements are noise and the kit
will fetch it on request, but it will not put somebody else's program on a
machine unless it is asked in so many words.
