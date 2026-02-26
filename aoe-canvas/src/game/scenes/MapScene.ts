import Phaser from 'phaser';
import { Unit } from '../entities/Unit';
import { Building } from '../entities/Building';
import { SelectionBox } from '../entities/SelectionBox';
import { EventBus } from '../EventBus';
import {
  tileToWorld,
  worldToTile,
  GRID_COLS,
  GRID_ROWS,
  TILE_HALF_W,
  TILE_HALF_H,
  TILE_H,
} from '../utils/isometric';
import {
  UnitProfile,
  BuildingData,
  UnitData,
  MapState,
} from '../../types/game';

export class MapScene extends Phaser.Scene {
  private tileImages: Phaser.GameObjects.Image[] = [];
  private units: Map<string, Unit> = new Map();
  private buildings: Map<string, Building> = new Map();
  private selectionBox!: SelectionBox;
  private selectedUnits: Set<string> = new Set();
  private selectedBuilding: string | null = null;
  // Pan state — activated by Space+leftdrag or middle drag
  private isPanning = false;
  private panStart?: { x: number; y: number };
  private spaceKey?: Phaser.Input.Keyboard.Key;
  // Box select state — left drag without space
  private isBoxSelecting = false;
  private boxSelectStart?: { x: number; y: number };
  private cursors?: Phaser.Types.Input.Keyboard.CursorKeys;
  private hoveredTile: { col: number; row: number } | null = null;
  private lastRenderedHover: { col: number; row: number } | null = null;
  private tileOverlay!: Phaser.GameObjects.Graphics;

  constructor() {
    super({ key: 'MapScene' });
  }

  create() {
    // World bounds
    const worldW = (GRID_COLS + GRID_ROWS) * TILE_HALF_W + 200;
    const worldH = (GRID_COLS + GRID_ROWS) * TILE_HALF_H + 200;

    this.cameras.main.setBounds(-worldW / 2, -100, worldW, worldH + 200);
    this.cameras.main.setZoom(1.6);

    // Center camera to frame full base: trees above, buildings below
    const center = tileToWorld(16, 15);
    this.cameras.main.centerOn(center.x, center.y + 28);

    // Prevent Phaser from oscillating cursor style at interactive object boundaries
    this.input.setDefaultCursor('default');

    // Draw tile grid then environment decorations
    this.tileOverlay = this.add.graphics();
    this.tileOverlay.setDepth(1);
    this.drawTiles();
    this.drawEnvironment();

    // Selection box
    this.selectionBox = new SelectionBox(this);

    // Place initial units — clustered north of the town center
    this.spawnNamedUnit('avery-1', 'avery', 13, 14);
    this.spawnNamedUnit('gilfoyle-1', 'gilfoyle', 15, 13);
    this.spawnNamedUnit('ralph-1', 'ralph', 17, 13);
    this.spawnNamedUnit('jobin-1', 'jobin', 19, 14);
    this.spawnNamedUnit('colin-1', 'colin', 21, 14);

    // Place default Town Center building
    this.placeBuilding({
      id: 'building-tc-1',
      type: 'town-center',
      status: 'idle',
      col: 16,
      row: 16,
      name: 'Town Center',
    });

    // Demo buildings — populate the map until API data loads
    // Castle NW of TC: guards the forest flank
    this.placeBuilding({
      id: 'building-castle-1',
      type: 'castle',
      status: 'idle',
      col: 12,
      row: 16,
      name: 'Castle',
    });
    // Barracks SW of TC: col-row=-4 → x=-128, well inside viewport
    this.placeBuilding({
      id: 'building-barracks-1',
      type: 'barracks',
      status: 'idle',
      col: 15,
      row: 19,
      name: 'Barracks',
    });
    // Market SE of TC: x=64, slightly below and right
    this.placeBuilding({
      id: 'building-market-1',
      type: 'market',
      status: 'idle',
      col: 19,
      row: 17,
      name: 'Market',
    });
    // University NE of TC: x=192, along the east road direction
    this.placeBuilding({
      id: 'building-university-1',
      type: 'university',
      status: 'idle',
      col: 21,
      row: 15,
      name: 'University',
    });

    // Setup input
    this.setupInput();
    this.cursors = this.input.keyboard!.createCursorKeys();

    // Listen to React events
    EventBus.on('dispatch-job-to-building', this.handleDispatchJob, this);
    EventBus.on('place-building', this.handlePlaceBuilding, this);
    EventBus.on('sync-jobs', this.handleJobSync, this);
    EventBus.on('load-map-state', this.handleLoadMapState, this);

    // Tell React the scene is ready
    EventBus.emit('scene-ready', this);
  }

