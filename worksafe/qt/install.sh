#!/bin/sh
# Remainder for Qt — qt5ct, qt6ct and the KDE colour scheme. Per-user install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md Qt. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--no-qt5] [--no-qt6] [--no-kde] [--no-fonts] [--no-declutter] [--platformtheme]
#                      [--flatpak] [--into DIR] [--no-ask]
#
# A Qt application takes its colours from a PALETTE, and on Linux outside Plasma the palette reaches it through a
# platform theme plugin. This installs the kit's palette for the two a user can configure without elevation --
# qt5ct for Qt 5 and qt6ct for Qt 6 -- by copying a scheme file into each one's colours directory and merging a
# few keys into its config (the scheme, the Fusion style, the type, no motion), and it installs the same palette
# as a KDE colour scheme, which is what a Qt application in a Flatpak on the KDE runtime reads, and what Plasma
# reads. Every file it touches is saved under ~/.local/state/remainder on the first run. Nothing is asked,
# because nothing here is another project's program; the flags narrow it.
#
#   --no-qt5, --no-qt6   skip that target.
#   --no-kde             skip ~/.config/kdeglobals and ~/.local/share/color-schemes/Remainder.colors.
#   --no-fonts           leave [Fonts] alone: the type stays whatever qt5ct/qt6ct had.
#   --no-declutter       leave [Interface] gui_effects alone, so §0's larger half stays where the platform put it.
#   --platformtheme      also write ~/.config/environment.d/90-remainder-qt.conf setting QT_QPA_PLATFORMTHEME=qt5ct,
#                        for a desktop that does not set it (COSMIC does, in start-cosmic; so does Ubuntu's X session
#                        with qt5ct installed). Off by default: a session variable reaches every Qt application, which
#                        is more than painting. Takes effect at the next login.
#   --flatpak            for every installed Flatpak on the KDE runtime, set QT_QPA_PLATFORMTHEME=kde inside its
#                        sandbox (flatpak override --user --env, per application). Measured 2026-09-21 on COSMIC:
#                        inside the sandbox the session's qt5ct is inherited and the runtime has no such plugin, so
#                        the application paints Qt's stock palette; with kde it reads ~/.config/kdeglobals, which
#                        COSMIC already exposes to every Flatpak, and the scheme above reaches it. Off by default:
#                        an environment override is more than painting, and COSMIC's daemon removes the same
#                        variable from the GLOBAL override at every login, which is why this is per application.
#                        Undo: flatpak override --user --unset-env=QT_QPA_PLATFORMTHEME APP
#   --into DIR           write into DIR as if it were $XDG_CONFIG_HOME (DIR/qt5ct, DIR/qt6ct, DIR/kdeglobals, and
#                        DIR/color-schemes) instead of the real one. This is the QA profile (CONTRIBUTING.md §10):
#                        XDG_CONFIG_HOME=DIR qt6ct shows the palette on a real Qt 6 window with nothing of yours touched.
#   --no-ask             accepted for parity with the other installers; nothing is asked anyway.
#
# Qt applications may stay open: qt5ct and qt6ct watch their config file and re-read it, and the palette changes in
# place (the plugin's createFSWatcher). The KDE scheme is read when an application starts.
#
# COSMIC exports a Qt palette of its own when "Apply theme to other toolkits" is on (Pop!_OS ships it on), and
# its daemon keeps a version marker, cosmic_qt_version, in qt5ct.conf and qt6ct.conf. Once that marker is at the
# daemon's current version it only rewrites a scheme path that contains "Cosmic", so this scheme's path survives
# every theme change and mode switch; the marker is left exactly as found. If the marker is absent -- the toggle
# was never on -- and it is turned on later, the daemon's first export replaces the path and the icon theme; re-run
# this script. Turning the toggle off removes the scheme path outright (the daemon's reset); re-run this script.
# PLATFORM.md carries the contract and where it was read.
set -e

