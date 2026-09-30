#!/bin/sh
# Remainder for Firefox — per-profile install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md Firefox. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--profile PATH] [--ublock|--no-ublock] [--stylus|--no-stylus] [--style] [--no-ask]
#
# Run it with no arguments on a terminal and it asks two questions -- uBlock Origin, then Stylus -- before it
# writes anything, and Ctrl-C before answering leaves the machine untouched. A flag answers its own question in
# advance so a scripted install never blocks. With no terminal on stdin nothing is asked and the defaults stand.
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
#   --stylus   also install Stylus the same way, for elevated/remainder.user.css -- the kit's all-sites
#              sheet, the one thing it has whose reach is every site. Sideloading puts the extension in the
#              profile; IMPORTING THE SHEET IS A MANUAL STEP and always will be, because Stylus imports
#              through its own UI: Stylus > Manage > Import, and choose the file --style prints. Off by
#              default for the same reason as uBlock. --no-stylus declines without being asked.
#   --style    print where the import file is and exit. Writes nothing, asks nothing, and does not need
#              Firefox closed. Stylus reads its own JSON cleanly and balks at *.user.css, so the kit ships
#              both: elevated/remainder.user.css is the source and build/stylus_json.py generates the JSON.
#   --no-ask   ask nothing; take the flags and the defaults. Implied when stdin is not a terminal.
#
# Firefox must be closed. user.js and the chrome stylesheets are read once, at startup.
set -e

WANT_UBLOCK=''; WANT_STYLUS=''; PROFILE=''; NOASK=0; STYLE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --ublock) WANT_UBLOCK=1 ;;
    --no-ublock) WANT_UBLOCK=0 ;;
    --stylus) WANT_STYLUS=1 ;;
    --no-stylus) WANT_STYLUS=0 ;;
    --style) STYLE=1 ;;
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

# --style writes nothing and needs no profile, so it answers before any of the checks below.
if [ "$STYLE" = 1 ]; then
  JSON="$KIT/elevated/remainder.stylus.json"
  [ -f "$JSON" ] || python3 "$KIT/build/stylus_json.py" >/dev/null 2>&1
  if [ -f "$JSON" ]; then
    echo "remainder: in Firefox, Stylus > Manage > Import, and choose"
    echo "           $JSON"
    echo "           It is generated from elevated/remainder.user.css. After editing the sheet: bump"
    echo "           @version, add a line to the header changelog, run python3 $KIT/build/stylus_json.py,"
    echo "           and commit both files together (CONTRIBUTING.md §11)."
  else
    echo "remainder: no import file, and python3 could not generate one from $KIT/elevated/remainder.user.css" >&2
    exit 1
  fi
  exit 0
fi
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
# moves with the packaging: deb, snap and flatpak each put it somewhere else -- and a Firefox that finds no
# ~/.mozilla on first start puts it under XDG_CONFIG_HOME instead (156 on Arch, PLATFORM.md). The legacy root
# is tried first because that is Firefox's own precedence: where ~/.mozilla exists it keeps using it.
MOZ="${MOZ_HOME:-}"
if [ -z "$MOZ" ]; then
  for d in "$HOME/.mozilla/firefox" "${XDG_CONFIG_HOME:-$HOME/.config}/mozilla/firefox" \
           "$HOME/snap/firefox/common/.mozilla/firefox" \
           "$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox"; do
    [ -f "$d/profiles.ini" ] && MOZ="$d" && break
  done
fi
if [ -z "$PROFILE" ]; then
  [ -n "$MOZ" ] || { say "no Firefox profile root found (looked in ~/.mozilla, ~/.config/mozilla, snap and flatpak; set MOZ_HOME)" >&2; exit 1; }
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
if [ "$ASK" = 1 ] && [ -z "$WANT_STYLUS" ]; then
  cat <<Q
remainder: the kit's all-sites sheet, elevated/remainder.user.css, restyles every site you visit -- §0a
           exempts content, so that sheet is the reader's choice about their own screen and never the kit's.
           Stylus is the extension that loads it, and it is another project's software, fetched the same way.
           Sideloading it here does NOT import the sheet: Stylus imports through its own UI, so that stays a
           step you take (sh install.sh --style prints the file to choose).
Q
  if yesno "Install Stylus into this profile?" n; then WANT_STYLUS=1; else WANT_STYLUS=0; fi
fi
[ -n "$WANT_UBLOCK" ] || WANT_UBLOCK=0
[ -n "$WANT_STYLUS" ] || WANT_STYLUS=0

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
STYLUS_ID="{7a7a4a92-a2a0-41d1-9fd7-1e92480d612d}"
STYLUS_URL="https://addons.mozilla.org/firefox/downloads/latest/styl-us/latest.xpi"
SIDELOADED=0
sideload() {  # sideload ID URL NAME
  mkdir -p "$PROFILE/extensions"; XPI="$PROFILE/extensions/$1.xpi"
  if   command -v curl >/dev/null 2>&1; then curl -fsSL --max-time 120 -o "$XPI" "$2"
  elif command -v wget >/dev/null 2>&1; then wget -q -O "$XPI" "$2"
  else say "sideloading needs curl or wget -- $3 NOT installed"; return 1; fi
  if [ -s "$XPI" ]; then
    SIDELOADED=1
    say "$3 $(du -h "$XPI" | cut -f1) at $XPI (signed by Mozilla; from $2)"
  else
    rm -f "$XPI"; say "$3 NOT installed -- the download was empty"; return 1
  fi
}
[ "$WANT_UBLOCK" = 1 ] && { sideload "$UBLOCK_ID" "$UBLOCK_URL" "uBlock Origin" || true; }
[ "$WANT_STYLUS" = 1 ] && { sideload "$STYLUS_ID" "$STYLUS_URL" "Stylus" || true; }
if [ "$SIDELOADED" = 1 ]; then
  # Firefox starts a sideloaded extension disabled and asks once. Scope 1 is the profile directory -- the
  # user's own -- so 15 - 1 = 14 narrows the asking to that one scope and leaves user, system and
  # application scopes exactly as they were. No checksum is pinned on either of these on purpose: both fetch
  # the CURRENT build, which is the one with current filter-list and browser compatibility, and Mozilla's
  # signature is the provenance. A font is pinned to a tag because §5 names a version; these are not.
  printf '\n// sideloaded by install.sh: enable extensions the user put in this profile\nuser_pref("extensions.autoDisableScopes", 14);\n' >> "$PROFILE/user.js"
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
[ "$WANT_STYLUS" = 1 ] && Y="Stylus installed" || Y="Stylus left alone"
cat <<MSG
remainder: Firefox profile $PROFILE
           user.js, chrome/userChrome.css, chrome/userContent.css in place; $U; $Y.
           what was replaced is in $STATE
Start Firefox. The tab strip is the key titlebar and goes LIGHT when the window is not key -- the one
surface on this desktop that shows it (PLATFORM.md).
MSG
if [ "$WANT_STYLUS" = 1 ]; then cat <<MSG
           Stylus does not import the sheet for you. In Firefox: Stylus > Manage > Import, and choose
           $KIT/elevated/remainder.stylus.json
           That sheet restyles every site you visit, which is the reader's choice and not the kit's (§0a).
MSG
fi
