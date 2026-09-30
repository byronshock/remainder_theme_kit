#!/bin/sh
# Remainder for Zettlr — per-user install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md Zettlr. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--data-dir DIR]... [--qa DIR] [--no-declutter] [--no-ask]
#
# Zettlr keeps one stylesheet of the user's own, custom.css, in its data directory -- ${XDG_CONFIG_HOME:-~/.config}/
# Zettlr for the Arch, deb, rpm and AppImage builds, ~/.var/app/com.zettlr.Zettlr/config/Zettlr for the Flatpak --
# and every window loads it last. So this copies the theme (remainder.css) and the declutter (remainder-declutter.css)
# into that directory and puts two @import lines at the top of custom.css, between markers: whatever CSS you keep
# there stays yours, below the block, and still wins over the kit's. It merges four settings into config.json, and
# it saves both files under ~/.local/state/remainder on the first run. Undo it by deleting the block from custom.css
# -- Zettlr's own editor for that file is Assets Manager > Custom CSS -- or by putting the saved files back.
#
#   --data-dir DIR  this data directory only (repeatable): for a Zettlr you start with --data-dir=DIR yourself.
#   --qa DIR        a QA profile at DIR, to look at a change without touching yours: DIR/config/Zettlr holding the
#                   theme and a config that opens DIR/notes/QA.md, a note with every kind of block Zettlr renders.
#                   The command that opens it, and the one that reads what it paints, are printed.
#   --no-declutter  paint only: the theme, and not the stylesheet that removes motion, so §0's larger half stays
#                   where the platform put it.
#   --no-ask        accepted for parity with the other installers; nothing is asked anyway.
#
# Zettlr must be closed. It keeps config.json in memory and writes it back when it quits, and it reads custom.css
# when a window opens, so a running Zettlr would undo the settings and not show the theme (PLATFORM.md Zettlr).
set -e

DECLUTTER=1; DIRS=''; QA=''
while [ $# -gt 0 ]; do
  case "$1" in
    --data-dir) shift; DIRS="$DIRS
$1" ;;
    --data-dir=*) DIRS="$DIRS
${1#--data-dir=}" ;;
    --qa) shift; QA="$1" ;;
    --qa=*) QA="${1#--qa=}" ;;
    --no-declutter) DECLUTTER=0 ;;
    --no-ask) ;;
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
remainder: refusing to run under sudo -- this is a per-user install and under sudo it is not your Zettlr.
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
# Zettlr puts everything under XDG_CONFIG_HOME/Zettlr, its single-instance lock included, so a profile of its own
# is one variable away and runs beside yours. (--data-dir would not do: Zettlr takes the lock before it reads that
# flag, so a second instance started with it finds yours running and exits -- PLATFORM.md Zettlr.) The config
# names the installed version, or Zettlr would take the profile for a first start and open its onboarding window.
if [ -n "$QA" ]; then
  mkdir -p "$QA/config/Zettlr" "$QA/notes/sub"
  QA=$(cd "$QA" && pwd)
  VERSION=$(zettlr --version 2>/dev/null | sed -n 's/^Zettlr //p')
  [ -n "$VERSION" ] || { say "zettlr --version printed no version: is Zettlr installed as \`zettlr\`?" >&2; exit 1; }
  [ -f "$QA/notes/QA.md" ] || cat > "$QA/notes/QA.md" <<'NOTE'
---
title: "QA note"
keywords:
  - qa
---

# Heading one

