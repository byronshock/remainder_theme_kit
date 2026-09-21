#!/bin/sh
# Remainder for VS Code — per-user install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md VS Code. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--no-declutter] [--keep-file-icons] [--into DIR] [--no-ask]
#
# It installs the theme extension into every VS Code it finds under $HOME -- Code (deb, rpm, tar), Code as a
# Flatpak, Code Insiders, VSCodium, and VSCodium as a Flatpak -- by copying worksafe/vscode/remainder/ into that
# install's extensions directory, and then merges the kit's settings into that install's settings.json, key by
# key, after saving the original under ~/.local/state/remainder on the first run. Nothing is asked, because
# nothing here is another project's program (compare worksafe/firefox/install.sh --ublock); the flags narrow it.
#
#   --no-declutter    paint only: merge settings.json (the theme, the type, the caret) and not declutter.json,
#                     so §0's larger half stays where the platform put it.
#   --keep-file-icons leave workbench.iconTheme as it is (settings.json says why the kit sets vs-minimal).
#   --into DIR        install into a user-data-dir at DIR instead of any VS Code found: DIR/extensions and
#                     DIR/User/settings.json. This is the QA profile (CONTRIBUTING.md §10): run
#                       code --user-data-dir=DIR --extensions-dir=DIR/extensions
#                     and the kit's own VS Code is untouched. Keep DIR under $HOME: a Flatpak VS Code
#                     has a private /tmp, and a profile put there is created inside the sandbox, empty,
#                     where nothing you installed can be seen (PLATFORM.md VS Code).
#   --no-ask          accepted for parity with the other installers; nothing is asked anyway.
#
# VS Code may stay open. It watches settings.json and re-reads it when the file changes; the extension is seen
# on the next window reload (Developer: Reload Window) or the next start, which is when the theme appears.
#
# A settings.json with comments in it is not rewritten. Python's json writes none back, and a file the user
# annotated would come back bare -- so for that file the merged result is written beside the backup and the
# script says where, and the file itself is left alone.
set -e

DECLUTTER=1; KEEP_ICONS=0; INTO=''
while [ $# -gt 0 ]; do
  case "$1" in
    --no-declutter) DECLUTTER=0 ;;
    --keep-file-icons) KEEP_ICONS=1 ;;
    --into) shift; INTO="$1" ;;
    --into=*) INTO="${1#--into=}" ;;
    --no-ask) ;;
    -h|--help) sed -n '2,/^[^#]/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "remainder: unknown option $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done

# --- 0. the account this installs for -------------------------------------------------------------
# Same promise, and the same way sudo breaks it, as the COSMIC and Firefox installers: every path below is
# built from $HOME, and under sudo $HOME is root's.
if [ -n "$SUDO_USER" ]; then
  cat >&2 <<MSG
remainder: refusing to run under sudo -- this is a per-user install and under sudo it is not your VS Code.
           Everything it writes lands under \$HOME (here: $HOME). Run it as yourself:  sh $0
MSG
  exit 2
fi
[ "$(id -u)" = 0 ] && echo "remainder: running as root -- installing for root ($HOME), not for any other user."

HERE=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$HERE/../.." && pwd)
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/remainder"
say() { echo "remainder: $*"; }
backup() {  # backup PATH LABEL — first run only, so a re-run never overwrites the original
  [ -f "$1" ] && [ ! -e "$STATE/$2" ] && cp "$1" "$STATE/$2" && say "saved $1 -> $STATE/$2"
  return 0
}
VERSION=$(sed -n 's/^ *"version": *"\([^"]*\)".*/\1/p' "$HERE/remainder/package.json" | head -1)
[ -n "$VERSION" ] || { say "cannot read the version out of $HERE/remainder/package.json" >&2; exit 1; }
FOLDER="byronshock.remainder-$VERSION"

# --- 1. the installs -------------------------------------------------------------------------------
# Each line: label|extensions dir|settings.json. An install is present when its User directory exists; the
# extensions directory is created if it is not there yet. PLATFORM.md VS Code records where each packaging
# keeps them.
if [ -n "$INTO" ]; then
  mkdir -p "$INTO/extensions" "$INTO/User"
  TARGETS="qa|$INTO/extensions|$INTO/User/settings.json"
else
  TARGETS=''
  while IFS='|' read -r label ext cfg; do
    [ -n "$label" ] || continue
    [ -d "$(dirname "$cfg")" ] && TARGETS="$TARGETS
$label|$ext|$cfg"
  done <<LIST
