"""Generate the Remainder overlay icon theme (AUTHORITY.md §4).

Finds every application's real icon the way the desktop does — the .desktop file's Icon= name, resolved
through the platform's icon-theme chain — projects each pixel to the nearest of the seven values the kit
authors (build/remainder_space.py: §2's four-step ladder plus ACCENT, SELECT and CURSOR, flat, with the
gray guard and the 3x3 edge vote), and writes an icon theme that ships only the Applications context and
inherits the platform's own theme for everything else. Alpha is kept.

Discovery is the parent kit's, carried over unchanged: which .desktop files exist, how the icon-theme
chain resolves a name, which entries the panel shows. That half is theme-independent, the same way
PLATFORM.md is, and rediscovering it would be expensive for nothing. Only the projection is this kit's.
The generator authors nothing: an icon the chain cannot find is skipped, and an Icon= that is an absolute
path (Zed, NVIDIA tools) cannot be overridden by any theme and is reported.

Not committed: the output is the user's brands in the user's own paint, made at install time.

    python3 build/icon_theme.py --out ~/.local/share/icons/remainder [--inherits Cosmic,Pop,Adwaita,hicolor]
                                 [--names a,b,c] [--sizes 32,48,64,96,128,144,192,256] [--lookup Cosmic,Pop,Adwaita,hicolor]
                                 [--anchors all|neutral]
Needs Pillow, numpy, cairosvg. `--anchors neutral` drops the three chrome hues; see remainder_space.py
for why that escape hatch exists (CURSOR is a locator, and teal in a dock icon spends some of that).
"""
import argparse, configparser, glob, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import remainder_space as rs

HOME = os.path.expanduser('~')
DATA_DIRS = [os.environ.get('XDG_DATA_HOME', os.path.join(HOME, '.local/share'))] + \
            [d for d in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if d] + \
            ['/var/lib/flatpak/exports/share', os.path.join(HOME, '.local/share/flatpak/exports/share'), '/var/lib/snapd/desktop']
ICON_BASES = [os.path.join(d, 'icons') for d in DATA_DIRS] + [os.path.join(HOME, '.icons')]
APP_DIRS = [os.path.join(d, 'applications') for d in DATA_DIRS]


def desktop_icons(hidden_prefixes=('com.system76.',)):
    """{icon name: desktop file} for visible applications; absolute Icon= paths returned separately.
    Hidden (NoDisplay) entries are skipped unless their icon carries a hidden_prefix: the desktop's own
    panel and dock applets (launcher, workspaces, app library) are NoDisplay but on screen all day."""
    names, absolute = {}, []
    for d in APP_DIRS:
        for f in sorted(glob.glob(os.path.join(d, '*.desktop'))):
            cp = configparser.RawConfigParser(strict=False, interpolation=None)
            try: cp.read(f, encoding='utf-8')
            except Exception: continue
            if not cp.has_section('Desktop Entry'): continue
            e = cp['Desktop Entry']
            if e.get('Type', '') != 'Application': continue
            ic = e.get('Icon', '').strip()
            if not ic: continue
            if e.get('NoDisplay', 'false').lower() == 'true' and not ic.startswith(tuple(hidden_prefixes)): continue
            (absolute.append((os.path.basename(f), ic)) if ic.startswith('/') else names.setdefault(ic, os.path.basename(f)))
    return names, absolute


def theme_chain(names):
    """Themes in lookup order, following each index.theme's Inherits, no repeats."""
    out, seen = [], set()
    def visit(n):
        if n in seen: return
        seen.add(n); out.append(n)
        for base in ICON_BASES:
            idx = os.path.join(base, n, 'index.theme')
            if os.path.exists(idx):
                cp = configparser.RawConfigParser(strict=False, interpolation=None); cp.read(idx, encoding='utf-8')
                for inh in cp.get('Icon Theme', 'Inherits', fallback='').split(','):
                    if inh.strip(): visit(inh.strip())
                break
    for n in names: visit(n)
    if 'hicolor' not in seen: out.append('hicolor')
    return out


