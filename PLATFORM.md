# Platform findings

Theme-independent research: what a per-user install can actually reach on each
platform, what it cannot, and which knob does it. **Nothing here is about
color.** This file is kept parallel in the De Stijl kit and in Remainder,
because rediscovering a registry key is expensive and neither kit's palette
changes the answer.

When you change something here, change it in both. When the two disagree,
one of them is out of date — this file records facts about platforms, and
platforms do not have opinions about either kit.

Seeded from `DESTIJL_STYLE.md` §7 at the fork, 2026-09-19. The entries below
are the headings; fill each from the parent kit's §7 as you touch that
surface, and keep the theme-specific color claims out.

## Windows 11 (24H2)

Standard theme engine in light mode, not a contrast theme — forced colors
strip affordances users need and read as an accessibility mode.

- Transparency (mica, acrylic) off system-wide; animation off; scrollbars
  always shown.
- Accent on title bars and borders; `AccentColorInactive` under
  `HKCU\Software\Microsoft\Windows\DWM` for the inactive titlebar.
- `Hilight` / `HotTrackingColor` in the `.theme` colors table — legacy Win32
  honours them.
- Text cursor indicator: Accessibility → Text cursor → indicator on.
- Edge frame: `edge://settings/appearance` custom theme color. A Preferences
  entry, not a registry key, so it is a README step and cannot be scripted.
- Taskbar left; widgets, Copilot, task view off; Start recommendations and
  search highlights off.
- Window corners: `DWMWA_WINDOW_CORNER_PREFERENCE` via
  `DwmSetWindowAttribute`, settable per window from any process — so square
  corners are reachable per-user.
- `declutter.reg` (HKCU): tips, welcome experience, Settings suggestions,
  lock-screen facts, notification defaults.
- **Colour arrives in five notations and only one of them is hex**, which is the
  fact an installer and its checker both have to carry. A bare decimal triple
  (`Background=15 9 12`) in a `.theme`; the same value quoted
  (`"Background"="15 9 12"`) in a `.reg`; an **ABGR** `DWORD` with the alpha in the
  high byte for `AccentColor` and `AccentColorInactive` under DWM and for
  `Explorer\Accent` — Microsoft's own default accent `#0078D7` is stored
  `dword:00d77800`; an **AARRGGBB** value for `ColorizationColor` — in the
  `.theme`'s `[VisualStyles]` and in the DWM `ColorizationColor` /
  `ColorizationAfterglow` DWORDs alike, the order the documented default
  `0xC40078D7` shows and the order the parent kit's `theme.reg` has always
  written; and a REG_BINARY run of RGBA quads in `AccentPalette`. So two DWORDs
  under the one DWM key carry two byte orders, and flags, masks and delays share
  the `DWORD` and REG_BINARY forms besides — nothing can tell a colour from a flag,
  or one order from the other, by looking at the value; only by knowing the key.
  This kit wrote its `Colorization*` pair ABGR until 2026-09-21 and its checker
  passed them, having read the notation the same wrong way; the parent kit's
  comment in `theme.reg` is what caught it.

  *(`#0078D7` is Microsoft's own default accent and appears here as the worked
  example of a byte order, which is a platform fact. No value either kit authors is
  in this file, and none should be.)*
- **`AccentPalette` is eight RGBA quads**, of which indices 0–6 are a light-to-dark
  ramp and index 7 is a separate emphasis slot unrelated to it. Index 3 is the
  accent Settings displays and the value `AccentColor` mirrors; the darker indices
  are what the menu and Start surfaces read. *Inferred from Microsoft's shipped
  default palette, where `#0078D7` sits at index 3 and index 7 is an orange; not
  confirmed on a machine.*
- **Applying a `.theme` rewrites the DWM accent keys**, so a `.reg` that sets them
  has to be merged *after* the theme and not before. *Inferred from the format —
  `[VisualStyles] ColorizationColor` is part of what a theme carries — and not
  confirmed on a machine.*
