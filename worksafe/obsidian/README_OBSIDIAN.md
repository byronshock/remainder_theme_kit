# Remainder — Obsidian

Obsidian is Electron, so the whole window is a web page and a theme is a
stylesheet — which makes this surface the Firefox surface's nearest relative,
not VS Code's. A theme here sets weights, sizes, radii and structure as well as
colour, and the window knows when it is key. Themes belong to a vault rather
than to the user, so the installer goes vault by vault. Everything here is per
user, no sudo, and reversible.

```
sh worksafe/obsidian/install.sh        # every vault Obsidian knows; Obsidian may stay open
```

Measured on **Obsidian 1.13.7** (the Arch `obsidian` package, on `electron43`)
on COSMIC, 2026-09-25.

| File | What it does | Generated |
|---|---|---|
| `Remainder/manifest.json` | the theme's manifest: a folder called Remainder, which is the name `cssTheme` selects | no |
| `Remainder/theme.css` | the theme: 348 variables on 15 values, four scopes, and the rules no variable reaches. **Generated and committed** (`CONTRIBUTING.md` §11); `build/obsidian.py` fails if it is not what the role table now produces. | yes |
| `remainder-declutter.css` | §0's larger half, as a CSS snippet: motion and blur removed. It carries no colour and works under any theme. **Generated and committed**, and switched on unless `--no-declutter`. | yes |
| `appearance.json` | the theme selected, light mode, text at 16 px, translucency off. Merged key by key into each vault's `.obsidian/appearance.json`. | no |
| `install.sh` | finds every vault in `obsidian.json` (native, Flatpak, Snap), copies the theme and the snippet into each vault's `.obsidian/`, backs up `appearance.json` under `~/.local/state/remainder`, merges the settings. Asks one question — the Sync plugin — and defaults to no. `--qa DIR` builds a QA profile instead. | no |

`appearance.json` is JSON with comments, and each key quotes the shipped default
it changes, read off `app.js` in the installed build. The installer strips the
comments before it merges: Obsidian reads the vault's copy as plain JSON.

## Three things the build decided

**The window knows when it is key.** Obsidian toggles `is-focused` on `<body>`
with the window's focus, and with the default hidden frame the top 40 px is its
own: the tab strips, the sidebar toggles and the window buttons, which it
already paints from one pair of variables, `--titlebar-background` and its
`-focused` twin. So this is the second surface on this desktop that can show key
state — `PLATFORM.md` records that COSMIC cannot — and it shows it as Firefox
does: ACCENT carrying WHITE when key, LIGHT carrying BLACK at 700 when not.

**Nearly every state is a blend.** Obsidian derives its hover, its selection,
the current file, tags, the text selection and the scrollbars by mixing a colour
with transparent — `color-mix(in oklch, X N%, transparent)`. Of the 302 body
variables that take a colour on 1.13.7, 32 resolve to a blend and 39 more to
`#FFFFFF` or `#000000`, which §3 reserves; 38 sit inside a pole. A blend is not
an authored value and nothing downstream can measure one, so the theme names an
authored value for every one of them that paints, and leaves only the shadows
and the modal scrim, which §4 permits.