code|$HOME/.vscode/extensions|$HOME/.config/Code/User/settings.json
code-flatpak|$HOME/.var/app/com.visualstudio.code/data/vscode/extensions|$HOME/.var/app/com.visualstudio.code/config/Code/User/settings.json
code-insiders|$HOME/.vscode-insiders/extensions|$HOME/.config/Code - Insiders/User/settings.json
codium|$HOME/.vscode-oss/extensions|$HOME/.config/VSCodium/User/settings.json
codium-flatpak|$HOME/.var/app/com.vscodium.codium/data/codium/extensions|$HOME/.var/app/com.vscodium.codium/config/VSCodium/User/settings.json
LIST
  if [ -z "$(printf '%s' "$TARGETS" | tr -d '\n')" ]; then
    say "no VS Code found under $HOME (looked for Code, Code Flatpak, Code Insiders, VSCodium, VSCodium Flatpak)" >&2
    say "to install into a user-data-dir of your own: sh $0 --into DIR" >&2
    exit 1
  fi
fi

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 2. per install: the extension, then the settings ----------------------------------------------
printf '%s\n' "$TARGETS" | while IFS='|' read -r LABEL EXT CFG; do
  [ -n "$LABEL" ] || continue
  # the extension: the kit's own earlier versions go, then this one is copied in whole
  mkdir -p "$EXT"
  for old in "$EXT"/byronshock.remainder-*; do
    [ -d "$old" ] && rm -r "$old"
  done
  cp -R "$HERE/remainder" "$EXT/$FOLDER"
  say "[$LABEL] extension: $EXT/$FOLDER"

  # the settings: back up, then merge key by key
  mkdir -p "$(dirname "$CFG")"
  [ -f "$CFG" ] || printf '{}\n' > "$CFG"
  backup "$CFG" "vscode.$LABEL.settings.json"
  MERGED="$STATE/vscode.$LABEL.merged.json"
  DECL=''; [ "$DECLUTTER" = 1 ] && DECL="$HERE/declutter.json"
  python3 - "$CFG" "$MERGED" "$KEEP_ICONS" "$HERE/settings.json" $DECL <<'PY'
import json, re, sys
cfg, merged, keep_icons, kit_files = sys.argv[1], sys.argv[2], sys.argv[3] == '1', sys.argv[4:]
strip = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.S)
def jsonc(text):
    s = strip.sub(lambda m: m.group(1) or '', text)
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', s) or '{}')
raw = open(cfg, encoding='utf-8').read()
try:
    user, plain = json.loads(raw or '{}'), True        # strict JSON: safe to write back
except ValueError:
    user, plain = jsonc(raw), False                     # comments or trailing commas: not rewritten
kit = {}
for f in kit_files:
    kit.update(jsonc(open(f, encoding='utf-8').read()))
if keep_icons:
    kit.pop('workbench.iconTheme', None)
changed = {k: v for k, v in kit.items() if user.get(k) != v}
user.update(kit)
out = json.dumps(user, indent=4, ensure_ascii=False) + '\n'
if plain:
    open(cfg, 'w', encoding='utf-8').write(out)
    print(f'remainder: settings: {len(changed)} key(s) set in {cfg}' + (', ' + ', '.join(sorted(changed)) if changed else ' (all were already set)'))
else:
    open(merged, 'w', encoding='utf-8').write(out)
    print(f'remainder: {cfg} has comments in it, so it is NOT rewritten -- python would write it back bare.')
    print(f'           the merged file is at {merged}; copy it over, or add these {len(changed)} key(s) by hand:')
    for k in sorted(changed):
        print(f'             {json.dumps(k)}: {json.dumps(kit[k])},')
PY
done

# --- 3. the fonts §5 declares, which this installer does not fetch --------------------------------
# One installer owns the checksums (CONTRIBUTING.md §12): worksafe/cosmic/install.sh --fonts.
fc-list 2>/dev/null | grep -qi ':Hack:\|: Hack:' || say "Hack is not installed -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"

# --- 4. what happened ---------------------------------------------------------------------------
[ "$DECLUTTER" = 1 ] && D="the declutter merged (§0)" || D="the declutter left alone (--no-declutter)"
cat <<MSG
remainder: theme $VERSION installed; $D; what was replaced is in $STATE
           VS Code re-reads settings.json on its own. The extension appears after a window reload
           (Developer: Reload Window) or a restart, and workbench.colorTheme already selects it.
           To undo: delete the byronshock.remainder-* folder and put the saved settings.json back.
MSG
