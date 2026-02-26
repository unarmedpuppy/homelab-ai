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
    const wallHeights: Record<BuildingType, number> = {
      'town-center': 30,
      'castle': 26,
      'university': 22,
      'barracks': 18,
      'market': 16,
    };
    const wallH = wallHeights[this.buildingType];

    // Left wall (deep shadow — darkest face)
    const leftColor = Phaser.Display.Color.IntegerToColor(color);
    leftColor.darken(40);
    this.base.fillStyle(leftColor.color, 1);
    this.base.fillPoints([
      { x: -hw, y: hh }, { x: 0, y: hh * 2 }, { x: 0, y: hh * 2 + wallH }, { x: -hw, y: hh + wallH },
    ], true);

    // Right wall (medium shadow)
    const rightColor = Phaser.Display.Color.IntegerToColor(color);
    rightColor.darken(20);
    this.base.fillStyle(rightColor.color, 1);
    this.base.fillPoints([
      { x: 0, y: hh * 2 }, { x: hw, y: hh }, { x: hw, y: hh + wallH }, { x: 0, y: hh * 2 + wallH },
    ], true);

    // Wall outlines for crisp edges
    this.base.lineStyle(1, 0x000000, 0.5);
    this.base.strokePoints([
      { x: -hw, y: hh }, { x: 0, y: hh * 2 }, { x: 0, y: hh * 2 + wallH }, { x: -hw, y: hh + wallH },
    ], true);
    this.base.strokePoints([
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

    // NW + NE edge highlight (sun-lit top ridge)
    const hiColor = Phaser.Display.Color.IntegerToColor(color);
    hiColor.lighten(30);
    this.roof.lineStyle(2, hiColor.color, 0.9);
    this.roof.lineBetween(0, 0, -hw, hh);
    this.roof.lineBetween(0, 0, hw, hh);

    // Outline
    this.roof.lineStyle(1, 0x000000, 0.4);
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