- **A `.reg` or `.theme` without a byte-order mark is read as ANSI.** Non-ASCII in
  a comment imports as mojibake and non-ASCII in a value is corrupted, so a file
  meant to be double-clicked is safest written ASCII, CRLF, no BOM.
- **`reg import` restores values but does not remove them.** It writes back what an
  export saved and has no way to express "this key did not exist", so a backup taken
  with `reg export` does not fully undo an install that created keys from nothing.

**Cannot reach per-user:** DWM draws a 1 px frame and nothing per-user
thickens it. Segoe UI Variable in system chrome (needs HKLM
`FontSubstitutes`). Control corner radii. Terminal and Chrome tab shapes.

**Not verified on a machine.** Everything in this section is inherited research;
neither kit has had a Windows 11 machine to put it on. The entries marked
*inferred* above are the weakest of it, and `UserPreferencesMask`'s
`90 12 03 80 10 00 00 00` — the conventional "adjust for best performance" mask —
is weaker still: it is convention rather than documentation. Confirming any of it
is a correction to this file, in both kits.

## COSMIC (Pop!_OS)

The surface where a theme gets nearest to exact: radius 0, explicit surface
values, and tiling gaps are all settable per-user with no sudo.

- Light/dark and auto-switch are theme inputs.
- Tiling gaps: COSMIC adds its outer gap to the inner one at a screen edge,
  so set outer 0 and inner to the wanted gap for one consistent gap.
- `active_hint` draws a band of `window_hint` around the **focused window
  only**, `active_hint` dp wide, **in the gap from the window's edge outward**:
  the window does not move or shrink, and at `active_hint` = the inner gap the
  band fills the gap and touches the neighbours. Painted at the exact value, no
  blending. Measured 2026-09-21 at 150%: 8 dp → 12 px, 22 dp → 33 px, 67,912 of
  67,920 pixels the exact value; 11 dp → 16.5, and the half pixel lands on one
  side or the other — 16 px on two sides, 17 on the other two, still unblended;
  1 dp → 1 px on the sides and 2 on the top and bottom; 2 → 3; 3 → 5; 4 → 6,
  and a multiple of 4 dp is whole at every quarter-step scale. Exact at every
  width: no blended pixel at 1, 2, 3, 4, 8, 11 or 22 dp.
  **The band's outer corners are rounded to a radius equal to its thickness**
  (profile measured: 12 px band, 12 px radius; 16 px band, 16 px radius), and
  the theme's `corner_radii` — all 0 here — do not reach it; the inner corners
  are square and the window itself is not clipped. A hint therefore makes the
  gap carry focus to exactly the extent of its width, which is the trade a
  theme makes with it.
- Background is per output, not per workspace.
- Toolkit config (`com.system76.CosmicTk`): fonts, density, header size.
- `cosmic-randr` reports output size and scale, so an installer can compute
  per-output geometry.
- `cosmic-settings appearance export|import` prints two ERRORs on **stderr** —
  `1:1: Expected identifier` and `failed to get key 'frosted_maximized_apps'`,
  both at `theme_manager.rs:62` — and exits 0 regardless. They are about
  cosmic-settings' own config state, not the file being imported: an *export*,
  which reads no theme file at all, prints the identical pair. Do not suppress
  them in an installer; a real import failure would go with them.

- **The compositor draws a 2 px outline around every window** at 150% (one
  logical pixel), native and foreign alike, in a value derived from the theme
  and not settable by a window's own theme. Measured 2026-09-20 on a COSMIC
  Files window and on two Electron windows in the same frame: the same value
  on all three. A pixel pass over a window's edge finds it; it is the
  compositor's, not the window's.

**Cannot reach:** this libcosmic paints header bars with the window
background, so a header bar cannot differ from the field and every window
reads as non-key. Toggles, nav indicators, check marks and focus rings all
follow the single accent — a theme cannot split focus from accent.
Client-side decorations (Electron, GTK) keep their own chrome. Some surfaces
are *derived* from theme inputs and no theme value prevents it; measure the
derivation and record it.