DO_QT5=1; DO_QT6=1; DO_KDE=1; FONTS=1; DECLUTTER=1; ENVD=0; FLATPAK=0; INTO=''
while [ $# -gt 0 ]; do
  case "$1" in
    --no-qt5) DO_QT5=0 ;;
    --no-qt6) DO_QT6=0 ;;
    --no-kde) DO_KDE=0 ;;
    --no-fonts) FONTS=0 ;;
    --no-declutter) DECLUTTER=0 ;;
    --platformtheme) ENVD=1 ;;
    --flatpak) FLATPAK=1 ;;
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
remainder: refusing to run under sudo -- this is a per-user install and under sudo it is not your Qt.
           Everything it writes lands under \$HOME (here: $HOME). Run it as yourself:  sh $0
MSG
  exit 2
fi
[ "$(id -u)" = 0 ] && echo "remainder: running as root -- installing for root ($HOME), not for any other user."

HERE=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$HERE/../.." && pwd)
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/remainder"
if [ -n "$INTO" ]; then
  mkdir -p "$INTO"
  CFG=$(cd "$INTO" && pwd)
  DATA="$CFG"
else
  CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
  DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
fi
say() { echo "remainder: $*"; }
backup() {  # backup PATH LABEL — first run only, so a re-run never overwrites the original
  [ -f "$1" ] && [ ! -e "$STATE/$2" ] && cp "$1" "$STATE/$2" && say "saved $1 -> $STATE/$2"
  return 0
}
for f in qt5ct/colors/remainder.conf qt6ct/colors/remainder.conf kde/Remainder.colors qt5ct/qt5ct.conf qt6ct/qt6ct.conf; do
  [ -f "$HERE/$f" ] || { say "missing $HERE/$f -- run: python3 $KIT/build/qt.py --write" >&2; exit 1; }
done

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 1. qt5ct and qt6ct: the scheme, then the config keys -----------------------------------------------
# The scheme is the kit's own file and is overwritten freely; the config is the user's and is merged key by key,
# keeping every key this fragment does not name (icon_theme, standard_dialogs, COSMIC's marker, window geometry).
for CT in qt5ct qt6ct; do
  if [ "$CT" = qt5ct ] && [ "$DO_QT5" = 0 ]; then continue; fi
  if [ "$CT" = qt6ct ] && [ "$DO_QT6" = 0 ]; then continue; fi
  DIR="$CFG/$CT"; CONF="$DIR/$CT.conf"; SCHEME="$DIR/colors/remainder.conf"
  mkdir -p "$DIR/colors"
  cp "$HERE/$CT/colors/remainder.conf" "$SCHEME"
  backup "$CONF" "$CT.conf"
  [ -f "$CONF" ] || : > "$CONF"
  python3 - "$CONF" "$HERE/$CT/$CT.conf" "$SCHEME" "$FONTS" "$DECLUTTER" <<'PY'
import re, sys
conf, frag, scheme, fonts, declutter = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == '1', sys.argv[5] == '1'

