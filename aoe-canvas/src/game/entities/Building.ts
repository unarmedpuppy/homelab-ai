import Phaser from 'phaser';
import { BuildingData, BuildingStatus, BuildingType, BUILDING_COLORS } from '../../types/game';
import { tileToWorld, TILE_HALF_W, TILE_HALF_H, TILE_W, TILE_H } from '../utils/isometric';
import { EventBus } from '../EventBus';

const WALL_H: Record<BuildingType, number> = {
  'town-center': 28,
  'castle': 26,
  'university': 22,
  'barracks': 18,
  'market': 14,
};

// Extra height above tile N vertex occupied by rooftop elements
const ROOFTOP_H: Record<BuildingType, number> = {
  'town-center': 22,  // central tower
  'castle': 10,       // battlements
  'university': 24,   // spire
  'barracks': 16,     // flag
  'market': 4,
};

// Suppress unused import warnings
void TILE_H;

export class Building extends Phaser.GameObjects.Container {
  public buildingId: string;
  public buildingType: BuildingType;
  public buildingStatus: BuildingStatus;
  public projectId?: string;
  public col: number;
  public row: number;
  public buildingName: string;

  private walls: Phaser.GameObjects.Graphics;
  private roofGfx: Phaser.GameObjects.Graphics;
  private details: Phaser.GameObjects.Graphics;
  private nameLabel: Phaser.GameObjects.Text;
  private glowTween?: Phaser.Tweens.Tween;