## Firefox

Draws its own chrome and hands it to a per-profile stylesheet — so it is the
one surface that can show key/non-key state where the platform will not.
Measured on 155.0.1 (deb), 2026-09-19, except where noted.

- `user.js` for prefs; `chrome/userChrome.css` and `userContent.css` for
  chrome and content. Requires `toolkit.legacyUserProfileCustomizations.
  stylesheets`.
- Reachable: tab strip, toolbars, address and search fields, menus, panels,
  sidebar, new tab / home / blank pages, every radius.
- Prefs: density, scrollbars, reduced motion, fonts, and the declutter —
  sponsored tiles, suggestions, trending, promotions, "what's new".
- uBlock Origin can be installed into the profile by script.
- **A user sheet outranks the layers.** Firefox defines its own chrome tokens
  inside `@layer` blocks, where layer order normally decides. It does not bite:
  `userChrome.css` loads in the *user* origin, and a user-origin `!important`
  outranks every author-origin declaration, layered or not.
- **The chrome resolves through a design-token system**, not through a handful
  of theme colors: a primitive ramp plus roughly 280 named color tokens above
  it. **The names are renamed most releases**, and a renamed token is how a
  strip silently falls back to a built-in color. Read the current ones off the
  installed build rather than from memory:

  ```
  unzip -p /usr/lib/firefox/omni.ja \
    chrome/toolkit/skin/classic/global/design-system/tokens-shared.css
  unzip -p /usr/lib/firefox/browser/omni.ja \
    chrome/browser/skin/classic/browser/urlbar/urlbar.tokens.css
  ```

  `python3` cannot open these: Firefox ships `omni.ja` optimised, with data
  ahead of the central directory, which `zipfile` rejects as a bad magic number
  and `unzip` reads with a warning.
- **Some surfaces are derived by alpha-mixing** — `color-mix(in srgb,
  currentColor N%, transparent)` and a `--color-*-alpha-*` family. Anything
  painted that way is a blend of two things rather than a value a theme set.
- **A component token cannot be set from `:root`.** Each `moz-*` web component
  ships its own `*.tokens.css` declaring its tokens on `:root, :host`, and the
  `:host` half lands on the custom element. A value inherited from `:root` loses
  to a value declared at the element, whatever origin the inherited one came
  from — importance does not cross inheritance, so even a user-origin
  `!important` on `:root` loses. Set such a token on the element itself
  (`moz-page-nav { --page-nav-...: ... }`). Only components with a real shadow
  root are affected; `--tab-*` and `--urlbar-*` are declared the same way and
  are read in the light DOM, where `:root` reaches them.

  **The same rule bites outside shadow DOM, on ordinary inherited properties.**
  Firefox declares `font-family` on its popups and `font-weight` on its menu
  items, so a `font-family` or `font-weight` set on `:root` — with `!important`,
  from the user origin — never reaches them. Importance does not cross
  inheritance. Anything inherited that a theme cares about has to be declared on
  the element that will render it.
- **To reach the chrome from a script, use Marionette.** `--marionette` opens
  Firefox's own automation socket (port 2828, length-prefixed JSON); its CHROME
  context runs privileged JS against `browser.xhtml`, which is the only way to
  open a XUL popup where the compositor will not let a script synthesise a
  click. Firefox 155 gates that context behind the extra flag
  `-remote-allow-system-access`. It works headless.
- **A headless chrome screenshot does not composite a popup**, even one whose
  `state` reads `open`, because XUL panels are separate widgets.
  `getComputedStyle` reads back what the cascade produced and does not care, so
  it is the better instrument for "what did this surface actually get".
- **A brand-new profile shows the terms notice**, which dims the entire window —
  chrome included — at 75% black until it is answered. A first screenshot of a
  fresh profile therefore measures every surface at a quarter of its value.
  `termsofuse.bypassNotification` gets past it; the pref exists for a test
  profile and not for a user's.