**The UI renders under the size the floors assume.** Every contrast floor in
§0e is a function of text at about 16 px (§5), and Obsidian sets its chrome at
12, 13 and 15 px. Measured at the 16 px tiers, those pairs would pass on paper
and not on the screen — a false pass, which is worse than a failing one. So the
theme sets the chrome's text at 16 px, a choice (§0c) with that reason beside
it, and the tiers `build/obsidian.py` measures are the tiers on screen.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| the top strip, key window | ACCENT `#763555` | WHITE, 400 — Lc −78.5 |
| the top strip, non-key window | LIGHT `#BAADB2` | BLACK, 700 — Lc 61.2 |
| the active tab | WHITE `#F1E4E9` | BLACK, 400 — the edge of the note below it |
| a hovered tab or button on the key strip | BLACK `#10080C` | WHITE |
| ribbon, sidebars, status bar, the settings page | LIGHT `#BAADB2` | BLACK, 700 |
| the note, the view header, dialogs, the palette, fields | WHITE `#F1E4E9` | BLACK, 400 — Lc 91.8 |
| menus | a LIGHT frame, WHITE rows | BLACK, 400 |
| search results, settings groups | WHITE cards on the LIGHT panel | BLACK, 400; DARK for descriptions, Lc 79.0 |
| the current file, the selected row, selected text in reading view | SELECT `#521436` | WHITE — Lc −87.5 |
| hover on a panel | WHITE `#F1E4E9` | BLACK, 700 |
| hover on the note, the editor's selection, `==marks==` | LIGHT `#BAADB2` | text keeps its colour — Lc 61.2; a mark is set 700 |
| buttons | LIGHT on the note, WHITE on a panel, BLACK outline | BLACK, 700; hovered SELECT carrying WHITE |
| the primary button, a ticked box, a toggle that is on, focus, links, tags | ACCENT `#763555` | WHITE on it; links and tags Lc 75.4 on WHITE |
| the caret | CURSOR `#007891` | Lc 60.7 on WHITE |
| key caps | DARK `#4B4045` | WHITE — Lc −81.7 |
| notices, tooltips | BLACK `#10080C` | WHITE — Lc −92.3 |
| a destructive button, the close button hovered | DESTRUCTIVE `#AF1E2D` | `#FFFFFF`, §3's legend |
| error, success, warning **text** | the ANSI normal tier | `#930000` Lc 75.0, `#005800` 75.3, `#525200` 74.1 (yellow's gamut cap) |

No line is drawn between surfaces. Every border between two grounds is
transparent and the tone changes instead — the note against a sidebar is WHITE
against LIGHT, ΔE 17.1, the separator §5 names. The outline of a **control** is
a different thing: it is the control's own glyph, like a checkbox's box, and
takes BLACK, as in `worksafe/vscode/` — fields, buttons, toggles, dropdowns.
Every corner is square, bullets, checkboxes and radio buttons included.

## Decisions worth naming

**Weight follows the ground.** BLACK on LIGHT is Lc 61.2, APCA's 16px/700 tier
and not its 16px/400 one, so every LIGHT surface carries 700 and every WHITE one
nested inside it goes back to 400 — as in `worksafe/firefox/`, and for the same
measured reason. This platform lets a theme set weight, so, unlike VS Code, the
sidebars can be LIGHT panels with the file list on them in bold. Montserrat is
installed in its Medium and ExtraBold cuts only, so 400 and 700 render at 500
and 800, the safe direction (`AUTHORITY.md` §5).

**Hover is the other tone.** A hover in Obsidian is a fill under text that keeps
its colour, the way VS Code's webviews use their hover id, so SELECT there would
put BLACK on SELECT at Lc 0.0 — the failure `worksafe/vscode/` recorded. On a
panel the hover is WHITE (BLACK on it at 700, Lc 91.8); on the note it is LIGHT,
BLACK at Lc 61.2, the shortfall recorded beside the editor selection's. Where
the theme can set both sides — the current file, the palette's selected row,
menus, buttons — it is SELECT carrying WHITE, as §2 authors it.

**A custom property is computed where it is declared.** So a region cannot
change a ground by redefining one variable: every variable declared on `body`
that reads it has already taken body's answer. The theme's four scopes — panel,
field, the key strip, and the active tab on it — each re-declare what they change,
and `build/obsidian.py` resolves the way the browser does, per scope, before it
measures anything.

**Callouts: §3's three where their meaning is, and nothing else.** A callout is a
frame in its own colour with its title on the frame and its content on a WHITE
inset. `danger`, `error`, `bug`, `failure` are DESTRUCTIVE carrying `#FFFFFF`;
`warning` is WARNING carrying `#000000`; `success` is SUCCESS carrying `#FFFFFF`
— the one use §3 permits the two reserved values. Every other kind — note, info,
tip, question, example, quote — is furniture and carries its meaning in its
title: a LIGHT frame, BLACK at 700. Information has no hue, as on every surface
(§3 has three semantics, not four).

**Tables and code draw no grid.** A table's header row is LIGHT carrying BLACK at
700 over WHITE rows, with no lines between cells, as `worksafe/firefox/` does
it. Code keeps the field's ground and is carried by its face, Hack, and by the
colouring `worksafe/vscode/` chose (§0c): keywords and tags BLACK and bold,
comments DARK and italic, literals ACCENT, functions SELECT, inserted and deleted
lines in the ANSI green and red.

**The settings are a page and cards.** Obsidian paints the settings page WHITE
and each group of settings a WHITE card on it, so the groups had no edge. The
page is LIGHT here and the cards WHITE on it; the list of pages beside it is
WHITE with its labels at 400. On 1.13.7 Settings open in a window of their own
(`settingsPopoutWindow`), which gets the theme and has its own titlebar, key
state included.

**The Sync plugin is a question, and the answer defaults to no.** Obsidian ships
Sync switched on, and with no account connected it paints a red status icon on
every screen — an error for a service nobody signed up for, which §3 does not
allow and §0 removes. But Sync keeps its connection in Obsidian's own storage
and not in the vault, so an installer cannot tell a vault that syncs from one
that does not, and turning it off in the wrong one stops the syncing. So the
installer lists the vaults where it is on and asks; `--sync-off` and
`--keep-sync` answer in advance.

## The ladder

```
python3 build/obsidian.py --derive     # the ramp, and the roles the theme may name
python3 build/obsidian.py              # every value, pair and adjacency in the committed theme
python3 build/obsidian.py --write      # regenerate the theme and the snippet from the tables
python3 build/obsidian.py --coverage   # the installed build's variables against the theme
python3 build/obsidian.py --screen P   # what a running Obsidian paints (below)
```

Obsidian's twelve `--color-base-*` slots are **snapped** to the nearest of §2's
four by lightness, as `build/firefox.py` snaps Firefox's greys: a backstop under
the role table, so a variable the table does not name lands on the kit's ladder.
Everything else is a role assignment. The theme holds **15 values and adds none
to the kit**: §2's seven, §3's three and their two legend values, and the three
ANSI normals `build/cosmic.py` already solved for the terminal and
`worksafe/vscode/` already uses for signal text.

**The checker gates on the platform, recorded.** The 305 declarations Obsidian's
colour variables resolve through — `body { }` and `.theme-light { }` in
`app.css`, 1.13.7 — are recorded in `build/obsidian.py` with their date, and the
checker overlays the theme on them and resolves every one, per scope, the way
the browser does. On 1.13.7 all 302 land on a kit value, on transparent, or on
content left to the platform on purpose: the canvas card labels, the graph's
node types and the sync avatars, which are information by §3's test, and the
named palette they resolve through. The two blends left are the scrim and the
box shadow. `--coverage` re-reads the installed `obsidian.asar` — the newest one
Obsidian would load, which may be one it downloaded into its own config
directory — and reports what changed since: on this build, nothing.

## Reached, measured

Not a pixel pass: the running app asked what it computed, over its DevTools
port, which is `worksafe/firefox/`'s Marionette probe for this platform. For
"did this surface get LIGHT" the computed value *is* the measurement — exact,
per element, and it names the element that lost instead of averaging a region.
`--screen` walks every visible element of every window, reads its background,
borders, text and SVG strokes as computed, composites the text's ground from
its ancestors, and reports every value off the ladder and every text pair under
the tier its own computed size and weight demand.

Run on a QA vault — Obsidian's own sandbox notes, plus the note `--qa` writes,
which holds every kind of block — on 2026-09-25, in 24 states of the main
window, key and not: the note in live preview and in reading view, scrolled
through; a selection in reading view; the file list expanded and hovered; a
tooltip; the file menu, opened with a real right-click; the command palette with
a row selected; the quick switcher; search; a confirmation dialog with its
button hovered; a notice; the graph. Every painted value was a kit value except
one — the modal scrim, `#DCDCDC` at 0.4, which §4 permits. No text pair was
under its tier. Every text element computed Montserrat or Hack. A hovered dialog
button computed SELECT carrying WHITE.

The pass found seven things the checker could not, each now in the theme with
its reason beside it: disabled buttons faded to 0.4 (a blend; now DARK); the
key cap in the palette's selected row, WHITE on WHITE; dialog buttons at 400 on
LIGHT, Lc 61.2 against the 75 tier; the search counts DARK on LIGHT at 48.4;
file-type badges at 9 px; a hovered property turning LIGHT under an ACCENT tag,
Lc 44.8; and in the Settings window, a title faded to 0.85. The Settings window
was probed once, separately, and **its last two changes are not yet looked at on
the screen**: the title's fade, and the page, which was WHITE — so its WHITE
setting cards had no edge — and is LIGHT now. The checker measures what that
puts on the page, BLACK on LIGHT at 700 and the cards WHITE on it at ΔE 17.1,
and the next pass should look. The graph itself is drawn on a canvas the probe cannot read:
its colours come from the theme's `--graph-*` variables, which the checker
measures.

## Residue

Tolerated, never echoed (§4). `PLATFORM.md` is the record:

- **The modal scrim and the shadows**: real shadows, which §4 permits. The
  checker lets exactly two variables resolve to a blend, and names them.
- **The release notes.** After an update Obsidian opens its release notes in a
  tab, decided by a value in its own local storage, not by a setting a vault or
  a script can reach.
- **The red Sync icon**, in a vault where you answered no, or passed
  `--keep-sync`. It is `--text-error`, the ANSI red, and not a value the theme
  can decide against Obsidian's claim that sync is failing.
- **Content.** Canvas card colours are labels you assigned; the graph's tag and
  attachment nodes, and sync avatars, are information. All are left as Obsidian
  paints them (§0a).
- **The 2 px outline** COSMIC draws around every window. It is the
  compositor's.
- **The native frame.** With Settings › Appearance › Window frame style set to
  native, the compositor paints the titlebar, and on COSMIC every window then
  reads as non-key. The default, the hidden frame, is what this surface is built
  on.
- **Plugins' CSS.** A community plugin's stylesheet paints whatever it likes.
  One that reads Obsidian's variables lands on the kit's values; one that writes
  its own colours keeps them.
- **Tables have no grid**, and a code block no ground (above). That is the kit
  keeping §5 rather than a platform limit, and it has a cost in a wide table.

## Installing, and undoing

`install.sh` reads the vault list from `obsidian.json` in each packaging's
config directory — `${XDG_CONFIG_HOME:-~/.config}/obsidian`,
`~/.var/app/md.obsidian.Obsidian/config/obsidian`,
`~/snap/obsidian/current/.config/obsidian` — and in each vault copies
`Remainder/` into `.obsidian/themes/` and the snippet into `.obsidian/snippets/`,
then merges `appearance.json` after saving the vault's own under
`~/.local/state/remainder/` on the first run. A vault Obsidian lists that is no
longer on disk is skipped and named. A vault kept in a git repository usually
ignores `.obsidian/`, and the installer writes nowhere else.

```
sh worksafe/obsidian/install.sh                   # every vault, theme and declutter
sh worksafe/obsidian/install.sh --vault DIR       # one vault (repeatable)
sh worksafe/obsidian/install.sh --no-declutter    # paint only
sh worksafe/obsidian/install.sh --sync-off        # and turn the Sync plugin off where it is on
sh worksafe/obsidian/install.sh --qa DIR          # a QA profile of its own (below)
```

Obsidian may stay open: it watches `appearance.json` and the theme's own file
and applies both as they change. To undo, choose another theme in Settings ›
Appearance and switch the snippet off there — or put the saved
`appearance.json` back — and delete `.obsidian/themes/Remainder`. The Sync
plugin, if the installer turned it off, is under Settings › Core plugins, and
its original `core-plugins.json` is saved beside the rest.

The QA profile is how the pass above was run, and how to look at a change
without touching a vault of yours. `XDG_CONFIG_HOME` gives Obsidian a profile of
its own — its vault list, its window state and its storage — and `--qa` writes
that profile's `obsidian.json` with the QA vault in it, because Obsidian opens
only a vault its list names: a path on its command line, or an
`obsidian://open?path=` link to a vault it does not list, opens the vault picker
instead (`PLATFORM.md` Obsidian).

```
sh worksafe/obsidian/install.sh --qa ~/.local/state/remainder/obsidian-qa
XDG_CONFIG_HOME=$HOME/.local/state/remainder/obsidian-qa/config obsidian --remote-debugging-port=9223
python3 build/obsidian.py --screen 9223
```

`--screen` reads every window on the port, the Settings window included.
