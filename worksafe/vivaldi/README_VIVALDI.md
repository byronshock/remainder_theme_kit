# Remainder — Vivaldi

Vivaldi draws its whole interface — tabs, toolbars, panels, the start page,
Settings — as one web page, `window.html`, over a Chromium that shows the web
in `<webview>`s beneath it. A theme reaches that page two ways, and this
surface uses both: a native Vivaldi theme, which is four colours and some
switches in the profile's `Preferences`, and an interface stylesheet, which
Vivaldi loads from a folder once an experiment is switched on. Everything here
is per user, no sudo, and reversible. Vivaldi must be closed while it installs.

```
sh worksafe/vivaldi/install.sh        # quit Vivaldi first
```

Measured on **Vivaldi 8.2.4133.76** (the Arch `vivaldi` package) on COSMIC,
2026-09-29.

| File | What it does | Generated |
|---|---|---|
| `remainder.css` | the interface stylesheet: every colour variable Vivaldi defines — 87 of them, 74 its script derives from the theme and 13 its stylesheet mixes from those — pinned to a kit value in six regions; the chrome's text raised to 14 px at each of the 166 selectors where Vivaldi sets it smaller; and 39 rules for what no variable reaches. Scoped to the Remainder theme. **Generated and committed** (`CONTRIBUTING.md` §11); `build/vivaldi.py` fails if it is not what the tables now produce. | yes |
| `remainder-declutter.css` | §0's larger half, as far as a stylesheet reaches it: motion and blur removed. It carries no colour. **Generated and committed**, and installed unless `--no-declutter`. | yes |
| `theme.json` | the native theme: §2's four as Vivaldi's four, and every switch that would composite something under the chrome — transparency, blur, a background image, the page's own colour on the strip — off. **Generated and committed.** | yes |
| `build/vivaldi_platform.json` | the record: every size Vivaldi's stylesheet sets under 14 px, selector and size, with the `@media` or `@container` condition it holds under. Written by `build/vivaldi.py --record` off the installed build, never by hand. | recorded |
| `settings.json` | the theme selected, for private windows too; the schedule that swaps in Vivaldi's own themes, off; §0's tips, nags and promotions, off; Settings' monochrome icons; the fonts for pages that name none. Merged key by key into each profile's `Preferences`. | no |
| `install.sh` | finds Vivaldi's user-data directories (native, snapshot, Flatpak, or `--user-data-dir`) and every profile in each, and for each profile: adds and selects the theme, copies the two stylesheets into the folder Vivaldi loads, takes the VPN button out of the toolbars, merges the settings, and switches on the experiment in `Local State`. Saves `Preferences` and `Local State` under `~/.local/state/remainder` on the first run. `--qa DIR` builds a QA profile instead. | no |

`settings.json` is JSON with comments, and each key quotes the shipped default
it changes, read off `prefs_definitions.json` in the installed build. Vivaldi
stores an enum as its index, so those are numbers with the name beside them.

## Three things the build decided

**The theme is four colours, and the rest is derived.** A Vivaldi theme names a
background, a foreground, a highlight and an accent, and a window colour; from
the four, Vivaldi's own script derives 43 colour variables for the chrome by
lightening, darkening and mixing, and sets them inline on `#browser`. Given the
kit's four it derives 8 on the ladder, 3 that are §3's legends on its semantic
grounds, and **32 off it**: an address field at `#C9BCC1`, a hover at
`#B3A6AB`, an "intense" foreground at `#000000`, which §3 reserves (`--derive`
lists all 43 and how far each lands from the kit value it is pinned to). So the
native theme alone is near the kit and is not it. It is still installed, for
what no stylesheet reaches — it switches off the transparency, the blur, the
background image and the page-coloured accent — and it is what shows if the
stylesheet does not load.

**The stylesheet is an experiment, and it pins everything.**
vivaldi://experiments › *Allow CSS modifications* makes Vivaldi load every
`.css` file in the folder named at Settings › Appearance › *Custom UI
Modifications* into `window.html`, after its own. The installer switches both
on. Each variable is declared there with `!important`, on `#browser` **and on
every element under it**: Vivaldi re-declares its variables on descendants —
the tab strip, the non-key header, break mode — and a value inherited from
`#browser` loses to one declared at the element, whatever its importance
(`PLATFORM.md` Firefox). A region that changes its ground re-declares what reads
it, one specificity step up, and the checker proves the steps rank the way it
resolves them. The whole stylesheet is scoped to `#browser.theme-id-Remainder`,
so selecting another theme in Settings › Themes undoes it.

