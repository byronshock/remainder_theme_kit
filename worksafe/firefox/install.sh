#!/bin/sh
# Remainder for Firefox — per-profile install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md Firefox. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--profile PATH] [--ublock|--no-ublock] [--no-ask]
#
# Run it with no arguments on a terminal and it asks one question -- uBlock Origin -- before it writes
# anything, and Ctrl-C before answering leaves the machine untouched. The flag answers the question in advance
# so a scripted install never blocks. With no terminal on stdin nothing is asked and the default stands.
#
#   --profile PATH  install into this profile directory instead of the one this Firefox opens. The default is
#              read from installs.ini, and failing that from the Default= flag in profiles.ini.
#   --ublock   also install uBlock Origin into the profile: the current signed build from addons.mozilla.org,
#              into the profile's own extensions/ directory, with extensions.autoDisableScopes narrowed so a
#              profile-directory extension starts enabled instead of asking. §0 holds that advertisements are
#              noise and that removing what was put in the user's way is the larger half of the kit.
#              OFF BY DEFAULT, and the question defaults to no -- which is a narrower default than the COSMIC
#              installer's two. Fonts are the faces §5 declares and icons are the machine's own art reprojected;
#              uBlock is another project's program, and the kit does not put somebody else's program on a
#              machine unless it is asked in so many words. --no-ublock declines without being asked.
#   --no-ask   ask nothing; take the flags and the defaults. Implied when stdin is not a terminal.
#
# Firefox must be closed. user.js and the chrome stylesheets are read once, at startup.
set -e

WANT_UBLOCK=''; PROFILE=''; NOASK=0
while [ $# -gt 0 ]; do
  case "$1" in
    --ublock) WANT_UBLOCK=1 ;;
    --no-ublock) WANT_UBLOCK=0 ;;
    --profile) shift; PROFILE="$1" ;;
    --profile=*) PROFILE="${1#--profile=}" ;;
    --no-ask) NOASK=1 ;;
    # The help text is the comment block above: line 2 to the first line that is not a comment, less that line.
    -h|--help) sed -n '2,/^[^#]/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "remainder: unknown option $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done

# --- 0. the account this installs for -------------------------------------------------------------
# Same promise, and the same way sudo breaks it, as worksafe/cosmic/install.sh: every path below is built from
# $HOME, and under sudo $HOME is root's. There is no system-wide Firefox profile here that would need root.
if [ -n "$SUDO_USER" ]; then
  cat >&2 <<MSG
remainder: refusing to run under sudo -- this is a per-profile install and under sudo it is not your profile.
           Everything it writes lands under \$HOME (here: $HOME), as the user sudo switched to and not as
           $SUDO_USER. Run it as yourself:  sh $0
MSG
  exit 2
fi
[ "$(id -u)" = 0 ] && echo "remainder: running as root -- installing for root ($HOME), not for any other user."

HERE=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$HERE/../.." && pwd)
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/remainder"   # what this script replaced, so it is reversible
say() { echo "remainder: $*"; }
backup() {  # backup PATH LABEL — first run only, so a re-run never overwrites the original
  [ -f "$1" ] && [ ! -e "$STATE/$2" ] && cp "$1" "$STATE/$2" && say "saved $1 -> $STATE/$2"
  return 0
}

# --- 1. Firefox must be closed --------------------------------------------------------------------
# Not politeness: Firefox reads user.js at startup and writes prefs.js at shutdown, so a running instance
# overwrites what this script just installed, and userChrome.css is read once at startup as well.
for p in firefox firefox-bin firefox-esr; do
  if pgrep -x "$p" >/dev/null 2>&1; then
    say "close Firefox first -- user.js and userChrome.css are read at startup, and a running Firefox" >&2
    say "         overwrites prefs.js from memory when it exits." >&2
    exit 1
  fi
done

# --- 2. the profile -------------------------------------------------------------------------------
# installs.ini names the profile THIS Firefox install opens, which is the one the user will see; profiles.ini's
# Default= is the fallback for a build that writes no installs.ini. Both live under the same root, and the root
# moves with the packaging: deb, snap and flatpak each put it somewhere else.
MOZ="${MOZ_HOME:-}"
if [ -z "$MOZ" ]; then
  for d in "$HOME/.mozilla/firefox" "$HOME/snap/firefox/common/.mozilla/firefox" \
           "$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox"; do
    [ -f "$d/profiles.ini" ] && MOZ="$d" && break
  done
fi
if [ -z "$PROFILE" ]; then
  [ -n "$MOZ" ] || { say "no Firefox profile root found (looked in ~/.mozilla, snap and flatpak; set MOZ_HOME)" >&2; exit 1; }
  PROFILE=$(python3 - "$MOZ" <<'PY'
import configparser, os, sys
moz = sys.argv[1]
def rel(sec): return os.path.join(moz, sec.get('Path', '')) if sec.get('IsRelative', '1') == '1' else sec.get('Path', '')
ini = configparser.RawConfigParser(strict=False); ini.read(os.path.join(moz, 'profiles.ini'))
inst = configparser.RawConfigParser(strict=False); inst.read(os.path.join(moz, 'installs.ini'))
for s in inst.sections():                       # the profile this Firefox install opens
    if inst[s].get('Default'):
        print(os.path.join(moz, inst[s]['Default'])); sys.exit()
for s in ini.sections():
    if s.startswith('Install') and ini[s].get('Default'):
        print(os.path.join(moz, ini[s]['Default'])); sys.exit()
for s in ini.sections():
    if s.startswith('Profile') and ini[s].get('Default') == '1':
        print(rel(ini[s])); sys.exit()
PY
)
fi
[ -d "$PROFILE" ] || { say "no Firefox profile at '$PROFILE'" >&2; exit 1; }

