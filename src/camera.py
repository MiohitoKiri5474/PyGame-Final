from constants import (
    TILE_SIZE,
    GRID_WIDTH,
    GRID_HEIGHT,
    VIEWPORT_TILES_X,
    VIEWPORT_TILES_Y,
    CAMERA_PAN_SPEED,
    CAMERA_MARGIN_LEFT,
    CAMERA_MARGIN_RIGHT,
    CAMERA_MARGIN_TOP,
    CAMERA_MARGIN_BOTTOM,
)

# The camera's pan range over the map itself, ignoring HUD chrome - used to
# center the initial view. Pan clamping (below) extends past this on every
# side by the matching CAMERA_MARGIN_* so a fully-panned edge never lands
# under the HUD; see the CAMERA_MARGIN_* comment in constants.py.
GRID_MAX_OFFSET_X = max(0, GRID_WIDTH * TILE_SIZE - VIEWPORT_TILES_X * TILE_SIZE)
GRID_MAX_OFFSET_Y = max(0, GRID_HEIGHT * TILE_SIZE - VIEWPORT_TILES_Y * TILE_SIZE)

MIN_OFFSET_X = -CAMERA_MARGIN_LEFT
MAX_OFFSET_X = GRID_MAX_OFFSET_X + CAMERA_MARGIN_RIGHT
MIN_OFFSET_Y = -CAMERA_MARGIN_TOP
MAX_OFFSET_Y = GRID_MAX_OFFSET_Y + CAMERA_MARGIN_BOTTOM


class Camera:
    def __init__(self):
        self.x = GRID_MAX_OFFSET_X // 2
        self.y = GRID_MAX_OFFSET_Y // 2

    def pan(self, dx: int, dy: int, dt: float) -> None:
        self.x = int(min(max(MIN_OFFSET_X, self.x + dx * CAMERA_PAN_SPEED * dt), MAX_OFFSET_X))
        self.y = int(min(max(MIN_OFFSET_Y, self.y + dy * CAMERA_PAN_SPEED * dt), MAX_OFFSET_Y))
