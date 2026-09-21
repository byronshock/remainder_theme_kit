# Remainder — Qt

A Qt application takes its colours from a palette — twenty-one roles, twenty-two
from Qt 6.6, in three groups — and a style paints every control from it. On
Linux, outside Plasma, the palette reaches the application through a platform
theme plugin, and the two a user can configure without elevation are qt5ct for
Qt 5 and qt6ct for Qt 6. This surface is that palette for both, and the same
palette a third time as a KDE colour scheme. Everything here is per user, no
sudo, and reversible; applications may stay open.

```
sh worksafe/qt/install.sh          # qt5ct, qt6ct, and the KDE colour scheme
```

Measured on **qt5ct 1.5 with Qt 5.15.13 and qt6ct 0.9 with Qt 6.4.2** (the
Pop!_OS 24.04 packages), on COSMIC, 2026-09-21; read off the sources of those
versions, of qtbase `v5.15.13-lts-lgpl` and `v6.4.2`, of KDE's `kcolorscheme.cpp`,
and of libcosmic and cosmic-settings-daemon. `PLATFORM.md` carries the platform
facts; this file carries what the kit does with them.

| File | What it does | Generated |
|---|---|---|
| `qt5ct/colors/remainder.conf` | the scheme: 21 `#AARRGGBB` per group in `QPalette::ColorRole` order, three groups. qt5ct wants exactly 21. **Generated and committed** (`CONTRIBUTING.md` §11); `build/qt.py` fails if it is not what the generator produces. | yes |
| `qt6ct/colors/remainder.conf` | the same 21 and a twenty-second, `Accent` (Qt 6.6+). qt6ct 0.9 takes 21 or more on any Qt 6, so one file serves 6.4 through 6.x. | yes |
| `kde/Remainder.colors` | the KDE colour scheme: the seven colour sets, the two effects groups, `[General]`, `[KDE]`, `[WM]`, decimal triples. | yes |
| `qt5ct/qt5ct.conf`, `qt6ct/qt6ct.conf` | the six keys `install.sh` merges into each tool's config: the scheme, `custom_palette`, the Fusion style, Montserrat and Hack at 12 pt, no motion. Fragments with comments, not files. | no |
| `install.sh` | copies each scheme into `~/.config/qt{5,6}ct/colors/`, merges the keys into `qt5ct.conf` and `qt6ct.conf` key by key, keeping every key it does not name; copies the KDE scheme to `~/.local/share/color-schemes/` and merges its groups into `~/.config/kdeglobals`. Backs each file up under `~/.local/state/remainder` on the first run. | no |

## The three constraints

**Fusion derives its chrome from the palette; it does not paint it.** Every
outline is Window darkened by 40%. A button face is Button lightened by up to
(180 − grey)/6 percent, desaturated to three quarters, and drawn as a gradient
from 124% to 102% of that; a tab page is the same value lightened 4% more; a
menu is Base lightened 8%; a check box is Base darkened 15% down to Base; the
focus frame is Highlight darkened by a quarter — some twenty values, computed
in Qt's own 16-bit HSV arithmetic with integer factors and float32 conversions
(`qcolor.cpp`), none of them a value the theme set and none the theme can
prevent. The constants are identical in 5.15.13 and 6.4.2. So `build/qt.py`
does what `CONTRIBUTING.md` §8 asks of a derived surface: it emulates `QColor`
— including the spec a colour is left in, since `lighter()` on an HSV colour
never touches RGB — computes every value Fusion will paint from the committed
palette, and holds each to the same bar as an authored one: clear of every
pole, not reserved, carrying its text at the tier. The on-screen pass then
found the model's bytes on the real window, exactly (below).

**The platform sets no weight.** A palette names colours; Fusion renders
labels, tab titles and button text at the application font's 400. BLACK on
LIGHT is Lc 61.3, the pair §2 authors as the 16px/700 tier, so on this surface,
as on VS Code, LIGHT cannot be the ground of a label a user reads. Read text
sits on WHITE, and where the style paints a face from an input, the input is
chosen so the *face* carries BLACK at the 400 tier.

