from constants import TILE_SIZE


def tile_center(gx: int, gy: int) -> tuple[float, float]:
    return gx * TILE_SIZE + TILE_SIZE / 2, gy * TILE_SIZE + TILE_SIZE / 2


def tile_at(px: float, py: float) -> tuple[int, int]:
    return int(px // TILE_SIZE), int(py // TILE_SIZE)
