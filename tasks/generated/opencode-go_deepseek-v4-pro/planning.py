from __future__ import annotations

import heapq
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

Coord = Tuple[int, int]


def _reconstruct(came_from: List[List[Coord | None]], goal: Coord, start: Coord) -> List[Coord]:
    path: List[Coord] = []
    cur: Coord = goal
    while cur != start:
        path.append(cur)
        nxt = came_from[cur[0]][cur[1]]
        if nxt is None:
            return []
        cur = nxt
    path.append(start)
    path.reverse()
    return path


def _astar8(grid: List[List[int]], start: Coord, goal: Coord) -> List[Coord]:
    h, w = len(grid), len(grid[0])

    def heuristic(a: Coord, b: Coord) -> int:
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])
        return max(dr, dc)  # Chebyshev distance (8-dir)

    if not (0 <= start[0] < h and 0 <= start[1] < w
            and 0 <= goal[0] < h and 0 <= goal[1] < w):
        return []
    if grid[start[0]][start[1]] != 0 or grid[goal[0]][goal[1]] != 0:
        return []

    came_from: List[List[Coord | None]] = [[None] * w for _ in range(h)]
    g_score: List[List[int]] = [[1 << 30] * w for _ in range(h)]
    g_score[start[0]][start[1]] = 0

    open_set: List[Tuple[int, int, int]] = []
    heapq.heappush(open_set, (heuristic(start, goal), start[0], start[1]))

    opened: List[List[bool]] = [[False] * w for _ in range(h)]
    opened[start[0]][start[1]] = True

    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    while open_set:
        _f, r, c = heapq.heappop(open_set)
        cur: Coord = (r, c)
        gc = g_score[r][c]

        if cur == goal:
            return _reconstruct(came_from, goal, start)

        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] != 0:
                continue

            cost = 14 if dr != 0 and dc != 0 else 10
            ng = gc + cost
            if ng < g_score[nr][nc]:
                g_score[nr][nc] = ng
                came_from[nr][nc] = cur
                f = ng + heuristic((nr, nc), goal)
                heapq.heappush(open_set, (f, nr, nc))

    return []


def _smooth_path(path: List[Coord], grid: List[List[int]]) -> List[Coord]:
    if len(path) <= 2:
        return path[:]

    h, w = len(grid), len(grid[0])

    def line_of_sight(a: Coord, b: Coord) -> bool:
        r0, c0 = a
        r1, c1 = b
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        steps = max(dr, dc)
        if steps == 0:
            return True
        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0.0
            r = int(round(r0 + (r1 - r0) * t))
            c = int(round(c0 + (c1 - c0) * t))
            if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
                return False
        return True

    smoothed: List[Coord] = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i:
            if line_of_sight(path[i], path[j]):
                break
            j -= 1
        if i + 1 != j:
            i = j
        else:
            i += 1
        smoothed.append(path[i])

    return smoothed


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
    if path and noise <= 0.0:
        path = _smooth_path(path, grid)

    return {
        "path": [[int(a), int(b)] for a, b in path],
    }