**One highlight.** Qt 5 and Qt 6.4 have one role for what §2 splits in two: the
selection (SELECT carrying WHITE) and focus (ACCENT). `Highlight` paints
selected rows, selected text, the hovered menu item, the progress fill and the
focus frame alike. The text-carrying uses decide it: Highlight is SELECT, WHITE
on it Lc −87.5, and focus is a mark in SELECT darkened by a quarter, `#42112C`.
From Qt 6.6 a twenty-second role, `Accent`, takes what a style uses for toggles
and checked marks; the qt6ct file carries it as ACCENT.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| the window, dialogs, tool bars, the status bar (`Window`) | WHITE `#EFE5E9` | BLACK — Lc 91.9 |
| fields, views, lists, the combo box list (`Base`) | WHITE `#EFE5E9` | BLACK — Lc 91.9; placeholders DARK, Lc 78.9 |
| buttons, combo boxes, tabs, headers, scrollbars (`Button`) | `neutral_9` `#D3C9CD` as the input; Fusion paints `#FEF5F9` → `#D1CACD` | BLACK — Lc 88.1 where the label sits, 76.1 at the bottom stop |
| the tab page | Fusion paints `#DED6D9` from the same input | BLACK — Lc 83.0 |
| selected rows, selected text, the highlighted menu item, the progress fill (`Highlight`) | SELECT `#531537` | WHITE — Lc −87.5 |
| the focus frame, a focused edit's frame, the default button's outline | `#42112C`, Fusion's, from SELECT | a mark: Lc 88.1 against the field |
| links, visited links | ACCENT `#773556` | Lc 75.4 on WHITE, the body minimum |
| tool tips | WHITE `#EFE5E9`, framed 1 px in the text colour | BLACK — Lc 91.9 |
| disabled text | DARK `#4A4145` | Lc 78.9 on WHITE |
| a disabled selection | DARK `#4A4145` | WHITE — Lc −81.7 |
| the 3D ladder (`Light`, `Midlight`, `Mid`, `Dark`, `Shadow`) | WHITE, `neutral_9`, `neutral_6` `#8A8084`, DARK, BLACK | Fusion draws almost none of it; a sunken frame an application draws itself gets DARK and BLACK lines |
| **the KDE scheme's `Button` set** | DARK `#4A4145`, flat | WHITE — Lc −81.7 |

The inactive group is the active one: focus is shown by the caret and the key
window's mark (§2, §5), not by greying a selection in a window that is not key.
No alternating row band is drawn: a band lighter than LIGHT is not a tone change
(§5) and LIGHT cannot carry read text at 400, so `AlternateBase` is `Base`.

## Five decisions worth naming

**Button is `neutral_9`, chosen against the derivation.** §2 says buttons are
LIGHT, and Fusion cannot paint LIGHT: it lightens what it is fed and spreads it
into a gradient. `build/qt.py --derive` prints the trials:

| Input | Face top | Where the label sits | Face bottom | Tab page | BLACK on top / label / bottom / page |
|---|---|---|---|---|---|
| LIGHT | `#DED5D9` | `#CAC1C5` | `#B6AFB2` | `#C1BABD` | 82.6 / 71.4 / 61.5 / 67.3 |
| WHITE | `#FFFFFF` | `#F5F1F3` | `#ECE5E8` | `#FBF3F6` | clips to the reserved value (§3) |
| DARK | `#685E63` | `#5E5659` | `#554E51` | `#5A5256` | WHITE on it −70.9 at the top |
| **`neutral_9`** | `#FEF5F9` | `#E7DFE2` | `#D1CACD` | `#DED6D9` | 101.2 / 88.1 / 76.1 / 83.0 |

