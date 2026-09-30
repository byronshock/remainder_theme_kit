#!/bin/sh
# Remainder for GTK 3 -- the theme every GTK 3 application draws with. Per-user install. No sudo, nothing outside
# $HOME. (worksafe tier) Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md GTK 3. Re-runnable, and it backs up
# what it replaces.
#
# Usage: sh install.sh [--no-declutter] [--no-select] [--into DIR] [--no-ask]
#
# A GTK 3 application -- Nemo, GIMP, Inkscape, Meld, GParted, Emacs, the GTK file chooser, and the dialogs and menus
# Firefox and Chromium borrow from GTK -- draws with the GTK theme the desktop names. This copies the Remainder theme
# into ~/.local/share/themes/Remainder and names it twice: org.gnome.desktop.interface gtk-theme, which GTK 3 reads
# on COSMIC, and gtk-theme-name in ~/.config/gtk-3.0/settings.ini, which it reads where no settings service
# answers. §0's larger half goes with it: the theme's declutter sheet turns every transition and animation off, and
# org.gnome.desktop.interface enable-animations, which GTK's own revealers and stacks obey, is set to false. What
# either setting held before is saved under ~/.local/state/remainder on the first run. Nothing is asked, because
# nothing here is another project's program; the flags narrow it.
#
#   --no-declutter  install the declutter sheet empty and leave enable-animations alone, so motion stays.
#   --no-select     copy the theme and name nothing: the screen does not change until the theme is chosen.
#   --into DIR      install the theme into DIR/themes/Remainder and name nothing: the QA profile
#                   (CONTRIBUTING.md §10). build/gtk.py --screen builds its own.
#   --no-ask        accepted for parity with the other installers; nothing is asked anyway.
#
# Running GTK 3 applications take the new theme at once: GTK watches the setting and restyles every window.
#
# COSMIC's "Apply current theme to GNOME apps" (the toolkit setting apply_theme_global) writes
# ~/.config/gtk-3.0/gtk.css with its own colours under libadwaita's names. That sheet sits above any theme and
# redefines those names for whatever reads them; this theme paints from names of its own (@rm_*), so its own rules
# are untouched, and only an application's own CSS that asks for a libadwaita name gets COSMIC's colour. The
# installer says so when it finds that file. PLATFORM.md carries the contract.
#
# Undo: gsettings set org.gnome.desktop.interface gtk-theme "$(cat ~/.local/state/remainder/gtk-theme.before)",
#       the same for enable-animations, put the saved settings.ini back, and delete ~/.local/share/themes/Remainder.
set -e

DECLUTTER=1; SELECT=1; INTO=''
while [ $# -gt 0 ]; do
  case "$1" in
    --no-declutter) DECLUTTER=0 ;;
    --no-select) SELECT=0 ;;
    --into) shift; INTO="$1" ;;
    --into=*) INTO="${1#--into=}" ;;
    --no-ask) ;;
    -h|--help) sed -n '2,/^[^#]/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "remainder: unknown option $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done

# --- 0. the account this installs for -------------------------------------------------------------
# Same promise, and the same way sudo breaks it, as the other installers: every path below is built from $HOME,
# and under sudo $HOME is root's.
if [ -n "$SUDO_USER" ]; then
  cat >&2 <<MSG
remainder: refusing to run under sudo -- this is a per-user install and under sudo it is not your GTK.
           Everything it writes lands under \$HOME (here: $HOME). Run it as yourself:  sh $0
MSG
  exit 2
fi
[ "$(id -u)" = 0 ] && echo "remainder: running as root -- installing for root ($HOME), not for any other user."

HERE=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$HERE/../.." && pwd)
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/remainder"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
if [ -n "$INTO" ]; then
  mkdir -p "$INTO"
  DATA=$(cd "$INTO" && pwd)
  SELECT=0
else
  DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
fi
say() { echo "remainder: $*"; }
backup() {  # backup PATH LABEL -- first run only, so a re-run never overwrites the original
  [ -f "$1" ] && [ ! -e "$STATE/$2" ] && cp "$1" "$STATE/$2" && say "saved $1 -> $STATE/$2"
  return 0
}
for f in Remainder/index.theme Remainder/gtk-3.0/gtk.css Remainder/gtk-3.0/remainder-declutter.css; do
  [ -f "$HERE/$f" ] || { say "missing $HERE/$f -- run: python3 $KIT/build/gtk.py --write" >&2; exit 1; }
done

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 1. the theme: the kit's own directory, replaced whole ------------------------------------------
# A directory of the same name that this kit did not write is moved aside, not deleted.
DEST="$DATA/themes/Remainder"
if [ -d "$DEST" ] && ! grep -q 'build/gtk.py' "$DEST/index.theme" 2>/dev/null; then
  ASIDE="$STATE/themes-Remainder.before-$(date +%Y%m%d-%H%M%S)"
  mv "$DEST" "$ASIDE"
  say "a theme called Remainder that this kit did not write was in the way: moved to $ASIDE"