**The chrome's text is 14 px: raised, and still under the size the floors
assume.** Vivaldi writes its sizes as literals — 11.5 px in 110 rules, 13 px in
34, 10 to 12 px in 22 more — under a 13 px root, and every contrast floor in §0e
assumes about 16 (§5). The first answer was Vivaldi's own User Interface Zoom at
140%, the least tenth that lifts 11.5 px to 16. It scales everything, the icons,
bars and spacing with the text, and on a desktop already scaled to 175% it read
as a zoom on a zoom; it was looked at and retired the same day (`CONTRIBUTING.md`
§9). So the text alone is raised, as Obsidian's and Zettlr's are, and to **14 px**
(CHOSEN, 2026-09-29), not 16: every size Vivaldi sets under 14 px is recorded off
the installed build and answered at its own selector, and the root takes 14 px
for everything that inherits. Icons, tab heights and spacing stay Vivaldi's.

14 px is a choice made under the floors, and what it costs is measured rather
than hidden. The pairs are gated at the kit's 16 px tiers, as on every other
surface; at 14 px, `build/apca.py` asks Lc 90 of text at 400, and eight of the
400-weight pairs sit under it — WHITE on ACCENT (−78.5) on the key strip, WHITE
on SELECT (−87.5) on a selected row, WHITE on DARK (−81.7) on a private window's
hovered tab, DARK on WHITE (79.0) for secondary text in a field. BLACK on WHITE
(91.8) clears it. The checker prints the list every run. It also costs room: the
weather widget's footer wraps to two lines, and speed dials' titles are cut
sooner.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| the strip that holds the tabs, and the header above it when they are at the side, **key** | ACCENT `#763555` | WHITE, 400 — Lc −78.5 |
| the same strip, **not key** | LIGHT `#BAADB2` | BLACK, 700 — Lc 61.2 |
| the same strip in a **private** window, key | BLACK `#10080C` | WHITE, 400 — Lc −92.3 |
| the current tab | LIGHT on the key strip, WHITE when not key | BLACK, 700 |
| a hovered tab | BLACK on ACCENT, DARK on BLACK, WHITE on LIGHT | WHITE / BLACK |
| toolbars, the panel bar, side panels, the status bar, popups, Settings' list of pages | LIGHT | BLACK, 700 — Lc 61.2 |
| the address and search fields, inputs, a Settings page, a start-page card | WHITE `#F1E4E9` | BLACK, 400 — Lc 91.8; DARK for secondary text, Lc 79.0 |
| the start page | LIGHT, its search field, tiles and widgets WHITE on it | titles on the page BLACK, 700 |
| a hover on the chrome | WHITE; on a field, LIGHT | its text keeps its colour |
| a selected row, the chosen suggestion, Settings' open page | SELECT `#521436` | WHITE — Lc −87.5 |
| buttons | WHITE on the chrome, LIGHT on a field, flat | BLACK, 700 |
| the default action, a ticked box, a chosen radio | ACCENT | WHITE — Lc −78.5 |
| a box or radio button not ticked, a field in a card | its ground | outline BLACK, 1 px: the control's glyph |
| the start page's current group | a line in ACCENT under it | — |
| the caret | CURSOR `#007891` | Lc 60.7 on WHITE |
| closing the window, hovered | DESTRUCTIVE `#AF1E2D` | `#FFFFFF`, §3's legend |
| a success, warning or error ground | §3's three | their legends |

No line is drawn between surfaces: every border between two grounds is
transparent and the tone changes instead — the toolbar against the page is
LIGHT against WHITE, ΔE 17.1, the separator §5 names. Every corner is square,
the pills and circles Vivaldi draws with `--radiusRound` included.

## Decisions worth naming

**The strip that holds the tabs is the titlebar, wherever it is.** That is what
Vivaldi's own *Accent Color on Tab Bar* means, and what `worksafe/firefox/`'s tab
strip is. With the tabs on top the header *is* the strip. With them at the side
the strip is a column, and the header above the page — the window's title and
its buttons — is a titlebar too, so both go ACCENT while the window is key. That
is more ACCENT than a top strip, in the layout you choose for it, and it carries
the same one state. The address field on that column is a field there too: WHITE,
where Vivaldi paints it in the accent's dark shade until it is focused.