- `browser.nova.enabled` (default **false** in 155) is a second, parallel set of
  token values behind a pref, and it **renumbers the primitive grey ramp**: the
  same slot name carries a different lightness under it. A theme derived against
  one numbering is not derived against the other.
- `browser.theme.native-theme` is 155's "use system colors" switch. With it on,
  the `-moz-native-theme` media query matches and the chrome takes GTK's colors
  for everything a theme has not named.
- **Prefs gone by 155**, and a pref for a feature that is gone looks like it is
  doing something: `extensions.pocket.enabled`, `browser.theme.toolbar-theme`
  and its `content-theme` pair, `browser.messaging-system.whatsNewPanel.enabled`,
  `browser.tabs.firefox-view`, `browser.promo.focus.enabled`.
- **On by default in 155**, and new since the parent kit's list:
  `browser.ml.chat.enabled` (a chatbot in the sidebar),
  `browser.tabs.groups.smart.enabled`, `browser.urlbar.suggest.weather`,
  `browser.preferences.moreFromMozilla`.
- **The profile root moves with the packaging**: `~/.mozilla/firefox` (deb),
  `~/snap/firefox/common/.mozilla/firefox`,
  `~/.var/app/org.mozilla.firefox/.mozilla/firefox`. Inside it, `installs.ini`
  names the profile *this install* opens, which is not always the one
  `profiles.ini` marks `Default=1`.
- **The running process is named `firefox-bin`**, not `firefox`: on the deb
  build the main process's `argv[0]` is `firefox` while its `comm` is
  `firefox-bin`, so `pgrep -x firefox` reports nothing while Firefox is running.
  An installer that checks only that name will write into a live profile, and
  Firefox will overwrite `prefs.js` from memory when it exits.

**Cannot reach:** a running window's dock icon is the one the window
supplies. GTK dialogs (file picker) are GTK's.

## VS Code

Measured on 1.137.0 (Flatpak `com.visualstudio.code`, commit 645f29cc), 2026-09-20,
on COSMIC.

- A colour theme is an extension: a folder holding a `package.json` with
  `contributes.themes` and the theme JSON it points at. **A folder copied into
  the extensions directory is picked up** — the scanner lists it and writes its
  own `extensions.json` beside it — so no `.vsix` and no CLI is needed to
  install one. It is seen on the next window reload or start.
- Where each packaging keeps things (per user, no elevation):
  `~/.vscode/extensions` and `~/.config/Code/User/settings.json` (deb, rpm, tar);
  `~/.var/app/com.visualstudio.code/data/vscode/extensions` and
  `~/.var/app/com.visualstudio.code/config/Code/User/settings.json` (Flatpak);
  `~/.vscode-insiders` and `~/.config/Code - Insiders` (Insiders);
  `~/.vscode-oss` and `~/.config/VSCodium` (VSCodium);
  `~/.var/app/com.vscodium.codium/data/codium` and `…/config/VSCodium` (VSCodium
  Flatpak).
- **`settings.json` is JSON with comments and trailing commas**, and VS Code
  watches it: an edit on disk is applied to a running instance without a
  restart. Theme files are read the same way.
- **The whole colour vocabulary is readable off the installed build.** In
  `resources/app/out/vs/workbench/workbench.desktop.main.js` the minified
  `registerColor` is `se("id",{light:…,dark:…,hcDark:…,hcLight:…},…)`, a
  variable bound to the call (`rn=se("editor.background",…)`) is how another
  id's default refers to it, the terminal slots are a table
  (`"terminal.ansiRed":{index:1,defaults:{light:…}}`), and the git extension
  contributes its own under `contributes.colors`. 977 ids on 1.137. A default
  that names another id resolves through the *theme's* value of that id.
  A default of `null` paints nothing.
