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

    const config: Phaser.Types.Core.GameConfig = {
      type: Phaser.AUTO,
      parent: containerRef.current,
      backgroundColor: '#2a1f0a',
      width: '100%',
      height: '100%',
      scene: [PreloadScene, MapScene],
      input: {
        mouse: {
          preventDefaultWheel: true,
        },
      },
      render: {
        antialias: true,
        pixelArt: false,
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
    />
  );
}
