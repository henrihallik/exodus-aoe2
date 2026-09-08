#!/usr/bin/env python3
"""Build Exodus using only the standard library. No dependency on other maps.

Authored macro terrain and paired critical objects; native cosmetic mixing.
The emitted RMS is reconstructed by tests, not trusted just because the
source geometry looks right. Runtime scenery is deliberately not terrain.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import random
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.2"
SIZE = 120
STARTS = [(60, 24), (59, 95)]
TERRAIN = {"sand": 14, "dirt": 6, "grass": 0, "water": 1, "beach": 2,
           "shallows": 4, "palms": 13, "acacia": 50, "cracked": 45}
FORESTS = {13, 50}
OBJECTS = {"gold": 66, "stone": 102, "berries": 59, "sheep": 594,
           "boar": 48, "deer": 65, "relic": 285, "fish": 458,
           "acacia": 1063, "palm": 351, "bush": 1360, "wall": 117,
           "gate": 1323, "torch": 499, "rock": 623, "mountain": 1048,
           "flowers": 334}
LAND_IDS = {name: 500 + i for i, name in enumerate(OBJECTS)}
COLORS = {14: "#caa571", 6: "#b58c58", 0: "#8c9956", 1: "#265e6a",
          2: "#dfc38e", 4: "#74a9a6", 13: "#42674a", 50: "#647042", 45: "#bd995f"}


def rotate(x, y):
    return SIZE - 1 - x, SIZE - 1 - y


def make_layout():
    grid = [[TERRAIN["sand"] for _ in range(SIZE)] for _ in range(SIZE)]

    def pair_tile(x, y, terrain):
        grid[y][x] = terrain
        rx, ry = rotate(x, y)
        grid[ry][rx] = terrain

    def ellipse(cx, cy, rx, ry, terrain):
        for y in range(max(0, cy-ry), min(SIZE, cy+ry+1)):
            for x in range(max(0, cx-rx), min(SIZE, cx+rx+1)):
                if ((x-cx)/rx)**2 + ((y-cy)/ry)**2 <= 1:
                    pair_tile(x, y, terrain)

    # Layered alluvial plain around two compact, protected starting oases.
    ellipse(60, 24, 29, 15, TERRAIN["dirt"])
    ellipse(60, 24, 20, 11, TERRAIN["grass"])
    for cx, cy, rx, ry in [(21, 18, 13, 7), (96, 27, 10, 5), (30, 35, 9, 4)]:
        ellipse(cx, cy, rx, ry, TERRAIN["cracked"])
    # One broad sea, not Deadfall's narrow river. Shores curve inward toward
    # both coastal routes; the longest possible shoreline is still mirrored.
    for y in range(40, 80):
        inset = max(0, 6 - min(y-40, 79-y))
        for x in range(18+inset, 102-inset):
            grid[y][x] = TERRAIN["beach"]
    for y in range(44, 76):
        inset = max(0, 5 - min(y-44, 75-y))
        for x in range(21+inset, 99-inset):
            grid[y][x] = TERRAIN["water"]
    # Match XS hazard bounds exactly. This is always shallow terrain. No
    # false claim of live water->land->water terrain replacement is made.
    for y in range(44, 76):
        for x in range(55, 65):
            grid[y][x] = TERRAIN["shallows"]
    # Paired, irregular, contiguous woodlines. Acacia and palm ONLY.
    for cx, cy, rx, ry, terrain in [
        (45, 22, 5, 7, 50), (77, 20, 6, 5, 13), (55, 9, 12, 4, 13),
        (30, 18, 7, 5, 50), (88, 12, 10, 5, 50), (27, 30, 6, 4, 13),
        (94, 32, 8, 4, 13), (9, 33, 5, 6, 50), (9, 84, 5, 5, 13),
        (30, 4, 9, 3, 50), (107, 13, 6, 5, 13)]:
        ellipse(cx, cy, rx, ry, terrain)

    objects = []
    occupied = set()

    def add(kind, x, y, role="scenery", paired=True):
        for xx, yy in [(x, y)] + ([rotate(x, y)] if paired else []):
            assert (xx, yy) not in occupied, (kind, xx, yy)
            occupied.add((xx, yy))
            objects.append({"kind": kind, "x": xx, "y": yy, "role": role})

    def group(kind, x, y, offsets, role="start"):
        for dx, dy in offsets:
            add(kind, x+dx, y+dy, role)

    group("gold", 65, 15, [(0,0),(1,0),(2,0),(0,1),(1,1),(2,1),(1,2)])
    group("gold", 83, 30, [(0,0),(1,0),(0,1),(1,1)], "expansion")
    group("stone", 52, 32, [(0,0),(1,0),(2,0),(0,1),(1,1)])
    group("stone", 35, 31, [(0,0),(1,0),(0,1),(1,1)], "expansion")
    group("berries", 69, 28, [(0,0),(1,0),(2,0),(0,1),(1,1),(2,1)])
    group("sheep", 60, 24, [(-3,-1),(-3,0),(-3,1),(-2,-3),(-10,-7),(-9,-7),(7,10),(8,10)])
    group("boar", 60, 24, [(-7,-9),(4,13)])
    group("deer", 60, 24, [(-10,8),(-9,9),(-8,10),(-11,10)])
    group("acacia", 60, 24, [(-4,-4),(-5,3),(5,-4),(4,5),(0,-6)])
    add("bush", 46, 35, "burning-bush")
    # 40 middle-of-channel barriers: return water can never cage an army
    # between two blocked entrances. Each half has an unobstructed bank exit.
    for y in range(58, 60):
        for x in range(55, 65):
            add("gate", x, y, "sea-gate")
    for y in (42, 48, 54, 60, 66, 72, 77):
        add("torch", 53, y, "seabed-marker")
    # Jericho: 9x9 enclosures on each coastal route. Paths outside the walls
    # remain available even before the scripted collapse (or an early siege).
    for y in range(56, 65):
        for x in range(6, 15):
            if x in (6,14) or y in (56,64):
                add("wall", x, y, "jericho")
    group("gold", 8, 58, [(0,0),(1,0),(0,1),(1,1)], "jericho-reward")
    add("relic", 12, 61, "jericho-reward")
    add("relic", 37, 40, "shared")
    for x, y in [(32,52),(43,65),(76,50),(85,64)]:
        add("fish", x, y, "shared")
    # Sandstone backdrops are remote from army routes and starting resources.
    for x, y in [(4,7),(16,8),(104,5),(112,26)]:
        add("mountain", x, y)
    for x, y in [(21,38),(33,38),(47,40),(78,39),(87,39),(102,42)]:
        add("rock", x, y)
    for x, y in [(39,26),(40,28),(64,34),(71,33),(50,14),(72,12)]:
        add("flowers", x, y)
    # Point anchors for regular resources must never stand inside forests.
    for obj in objects:
        if obj["kind"] not in ("gate", "torch", "fish"):
            if grid[obj["y"]][obj["x"]] in FORESTS:
                pair_tile(obj["x"], obj["y"], TERRAIN["dirt"])
    return {"name": "Exodus: Sea of Signs", "version": VERSION, "size": SIZE,
            "starts": STARTS, "terrain": grid, "objects": objects,
            "hazard": [55,44,65,76], "manna": [[73,35],[74,35],[75,35],[73,38],[74,38],[75,38]]}


def squares(grid, skip=14):
    used = set()
    for y in range(SIZE):
        for x in range(SIZE):
            terrain = grid[y][x]
            if (x,y) in used or terrain == skip:
                continue
            side = 1
            for candidate in range(3, min(SIZE-x, SIZE-y)+1, 2):
                if not all((xx,yy) not in used and grid[yy][xx] == terrain
                           for yy in range(y,y+candidate) for xx in range(x,x+candidate)):
                    break
                side = candidate
            for yy in range(y,y+side):
                for xx in range(x,x+side):
                    used.add((xx,yy))
            yield x+side//2, y+side//2, side//2, terrain


def percent(tile):
    return f"{(tile+.25)*100/SIZE:.2f}"


def land(x, y, radius, terrain, extra=""):
    return f"create_land {{ terrain_type T{terrain} base_size {radius} land_percent 0 land_position {percent(x)} {percent(y)}{extra} }}"


def rms(layout):
    lines = ["/* Compatibility: Definitive Edition */",
             f"/* EXODUS: SEA OF SIGNS {VERSION}. Original Art of the Map I candidate.",
             "   Tiny / two players / standard dataset / Conquest. Both scripts required.",
             "   Coast roads always open. Seabed x55..64, y44..75: 6 HP/s while flooded.",
             "   Sea opens 12:20, returns 18:00; 18-minute repeating cycle.",
             "   Actual terrain is fixed; XS uses Gaia water scenery and barriers. */",
             "#includeXS exodus.xs"]
    for value in sorted(set(TERRAIN.values())):
        lines.append(f"#const T{value} {value}")
    for name, value in OBJECTS.items():
        lines.append(f"#const EX_{name.upper()} {value}")
    for name,value in {"GAIA_SET":-1,"SIZE_X":3,"SIZE_Y":4,"OBSTRUCTION":78,"BLOCKAGE":79,"DESERT_MOOD":4}.items():
        lines.append(f"#const EX_{name} {value}")
    lines += ["<PLAYER_SETUP>", "direct_placement", "behavior_version 1", "override_map_size 120",
              "ai_info_map_type MEDITERRANEAN 0 0 0",
              "/* Pre-placement Gaia-only collision and effect settings. */",
              "effect_percent EX_GAIA_SET EX_GATE EX_SIZE_X 50",
              "effect_percent EX_GAIA_SET EX_GATE EX_SIZE_Y 50",
              "effect_amount EX_GAIA_SET EX_GATE EX_OBSTRUCTION 2",
              "effect_amount EX_GAIA_SET EX_GATE EX_BLOCKAGE 6",
              "effect_amount EX_GAIA_SET EX_TORCH EX_OBSTRUCTION 4",
              "<LAND_GENERATION>", "base_terrain T14", "enable_waves 0"]
    for x,y,r,t in squares(layout["terrain"]):
        lines.append(land(x,y,r,t))
    lines.append("/* One exact point anchor per critical Gaia object. */")
    for obj in layout["objects"]:
        x,y = obj["x"],obj["y"]
        lines.append(land(x,y,0,layout["terrain"][y][x], f" land_id {LAND_IDS[obj['kind']]}"))
    for player,(x,y) in enumerate(STARTS,1):
        lines.append(land(x,y,0,layout["terrain"][y][x], f" assign_to_player {player}"))
    lines += ["<TERRAIN_GENERATION>", "color_correction EX_DESERT_MOOD",
              "/* Native visual mixing; masks do not relocate the water or forests. */",
              "create_terrain T6 { base_terrain T14 land_percent 9 number_of_clumps 55 terrain_mask 1 }",
              "create_terrain T45 { base_terrain T14 land_percent 11 number_of_clumps 65 terrain_mask 1 }",
              "create_terrain T14 { base_terrain T6 land_percent 12 number_of_clumps 60 terrain_mask 1 }",
              "create_terrain T6 { base_terrain T0 land_percent 9 number_of_clumps 45 terrain_mask 1 }",
              "<OBJECTS_GENERATION>",
              "/* Native start logic retains civ-specific villagers/scout replacements. */",
              "create_object TOWN_CENTER { set_place_for_every_player max_distance_to_players 0 }"]
    for kind in OBJECTS:
        if not any(o['kind'] == kind for o in layout['objects']):
            continue
        # Native RMS walls use enclosure-generation semantics, not point placement.
        # Place nonblocking torches at the exact wall anchors; XS stages real walls.
        placed = "TORCH" if kind == "wall" else kind.upper()
        lines.append(f"create_object EX_{placed} {{ place_on_specific_land_id {LAND_IDS[kind]} set_gaia_object_only max_distance_to_players 0 ignore_terrain_restrictions }}")
    lines += ["create_object VILLAGER { set_place_for_every_player min_distance_to_players 3 max_distance_to_players 5 }",
              "create_object SCOUT { set_place_for_every_player min_distance_to_players 6 max_distance_to_players 7 }",
              "if REGICIDE", "create_object KING { set_place_for_every_player min_distance_to_players 2 max_distance_to_players 4 }", "endif"]
    return "\n".join(lines)+"\n"


def atlas(layout):
    """Source-faithful vector planning drawing; explicitly NOT a game image."""
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1010">',
           '<rect width="1200" height="1010" fill="#152529"/>',
           '<text x="50" y="56" fill="#d7b77e" font-family="sans-serif" font-size="12" letter-spacing="4">THE ART OF THE MAP I / TINY / 1V1</text>',
           '<text x="46" y="119" fill="#f0e4cb" font-family="Georgia,serif" font-size="64">EXODUS</text>',
           '<text x="50" y="151" fill="#b1beba" font-family="sans-serif" font-size="18">SEA OF SIGNS</text>',
           '<g transform="translate(50 196) scale(6)">',
           '<rect width="120" height="120" fill="#caa571"/>']
    for x,y,r,t in squares(layout["terrain"]):
        out.append(f'<rect x="{x-r}" y="{y-r}" width="{2*r+1}" height="{2*r+1}" fill="{COLORS[t]}"/>')
    for obj in layout["objects"]:
        x,y,k = obj["x"]+.5,obj["y"]+.5,obj["kind"]
        color = {"gold":"#f6d25b","stone":"#767e83","berries":"#7e3940","sheep":"#faf4de",
                 "boar":"#674a36","deer":"#a07742","relic":"#fff0a3","fish":"#b3ddcf",
                 "wall":"#705946","gate":"#a2e1dd","bush":"#e36837","torch":"#ee923e",
                 "acacia":"#516b3c","palm":"#385c3d","flowers":"#d9dbad","rock":"#947450","mountain":"#997f65"}[k]
        radius = .35 if k in ("flowers","torch") else .55
        if k in ("wall","gate","gold","stone"):
            out.append(f'<rect x="{x-.47}" y="{y-.47}" width=".94" height=".94" fill="{color}"/>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')
    out += ['<rect x="55" y="44" width="10" height="32" fill="none" stroke="#fff1d3" stroke-width=".3" stroke-dasharray="1 1"/>']
    for i,(x,y) in enumerate(STARTS,1):
        out.append(f'<rect x="{x-1.5}" y="{y-1.5}" width="4" height="4" fill="{["#276fbb","#ad3d36"][i-1]}" stroke="#fff0d7" stroke-width=".4"/>')
        out.append(f'<text x="{x+.5}" y="{y+1.4}" text-anchor="middle" fill="white" font-family="sans-serif" font-size="2.5">{i}</text>')
    out += ['</g>', '<g font-family="sans-serif">']
    notes = [("01 / FIRE WITHOUT ASH", "Approach either burning bush."),
             ("02 / BREAD IN THE DESERT", "Paired manna gardens at 07:00 / 25:00."),
             ("03 / THE WATERS DIVIDE", "Sea road opens at 12:20."),
             ("04 / THE WATERS RETURN", "90-second warning. Flood at 18:00."),
             ("05 / SEVEN TRUMPETS", "Jericho walls fall at 24:07."),
             ("ALWAYS A WAY AROUND", "Both coastal roads stay open.")]
    for i,(title,desc) in enumerate(notes):
        yy=240+i*100
        out += [f'<text x="810" y="{yy}" fill="#d7b77e" font-size="13" letter-spacing="1">{title}</text>',
                f'<text x="810" y="{yy+26}" fill="#c0ccca" font-size="14">{desc}</text>']
    out += ['<text x="810" y="856" fill="#e9deca" font-size="14">Cloud by day. Fire in the east wind.</text>',
            '<text x="50" y="953" fill="#b1beba" font-size="14">Authored terrain plan — not an in-game screenshot. Scenery animation and native blending require DE testing.</text>',
            '<text x="50" y="980" fill="#b1beba" font-size="13">120 × 120 tiles · Rotationally paired resources · Conquest · Standard civilizations · RMS + XS</text>', '</g></svg>']
    return "\n".join(out)


def ascii_script(source, name):
    """Reject unsafe source instead of silently replacing message contents."""
    try:
        data = source.encode("ascii")
    except UnicodeEncodeError as error:
        line = source.count("\n", 0, error.start) + 1
        raise ValueError(f"{name}:{line}: game script must contain ASCII only") from error
    if any(byte < 32 and byte not in (9, 10, 13) for byte in data):
        raise ValueError(f"{name}: unsupported control character in game script")
    return data


def validate_xs_source(source):
    # Strip comments and strings before checking declarations, so examples
    # in documentation cannot trigger a false rejection.
    code = re.sub(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', '', source)
    if re.search(r'\b(?:int|float|bool|string|vector)\s+\w+\s*;', code):
        raise ValueError("XS variables must have an initializer")
    depth = 0
    for line in code.splitlines():
        if depth == 0 and re.match(r'\s*(?:extern\s+)?string\s+\w+\s*=', line):
            raise ValueError("Use numeric IDs instead of global XS string state")
        depth += line.count('{') - line.count('}')


def build(scripts_only=False):
    layout = make_layout()
    # Validate BOTH scripts before touching the runnable output/package.
    rms_data = ascii_script(rms(layout), "Exodus.rms")
    xs_data = ascii_script((ROOT/"src/exodus.xs").read_text(encoding="utf-8"), "exodus.xs")
    validate_xs_source(xs_data.decode("ascii"))
    mod = ROOT/"dist"/"Exodus"
    rpath = mod/"resources/_common/random-map-scripts/Exodus.rms"
    xpath = mod/"resources/_common/xs/exodus.xs"
    rpath.parent.mkdir(parents=True,exist_ok=True)
    xpath.parent.mkdir(parents=True,exist_ok=True)
    rpath.write_bytes(rms_data)
    xpath.write_bytes(xs_data)
    if scripts_only:
        print("Updated loose RMS and XS only; no ZIP created.")
        return layout
    (ROOT/"docs/layout.json").write_text(json.dumps(layout,separators=(",",":"))+"\n")
    (ROOT/"docs/atlas.svg").write_text(atlas(layout),encoding="utf-8")
    members = [rpath,xpath]
    for name in ("README.md","PLAYTEST.md","SUBMISSION.md","THIRD_PARTY.md","docs/EVENTS.md","docs/AUDIO.md","docs/ART.md","docs/UPGRADE-0.2.0.md","docs/VALIDATION.md","docs/atlas.svg","docs/age-of-rms-seed-1.png"):
        source=ROOT/name
        if source.exists():
            target=mod/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            members.append(target)
    # Only verified-format custom WEMs enter the game audio path. WAV source
    # is a separate, clearly labelled production asset folder in the ZIP.
    for source in sorted((ROOT/"audio").glob("*.wav")):
        target=mod/"audio-source"/source.name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        members.append(target)
    for source in sorted((ROOT/"audio/converted").glob("*.wem")):
        target=mod/"resources/_common/drs/sounds"/source.name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        members.append(target)
    archive=ROOT/"dist"/f"Exodus-{VERSION}.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(members):
            info=zipfile.ZipInfo("Exodus/"+path.relative_to(mod).as_posix(),(2026,9,6,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,path.read_bytes())
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    checksums=f"{digest}  {archive.name}\n"
    art=ROOT/"dist"/f"Exodus-Art-Study-{VERSION}.zip"
    with zipfile.ZipFile(art,"w",zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted((ROOT/"assets").rglob("*")) + [ROOT/"docs/ART.md"]:
            if path.is_file():
                info=zipfile.ZipInfo("Exodus-Art-Study/"+path.relative_to(ROOT).as_posix(),(2026,9,6,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                bundle.writestr(info,path.read_bytes())
    checksums+=f"{hashlib.sha256(art.read_bytes()).hexdigest()}  {art.name}\n"
    (ROOT/"dist/SHA256SUMS").write_text(checksums)
    print(f"RMS: {rpath.stat().st_size:,} bytes; XS: {xpath.stat().st_size:,} bytes; ZIP: {archive.stat().st_size:,} bytes")
    print(dict(Counter(o["kind"] for o in layout["objects"])))
    return layout


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts-only", action="store_true")
    build(scripts_only=parser.parse_args().scripts_only)