  constructor(scene: Phaser.Scene, data: BuildingData) {
    const { x, y } = tileToWorld(data.col, data.row);
    super(scene, x, y + TILE_HALF_H);

    this.buildingId = data.id;
    this.buildingType = data.type;
    this.buildingStatus = data.status;
    this.projectId = data.projectId;
    this.col = data.col;
    this.row = data.row;
    this.buildingName = data.name;

    const color = BUILDING_COLORS[data.type];

    // Ground shadow ellipse anchored at tile center
    const shadow = scene.add.graphics();
    shadow.fillStyle(0x000000, 0.22);
    shadow.fillEllipse(0, TILE_HALF_H * 2 + 4, TILE_W * 1.1, TILE_HALF_H * 0.8);

    this.walls = scene.add.graphics();
    this.roofGfx = scene.add.graphics();
    this.details = scene.add.graphics();

    // Label floats above the tallest point (tile N vertex + rooftop elements)
    const labelY = -(TILE_HALF_H + ROOFTOP_H[data.type] + 10);
    this.nameLabel = scene.add.text(0, labelY, data.name.toUpperCase(), {
      fontSize: '7px',
      color: '#ffe4a0',
      fontFamily: 'Courier New',
      fontStyle: 'bold',
      backgroundColor: '#00000088',
      padding: { x: 3, y: 2 },
    }).setOrigin(0.5);

    this.add([shadow, this.walls, this.roofGfx, this.details, this.nameLabel]);
    scene.add.existing(this as unknown as Phaser.GameObjects.GameObject);

    this.setSize(TILE_W * 1.5, TILE_H * 3);
    this.setInteractive();
    this.setDepth(5 + data.col + data.row);

    this.draw(color);

    this.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.leftButtonDown()) EventBus.emit('building-clicked', this);
    });

    this.setBuildingStatus(data.status);
  }

  private draw(color: number) {
    this.drawWalls(color);
    this.drawRoof(color);
    this.drawDetails(color);
  }

  // ─── Walls ────────────────────────────────────────────────────────────────

  private drawWalls(color: number) {
    const g = this.walls;
    g.clear();
    const hw = TILE_HALF_W, hh = TILE_HALF_H;
    const wh = WALL_H[this.buildingType];

    // Left wall (NW face — deep shadow)
    const lc = Phaser.Display.Color.IntegerToColor(color); lc.darken(44);
    g.fillStyle(lc.color, 1);
    g.fillPoints([
      { x: -hw, y: hh }, { x: 0, y: hh * 2 },
      { x: 0, y: hh * 2 + wh }, { x: -hw, y: hh + wh },
    ], true);

    // Right wall (SE face — mid shadow)
    const rc = Phaser.Display.Color.IntegerToColor(color); rc.darken(22);
    g.fillStyle(rc.color, 1);
    g.fillPoints([
      { x: 0, y: hh * 2 }, { x: hw, y: hh },
      { x: hw, y: hh + wh }, { x: 0, y: hh * 2 + wh },
    ], true);

    // Wall outlines
    g.lineStyle(1, 0x000000, 0.7);
    g.strokePoints([
      { x: -hw, y: hh }, { x: 0, y: hh * 2 },
      { x: 0, y: hh * 2 + wh }, { x: -hw, y: hh + wh },
    ], true);
    g.strokePoints([
      { x: 0, y: hh * 2 }, { x: hw, y: hh },
      { x: hw, y: hh + wh }, { x: 0, y: hh * 2 + wh },
    ], true);
    g.strokePoints([
      { x: -hw, y: hh + wh }, { x: 0, y: hh * 2 + wh }, { x: hw, y: hh + wh },
    ], false);
  }

  // ─── Roof ─────────────────────────────────────────────────────────────────

  private drawRoof(color: number) {
    const g = this.roofGfx;
    g.clear();
    const hw = TILE_HALF_W, hh = TILE_HALF_H;

    const tc = Phaser.Display.Color.IntegerToColor(color); tc.lighten(20);
    g.fillStyle(tc.color, 1);
    g.fillPoints([
      { x: 0, y: 0 }, { x: hw, y: hh }, { x: 0, y: hh * 2 }, { x: -hw, y: hh },
    ], true);

    // Sun-lit NW + NE ridge highlights
    const hi = Phaser.Display.Color.IntegerToColor(color); hi.lighten(50);
    g.lineStyle(2, hi.color, 0.9);
    g.lineBetween(0, 0, -hw, hh);
    g.lineBetween(0, 0, hw, hh);

    g.lineStyle(1, 0x000000, 0.55);
    g.strokePoints([
      { x: 0, y: 0 }, { x: hw, y: hh }, { x: 0, y: hh * 2 }, { x: -hw, y: hh },
    ], true);
  }

  // ─── Type-specific details ────────────────────────────────────────────────

  private drawDetails(color: number) {
    this.details.clear();
    const g = this.details;
    const hw = TILE_HALF_W, hh = TILE_HALF_H;
    const wh = WALL_H[this.buildingType];

    switch (this.buildingType) {

      case 'town-center': {
        // Windows on both walls
        this.winRight(g, wh, 0.28, 0.22, 0.72, 0.68);
        this.winLeft(g, wh, 0.25, 0.25, 0.75, 0.68);

        // Central tower rising above roof
        const thw = hw * 0.4, thh = hh * 0.4, tH = 22;
        // Tower left wall
        const tlc = Phaser.Display.Color.IntegerToColor(color); tlc.darken(38);
        g.fillStyle(tlc.color, 1);
        g.fillPoints([
          { x: -thw, y: thh }, { x: 0, y: thh * 2 },
          { x: 0, y: thh * 2 - tH }, { x: -thw, y: thh - tH },
        ], true);
        // Tower right wall
        const trc = Phaser.Display.Color.IntegerToColor(color); trc.darken(18);
        g.fillStyle(trc.color, 1);
        g.fillPoints([
          { x: 0, y: thh * 2 }, { x: thw, y: thh },
          { x: thw, y: thh - tH }, { x: 0, y: thh * 2 - tH },
        ], true);
        // Tower roof
        const ttc = Phaser.Display.Color.IntegerToColor(color); ttc.lighten(28);
        g.fillStyle(ttc.color, 1);
        g.fillPoints([
          { x: 0, y: -tH }, { x: thw, y: thh - tH },
          { x: 0, y: thh * 2 - tH }, { x: -thw, y: thh - tH },
        ], true);
        // Tower ridge highlight
        const tri = Phaser.Display.Color.IntegerToColor(color); tri.lighten(55);
        g.lineStyle(1.5, tri.color, 0.8);
        g.lineBetween(0, -tH, -thw, thh - tH);
        g.lineBetween(0, -tH, thw, thh - tH);
        // Tower outlines
        g.lineStyle(1, 0x000000, 0.55);
        g.strokePoints([
          { x: -thw, y: thh }, { x: 0, y: thh * 2 },
          { x: 0, y: thh * 2 - tH }, { x: -thw, y: thh - tH },
        ], true);
        g.strokePoints([
          { x: 0, y: thh * 2 }, { x: thw, y: thh },
          { x: thw, y: thh - tH }, { x: 0, y: thh * 2 - tH },
        ], true);
        g.strokePoints([
          { x: 0, y: -tH }, { x: thw, y: thh - tH },
          { x: 0, y: thh * 2 - tH }, { x: -thw, y: thh - tH },
        ], true);
        // Flag pole on tower (slightly right of center)
        const px = thw * 0.5, py = -tH;
        g.lineStyle(1.5, 0x3a1e06, 1);
        g.lineBetween(px, py, px, py - 14);
        // Flag banner
        g.fillStyle(0xcc2200, 1);
        g.fillTriangle(px, py - 14, px + 12, py - 9, px, py - 4);
        g.lineStyle(0.75, 0x000000, 0.5);
        g.strokeTriangle(px, py - 14, px + 12, py - 9, px, py - 4);
        break;
      }

      case 'castle': {
        // Arrow slits on right wall
        const slX = hw * 0.52, slY0 = hh * 2 - hh * 0.52 + wh * 0.18;
        const slY1 = hh * 2 - hh * 0.52 + wh * 0.78;
        g.fillStyle(0x000000, 0.9);
        g.fillRect(slX - 1.5, slY0, 3, slY1 - slY0);
        // Cross slit
        g.fillRect(slX - 4, slY0 + (slY1 - slY0) * 0.35, 8, 2.5);

        // Merlons along LEFT wall top edge: (-hw, hh) → (0, hh*2)
        const lmc = Phaser.Display.Color.IntegerToColor(color); lmc.darken(40);
        const rmc = Phaser.Display.Color.IntegerToColor(color); rmc.darken(18);
        const mCount = 3, mH = 7;
        for (let i = 0; i < mCount; i++) {
          const t0 = i / mCount, t1 = (i + 0.55) / mCount;
          const lx0 = -hw + hw * t0, ly0 = hh + hh * t0;
          const lx1 = -hw + hw * t1, ly1 = hh + hh * t1;
          g.fillStyle(lmc.color, 1);
          g.fillPoints([
            { x: lx0, y: ly0 }, { x: lx1, y: ly1 },
            { x: lx1, y: ly1 + mH }, { x: lx0, y: ly0 + mH },
          ], true);
          g.lineStyle(0.75, 0x000000, 0.65);
          g.strokePoints([
            { x: lx0, y: ly0 }, { x: lx1, y: ly1 },
            { x: lx1, y: ly1 + mH }, { x: lx0, y: ly0 + mH },
          ], true);
          // Right wall merlons: (0, hh*2) → (hw, hh)
          const rx0 = hw * t0, ry0 = hh * 2 - hh * t0;
          const rx1 = hw * t1, ry1 = hh * 2 - hh * t1;
          g.fillStyle(rmc.color, 1);
          g.fillPoints([
            { x: rx0, y: ry0 }, { x: rx1, y: ry1 },
            { x: rx1, y: ry1 + mH }, { x: rx0, y: ry0 + mH },
          ], true);
          g.lineStyle(0.75, 0x000000, 0.65);
          g.strokePoints([
            { x: rx0, y: ry0 }, { x: rx1, y: ry1 },
            { x: rx1, y: ry1 + mH }, { x: rx0, y: ry0 + mH },
          ], true);
        }
        // Banner on left battlement
        const bpx = -hw * 0.62, bpy = hh * 0.42;
        g.lineStyle(1.5, 0x555555, 1);
        g.lineBetween(bpx, bpy, bpx, bpy - 14);
        g.fillStyle(0x880000, 1);
        g.fillTriangle(bpx, bpy - 14, bpx + 10, bpy - 9, bpx, bpy - 5);
        break;
      }

      case 'university': {
        // Large arched window on right wall
        this.winRight(g, wh, 0.18, 0.12, 0.82, 0.78);
        // Small window on left wall
        this.winLeft(g, wh, 0.28, 0.28, 0.72, 0.72);

        // Spire from roof center (N vertex at (0,0))
        g.lineStyle(2.5, 0x1a1a8e, 1);
        g.lineBetween(0, 0, 0, -20);
        // Spire head (colored to match building)
        const spC = Phaser.Display.Color.IntegerToColor(color); spC.lighten(55);
        g.fillStyle(spC.color, 1);
        g.fillTriangle(0, -22, -5, -12, 5, -12);
        g.lineStyle(1, 0x000000, 0.6);
        g.strokeTriangle(0, -22, -5, -12, 5, -12);
        // Gold orb at tip
        g.fillStyle(0xffdd44, 1);
        g.fillCircle(0, -22, 2.5);
        g.lineStyle(0.75, 0x000000, 0.5);
        g.strokeCircle(0, -22, 2.5);
        break;
      }

      case 'barracks': {
        // Crossed swords emblem on right wall
        // Right wall center: (th=0.5, tv=0.5) → x=16, y=32-8+wh*0.5
        const sx = hw * 0.5, sy = hh * 2 - hh * 0.5 + wh * 0.5;
        // Blade 1
        g.lineStyle(2.5, 0xddddcc, 0.9);
        g.lineBetween(sx - 7, sy - 6, sx + 7, sy + 6);
        // Blade 2
        g.lineBetween(sx + 7, sy - 6, sx - 7, sy + 6);
        // Crossguards
        g.lineStyle(2, 0xaaaaaa, 0.8);
        g.lineBetween(sx - 5, sy - 4, sx + 5, sy - 1);
        g.lineBetween(sx - 5, sy + 1, sx + 5, sy + 4);
        // Handle pommels
        g.fillStyle(0x888888, 0.9);
        g.fillCircle(sx - 7, sy - 6, 2);
        g.fillCircle(sx + 7, sy + 6, 2);

        // Flag pole + pennant
        const fpx = -hw * 0.55, fpy = hh * 0.38;
        g.lineStyle(1.5, 0x3a1808, 1);
        g.lineBetween(fpx, fpy, fpx, fpy - 17);
        g.fillStyle(0x991a00, 1);
        g.fillTriangle(fpx, fpy - 17, fpx + 11, fpy - 12, fpx, fpy - 7);
        g.lineStyle(0.75, 0x000000, 0.4);
        g.strokeTriangle(fpx, fpy - 17, fpx + 11, fpy - 12, fpx, fpy - 7);
        break;
      }

      case 'market': {
        // Window on right wall
        this.winRight(g, wh, 0.22, 0.18, 0.78, 0.78);

        // Canopy/awning extending from SE wall bottom edge
        // Right wall bottom: (0, hh*2+wh) → (hw, hh+wh)
        const awC = Phaser.Display.Color.IntegerToColor(color); awC.darken(8);
        g.fillStyle(awC.color, 0.95);
        g.fillPoints([
          { x: 0, y: hh * 2 + wh },
          { x: hw, y: hh + wh },
          { x: hw + 12, y: hh + wh + 7 },
          { x: 2, y: hh * 2 + wh + 8 },
        ], true);
        // Awning stripes (yellow)
        for (let i = 1; i <= 3; i++) {
          const t = i / 4;
          const ax = hw * t, ay = hh * 2 - hh * t + wh;
          g.lineStyle(2, 0xffdd55, 0.55);
          g.lineBetween(ax, ay, ax + 3, ay + 8);
        }
        g.lineStyle(1, 0x000000, 0.45);
        g.strokePoints([
          { x: 0, y: hh * 2 + wh }, { x: hw, y: hh + wh },
          { x: hw + 12, y: hh + wh + 7 }, { x: 2, y: hh * 2 + wh + 8 },
        ], true);
        break;
      }
    }
  }

  // ─── Window helpers ───────────────────────────────────────────────────────
  // Right wall point at (th, tv): x = hw*th, y = hh*2 - hh*th + wh*tv
  private winRight(g: Phaser.GameObjects.Graphics, wh: number,
    th0: number, tv0: number, th1: number, tv1: number) {
    const hw = TILE_HALF_W, hh = TILE_HALF_H;
    const pts = [
      { x: hw * th0, y: hh * 2 - hh * th0 + wh * tv0 },
      { x: hw * th1, y: hh * 2 - hh * th1 + wh * tv0 },
      { x: hw * th1, y: hh * 2 - hh * th1 + wh * tv1 },
      { x: hw * th0, y: hh * 2 - hh * th0 + wh * tv1 },
    ];
    g.fillStyle(0x000000, 0.72);
    g.fillPoints(pts, true);
    g.fillStyle(0xffcc44, 0.75);
    g.fillPoints([
      { x: pts[0].x + 2, y: pts[0].y + 1.5 },
      { x: pts[1].x - 2, y: pts[1].y + 1.5 },
      { x: pts[2].x - 2, y: pts[2].y - 1.5 },
      { x: pts[3].x + 2, y: pts[3].y - 1.5 },
    ], true);
  }

  // Left wall point at (th, tv): x = hw*(th-1), y = hh + hh*th + wh*tv
  private winLeft(g: Phaser.GameObjects.Graphics, wh: number,
    th0: number, tv0: number, th1: number, tv1: number) {
    const hw = TILE_HALF_W, hh = TILE_HALF_H;
    const pts = [
      { x: hw * (th0 - 1), y: hh + hh * th0 + wh * tv0 },
      { x: hw * (th1 - 1), y: hh + hh * th1 + wh * tv0 },
      { x: hw * (th1 - 1), y: hh + hh * th1 + wh * tv1 },
      { x: hw * (th0 - 1), y: hh + hh * th0 + wh * tv1 },
    ];
    g.fillStyle(0x000000, 0.72);
    g.fillPoints(pts, true);
    g.fillStyle(0xffcc44, 0.75);
    g.fillPoints([
      { x: pts[0].x + 2, y: pts[0].y + 1.5 },
      { x: pts[1].x - 2, y: pts[1].y + 1.5 },
      { x: pts[2].x - 2, y: pts[2].y - 1.5 },
      { x: pts[3].x + 2, y: pts[3].y - 1.5 },
    ], true);
  }

  // ─── Status ───────────────────────────────────────────────────────────────

  setBuildingStatus(status: BuildingStatus) {
    this.buildingStatus = status;
    this.glowTween?.destroy();
    if (status === 'active') {
      this.glowTween = this.scene.tweens.add({
        targets: this.roofGfx,
        alpha: 0.6,
        duration: 800,
        yoyo: true,
        repeat: -1,
      });
    } else {
      this.roofGfx.setAlpha(1);
    }
  }
}
