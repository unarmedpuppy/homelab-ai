import Phaser from 'phaser';
import { BuildingData, BuildingStatus, BuildingType, BUILDING_COLORS, BUILDING_LABELS } from '../../types/game';
import { tileToWorld, TILE_HALF_W, TILE_HALF_H, TILE_W, TILE_H } from '../utils/isometric';
import { EventBus } from '../EventBus';

export class Building extends Phaser.GameObjects.Container {
  public buildingId: string;
  public buildingType: BuildingType;
  public buildingStatus: BuildingStatus;
  public projectId?: string;
  public col: number;
  public row: number;
  public buildingName: string;

  private base: Phaser.GameObjects.Graphics;
  private roof: Phaser.GameObjects.Graphics;
  private label: Phaser.GameObjects.Text;
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
    const lbl = BUILDING_LABELS[data.type];

    // Draw isometric box
    this.base = scene.add.graphics();
    this.drawBase(color);

    this.roof = scene.add.graphics();
    this.drawRoof(color);

    this.label = scene.add.text(0, -20, lbl, {
      fontSize: '9px',
      color: '#ffffff',
      fontFamily: 'Courier New',
      fontStyle: 'bold',
      backgroundColor: '#00000088',
      padding: { x: 2, y: 1 },
    }).setOrigin(0.5);

    this.add([this.base, this.roof, this.label]);
    scene.add.existing(this as unknown as Phaser.GameObjects.GameObject);

    this.setSize(TILE_W * 1.5, TILE_H * 2);
    this.setInteractive();
    this.setDepth(5 + data.col + data.row);

    this.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.leftButtonDown()) {
        EventBus.emit('building-clicked', this);
      }
    });

    this.setBuildingStatus(data.status);
  }

  private drawBase(color: number) {
    this.base.clear();
    const hw = TILE_HALF_W;
    const hh = TILE_HALF_H;
    const wallH = 16;

    const darkerColor = Phaser.Display.Color.IntegerToColor(color);
    darkerColor.darken(30);
    const darkColor = darkerColor.color;

    // Left wall (darker)
    this.base.fillStyle(darkColor, 1);
    this.base.fillPoints([
      { x: -hw, y: hh }, { x: 0, y: hh * 2 }, { x: 0, y: hh * 2 + wallH }, { x: -hw, y: hh + wallH },
    ], true);

    // Right wall (medium)
    const medColor = Phaser.Display.Color.IntegerToColor(color);
    medColor.darken(15);
    this.base.fillStyle(medColor.color, 1);
    this.base.fillPoints([
      { x: 0, y: hh * 2 }, { x: hw, y: hh }, { x: hw, y: hh + wallH }, { x: 0, y: hh * 2 + wallH },
    ], true);
  }

  private drawRoof(color: number) {
    this.roof.clear();
    const hw = TILE_HALF_W;
    const hh = TILE_HALF_H;

    // Isometric diamond top face
    this.roof.fillStyle(color, 1);
    this.roof.fillPoints([
      { x: 0, y: 0 }, { x: hw, y: hh }, { x: 0, y: hh * 2 }, { x: -hw, y: hh },
    ], true);

    // Outline
    this.roof.lineStyle(1, 0x000000, 0.3);
    this.roof.strokePoints([
      { x: 0, y: 0 }, { x: hw, y: hh }, { x: 0, y: hh * 2 }, { x: -hw, y: hh },
    ], true);
  }

  setBuildingStatus(status: BuildingStatus) {
    this.buildingStatus = status;
    this.glowTween?.destroy();

    if (status === 'active') {
      // Gold pulse when job is running
      this.glowTween = this.scene.tweens.add({
        targets: this.roof,
        alpha: 0.6,
        duration: 800,
        yoyo: true,
        repeat: -1,
      });
    } else {
      this.roof.setAlpha(1);
    }
  }
}
