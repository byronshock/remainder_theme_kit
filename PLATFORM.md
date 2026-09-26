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
  `~/.var/app/org.mozilla.firefox/.mozilla/firefox` — and
  `${XDG_CONFIG_HOME:-~/.config}/mozilla/firefox` on a machine where Firefox
  found no `~/.mozilla` at its first start: measured 2026-09-23 on 156.0.1 (the
  Arch package), which created no `~/.mozilla` at all and keeps `profiles.ini`
  there; its libxul carries both `XDG_CONFIG_HOME` and a `MOZ_LEGACY_HOME`
  override. Where `~/.mozilla` exists it is still the root. Inside it, `installs.ini`
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
  the extensions directory is picked up only while there is no
  `extensions.json` beside it.** On a directory without one, the scanner lists
  the folder and writes that file from what it finds (the 1.137.0 measurement,
  on a fresh directory). The first marketplace install writes
  `extensions.json`, and from then on it is the record of what is installed: a
  folder it does not list is logged `Marked extension as removed` on the next
  start, its name goes into `.obsolete` in the same directory, and the theme
  never appears — 1.138.0 (Code - OSS, 2026-09-23), five consecutive starts,
  with `workbench.colorTheme` naming the theme throughout; the window fell
  back to the build's default, Dark 2026. Appending the folder's entry to
  `extensions.json` in the form VS Code writes (`identifier`, `version`,
  `location` as URI components, `relativeLocation`, `metadata`) and dropping
  its name from `.obsolete` registers it: `code --list-extensions` reads the
  same record and listed it at once, and the start that followed logged no
  removal. So no `.vsix` and no CLI is needed to install one, but the entry is.
  It is seen on the next window reload or start.
- Where each packaging keeps things (per user, no elevation):
  `~/.vscode/extensions` and `~/.config/Code/User/settings.json` (deb, rpm, tar);
  `~/.var/app/com.visualstudio.code/data/vscode/extensions` and
  `~/.var/app/com.visualstudio.code/config/Code/User/settings.json` (Flatpak);
  `~/.vscode-insiders` and `~/.config/Code - Insiders` (Insiders);
  `~/.vscode-oss` and `~/.config/VSCodium` (VSCodium);
  `~/.vscode-oss` and `~/.config/Code - OSS` (Code - OSS, the Arch `code`
  package: the same extensions directory as VSCodium, since both set
  `dataFolderName` to `.vscode-oss`, and its own config folder; 1.138.0,
  2026-09-23);
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

## Claude Code

Custom theme JSON in `~/.claude/themes/`, selected with `/theme`, or
`"theme": "custom:<name>"` in `~/.claude/settings.json` where `/theme` is
unavailable. Every token takes a hex value, so the terminal's own palette
does not enter into it.

**Cannot reach:** the desktop app's shell. Its appearance setting offers
light, dark and high contrast only, it loads no stylesheet, and modifying the
bundle is on the far side of the tier line.
