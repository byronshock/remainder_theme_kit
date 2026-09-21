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
- `active_hint` 0, or the focused window alone gets a hint and the gap
  carries state.
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

## Claude Code

Custom theme JSON in `~/.claude/themes/`, selected with `/theme`, or
`"theme": "custom:<name>"` in `~/.claude/settings.json` where `/theme` is
unavailable. Every token takes a hex value, so the terminal's own palette
does not enter into it.

**Cannot reach:** the desktop app's shell. Its appearance setting offers
light, dark and high contrast only, it loads no stylesheet, and modifying the
bundle is on the far side of the tier line.
