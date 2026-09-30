#!/bin/sh
# Remainder for Vivaldi — per-user install. No sudo, nothing outside $HOME. (worksafe tier)
# Implements AUTHORITY.md §0, §2, §3, §5 and PLATFORM.md Vivaldi. Re-runnable, and it backs up what it replaces.
#
# Usage: sh install.sh [--user-data-dir DIR]... [--qa DIR] [--no-declutter] [--no-ask]
#
# Vivaldi keeps its settings in a user-data directory -- ${XDG_CONFIG_HOME:-~/.config}/vivaldi for the Arch, deb and
# rpm builds, vivaldi-snapshot beside it for the snapshot, ~/.var/app/com.vivaldi.Vivaldi/config/vivaldi for the
# Flatpak -- holding Local State and one folder per profile (Default, Profile 1, ...). For each profile this adds the
# Remainder theme to Settings > Themes and selects it, copies the interface stylesheet (remainder.css) and the
# declutter (remainder-declutter.css) into the folder Vivaldi loads interface stylesheets from, and merges
# settings.json into Preferences; in Local State it switches on the experiment that loads those
# stylesheets, vivaldi://experiments > "Allow CSS modifications". Both files are saved under
# ~/.local/state/remainder on the first run. Undo it by selecting another theme in Settings > Themes -- the
# stylesheet is scoped to Remainder and paints nothing under any other -- or by putting the saved files back.
#
#   --user-data-dir DIR  this user-data directory only (repeatable): for a Vivaldi you start with --user-data-dir.
#   --qa DIR             a QA profile at DIR, to look at a change without touching yours: DIR/profile, set up past
#                        Vivaldi's first-run pages and installed into. The commands that open it on a display of
#                        its own and read what it paints are printed.
#   --no-declutter       paint only: the theme, and not the stylesheet that removes motion and blur, nor the
#                        settings that switch off the tips, nags and promotions, so §0's larger half stays where the
#                        platform put it.
#   --no-ask             accepted for parity with the other installers; nothing is asked anyway.
#
# Vivaldi must be closed. It keeps Preferences and Local State in memory and writes them back when it quits, so a
# running Vivaldi would undo all of this (PLATFORM.md Vivaldi).
set -e

DECLUTTER=1; DIRS=''; QA=''
while [ $# -gt 0 ]; do
  case "$1" in
    --user-data-dir) shift; DIRS="$DIRS
$1" ;;
    --user-data-dir=*) DIRS="$DIRS
