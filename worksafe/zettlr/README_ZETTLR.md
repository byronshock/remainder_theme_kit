# Remainder — Zettlr

Zettlr is Electron, like Obsidian, so its windows are web pages and a theme is
a stylesheet. But Zettlr has no theme slot and almost no variables: it offers
one stylesheet of your own, `custom.css` in its data directory, which every
window loads after all of its own. The theme is a stylesheet that `custom.css`
imports, and it answers Zettlr's own CSS rule by rule. Everything here is per
user, no sudo, and reversible. Zettlr must be closed while it installs.

```
sh worksafe/zettlr/install.sh        # quit Zettlr first
```

Measured on **Zettlr 4.8.0** (the CachyOS `zettlr` package, on `electron43`)
on COSMIC, 2026-09-25 and 26.

| File | What it does | Generated |
|---|---|---|
| `remainder.css` | the theme: 707 rules — Zettlr's own 1,449 painting declarations answered at their own selectors, each scoped to the windows that load it, and 90 rules for what no declaration of Zettlr's reaches. **Generated and committed** (`CONTRIBUTING.md` §11); `build/zettlr.py` fails if it is not what the tables now produce. | yes |
| `remainder-declutter.css` | §0's larger half: motion and blur removed. It carries no colour. **Generated and committed**, and imported unless `--no-declutter`. | yes |
| `config.json` | light mode, pinned; the editor following the app; and Zettlr's own frame. Merged key by key into Zettlr's `config.json`. | no |
| `install.sh` | finds Zettlr's data directory (native, Flatpak, or `--data-dir`), copies the two stylesheets in, writes the import block at the top of `custom.css`, merges the settings, and saves both files under `~/.local/state/remainder` on the first run. `--qa DIR` builds a QA profile instead. | no |
| `build/zettlr_platform.css` | the record: Zettlr's own CSS as this theme was built against it, trimmed to what paints. Written by `build/zettlr.py --record`, never by hand. | recorded |

`config.json` is JSON with comments, and each key quotes the shipped default it
changes, read off the config template in the installed build. The installer
strips the comments before it merges: Zettlr reads its own copy as plain JSON.

## Three things the build decided

**There is nothing to set.** Obsidian paints from variables, and a theme there
is mostly a list of values. Zettlr paints from literals: 1,449 declarations that
put a colour or a type on the screen, in 76 stylesheets across fourteen windows,
and the CSS CodeMirror writes at run time for each of Zettlr's five editor
themes. Setting its few variables would reach a fraction of it. So the platform
is **recorded** — read out of `app.asar` and a running window into
`build/zettlr_platform.css` — every recorded declaration is **classified** by
the role it plays, and the theme **mirrors** each one: the same selector, one
class higher, carrying the kit's value for that role. The checker fails on any
declaration no row of the table classifies, so a platform rule cannot slip
through unanswered, and `--coverage` says what an update moved.

**The window does not say when it is key.** Nothing in Zettlr's page changes
with the window's focus, and the minimise, maximise and close buttons are
Electron's, drawn over Zettlr's toolbar in fixed dark symbols no stylesheet
reaches. So Zettlr shows no key state, as COSMIC cannot (`PLATFORM.md`), and the
theme does not pretend to: every window is painted the same, focused or not.

**The UI renders under the size the floors assume.** Zettlr sets its chrome at
10 to 15 px, and every contrast floor in §0e is a function of text at about
16 px (§5). Measured at the 16 px tiers those pairs would pass on paper and not
on the screen. So the chrome's text is set at 16 px, a choice (§0c) with that
reason beside it, as on `worksafe/obsidian/`, and the tiers `build/zettlr.py`
measures are the tiers on screen. Three things it costs, each left visible
rather than squeezed: the About window's six tabs take two rows, and the strip
grows to hold them; a few fixed-width buttons cut their labels short
(*Select fo…*); and the settings' list of pages is cut at its default width.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| menubar, toolbar, tab strip, file manager, sidebar, status bar, popovers, tooltips of the editor | LIGHT `#BAADB2` | BLACK, 700 — Lc 61.2 |
| the note, fields, lists, the settings' list of pages | WHITE `#F1E4E9` | BLACK, 400 — Lc 91.8 |
| the current tab | WHITE | BLACK, 400 — the edge of the note below it |
| menus | a LIGHT frame, WHITE rows | BLACK, 400 |
| the settings page, search results | WHITE cards on a LIGHT page | BLACK, 400; DARK for descriptions, Lc 79.0 |
| the current file, a selected row, the chosen completion or result | SELECT `#521436` | WHITE — Lc −87.5 |
| hover on a panel, a hovered tab | WHITE | BLACK, 700 |
| buttons | LIGHT on the field, WHITE on a panel, BLACK outline; hovered SELECT | BLACK, 700; WHITE on SELECT |
| the primary button, a ticked box, a chosen radio, a switch that is on, focus | ACCENT `#763555` | WHITE on it |
| a toolbar toggle that is on | WHITE | its glyph or label ACCENT — Lc 75.4 |
| links, tags, citation keys | on WHITE | ACCENT, links underlined — Lc 75.4 |
| the editor's selection | LIGHT | text keeps its colour — Lc 61.2 |
| `==marks==`, search matches, the diagnostic open in the lint panel | LIGHT; the current match outlined in ACCENT | set 700 — Lc 61.2 |
| the caret | CURSOR `#007891` | Lc 60.7 on WHITE |
| key caps, tag badges | DARK `#4B4045` | WHITE — Lc −81.7 |
| tooltips on buttons | BLACK `#10080C` | WHITE — Lc −92.3 |
| a caution alert, an error, an error in the log | DESTRUCTIVE `#AF1E2D` | `#FFFFFF`, §3's legend |
| a warning alert, a warning in the log | WARNING `#FCD116` | `#000000`, §3's legend |
| a finished task (LanguageTool's run) | SUCCESS `#006B54` | `#FFFFFF` |
| error, success, warning **text**; a diff's lines | the ANSI normal tier | `#930000` Lc 75.0, `#005800` 75.3, `#525200` 74.1 (yellow's gamut cap) |
| a misspelling, a lint error / warning / note | underlined in DESTRUCTIVE, the ANSI yellow, DARK | marks, tier 30 |