Body text with **bold**, _italic_, ==a highlight==, ~~struck~~, `inline code`, a #tag, a [[20260925120000]]
zettelkasten link, a citation [@doe2020], [text marked]{.mark}, and an [external link](https://example.org).

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

```diff
- removed
+ added
```

> [!NOTE]
> A note alert: furniture.

> [!TIP]
> A tip alert: furniture.

> [!IMPORTANT]
> An important alert: furniture.

> [!WARNING]
> A warning alert.

> [!CAUTION]
> A caution alert.

Inline math $e^{i\pi} + 1 = 0$, and display math:

$$
\int_0^1 x^2 \, dx = \frac{1}{3}
$$

A footnote reference.[^1]

<!-- a comment -->

::: {.aside}
A pandoc div.
:::

***

[^1]: The footnote.
NOTE
  [ -f "$QA/notes/second.md" ] || printf '# A second note\n\nWith a #tag, and a link back to [[QA note]].\n' > "$QA/notes/second.md"
  [ -f "$QA/notes/sub/third.md" ] || printf '# In a folder\n\nText.\n' > "$QA/notes/sub/third.md"
  python3 - "$QA" "$VERSION" <<'PY'
import json, os, sys
qa, version = sys.argv[1], sys.argv[2]
cfg = os.path.join(qa, 'config', 'Zettlr')
json.dump({'version': version, 'app': {'openFiles': [], 'openWorkspaces': [os.path.join(qa, 'notes')]},
           'openDirectory': os.path.join(qa, 'notes'), 'system': {'checkForUpdates': False}},
          open(os.path.join(cfg, 'config.json'), 'w'), indent=2)
note = os.path.join(qa, 'notes', 'QA.md')
open(os.path.join(cfg, 'documents.yaml'), 'w').write(
    f'qa:\n  type: leaf\n  id: qa\n  openFiles:\n    - path: {note}\n      pinned: false\n'
    f'  activeFile:\n    path: {note}\n    pinned: false\n')
PY
  DIRS="
$QA/config/Zettlr"
  STATE="$QA/state"      # a QA profile is disposable: what it replaces is kept inside it, not beside yours
fi

# --- 1. the data directories ---------------------------------------------------------------------------
# One line per directory: label|folder. The label names the backups. A directory counts once Zettlr has run in it
# and written config.json: before that there is nothing to merge into, and writing a config first would make its
# first start look like an ordinary one.
FOUND=$(python3 - "$DIRS" "$HOME" "${XDG_CONFIG_HOME:-$HOME/.config}" <<'PY'
import hashlib, os, sys
asked, home, xdg = sys.argv[1], sys.argv[2], sys.argv[3]
out, seen = [], set()
def add(label, path):
    path = os.path.realpath(os.path.expanduser(path))
    if path in seen:
        return
    seen.add(path)
    if os.path.isfile(os.path.join(path, 'config.json')):
        out.append(f'{label or "dir-" + hashlib.sha1(path.encode()).hexdigest()[:12]}|{path}')
    elif asked.strip():
        print(f'remainder: skipping {path}: no config.json there -- start Zettlr with it once, then run this again',
              file=sys.stderr)
if asked.strip():
    for p in asked.split('\n'):
        if p.strip():
            add('', p.strip())
else:
    add('native', os.path.join(xdg, 'Zettlr'))
    add('flatpak', os.path.join(home, '.var/app/com.zettlr.Zettlr/config/Zettlr'))
print('\n'.join(out))
PY
)
if [ -z "$FOUND" ]; then
  if [ -n "$DIRS" ]; then
    say "no data directory to install into" >&2
  else
    say "found no Zettlr data directory with a config.json in it (looked in ${XDG_CONFIG_HOME:-~/.config}/Zettlr and" >&2
    say "the Flatpak's). Start Zettlr once and quit it, then run this again; or:  sh $0 --data-dir DIR" >&2
  fi
  exit 1
fi

# --- 2. Zettlr must be closed -----------------------------------------------------------------------------
# Not politeness: Zettlr writes config.json back from memory when it quits, which would undo the merge, and it
# reads custom.css when a window opens. The packagings name the process differently: `zettlr` for the deb, rpm,
# AppImage and Flatpak, and the system Electron running /usr/lib/zettlr/app.asar for the Arch package.
if [ -z "$QA" ] && { pgrep -x zettlr >/dev/null 2>&1 || pgrep -x Zettlr >/dev/null 2>&1 ||
                     pgrep -f '/zettlr/app\.asar' >/dev/null 2>&1; }; then
  say "quit Zettlr first -- it writes config.json back from memory when it quits, and reads custom.css when a" >&2
  say "         window opens. (A QA profile of the kit's own counts too: quit that one as well.)" >&2
  exit 1
fi

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 3. per directory: the stylesheets, the import block, the settings ----------------------------------
printf '%s\n' "$FOUND" | while IFS='|' read -r LABEL DIR; do
  [ -n "$LABEL" ] || continue
  cp "$HERE/remainder.css" "$DIR/remainder.css"
  if [ "$DECLUTTER" = 1 ]; then
    cp "$HERE/remainder-declutter.css" "$DIR/remainder-declutter.css"
  else
    rm -f "$DIR/remainder-declutter.css"
  fi
  python3 - "$DIR" "$STATE" "$LABEL" "$HERE/config.json" "$DECLUTTER" <<'PY'
import json, os, re, shutil, sys
data, state, label, kit_file, declutter = sys.argv[1:6]
strip = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.S)
def jsonc(text):
    s = strip.sub(lambda m: m.group(1) or '', text)
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', s) or '{}')
def backup(p, name):                   # first run only, so a re-run never overwrites the original
    dest = os.path.join(state, name)
    if os.path.exists(p) and not os.path.exists(dest):
        shutil.copy2(p, dest); print(f'remainder: saved {p} -> {dest}')
