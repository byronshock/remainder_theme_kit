#!/bin/sh
# Remainder for Obsidian — per-user install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md Obsidian. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--vault DIR]... [--qa DIR] [--no-declutter] [--sync-off|--keep-sync] [--no-ask]
#
# A theme in Obsidian belongs to a vault, not to the user, so this installs into every vault Obsidian knows: the
# list in obsidian.json, in the config directory of each packaging it finds (the Arch or deb or tar build under
# ${XDG_CONFIG_HOME:-~/.config}/obsidian, the Flatpak under ~/.var/app/md.obsidian.Obsidian/config/obsidian, the
# Snap under ~/snap/obsidian/current/.config/obsidian). In each vault it copies worksafe/obsidian/Remainder/ into
# .obsidian/themes/Remainder/ and the declutter snippet into .obsidian/snippets/, then merges appearance.json
# key by key after saving the original under ~/.local/state/remainder on the first run. Undo it by choosing
# another theme in Settings > Appearance, or by putting the saved appearance.json back.
#
#   --vault DIR     this vault only (repeatable), whether Obsidian lists it or not: DIR is the folder that holds
#                   .obsidian. A vault kept in a git repository usually ignores .obsidian/, and this writes only
#                   inside it.
#   --qa DIR        a QA profile at DIR, to look at a change without touching a vault of yours: DIR/vault, with a
#                   note holding every kind of block, and DIR/config/obsidian/obsidian.json listing it as open. The
#                   theme goes into that vault only, and the command that opens it is printed. The list is the
#                   point: Obsidian opens only a vault its obsidian.json names, and a path on its command line opens
#                   the vault picker instead (PLATFORM.md Obsidian).
#   --no-declutter  paint only: the theme and appearance.json, and not the snippet that removes motion and blur,
#                   so §0's larger half stays where the platform put it.
#   --sync-off      turn the Sync core plugin off in every vault where it is on. Obsidian ships it on, and with no
#                   Sync account connected it paints a red status icon on every screen -- an error for a service
#                   nobody signed up for, which §3 does not allow and §0 removes. But Sync keeps its connection in
#                   Obsidian's own storage and not in the vault, so this script cannot tell a vault that uses Sync
#                   from one that does not: on a terminal it asks, and the answer defaults to no.
#   --keep-sync     leave Sync alone without asking.
#   --no-ask        ask nothing; take the flags and the defaults. Implied when stdin is not a terminal.
#
# Obsidian may stay open. It watches appearance.json and the theme's own file and applies both as they change
# (PLATFORM.md Obsidian); a vault that is not open picks the theme up when it next is.
set -e

DECLUTTER=1; SYNC=''; NOASK=0; VAULTS=''; QA=''
while [ $# -gt 0 ]; do
  case "$1" in
    --vault) shift; VAULTS="$VAULTS
$1" ;;
    --vault=*) VAULTS="$VAULTS
${1#--vault=}" ;;
    --qa) shift; QA="$1" ;;
    --qa=*) QA="${1#--qa=}" ;;
    --no-declutter) DECLUTTER=0 ;;
    --sync-off) SYNC=off ;;
    --keep-sync) SYNC=keep ;;
    --no-ask) NOASK=1 ;;
    # The help text is the comment block above: line 2 to the first line that is not a comment, less that line.
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
remainder: refusing to run under sudo -- this is a per-user install and under sudo it is not your vaults.
           Everything it writes lands under \$HOME (here: $HOME). Run it as yourself:  sh $0
MSG
  exit 2
fi
[ "$(id -u)" = 0 ] && echo "remainder: running as root -- installing for root ($HOME), not for any other user."

HERE=$(cd "$(dirname "$0")" && pwd)
KIT=$(cd "$HERE/../.." && pwd)
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/remainder"
say() { echo "remainder: $*"; }

# --- 0b. the QA profile, when asked for ---------------------------------------------------------------
if [ -n "$QA" ]; then
  mkdir -p "$QA/vault" "$QA/config/obsidian"
  QA=$(cd "$QA" && pwd)
  [ -f "$QA/vault/QA.md" ] || cat > "$QA/vault/QA.md" <<'NOTE'
---
tags:
  - qa
status: draft
---
# Heading one

Body text with **bold**, *italic*, ==a highlight==, ~~struck~~, `inline code`, a #tag, an [[Nowhere|unresolved link]], and an [external link](https://example.org).