No line is drawn between surfaces: every border between two grounds is
transparent and the tone changes instead — the note against the file manager is
WHITE against LIGHT, ΔE 17.1, the separator §5 names. Two editor panes side by
side are both the field, and meet without a line, as on `worksafe/obsidian/`;
each has its own tab strip and status bar. The outline of a **control** is a
different thing, the control's own glyph, and takes BLACK: fields, buttons,
checkboxes, key caps. Every corner is square.

## Decisions worth naming

**The mirror answers each rule where it stands, and only in its own windows.**
Each override is Zettlr's selector with `:root` in front: it matches the same
elements and outranks Zettlr's rule wherever both apply, whatever order the two
load in, so the theme's rules win exactly where Zettlr's did and keep Zettlr's
order among themselves. But the theme is one stylesheet that all fourteen
windows load, and Zettlr's are per window — an override of a rule only the
Assets Manager has reached the main window's editor, and turned a caution
alert's text BLACK on DESTRUCTIVE. So each override also names the windows
whose bundle loads its rule, `:where(:has(script[src="../assets/index.js"]))`;
`:where()` keeps that out of the specificity, so a scoped override ranks
exactly as an unscoped one.

**Weight follows the ground.** BLACK on LIGHT is Lc 61.2, APCA's 16px/700 tier
and not its 16px/400 one, so every LIGHT panel carries 700 and every WHITE field
nested in one goes back to 400 — as on `worksafe/firefox/` and
`worksafe/obsidian/`, for the same measured reason.

**The editor's selection keeps the text's own colour.** CodeMirror paints the
selection *behind* the text, so its fill is LIGHT, BLACK on it Lc 61.2 — the
platform's shortfall, measured and recorded beside Obsidian's. Chromium hands a
selection's ink down from the element around it, so the WHITE that §2's
selection carries everywhere else reached into the note too, WHITE on LIGHT; the
theme gives the note's text its own colour back (`currentColor`). Chromium's
`getComputedStyle` reports that case wrongly, so it was checked in pixels.

**Alerts: §3's three where their meaning is, and nothing else.** GitHub's five
alerts are a frame in their role with the title on it and the content on a WHITE
inset, as Obsidian's callouts are. *Caution* is DESTRUCTIVE carrying `#FFFFFF`,
*warning* is WARNING carrying `#000000` — the one use §3 permits the two
reserved values — and *note*, *tip* and *important* are furniture: a LIGHT
frame, BLACK at 700. Information has no hue (§3 has three semantics, not four).
In raw mode an alert is only its markers, on the note: a caution's in the ANSI
red, a warning's in the ANSI yellow — at its gamut cap, Lc 74.1 — and the others
BLACK.

**A state Zettlr shows only elsewhere is shown here.** Several of Zettlr's
states are drawn only in dark mode or only on macOS, so on Linux in light mode
they were invisible: a chosen radio button, a shortcut that is not bound, a
pressed toolbar toggle (the log viewer's level filters, the sidebar's button).
Each is drawn here in the kit's value for it, and the rule says why.

**Code and tables draw no grid.** Code keeps the field's ground and is carried
by its face, Hack, and by the colouring `worksafe/vscode/` chose (§0c):
keywords and tags BLACK and bold, comments DARK and italic, literals ACCENT,
names SELECT, a diff's lines in the ANSI green and red. A table's header row is
LIGHT carrying BLACK at 700 over WHITE rows, with no lines between cells.

