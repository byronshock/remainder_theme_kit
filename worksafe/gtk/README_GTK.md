# Remainder — GTK 3

Every GTK 3 application draws with the theme the desktop names: Nemo, GIMP,
Inkscape, Meld, GParted, Emacs, the GTK file chooser, and the menus and dialogs
Firefox and Chromium borrow from GTK. This surface is that theme. It is built
against adw-gtk3, the GTK 3 theme COSMIC itself uses, and walked on Nemo.
Everything here is per user, no sudo, and reversible.

```
sh worksafe/gtk/install.sh        # GTK 3 applications may stay open; they restyle at once
```

Measured on **GTK 3.24.52** (the CachyOS `gtk3` package) with **adw-gtk3 6.5**
(`adw-gtk-theme`) and **Nemo 6.6.4**, on COSMIC, 2026-09-30.

| File | What it does | Generated |
|---|---|---|
| `Remainder/gtk-3.0/gtk.css` | the theme: adw-gtk3's own rules, every colour answered by role, and the kit's rules after them. **Generated and committed** (`CONTRIBUTING.md` §11); `build/gtk.py` fails if it is not what the record and the tables produce. | yes |
| `Remainder/gtk-3.0/remainder-declutter.css` | §0's larger half: every transition and animation the platform writes, switched off at its own selector. It names no colour, and the theme imports it last. **Generated and committed.** | yes |
| `Remainder/gtk-3.0/assets/*.svg` | the check, the dash and the bullet a check box and a radio button draw: square, and symbolic, so GTK paints them in the element's ink and they carry no colour. **Generated.** | yes |
| `Remainder/index.theme` | the theme's name. **Generated.** | yes |
| `install.sh` | copies the theme into `~/.local/share/themes/Remainder`, names it in gsettings (`gtk-theme`) and in `~/.config/gtk-3.0/settings.ini`, and sets `enable-animations` false — saving what each held under `~/.local/state/remainder` first. `--no-declutter` leaves motion alone; `--no-select` copies and names nothing. | no |

The platform the theme answers is `build/gtk_platform.css`: adw-gtk3's
`gtk-3.0/gtk.css` as installed, **recorded** by `build/gtk.py --record` and
never edited by hand. adw-gtk3 is LGPL-2.1, carried here under its §3 as
GPL-3.0-or-later with the rest of `build/`.

## Three things the build decided

**No expression means one role.** adw-gtk3 writes each state as a tint of the
ink over the ground — `mix(fg, bg, 0.9)` for a button at rest, 0.85 hovered,
0.7 pressed; `alpha(currentColor, 0.1)` for a hover — and 1,493 of its
declarations carry a colour, in 412 distinct expressions. The same mix is a
button on a WHITE window and a button on a LIGHT tool bar. So `build/gtk.py`
reads every selector for three things: the surface the element sits on (the
key strip, a panel, a menu, a field, an OSD), what the element is, and what
state it is in. The declaration becomes the kit's ground or ink for that
element in that state on that ground. The theme is the record answered: the
same rules and the same geometry, with every colour a kit value by name. A
selector whose element the table does not know is unclassified and fails the
gate. None is.

**The window knows when it is key.** GTK 3 has no server-side decorations on
COSMIC, so it draws its own title bar and marks a window that is not key
`:backdrop` on every node. The title bar is the key strip: ACCENT carrying
WHITE while the window is key, LIGHT carrying BLACK at 700 when it is not, as on
`worksafe/firefox/` and `worksafe/obsidian/`. This makes GTK 3 the fifth surface
on this desktop that can show key state; COSMIC's own header bars cannot. Nothing
else changes when a window is not key. The platform's 255 selectors for a
window that is not key, outside its strip, are not written, as `worksafe/qt/`
holds its inactive palette equal to its active one. Written, they reached
further than they said: `button.flat:backdrop` names no `:checked`, so it
cleared a toggled button's ACCENT and left its WHITE glyph on the LIGHT tool bar.