# --- 3. the question, asked before anything is written ---------------------------------------------
ASK=1
[ "$NOASK" = 1 ] && ASK=0
{ [ ! -t 0 ] || [ ! -t 1 ]; } && ASK=0
yesno() {   # yesno QUESTION DEFAULT(y|n) -- 0 for yes. Empty or EOF takes the default.
  case "$2" in y) _hint='[Y/n]' ;; *) _hint='[y/N]' ;; esac
  printf 'remainder: %s %s ' "$1" "$_hint"
  if ! read -r _reply; then _reply=''; echo; fi
  [ -n "$_reply" ] || _reply=$2
  case "$_reply" in [Yy]*) return 0 ;; *) return 1 ;; esac
}
if [ "$ASK" = 1 ] && [ -z "$WANT_UBLOCK" ]; then
  cat <<Q
remainder: the kit's larger half is removal (§0), and on the web that means an ad blocker. uBlock Origin is
           not the kit's software: the installer would fetch the current signed build from addons.mozilla.org
           into this profile's own extensions directory and let profile-directory extensions start enabled.
           Nothing outside the profile, and deleting the .xpi undoes it.
           Profile: $PROFILE
Q
  if yesno "Install uBlock Origin into this profile?" n; then WANT_UBLOCK=1; else WANT_UBLOCK=0; fi
fi
[ -n "$WANT_UBLOCK" ] || WANT_UBLOCK=0

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 4. the sheets and the prefs --------------------------------------------------------------------
STAMP=$(basename "$PROFILE")
backup "$PROFILE/user.js" "firefox.$STAMP.user.js"
backup "$PROFILE/chrome/userChrome.css" "firefox.$STAMP.userChrome.css"
backup "$PROFILE/chrome/userContent.css" "firefox.$STAMP.userContent.css"
mkdir -p "$PROFILE/chrome"
cp "$HERE/user.js" "$PROFILE/user.js"
cp "$HERE/chrome/userChrome.css" "$HERE/chrome/userContent.css" "$PROFILE/chrome/"

# --- 5. uBlock Origin (§0), asked for or --ublock ----------------------------------------------------
UBLOCK_ID="uBlock0@raymondhill.net"
UBLOCK_URL="https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
if [ "$WANT_UBLOCK" = 1 ]; then
  mkdir -p "$PROFILE/extensions"; XPI="$PROFILE/extensions/$UBLOCK_ID.xpi"
  if   command -v curl >/dev/null 2>&1; then curl -fsSL --max-time 120 -o "$XPI" "$UBLOCK_URL"
  elif command -v wget >/dev/null 2>&1; then wget -q -O "$XPI" "$UBLOCK_URL"
  else say "sideloading needs curl or wget -- uBlock NOT installed"; XPI=''; fi
  if [ -n "$XPI" ] && [ -s "$XPI" ]; then
    # Firefox starts a sideloaded extension disabled and asks once. Scope 1 is the profile directory -- the
    # user's own -- so 15 - 1 = 14 narrows the asking to that one scope and leaves user, system and
    # application scopes exactly as they were. No checksum is pinned here on purpose: this fetches the
    # CURRENT build, which is the one with the current filter-list compatibility, and Mozilla's signature is
    # the provenance. A font is pinned to a tag because §5 names a version; an ad blocker is not.
    printf '\n// sideloaded by install.sh --ublock: enable extensions the user put in this profile\nuser_pref("extensions.autoDisableScopes", 14);\n' >> "$PROFILE/user.js"
    say "uBlock Origin $(du -h "$XPI" | cut -f1) at $XPI (signed by Mozilla; from $UBLOCK_URL)"
  else
    [ -n "$XPI" ] && { rm -f "$XPI"; say "uBlock Origin NOT installed -- the download was empty"; }
  fi
fi

# --- 6. the fonts §5 declares, which this installer does not fetch -----------------------------------
# One installer owns the checksums. worksafe/cosmic/install.sh pins Hack and Montserrat to a tag and verifies
# each file against a SHA-256 recorded there (CONTRIBUTING.md §12); a second copy of those checksums in this
# file would be a second thing to keep true. So this one only says whether the faces are here.
missing=''
for f in Montserrat Hack; do
  fc-list 2>/dev/null | grep -qi ":$f:\|: $f:" || missing="$missing $f"
done
[ -n "$missing" ] && say "font(s) not installed:$missing -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"

# --- 7. what happened ---------------------------------------------------------------------------------
[ "$WANT_UBLOCK" = 1 ] && U="uBlock Origin installed" || U="uBlock left alone (§0 default)"
cat <<MSG
remainder: Firefox profile $PROFILE
           user.js, chrome/userChrome.css, chrome/userContent.css in place; $U.
           what was replaced is in $STATE
Start Firefox. The tab strip is the key titlebar and goes LIGHT when the window is not key -- the one
surface on this desktop that shows it (PLATFORM.md).
MSG