- **A theme names what it names and the registry's light default fills the
  rest.** An unset id is not "unstyled"; it is the platform's colour.
- **`editor.selectionForeground` is honoured only under a high-contrast theme
  type**: the `inline-selected-text` span is created when `isHighContrast(
  themeType)`. In a `vs` (light) theme the editor selection is a fill behind
  text that keeps its own colour. The same is true of `selection.background`
  for text outside the editor. The **terminal** is different: xterm.js takes
  `terminal.selectionForeground` whatever the theme type.
- **A theme sets no font weight.** The workbench renders labels at 400; only
  `.pane-header` (11px) and a few badges render bold, and the status bar is
  12px in a 22px strip whose height is not a setting. What a theme can decide
  is colour.
- **The workbench face is not a setting.** It is `system-ui, Ubuntu, Droid Sans,
  sans-serif` on Linux, which Chromium resolves through the desktop's font
  setting and otherwise through fontconfig's `sans-serif` alias — on this
  machine Noto Sans. `editor.fontFamily`, `terminal.integrated.fontFamily` and
  a few view-specific keys are settings; the chrome's face is reached only by
  fontconfig or the desktop.
- **`terminal.integrated.minimumContrastRatio` defaults to 4.5** — a WCAG
  luminance ratio the terminal enforces by *repainting* any slot that falls
  under it against the background. A terminal scheme arrives on screen altered
  unless it is set to 1.
- Borders are 1 px and their width is not themeable; every `*.border` id can
  be made transparent. Corner radii are not themeable.
- Chromium reorders argv into switches then operands, so `--user-data-dir DIR`
  shows in a process list as `--user-data-dir … DIR`; VS Code reads it
  correctly either way. `window.activeBorder` and `window.inactiveBorder` are
  never drawn on Linux (`updateWindowBorder` returns early there); the window's
  edge is the compositor's. **A Flatpak VS Code has a private `/tmp`**: a
  `--user-data-dir` under `/tmp` is created inside the sandbox, empty, and
  nothing put there from outside is seen. A test profile goes under `$HOME`.
- **A profile with no settings opens an onboarding window before the
  workbench** — `welcomeOnboarding`, "Welcome to Visual Studio Code / Sign in to
  use GitHub Copilot / Continue without Signing In", in a window of its own that
  no theme reaches. With `chat.disableAIFeatures` and `workbench.startupEditor`
  set it did not appear; which of the two suppresses it was not isolated.
- Settings that remove what the platform puts in the way, all present on 1.137
  with their defaults readable off the bundle: `workbench.startupEditor`,
  `workbench.tips.enabled`, `workbench.welcomePage.walkthroughs.openOnInstall`,
  `workbench.editor.empty.hint`, `extensions.ignoreRecommendations`,
  `update.showReleaseNotes`, `workbench.enableExperiments`,
  `workbench.settings.enableNaturalLanguageSearch`, `telemetry.telemetryLevel`,
  `telemetry.feedback.enabled`, `chat.disableAIFeatures`,
  `workbench.reduceMotion`. Editor options are registered by bare name
  (`"smoothScrolling"`, not `"editor.smoothScrolling"`), so a search of the
  bundle for the full id misses them.
- `window.titleBarStyle` defaults to `custom` on Linux, so the title bar is
  the theme's to paint by key state; with `native` the compositor paints it.

- **Extension webviews receive the theme as `--vscode-*` custom properties**
  and map them onto their own tokens: the Qwen Code companion 0.24.2's webview
  maps `--accent` to `list.hoverBackground`, `--muted` to
  `sideBarSectionHeader.background`, `--secondary` to `input.background`,
  `--card` to `editorWidget.background`, `--background` to
  `sideBar.background`, and its utility classes set the background alone, so
  the text inherits `foreground`. An id whose platform default is a faint tint
  is therefore read by webviews as a tint under the base foreground, whatever
  its own foreground id says. Measured 2026-09-21: BLACK on a SELECT-valued
  `list.hoverBackground` in that panel.

