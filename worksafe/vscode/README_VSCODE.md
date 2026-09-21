# Remainder — VS Code

VS Code hands a theme every colour in its workbench — 977 ids on 1.137 — and
nothing else: no weight, no width, no face. Two of those absences decide the
shape of this surface, and both were measured off the installed build rather
than assumed. Everything here is per user, no sudo, and reversible.

```
sh worksafe/vscode/install.sh          # every VS Code found under $HOME; reload the window afterwards
```

Measured on **1.137.0** (Flatpak `com.visualstudio.code`, commit 645f29cc) on
COSMIC, 2026-09-20.

| File | What it does | Generated |
|---|---|---|
| `remainder/package.json` | the extension manifest: one light (`vs`) theme called Remainder | no |
| `remainder/themes/remainder-color-theme.json` | the theme: 965 ids on 30 values, the syntax colouring, and the semantic token colours. **Generated and committed** (`CONTRIBUTING.md` §11); `build/vscode.py` fails if it is not what the generator now produces. | yes |
| `settings.json` | the theme selected, the type (Hack at 16 px), the caret solid and the current-line band off, no indent guides, the terminal's WCAG repainting off, the minimal file icons. Merged key by key. | no |
| `declutter.json` | §0's larger half: the welcome page, tips, walkthroughs, the empty-editor hint, recommendations, release notes, experiments, natural-language settings search, telemetry, feedback prompts, the chat sidebar, motion. Merged unless `--no-declutter`. | no |
| `install.sh` | copies the extension into each install's extensions directory (Code, Code Flatpak, Insiders, VSCodium, VSCodium Flatpak), backs each `settings.json` up under `~/.local/state/remainder`, merges the two files in. VS Code may stay open. | no |

Both settings files are JSON with comments, as VS Code reads them, and each key
quotes the shipped default it changes. `python3 build/vscode.py --settings`
re-reads those defaults off whatever build is installed.

## The two constraints

**The platform sets no weight.** A theme names colours. The workbench renders
its labels at 400 and only its section headers at 700 (`.pane-header
{font-size:11px;font-weight:700}` in `workbench.desktop.main.css`), and the
status bar at 12 px in a 22 px strip. BLACK on LIGHT is Lc 61.3 — the pair §2
authors as the 16px/700 tier, the one the Firefox surface sets 700 on. Here it
cannot be bolded, so LIGHT can carry a header, an icon or a mark, and not a
label a user reads. Every ground that carries read text on this surface is
WHITE, BLACK on it Lc 91.9.

**The editor selection cannot carry its own text.** `editor.selectionForeground`
takes effect only under a high-contrast theme type — the `inline-selected-text`
span is created when `isHighContrast(themeType)` — so in a light theme the
selection is a fill behind text that keeps its colour. §2's SELECT carrying
WHITE is out of reach in the editor, and the pale tint §2 measured and rejected
is what the platform leaves: the best in-gamut tint at CHROME chroma that still
clears the surface floor carries BLACK at Lc 63.4, and LIGHT, an authored value,
carries it at 61.3. The selection is LIGHT, and the shortfall against the body
tier is recorded in the checker's HIGHLIGHTS table rather than hidden. The
**terminal** is different: xterm.js honours `selectionForeground`, so the
terminal's selection is SELECT carrying WHITE, Lc −87.5, as §2 authors it.

## The shape of it

| Surface | Value | Text |
|---|---|---|
| title bar, key window | ACCENT `#773556` | WHITE — Lc −78.5, at the 400 the platform renders |
| title bar, non-key window | WHITE `#EFE5E9` | DARK — Lc 78.9 |
| the command centre | WHITE `#EFE5E9` | BLACK, in a BLACK outline |
| activity bar | LIGHT `#B8AEB2` | BLACK icons; the active item a WHITE well with an ACCENT bar |
| sidebar, lists, menus, inputs, panels, notifications, hovers, the palette | WHITE `#EFE5E9` | BLACK — Lc 91.9 |
| section headers (11px/700) | LIGHT `#B8AEB2` | BLACK — Lc 61.3, the bold tier |
| the tab strip | LIGHT `#B8AEB2` | — the tabs on it are WHITE |
| the active tab | WHITE `#EFE5E9` | BLACK, under a 2 px ACCENT bar |
| inactive tabs | WHITE `#EFE5E9` | DARK — Lc 78.9 |
| selected and hovered rows, menu items, palette rows, suggestions | SELECT `#531537` | WHITE — Lc −87.5 |
| the editor selection | LIGHT `#B8AEB2` | code keeps its colour — Lc 61.3 (above) |
| the terminal selection | SELECT `#531537` | WHITE — Lc −87.5 |
| the caret, the terminal cursor | CURSOR `#007891` | Lc 60.9 on WHITE |
| primary buttons, toggles that are on, focus, links | ACCENT `#773556` | WHITE on the button; links Lc 75.4 on WHITE |
| secondary buttons, badges, key caps, disabled | DARK `#4A4145` | WHITE — Lc −81.7 |
| **the status bar** | BLACK `#0F090C` | WHITE — Lc −92.4 |

