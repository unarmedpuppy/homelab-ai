import Phaser from 'phaser';

export class PreloadScene extends Phaser.Scene {
  constructor() {
    super({ key: 'PreloadScene' });
  }

  create() {
    // All textures are generated programmatically — no asset loading needed
    this.createTileTextures();
    this.scene.start('MapScene');
  }

  private createTileTextures() {
    // Grass tile
    this.createIsoTileTexture('tile-grass', 0x5a8a3c, 0x4a7c2c, 0x3d6624);
    // Dirt tile
    this.createIsoTileTexture('tile-dirt', 0x8b6914, 0x7a5c10, 0x6b4e0c);
    // Water tile
    this.createIsoTileTexture('tile-water', 0x1a6b9a, 0x155d87, 0x104f74);
    // Path tile
    this.createIsoTileTexture('tile-path', 0x9a8a6a, 0x8a7a5a, 0x7a6a4a);
  }

  private createIsoTileTexture(key: string, topColor: number, _leftColor: number, _rightColor: number) {
    const tw = 64;
    const th = 32;
    const hw = tw / 2;
    const hh = th / 2;

    const canvas = this.textures.createCanvas(key, tw, th);
    if (!canvas) return;
    const ctx = canvas.getCanvas().getContext('2d');
    if (!ctx) return;

    // Top face (diamond)
    ctx.fillStyle = '#' + topColor.toString(16).padStart(6, '0');
    ctx.beginPath();
    ctx.moveTo(hw, 0);
    ctx.lineTo(tw, hh);
    ctx.lineTo(hw, th);
    ctx.lineTo(0, hh);
    ctx.closePath();
    ctx.fill();

    // Subtle grid lines
    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    ctx.lineWidth = 0.5;
    ctx.stroke();

    canvas.refresh();
  }
}