**Dark mode is pinned off, and painted light anyway.** `config.json` turns dark
mode and its automatic switch off. Turned back on, Zettlr adds its `body.dark`
rules and CodeMirror its dark themes; the theme answers those in the light
palette too. All five editor themes, light and dark, were probed and
photographed: every one computes the same values.

**Zettlr's own frame is the one the theme is built on.** With
`window.nativeAppearance` off, Zettlr draws its menubar and toolbar in the page
and Electron draws the window buttons over them. On, the desktop draws a title
bar and the menus become a native menu bar no stylesheet reaches. `config.json`
pins it off; Zettlr applies it when it restarts.

## The ladder

```
python3 build/zettlr.py --derive       # Zettlr's grey ramp, snapped, and the roles the theme may name
python3 build/zettlr.py                # every value, pair and adjacency in the committed theme
python3 build/zettlr.py --write        # regenerate the theme and the declutter from the record and the tables
python3 build/zettlr.py --coverage     # the installed build's stylesheets against the record
python3 build/zettlr.py --record P     # re-record from the installed build and a Zettlr on DevTools port P
python3 build/zettlr.py --screen P     # what a running Zettlr paints (below)
```

Zettlr's eight greys, `--grey-0` to `--grey-7`, are **snapped** to the nearest
of §2's four by lightness, as `build/firefox.py` snaps Firefox's: a backstop,
so a grey the table does not name lands on the kit's ladder. Everything else is
a role assignment. The theme holds **15 values and adds none to the kit**: §2's
seven, §3's three and their two legend values, and the three ANSI normals
`build/cosmic.py` solved for the terminal, which `worksafe/vscode/` and
`worksafe/obsidian/` already use for signal text.

**The checker gates on the platform, recorded.** Of the 1,449 declarations the
record holds, 1,015 take a kit role and 434 are left to Zettlr on purpose: 427
are content (below), from the sizes of a note's headings to the colours of a
chart, 6 are real shadows and 1 a scrim over content while it loads (§4). The
record is dated and names its build, and `--coverage` re-reads the installed
`app.asar` and reports every declaration added or dropped since. The parts
CodeMirror generates at run time need a running window, so `--record` reads
them: it switches through the five editor themes, light and dark, each in raw
mode too — raw mode mounts CSS of its own, which the first record missed — and
puts every setting back.

## Reached, measured

`--screen` asks a running Zettlr, over its DevTools port, what every visible
element computed — in every window, into every shadow root (Zettlr's icons are
web components) — composites each text's ground from its ancestors, and reports
every value off the ladder and every text pair under the tier its own computed
size and weight demand. Then it **photographs** each window and reads the
pixels, because the computed styles cannot see what Chromium draws itself: a
pixel with a readable hue must belong to a family the kit paints and be no more
chromatic than the kit's own member of it. The first test found a search
field's blue clear button; the second catches Chromium's own red under a
misspelling, which a test of hue alone lets pass for the kit's DESTRUCTIVE. It
also counts the rules the browser parses out of the theme, since a broken
selector list silently ends a stylesheet where it happens.

Run on a QA profile (below), most of it on an invisible display, 2026-09-25 and
26:

- **the main window**: at rest; its six menus, a row hovered; the file, editor
  and tab context menus; the seven toolbar popovers; global search with results
  and its folder autocomplete; the sidebar's four tabs; the file manager in each
  of its three modes, with tags and writing targets; two tabs, one hovered; two
  panes side by side;
- **the note**, top to bottom — frontmatter, headings, tasks, lists, a quote, a
  table, code, a diff, the five alerts, math, a footnote, a comment, a pandoc
  div — with a selection in plain text and in a mark; the footnote, citation and
  linked-note previews; tag and link completion; the find panel with matches;
  the formatting bar; the lint panel with errors and warnings, a diagnostic
  chosen, and its tooltip; typewriter, distraction-free, raw and readability
  modes; all five editor themes, light and dark;
- **every other window**: Preferences' twelve pages, scrolled through; the
  Assets Manager's five tabs; About's six; Statistics' four; the Tags Manager;
  the log viewer; Project Properties' three tabs; Print; the Updater; an error
  window, raised by a broken citation library; Insert Image from Clipboard;
  onboarding, after an update and on a first start (nine pages); the splash
  screen, opened with Zettlr's own window options, since it shows only when
  starting takes over a second.

