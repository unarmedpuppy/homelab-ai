import Phaser from 'phaser';

export class SelectionBox {
  private graphics: Phaser.GameObjects.Graphics;
  private startX = 0;
  private startY = 0;
  private active = false;

  constructor(scene: Phaser.Scene) {
    this.graphics = scene.add.graphics();
    this.graphics.setDepth(100);
  }

  start(x: number, y: number) {
    this.startX = x;
    this.startY = y;
    this.active = true;
  }

  update(currentX: number, currentY: number) {
    if (!this.active) return;
    this.graphics.clear();
    const x = Math.min(this.startX, currentX);
    const y = Math.min(this.startY, currentY);
    const w = Math.abs(currentX - this.startX);
    const h = Math.abs(currentY - this.startY);
    if (w < 4 || h < 4) return;
    this.graphics.lineStyle(1, 0xffffff, 0.8);
    this.graphics.strokeRect(x, y, w, h);
    this.graphics.fillStyle(0xffffff, 0.05);
    this.graphics.fillRect(x, y, w, h);
  }

  getBounds(): Phaser.Geom.Rectangle | null {
    if (!this.active) return null;
    return new Phaser.Geom.Rectangle(
      Math.min(this.startX, this.startX),
      Math.min(this.startY, this.startY),
      0, 0,
    );
  }

  end(): { x: number; y: number; width: number; height: number } | null {
    if (!this.active) return null;
    this.active = false;
    this.graphics.clear();
    return null;
  }

  destroy() {
    this.graphics.destroy();
  }
}