The status bar is the rule (§5): 22 px of BLACK carrying WHITE, which is the
rule's own width, and on COSMIC the tiling gap below it is the same value — the
BLACK runs on past the window's edge, ΔE 0.0, as §5 says it should.

No line is drawn between surfaces. Every `*.border` between two grounds is
`#00000000`, which is `transparent` as VS Code spells it, and the tone changes
instead: LIGHT strip against WHITE tab, LIGHT bar against WHITE sidebar, BLACK
rule under it all. Where two WHITE fields meet — the sidebar and the editor, the
editor and the panel — the join is unmarked and the content marks it; both carry
read text at 400, which leaves WHITE as the only ground, and §5 permits no line
thinner than the rule while the platform draws none wider than 1 px. The
**outline of a control** is a different thing from a boundary between surfaces:
it is the control's own glyph, like a checkbox's box, and takes BLACK — inputs,
dropdowns, checkboxes, the command centre's well.

## Five decisions worth naming

**Read text goes on WHITE, and that is a measurement.** The kit's structure is
WHITE fields inside LIGHT panels with bold labels on the panels. This platform
renders no bold, so a LIGHT sidebar would put every file name at Lc 61.3 against
a 400-weight floor of 75 — the exact pair `build/firefox.py` fails a rule for.
So the panels that carry text are WHITE and LIGHT recedes to the strips that
carry icons and headers. The picture that results is a paper-like window with a
LIGHT edge on the left and top and a BLACK rule at the bottom.

**Semantic meaning splits three ways, because §3's values are grounds.**
DESTRUCTIVE on WHITE is Lc 68.2 and WARNING on WHITE is Lc 8.2 — under the
visibility floor. So a *ground* that means something takes the FHWA value with
its legend (`statusBarItem.errorBackground` with `#FFFFFF`,
`inputValidation.warningBackground` with `#000000`: the one use §3 permits the
two reserved values, and the checker fails any other); *text* that means
something takes the ANSI normal slot from `build/cosmic.py` — `#930000` for an
error count, `#005900` for an added file, `#525200` for a file with warnings,
at Lc 75.2 / 75.1 / 74.3, the last at yellow's gamut cap; and a *mark* that
means warning takes the bright yellow slot `#747400` (Lc 60.2), because the
FHWA yellow cannot be seen on the field at all. Information has no hue — §3 has
three semantics, not four — and takes DARK, by tone.

**The syntax colouring is chosen, and says so.** Unlike the ANSI slots there is
no realized convention to honour: keywords are blue in one editor and orange in
the next. And the kit's own arc offers no second hue at its chroma — the three
arc hues at one lightness, solved text-on-WHITE at Lc 75, sit ΔE 4.8, 4.8 and
9.3 apart, and the last of them is ACCENT to ΔE 0.2. So the buffer is coloured
by tone and geometry (§6.8): keywords BLACK and bold; comments DARK and italic
(Lc 78.9, over the body tier); literals in the kit's one hue, ACCENT (Lc 75.4);
types in the same hue bold; functions, members and property names in SELECT
(Lc 85.7); variables, operators and punctuation the base text; and the three
semantic hues exactly where their meaning is — `invalid` and `markup.deleted`
in the ANSI red, `markup.inserted` in the ANSI green, `markup.changed` DARK.