  private getTileFrame(col: number, row: number): number {
    const dx = col - 16, dy = row - 16;
    const tcDist = Math.max(Math.abs(dx), Math.abs(dy));

    // Stone plaza surrounding the town center (frames 4–5)
    if (tcDist <= 1) return 4;
    if (tcDist === 2) return (col + row) % 2 === 0 ? 5 : 4;

    // Dirt paths (frames 8–9)
    if (col === 16 && row >= 19 && row <= 26) return 8;
    if (col === 17 && row >= 20 && row <= 25) return 9;
    if (row === 16 && col >= 19 && col <= 26) return 8;
    if (row === 15 && col >= 20 && col <= 25) return 9;

    // Grass with variety (frames 0–3)
    if ((col + row) % 4 === 0) return 2; // rocky grass
    if ((col + row) % 4 === 3) return 3; // flower grass
    return (col + row) % 2 === 0 ? 0 : 1;
  }

  private drawTiles() {
    this.tileImages.forEach(img => img.destroy());
    this.tileImages = [];

    for (let row = 0; row < GRID_ROWS; row++) {
      for (let col = 0; col < GRID_COLS; col++) {
        const { x, y } = tileToWorld(col, row);
        const frame = this.getTileFrame(col, row);
        const img = this.add.image(x, y, 'terrain', frame);
        img.setOrigin(0.5, 0);
        img.setDepth(0);
        this.tileImages.push(img);
      }
    }
  }

  private drawEnvironment() {
    // Single graphics layer for all trees — depth between tiles and buildings
    const g = this.add.graphics();
    g.setDepth(3);

    // Key: x = (col-row)*32, y = (col+row)*16+16
    // Viewport at 1.6x centered at ~(32, 524): x range [-202, 266], y range [399, 649]
    const trees: [number, number][] = [
      // ── TOP FOREST LINE (visible above units, col+row≈25, y≈416) ──────
      [10, 15], [11, 14], [12, 13], [13, 12], [14, 11], [15, 10], [16, 9],

      // ── SECOND ROW (forest depth, col+row≈27) ───────────────────────────
      [11, 16], [12, 15],          // left, x=-160/-96
      [16, 11], [17, 10],          // right-center, x=160/224

      // ── NE CLUSTER (right side balance, x=128-192) ───────────────────────
      [19, 12], [20, 12],          // NE of units, x=224/256 — right edge area
      [20, 14], [20, 15],          // east side, x=192/160

      // ── LEFT CORRIDOR (south-west side trees) ────────────────────────────
      [12, 17], [12, 18],          // x=-160/-192

      // ── SOUTH VISIBLE (near bottom of viewport, col+row≈37-38) ───────────
      [17, 21], [18, 20], [19, 19], // x=-128/-64/0, y=624

      // ── MID-RANGE EXPLORATION (panning reveals these) ────────────────────
      [7, 8], [8, 7], [9, 7],       // NW mid
      [22, 8], [23, 9],             // NE mid  (x=448/448 — off screen by default, for exploration)
      [8, 22], [9, 23],             // SW mid
      [22, 23], [23, 22],           // SE mid

      // ── WORLD EDGE TREES (exploration / sense of world) ──────────────────
      [3, 5], [5, 3], [4, 6],
      [27, 4], [26, 5],
      [4, 26], [5, 27],
      [26, 27], [27, 26],
    ];

    // Draw furthest trees first (lowest col+row = furthest back in isometric)
    const sorted = [...trees].sort(([c1, r1], [c2, r2]) => (c1 + r1) - (c2 + r2));
    for (const [col, row] of sorted) {
      const { x, y } = tileToWorld(col, row);
      this.renderTree(g, x, y + TILE_HALF_H);
    }
  }

