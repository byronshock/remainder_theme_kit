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

**Cannot reach per-user:** DWM draws a 1 px frame and nothing per-user
thickens it. Segoe UI Variable in system chrome (needs HKLM
`FontSubstitutes`). Control corner radii. Terminal and Chrome tab shapes.

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

- `user.js` for prefs; `chrome/userChrome.css` and `userContent.css` for
  chrome and content. Requires `toolkit.legacyUserProfileCustomizations.
  stylesheets`.
- Reachable: tab strip, toolbars, address and search fields, menus, panels,
  sidebar, new tab / home / blank pages, every radius.
- Prefs: density, scrollbars, reduced motion, fonts, and the declutter —
  sponsored tiles, suggestions, Pocket, trending, promotions, "what's new".
- uBlock Origin can be installed into the profile by script.

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
