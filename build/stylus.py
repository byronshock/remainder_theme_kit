"""The all-sites sheet: check what is committed. AUTHORITY.md is the authority.

elevated/remainder.user.css is the kit's third surface and the only one whose reach is every site, which is
the whole reason it is in the elevated tier: Firefox hands an all-sites sheet to a per-profile extension, so
it asks for no privilege at all (CONTRIBUTING.md §1). Reach, not privilege, puts it there.

It reads as CSS like worksafe/firefox/, keeps the same invariant -- the only literal colours in it are the
--rm-* definitions -- and is read with the same parser, imported rather than restated. What it needs that the
chrome sheet did not is a check on the other side of the line:

  CONTENT IS NEVER PAINTED (§0a). The chrome sheet could not touch content, because chrome is all it can
  reach. This one can reach everything, so the exemption has to be enforced rather than assumed: no rule may
  give an authored colour to an img, video, canvas, picture, svg, iframe, embed or object. Restoring one --
  `color: inherit`, `filter: none` -- is not painting it, and is what the sheet does instead. A selector that
  only excludes a content tag inside :not() is not painting it either, which is why :not() is stripped before
  the check: the ground rule's whole job is that exclusion list.

  THE IMPORT FILE MATCHES THE SOURCE. Stylus imports its own JSON and balks at *.user.css, so the kit ships
  both and the generated one is committed (§11). Same shape as palette.json's invariant in §7: the committed
  file has to be what the generator produces. One field is allowed to differ -- installDate is a timestamp
  taken at generation, so it is compared out, exactly as build/stylus_json.py --check does.

  THE HEADER IS THE CHANGELOG. §11 makes bumping @version and writing what the change fixed part of editing
  the sheet, so the checker reads both back: a @version with no line about it in the header is a change
  nobody wrote down.

    python3 build/stylus.py             check every value, pair and rule in the sheet
    python3 build/stylus.py --derive    the roles the sheet may name, and the pairs it authors
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ok, poles as P, apca, firefox as F, stylus_json

ROOT = F.ROOT
SHEET = os.path.join(ROOT, 'elevated', 'remainder.user.css')
JSON_OUT = os.path.join(ROOT, 'elevated', 'remainder.stylus.json')
ROLES, RESERVED, SEMANTIC_ROLES = F.ROLES, F.RESERVED, F.SEMANTIC_ROLES
FLOOR = F.FLOOR

# Pairs no single rule block states, because the text and its ground are set in different rules -- a link
# is coloured once and lands on whatever surface it sits on. Named here so they are measured rather than
# assumed, with APCA's tier for what each carries: a link and typed text are read, a caret and a focus ring
# are marks. The nav-link entry is the one that changed the sheet: ACCENT on LIGHT is Lc 44.8, so a link in
# a navigation takes the field's own pair instead and is not in this table at all.
PAIRS = [
    ('accent', 'white', 75, 'a link in running text on the page ground (§3 keeps the underline)'),
    ('cursor', 'white', 30, 'the caret in a well on a field'),
    ('cursor', 'light', 30, 'the caret in a well on a document'),
    ('accent', 'white', 30, 'the focus ring on a document'),
    ('accent', 'light', 30, 'the focus ring on a field'),
    ('dark', 'white', 60, 'a placeholder in a well on a field'),
    ('dark', 'light', 30, 'a placeholder in a well on a document'),
    ('black', 'light', 60, 'a navigation link, which is a field label and not prose'),
]

# §0a's list, and it is the whole list. An element here is information by anyone's reckoning.
CONTENT = ('img', 'video', 'canvas', 'picture', 'svg', 'iframe', 'embed', 'object', 'source', 'audio')
COLOUR_PROPS = ('color', 'background', 'background-color', 'fill', 'stroke', 'border-color',
                'outline', 'outline-color', 'caret-color', 'text-decoration-color', '-webkit-text-fill-color')
NOT = re.compile(r':not\([^)]*\)')
# §5 declares the rule's reference width, and the sheet is the one place in the kit that draws it in pixels.
RULE_PX = 22


def _subjects(sel):
    """The tags a selector actually targets, with every :not() argument removed first."""
    return set(re.findall(r'(?:^|[\s>+~,])([a-z]+)(?=$|[\s>+~,:.\[])', NOT.sub(' ', sel)))


def check():
    if not os.path.exists(SHEET):
        print('stylus: elevated/remainder.user.css is not committed yet'); return False
    defs, tokens, blocks, defects, named = F.read_sheet(SHEET)
    bad, notes = 0, list(defects)
    bad += len(defects)
    src = open(SHEET, encoding='utf-8').read()

    # --- the header (§11) ---------------------------------------------------------------------------
    name = re.search(r'@name\s+(.+)', src)
    version = re.search(r'@version\s+(\S+)', src)
    if not name or not version:
        notes.append('the header has no @name or no @version -- build/stylus_json.py cannot read it'); bad += 1
    else:
        v = version.group(1)
        print(f"{name.group(1).strip()} {v}")
        if not re.search(r'^\s*' + re.escape(v) + r':', src, re.M):
            notes.append(f'@version {v} has no line in the header changelog saying what it changed (§11)')
            bad += 1
    prefixes = re.findall(r'url-prefix\("([^"]+)"\)', src)
    print(f"reach: {', '.join(prefixes) or 'NONE -- an all-sites sheet that matches nothing'}")
    if not prefixes:
        bad += 1

    # --- every literal is a value the kit authors --------------------------------------------------
    print(f"\n--rm-* definitions: {len(defs)}")
    for nm in sorted(defs):
        hx, want = defs[nm], ROLES.get(nm)
        note = ''
        if want is None:
            note = 'NOT A ROLE THE KIT AUTHORS'; bad += 1
        elif hx != want.upper():
            note = f'does not match palette.json ({want})'; bad += 1
        elif P.reserved(hx) and nm not in RESERVED:
            note = 'reserved by §3'; bad += 1
        if nm not in RESERVED and nm not in SEMANTIC_ROLES and not P.clear(hx):
            note = (note + ' POLE: chrome must clear every pole').strip(); bad += 1
        fam, gap, req = P.clearance(hx)
        tag = 'neutral' if not P.readable(hx) else f'{gap:5.1f}/{req:4.1f} {fam}'
        print(f"  --rm-{nm:13} {hx}  {tag:26} {note}")

    # §5: the rule has one width and this sheet draws it.
    m = re.search(r'--rm-rule:\s*(\d+)px', src)
    if not m:
        notes.append('the sheet draws no rule -- §5 gives hr the rule width'); bad += 1
    elif int(m.group(1)) != RULE_PX:
        notes.append(f'--rm-rule is {m.group(1)}px; §5 declares {RULE_PX}'); bad += 1

    # --- content is never painted (§0a) ------------------------------------------------------------
    painted = []
    for sel, decls, rel in blocks:
        subj = _subjects(sel) & set(CONTENT)
        if not subj:
            continue
        for prop, val in decls:
            if prop in COLOUR_PROPS and F.VAR.search(val):
                painted.append(f'{sel[:60]} gives {prop} an authored colour, and {"/".join(sorted(subj))} is content (§0a)')
    print(f"\ncontent (§0a): {len(CONTENT)} tags the sheet may never paint")
    for x in painted:
        notes.append(x); bad += 1
    if not painted:
        print("  no rule gives one an authored colour; the ones that name them restore instead")

    # --- the pairs the sheet authors ---------------------------------------------------------------
    # Same machinery as the chrome sheet: both sides read out of the file, the floor taken from the weight
    # the rule itself sets. DARK is §2's disabled and secondary value and is authored weak on purpose.
    print(f"\npairs the rule blocks author (APCA Lc, signed):")
    for where, tr, gr, weight in F.block_pairs(blocks, defs):
        lc = apca.lc(ROLES[tr], ROLES[gr])
        floor = 30 if tr == 'dark' else (60 if weight == 700 else 75)
        okay = abs(lc) >= floor
        bad += not okay
        if tr in RESERVED and gr not in SEMANTIC_ROLES:
            notes.append(f'{where}: §3 reserves {ROLES[tr]} for legend on a semantic field'); bad += 1
        print(f"  {tr:12} on {gr:12} Lc {lc:7.1f}  floor {floor:3.0f}  /{weight}  "
              f"{'ok ' if okay else 'LOW'}  {where.split('  ', 1)[-1][:52]}")

    print(f"\npairs set in two places, named here so they are measured (APCA Lc, signed):")
    for t, g, floor, why in PAIRS:
        lc = apca.lc(ROLES[t], ROLES[g])
        okay = abs(lc) >= floor
        bad += not okay
        print(f"  {t:12} on {g:12} Lc {lc:7.1f}  floor {floor:3.0f}        {'ok ' if okay else 'LOW'}  {why}")

    # --- the surfaces that nest, and the floor between them ----------------------------------------
    # The sheet alternates: a well or a button on a document is LIGHT, the same thing on a field is WHITE.
    # Both boundaries are the one §2 derives its floor from, so both are exactly at it.
    print(f"\nsurfaces that nest (OKLab dE; floor {FLOOR}):")
    for a, b, why in (('white', 'light', 'a field or panel on the page ground'),
                      ('light', 'white', 'a well or button on a document'),
                      ('white', 'select', 'the selected row of a list'),
                      ('light', 'select', 'the selected row on a field'),
                      ('white', 'accent', 'the focus ring, and a primary button'),
                      ('light', 'accent', 'a primary button on a field')):
        d = ok.delta_e(ROLES[a], ROLES[b])
        okay = d >= FLOOR - 0.05
        bad += not okay
        print(f"  {a:8} / {b:8} dE {d:5.1f}  {'ok ' if okay else 'BELOW'}  {why}")

    # --- the import file is what the generator produces (§11) --------------------------------------
    print("\nthe Stylus import file:")
    if not os.path.exists(JSON_OUT):
        notes.append('elevated/remainder.stylus.json is not committed -- Stylus balks at *.user.css (§11)')
        bad += 1
    else:
        gen = stylus_json.build(SHEET)[0]
        have = json.load(open(JSON_OUT, encoding='utf-8'))[0]
        a = {**gen, 'installDate': 0}
        b = {**have, 'installDate': 0}
        if a == b:
            print("  matches the source; installDate is a timestamp and is compared out")
        else:
            for k in a:
                if a.get(k) != b.get(k):
                    notes.append(f'remainder.stylus.json is stale in "{k}" -- run python3 build/stylus_json.py')
                    bad += 1

    if notes:
        print('\nnotes:')
        for n in notes:
            print(f'  {n}')
    print(f"\nstylus: {'every value, pair and rule clears' if not bad else str(bad) + ' DEFECT(S)'}")
    return bad == 0


def _print_derivations():
    print("=== the roles the sheet may name, and nothing else ===")
    for nm in sorted(ROLES):
        hx = ROLES[nm]
        fam, gap, req = P.clearance(hx)
        tag = ('reserved for legend (§3)' if nm in RESERVED else
               'a pole by construction (§3)' if nm in SEMANTIC_ROLES else
               'neutral, no readable hue' if not P.readable(hx) else
               f'clears {gap:.1f}deg from {fam}, needs {req:.1f}')
        print(f"  --rm-{nm:13} {hx}  {tag}")
    print(f"\n=== pairs set in two places, which no rule block states ===")
    for t, g, floor, why in PAIRS:
        print(f"  {t:7} on {g:7} Lc {apca.lc(ROLES[t], ROLES[g]):7.1f}  floor {floor:3.0f}   {why}")
    print(f"\n=== the rule (§5) ===")
    print(f"  hr is {RULE_PX}px of BLACK. §5's reference width is 22 dp/pt, a 44 pt hit box; the parent")
    print(f"  kit's 28 came from measuring its painting, and there is no painting here (§5).")


if __name__ == '__main__':
    if '--derive' in sys.argv:
        _print_derivations(); sys.exit(0)
    sys.exit(0 if check() else 1)
