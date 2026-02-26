# Sprite Sheet Generation Prompts

Pixel art style: **isometric 2.5D RPG** (inspired by Age of Empires 2, Warcraft 2).
Perspective: top-down oblique, ~30° elevation, unit faces **SE direction** (down-right).
All sheets: **transparent PNG background** (no checkerboard, no fill — pure alpha).

---

## UNIT SPRITES

### Shared Layout for All 5 Units

- **Frame size**: 32 × 48 pixels each
- **Sheet layout**: 4 columns × 4 rows = 16 frames total
- **Total sheet dimensions**: 128 × 192 pixels
- **Row 0** (frames 0–3): Idle — subtle breathing/stand still (4-frame loop, gentle vertical bob of 1px)
- **Row 1** (frames 4–7): Walk SE — walking toward lower-right (4-frame cycle, feet alternating)
- **Row 2** (frames 8–11): Work — performing a task (4-frame cycle, torso leaning forward/back, arms moving)
- **Row 3** (frames 12–13): Celebrate — small jump + arms up (2 frames); Error/Shake (frames 14–15): unit rocks left-right 2px
- Character is centered horizontally in each 32px frame, feet near the bottom at y=44, head near top at y=4
- Outline each character with 1px dark (#1a1a1a) anti-pixel border for readability

---

### 1. Avery — Unit Sprite Sheet (`avery-sheet.png`, 128×192)

Primary color: #4a90e2 (steel blue)
Character: **female AI coordinator** in blue medium armor. Slim build, short dark hair, blue pauldrons, white undershirt visible at neck. Carries a small holographic datapad in left hand. Confident posture.

Prompt:
> Pixel art sprite sheet, 128x192 pixels total, 4 columns x 4 rows, each frame 32x48 pixels, transparent background. Isometric 2.5D game unit facing SE (down-right). Female character with short dark hair, blue (#4a90e2) medium plate armor with white chest piece accents, small round pauldrons, blue gauntlets. Carries a glowing blue datapad in left hand. Style: Age of Empires 2 / Warcraft 2 pixel art, ~16 colors, 1px dark outline. Row 0: idle breathing (4 frames, 1px vertical bob). Row 1: walking SE (4 frames, standard walk cycle). Row 2: working/typing gesture (4 frames, leans forward, arms move). Row 3: celebrate jump arms-up (2 frames) then shake/error left-right (2 frames). Feet at bottom of frame, head near top.

---

### 2. Gilfoyle — Unit Sprite Sheet (`gilfoyle-sheet.png`, 128×192)

Primary color: #e24a4a (crimson red)
Character: **male server hacker** in dark hooded robe with crimson trim. Lean build, pale, goatee. Hood up, crimson sigil on chest. Carries a small server blade / USB key in right hand. Slightly hunched.

Prompt:
> Pixel art sprite sheet, 128x192 pixels total, 4 columns x 4 rows, each frame 32x48 pixels, transparent background. Isometric 2.5D game unit facing SE (down-right). Male character, lean and pale, goatee, wearing a dark charcoal (#222222) hooded cloak with crimson (#e24a4a) trim and a glowing red sigil on chest. Hood up. Holds a small glowing red server blade in right hand. Style: Age of Empires 2 / Warcraft 2 pixel art, ~16 colors, 1px dark outline. Row 0: idle breathing (4 frames, subtle cloak sway). Row 1: walking SE (4 frames, slightly hunched). Row 2: working — holds blade up, types on it (4 frames). Row 3: celebrate smirk-pose (2 frames) then error shake (2 frames). Feet at bottom, head near top.

---

### 3. Ralph — Unit Sprite Sheet (`ralph-sheet.png`, 128×192)

Primary color: #e2844a (warm orange)
Character: **male junior agent** in orange tunic with brown belt. Stocky, enthusiastic build. Big eyes, wavy brown hair. Carries a clipboard/notepad. Slightly wide stance.

Prompt:
> Pixel art sprite sheet, 128x192 pixels total, 4 columns x 4 rows, each frame 32x48 pixels, transparent background. Isometric 2.5D game unit facing SE (down-right). Male character, stocky build, big expressive eyes, wavy brown hair, wearing an orange (#e2844a) short-sleeve tunic with a brown leather belt and matching brown boots. Carries a small clipboard/notepad in left hand. Style: Age of Empires 2 / Warcraft 2 pixel art, ~16 colors, 1px dark outline. Row 0: idle (4 frames, slight heel-rock, eager posture). Row 1: walking SE (4 frames, energetic gait). Row 2: working — scribbles on clipboard (4 frames). Row 3: celebrate — pumps fist (2 frames) then error — flails arms (2 frames). Feet at bottom, head near top.

---

### 4. Jobin — Unit Sprite Sheet (`jobin-sheet.png`, 128×192)

Primary color: #9b4ae2 (violet purple)
Character: **male mystical engineer** in purple robes with gold accents. Tall, lean, long dark hair tied back. Calm/ambiguous expression. Carries a glowing purple gem orb. Floats 1px off the ground.

Prompt:
> Pixel art sprite sheet, 128x192 pixels total, 4 columns x 4 rows, each frame 32x48 pixels, transparent background. Isometric 2.5D game unit facing SE (down-right). Male character, tall and lean, long dark hair tied back, serene expression, wearing flowing violet (#9b4ae2) robes with gold trim at cuffs and hem. Holds a small glowing purple orb in one hand. Feet barely touch ground (slightly elevated, 1px float). Style: Age of Empires 2 / Warcraft 2 pixel art, ~16 colors, 1px dark outline. Row 0: idle (4 frames, robes flutter gently, orb pulses). Row 1: walking SE (4 frames, gliding walk, robes flow). Row 2: working — waves hand over orb, orb glows brighter (4 frames). Row 3: celebrate — orb flares (2 frames) then error — orb dims, slumps (2 frames). Feet at bottom, head near top.

---

### 5. Villager — Unit Sprite Sheet (`villager-sheet.png`, 128×192)

Primary color: #c8a84b (tan/gold)
Character: **generic worker** in tan/brown peasant clothes. Average build, short brown hair, no face detail. Carries a small pickaxe or wrench on back. Generic and interchangeable — this sprite will be reused for all villager swarm units.

Prompt:
> Pixel art sprite sheet, 128x192 pixels total, 4 columns x 4 rows, each frame 32x48 pixels, transparent background. Isometric 2.5D game unit facing SE (down-right). Generic male villager, average build, plain face, short brown hair, wearing a tan (#c8a84b) linen tunic, brown trousers, brown boots. Small pickaxe or wrench strapped to back. Minimalist design — should read clearly at small sizes. Style: Age of Empires 2 / Warcraft 2 pixel art, ~12 colors, 1px dark outline. Row 0: idle (4 frames, neutral stand, weight shift). Row 1: walking SE (4 frames, standard walk). Row 2: working — swings pickaxe/wrench (4 frames). Row 3: celebrate — waves arms (2 frames) then error — shakes head (2 frames). Feet at bottom, head near top.

---

## TERRAIN TILES

### Isometric Tile Sheet (`terrain-tiles.png`, 256×128)

- **Tile frame size**: 64 × 32 pixels each (standard isometric diamond tile at 2:1 ratio)
- **Sheet layout**: 4 columns × 4 rows = 16 tiles
- **Total sheet dimensions**: 256 × 128 pixels
- All tiles are isometric diamond shapes (hexagonal outline: 64px wide, 32px tall)
- Diamond corners: top at (32,0), right at (64,16), bottom at (32,32), left at (0,16)

Prompt:
> Pixel art terrain tile sheet, 256x128 pixels total, 4 columns x 4 rows, each frame 64x32 pixels, transparent background outside diamond shape. Isometric top-down diamond tile format (64px wide, 32px tall). Style: Age of Empires 2 terrain tiles, 16-bit pixel art. Include these 16 tiles (left-to-right, top-to-bottom):
> - Row 0: (1) Grass light #4a7c34, flat even grass; (2) Grass dark #527a3c, slightly deeper green; (3) Grass rocky, green with pebbles; (4) Grass flowers, light green with tiny flowers
> - Row 1: (5) Stone cobble #8a8070, grey stone plaza tile with grout lines; (6) Stone worn #7e7666, darker worn stone; (7) Stone cracked, aged stone with crack; (8) Stone edge, stone transitioning to dirt
> - Row 2: (9) Dirt path #7a6040, packed dirt, slightly rutted; (10) Dirt road #726038, darker trodden earth; (11) Dirt gravel, earth with small stones; (12) Dirt patchy, uneven dirt with sparse grass patches
> - Row 3: (13) Water tile, shallow blue water with ripple; (14) Water deep, darker blue; (15) Sand, light tan; (16) Mud, dark brown wet earth
> Each tile: only color the diamond area, keep corners fully transparent. 1px darker edge on all 4 diamond sides for depth. Natural texture variation within each tile.

---

## BUILDING SPRITES

### Shared Layout for All 5 Buildings

- **Frame size**: 96 × 96 pixels each
- **Sheet layout**: 5 columns × 1 row = 5 frames total
- **Total sheet dimensions**: 480 × 96 pixels
- **Filename**: `buildings-sheet.png`
- Isometric SE-facing view: left wall = NW face (deep shadow), right wall = SE face (mid shadow), roof = top diamond (lit)
- Transparent PNG background (no fill — pure alpha outside the building shape)
- 1px dark (#1a1a1a) outline on all visible edges
- Each building is horizontally centered in its 96px frame; base sits near y=72, top of tallest element near y=4
- Light source is top-left (NW) — NW-facing left wall is darkest, roof is brightest
- Style: Age of Empires 2 / Warcraft 2 pixel art, ~20 colors per building, clean crisp edges

**Building order left-to-right:** town-center (col 0), castle (col 1), barracks (col 2), market (col 3), university (col 4)

---

### 1. Town Center (`buildings-sheet.png` col 0, offset x=0)

Base color: #d4a017 (warm gold/amber)
Height: tallest building — central tower extends ~22px above roof; flag pole adds 14px more

Prompt:
> Pixel art isometric building sprite, 96x96 pixels, transparent background. Single frame. Isometric SE-facing view (standard AoE2 perspective). Style: Age of Empires 2 pixel art, ~20 colors, 1px dark outline.
>
> Town Center building. Base color #d4a017 (warm gold/amber). Isometric diamond footprint ~64px wide, 32px tall at base. Two visible walls: left wall (NW face, color #7a5a0a — dark amber shadow) and right wall (SE face, color #a87c10 — medium amber shadow). Flat roof diamond (lightened to #e8b820). Bright NW and NE roof edge highlights (#f5d060).
>
> Details: Small arched windows on both walls with dark frames and warm amber (#ffcc44) interior glow. Rising from the center of the roof: a small square tower (about 40% tile width, same wall coloring, darker shade). Tower has its own diamond mini-roof. On the right side of the tower roof: a thin brown flagpole rising ~14px, with a small red triangular pennant banner.
>
> Building centered in frame, base at y≈72, top of flag at y≈4. 1px dark outline throughout.

---

### 2. Castle (`buildings-sheet.png` col 1, offset x=96)

Base color: #708090 (slate grey)
Height: mid-height with battlements — merlons line both wall tops; dark banner on left

Prompt:
> Pixel art isometric building sprite, 96x96 pixels, transparent background. Single frame. Isometric SE-facing view. Style: Age of Empires 2 pixel art, ~20 colors, 1px dark outline.
>
> Castle building. Base color #708090 (slate grey). Two visible walls: left wall (NW face, #3a414a — deep cool shadow) and right wall (SE face, #545e68 — mid grey shadow). Flat roof diamond (#8a96a4, slightly lighter grey). Bright NW and NE ridge highlights (#b0bcc8).
>
> Details: On the right (SE) wall: a narrow vertical cross-shaped arrow slit (3px wide × 8px tall with a 2px horizontal bar), dark void inside. Along the top edge of both walls: 3 rectangular merlons/battlements per wall (blocky square crenellations, same wall color as their respective face). On the left wall, near the left battlement: a thin dark grey flagpole (~14px tall) with a small dark red (#880000) triangular pennant.
>
> Building centered in frame, base at y≈72, top of battlements/banner at y≈16. 1px dark outline throughout.

---

### 3. Barracks (`buildings-sheet.png` col 2, offset x=192)

Base color: #8b4513 (saddle brown / rust)
Height: shorter than castle — flag pole is the tallest element

Prompt:
> Pixel art isometric building sprite, 96x96 pixels, transparent background. Single frame. Isometric SE-facing view. Style: Age of Empires 2 pixel art, ~20 colors, 1px dark outline.
>
> Barracks building. Base color #8b4513 (saddle brown/rust). Two visible walls: left wall (NW face, #3e1e08 — deep brown shadow) and right wall (SE face, #6a3510 — medium rust shadow). Flat roof diamond (#a85520, slightly lighter brown). Bright NW and NE ridge highlights (#cc7040).
>
> Details: Centered on the right (SE) wall: a crossed swords emblem — two silver (#ddddcc) sword blades crossing at 45°, each ~12px long, with small grey (#aaaaaa) crossguards and dark grey pommel circles at each tip. On the left wall, upper area: a thin dark brown flagpole (~17px tall) with a small dark red (#991a00) triangular pennant pointing right.
>
> Building centered in frame, base at y≈72, top of flagpole at y≈10. 1px dark outline throughout.

---

### 4. Market (`buildings-sheet.png` col 3, offset x=288)

Base color: #2e8b57 (sea green)
Height: shortest building — low walls, canopy extends from the SE wall base

Prompt:
> Pixel art isometric building sprite, 96x96 pixels, transparent background. Single frame. Isometric SE-facing view. Style: Age of Empires 2 pixel art, ~20 colors, 1px dark outline.
>
> Market building. Base color #2e8b57 (sea green). Low walls (about half height of town-center). Two visible walls: left wall (NW face, #124a2e — deep green shadow) and right wall (SE face, #226b44 — medium green shadow). Flat roof diamond (#3aaa6a, lighter green). Bright NW and NE ridge highlights (#5ecc88).
>
> Details: On the right (SE) wall: a small arched window with dark frame and warm amber (#ffcc44) interior glow. Extending from the bottom edge of the right (SE) wall outward: a small canopy/awning — a parallelogram flap in slightly darkened sea green (#267550) with 3 thin vertical yellow (#ffdd55) stripe lines across it, overhang of ~8px. The awning bottom edge has a 1px dark outline.
>
> Building centered in frame, base at y≈72 (lower than others — short building), top of roof at y≈42. Canopy extends slightly beyond the right wall footprint. 1px dark outline throughout.

---

### 5. University (`buildings-sheet.png` col 4, offset x=384)

Base color: #4169e1 (royal blue)
Height: tall spire — blue shaft rising ~20px from roof + triangular head + gold orb at tip

Prompt:
> Pixel art isometric building sprite, 96x96 pixels, transparent background. Single frame. Isometric SE-facing view. Style: Age of Empires 2 pixel art, ~20 colors, 1px dark outline.
>
> University building. Base color #4169e1 (royal blue). Two visible walls: left wall (NW face, #1a2d80 — deep blue shadow) and right wall (SE face, #2d50b8 — medium blue shadow). Flat roof diamond (#5580f0, lighter blue). Bright NW and NE ridge highlights (#88aaff).
>
> Details: On the right (SE) wall: a large arched window (taller than wide, gothic arch shape) with dark frame and warm amber (#ffcc44) glow inside — the largest window of any building. On the left (NW) wall: a small square window, same amber glow. Rising from the center of the roof diamond: a thin dark blue (#1a1a8e) spire shaft, ~20px tall. At the tip: a small upward-pointing colored triangle (lightened blue, ~5px wide × 4px tall). Sitting atop the triangle: a tiny gold (#ffdd44) circle/orb, 2–3px diameter, 1px dark outline.
>
> Building centered in frame, base at y≈72, gold orb at y≈4. 1px dark outline throughout.

---

## Implementation Notes

When sprites are ready, drop them in `public/assets/`:
```
public/assets/
  units/
    avery-sheet.png      # 128×192
    gilfoyle-sheet.png   # 128×192
    ralph-sheet.png      # 128×192
    jobin-sheet.png      # 128×192
    villager-sheet.png   # 128×192
  tiles/
    terrain-tiles.png    # 256×128
  buildings/
    buildings-sheet.png  # 480×96
```

Phaser frame mapping in `PreloadScene.ts`:
```ts
this.load.spritesheet('unit-avery', 'assets/units/avery-sheet.png', { frameWidth: 32, frameHeight: 48 });
// frames 0-3: idle | 4-7: walk | 8-11: work | 12-13: celebrate | 14-15: error

this.load.spritesheet('terrain', 'assets/tiles/terrain-tiles.png', { frameWidth: 64, frameHeight: 32 });
// frame 0-1: grass | 4-5: stone | 8-9: dirt | 12: water

this.load.spritesheet('buildings', 'assets/buildings/buildings-sheet.png', { frameWidth: 96, frameHeight: 96 });
// frame 0: town-center | 1: castle | 2: barracks | 3: market | 4: university
```