**Cannot reach:** the workbench face (above); font weight; border widths and
radii; the onboarding window; the file icons' own colours, other than by
choosing an icon theme (`vs-minimal` is monochrome and takes `icon.foreground`).

## Qt (qt5ct, qt6ct, and the KDE colour scheme)

Measured on qt5ct 1.5 with Qt 5.15.13 and qt6ct 0.9 with Qt 6.4.2 (the Pop!_OS
24.04 packages), on COSMIC, 2026-09-21, and read off the sources of those
versions — Debian's, and qtbase `v5.15.13-lts-lgpl` and `v6.4.2` — and off
libcosmic and cosmic-settings-daemon at master.

- A Qt application takes its colours from a **palette** — `QPalette`, 21 colour
  roles on Qt 5.12 to 6.5, 22 from 6.6 (`Accent`), in three groups: active,
  inactive, disabled — and a **style** paints every control from it. On Linux
  the palette arrives through a platform theme plugin named by
  `QT_QPA_PLATFORMTHEME`, and the two a user can configure without elevation
  are qt5ct and qt6ct. qt6ct's plugin registers under both `qt6ct` and
  `qt5ct`, so one variable serves both toolkits, which `start-cosmic` relies
  on: it prefers `cosmic` (CuteCosmic, `libcutecosmictheme.so`, not installed
  here) and otherwise sets `QT_QPA_PLATFORMTHEME=qt5ct` when either plugin is
  on disk. Ubuntu's X session does the same in `/etc/X11/Xsession.d/99qt5ct`
  unless the desktop is KDE.
- Config: `~/.config/qt5ct/qt5ct.conf` and `~/.config/qt6ct/qt6ct.conf` —
  `[Appearance] style`, `custom_palette`, `color_scheme_path`, `icon_theme`,
  `standard_dialogs`; `[Fonts] general`, `fixed`; `[Interface] gui_effects` and
  the rest. Schemes live in `~/.config/qt{5,6}ct/colors/*.conf`, with samples in
  `/usr/share/qt{5,6}ct/colors/`. Both plugins watch their config file and
  re-apply it to running applications. `style` defaults to Fusion when absent.
  `custom_palette=true` is required, or the scheme path is read and ignored.
- **The scheme file** is `[ColorScheme]` with `active_colors`,
  `disabled_colors` and `inactive_colors`, each a comma-separated list of
  `#AARRGGBB` in `QPalette::ColorRole` order: WindowText, Button, Light,
  Midlight, Dark, Mid, Text, BrightText, ButtonText, Base, Window, Shadow,
  Highlight, HighlightedText, Link, LinkVisited, AlternateBase, NoRole,
  ToolTipBase, ToolTipText, PlaceholderText, and Accent. **qt5ct 1.5 accepts
  exactly `NColorRoles` entries — 21 — and silently ignores a list of any
  other length**, leaving the style's default palette in place. qt6ct 0.9
  accepts `>= NColorRoles` and, built against Qt 6.6 or later, pads a
  21-entry list with Highlight as Accent, so one 22-entry file serves every
  Qt 6. The alpha byte is honoured: a translucent entry blends.
- **Fonts** are `QFont::toString()` strings. The 10-field Qt 5 form —
  `family,pointsize,-1,stylehint,weight,style,underline,strikeout,fixedpitch,rawmode`
  — is read by Qt 6 too, which converts the legacy weight scale (50 is
  Normal) to OpenType (400). The 16-field Qt 6 form is not read by Qt 5.
- `gui_effects` is a list; the empty list — which qt5ct's own dialog writes
  as `@Invalid()` — turns every menu, combo box, tool tip and tool box
  animation and fade off.