def parse(path):
    """[(group, key, value)] in file order, comments dropped."""
    out, cur = [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        s = line.rstrip('\n')
        if not s.strip() or s.lstrip().startswith(('#', ';')):
            continue
        if s.startswith('['):
            cur = s.strip()[1:-1]; continue
        k, _, v = s.partition('=')
        out.append((cur, k.strip(), v.strip()))
    return out

want = []
for g, k, v in parse(frag):
    if g == 'Fonts' and not fonts:
        continue
    if k == 'gui_effects' and not declutter:
        continue
    if k == 'color_scheme_path':
        v = scheme
    want.append((g, k, v))

lines = open(conf, encoding='utf-8', errors='replace').read().split('\n')
if lines and lines[-1] == '':
    lines.pop()
# where each group starts and ends (the line before the next group header, trailing blanks excluded)
def spans():
    sp, cur, start = {}, None, None
    for i, s in enumerate(lines):
        if s.startswith('['):
            if cur is not None:
                sp[cur] = (start, i)
            cur, start = s.strip()[1:-1], i + 1
    if cur is not None:
        sp[cur] = (start, len(lines))
    return sp

changed = []
for g, k, v in want:
    sp = spans()
    new = f'{k}={v}'
    if g in sp:
        a, b = sp[g]
        for i in range(a, b):
            if re.match(r'\s*' + re.escape(k) + r'\s*=', lines[i]):
                if lines[i].strip() != new:
                    lines[i] = new; changed.append(f'{g}/{k}')
                break
        else:
            end = b
            while end > a and lines[end - 1].strip() == '':
                end -= 1
            lines.insert(end, new); changed.append(f'{g}/{k}')
    else:
        if lines and lines[-1].strip() != '':
            lines.append('')
        lines += [f'[{g}]', new]; changed.append(f'{g}/{k}')
open(conf, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
marker = next((v for g, k, v in parse(conf) if g == 'Appearance' and k == 'cosmic_qt_version'), None)
name = conf.rsplit('/', 1)[-1]
print(f'remainder: {name}: {len(changed)} key(s) set' + (' (' + ', '.join(changed) + ')' if changed else ' (all were already set)')
      + (f"; COSMIC's marker cosmic_qt_version={marker} kept, so its daemon leaves this scheme path alone" if marker else ''))
PY
  say "[$CT] scheme: $SCHEME"
done

# --- 2. the KDE colour scheme: the file, then kdeglobals ------------------------------------------------
# ~/.local/share/color-schemes/Remainder.colors is what Plasma's settings list and plasma-apply-colorscheme
# take; ~/.config/kdeglobals is what applications actually read, so the scheme's groups are merged into it:
# the colour groups, the effects and [WM] replace their namesakes whole, [General] and [KDE] key by key,
# and every other group -- [Icons], the rest of [KDE] -- stays as it was.
if [ "$DO_KDE" = 1 ]; then
  mkdir -p "$DATA/color-schemes"
  cp "$HERE/kde/Remainder.colors" "$DATA/color-schemes/Remainder.colors"
  KG="$CFG/kdeglobals"
  backup "$KG" "kdeglobals"
  [ -f "$KG" ] || : > "$KG"
  python3 - "$KG" "$HERE/kde/Remainder.colors" <<'PY'
import sys
kg, scheme = sys.argv[1], sys.argv[2]

def groups(path):
    """{group: [lines]} in order, comments dropped, blank lines dropped."""
    out, cur = {}, None
    for line in open(path, encoding='utf-8', errors='replace'):
        s = line.rstrip('\n')
        if not s.strip() or s.lstrip().startswith(('#', ';')):
            continue
        if s.startswith('['):
            cur = s.strip()[1:-1]; out.setdefault(cur, []); continue
        out.setdefault(cur, []).append(s)
    return out

src, dst = groups(scheme), groups(kg)
whole = [g for g in src if g.startswith(('Colors:', 'ColorEffects:')) or g == 'WM']
for g in whole:
    dst[g] = list(src[g])
for g in ('General', 'KDE'):
    if g not in src:
        continue
    keys = {l.partition('=')[0].strip(): l for l in src[g]}
    kept = [l for l in dst.get(g, []) if l.partition('=')[0].strip() not in keys]
    dst[g] = kept + list(src[g])
out = []
for g, ls in dst.items():
    if g is None:
        out += ls; continue
    out += [f'[{g}]'] + ls + ['']
open(kg, 'w', encoding='utf-8').write('\n'.join(out).rstrip('\n') + '\n')
print(f'remainder: kdeglobals: {len(whole)} colour group(s) replaced, [General] and [KDE] merged; ColorScheme=Remainder')
PY
  say "kde scheme: $DATA/color-schemes/Remainder.colors"
fi

# --- 3. the session variable, only when asked ----------------------------------------------------------
if [ "$ENVD" = 1 ] && [ -z "$INTO" ]; then
  ED="$CFG/environment.d"; mkdir -p "$ED"
  backup "$ED/90-remainder-qt.conf" "environment.d-90-remainder-qt.conf"
  printf '# Remainder: Qt reads its palette through qt5ct (Qt 5) and qt6ct (Qt 6, which answers to this name too).\n# Written by worksafe/qt/install.sh --platformtheme; delete this file to undo it. Takes effect at the next login.\nQT_QPA_PLATFORMTHEME=qt5ct\n' > "$ED/90-remainder-qt.conf"
  say "wrote $ED/90-remainder-qt.conf (QT_QPA_PLATFORMTHEME=qt5ct at the next login)"
fi

# --- 3b. Flatpak applications on the KDE runtime, only when asked --------------------------------------
# Per application, never the global override: cosmic-settings-daemon strips QT_QPA_PLATFORMTHEME=kde from
# ~/.local/share/flatpak/overrides/global whenever it sets its own overrides (libcosmic set_flatpak_overrides),
# which is at every login. The list is what is installed now; re-run after installing another.
FP_DONE=''
if [ "$FLATPAK" = 1 ] && [ -z "$INTO" ] && command -v flatpak >/dev/null 2>&1; then
  for app in $(flatpak list --app --columns=application,runtime 2>/dev/null | awk '$2 ~ /^org\.kde\.(Platform|Sdk)\// {print $1}'); do
    flatpak override --user --env=QT_QPA_PLATFORMTHEME=kde "$app" && FP_DONE="$FP_DONE $app"
  done
  [ -n "$FP_DONE" ] && say "flatpak: QT_QPA_PLATFORMTHEME=kde set for$FP_DONE" || say "flatpak: no application on the KDE runtime is installed"
fi

# --- 4. the fonts §5 declares, which this installer does not fetch ---------------------------------------
# One installer owns the checksums (CONTRIBUTING.md §12): worksafe/cosmic/install.sh --fonts.
if [ "$FONTS" = 1 ]; then
  # fc-list names a family by every name it carries -- "Montserrat,Montserrat Medium" for the Medium cut -- so the
  # family list is split on commas before it is searched, or the cuts §5 chooses fail the test.
  for f in Montserrat Hack; do
    fc-list : family 2>/dev/null | tr ',' '\n' | grep -qix "$f" || say "font '$f' is not installed -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"
  done
fi

# --- 5. what happened, and what the session does with it ---------------------------------------------------
PT="${QT_QPA_PLATFORMTHEME:-}"
case "$PT" in
  qt5ct|qt6ct) E="QT_QPA_PLATFORMTHEME=$PT: Qt applications read the palette" ;;
  '') E="QT_QPA_PLATFORMTHEME is unset in this shell: a Qt application started from it uses no palette. COSMIC sets it for the session (start-cosmic); elsewhere, --platformtheme writes it for the next login" ;;
  *)  E="QT_QPA_PLATFORMTHEME=$PT: that platform theme paints its own palette, not this one; --platformtheme writes qt5ct for the next login" ;;
esac
[ "$DO_KDE" = 1 ] && K="the KDE scheme" || K="no KDE scheme (--no-kde)"
[ "$DECLUTTER" = 1 ] && D="no motion (§0)" || D="motion left alone (--no-declutter)"
[ "$FONTS" = 1 ] && T="Montserrat and Hack at 12 pt (§5)" || T="type left alone (--no-fonts)"
cat <<MSG
remainder: palette installed for $( [ "$DO_QT5" = 1 ] && printf 'qt5ct ' )$( [ "$DO_QT6" = 1 ] && printf 'qt6ct ' )and $K; $T; $D.
           what was replaced is in $STATE
           $E.
           Open Qt applications re-read qt5ct.conf and qt6ct.conf on their own; Plasma applications read the KDE
           scheme when they start, and a Flatpak on the KDE runtime reads it only with --flatpak (above).
           To undo: put the saved qt5ct.conf, qt6ct.conf and kdeglobals back, and delete the two remainder.conf
           files and Remainder.colors.
MSG
