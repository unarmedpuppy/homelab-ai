import Phaser from 'phaser';
import { UnitProfile, UnitStatus, UNIT_COLORS, UNIT_LABELS } from '../../types/game';
import { tileToWorld, TILE_HALF_H } from '../utils/isometric';
import { findPath } from '../utils/pathfinding';
import { EventBus } from '../EventBus';

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

  // Prefixed to avoid collision with Container/GameObject base properties
  private unitBody: Phaser.GameObjects.Arc;
  private unitLabel: Phaser.GameObjects.Text;
  private statusDot: Phaser.GameObjects.Arc;
  private selectionRing: Phaser.GameObjects.Arc;
  private shadow!: Phaser.GameObjects.Ellipse;
  private workingTween?: Phaser.Tweens.Tween;

  constructor(
    scene: Phaser.Scene,
    id: string,
    profile: UnitProfile,
    col: number,
    row: number,
  ) {
    const { x, y } = tileToWorld(col, row);
    super(scene, x, y + TILE_HALF_H); // center on tile

    this.unitId = id;
    this.profile = profile;
    this.col = col;
    this.row = row;
    this.homeCol = col;
    this.homeRow = row;

    const color = UNIT_COLORS[profile];
    const letter = UNIT_LABELS[profile];

    // Drop shadow (renders first, behind everything)
    this.shadow = scene.add.ellipse(0, 8, 26, 9, 0x000000, 0.25);

    // Selection ring (behind body)
    this.selectionRing = scene.add.arc(0, 0, 18, 0, 360, false, 0xffee44, 0.6);
    this.selectionRing.setVisible(false);

    // Body circle
    this.unitBody = scene.add.arc(0, 0, 13, 0, 360, false, color);
    this.unitBody.setStrokeStyle(1.5, 0x000000, 0.6);

    // Label text
    this.unitLabel = scene.add.text(0, 0, letter, {
      fontSize: '11px',
      color: '#ffffff',
      fontFamily: 'Courier New',
      fontStyle: 'bold',
    }).setOrigin(0.5);

    // Status dot (top-right)
    this.statusDot = scene.add.arc(11, -11, 5, 0, 360, false, 0x00ff00);

    this.add([this.shadow, this.selectionRing, this.unitBody, this.unitLabel, this.statusDot]);
    scene.add.existing(this as unknown as Phaser.GameObjects.GameObject);

    // Make interactive
    this.setSize(30, 30);
    this.setInteractive();

    this.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.leftButtonDown()) {
        EventBus.emit('unit-clicked', this);
      }
    });

    this.setDepth(10);
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
        targets: this.unitBody,
        alpha: 0.4,
        duration: 600,
        yoyo: true,
        repeat: -1,
      });
    } else {
      this.unitBody.setAlpha(1);
    }
  }

  /** Move unit to tile via A* path. Returns a promise that resolves when done. */
  async moveToTile(targetCol: number, targetRow: number, blocked: Set<string> = new Set()): Promise<void> {
    if (targetCol === this.col && targetRow === this.row) return;

    this.setUnitStatus('moving');
    const path = findPath(this.col, this.row, targetCol, targetRow, blocked);

    for (const step of path) {
      await this.stepTo(step.col, step.row);
    }

    this.col = targetCol;
    this.row = targetRow;
    if (this.unitStatus === 'moving') {
      this.setUnitStatus('idle');
    }
  }

  private stepTo(col: number, row: number): Promise<void> {
    return new Promise((resolve) => {
      const { x, y } = tileToWorld(col, row);
      const targetX = x;
      const targetY = y + TILE_HALF_H;

      // Update depth for isometric draw order
      this.setDepth(10 + col + row);

      this.scene.tweens.add({
        targets: this,
        x: targetX,
        y: targetY,
        duration: 200,
        ease: 'Linear',
        onComplete: () => {
          this.col = col;
          this.row = row;
          resolve();
        },
      });
    });
  }

  /** Return unit to its home tile */
  async returnHome(blocked: Set<string> = new Set()): Promise<void> {
    await this.moveToTile(this.homeCol, this.homeRow, blocked);
  }

  celebrate() {
    this.setUnitStatus('done');
    this.scene.tweens.add({
      targets: this,
      y: this.y - 8,
      duration: 150,
      yoyo: true,
      repeat: 3,
      onComplete: () => {
        this.setUnitStatus('idle');
      },
    });
  }

  shake() {
    this.setUnitStatus('error');
    this.scene.tweens.add({
      targets: this,
      x: this.x + 4,
      duration: 50,
      yoyo: true,
      repeat: 5,
      onComplete: () => {
        this.setUnitStatus('idle');
      },
    });
  }
}
