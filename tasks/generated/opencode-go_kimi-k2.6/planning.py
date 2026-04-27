from __future__ import annotations

import heapq
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

Coord = Tuple[int, int]


def _reconstruct(came: Dict[Coord, Coord | None], goal: Coord, start: Coord) -> List[Coord]:
    p: List[Coord] = []
    c: Coord | None = goal
    for _ in range(len(came) + 5):
        if c is None:
            break
        p.append(c)
        nxt = came.get(c)
        c = nxt
    p.reverse()
    if not p or p[0] != start:
        return []
    return p


def _astar8(grid: List[List[int]], start: Coord, goal: Coord) -> List[Coord]:
    h, w = len(grid), len(grid[0])

    def octile(a: Coord, b: Coord) -> float:
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)

    if not (
        0 <= start[0] < h
        and 0 <= start[1] < w
        and 0 <= goal[0] < h
        and 0 <= goal[1] < w
    ):
        return []
    if grid[start[0]][start[1]] != 0 or grid[goal[0]][goal[1]] != 0:
        return []

    openh: List[Tuple[float, float, int, int, int]] = []
    came: Dict[Coord, Coord | None] = {start: None}
    g: Dict[Coord, float] = {start: 0.0}
    counter = 0
    heapq.heappush(openh, (octile(start, goal), 0.0, counter, start[0], start[1]))

    while openh:
        _f, gc, _c, r, c = heapq.heappop(openh)
        cur: Coord = (r, c)
        if gc != g.get(cur, -1.0):
            continue
        if cur == goal:
            return _reconstruct(came, goal, start)
        for dr, dc, cost in (
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (1, 1, math.sqrt(2)),
        ):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] != 0:
                continue
            if dr != 0 and dc != 0:
                if grid[r + dr][c] != 0 or grid[r][c + dc] != 0:
                    continue
            nxt: Coord = (nr, nc)
            ngc = gc + cost
            if ngc < g.get(nxt, float("inf")):
                g[nxt] = ngc
                came[nxt] = cur
                counter += 1
                heapq.heappush(openh, (ngc + octile(nxt, goal), ngc, counter, nr, nc))
    return []


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
    return {
        "path": [[int(a), int(b)] for a, b in path],
    }
