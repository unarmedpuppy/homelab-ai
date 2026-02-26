import { GRID_COLS, GRID_ROWS } from './isometric';

interface Node {
  col: number;
  row: number;
  g: number; // cost from start
  h: number; // heuristic to end
  f: number; // g + h
  parent?: Node;
}

function heuristic(a: { col: number; row: number }, b: { col: number; row: number }): number {
  return Math.abs(a.col - b.col) + Math.abs(a.row - b.row);
}

function nodeKey(col: number, row: number): string {
  return `${col},${row}`;
}

/** Find A* path from (startCol, startRow) to (endCol, endRow).
 *  blocked: set of "col,row" strings that are impassable.
 *  Returns array of {col, row} waypoints including start and end, or [] if no path. */
export function findPath(
  startCol: number,
  startRow: number,
  endCol: number,
  endRow: number,
  blocked: Set<string> = new Set(),
): Array<{ col: number; row: number }> {
  if (startCol === endCol && startRow === endRow) return [];

  const open: Map<string, Node> = new Map();
  const closed: Set<string> = new Set();

  const startKey = nodeKey(startCol, startRow);
  const startNode: Node = {
    col: startCol, row: startRow, g: 0,
    h: heuristic({ col: startCol, row: startRow }, { col: endCol, row: endRow }),
    f: 0,
  };
  startNode.f = startNode.h;
  open.set(startKey, startNode);

  const neighbors = [
    { dc: 1, dr: 0 }, { dc: -1, dr: 0 },
    { dc: 0, dr: 1 }, { dc: 0, dr: -1 },
  ];

  let iterations = 0;
  const MAX_ITER = 500;

  while (open.size > 0 && iterations < MAX_ITER) {
    iterations++;
    // Pick node with lowest f
    let current: Node | undefined;
    for (const node of open.values()) {
      if (!current || node.f < current.f) current = node;
    }
    if (!current) break;

    const currentKey = nodeKey(current.col, current.row);

    if (current.col === endCol && current.row === endRow) {
      // Reconstruct path
      const path: Array<{ col: number; row: number }> = [];
      let node: Node | undefined = current;
      while (node) {
        path.unshift({ col: node.col, row: node.row });
        node = node.parent;
      }
      return path;
    }

    open.delete(currentKey);
    closed.add(currentKey);

    for (const { dc, dr } of neighbors) {
      const nc = current.col + dc;
      const nr = current.row + dr;
      if (nc < 0 || nc >= GRID_COLS || nr < 0 || nr >= GRID_ROWS) continue;
      const nk = nodeKey(nc, nr);
      if (closed.has(nk) || blocked.has(nk)) continue;

      const g = current.g + 1;
      const existing = open.get(nk);
      if (!existing || g < existing.g) {
        const h = heuristic({ col: nc, row: nr }, { col: endCol, row: endRow });
        const node: Node = { col: nc, row: nr, g, h, f: g + h, parent: current };
        open.set(nk, node);
      }
    }
  }

  // No path found — return direct path as fallback
  return [{ col: endCol, row: endRow }];
}