**Auto-hide slides the window's own title bar over the page**, out of the header,
and a title bar is part of the strip: ACCENT carrying WHITE when the window is
key, in whichever layout. It was LIGHT there — found on this machine's own
profile, which has auto-hide on, and not in the first pass, which did not.

**A private window is BLACK, where Vivaldi's is violet.** Vivaldi says a window is
private with a violet theme of its own — a hue carrying a state, which §6.8 gives
to no chrome hue — and with an indicator in the address toolbar, which a layout
can hide. So private windows get the kit too, and their key strip is **BLACK**
instead of ACCENT: the state carried by tone, which §6.8 permits. BLACK and not
DARK, because DARK is ΔE 9.2 from ACCENT, under the floor, and a private window
would not read as a different one; BLACK is ΔE 29.0 from it. Not key, a private
window is LIGHT like every other: key state is the one the strip carries first.

**The native theme is installed even though the stylesheet pins it.** Five
things are Vivaldi's to composite and no stylesheet reaches them: the background
image under the chrome, its blur, the chrome's transparency, the accent taken
from each page, and what shows behind a page while it loads. The native theme
turns the first four off and sets the fifth to WHITE.

**The start page is a page of cards.** Vivaldi paints it WHITE, its cards WHITE
or LIGHT, and its weather and currency widgets WHITE at 65% over whatever is
behind them — a blend nobody authored. Here it is laid out as Obsidian's
Settings are: the page LIGHT, and the search field, each speed dial's tile and
each widget a WHITE card on it; a title straight on the page is BLACK at 700.

**Side panels are LIGHT, as the other surfaces' sidebars are**, their labels at
700 and their fields WHITE — the ones Vivaldi leaves transparent to edit a
bookmark in place included.

**Theme previews are pictures, and keep their colours.** Settings › Themes shows
each theme as a small picture painted from that theme's own variables. A pin on
every element would repaint them all in the kit's, and a preview of Vivaldi's red
theme drawn in mauve tells you nothing. So no pin reaches into a preview: it is
information (§0a), like `worksafe/zettlr/`'s pictures of its editor themes.

**Settings' icons are monochrome.** Vivaldi colours each page's icon — orange,
teal, blue, green, every one of them a pole — and ships a monochrome set beside
them; `settings.json` selects it. That is paint, so it is set with
`--no-declutter` too.

**What the declutter switches off**, each with the shipped default beside it in
`settings.json`: interface animation, smooth scrolling, the pale wash over a
non-key window (a blend over every value in it; the strip already says the window
is not key — this one is paint, and set with `--no-declutter` too), tips in the
tab-bar popup, the extensions banner, the suggested tile on the start page and
suggested sites among the top sites, the default-browser check, the "Enable
Search Suggestions" prompt under the address field, the introductions to private
windows, auto-hide and break mode, the quick-commands tip, the donation banner at
the top of Settings, and the VPN button in the toolbar — a promotion, taken out of
every toolbar list that carries it. A toolbar you never changed is not in
`Preferences` at all, so its default is read off the installed build before the
button is taken out of it.

## The ladder

```
python3 build/vivaldi.py --derive       # the roles, the sizes, and what the native theme alone paints
python3 build/vivaldi.py                # every value, pair and adjacency in the committed stylesheet
python3 build/vivaldi.py --write        # regenerate the stylesheet, the declutter and theme.json
python3 build/vivaldi.py --record       # re-record Vivaldi's own sizes off the installed build
python3 build/vivaldi.py --coverage     # the installed build's variables and literals against the record
python3 build/vivaldi.py --screen P     # what a running Vivaldi paints (below); --brief for the defects only
```

There is no ramp to snap. Vivaldi's shades are derived from the theme's four,
not read from a scale, so every one is a role assignment by use: a shade Vivaldi
lightens toward a field is WHITE, a shade it darkens for a hover or a press is
WHITE too — the other tone, which carries the BLACK the control keeps — and a
blend it mixes from them is whatever its use needs. The stylesheet holds **15
values and adds none to the kit**: §2's seven, §3's three and their two legend
values, and the three ANSI normals `build/cosmic.py` solved for signal text,
exactly Obsidian's and Zettlr's. By `CONTRIBUTING.md` §2's pinned method the kit
holds 64 distinct values with `worksafe/vivaldi/` and without it.