**The diff fills are tints, derived, and under the body tier.** A fill drawn
behind code must let the code's own colour survive, so `build/vscode.py`
solves, for each semantic hue, the lightest in-gamut value between `C_FLOOR`
and a signal's own `C_REF` that still clears `SURFACE_FLOOR` against WHITE,
taking the one that carries BLACK best: `#4FFFD1` (SUCCESS, BLACK on it Lc
90.5), `#FF9E9B` (DESTRUCTIVE, Lc 65.7), `#FFD841` (WARNING, Lc 84.8); inserted
against removed, which abut in a hunk, ΔE 28.2. The red one is under the body
tier by 9.3 and no value at that hue does better: nothing at or under a
signal's chroma is both ΔE 17.1 from WHITE and a body ground, which is the same
wall §2 met with a pale selection. Capping the chroma at CHROME 0.1 was tried
and looked at (principle 12): the green and yellow tints come back darker and
carry BLACK worse (Lc 75.1 and 70.7), and the red is the same value.
Word-level changes inside a line are boxed in the signal itself
(`diffEditor.insertedTextBorder` SUCCESS, `removedTextBorder` DESTRUCTIVE), not
filled.

**The file icons are the minimal set.** The default `vs-seti` draws every file
type in Seti's own colours — blue, yellow, green, orange — which are poles doing
no semantic work in the explorer. §4 keeps a *brand's* art, and Seti's glyphs
are not brands. `vs-minimal` draws one glyph in `icon.foreground`;
`--keep-file-icons` leaves the choice alone.

## The ladders

```
python3 build/vscode.py --derive     # the tints, the orange, the ANSI reuse, the token scheme
python3 build/vscode.py              # every value, pair and adjacency in the committed theme
python3 build/vscode.py --write      # regenerate the theme from the role table
python3 build/vscode.py --coverage   # the installed build's registry against the theme
python3 build/vscode.py --settings   # the settings the kit sets, against the installed build
```

Most of the 965 ids are roles, and §2 names a value for every role the kit has
an opinion about, so the ladder is the assignment itself, as on Windows. The
rest: the sixteen ANSI slots from `build/cosmic.py`, unchanged — the same
buffer, the same content, the same values; the three tints above; `charts.orange`
solved from the platform's own `#EA5C00` the way an ANSI slot is solved from
xterm's (`#843000`, Lc 75.2 — charts are content, §0a, and the other five chart
slots reuse the ANSI normals); and two slots of the COSMIC neutral ladder,
`neutral_7` `#A1979B` for rendered whitespace and rulers (Lc 40.5 on WHITE, a
mark, where LIGHT is 28.5 and under the floor) and `neutral_5` `#746A6E` for the
fifth line of the source-control graph. Four values are new to the kit — the
three tints and the orange; the count went from 62 to 66 by `CONTRIBUTING.md`
§2's method.

**The checker gates on the platform's defaults, recorded.** A theme names what
it names and the registry's light default fills the rest, and on 1.137 that
default is a pole-bearing or a reserved literal for 299 ids — info-blue for
focus, links, badges and buttons; `#FFFFFF` for the editor. An unset id there is
a Microsoft colour showing through. Those ids are recorded in `build/vscode.py`
with their date and source, the gate runs on any machine, and `--coverage`
re-reads the live registry to report what was renamed or added since. On this
build: 977 ids, 965 set, 0 unset with a pole default, 7 unset blends all of
them shadows (§4 permits real shadows), 2 opacities left to the platform, 0
new, 0 renamed.

## Reached, measured

Sampled by region from a `cosmic-screenshot` of the QA profile — the kit
folder open, `build/vscode.py` in the editor, the window key — at 3840×2160
and 150%, 2026-09-20. Regions, never the whole frame (`CONTRIBUTING.md` §10).
The distinct values over 3% of any region are `#0F090C #531537 #773556 #B8AEB2
#EFE5E9`, and `build/poles.py` exits zero on all of them.

| Region | Authored | Modal |
|---|---|---|
| title bar | 94.8% | ACCENT 70.7% — the WHITE command centre is 22.2% |
| activity bar | 97.0% | LIGHT 87.5% — the active item's WHITE well 7.0% |
| the tab strip | 84.8% | WHITE 68.5% (the tabs), LIGHT 15.4% (the strip) |
| the sidebar | 90.7% | WHITE 79.5%, LIGHT 5.8% (headers), SELECT 3.4% (the selected row) |
| the editor | 88.9% | WHITE 87.1%, ACCENT 1.0% (the docstring) |
| the status bar | 84.4% | BLACK 81.8%, WHITE 2.5% (its text) |