fi
rm -rf "$DEST"
mkdir -p "$DATA/themes"
cp -R "$HERE/Remainder" "$DEST"
if [ "$DECLUTTER" = 0 ]; then
  printf '/* Remainder for GTK 3 -- the declutter, switched off by install.sh --no-declutter: motion is left as the\n   platform draws it. */\n' > "$DEST/gtk-3.0/remainder-declutter.css"
fi
say "theme: $DEST"

# --- 2. naming it -------------------------------------------------------------------------------------
# gsettings is what GTK 3 reads on COSMIC, under Wayland and XWayland alike; settings.ini is what it reads where no
# settings service answers (a bare X session, a nested one). The first value found for each is saved once.
if [ "$SELECT" = 1 ]; then
  if command -v gsettings >/dev/null 2>&1; then
    [ -e "$STATE/gtk-theme.before" ] || gsettings get org.gnome.desktop.interface gtk-theme | tr -d "'" > "$STATE/gtk-theme.before"
    gsettings set org.gnome.desktop.interface gtk-theme 'Remainder'
    say "gtk-theme: Remainder (it was $(cat "$STATE/gtk-theme.before"))"
    if [ "$DECLUTTER" = 1 ]; then
      [ -e "$STATE/enable-animations.before" ] || gsettings get org.gnome.desktop.interface enable-animations > "$STATE/enable-animations.before"
      gsettings set org.gnome.desktop.interface enable-animations false
      say "enable-animations: false (it was $(cat "$STATE/enable-animations.before"))"
    fi
  else
    say "gsettings is not on this machine: settings.ini alone names the theme"
  fi
  INI="$CFG/gtk-3.0/settings.ini"
  mkdir -p "$CFG/gtk-3.0"
  backup "$INI" "gtk-3.0-settings.ini"
  [ -f "$INI" ] || : > "$INI"
  python3 - "$INI" "$DECLUTTER" <<'PY'
import re, sys
ini, declutter = sys.argv[1], sys.argv[2] == '1'
want = [('gtk-theme-name', 'Remainder')] + ([('gtk-enable-animations', 'false')] if declutter else [])
lines = open(ini, encoding='utf-8', errors='replace').read().split('\n')
if lines and lines[-1] == '':
    lines.pop()
start = next((i for i, l in enumerate(lines) if l.strip() == '[Settings]'), None)
if start is None:
    if lines and lines[-1].strip():
        lines.append('')
    lines.append('[Settings]')
    start = len(lines) - 1
end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('[')), len(lines))
for k, v in want:
    for i in range(start + 1, end):
        if re.match(r'\s*' + re.escape(k) + r'\s*=', lines[i]):
            lines[i] = f'{k}={v}'
            break
    else:
        lines.insert(end, f'{k}={v}')
        end += 1
open(ini, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print(f'remainder: {ini}: ' + ', '.join(f'{k}={v}' for k, v in want))
PY
fi

# --- 3. COSMIC's own GTK export, if it is on --------------------------------------------------------------
if [ -z "$INTO" ] && [ -f "$CFG/gtk-3.0/gtk.css" ] && grep -q 'define-color' "$CFG/gtk-3.0/gtk.css"; then
  say "$CFG/gtk-3.0/gtk.css defines colours of its own (COSMIC's \"Apply current theme to GNOME apps\" writes it):"
  say "  the theme's own rules are untouched by it; an application's own CSS that reads a libadwaita name gets its colour."
fi

# --- 4. the fonts §5 declares, which this installer does not fetch ---------------------------------------
# One installer owns the checksums (CONTRIBUTING.md §12): worksafe/cosmic/install.sh --fonts. fc-list names a family
# by every name it carries -- "Montserrat,Montserrat Medium" -- so the list is split on commas before it is searched.
fc-list : family 2>/dev/null | tr ',' '\n' | grep -qix Montserrat \
  || say "font 'Montserrat' is not installed -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"
fc-list : family 2>/dev/null | tr ',' '\n' | grep -qix -e 'IntoneMono Nerd Font Mono' -e 'Intel One Mono' \
  || say "font 'IntoneMono Nerd Font Mono' is not installed -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"

# --- 5. what happened -----------------------------------------------------------------------------------
[ "$DECLUTTER" = 1 ] && D="no motion (§0)" || D="motion left alone (--no-declutter)"
if [ "$SELECT" = 1 ]; then
  cat <<MSG
remainder: GTK 3 theme installed and selected; $D.
           Open GTK 3 applications restyle now. What was replaced is in $STATE.
           To undo: gsettings set org.gnome.desktop.interface gtk-theme "\$(cat $STATE/gtk-theme.before)"
MSG
else
  say "GTK 3 theme installed in $DEST and not selected; $D."
fi