  private renderTree(g: Phaser.GameObjects.Graphics, cx: number, cy: number) {
    // Shadow
    g.fillStyle(0x000000, 0.18);
    g.fillEllipse(cx, cy + 2, 22, 8);

    // Trunk
    g.fillStyle(0x5a3010, 1);
    g.fillRect(cx - 2.5, cy - 10, 5, 12);
    g.lineStyle(0.75, 0x3a1e08, 0.7);
    g.strokeRect(cx - 2.5, cy - 10, 5, 12);

    // Foliage — 3 stacked diamond layers (darkest at bottom, lightest at top)
    // Bottom (widest)
    g.fillStyle(0x2a6818, 1);
    g.fillPoints([
      { x: cx, y: cy - 8 }, { x: cx + 14, y: cy - 2 },
      { x: cx, y: cy + 4 }, { x: cx - 14, y: cy - 2 },
    ], true);
    g.lineStyle(1, 0x1e4e12, 0.45);
    g.strokePoints([
      { x: cx, y: cy - 8 }, { x: cx + 14, y: cy - 2 },
      { x: cx, y: cy + 4 }, { x: cx - 14, y: cy - 2 },
    ], true);

    // Middle
    g.fillStyle(0x358c22, 1);
    g.fillPoints([
      { x: cx, y: cy - 18 }, { x: cx + 10, y: cy - 13 },
      { x: cx, y: cy - 8 }, { x: cx - 10, y: cy - 13 },
    ], true);
    g.lineStyle(1, 0x266018, 0.4);
    g.strokePoints([
      { x: cx, y: cy - 18 }, { x: cx + 10, y: cy - 13 },
      { x: cx, y: cy - 8 }, { x: cx - 10, y: cy - 13 },
    ], true);

    // Top (narrowest, brightest)
    g.fillStyle(0x44aa2c, 1);
    g.fillPoints([
      { x: cx, y: cy - 27 }, { x: cx + 6, y: cy - 22 },
      { x: cx, y: cy - 17 }, { x: cx - 6, y: cy - 22 },
    ], true);

    // Top highlight
    g.lineStyle(1, 0x66cc44, 0.5);
    g.lineBetween(cx, cy - 27, cx - 4, cy - 24);
    g.lineBetween(cx, cy - 27, cx + 4, cy - 24);
  }

  private setupInput() {
    const cam = this.cameras.main;

    this.spaceKey = this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

    this.input.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.middleButtonDown()) {
        this.isPanning = true;
        this.panStart = { x: ptr.x, y: ptr.y };
        return;
      }

