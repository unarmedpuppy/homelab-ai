import Phaser from 'phaser';
import { UnitProfile, UnitStatus } from '../../types/game';
import { tileToWorld, TILE_HALF_H } from '../utils/isometric';
import { findPath } from '../utils/pathfinding';
import { EventBus } from '../EventBus';

// Sprite origin Y: positions feet near ground shadow
const ORIGIN_Y = 0.85;
const SPRITE_W = 32;
const SPRITE_H = 48;

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

  private sprite: Phaser.GameObjects.Sprite;
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

    // Ground shadow
    const shadow = scene.add.ellipse(0, 7, 28, 10, 0x000000, 0.2);

    // Selection ring at ground level
    this.selectionRing = scene.add.ellipse(0, 4, 34, 13, 0x000000, 0);
    this.selectionRing.setStrokeStyle(2.5, 0xffee44, 1);
    this.selectionRing.setVisible(false);

    // Character sprite
    this.sprite = scene.add.sprite(0, 0, `unit-${profile === 'colin' ? 'villager' : profile}`, 0);
    this.sprite.setOrigin(0.5, ORIGIN_Y);
    this.sprite.setDisplaySize(SPRITE_W, SPRITE_H);
    this.sprite.play(`${profile}-idle`);

    // Switch back to idle after non-looping animations complete
    this.sprite.on('animationcomplete', (anim: Phaser.Animations.Animation) => {
      if (anim.key === `${this.profile}-celebrate` || anim.key === `${this.profile}-error`) {
        this.sprite.play(`${this.profile}-idle`);
      }
    });

    // Status dot floats above sprite
    const dotY = -(ORIGIN_Y * SPRITE_H + 6);
    this.statusDot = scene.add.arc(0, dotY, 3, 0, 360, false, 0x00cc00);
    this.statusDot.setStrokeStyle(0.5, 0x000000, 0.4);

    this.add([shadow, this.selectionRing, this.sprite, this.statusDot]);
    scene.add.existing(this as unknown as Phaser.GameObjects.GameObject);

    this.setSize(SPRITE_W, SPRITE_H - 4);
    this.setInteractive();
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
      idle:    0x00cc00,
      moving:  0xffaa00,
      working: 0xffff00,
      done:    0x00ff88,
      error:   0xff2222,
    };
    this.statusDot.setFillStyle(dotColors[status]);

    // Drive animation from status
    switch (status) {
      case 'idle':
        this.sprite.play(`${this.profile}-idle`);
        this.sprite.setAlpha(1);
        break;
      case 'moving':
        this.sprite.play(`${this.profile}-walk`);
        break;
      case 'working':
        this.sprite.play(`${this.profile}-work`);
        this.workingTween = this.scene.tweens.add({
          targets: this.sprite,
          alpha: 0.6,
          duration: 600,
          yoyo: true,
          repeat: -1,
        });
        break;
      case 'done':
        this.sprite.play(`${this.profile}-celebrate`);
        break;
      case 'error':
        this.sprite.play(`${this.profile}-error`);
        break;
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
