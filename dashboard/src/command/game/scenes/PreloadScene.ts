import Phaser from 'phaser';
import type { UnitProfile } from '../../types/game';

const SHEET_PROFILES: Exclude<UnitProfile, 'colin'>[] = ['avery', 'gilfoyle', 'ralph', 'jobin', 'villager'];

const ANIM_DEFS = [
  { suffix: 'idle',      start: 0,  end: 3,  fps: 5,  repeat: -1 },
  { suffix: 'walk',      start: 4,  end: 7,  fps: 8,  repeat: -1 },
  { suffix: 'work',      start: 8,  end: 11, fps: 6,  repeat: -1 },
  { suffix: 'celebrate', start: 12, end: 13, fps: 6,  repeat: 2  },
  { suffix: 'error',     start: 14, end: 15, fps: 8,  repeat: 3  },
] as const;

export class PreloadScene extends Phaser.Scene {
  constructor() {
    super({ key: 'PreloadScene' });
  }

  preload() {
    for (const profile of SHEET_PROFILES) {
      this.load.spritesheet(`unit-${profile}`, `assets/units/${profile}-sheet.png`, {
        frameWidth: 64, frameHeight: 96,
      });
    }
    this.load.spritesheet('buildings', 'assets/buildings/buildings-sheet.png', {
      frameWidth: 128, frameHeight: 128,
    });
    this.load.spritesheet('terrain', 'assets/tiles/terrain-tiles.png', {
      frameWidth: 64, frameHeight: 32,
    });
  }

  create() {
    // Colin has no dedicated sheet — reuses villager
    const profileToSheet: Record<UnitProfile, string> = {
      avery:    'unit-avery',
      gilfoyle: 'unit-gilfoyle',
      ralph:    'unit-ralph',
      jobin:    'unit-jobin',
      colin:    'unit-villager',
      villager: 'unit-villager',
    };

    const allProfiles: UnitProfile[] = ['avery', 'gilfoyle', 'ralph', 'jobin', 'colin', 'villager'];
    for (const profile of allProfiles) {
      const sheetKey = profileToSheet[profile];
      for (const anim of ANIM_DEFS) {
        const key = `${profile}-${anim.suffix}`;
        if (!this.anims.exists(key)) {
          this.anims.create({
            key,
            frames: this.anims.generateFrameNumbers(sheetKey, { start: anim.start, end: anim.end }),
            frameRate: anim.fps,
            repeat: anim.repeat,
          });
        }
      }
    }

    this.scene.start('MapScene');
  }
}
