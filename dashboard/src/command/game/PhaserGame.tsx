import { useEffect, useRef } from 'react';
import Phaser from 'phaser';
import { PreloadScene } from './scenes/PreloadScene';
import { MapScene } from './scenes/MapScene';
import { EventBus } from './EventBus';

interface PhaserGameProps {
  onReady?: (scene: MapScene) => void;
}

export function PhaserGame({ onReady }: PhaserGameProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Phaser.Game | null>(null);

  useEffect(() => {
    if (!containerRef.current || gameRef.current) return;

    const container = containerRef.current;
    const w = container.clientWidth || window.innerWidth;
    const h = container.clientHeight || window.innerHeight;

    const config: Phaser.Types.Core.GameConfig = {
      type: Phaser.AUTO,
      parent: container,
      backgroundColor: '#3a6020',
      width: w,
      height: h,
      scale: {
        mode: Phaser.Scale.RESIZE,
        autoCenter: Phaser.Scale.NO_CENTER,
      },
      scene: [PreloadScene, MapScene],
      input: {
        mouse: {
          preventDefaultWheel: true,
        },
      },
      render: {
        antialias: false,
        pixelArt: true,
      },
    };

    gameRef.current = new Phaser.Game(config);

    const handleSceneReady = (scene: MapScene) => {
      onReady?.(scene);
    };

    EventBus.on('scene-ready', handleSceneReady);

    return () => {
      EventBus.off('scene-ready', handleSceneReady);
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0"
      style={{ cursor: 'default' }}
      onContextMenu={(e) => e.preventDefault()}
    />
  );
}