The pass found about thirty things the checker could not, each now in the theme
with its reason beside it. They were of five kinds. States Zettlr draws only in
dark mode or on macOS (above). Inks left to inheritance under a ground the
mirror moved: a chosen onboarding button BLACK on ACCENT, the lint panel's
chosen row BLACK on SELECT. What the browser draws itself: the search field's
blue glyph, native task checkboxes, the red spelling dots, `<mark>` in its own
yellow in the linked-note preview. Two things meeting where the checker cannot
see them: tag chips DARK on the selected row (ΔE 11.2), muted alert titles DARK
on LIGHT, the sponsors' white logos on LIGHT. And two in the machinery: the
cross-window leak the scoping now prevents, and a theme file cut short at a
selector list split inside a quoted value, which the parse count now guards.

## Residue

Tolerated, never echoed (§4). `PLATFORM.md` is the record:

- **The window buttons**: Electron's own, over the toolbar, in fixed dark
  symbols. No stylesheet reaches them.
- **Key state**: none, as above.
- **Pictures**: Zettlr's logo on the splash screen and in onboarding, the
  sponsors' logos, and the flags in LanguageTool's language-variant menus
  (🇩🇪 German (Germany)), which are emoji drawn by a colour font: `color` cannot
  reach them, and a text presentation needs a font most systems do not have.
- **Content** (§0a): math, diagrams, the statistics' calendar, charts and graph,
  the print preview (the page as it will print), the pictures of the editor
  themes in Preferences, the image viewer's backdrops, colours you give a folder
  or a tag, and readability mode's analysis. All are left as Zettlr paints them.
- **Real shadows**, under popovers and menus (§4).
- **The 2 px outline** COSMIC draws around every window. It is the
  compositor's.
- **The Statistics graph** scrolls by 25 px: Zettlr sizes it to the window and
  adds its controls above. That is Zettlr's layout, not the 16 px text.
- **Your own CSS.** Anything you keep in `custom.css` below the block wins over
  the kit's, which is the point of that file.

## Installing, and undoing

`install.sh` works in each data directory Zettlr has used —
`${XDG_CONFIG_HOME:-~/.config}/Zettlr` for the Arch, deb, rpm and AppImage
builds, `~/.var/app/com.zettlr.Zettlr/config/Zettlr` for the Flatpak — once
Zettlr has run there and written its `config.json`. It copies `remainder.css`
and `remainder-declutter.css` beside `custom.css`, and puts one block at the top
of `custom.css`:

```
/* remainder:begin -- the Remainder theme, put here by worksafe/zettlr/install.sh. ... */
@import url("remainder.css");
@import url("remainder-declutter.css");
/* remainder:end */
```

`@import` has to come before every other rule, so the block goes first (after a
`@charset`, if the file has one), and whatever you keep in `custom.css` stays
below it, untouched. A re-run replaces the block and nothing else. Then it
merges `config.json`'s four settings into Zettlr's, key by key. Both files are
saved under `~/.local/state/remainder/` on the first run.

```
sh worksafe/zettlr/install.sh                   # every data directory, theme and declutter
sh worksafe/zettlr/install.sh --data-dir DIR    # one data directory (repeatable)
sh worksafe/zettlr/install.sh --no-declutter    # paint only
sh worksafe/zettlr/install.sh --qa DIR          # a QA profile of its own (below)
```

Zettlr must be closed: it keeps `config.json` in memory and writes it back when
it quits, which would undo the merge, and it reads `custom.css` as each window
opens. To undo, delete the block from `custom.css` — Zettlr's own editor for it
is Assets Manager › Custom CSS, and Zettlr applies a change there at once — and
set Preferences › Appearance back as you had it; or, with Zettlr closed, put
the two saved files back. The two stylesheets left beside `custom.css` do
nothing once nothing imports them.

The QA profile is how the pass above was run, and how to look at a change
without touching your own Zettlr. Zettlr keeps everything under
`XDG_CONFIG_HOME/Zettlr`, its single-instance lock included, so a profile of its
own is one variable away and runs beside yours. (`--data-dir` would not do:
Zettlr takes the lock before it reads that flag, so a second instance started
with it finds yours and exits — `PLATFORM.md` Zettlr.) `--qa` writes a config
naming the installed version, or Zettlr would take the profile for a first start
and open onboarding, and a note with every kind of block Zettlr renders.

```
sh worksafe/zettlr/install.sh --qa ~/.local/state/remainder/zettlr-qa
XDG_CONFIG_HOME=$HOME/.local/state/remainder/zettlr-qa/config zettlr --remote-debugging-port=9224
python3 build/zettlr.py --screen 9224
```

To keep the QA windows off your desktop, run them on a virtual display
(`xorg-server-xvfb` on Arch); the pass above ran this way:

```
Xvfb :77 -screen 0 2000x1250x24 -nolisten tcp &
env -u WAYLAND_DISPLAY DISPLAY=:77 XDG_CONFIG_HOME=$HOME/.local/state/remainder/zettlr-qa/config zettlr --ozone-platform=x11 --remote-debugging-port=9224
```

`--screen` reads every window on the port; `--screen 9224 preferences` reads
one. Reading the photographs needs Pillow.