def find_icon(name, chain):
    """First theme in the chain that has the icon: prefer an SVG, else the largest PNG. Then pixmaps."""
    for theme in chain:
        svg, pngs = None, []
        for base in ICON_BASES:
            root = os.path.join(base, theme)
            if not os.path.isdir(root): continue
            for path in glob.glob(os.path.join(root, '*', '*', name + '.*')) + glob.glob(os.path.join(root, '*', name + '.*')):
                if path.endswith('.svg'): svg = svg or path
                elif path.endswith('.png'):
                    try:
                        from PIL import Image
                        pngs.append((Image.open(path).size[0], path))
                    except Exception: pass
        if svg: return svg
        if pngs: return max(pngs)[1]
    for pm in ('/usr/share/pixmaps', '/usr/local/share/pixmaps'):
        for ext in ('svg', 'png'):
            p = os.path.join(pm, name + '.' + ext)
            if os.path.exists(p): return p
    return None


def load_master(path, px=512):
    from PIL import Image
    if path.endswith('.svg'):
        import cairosvg
        return Image.open(io.BytesIO(cairosvg.svg2png(url=path, output_width=px, output_height=px))).convert('RGBA')
    return Image.open(path).convert('RGBA')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HOME, '.local/share/icons/remainder'))
    ap.add_argument('--inherits', default='Cosmic,Pop,Adwaita,hicolor', help='Inherits= of the written theme')
    ap.add_argument('--lookup', default='Cosmic,Pop,Adwaita,hicolor', help='chain used to find the source art')
    ap.add_argument('--names', default='', help='comma list; default: every visible .desktop Icon=')
    ap.add_argument('--sizes', default='32,48,64,96,128,144,192,256')
    ap.add_argument('--hidden-prefixes', default='com.system76.', help='comma list; hidden .desktop entries with these icon prefixes are included (applets)')
    ap.add_argument('--anchors', default='all', choices=sorted(rs.ANCHOR_SETS), help='all seven values, or the neutral ladder alone')
    a = ap.parse_args()
    from PIL import Image
    sizes = [int(x) for x in a.sizes.split(',')]
    names, absolute = desktop_icons(tuple(x for x in a.hidden_prefixes.split(',') if x))
    wanted = [n for n in a.names.split(',') if n] or sorted(names)
    chain = theme_chain(a.lookup.split(','))
    made, missing = [], []
    for n in wanted:
        src = find_icon(n, chain)
        if not src: missing.append(n); continue
        try: master = load_master(src)
        except Exception as e: missing.append(f'{n} ({e.__class__.__name__})'); continue
        for s in sizes:
            d = os.path.join(a.out, f'{s}x{s}', 'apps'); os.makedirs(d, exist_ok=True)
            im = master.resize((s, s), Image.LANCZOS) if master.size != (s, s) else master
            rs.project_image(im, mode='poster', clean=True, which=a.anchors).save(os.path.join(d, n + '.png'))
        made.append((n, src))
    dirs = ','.join(f'{s}x{s}/apps' for s in sizes)
    with open(os.path.join(a.out, 'index.theme'), 'w') as f:
        anc = ', '.join(rs.ANCHOR_SETS[a.anchors])
        f.write(f'[Icon Theme]\nName=Remainder\nComment=Application icons projected onto the values the kit authors: {anc} (AUTHORITY.md 4)\n'
                f'Inherits={a.inherits}\nDirectories={dirs}\n\n')
        for s in sizes:
            f.write(f'[{s}x{s}/apps]\nSize={s}\nType=Fixed\nContext=Applications\n\n')
    print(f'remainder icons: {len(made)} made in {a.out} at {len(sizes)} sizes; '
          f'anchors={a.anchors}; lookup chain {chain}')
    for n, src in made: print(f'  {n:40} <- {src}')
    if missing: print(f'  not found ({len(missing)}): ' + ', '.join(missing))
    if absolute: print(f'  absolute Icon= paths, not themeable ({len(absolute)}): ' + ', '.join(f'{f} -> {p}' for f, p in absolute))


if __name__ == '__main__':
    main()
