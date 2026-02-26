import Phaser from 'phaser';
import { BuildingData, BuildingStatus, BuildingType } from '../../types/game';
import { tileToWorld, TILE_HALF_H, TILE_W, TILE_H } from '../utils/isometric';
import { EventBus } from '../EventBus';

const BUILDING_FRAME: Record<BuildingType, number> = {
  'town-center': 0,
  'castle':      1,
  'barracks':    2,
  'market':      3,
  'university':  4,
};

// Origin Y for the building sprite: positions visual floor near tile S-vertex
const ORIGIN_Y = 0.70;
const SPRITE_W = 96;
const SPRITE_H = 96;

export class Building extends Phaser.GameObjects.Container {
  public buildingId: string;
  public buildingType: BuildingType;
  public buildingStatus: BuildingStatus;
  public projectId?: string;
  public col: number;
  public row: number;
  public buildingName: string;

  private sprite: Phaser.GameObjects.Sprite;
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

    // Ground shadow at visual floor level (below origin)
    const floorY = (1 - ORIGIN_Y) * SPRITE_H;
    const shadow = scene.add.graphics();
    shadow.fillStyle(0x000000, 0.22);
    shadow.fillEllipse(0, floorY, TILE_W * 1.1, TILE_HALF_H * 0.8);

    // Building sprite
    this.sprite = scene.add.sprite(0, 0, 'buildings', BUILDING_FRAME[data.type]);
    this.sprite.setOrigin(0.5, ORIGIN_Y);
    this.sprite.setDisplaySize(SPRITE_W, SPRITE_H);

    // Label floats above sprite top
    const labelY = -(ORIGIN_Y * SPRITE_H + 8);
    this.nameLabel = scene.add.text(0, labelY, data.name.toUpperCase(), {
      fontSize: '7px',
      color: '#ffe4a0',
      fontFamily: 'Courier New',
      fontStyle: 'bold',
      backgroundColor: '#00000088',
      padding: { x: 3, y: 2 },
    }).setOrigin(0.5);

    this.add([shadow, this.sprite, this.nameLabel]);
    scene.add.existing(this as unknown as Phaser.GameObjects.GameObject);

    this.setSize(TILE_W * 1.5, TILE_H * 3);
    this.setInteractive();
    this.setDepth(5 + data.col + data.row);

    this.on('pointerdown', (ptr: Phaser.Input.Pointer) => {
      if (ptr.leftButtonDown()) EventBus.emit('building-clicked', this);
    });

    this.setBuildingStatus(data.status);
  }

  setBuildingStatus(status: BuildingStatus) {
    this.buildingStatus = status;
    this.glowTween?.destroy();
    if (status === 'active') {
      this.glowTween = this.scene.tweens.add({
        targets: this.sprite,
        alpha: 0.6,
        duration: 800,
        yoyo: true,
        repeat: -1,
      });
    } else {
      this.sprite.setAlpha(1);
    }
  }
}