**The text renders under the size the floors assume.** GTK 3 renders a font
named without a size at 10 pt, 13.3 px at 96 dpi, and every floor in §0e
assumes about 16 px (§5). The theme sets 16 px on every window, a choice made
(§0c) as on `worksafe/obsidian/` and `worksafe/zettlr/`. Every smaller size the
platform declares is raised where it is declared, and every weight under 400 is
raised to 400, the safe direction (§5). The face is Montserrat, named by the
theme itself rather than left to the desktop's font setting, so the pairs are
measured in the face that renders them.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| the title bar, key window | ACCENT `#763555` | WHITE, 700 — Lc −78.5 |
| the title bar, not key | LIGHT `#BAADB2` | BLACK, 700 — Lc 61.2 |
| a button hovered in the key strip, the window's own three included | BLACK `#10080C` | WHITE |
| menu bar, tool bar, sidebar, status bar, column headers, tab strip, the inactive pane of a split | LIGHT `#BAADB2` | BLACK, 700 — Lc 61.2 |
| the window, the file view, dialogs, fields, popovers, menu rows, the current tab | WHITE `#F1E4E9` | BLACK, 400 — Lc 91.8 |
| menus | a LIGHT frame around WHITE rows | BLACK, 400; accelerators DARK, Lc 79.0 |
| the selected file, row or text; a hovered button or menu row | SELECT `#521436` | WHITE — Lc −87.5 |
| a row hovered on a panel | WHITE | BLACK, 700 |
| a row hovered on a WHITE list | no fill | — |
| buttons | LIGHT on WHITE, WHITE on a panel, in a BLACK outline | BLACK, 700 |
| a toggle that is on, a ticked box, the primary button, focus, a link, a nav indicator, the fills of the disk bar and the zoom slider | ACCENT `#763555` | WHITE on it; a link Lc 75.4 on WHITE |
| fields | WHITE in a BLACK outline, ACCENT when focused | BLACK, 400 |
| troughs, scroll bar thumbs, the disk bar's trough | DARK `#4B4045` | — |
| the caret | CURSOR `#007891` | Lc 60.7 on WHITE |
| tooltips, on-screen displays | BLACK | WHITE — Lc −92.3 |
| a destructive button, an error bar | DESTRUCTIVE `#AF1E2D` | `#FFFFFF`, §3's legend |
| a warning bar | WARNING `#FCD116` | `#000000`, §3's legend |
| error, success, warning **text** | the ANSI normal tier | `#930000` Lc 75.0, `#005800` 75.3, `#525200` 74.1 (yellow's gamut cap) |
| disabled text | DARK on the light grounds, LIGHT on the dark | APCA's 30 for a disabled state: 79.0, 48.4, −54.8 |

No line is drawn between surfaces. Every border between two grounds is
transparent, and the tone changes instead: the view against the sidebar is WHITE
against LIGHT, ΔE 17.1, the separator §5 names. A menu separator is the LIGHT
frame showing between two WHITE rows. The outline of a **control** is different:
it is the control's own glyph, like a check box's box, and it is BLACK, as on
`worksafe/obsidian/` and `worksafe/vscode/`. Every corner is square, bullets,
check boxes and radio buttons included.

## Decisions worth naming

**Weight follows the ground.** BLACK on LIGHT is Lc 61.2, APCA's 16px/700 tier
and not its 16px/400 one. So every LIGHT surface carries 700: the panels, the
column headers, the tab strip, the inactive pane, and every button's label.
Every WHITE surface nested in one goes back to 400. Where adw-gtk3 declares
`normal` on something that sits on a LIGHT panel (`notebook > header tab`),
the declaration is answered `bold`.

**Hover is SELECT on anything you press, and the other tone on a panel's
rows.** A hovered button or menu row is SELECT carrying WHITE, the pair §2
authors. A hovered row in a sidebar is WHITE with its label at 700. A hovered
row in a WHITE list gets no fill. LIGHT there would put BLACK at 400 on it at
Lc 61.2, the shortfall `worksafe/obsidian/` records, and GTK 3's own Adwaita
draws no hover on a list row: the pointer already marks it. A hovered button in
the key strip is BLACK carrying WHITE, since SELECT on ACCENT is ΔE 11.8.

**Opacity is a blend.** adw-gtk3 dims a label, a subtitle and a disabled spinner
by drawing the ink at 55% or 50% over whatever is beneath, and dims a disabled
icon with `-gtk-icon-effect`. Each is opacity 1 here, with the ink named: DARK on
the light grounds.

**The theme paints from names of its own.** GTK resolves a colour name through
every sheet, highest priority first, and the user's `~/.config/gtk-3.0/gtk.css`
outranks any theme (measured). COSMIC's "Apply current theme to GNOME apps"
writes that file, defining libadwaita's names. So the theme's rules read only
`@rm_*` names, which no other sheet defines, and COSMIC's export cannot repaint
them. The names applications read — GTK 3's own `@theme_bg_color` and the rest,
libadwaita's `@window_bg_color` and the rest, and the six Nemo's sheets read —
are defined too, each as a kit value. GNOME's palette names (`@blue_3`…) are
not: no GTK 3 theme owes them, and they name poles.

**Content keeps its colours** (§0a). adw-gtk3 styles a few things that are
pictures of something: an avatar's colour (the person's, generated from their
name), a disk-usage chart's file types, a colour-temperature scale, a colour
swatch, the checkerboard behind a translucent colour, and the scrim over a window
while a dialog is modal (§4). Those rules are carried as the platform wrote them,
and `build/gtk.py` names each one.

