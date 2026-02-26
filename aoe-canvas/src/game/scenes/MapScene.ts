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
  TILE_W,
  TILE_H,
} from '../utils/isometric';
import {
  UnitProfile,
  BuildingData,
  UnitData,
  MapState,
} from '../../types/game';

export class MapScene extends Phaser.Scene {
  private tileGraphics!: Phaser.GameObjects.Graphics;
  private units: Map<string, Unit> = new Map();
  private buildings: Map<string, Building> = new Map();
  private selectionBox!: SelectionBox;
  private selectedUnits: Set<string> = new Set();
  private selectedBuilding: string | null = null;
  private dragStart?: { x: number; y: number };
  private isDragging = false;
  private isBoxSelecting = false;
  private boxSelectStart?: { x: number; y: number };
  private cursors?: Phaser.Types.Input.Keyboard.CursorKeys;
  private hoveredTile: { col: number; row: number } | null = null;
  private tileOverlay!: Phaser.GameObjects.Graphics;

  constructor() {
    super({ key: 'MapScene' });
  }

  create() {
    // World bounds
    const worldW = (GRID_COLS + GRID_ROWS) * TILE_HALF_W + 200;
    const worldH = (GRID_COLS + GRID_ROWS) * TILE_HALF_H + 200;

    this.cameras.main.setBounds(-worldW / 2, -100, worldW, worldH + 200);
    this.cameras.main.setZoom(1.0);

    // Center camera on map center
    const center = tileToWorld(16, 16);
    this.cameras.main.centerOn(center.x, center.y + 100);

    // Draw tile grid
    this.tileGraphics = this.add.graphics();
    this.tileOverlay = this.add.graphics();
    this.tileOverlay.setDepth(1);
    this.drawTiles();

    // Selection box
    this.selectionBox = new SelectionBox(this);

    // Place initial units
    this.spawnNamedUnit('avery-1', 'avery', 14, 14);
    this.spawnNamedUnit('gilfoyle-1', 'gilfoyle', 15, 14);
    this.spawnNamedUnit('ralph-1', 'ralph', 16, 14);
    this.spawnNamedUnit('jobin-1', 'jobin', 17, 14);

    // Place default Town Center building
    this.placeBuilding({
      id: 'building-tc-1',
      type: 'town-center',
      status: 'idle',
      col: 16,
      row: 16,
      name: 'Town Center',
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

  private drawTiles() {
    this.tileGraphics.clear();

    for (let row = 0; row < GRID_ROWS; row++) {
      for (let col = 0; col < GRID_COLS; col++) {
        const { x, y } = tileToWorld(col, row);
        const isEven = (col + row) % 2 === 0;

        // Alternate grass shades
        const baseColor = isEven ? 0x4a7c34 : 0x527a3c;

        this.tileGraphics.fillStyle(baseColor, 1);
        this.tileGraphics.fillPoints([
          { x, y },
          { x: x + TILE_HALF_W, y: y + TILE_HALF_H },
          { x, y: y + TILE_H },
          { x: x - TILE_HALF_W, y: y + TILE_HALF_H },
        ], true);

        // Tile border
        this.tileGraphics.lineStyle(0.5, 0x000000, 0.15);
        this.tileGraphics.strokePoints([
          { x, y },
          { x: x + TILE_HALF_W, y: y + TILE_HALF_H },
          { x, y: y + TILE_H },
          { x: x - TILE_HALF_W, y: y + TILE_HALF_H },
        ], true);
      }
    }
  }

  private setupInput() {
    const cam = this.cameras.main;

    this.input.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.middleButtonDown() || ptr.rightButtonDown()) {
        this.dragStart = { x: ptr.x, y: ptr.y };
        this.isDragging = true;
      }

      if (ptr.leftButtonDown()) {
        this.boxSelectStart = { x: ptr.worldX, y: ptr.worldY };
        this.isBoxSelecting = false;
        this.selectionBox.start(ptr.x, ptr.y);
      }
    });

    this.input.on('pointermove', (ptr: Phaser.Input.Pointer) => {
      // Camera pan
      if (this.isDragging && this.dragStart) {
        const dx = ptr.x - this.dragStart.x;
        const dy = ptr.y - this.dragStart.y;
        cam.scrollX -= dx / cam.zoom;
        cam.scrollY -= dy / cam.zoom;
        this.dragStart = { x: ptr.x, y: ptr.y };
      }

      // Box select
      if (ptr.leftButtonDown() && this.boxSelectStart) {
        const dist = Phaser.Math.Distance.Between(ptr.worldX, ptr.worldY, this.boxSelectStart.x, this.boxSelectStart.y);
        if (dist > 10) {
          this.isBoxSelecting = true;
          this.selectionBox.update(ptr.x, ptr.y);
        }
      }

      // Tile hover
      const tilePos = worldToTile(ptr.worldX, ptr.worldY - TILE_HALF_H);
      if (!this.hoveredTile || this.hoveredTile.col !== tilePos.col || this.hoveredTile.row !== tilePos.row) {
        this.hoveredTile = tilePos;
        this.drawTileHover();
      }
    });

    this.input.on('pointerup', (ptr: Phaser.Input.Pointer) => {
      if (ptr.middleButtonReleased() || ptr.rightButtonReleased()) {
        // Right-click context (only if not dragging far)
        if (ptr.rightButtonReleased() && !this.isDragging) {
          const tilePos = worldToTile(ptr.worldX, ptr.worldY - TILE_HALF_H);
          this.handleRightClick(tilePos.col, tilePos.row);
        }
        this.isDragging = false;
        this.dragStart = undefined;
      }

      if (ptr.leftButtonReleased()) {
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

// Suppress unused warnings for tile dimension constants referenced from isometric.ts
void TILE_W;
void TILE_H;
