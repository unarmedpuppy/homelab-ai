import Phaser from 'phaser';
import { UnitProfile, UnitStatus, UNIT_COLORS } from '../../types/game';
import { tileToWorld, TILE_HALF_H } from '../utils/isometric';
import { findPath } from '../utils/pathfinding';
import { EventBus } from '../EventBus';

const INITIALS: Record<UnitProfile, string> = {
  avery: 'A', gilfoyle: 'G', ralph: 'R', jobin: 'J', villager: 'V',
};

export class Unit extends Phaser.GameObjects.Container {
  public unitId: string;
  public profile: UnitProfile;
  public unitStatus: UnitStatus = 'idle';
  public currentJobId?: string;
  public col: number;
  public row: number;
  public homeCol: number;
  public homeRow: number;
  public selected: boolean = false;

  private bodyGfx: Phaser.GameObjects.Graphics;
  private head: Phaser.GameObjects.Arc;
  private selectionRing: Phaser.GameObjects.Ellipse;
  private statusDot: Phaser.GameObjects.Arc;
  private workingTween?: Phaser.Tweens.Tween;

  constructor(
    scene: Phaser.Scene,
    id: string,
    profile: UnitProfile,
    col: number,
    row: number,
  ) {
    const { x, y } = tileToWorld(col, row);
    super(scene, x, y + TILE_HALF_H);

    this.unitId = id;
    this.profile = profile;
    this.col = col;
    this.row = row;
    this.homeCol = col;
    this.homeRow = row;

    const color = UNIT_COLORS[profile];
    const lightColor = Phaser.Display.Color.IntegerToColor(color);
    lightColor.lighten(28);
    const darkColor = Phaser.Display.Color.IntegerToColor(color);
    darkColor.darken(28);

    // Ground shadow
    const shadow = scene.add.ellipse(0, 7, 28, 10, 0x000000, 0.2);

    // Selection ring (ellipse at base level, gold outline)
    this.selectionRing = scene.add.ellipse(0, 4, 34, 13, 0x000000, 0);
    this.selectionRing.setStrokeStyle(2.5, 0xffee44, 1);
    this.selectionRing.setVisible(false);

    // Body: pawn-like pentagon shape (wider at base, tapers to neck)
    this.bodyGfx = scene.add.graphics();

    // Outer shell (darkened)
    this.bodyGfx.fillStyle(darkColor.color, 1);
    this.bodyGfx.fillPoints([
      { x: -10, y: 5 }, { x: 10, y: 5 },
      { x: 8, y: -3 }, { x: 0, y: -9 }, { x: -8, y: -3 },
    ], true);

    // Inner fill (main faction color)
    this.bodyGfx.fillStyle(color, 1);
    this.bodyGfx.fillPoints([
      { x: -8, y: 4 }, { x: 8, y: 4 },
      { x: 6, y: -2 }, { x: 0, y: -7 }, { x: -6, y: -2 },
    ], true);

    // Highlight streak on body (top-left)
    const hiColor = Phaser.Display.Color.IntegerToColor(color);
    hiColor.lighten(45);
    this.bodyGfx.lineStyle(1.5, hiColor.color, 0.6);
    this.bodyGfx.lineBetween(-7, 3, -5, -5);

    // Body outline
    this.bodyGfx.lineStyle(1.5, 0x000000, 0.55);
    this.bodyGfx.strokePoints([
      { x: -10, y: 5 }, { x: 10, y: 5 },
      { x: 8, y: -3 }, { x: 0, y: -9 }, { x: -8, y: -3 },
    ], true);

    // Head circle (lighter shade of faction color)
    this.head = scene.add.arc(0, -14, 7, 0, 360, false, lightColor.color);
    this.head.setStrokeStyle(1.5, 0x000000, 0.5);

    // Letter initial on head
    const label = scene.add.text(0, -14, INITIALS[profile], {
      fontSize: '8px',
      color: '#ffffff',
      fontFamily: 'Courier New',
      fontStyle: 'bold',
    }).setOrigin(0.5);

    // Status dot (tiny, floats just above head)
    this.statusDot = scene.add.arc(0, -24, 3, 0, 360, false, 0x00cc00);
    this.statusDot.setStrokeStyle(0.5, 0x000000, 0.4);

    this.add([shadow, this.selectionRing, this.bodyGfx, this.head, label, this.statusDot]);
    scene.add.existing(this as unknown as Phaser.GameObjects.GameObject);

    this.setSize(28, 34);
    this.setInteractive();
    // Depth: units always render in front of buildings/tiles at same position
    this.setDepth(10 + col + row);

    this.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.leftButtonDown()) EventBus.emit('unit-clicked', this);
    });
  }

  setSelected(selected: boolean) {
    this.selected = selected;
    this.selectionRing.setVisible(selected);
  }

  setUnitStatus(status: UnitStatus) {
    this.unitStatus = status;
    this.workingTween?.destroy();

    const dotColors: Record<UnitStatus, number> = {
      idle: 0x00cc00,
      moving: 0xffaa00,
      working: 0xffff00,
      done: 0x00ff88,
      error: 0xff2222,
    };
    this.statusDot.setFillStyle(dotColors[status]);

    if (status === 'working') {
      this.workingTween = this.scene.tweens.add({
        targets: this.bodyGfx,
        alpha: 0.45,
        duration: 600,
        yoyo: true,
        repeat: -1,
      });
    } else {
      this.bodyGfx.setAlpha(1);
    }
  }

  async moveToTile(targetCol: number, targetRow: number, blocked: Set<string> = new Set()): Promise<void> {
    if (targetCol === this.col && targetRow === this.row) return;
    this.setUnitStatus('moving');
    const path = findPath(this.col, this.row, targetCol, targetRow, blocked);
    for (const step of path) {
      await this.stepTo(step.col, step.row);
    }
    this.col = targetCol;
    this.row = targetRow;
    if (this.unitStatus === 'moving') this.setUnitStatus('idle');
  }

  private stepTo(col: number, row: number): Promise<void> {
    return new Promise((resolve) => {
      const { x, y } = tileToWorld(col, row);
      this.setDepth(10 + col + row);
      this.scene.tweens.add({
        targets: this,
        x, y: y + TILE_HALF_H,
        duration: 200,
        ease: 'Linear',
        onComplete: () => { this.col = col; this.row = row; resolve(); },
      });
    });
  }

  async returnHome(blocked: Set<string> = new Set()): Promise<void> {
    await this.moveToTile(this.homeCol, this.homeRow, blocked);
  }

  celebrate() {
    this.setUnitStatus('done');
    this.scene.tweens.add({
      targets: this, y: this.y - 8, duration: 150, yoyo: true, repeat: 3,
      onComplete: () => this.setUnitStatus('idle'),
    });
  }

  shake() {
    this.setUnitStatus('error');
    this.scene.tweens.add({
      targets: this, x: this.x + 4, duration: 50, yoyo: true, repeat: 5,
      onComplete: () => this.setUnitStatus('idle'),
    });
  }
}