**Nemo.** Nemo 6.6 reads the theme's CSS and adds a fallback sheet of its own
unless it finds `nemo` in it. This theme carries adw-gtk3's Nemo rules, so the
fallback is never added, and the theme answers what the fallback would have
set:

- The sidebar's disk-usage bars are a DARK trough and an ACCENT fill on the
  panel, and LIGHT and WHITE on a selected row.
- The rename box is WHITE in a BLACK outline, its selected text SELECT.
- The pane that does not have focus in a split (F3) is LIGHT with its labels
  at 700, the tone change that divides the two panes, since nothing else does
  (issue 002).
- The status that floats over the view when the status bar is off is a LIGHT
  panel.

Nemo 6.6's sidebar has no viewport where adw-gtk3's rules for it expect one, so
the kit states the sidebar list's ground itself.

## The pass

`python3 build/gtk.py --screen DIR` runs the pass (`CONTRIBUTING.md` §10). It
starts Nemo on a virtual X display (`Xvfb :77`) with:

- a session bus of its own and no portals;
- settings kept in memory, so nothing is written to dconf;
- a profile under `DIR` that links to the committed theme and holds a folder of
  sample files;
- `build/gtk_probe.c` compiled and loaded as a GTK module.

GTK 3 on X draws its own title bar only for a compositing window manager that
says it supports `_GTK_FRAME_EXTENTS`. A stand-in claims that and nothing more
(`--qa-wm`), and also advertises `_NET_WM_STATE_FOCUSED`, so the pass sets which
window is key. Nothing composites, so a menu's or window's shadow margin
photographs black. That black is the virtual display, not the theme.

The walk is by keyboard wherever Nemo has a key for a state, since a key reaches
the same place at any size. It covers 18 states:

- the icon view at rest, with a file selected, and renaming it;
- the context menu, the menu bar, and a menu with a row hovered;
- the list and compact views, and the location entry;
- a split window, tabs, search, hidden files, and the view without its status
  bar;
- the window not key;
- Connect to Server, a folder's Properties, and Preferences.

At each state the probe writes every window's computed CSS tree, with the
stylesheet line that set each value, and the display is photographed. At the
end the probe puts every widget through hover, press, checked, selected and
disabled in turn, and the whole window through not-key, recording each.

Measured 2026-09-30, over 1,375 computed trees:

- every painted value is a kit value;
- no text or glyph is under the tier its size and weight need (glyphs at 30, a
  mark's);
- no readable hue in the chrome is off the kit's families.

The only hues outside the home family were the caret's CURSOR in a focused
field, and the spreadsheet icon's green in the file view, which is content and
left out of the test. The pass found thirteen defects before that, each fixed
in the table, among them:

- a WHITE glyph on the tool bar in a window that was not key;
- an unreadable name in the rename box;
- two panes of a split sharing one ground;
- the accelerators of a menu opened from the menu bar taking the menu bar's
  ink, because GTK parents a menu's nodes under the item that opened it;
- fields drawn with no outline.

## What is left over

- **Only Nemo has been walked.** Every declaration adw-gtk3 makes is answered and
  gated, so every GTK 3 application gets the same shape. But GIMP, Inkscape,
  Meld, GParted, Emacs, the file chooser, and the menus Firefox and Chromium take
  from GTK have not been looked at, and an application's own CSS at its own
  priority can put its own colours on top.
- **The desktop pass is still owed.** The walk was on a virtual X display. On
  COSMIC, GTK 3 is a Wayland client that learns focus from the compositor. Key
  state and the title bar should be looked at on the desktop once installed.
- **GTK 4 and libadwaita applications** take no theme, only colour names from
  `~/.config/gtk-4.0/gtk.css`; this surface does not reach them.
- **A GTK 3 Flatpak** sees the theme only with a filesystem override. None is
  installed here, so the installer offers none rather than an untried one.
- **Nemo's desktop** (`nemo-desktop`, Cinnamon's) paints its icon labels from
  literals in Nemo's own sheet at application priority. It does not run on
  COSMIC.
- **The attention dot** a stack switcher shows is a radial gradient from ACCENT
  to nothing, so its edge is a blend. It is the indicator's own edge, and it is
  left as it is.
- **A selected file's icon** is drawn by Nemo with its own highlight over the
  icon, which is content. The label under it is SELECT carrying WHITE.
