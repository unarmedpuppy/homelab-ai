// Tile dimensions in world space
export const TILE_W = 64;
export const TILE_H = 32;
export const TILE_HALF_W = TILE_W / 2; // 32
export const TILE_HALF_H = TILE_H / 2; // 16

// Grid size
export const GRID_COLS = 32;
export const GRID_ROWS = 32;

// Origin offset (where tile 0,0 renders in screen space, relative to camera)
// Tile 0,0 is at top of diamond. Center of map is tile (16,16)
export const ORIGIN_X = 0; // camera handles offset
export const ORIGIN_Y = 0;

/** Convert grid (col, row) to world (x, y) — x is center of tile, y is top of tile */
export function tileToWorld(col: number, row: number): { x: number; y: number } {
  return {
    x: (col - row) * TILE_HALF_W,
    y: (col + row) * TILE_HALF_H,
  };
}

/** Convert world (x, y) to nearest grid (col, row) */
export function worldToTile(x: number, y: number): { col: number; row: number } {
  // Inverse of tileToWorld:
  // x = (col - row) * TILE_HALF_W  => col - row = x / TILE_HALF_W
  // y = (col + row) * TILE_HALF_H  => col + row = y / TILE_HALF_H
  const colMinusRow = x / TILE_HALF_W;
  const colPlusRow = y / TILE_HALF_H;
  const col = Math.round((colMinusRow + colPlusRow) / 2);
  const row = Math.round((colPlusRow - colMinusRow) / 2);
  return {
    col: Math.max(0, Math.min(GRID_COLS - 1, col)),
    row: Math.max(0, Math.min(GRID_ROWS - 1, row)),
  };
}

/** Get the 4 corner points of an isometric tile diamond (for Polygon rendering) */
export function tileDiamondPoints(col: number, row: number): number[] {
  const { x, y } = tileToWorld(col, row);
  // Diamond: top, right, bottom, left
  return [
    x, y,                          // top
    x + TILE_HALF_W, y + TILE_HALF_H, // right
    x, y + TILE_H,                  // bottom
    x - TILE_HALF_W, y + TILE_HALF_H, // left
  ];
}

export function clampCol(col: number) {
  return Math.max(0, Math.min(GRID_COLS - 1, col));
}

export function clampRow(row: number) {
  return Math.max(0, Math.min(GRID_ROWS - 1, row));
}
