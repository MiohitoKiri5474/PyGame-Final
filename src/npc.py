import math

from coords import tile_center

DEFAULT_SPEED = 120.0  # pixels/sec


class NPC:
    def __init__(self, x: float, y: float, speed: float = DEFAULT_SPEED):
        self.x = x
        self.y = y
        self.speed = speed
        self.path: list[tuple[int, int]] = []

    @property
    def has_arrived(self) -> bool:
        return not self.path

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float) -> None:
        if not self.path:
            return

        target_x, target_y = tile_center(*self.path[0])
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt

        if dist <= step:
            self.x, self.y = target_x, target_y
            self.path.pop(0)
        else:
            self.x += dx / dist * step
            self.y += dy / dist * step
