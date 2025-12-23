import { Suspense, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, Stats, Grid } from '@react-three/drei';
import { Room } from './Room';
import { useSceneStore } from '../../store';

function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="#666" wireframe />
    </mesh>
  );
}

function SceneContent() {
  const { floorPlan, activeLevel, cameraPosition } = useSceneStore();

  const rooms = useMemo(() => {
    if (!activeLevel) return [];
    return activeLevel.rooms.map((room) => ({
      ...room,
      levelElevation: activeLevel.elevation,
    }));
  }, [activeLevel]);

  return (
    <>
      <PerspectiveCamera makeDefault position={cameraPosition} fov={50} />

      <color attach="background" args={['#1a1a2e']} />

      <ambientLight intensity={0.4} />
      <directionalLight
        position={[10, 20, 10]}
        intensity={1}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />

      <Environment preset="city" />

      <Suspense fallback={<LoadingFallback />}>
        {rooms.map((room) => (
          <Room key={room.id} room={room} />
        ))}
      </Suspense>

      {/* Grid helper */}
      <Grid
        args={[50, 50]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#444444"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#666666"
        fadeDistance={50}
        position={[0, 0, 0]}
      />

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minPolarAngle={0}
        maxPolarAngle={Math.PI / 2}
        minDistance={2}
        maxDistance={50}
      />

      {import.meta.env.DEV && <Stats />}
    </>
  );
}

export function Scene() {
  return (
    <div className="w-full h-full">
      <Canvas shadows dpr={[1, 2]}>
        <SceneContent />
      </Canvas>
    </div>
  );
}