## Heading two

- [ ] a task not done
- [x] a task done
- a bullet
	- nested

1. first
2. second

> A blockquote, carrying a line of text.

| Column | Other |
| ------ | ----- |
| a cell | b     |
| c      | d     |

```python
def remainder(x: int) -> str:
    # a comment
    return f"{x} is {'odd' if x % 2 else 'even'}"
```

> [!note] Note
> A note callout: furniture.

> [!warning] Warning
> A warning callout.

> [!danger] Danger
> A danger callout.

> [!success] Success
> A success callout.

> [!question] Question
> A question callout: furniture.

A footnote reference.[^1]

---

[^1]: The footnote.
NOTE
  python3 - "$QA" <<'PY'
import json, os, sys, time
qa = sys.argv[1]
json.dump({'vaults': {'72656d61696e6465': {'path': os.path.join(qa, 'vault'), 'ts': int(time.time() * 1000),
                                           'open': True}}},
          open(os.path.join(qa, 'config', 'obsidian', 'obsidian.json'), 'w'))
PY
  VAULTS="
$QA/vault"
  SYNC=keep
fi

# --- 1. the vaults ---------------------------------------------------------------------------------
# One line per vault: label|folder. The label names the backup, so it is the vault's own id where Obsidian
# gave it one. PLATFORM.md Obsidian records where each packaging keeps obsidian.json. A vault Obsidian lists
# that is no longer on disk is reported and skipped.
FOUND=$(python3 - "$VAULTS" "$HOME" "${XDG_CONFIG_HOME:-$HOME/.config}" <<'PY'
import hashlib, json, os, sys
asked, home, xdg = sys.argv[1], sys.argv[2], sys.argv[3]
out, seen, gone = [], set(), []
def add(label, path):
    path = os.path.realpath(os.path.expanduser(path))
    if path in seen:
        return
    seen.add(path)
    if os.path.isdir(path):
        out.append(f'{label or "vault-" + hashlib.sha1(path.encode()).hexdigest()[:16]}|{path}')
    else:
        gone.append(path)
if asked.strip():
    for p in asked.split('\n'):
        if p.strip():
            add('', p.strip())
else:
    for root in (os.path.join(xdg, 'obsidian'),
                 os.path.join(home, '.var/app/md.obsidian.Obsidian/config/obsidian'),
                 os.path.join(home, 'snap/obsidian/current/.config/obsidian')):
        try:
            vaults = json.load(open(os.path.join(root, 'obsidian.json'), encoding='utf-8')).get('vaults', {})
        except (OSError, ValueError):
            continue
        for vid, v in vaults.items():
            if isinstance(v, dict) and v.get('path'):
                add(vid, v['path'])
for g in gone:
    print(f'remainder: skipping {g}: not a folder on disk', file=sys.stderr)
print('\n'.join(out))
PY
)
if [ -z "$FOUND" ]; then
  if [ -n "$VAULTS" ]; then
    say "no vault to install into: none of the --vault folders exists" >&2
  else
    say "no vault found: Obsidian lists none in obsidian.json (looked under ${XDG_CONFIG_HOME:-~/.config}/obsidian," >&2
    say "the Flatpak and the Snap). To install into one folder:  sh $0 --vault DIR" >&2
  fi
  exit 1
fi

# --- 2. the question, asked before anything is written ----------------------------------------------
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
SYNC_ON=$(printf '%s\n' "$FOUND" | while IFS='|' read -r label dir; do
  [ -n "$label" ] || continue
  python3 -c 'import json,sys
try: print(sys.argv[1] if json.load(open(sys.argv[2])).get("sync") else "")
except Exception: print("")' "$dir" "$dir/.obsidian/core-plugins.json"
done | sed '/^$/d')
if [ -n "$SYNC_ON" ] && [ -z "$SYNC" ] && [ "$ASK" = 1 ]; then
  cat <<Q
remainder: Obsidian ships its Sync plugin switched on, and with no Sync account connected it shows a red
           status icon on every screen. It is on in:
$(printf '%s\n' "$SYNC_ON" | sed 's/^/             /')
           If you use Obsidian Sync in any of these, answer no: turning it off stops syncing there. This
           script cannot tell, because Sync keeps its connection in Obsidian's own storage, not in the vault.
