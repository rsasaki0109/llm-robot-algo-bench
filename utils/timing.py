import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List


@dataclass
class Timer:
    """ wall-clock 計測（ms）。"""

    starts: List[float] = field(default_factory=list)
    ends: List[float] = field(default_factory=list)

    @contextmanager
    def block(self):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            t1 = time.perf_counter()
            self.starts.append(t0)
            self.ends.append(t1)

    def last_ms(self) -> float:
        if not self.starts or not self.ends:
            return 0.0
        return (self.ends[-1] - self.starts[-1]) * 1000.0

    def total_ms(self) -> float:
        if not self.starts or not self.ends:
            return 0.0
        return (self.ends[-1] - self.starts[0]) * 1000.0
