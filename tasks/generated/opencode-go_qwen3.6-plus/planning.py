from __future__ import annotations

import heapq
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

Coord = Tuple[int, int]

_DIR8 = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
_DIAG_COST = 1.4142135623730951


def _octile(a: Coord, b: Coord) -> float:
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (2 ** 0.5 - 1) * min(dx, dy)


def _reconstruct(came: Dict[Coord, Coord], goal: Coord, start: Coord) -> List[Coord]:
    path: List[Coord] = []
    cur: Coord | None = goal
    visited: set[Coord] = set()
    while cur is not None and cur not in visited:
        visited.add(cur)
        path.append(cur)
        cur = came.get(cur)
    path.reverse()
    if not path or path[0] != start:
        return []
    return path


def _is_free(grid: List[List[int]], r: int, c: int, h: int, w: int) -> bool:
    return 0 <= r < h and 0 <= c < w and grid[r][c] == 0


def _can_move_4(grid: List[List[int]], fr: int, fc: int, tr: int, tc: int, h: int, w: int) -> bool:
    return _is_free(grid, tr, tc, h, w)


def _can_move_diag(grid: List[List[int]], fr: int, fc: int, tr: int, tc: int, h: int, w: int) -> bool:
    if not _is_free(grid, tr, tc, h, w):
        return False
    if grid[fr][tc] == 0 and grid[tr][fc] == 0:
        return True
    return False


def _astar8(grid: List[List[int]], start: Coord, goal: Coord) -> List[Coord]:
    h, w = len(grid), len(grid[0])

    if not (0 <= start[0] < h and 0 <= start[1] < w and 0 <= goal[0] < h and 0 <= goal[1] < w):
        return []
    if grid[start[0]][start[1]] != 0 or grid[goal[0]][goal[1]] != 0:
        return []
    if start == goal:
        return [start]

    openh: List[Tuple[float, int, int, int]] = []
    came: Dict[Coord, Coord] = {}
    g: Dict[Coord, float] = {start: 0.0}
    tie = 0
    heapq.heappush(openh, (_octile(start, goal), tie, start[0], start[1]))

    while openh:
        _f, _t, r, c = heapq.heappop(openh)
        cur = (r, c)
        if cur == goal:
            return _reconstruct(came, goal, start)
        cg = g.get(cur)
        if cg is None:
            continue
        for dr, dc in _DIR8:
            nr, nc = r + dr, c + dc
            if not _is_free(grid, nr, nc, h, w):
                continue
            if abs(dr) + abs(dc) == 2:
                if not _can_move_diag(grid, r, c, nr, nc, h, w):
                    continue
                cost = _DIAG_COST
            else:
                cost = 1.0
            ng = cg + cost
            nxt = (nr, nc)
            if ng < g.get(nxt, float('inf')) - 1e-9:
                g[nxt] = ng
                came[nxt] = cur
                tie += 1
                heapq.heappush(openh, (ng + _octile(nxt, goal), tie, nr, nc))
    return []


def _smooth_path(path: List[Coord], grid: List[List[int]]) -> List[Coord]:
    if len(path) <= 2:
        return path
    h, w = len(grid), len(grid[0])
    result = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            if _line_of_sight(grid, path[i], path[j], h, w):
                break
            j -= 1
        result.append(path[j])
        i = j
    return result


def _line_of_sight(grid: List[List[int]], a: Coord, b: Coord, h: int, w: int) -> bool:
    r0, c0 = a
    r1, c1 = b
    dr, dc = r1 - r0, c1 - c0
    steps = max(abs(dr), abs(dc))
    if steps == 0:
        return True
    for k in range(1, steps):
        t = k / steps
        rr = int(round(r0 + dr * t))
        cc = int(round(c0 + dc * t))
        if not (0 <= rr < h and 0 <= cc < w) or grid[rr][cc] != 0:
            return False
    return True


def run_planning(
    input_path: Path,
    model: str = "baseline",
    noise: float = 0.0,
) -> Dict[str, Any]:
    _ = model
    spec = json.loads(input_path.read_text(encoding="utf-8"))
    grid: List[List[int]] = [row[:] for row in spec["grid"]]
    if noise > 0.0:
        rng = np.random.default_rng(7)
        h, w = len(grid), len(grid[0])
        s = tuple(spec["start"])
        t = tuple(spec["goal"])
        nflip = int(min(3, max(0, round(noise * 5))))
        for _ in range(nflip):
            r, c = int(rng.integers(0, h)), int(rng.integers(0, w))
            if (r, c) != s and (r, c) != t and grid[r][c] == 0:
                grid[r][c] = 1
    start: Coord = (int(spec["start"][0]), int(spec["start"][1]))
    goal: Coord = (int(spec["goal"][0]), int(spec["goal"][1]))
    path = _astar8(grid, start, goal)
    if path:
        path = _smooth_path(path, grid)
    return {
        "path": [[int(a), int(b)] for a, b in path],
    }