Q
  if yesno "Turn the Sync plugin off in those vaults?" n; then SYNC=off; else SYNC=keep; fi
fi
[ -n "$SYNC" ] || SYNC=keep

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 3. per vault: the theme, the snippet, the settings ---------------------------------------------
printf '%s\n' "$FOUND" | while IFS='|' read -r LABEL DIR; do
  [ -n "$LABEL" ] || continue
  CFG="$DIR/.obsidian"
  mkdir -p "$CFG/themes" "$CFG/snippets"
  rm -rf "$CFG/themes/Remainder"
  cp -R "$HERE/Remainder" "$CFG/themes/Remainder"
  if [ "$DECLUTTER" = 1 ]; then
    cp "$HERE/remainder-declutter.css" "$CFG/snippets/remainder-declutter.css"
  fi
  python3 - "$CFG" "$STATE" "$LABEL" "$HERE/appearance.json" "$DECLUTTER" "$SYNC" <<'PY'
import json, os, re, shutil, sys
cfg, state, label, kit_file, declutter, sync = sys.argv[1:7]
strip = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.S)
def jsonc(text):
    s = strip.sub(lambda m: m.group(1) or '', text)
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', s) or '{}')
def load(p):
    try: return json.load(open(p, encoding='utf-8'))
    except (OSError, ValueError): return {}
def save(p, obj):                      # the whole file at once: Obsidian watches it
    tmp = p + '.remainder.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(obj, f, indent=2); f.write('\n')
    os.replace(tmp, p)
def backup(p, name):                   # first run only, so a re-run never overwrites the original
    dest = os.path.join(state, name)
    if os.path.exists(p) and not os.path.exists(dest):
        shutil.copy2(p, dest); print(f'remainder: saved {p} -> {dest}')
app = os.path.join(cfg, 'appearance.json')
backup(app, f'obsidian.{label}.appearance.json')
user, kit = load(app), jsonc(open(kit_file, encoding='utf-8').read())
if declutter == '1':
    snippets = list(user.get('enabledCssSnippets') or [])
    if 'remainder-declutter' not in snippets:
        snippets.append('remainder-declutter')
    kit['enabledCssSnippets'] = snippets
changed = sorted(k for k, v in kit.items() if user.get(k) != v)
user.update(kit)
save(app, user)
print(f'remainder: [{os.path.dirname(cfg)}] theme in place; appearance.json: '
      + (', '.join(changed) if changed else 'already set'))
if sync == 'off':
    core = os.path.join(cfg, 'core-plugins.json')
    plugins = load(core)
    if isinstance(plugins, dict) and plugins.get('sync'):
        backup(core, f'obsidian.{label}.core-plugins.json')
        plugins['sync'] = False
        save(core, plugins)
        print(f'remainder: [{os.path.dirname(cfg)}] the Sync plugin is off (§0); Settings > Core plugins turns it back on')
PY
done

# --- 4. the fonts §5 declares, which this installer does not fetch ------------------------------------
# One installer owns the checksums (CONTRIBUTING.md §12): worksafe/cosmic/install.sh --fonts. fontconfig
# lists a face under every name it has -- "Montserrat,Montserrat Medium" -- so a family is matched as one
# entry of that comma-separated list, not as the whole line.
missing=''
for f in Montserrat Hack; do
  fc-list : family 2>/dev/null | grep -qiE "(^|,)$f(,|\$)" || missing="$missing $f"
done
[ -n "$missing" ] && say "font(s) not installed:$missing -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"

# --- 5. what happened ---------------------------------------------------------------------------------
[ "$DECLUTTER" = 1 ] && D="the declutter snippet on (§0)" || D="the declutter left off (--no-declutter)"
[ "$SYNC" = off ] && Y="Sync off where it was on" || Y="Sync left as it was"
if [ -n "$QA" ]; then cat <<MSG
remainder: the QA profile is at $QA. Open it, with DevTools on a port of its own, and read what it paints:
             XDG_CONFIG_HOME=$QA/config obsidian --remote-debugging-port=9223
             python3 $KIT/build/obsidian.py --screen 9223
MSG
  exit 0
fi
cat <<MSG
remainder: Remainder installed; $D; $Y. What was replaced is in $STATE
           An open Obsidian applies it at once. The top strip is the key titlebar and goes LIGHT when the
           window is not key -- the second surface on this desktop that can show it (PLATFORM.md).
MSG