${1#--user-data-dir=}" ;;
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
remainder: refusing to run under sudo -- this is a per-user install and under sudo it is not your Vivaldi.
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
# A user-data directory of Vivaldi's own is one flag away and runs beside yours: the single-instance lock lives in
# the directory. Vivaldi's own first-run pages -- the setup wizard, the welcome tab -- are marked read, so the first
# window is the browser; everything else Vivaldi fills in with its defaults when it starts.
if [ -n "$QA" ]; then
  mkdir -p "$QA/profile/Default"
  QA=$(cd "$QA" && pwd)
  VERSION=$(vivaldi --version 2>/dev/null | sed -n 's/^Vivaldi \([0-9.]*\).*/\1/p')
  [ -n "$VERSION" ] || { say "vivaldi --version printed no version: is Vivaldi installed as \`vivaldi\`?" >&2; exit 1; }
  python3 - "$QA/profile" "$VERSION" <<'PY'
import json, os, sys
udd, version = sys.argv[1], sys.argv[2]
ls = os.path.join(udd, 'Local State')
if not os.path.exists(ls):
    json.dump({'browser': {'enabled_labs_experiments': []}, 'profile': {'info_cache': {'Default': {'name': 'QA'}}}},
              open(ls, 'w'))
prefs = os.path.join(udd, 'Default', 'Preferences')
if not os.path.exists(prefs):
    json.dump({'vivaldi': {
        'welcome': {'read_pages': ['intro', 'a11y_settings', 'account', 'control', 'import_data', 'tracker_and_ad',
                                   'layouts', 'personalize', 'panel_internal', 'panel_apps', 'welcome_feature_amount']},
        'startup': {'has_seen_welcome_page': True, 'first_seen_version': version, 'last_seen_version': version}}},
        open(prefs, 'w'))
PY
  DIRS="
$QA/profile"
  STATE="$QA/state"      # a QA profile is disposable: what it replaces is kept inside it, not beside yours
fi

# --- 1. the user-data directories and their profiles --------------------------------------------------------
# One line per profile: label|user-data dir|profile folder. The label names the backups. A directory counts once
# Vivaldi has run in it and written Local State: before that there is nothing to merge into.
FOUND=$(python3 - "$DIRS" "$HOME" "${XDG_CONFIG_HOME:-$HOME/.config}" <<'PY'
import hashlib, json, os, sys
asked, home, xdg = sys.argv[1], sys.argv[2], sys.argv[3]
out, seen = [], set()
def add(label, path):
    path = os.path.realpath(os.path.expanduser(path))
    if path in seen:
        return
    seen.add(path)
    ls = os.path.join(path, 'Local State')
    if not os.path.isfile(ls):
        if asked.strip():
            print(f'remainder: skipping {path}: no Local State there -- start Vivaldi with it once, then run this '
                  'again', file=sys.stderr)
        return
    label = label or 'dir-' + hashlib.sha1(path.encode()).hexdigest()[:12]
    profiles = sorted((json.load(open(ls)).get('profile') or {}).get('info_cache') or {'Default': {}})
    for p in profiles:
        if os.path.isdir(os.path.join(path, p)):
            out.append(f'{label}|{path}|{p}')
if asked.strip():
    for p in asked.split('\n'):
        if p.strip():
            add('', p.strip())
else:
    add('native', os.path.join(xdg, 'vivaldi'))
    add('snapshot', os.path.join(xdg, 'vivaldi-snapshot'))
    add('flatpak', os.path.join(home, '.var/app/com.vivaldi.Vivaldi/config/vivaldi'))
print('\n'.join(out))
PY
)
if [ -z "$FOUND" ]; then
  if [ -n "$DIRS" ]; then
    say "no user-data directory to install into" >&2
  else
    say "found no Vivaldi user-data directory with a Local State in it (looked in ${XDG_CONFIG_HOME:-~/.config}/vivaldi," >&2
    say "vivaldi-snapshot and the Flatpak's). Start Vivaldi once and quit it, then run this again; or:" >&2
    say "  sh $0 --user-data-dir DIR" >&2
  fi
  exit 1
fi

# --- 2. Vivaldi must be closed --------------------------------------------------------------------------------
# Not politeness: Vivaldi writes Preferences and Local State back from memory when it quits, which would undo the
# merge. The process is `vivaldi-bin` whichever directory it runs in, so the name cannot say which one is open;
# Chromium's own lock can. A running browser holds SingletonLock in its user-data directory, a symlink to
# "host-pid", and the lock is live when that pid is.
for UDD in $(printf '%s\n' "$FOUND" | cut -d'|' -f2 | sort -u); do
  LOCK=$(readlink "$UDD/SingletonLock" 2>/dev/null || true)
  PID=${LOCK##*-}
  if [ -n "$PID" ] && [ "${LOCK%-*}" = "$(uname -n)" ] && kill -0 "$PID" 2>/dev/null; then
    say "quit Vivaldi first -- it is running in $UDD (pid $PID), and it writes Preferences and Local State" >&2
    say "         back from memory when it quits. (A QA profile of the kit's own counts too: quit that one as well.)" >&2
    exit 1
  fi
done

mkdir -p "$STATE"        # the first thing this script writes, and not before here

# --- 3. per user-data directory: the experiment; per profile: the theme, the stylesheets, the settings ----------
python3 - "$HERE" "$STATE" "$DECLUTTER" "$FOUND" <<'PY'
import json, os, re, shutil, sys
here, state, declutter = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
strip = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.S)
def jsonc(text):
    s = strip.sub(lambda m: m.group(1) or '', text)
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', s) or '{}')
def backup(p, name):                   # first run only, so a re-run never overwrites the original
    dest = os.path.join(state, name)
    if os.path.exists(p) and not os.path.exists(dest):
        shutil.copy2(p, dest); print(f'remainder: saved {p} -> {dest}')
def replace(p, obj):                   # the whole file at once, the way Chromium writes it: compact
    tmp = p + '.remainder.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, separators=(',', ':'), ensure_ascii=False)
    os.replace(tmp, p)
def merge(dst, src, changed, path=''):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v, changed, f'{path}{k}.')
        elif dst.get(k) != v:
            dst[k] = v; changed.append(path + k)

theme = json.load(open(os.path.join(here, 'theme.json')))
kit = jsonc(open(os.path.join(here, 'settings.json')).read())
if not declutter:                      # paint only: the theme's selection, the wash, the fonts -- none of §0
    t = kit['vivaldi']['theme']
    kit = {'vivaldi': {'themes': kit['vivaldi']['themes'],
                       'theme': {'schedule': t['schedule'], 'dim_blurred': t['dim_blurred']},
                       'settings': {'mono_icons': kit['vivaldi']['settings']['mono_icons']}},
           'webkit': kit['webkit']}