Only the ladder's slot between LIGHT and WHITE carries BLACK at the 400 tier at
every stop of the resting face and on the tab page, and it costs one thing the
checker reports rather than hides: a *hovered* face's top stop clips to
`#FFFFFF` for the duration of the hover (the resting face tops out at
`#FEF5F9`, ΔE 2.4 from it). No input keeps the hover off the reserved value
while the resting face still carries its label at the tier; the gradient's
spread makes the two ends of that trade the same lever. Two shortfalls stay
recorded: an unselected tab, at 85% of its height, carries its title at Lc 73.9,
1.1 under the tier, and a dialog's default button — mixed a tenth toward the
highlight by the style — reaches 66.1 at its last pixel row, under the label
whose own ground is 77.0.

**The KDE `Button` set is DARK, and Fusion's is not.** The KDE styles paint
`Button` flat and render its label at 400, which is where LIGHT fails as a
ground: BLACK on it is 61.3, and nothing else the set names reads on it either
— ACCENT 45, DARK 48, the ANSI red 47. DARK carrying WHITE is Lc −81.7, the
pair `build/vscode.py` gives its secondary button for the same reason, so the
set is DARK and every text role on it is WHITE. One role, two styles, two
answers, each measured against what its style paints.

**Semantic text on the KDE scheme takes the ANSI normals**, as on VS Code:
`ForegroundNegative` is `#930000` (Lc 75.2 on WHITE), `ForegroundNeutral`
`#525200` (74.3, at yellow's gamut cap), `ForegroundPositive` `#005900` (75.1),
because §3's FHWA values are grounds and marks, not text — DESTRUCTIVE on WHITE
is Lc 68.2 and WARNING on WHITE 8.2. On the dark sets, Selection and
Complementary, no hue reaches the text tier: the three tints of
`build/vscode.py` measure −59 to −86 on SELECT, so semantic text there is WHITE
and the row's other marks carry the meaning.

**The disabled state is tone.** Text goes to DARK (§2), a selection loses its
hue — DARK carrying WHITE — and grounds do not change. The KDE scheme reaches
the same place through KColorScheme's effects: intensity and colour effects
off, contrast fade at 0.26, which is *solved* so that the fade of BLACK into
WHITE lands nearest DARK — `#494245`, ΔE 0.35 from it, Lc 78.8. A derived
value, and the checker measures it.

**Tool tips are WHITE, and `QMdiArea` is DARK.** A tip carries read text, so it
is WHITE with BLACK, and QCommonStyle frames it 1 px in the text colour — a
control's own outline, as on VS Code's inputs. `QMdiArea` paints its background
in `Dark`, which is why the preview pane of qt5ct and qt6ct comes up DARK: the
role table's ladder, doing exactly what the role is for.

## The ladders

```
python3 build/qt.py --derive     # the role table, the ladders, Fusion's derivations, the Button trials
python3 build/qt.py              # every value, pair, adjacency and derived value in the three files
python3 build/qt.py --write      # regenerate the qt5ct, qt6ct and KDE schemes from the role table
python3 build/qt.py --installed  # the live machine: platform theme, plugins, the schemes in use (a report)
```

The 63 palette slots and the 13 KDE groups land on nine values the kit already
had: §2's seven, `neutral_6` and `neutral_9` of the COSMIC ladder
(`build/cosmic.py`), and the three ANSI normals. The surface added no value
(`CONTRIBUTING.md` §2). What the checker adds is the model: `fusion()` in
`build/qt.py` returns 38 derived values with what each paints and what text
sits on it, and every one is checked for the pole test, for §3's reserved
values (a resting ground that clips to `#FFFFFF` is a defect; a hover's top
stop is recorded), and for its text pair. Ten blends the palette cannot reach
are listed so the on-screen pass knows what it is looking at.

## Reached, measured

`sh worksafe/qt/install.sh --into DIR` writes a config directory of its own, and
`XDG_CONFIG_HOME=DIR qt6ct` and `qt5ct` — Qt applications themselves, with a
tab widget, buttons, combo boxes, an edit, a check box and a progress bar —
render the palette through the very plugin every other Qt application uses.
Sampled from `cosmic-screenshot` at 3840×2160 and 150%, 2026-09-21, pixel
columns read through each control (`CONTRIBUTING.md` §10):

| Control | Model | Measured, Qt 6.4 | Measured, Qt 5.15 |
|---|---|---|---|
| every outline | `#ABA4A6` | `#ABA4A6` | `#ABA4A6` |
| the tab outline | `#BCB4B7` | `#BCB4B7` | — |
| an unselected tab | `#CDC6C9`, then `#BFB8BB` | `#CDC6C9` ×14, then `#C1BABD` | `#CDC6C9` ×12, then `#C1BABD` |
| the tab page | `#DED6D9` | `#DED6D9` | `#DED6D9` |
| the selected tab, top | `#E6DEE2` | `#E6DEE1` | `#E5DDE0` |
| a button face, top to bottom | `#FEF5F9` → `#D1CACD` | `#FBF4F7` → `#D3CCCF` | `#FBF4F7` → `#D5CED1` |
| the default button's outline | `#42112C` | `#42112C` | — |
| the default button's face | `#EDDEE6` → `#C3B6BD` | `#EDDFE6` → `#C7BBC2` | — |
| the progress bar's outline | `#3B0F27` | `#3B0F27` | — |
| the progress fill, top to bottom | `#641942` → `#531537` | `#621941` → `#541538` | — |
| the field behind an edit | WHITE | `#EFE5E9` | — |

The outlines and the flat fills are the modelled bytes exactly; every gradient
agrees with its stops to the sampling of its first and last rows and the
antialiasing of a rounded corner over its ground (`#C4BDBF` is `#ABA4A6` at
half cover on `#DED6D9`). Both toolkits paint the same bytes. Two things the
model had not named were found and added: the default button's mix toward the
highlight, and the progress fill's gradient. The blue and orange columns inside
every glyph are the rasteriser's subpixel antialiasing (`PLATFORM.md`), and the
group box's interior, `#DBD3D6` over the `#DED6D9` page, is a translucent
pixmap of Fusion's.

The KDE scheme was measured through a Flatpak on the KDE runtime,
`org.kde.isoimagewriter` (runtime 6.11), with `QT_QPA_PLATFORMTHEME=kde` set
inside its sandbox: the window came up 95.1% WHITE, its text BLACK, its buttons
DARK carrying WHITE, and nothing of COSMIC's own derived scheme in it. What
Breeze adds is its own: frames and shades mixed from the scheme (`#C2B9BD`,
`#CEC4C8`, `#DED4D8`, all neutral), which no scheme value sets.

## Residue

Tolerated, never echoed (§4). `PLATFORM.md` is the record:

- **Everything Fusion derives.** Twenty-odd values from four inputs, above, and
  the blends: white at 30/255 inside every control, the focus rectangle at
  80/255, black 18 inside edits, the group box's interior. The kit chooses its
  inputs against the derivation and measures the result; it cannot make the
  style paint a value as given.
- **Menus are nearly white.** A menu is Base lightened 8%, and from WHITE that
  clips to `#FFF7FA` — L 0.98, ΔE 1.9 from the reserved `#FFFFFF`, brighter
  than any field the kit authors. The only lever is Base, which §2 pins.
- **The caret** is drawn in `Text`. CURSOR reaches no Qt role; the locator hue
  is absent from this surface.
- **Radii and line widths** are the style's: 2 px corners on buttons, edits and
  tabs, 1 px outlines in a derived grey. §5 draws no line thinner than the rule
  and Fusion draws none wider than 1 px.
- **Subpixel antialiasing** puts blue and orange fringes on every glyph stem.
- **The title bar** on COSMIC is the compositor's, painted with the window
  background (`PLATFORM.md`, COSMIC); the KDE scheme's `[WM]` — ACCENT carrying
  WHITE when key, LIGHT with BLACK when not, as §2 — is read by KWin and was not
  measured here.
- **Two Button values.** Fusion's input is `neutral_9` because the style
  lightens it into a face that carries its label; the KDE styles paint the
  role flat, so theirs is DARK carrying WHITE. Neither is LIGHT, which no Qt
  style renders as a ground a 400-weight label reads on.

## COSMIC's own export, and living beside it

COSMIC exports a Qt palette derived from the COSMIC theme when "apply theme to
other toolkits" is on, which Pop!_OS ships on. Measured on this desktop,
2026-09-21, before this surface was installed: of its 21 active roles 4 were
values the kit authors; its `Base` sat ΔE 7.3 from its `Window`, under the 17.1
surface floor — a field neither the same as the window nor distinguishable from
it; its `HighlightedText` read at Lc −51.8 on its `Highlight`, where WHITE gives
−78.5; its button text at 55.9, its placeholders at 47.5. `python3 build/qt.py
--installed` measures whatever the live config points at, so the comparison
runs on any machine.

The two coexist by the daemon's own contract, which `install.sh` reads back to
you. It keeps a marker, `cosmic_qt_version`, in `qt5ct.conf` and `qt6ct.conf`;
once that marker is at its current version (2) it rewrites only a scheme path
containing "Cosmic". Measured: the kit's path survived a theme re-import, with
the file's keys re-ordered and nothing else changed. `kdeglobals` has no such
guard: the same re-import rewrote every colour group and `[General]
ColorScheme` back to COSMIC's, and the daemon does that at every login and
theme change. So on COSMIC with the setting on, the qt5ct and qt6ct palettes
stay and the KDE scheme is COSMIC's again by the next login — which matters for
Plasma applications and for `--flatpak` (below), and for nothing else, since
every native Qt application reads qt5ct or qt6ct.

To keep the KDE scheme too, turn the setting off **before** running
`install.sh`: turning it off removes the scheme path from both confs, whoever
wrote it, and takes COSMIC's GTK export with it. Turning it on later replaces
the path once, at the first export; re-run `install.sh`.

## Installing, and undoing

```
sh worksafe/qt/install.sh                  # qt5ct, qt6ct, and the KDE scheme
sh worksafe/qt/install.sh --no-kde         # the two qt*ct targets only
sh worksafe/qt/install.sh --no-fonts       # leave the type alone
sh worksafe/qt/install.sh --no-declutter   # leave the animations on
sh worksafe/qt/install.sh --flatpak        # QT_QPA_PLATFORMTHEME=kde inside each KDE-runtime Flatpak
sh worksafe/qt/install.sh --platformtheme  # write ~/.config/environment.d/90-remainder-qt.conf
sh worksafe/qt/install.sh --into DIR       # the QA profile: XDG_CONFIG_HOME=DIR qt6ct
```

Nothing is asked. `--flatpak` and `--platformtheme` are off by default because
each is more than painting (`CONTRIBUTING.md` §1): the first sets an
environment variable inside a sandbox, per application — never the global
override, which COSMIC's daemon strips at every login — and the second sets one
for the whole session, for a desktop that does not set it (COSMIC does, in
`start-cosmic`). A Flatpak on the KDE runtime has no qt5ct plugin inside its
sandbox and paints Qt's stock `#EFEFEF` palette without `--flatpak`; with it,
it reads `kdeglobals`, which COSMIC already exposes to every Flatpak.

Applications may stay open: qt5ct and qt6ct watch their config and re-apply it
in place. To undo, put the saved `qt5ct.conf`, `qt6ct.conf` and `kdeglobals`
from `~/.local/state/remainder/` back and delete the two `remainder.conf` files
and `Remainder.colors`; `flatpak override --user --unset-env=QT_QPA_PLATFORMTHEME APP`
undoes `--flatpak` (it records an unset, which lands where an inherited
`qt5ct` lands anyway); deleting `90-remainder-qt.conf` undoes `--platformtheme`.