- **Fusion derives its chrome from the palette rather than painting it**, in
  Qt's 16-bit HSV arithmetic (`QColor::lighter` and `darker` with integer
  factors, float32 conversions, and a colour that stays in whichever spec it
  was last set in — `lighter()` on an HSV colour never touches RGB). Every
  outline is Window darkened by 40%. A button face is Button lightened by
  `100 + max(1, (180 − grey) / 6)` percent with its saturation cut to three
  quarters, darkened 4%, and drawn as a gradient from 124% to 102% of that;
  a hovered face skips the 4%, a pressed face is darkened 10%, and a
  dialog's default button first mixes a tenth of Highlight.darker(125)
  .lighter(130) into the face. The tab pane and the selected tab are the
  button colour lightened 4% (and 4% again at the top); unselected tabs are
  it darkened 8% then 16%; table headers run 104% to 98%; the scrollbar
  groove is 93–95%, its slider 108% to 100%; a menu is Base lightened 8%
  inside Window darkened 60%; tool bars and menu bars run Window lightened
  4% down to Window; a check box is Base darkened 15% down to Base with the
  mark in Text darkened 20%; the focus frame and the default button's
  outline are Highlight darkened 25%, value capped at 160 through HSL; a
  progress fill is Highlight lightened 20% down to Highlight, outlined in the
  darker of the outline and Highlight darkened 40%. Every constant is
  identical in 5.15.13 and 6.4.2, and the rendered bytes were confirmed on
  screen for both. What the palette does not reach at all is painted as a
  blend: white at 30/255 inside every control, white 90 and black 60 on grips
  and tool bar edges, black 18 inside edits, the keyboard focus rectangle at
  80/255, the outline at 180 and 40 on scrollbars, arrows at 160, black 15
  under a tab pane, and a group box's interior, which is a translucent pixmap
  (`fusion_groupbox.png`). QCommonStyle frames a tool tip in `ToolTipText`,
  1 px. A text cursor is drawn in `Text`; no role reaches it. Corner radii
  (2 px on buttons, edits and tabs) and line widths are the style's.
- `QMdiArea` paints its background in `Dark`; qt5ct's and qt6ct's own preview
  is one.
- **Glyphs render with subpixel antialiasing** here: a vertical stem carries
  a blue fringe on one side and an orange one on the other. A pixel pass over
  a label finds saturated blue and orange columns that are the rasteriser's,
  not the palette's.
- **COSMIC exports a Qt palette of its own** when the toolkit setting
  `apply_theme_global` is on — off in libcosmic's own default, **on in the
  system default Pop!_OS ships**
  (`/usr/share/cosmic/com.system76.CosmicTk/v1/apply_theme_global`).
  cosmic-settings-daemon then writes, at start, on every theme change, on
  every mode switch and on auto-switch: `~/.config/qt{5,6}ct/colors/
  CosmicLight.conf` and `CosmicDark.conf` (`# GENERATED BY COSMIC`),
  `~/.local/share/color-schemes/CosmicLight.colors` and `CosmicDark.colors`,
  `~/.config/kdeglobals`, and the GTK export; and it runs `flatpak override
  --user --filesystem` for `xdg-config/gtk-3.0:ro`, `xdg-config/gtk-4.0:ro`,
  `xdg-config/kdeglobals:ro` and `xdg-data/color-schemes:ro`, **removing
  `QT_QPA_PLATFORMTHEME=kde` from the global override** if it finds it. In
  `qt5ct.conf` and `qt6ct.conf` it keeps a marker, `cosmic_qt_version` (2 at
  present): below that version it sets `color_scheme_path`,
  `custom_palette=true`, `icon_theme=breeze` (or `breeze-dark`) and
  `standard_dialogs=xdgdesktopportal` unconditionally; at that version it
  rewrites only a `color_scheme_path` that contains "Cosmic" and an
  `icon_theme` that contains "breeze". **Measured 2026-09-21: a foreign
  scheme path with the marker present survived a theme re-import — the file's
  keys were re-ordered and nothing else changed. kdeglobals has no such
  guard: the same re-import rewrote every colour group and `[General]
  ColorScheme` back to CosmicLight.** Turning the setting off runs the reset:
  it removes `cosmic_qt_version`, `color_scheme_path` and `icon_theme` from
  both confs whenever the marker is present, whoever wrote the path, and
  deletes its own `.colors` files; kdeglobals is reset only if its
  `ColorScheme` is CosmicLight or CosmicDark. The GTK export goes with it.
  (libcosmic `cosmic-theme/src/output/qt56ct_output.rs` and `qt_output.rs`,
  cosmic-settings-daemon `src/theme.rs`.) The daemon's INI writer drops
  comments and re-orders keys. Its export is a derivation of the COSMIC
  theme, not a copy of it: measured on this desktop, 4 of its 21 active roles
  were values the theme names.