def replace(p, text):                  # the whole file at once
    tmp = p + '.remainder.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, p)

# custom.css: the block at the top -- @import has to come before every other rule, and after a @charset -- and
# whatever the user keeps there below it, untouched. A re-run replaces the block and nothing else.
css_path = os.path.join(data, 'custom.css')
backup(css_path, f'zettlr.{label}.custom.css')
css = open(css_path, encoding='utf-8').read() if os.path.exists(css_path) else ''
css = re.sub(r'/\* remainder:begin.*?remainder:end \*/\n?', '', css, flags=re.S)
block = ('/* remainder:begin -- the Remainder theme, put here by worksafe/zettlr/install.sh. Delete this block to go\n'
         '   back to Zettlr\'s own look. Anything you write below it stays yours, and wins over the kit. */\n'
         '@import url("remainder.css");\n'
         + ('@import url("remainder-declutter.css");\n' if declutter == '1' else '')
         + '/* remainder:end */\n')
m = re.match(r'\s*@charset\s+"[^"]*"\s*;\s*\n?', css)
css = (css[:m.end()] + block + css[m.end():]) if m else block + css
replace(css_path, css)

# config.json: the kit's keys, merged into the user's, nested objects key by key.
cfg_path = os.path.join(data, 'config.json')
backup(cfg_path, f'zettlr.{label}.config.json')
user, kit = json.load(open(cfg_path, encoding='utf-8')), jsonc(open(kit_file, encoding='utf-8').read())
changed = []
def merge(dst, src, path=''):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v, f'{path}{k}.')
        elif dst.get(k) != v:
            dst[k] = v; changed.append(path + k)
merge(user, kit)
replace(cfg_path, json.dumps(user, indent=2, ensure_ascii=False) + '\n')
print(f'remainder: [{data}] the theme is imported by custom.css; config.json: '
      + (', '.join(changed) if changed else 'already set'))
PY
done

# --- 4. the fonts §5 declares, which this installer does not fetch ------------------------------------
# One installer owns the checksums (CONTRIBUTING.md §12): worksafe/cosmic/install.sh --fonts. fontconfig lists a
# face under every name it has -- "Montserrat,Montserrat Medium" -- so a family is matched as one entry of that
# comma-separated list, not as the whole line.
missing=''
for f in Montserrat Hack; do
  fc-list : family 2>/dev/null | grep -qiE "(^|,)$f(,|\$)" || missing="$missing $f"
done
[ -n "$missing" ] && say "font(s) not installed:$missing -- run: sh $KIT/worksafe/cosmic/install.sh --fonts"

# --- 5. what happened -------------------------------------------------------------------------------------
[ "$DECLUTTER" = 1 ] && D="the declutter imported too (§0)" || D="the declutter left out (--no-declutter)"
if [ -n "$QA" ]; then cat <<MSG
remainder: the QA profile is at $QA. Open it, with DevTools on a port of its own, and read what it paints:
             XDG_CONFIG_HOME=$QA/config zettlr --remote-debugging-port=9224
             python3 $KIT/build/zettlr.py --screen 9224
MSG
  exit 0
fi
cat <<MSG
remainder: Remainder installed; $D. What was replaced is in $STATE
           Start Zettlr: it reads the theme as each window opens. Your own CSS belongs below the block in
           custom.css (Assets Manager > Custom CSS), where it wins over the kit's.
MSG