      if (ptr.leftButtonDown()) {
        if (this.spaceKey?.isDown) {
          // Space + left drag = pan
          this.isPanning = true;
          this.panStart = { x: ptr.x, y: ptr.y };
        } else {
          // Plain left drag = box select
          this.boxSelectStart = { x: ptr.worldX, y: ptr.worldY };
          this.isBoxSelecting = false;
          this.selectionBox.start(ptr.x, ptr.y);
        }
      }
    });

    this.input.on('pointermove', (ptr: Phaser.Input.Pointer) => {
      // Camera pan
      if (this.isPanning && this.panStart) {
        const dx = ptr.x - this.panStart.x;
        const dy = ptr.y - this.panStart.y;
        cam.scrollX -= dx / cam.zoom;
        cam.scrollY -= dy / cam.zoom;
        this.panStart = { x: ptr.x, y: ptr.y };
      }

      // Box select (only when not panning)
      if (ptr.leftButtonDown() && !this.isPanning && this.boxSelectStart) {
        const dist = Phaser.Math.Distance.Between(ptr.worldX, ptr.worldY, this.boxSelectStart.x, this.boxSelectStart.y);
        if (dist > 10) {
          this.isBoxSelecting = true;
          this.selectionBox.update(ptr.x, ptr.y);
        }
      }

      // Tile hover — update state only; draw happens in update() to stay in sync with render loop
      this.hoveredTile = worldToTile(ptr.worldX, ptr.worldY - TILE_HALF_H);
    });

    this.input.on('pointerup', (ptr: Phaser.Input.Pointer) => {
      if (ptr.middleButtonReleased()) {
        this.isPanning = false;
        this.panStart = undefined;
      }

      if (ptr.rightButtonReleased()) {
        const tilePos = worldToTile(ptr.worldX, ptr.worldY - TILE_HALF_H);
        this.handleRightClick(tilePos.col, tilePos.row);
      }

      if (ptr.leftButtonReleased()) {
        this.isPanning = false;
        this.panStart = undefined;
        this.selectionBox.end();
        this.isBoxSelecting = false;
        this.boxSelectStart = undefined;
      }
    });

    // Zoom with scroll
    this.input.on('wheel', (_ptr: Phaser.Input.Pointer, _gobs: unknown, _dx: number, dy: number) => {
      const zoom = cam.zoom;
      const newZoom = Phaser.Math.Clamp(zoom - dy * 0.001, 0.4, 2.5);
      cam.setZoom(newZoom);
    });
  }

  private drawTileHover() {
    this.tileOverlay.clear();
    if (!this.hoveredTile) return;
    const { col, row } = this.hoveredTile;
    const { x, y } = tileToWorld(col, row);
    this.tileOverlay.lineStyle(1.5, 0xffffff, 0.4);
    this.tileOverlay.strokePoints([
      { x, y },
      { x: x + TILE_HALF_W, y: y + TILE_HALF_H },
      { x, y: y + TILE_H },
      { x: x - TILE_HALF_W, y: y + TILE_HALF_H },
    ], true);
  }

  private handleRightClick(col: number, row: number) {
    // If units selected, move them
    if (this.selectedUnits.size > 0) {
      const blocked = this.getBlockedTiles();
      let offset = 0;
      for (const unitId of this.selectedUnits) {
        const unit = this.units.get(unitId);
        if (!unit) continue;
        const targetCol = col + (offset % 3);
        const targetRow = row + Math.floor(offset / 3);
        unit.moveToTile(
          Math.min(targetCol, GRID_COLS - 1),
          Math.min(targetRow, GRID_ROWS - 1),
          blocked,
        );
        offset++;
      }
      return;
    }

    // Empty tile right-click
    const hasBuilding = this.isTileOccupied(col, row);
    if (!hasBuilding) {
      EventBus.emit('right-click-empty', { col, row });
    }
  }

  private getBlockedTiles(): Set<string> {
    const blocked = new Set<string>();
    for (const building of this.buildings.values()) {
      blocked.add(`${building.col},${building.row}`);
    }
    return blocked;
  }

  private isTileOccupied(col: number, row: number): boolean {
    for (const b of this.buildings.values()) {
      if (b.col === col && b.row === row) return true;
    }
    return false;
  }

  update(_time: number, _delta: number) {
    // Keyboard camera movement
    if (this.cursors) {
      const speed = 5 / this.cameras.main.zoom;
      if (this.cursors.left.isDown) this.cameras.main.scrollX -= speed;
      if (this.cursors.right.isDown) this.cameras.main.scrollX += speed;
      if (this.cursors.up.isDown) this.cameras.main.scrollY -= speed;
      if (this.cursors.down.isDown) this.cameras.main.scrollY += speed;
    }

    // Tile hover — drawn in update loop so it's always in sync with the render frame,
    // preventing the 1-frame clear flash that happens when drawing inside event handlers
    const h = this.hoveredTile;
    const lh = this.lastRenderedHover;
    if (h?.col !== lh?.col || h?.row !== lh?.row) {
      this.drawTileHover();
      this.lastRenderedHover = h ? { col: h.col, row: h.row } : null;
    }
  }

  // ─── Entity management ────────────────────────────────────────────────────

  spawnNamedUnit(id: string, profile: UnitProfile, col: number, row: number): Unit {
    const unit = new Unit(this, id, profile, col, row);
    this.units.set(id, unit);

    unit.on('pointerdown', () => {
      this.selectUnit(id);
    });

    return unit;
  }

  spawnVillager(): Unit {
    const id = `villager-${Date.now()}`;
    const unit = new Unit(this, id, 'villager', 15, 15);
    this.units.set(id, unit);
    return unit;
  }

  selectUnit(id: string) {
    this.clearSelection();
    const unit = this.units.get(id);
    if (!unit) return;
    unit.setSelected(true);
    this.selectedUnits.add(id);
    EventBus.emit('unit-selected', {
      type: 'unit-selected',
      unitId: id,
      profile: unit.profile,
      status: unit.unitStatus,
    });
  }

  clearSelection() {
    for (const id of this.selectedUnits) {
      this.units.get(id)?.setSelected(false);
    }
    this.selectedUnits.clear();
    this.selectedBuilding = null;
    EventBus.emit('selection-cleared', { type: 'selection-cleared' });
  }

  placeBuilding(data: BuildingData): Building {
    const building = new Building(this, data);
    this.buildings.set(data.id, building);

    building.on('pointerdown', () => {
      this.clearSelection();
      this.selectedBuilding = data.id;
      EventBus.emit('building-selected', {
        type: 'building-selected',
        buildingId: data.id,
        buildingData: data,
      });
    });

    return building;
  }

  handleJobSync(jobsData: Array<{ id: string; status: string; agent?: string }>) {
    // Update unit states based on active jobs
    for (const job of jobsData) {
      if (job.status === 'running' && job.agent) {
        const unitId = `${job.agent}-1`;
        const unit = this.units.get(unitId);
        if (unit && unit.unitStatus !== 'working') {
          unit.setUnitStatus('working');
          unit.currentJobId = job.id;
        }
      }
    }

    // Reset units whose jobs completed
    for (const [, unit] of this.units) {
      if (unit.unitStatus === 'working' && unit.currentJobId) {
        const job = jobsData.find(j => j.id === unit.currentJobId);
        if (!job || job.status === 'completed') {
          unit.celebrate();
          unit.currentJobId = undefined;
        } else if (job?.status === 'failed') {
          unit.shake();
          unit.currentJobId = undefined;
        }
      }
    }
  }

  handleDispatchJob(data: { unitId: string; buildingId: string }) {
    const unit = this.units.get(data.unitId);
    const building = this.buildings.get(data.buildingId);
    if (!unit || !building) return;

    const blocked = this.getBlockedTiles();
    // Move unit near building
    const targetCol = building.col - 1;
    const targetRow = building.row;
    unit.moveToTile(targetCol, targetRow, blocked).then(() => {
      unit.setUnitStatus('working');
      building.setBuildingStatus('active');
    });
  }

  handlePlaceBuilding(data: BuildingData) {
    if (this.buildings.has(data.id)) return;
    this.placeBuilding(data);
    EventBus.emit('building-placed', { type: 'building-placed', buildingData: data });
  }

  handleLoadMapState(state: MapState) {
    // Clear existing non-default buildings
    for (const [id, building] of this.buildings) {
      if (id !== 'building-tc-1') {
        building.destroy();
        this.buildings.delete(id);
      }
    }
    // Place loaded buildings
    for (const bData of state.buildings) {
      if (!this.buildings.has(bData.id)) {
        this.placeBuilding(bData);
      }
    }
  }

  getUnitsState(): UnitData[] {
    const state: UnitData[] = [];
    for (const [id, unit] of this.units) {
      state.push({
        id,
        profile: unit.profile,
        status: unit.unitStatus,
        currentJobId: unit.currentJobId,
        homeCol: unit.homeCol,
        homeRow: unit.homeRow,
        col: unit.col,
        row: unit.row,
      });
    }
    return state;
  }

  getBuildingsState(): BuildingData[] {
    const state: BuildingData[] = [];
    for (const [, b] of this.buildings) {
      state.push({
        id: b.buildingId,
        type: b.buildingType,
        status: b.buildingStatus,
        projectId: b.projectId,
        col: b.col,
        row: b.row,
        name: b.buildingName,
      });
    }
    return state;
  }

  shutdown() {
    EventBus.off('dispatch-job-to-building', this.handleDispatchJob, this);
    EventBus.off('place-building', this.handlePlaceBuilding, this);
    EventBus.off('sync-jobs', this.handleJobSync, this);
    EventBus.off('load-map-state', this.handleLoadMapState, this);
  }
}