- **A Flatpak on the KDE runtime** (`org.kde.Platform`) has no qt5ct plugin
  inside its sandbox and inherits the session's `QT_QPA_PLATFORMTHEME=qt5ct`,
  so Qt falls back to the generic theme and the application paints Qt's stock
  palette (`#EFEFEF` Window, `#FFFFFF` Base). Measured 2026-09-21 on
  `org.kde.isoimagewriter` (runtime 6.11): unset, or `xdgdesktopportal`, the
  same; `gtk3` reads the GTK theme; **`kde` — KDEPlasmaPlatformTheme6, which
  the runtime ships — reads `~/.config/kdeglobals`** and the scheme applies.
  `flatpak override --user --env=QT_QPA_PLATFORMTHEME=kde APP` sets it per
  application; the global override is stripped by COSMIC's daemon at every
  login (above). `flatpak override --unset-env` records an unset rather than
  removing the entry.
- **The KDE colour scheme** (`kcolorscheme.cpp`, KF6):
  `[Colors:View|Window|Button|Selection|Tooltip|Complementary|Header]`, each
  with `BackgroundNormal`, `BackgroundAlternate`,
  `ForegroundNormal|Inactive|Active|Link|Visited|Negative|Neutral|Positive`,
  `DecorationFocus|Hover`, values as decimal triples; `[Colors:Header]
  [Inactive]`; `[ColorEffects:Disabled]` and `[ColorEffects:Inactive]` —
  Intensity, Color and Contrast effects with amounts, and by default a
  disabled foreground is the text faded 65% into its ground; `[General]
  ColorScheme` and `Name`; `[KDE] contrast`; `[WM]` for the decoration.
  `createApplicationPalette` maps View to Base and Text, Window to Window and
  WindowText, Button to Button and ButtonText, Selection to Highlight,
  HighlightedText and Accent, Tooltip to the tool tip roles, View's
  InactiveText to PlaceholderText and its Link and Visited to Link and
  LinkVisited; Light, Midlight, Mid, Dark and Shadow are shades computed from
  Window's background and `contrast`. Applications read kdeglobals directly; a
  `.colors` file under `~/.local/share/color-schemes/` is what Plasma's
  settings list. The KDE styles paint `Button` flat. `[KDE]
  widgetStyle=qt6ct-style` is what COSMIC writes; that style is qt6ct's proxy
  and is absent inside a Flatpak.
- On Wayland Qt asks for server-side decorations; on COSMIC the title bar is
  the compositor's (COSMIC, above).

**Cannot reach:** the caret's colour (drawn in `Text`); Fusion's line widths,
radii and blends; the title bar on COSMIC; the palette of a Flatpak without the
per-application override; and kdeglobals on COSMIC across a theme change while
`apply_theme_global` is on.

## Claude Code

Custom theme JSON in `~/.claude/themes/`, selected with `/theme`, or
`"theme": "custom:<name>"` in `~/.claude/settings.json` where `/theme` is
unavailable. Every token takes a hex value, so the terminal's own palette
does not enter into it.

**Cannot reach:** the desktop app's shell. Its appearance setting offers
light, dark and high contrast only, it loads no stylesheet, and modifying the
bundle is on the far side of the tier line.
