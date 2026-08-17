from constants import (
    TILE_SIZE,
    GRID_WIDTH,
    GRID_HEIGHT,
    VIEWPORT_TILES_X,
    VIEWPORT_TILES_Y,
    CAMERA_PAN_SPEED,
)

MAX_OFFSET_X = max(0, GRID_WIDTH * TILE_SIZE - VIEWPORT_TILES_X * TILE_SIZE)
MAX_OFFSET_Y = max(0, GRID_HEIGHT * TILE_SIZE - VIEWPORT_TILES_Y * TILE_SIZE)


class Camera:
    def __init__(self):
        self.x = MAX_OFFSET_X // 2
        self.y = MAX_OFFSET_Y // 2

    def pan(self, dx: int, dy: int, dt: float) -> None:
        self.x = int(min(max(0, self.x + dx * CAMERA_PAN_SPEED * dt), MAX_OFFSET_X))
        self.y = int(min(max(0, self.y + dy * CAMERA_PAN_SPEED * dt), MAX_OFFSET_Y))
