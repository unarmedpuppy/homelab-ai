import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import { useDeviceStore } from '../../store';
import type { DeviceLocation } from '../../types';

interface DeviceMarkerProps {
  deviceLocation: DeviceLocation;
  roomId: string;
}

export function DeviceMarker({ deviceLocation }: DeviceMarkerProps) {
  const markerRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);
  const { getDevice, selectDevice, selectedDeviceId } = useDeviceStore();

  const device = getDevice(deviceLocation.deviceId);

  useFrame((state) => {
    if (markerRef.current && device?.state.on) {
      // Subtle floating animation for active devices
      markerRef.current.position.y =
        deviceLocation.position.z + Math.sin(state.clock.elapsedTime * 2) * 0.05 + 0.3;
    }
  });

  if (!device) {
    // Render placeholder for unmapped device
    return (
      <Sphere
        args={[0.1, 8, 8]}
        position={[
          deviceLocation.position.x,
          deviceLocation.position.z + 0.3,
          deviceLocation.position.y,
        ]}
      >
        <meshStandardMaterial color="#666" />
      </Sphere>
    );
  }

  const isSelected = selectedDeviceId === device.id;
  const isOn = device.state.on;

  const getColorByType = () => {
    switch (device.type) {
      case 'light':
        return isOn ? '#FFD700' : '#333333';
      case 'sensor':
        return '#00FF00';
      case 'thermostat':
        return '#FF6B6B';
      case 'camera':
        return '#4ECDC4';
      case 'lock':
        return device.state.door === 'locked' ? '#00FF00' : '#FF0000';
      default:
        return '#95A5A6';
    }
  };

  const handleClick = () => {
    selectDevice(isSelected ? null : device.id);
  };

  return (
    <group
      ref={markerRef}
      position={[
        deviceLocation.position.x,
        deviceLocation.position.z + 0.3,
        deviceLocation.position.y,
      ]}
      rotation={[0, deviceLocation.rotation, 0]}
      onClick={handleClick}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      {/* Indicator Sphere */}
      <Sphere args={[0.1, 16, 16]}>
        <meshStandardMaterial
          color={getColorByType()}
          emissive={isOn ? getColorByType() : '#000000'}
          emissiveIntensity={isOn ? 0.5 : 0}
        />
      </Sphere>

      {/* Selection ring */}
      {isSelected && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.15, 0]}>
          <ringGeometry args={[0.15, 0.2, 32]} />
          <meshBasicMaterial color="#00FFFF" side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Hover/Selection label */}
      {(hovered || isSelected) && (
        <Text
          position={[0, 0.3, 0]}
          fontSize={0.12}
          color="white"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.02}
          outlineColor="#000000"
        >
          {device.name}
        </Text>
      )}

      {/* Light cone for lights */}
      {device.type === 'light' && isOn && (
        <mesh position={[0, -0.5, 0]} rotation={[Math.PI, 0, 0]}>
          <coneGeometry args={[0.5, 1, 16, 1, true]} />
          <meshBasicMaterial
            color={device.state.color || '#FFFFAA'}
            transparent
            opacity={0.2}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  );
}
