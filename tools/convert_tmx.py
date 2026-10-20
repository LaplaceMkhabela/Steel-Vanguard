#!/usr/bin/env python3
"""Convert a Tiled .tmx (CSV layers) into assets/outpost.js for Steel Vanguard.
Usage: python3 tools/convert_tmx.py path/to/Scrapyard_outpost.tmx [assets/outpost.js]

Collision rules are in RULES below (edit to taste). Optional object layer: point objects named
player_start, exit, relay, overlord (boss relay, listed first), cache,
enemy_scout/enemy_medium/enemy_heavy/enemy_rocket override the automatic marker placement.
Usage: convert_tmx.py map.tmx out.js mapname   (mapname = key used by the game: outpost, foundry, overlord)"""
import re, sys, json, os
from collections import deque
tmx = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else 'assets/outpost.js'
name = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(os.path.basename(out))[0]
x = open(tmx, encoding='utf8').read()
W, H = (int(re.search(r'<map [^>]*\b%s="(\d+)"' % k, x).group(1)) for k in ('width', 'height'))
TW = int(re.search(r'<map [^>]*\btilewidth="(\d+)"', x).group(1))
# tileset basename -> image key used by the game (firstgids are read from the tmx)
KEYS = {'tar': 'tar', 'terrain_spritesheet': 'terrain', 'fencing': 'fence', 'buildings_objects_spritesheet_64': 'bld'}
ts = sorted((int(g), KEYS[os.path.splitext(os.path.basename(s))[0]]) for g, s in re.findall(r'<tileset firstgid="(\d+)" source="([^"]+)"', x))
# class codes: 1 solid indestructible, 2 car (hp3), 3 wood/crate (hp1), 4 fence (hp3), 5 tree/bush (hp5)
RULES = {'buildings': (1, lambda g: True),
         'Fencing': (4, lambda g: g >= 97),
         'cars': (2, lambda g: True),
         'wood': (3, lambda g: 129 <= g <= 142 or g == 84),
         'Vegetation': (5, lambda g: g in (69, 70, 71, 74, 82, 83, 85))}
PRIO = ['buildings', 'Fencing', 'cars', 'wood', 'Vegetation']
layers = []
for n, d in re.findall(r'<layer [^>]*name="([^"]+)"[^>]*>\s*<data encoding="csv">(.*?)</data>', x, re.S):
    v = [int(t) for t in d.replace('\n', '').split(',') if t.strip() != '']
    assert len(v) == W * H, n
    flips = sum(1 for t in v if t & 0xE0000000)
    layers.append((n, v))   # raw gids: flip flags are kept for the renderer
cls = [0] * (W * H); S = {}
for n, v in layers:
    S[n] = ''.join('1' if (n in RULES and RULES[n][0] != 1 and (t & 0x1FFFFFFF) and RULES[n][1](t & 0x1FFFFFFF)) else '0' for t in v)
for n in PRIO:
    if n not in RULES: continue
    c, f = RULES[n]
    for n2, v in layers:
        if n2 != n: continue
        for i, t in enumerate(v):
            g = t & 0x1FFFFFFF
            if g and f(g) and cls[i] == 0: cls[i] = c
# ---- markers: object layer if present, else automatic
objs = {}
for og in re.findall(r'<objectgroup[^>]*>(.*?)</objectgroup>', x, re.S):
    for m in re.finditer(r'<object [^>]*name="([^"]*)"[^>]*\bx="([\d.]+)"[^>]*\by="([\d.]+)"', og):
        objs.setdefault(m.group(1), []).append((int(float(m.group(2)) // TW), int(float(m.group(3)) // TW)))
free = lambda a, b: 0 <= a < W and 0 <= b < H and cls[b * W + a] == 0
def nearest(p):
    q = deque([p]); seen = {p}
    while q:
        a, b = q.popleft()
        if free(a, b): return (a, b)
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (a + da, b + db)
            if n not in seen and 0 <= n[0] < W and 0 <= n[1] < H: seen.add(n); q.append(n)
start = nearest(objs['player_start'][0] if 'player_start' in objs else (W - 5, H - 4))
ex = nearest(objs['exit'][0] if 'exit' in objs else (12, 1))
seen = {start}; q = deque([start])
while q:
    a, b = q.popleft()
    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (a + da, b + db)
        if n not in seen and free(*n): seen.add(n); q.append(n)
if ex not in seen:
    want = objs['exit'][0] if 'exit' in objs else (12, 1)
    ex = min(seen, key=lambda p: abs(p[0] - want[0]) + abs(p[1] - want[1]) * 1.5)
clear = lambda a, b, r: all(free(a + i, b + j) for i in range(-r, r + 1) for j in range(-r, r + 1))
snap = lambda p: p if p in seen else min(seen, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2)
if 'relay' in objs or 'overlord' in objs: relays = [snap(p) for p in objs.get('overlord', []) + objs.get('relay', [])]   # overlord first = boss relay
else:
    cand = [p for p in seen if 3 <= p[0] < W - 3 and 3 <= p[1] < H - 3 and clear(*p, 2)
            and abs(p[0] - start[0]) + abs(p[1] - start[1]) >= 16 and abs(p[0] - ex[0]) + abs(p[1] - ex[1]) >= 6]
    relays = []; pts = [start]
    for _ in range(3):
        best = max(cand, key=lambda p: min((p[0] - a) ** 2 + (p[1] - b) ** 2 for a, b in pts))
        relays.append(best); pts.append(best)
ETY = {'enemy_scout': 0, 'enemy_medium': 1, 'enemy_heavy': 2, 'enemy_rocket': 3}
en = [[t] + list(snap(p)) for k, t in ETY.items() for p in objs.get(k, [])]
caches = [list(snap(p)) for p in objs.get('cache', [])]
js = "(window.TMXS=window.TMXS||{})['%s']=" % name + json.dumps({
    'w': W, 'h': H, 'ts': [[g, k] for g, k in ts], 'c': cls,
    'l': [{'n': n, 'd': v, 's': S.get(n, '0' * (W * H))} for n, v in layers],
    'obj': {'s': list(start), 'e': list(ex), 'r': [list(r) for r in relays], 'en': en, 'c': caches}}, separators=(',', ':')) + ';\n'
os.makedirs(os.path.dirname(out) or '.', exist_ok=True); open(out, 'w').write(js)
print('map %dx%d, %d layers, %d solid cells, reachable free cells %d' % (W, H, len(layers), sum(1 for c in cls if c), len(seen)))
print('enemies', len(en), 'caches', len(caches), 'start', start, 'exit', ex, 'exit reachable', ex in seen, 'relays', relays, 'all reachable', all(r in seen for r in relays))