**The checker resolves every variable in every region, the way the browser
does.** The platform is recorded in `build/vivaldi.py` with its date: the 74
variables the engine derives, with the values it derived from the kit's four, and
the 13 the stylesheet mixes. The gate overlays the table on the record, resolves
each variable in each region and each region nested in another, and fails on any
that lands off the ladder, on a blend, or on `#FFFFFF` or `#000000` anywhere but a
semantic ground. Nineteen are left to Vivaldi by name, each with its reason: the
image-derived set the tab strip's text depends on staying undeclared, the colours
you give a tab stack, a calendar or a mail flag, and the few that resolve through
ones the table sets. It measures 32 text pairs at the tier each renders at and 19
adjacencies against the ΔE floor, and it checks that each region outranks every
one before it that can match the same element — a key window's and a non-key
window's cannot — since a region that ranked lower would lose to the one it
answers and the browser would resolve it differently from the checker.
`--coverage` re-reads the installed `bundle.js` and `style/common.css` and reports
what was renamed or added since, and every size under 14 px that is not the one
recorded.

**The sizes are answered where Vivaldi sets them, and nowhere else.** Each of
the 166 recorded sizes is raised at its own selector, scoped to the kit's
`#browser` in `:where()`, so it has exactly the specificity of Vivaldi's own rule
and wins by coming later — exactly where Vivaldi's did. An `:is()` scope was
tried first; it added an id's weight, so a plain `button { 13px }` outranked the
welcome page's `.welcome-button { 16px }` and shrank it. And each size keeps the
`@media` or `@container` condition it holds under: taken without it, a size
Vivaldi sets for a narrow welcome card applied at every width.

## Reached, measured

`--screen` asks a running Vivaldi, over its DevTools port, what every visible
element of every interface window computed, composites each text's ground from
its ancestors, and reports every value off the ladder and every text pair under
the tier its computed weight demands, and every text under 14 px at the UI
zoom. It reads every text's size with the interface stylesheet switched off and
on, and names any the kit made smaller. Then it photographs each window and reads the pixels for what no computed style
sees. It reads blends however Chromium writes them — `rgba()`, and `color(srgb
…)`, which is how it reports a `color-mix()`; a probe that read only the first
missed the widgets' 65% wash — and it counts the rules the browser parses out of
the stylesheet.

Run on QA profiles built by `install.sh --qa`, on an invisible display,
2026-09-29 — first at the 140% zoom, then again at 100% with the text at 14 px:

- **the main window**, tabs on top and at the side, and in your own layout — the
  navigation and the address field in the tab column, tab stacks as accordions,
  the status bar as an overlay, auto-hide on — key and not key, and a private
  window, key and not;
- **the start page** with its speed dials, its weather and currency widgets and
  its groups; a web page; four tabs, one hovered; the address field's suggestions
  with the search-suggestions prompt;
- **every side panel** — Bookmarks with its editor, Downloads, History, Notes,
  Translate, Windows and Tabs, Reading List, Sessions — and the workspaces popup;
- **Settings**, in a tab: General, and Themes with its library of previews;
- **first run**: the welcome pages a fresh profile opens.

The pass found about twenty things the checker could not, each now a rule with
its reason beside it: inactive tabs painted with a 30% wash of the accent,
which the table had pinned as a hover; the address field on a side strip in the
accent's dark shade; the side header's title WHITE on LIGHT; the current tab's
title WHITE on LIGHT; buttons and drop-downs filled with gradients; the window
buttons', the panel's edge, the bookmark glyph's and the close button's black
washes; the widgets' 65% wash; titles and labels faded by opacity; boxes WHITE
on a WHITE page; Settings' list at 400 on LIGHT; the theme previews, which the
pins had repainted; and, at 14 px, the welcome page's text shrunk by the two
scoping mistakes above, and the auto-hide title bar LIGHT carrying BLACK. At
100%, every text in every state walked is 14 px or larger and none is smaller
than Vivaldi alone makes it.

**Not walked**: quick commands and the bookmark-added popup — Vivaldi handles its
shortcuts in the browser process, which synthetic key events over DevTools do not
reach — mail, calendar and feeds, which ship switched off; tiling; the reader
view; Settings' other pages; extension popups, which are the extension's. They are
the first things the next pass should look at, on your own screen if not here.

