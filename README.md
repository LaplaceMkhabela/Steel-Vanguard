# Steel Vanguard: Iron Crucible (MVP)
Static site, no build. Deploy: drag this folder (or the zip) onto https://app.netlify.com/drop, or `netlify deploy --prod --dir .`
Local test: `python3 -m http.server` then open http://localhost:8000
Controls: WASD drive, mouse aim, click/Space fire. Front armor -50%, rear +50%. Titanium walls ricochet your shells once.

## Missions come from Tiled maps (edit locally)
Open the maps in `tiled/` with Tiled (tilesets are linked to `assets/`):
- `Scrapyard_outpost.tmx` (Mission 1, 44x28) - `foundry_gate.tmx` (Mission 2, 48x32) - `overlord_node.tmx` (Mission 3, 56x36)

After editing, rebuild the game data: `python3 tools/build_maps.py` (writes assets/outpost.js, foundry.js, overlord.js), then reload the game.

**Layers** (keep the names): main floor, Ground, Vegetation, Fencing, wood, cars, buildings.
Solid rules live at the top of `tools/convert_tmx.py`: everything in `buildings` is solid and indestructible; `Fencing` (gid 97+), `cars`, `wood` fences and logs, and trees/bushes/boulders in `Vegetation` are solid and shootable; ground, decals and the wooden deck are drivable.

**Markers**: add point objects in the `markers` object layer:
`player_start`, `exit`, `relay` (as many as the mission's relay count), `overlord` (boss relay, Mission 3), `cache`,
`enemy_scout`, `enemy_medium`, `enemy_heavy`, `enemy_rocket`. Markers snap to the nearest reachable free tile.
If a map has no markers (Mission 1) they are placed automatically. Keep relay and cache counts matching `rl`/`ca` in `MD` (index.html) for the mission briefing.
