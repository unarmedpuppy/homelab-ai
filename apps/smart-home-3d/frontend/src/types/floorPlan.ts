export interface Point {
  x: number;
  y: number;
}

export interface Point3D {
  x: number;
  y: number;
  z: number;
}

export interface FloorPlan {
  id: string;
  name: string;
  scale: number; // pixels per meter
  levels: FloorLevel[];
  createdAt: Date;
  updatedAt: Date;
}

export interface FloorLevel {
  id: string;
  name: string;
  elevation: number; // height in meters
  rooms: Room[];
}

export interface Room {
  id: string;
  name: string;
  outline: Point[]; // polygon points
  area: number; // square meters
  ceilingHeight: number; // meters
  floorThickness: number;
  walls: Wall[];
  doors: Door[];
  windows: WindowDef[];
  devices: DeviceLocation[];
  textures: RoomTextures;
}

export interface Wall {
  id: string;
  start: Point;
  end: Point;
  height: number;
  thickness: number;
  type: 'interior' | 'exterior' | 'load-bearing';
}

export interface Door {
  id: string;
  position: Point;
  width: number;
  height: number;
  rotation: number;
  type: 'standard' | 'sliding' | 'folding';
}

export interface WindowDef {
  id: string;
  position: Point;
  width: number;
  height: number;
  elevation: number; // from floor
}

export interface DeviceLocation {
  deviceId: string;
  position: Point3D;
  rotation: number;
}

export interface RoomTextures {
  floor?: string; // URL to texture
  walls?: string;
  ceiling?: string;
}
