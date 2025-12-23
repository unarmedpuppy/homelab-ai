import { useMemo } from 'react';
import * as THREE from 'three';
import { DeviceMarker } from './DeviceMarker';
import type { Room as RoomData } from '../../types';

interface RoomProps {
  room: RoomData & { levelElevation: number };
}

export function Room({ room }: RoomProps) {
  const { geometry, center } = useMemo(() => {
    // Create floor shape from room outline
    const shape = new THREE.Shape();
    room.outline.forEach((point, index) => {
      if (index === 0) {
        shape.moveTo(point.x, point.y);
      } else {
        shape.lineTo(point.x, point.y);
      }
    });
    shape.closePath();

    // Calculate center
    let sumX = 0,
      sumY = 0;
    room.outline.forEach((p) => {
      sumX += p.x;
      sumY += p.y;
    });
    const centerX = sumX / room.outline.length;
    const centerY = sumY / room.outline.length;

    return {
      geometry: new THREE.ShapeGeometry(shape),
      center: { x: centerX, y: centerY },
    };
  }, [room.outline]);

  const wallMeshes = useMemo(() => {
    return room.walls.map((wall) => {
      const dx = wall.end.x - wall.start.x;
      const dy = wall.end.y - wall.start.y;
      const length = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx);

      const posX = (wall.start.x + wall.end.x) / 2;
      const posZ = (wall.start.y + wall.end.y) / 2;

      return {
        id: wall.id,
        position: [posX, wall.height / 2, posZ] as [number, number, number],
        rotation: [0, -angle, 0] as [number, number, number],
        size: [length, wall.height, wall.thickness] as [number, number, number],
        type: wall.type,
      };
    });
  }, [room.walls]);

  return (
    <group position={[0, room.levelElevation, 0]}>
      {/* Floor */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        receiveShadow
        position={[0, 0, 0]}
      >
        <primitive object={geometry} />
        <meshStandardMaterial
          color="#8B7355"
          roughness={0.8}
          metalness={0.1}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Walls */}
      {wallMeshes.map((wall) => (
        <mesh
          key={wall.id}
          position={wall.position}
          rotation={wall.rotation}
          castShadow
          receiveShadow
        >
          <boxGeometry args={wall.size} />
          <meshStandardMaterial
            color={wall.type === 'exterior' ? '#e8e8e8' : '#f5f5f5'}
            roughness={0.9}
          />
        </mesh>
      ))}

      {/* Doors */}
      {room.doors.map((door) => (
        <mesh
          key={door.id}
          position={[door.position.x, door.height / 2, door.position.y]}
          rotation={[0, door.rotation, 0]}
        >
          <boxGeometry args={[door.width, door.height, 0.05]} />
          <meshStandardMaterial color="#8B4513" />
        </mesh>
      ))}

      {/* Windows */}
      {room.windows.map((window) => (
        <mesh
          key={window.id}
          position={[
            window.position.x,
            window.elevation + window.height / 2,
            window.position.y,
          ]}
        >
          <boxGeometry args={[window.width, window.height, 0.05]} />
          <meshStandardMaterial color="#87CEEB" transparent opacity={0.5} />
        </mesh>
      ))}

      {/* Room label */}
      <group position={[center.x, 0.1, center.y]}>
        {/* Text would go here - using drei Text component in a real implementation */}
      </group>

      {/* Device Markers */}
      {room.devices.map((deviceLoc) => (
        <DeviceMarker
          key={deviceLoc.deviceId}
          deviceLocation={deviceLoc}
          roomId={room.id}
        />
      ))}
    </group>
  );
}