## Residue

Tolerated, never echoed (§4). `PLATFORM.md` is the record:

- **Menus.** The Vivaldi menu and every context menu are Chromium's own, drawn
  from the GTK theme (`extensions.theme.system_theme` 1). With no GTK stylesheet
  under `~/.config` — none on this machine — that is Adwaita: a `#FFFFFF` ground,
  which §3 reserves, `#2E3436` text, `#E6E6E6` separators. A GTK 3 stylesheet
  would reach them, and it would reach every GTK 3 application with them, so it
  belongs to the COSMIC surface and not to this one.
- **Dialogs** that are GTK's: the file picker, print.
- **Web pages** are content (§0a). `elevated/remainder.user.css` reaches them
  through Stylus, from the Chrome Web Store, exactly as on Firefox; importing it
  is yours to choose.
- **Pictures**: favicons, speed dials' logos, the account's avatar, and the web
  panels' icons.
- **Sponsored speed dials.** A new profile's start page carries partner tiles —
  Booking.com, Yelp and others, by region. They are bookmarks, in your
  `Bookmarks` file, and the kit does not edit your bookmarks: delete them from the
  start page or the Bookmarks panel, and Vivaldi remembers not to add them back
  (`vivaldi.bookmarks.deleted_partners`).
- **Real shadows**, under popups, cards and the current tab (§4).
- **The 2 px outline** COSMIC draws around every window. It is the compositor's.

## Installing, and undoing

`install.sh` works in each user-data directory Vivaldi has run in —
`${XDG_CONFIG_HOME:-~/.config}/vivaldi` for the Arch, deb and rpm packages,
`vivaldi-snapshot` beside it for the snapshot,
`~/.var/app/com.vivaldi.Vivaldi/config/vivaldi` for the Flatpak (its convention,
*not verified on a machine*) — and in every profile listed in its `Local State`.
For each profile it copies the two stylesheets into the folder that profile
already names at Settings › Appearance › *Custom UI Modifications*, or into
`remainder-ui/` beside the profiles if it names none; your own stylesheets there
stay, and load beside the kit's. Then it adds the theme, selects it, and merges
the settings; in `Local State` it switches on the experiment.

```
sh worksafe/vivaldi/install.sh                      # every profile: theme and declutter
sh worksafe/vivaldi/install.sh --user-data-dir DIR  # one user-data directory (repeatable)
sh worksafe/vivaldi/install.sh --no-declutter       # paint only
sh worksafe/vivaldi/install.sh --qa DIR             # a QA profile of its own (below)
```

Vivaldi must be closed: it holds `Preferences` and `Local State` in memory and
writes them back when it quits, which would undo all of it. The process is
`vivaldi-bin` in every directory, so the installer asks Chromium's own lock —
`SingletonLock` in the user-data directory — which is live while a browser runs
there.

To undo, select another theme in Settings › Themes: the stylesheet is scoped to
Remainder and paints nothing under any other. The switches the declutter turned
off are each in Settings where Vivaldi keeps them. The installer leaves the UI
zoom alone; the first version of it set 140%, and Settings › Appearance › *User
Interface Zoom* puts that back to 100%. Or, with Vivaldi closed, put the two saved files back from
`~/.local/state/remainder/`.

The QA profile is how the pass above was run, and how to look at a change without
touching your own Vivaldi. The single-instance lock lives in the user-data
directory, so a directory of its own is one flag away and runs beside yours;
`--qa` marks Vivaldi's first-run pages read, so the first window is the browser,
and installs into it:

```
sh worksafe/vivaldi/install.sh --qa ~/.local/state/remainder/vivaldi-qa
Xvfb :77 -screen 0 1600x1000x24 -nolisten tcp &
env -u WAYLAND_DISPLAY DISPLAY=:77 vivaldi --user-data-dir=$HOME/.local/state/remainder/vivaldi-qa/profile \
    --ozone-platform=x11 --remote-debugging-port=9225
python3 build/vivaldi.py --screen 9225
```

`Xvfb` (`xorg-server-xvfb` on Arch) keeps the QA windows off your desktop; menus
are native, so a photograph of the whole display (`import -window root`, from
ImageMagick) is the only way to see one. Reading the photographs needs Pillow.