# The shipped toolbars, for the one promotion that lives in a toolbar: the VPN button. A toolbar the user has
# never changed is not in Preferences at all, so its default is read off the installed build.
defaults = {}
for p in ('/opt/vivaldi/resources/vivaldi/prefs_definitions.json',
          '/opt/vivaldi-snapshot/resources/vivaldi/prefs_definitions.json'):
    if os.path.exists(p):
        tb = json.load(open(p)).get('vivaldi', {}).get('toolbars', {})
        defaults = {k: v.get('default') for k, v in tb.items() if isinstance(v, dict) and isinstance(v.get('default'), list)}
        break

rows = [l.split('|') for l in sys.argv[4].split('\n') if l.strip()]
if not rows:
    sys.exit('remainder: no profile reached the install step -- this is a bug in install.sh')
for udd in sorted({r[1] for r in rows}):
    label = next(r[0] for r in rows if r[1] == udd)
    ls_path = os.path.join(udd, 'Local State')
    backup(ls_path, f'vivaldi.{label}.Local State')
    ls = json.load(open(ls_path))
    exps = [e for e in ls.setdefault('browser', {}).get('enabled_labs_experiments', [])
            if not e.startswith('vivaldi-css-mods@')]
    ls['browser']['enabled_labs_experiments'] = exps + ['vivaldi-css-mods@1']
    replace(ls_path, ls)
    print(f'remainder: [{udd}] the experiment "Allow CSS modifications" is on (Local State)')

for label, udd, profile in rows:
    pdir = os.path.join(udd, profile)
    prefs_path = os.path.join(pdir, 'Preferences')
    if not os.path.exists(prefs_path):
        print(f'remainder: [{pdir}] no Preferences yet -- start Vivaldi with this profile once, then run this again')
        continue
    backup(prefs_path, f'vivaldi.{label}.{profile}.Preferences')
    prefs = json.load(open(prefs_path))
    v = prefs.setdefault('vivaldi', {})
    changed = []

    # the stylesheet folder: the one this profile already names, or the kit's own beside the profiles
    app = v.setdefault('appearance', {})
    mods = app.get('css_ui_mods_directory') or ''
    if not (mods and os.path.isdir(mods)):
        mods = os.path.join(udd, 'remainder-ui')
        os.makedirs(mods, exist_ok=True)
        if app.get('css_ui_mods_directory') != mods:
            app['css_ui_mods_directory'] = mods; changed.append('vivaldi.appearance.css_ui_mods_directory')
    shutil.copy2(os.path.join(here, 'remainder.css'), os.path.join(mods, 'remainder.css'))
    decl = os.path.join(mods, 'remainder-declutter.css')
    if declutter:
        shutil.copy2(os.path.join(here, 'remainder-declutter.css'), decl)
    elif os.path.exists(decl):
        os.remove(decl)

    # the theme entry, replacing an earlier one of the kit's
    themes = v.setdefault('themes', {})
    before = themes.get('user', [])
    after = [t for t in before if t.get('id') != theme['id']] + [theme]
    if after != before:
        themes['user'] = after; changed.append('vivaldi.themes.user')
    merge(prefs, kit, changed)

    if declutter:                      # §0: the VPN button, a promotion, out of every toolbar that carries it
        tb = v.setdefault('toolbars', {})
        for name in sorted(set(tb) | set(defaults)):
            items = tb.get(name, defaults.get(name))
            if isinstance(items, list) and 'VPNButton' in items:
                tb[name] = [i for i in items if i != 'VPNButton']; changed.append(f'vivaldi.toolbars.{name}')

    replace(prefs_path, prefs)
    print(f'remainder: [{pdir}] the theme is selected and its stylesheet is in {mods}; Preferences: '
          + (', '.join(changed) if changed else 'already set'))
PY

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
[ "$DECLUTTER" = 1 ] && D="the declutter too (§0)" || D="the declutter left out (--no-declutter)"
if [ -n "$QA" ]; then cat <<MSG
remainder: the QA profile is at $QA/profile. Open it on a display of its own, with DevTools on a port of its own, and
           read what it paints:
             Xvfb :77 -screen 0 1600x1000x24 -nolisten tcp &
             env -u WAYLAND_DISPLAY DISPLAY=:77 vivaldi --user-data-dir=$QA/profile --ozone-platform=x11 \\
                 --remote-debugging-port=9225
             python3 $KIT/build/vivaldi.py --screen 9225
MSG
  exit 0
fi
cat <<MSG
remainder: Remainder installed; $D. What was replaced is in $STATE
           Start Vivaldi: Settings > Themes shows Remainder selected. To go back, select another theme there.
MSG