The remainder in every region under 100% is glyph antialiasing — the near-WHITE
`#EEE4E8` and `#EDE3E7` in the editor and the tab strip are BLACK text's edges
on WHITE — except one: 6.1% of the status bar's 33 rows is `#C6BDC1`, and it
is the bottom two. It is not the theme's. The same 2 px line surrounds every
window in the frame — a native COSMIC window and a dark-themed VS Code window
alike — so it is the compositor's outline, and it is neutral (chroma 0.011).
Taken as 31 rows the status bar is 88% BLACK.

**The pass found nothing the checker had not**, and the checker found three
things on the way that a table would have passed: three `problems*Icon` ids
left unset whose defaults are a red, a yellow and a blue; a hovered primary
button (SELECT on ACCENT) sitting ΔE 11.7 under the surface floor, which is
§2's own exempt pair and a change over time rather than a boundary, and is now
exempt for that stated reason; and the find widget's input, WHITE on WHITE,
which is edged by its own BLACK outline and not by a tone change.

## Residue

Tolerated, never echoed (§4). `PLATFORM.md` is the record:

- **The 2 px outline** COSMIC draws around every window, `#C6BDC1` on this
  desktop. It is the compositor's, and clear.
- **The workbench face.** It is not a setting: `system-ui, Ubuntu, Droid Sans,
  sans-serif`, which Chromium resolves through the desktop's font setting and
  otherwise through fontconfig's `sans-serif` alias — Noto Sans on this machine.
  The editor and the terminal take Hack; the chrome does not take Montserrat
  from any key VS Code has.
- **Weight.** Section headers are bold and nothing else is; the theme cannot
  change it, and the surface is shaped around it (above).
- **Borders are 1 px** and their width is not themeable; they are made
  transparent, never widened.
- **The onboarding window.** A profile with no settings at all opened
  "Welcome to Visual Studio Code / Sign in to use GitHub Copilot" before the
  workbench, in a window of its own that no theme reaches. With the kit's
  settings in place it did not appear; which key suppresses it —
  `chat.disableAIFeatures` or `workbench.startupEditor` — was not isolated.
- **File icons** take a glyph in `icon.foreground` under `vs-minimal`; any
  other icon theme brings its own colours, which is the user's call.
- **Shadows.** Seven `*.shadow` ids are left unset and paint a blend: real
  shadows, which §4 permits. `--coverage` lists them so the set is checked
  rather than remembered.
- **Two opacities** — `editorUnnecessaryCode.opacity`,
  `minimap.foregroundOpacity` — take a colour whose only read channel is its
  alpha, and are left to the platform by name.

## Installing, and undoing

`install.sh` finds every VS Code under `$HOME` by its `User` directory, copies
`remainder/` into that install's extensions directory as
`byronshock.remainder-<version>` — a copied folder is picked up by the
scanner, which writes its own `extensions.json` beside it — and merges the two
settings files into that install's `settings.json`, after saving the original
under `~/.local/state/remainder/` on the first run. A `settings.json` with
comments in it is not rewritten: Python's `json` writes none back, so the merged
result is written beside the backup instead and the script says where.

```
sh worksafe/vscode/install.sh                    # theme, type, and the declutter
sh worksafe/vscode/install.sh --no-declutter     # paint only
sh worksafe/vscode/install.sh --keep-file-icons  # leave workbench.iconTheme alone
sh worksafe/vscode/install.sh --into DIR         # a user-data-dir of your own -- the QA profile
```

VS Code may stay open: it watches `settings.json`. The extension appears on the
next window reload (Developer: Reload Window) or start, and
`workbench.colorTheme` already selects it. To undo, delete the
`byronshock.remainder-*` folder and put the saved `settings.json` back.

The QA profile is how the pass above was run, and how to look at a change
without touching your own:

```
sh worksafe/vscode/install.sh --into ~/.local/state/remainder/vscode-qa
flatpak run com.visualstudio.code --user-data-dir=$HOME/.local/state/remainder/vscode-qa \
    --extensions-dir=$HOME/.local/state/remainder/vscode-qa/extensions --new-window .
```

Keep it under `$HOME`. A Flatpak VS Code has a private `/tmp`: a profile put
there is created inside the sandbox, empty, and shows a dark, default,
recommendation-nagging window that has nothing of yours in it — which is what
this surface's first two launches showed, and why the fact is in `PLATFORM.md`.
