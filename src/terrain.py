"""Terrain background textures (parchment/grass) for render_grid. Pygame-
coupled like game.py itself - not part of the pygame-free test seam.

Every tile blits the exact same TILE_SIZE x TILE_SIZE stamp of the source
image. The source textures are seamlessly tileable, so repeating one
identical stamp edge-to-edge reads as one continuous ground rather than an
obviously repeating pattern - variant-per-tile slicing would break that
seam-matching since each slice is an unrelated crop of the source."""

from pathlib import Path

import pygame

from constants import TILE_SIZE

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "terrain"

_cache: dict[str, pygame.Surface] = {}


def _load(filename: str) -> pygame.Surface:
    if filename not in _cache:
        raw = pygame.image.load(str(_ASSETS_DIR / filename)).convert_alpha()
        _cache[filename] = pygame.transform.smoothscale(raw, (TILE_SIZE, TILE_SIZE))
    return _cache[filename]


def parchment() -> pygame.Surface:
    return _load("parchment.png")


def grass() -> pygame.Surface:
    return _load("grass.png")


def river() -> pygame.Surface:
    return _load("river.png")


def mountain() -> pygame.Surface:
    return _load("mountain.png")


def mud() -> pygame.Surface:
    if (_ASSETS_DIR / "swamp_center.png").exists():
        return _load("swamp_center.png")
    if (_ASSETS_DIR / "swamp.png").exists():
        return _load("swamp.png")
    return _load("mud.png")


def get_9slice_piece_name(top: bool, bot: bool, left: bool, right: bool) -> str:
    """Computes the 9-slice piece name ('top_left', 'top', etc.) from neighbor connections."""
    if not top and not left:
        return "top_left" if (bot or right) else "center"
    if not top and not right:
        return "top_right"
    if not bot and not left:
        return "bottom_left"
    if not bot and not right:
        return "bottom_right"
    if not top:
        return "top"
    if not bot:
        return "bottom"
    if not left:
        return "left"
    if not right:
        return "right"
    return "center"


_TERRAIN_PREFIXES = {
    "mud": "swamp",
    "river": "river",
    "mountain": "mountain",
    "scorched": "scorched",
}


def get_terrain_9slice_surface(
    terrain_type: str, top: bool, bot: bool, left: bool, right: bool
) -> pygame.Surface:
    """Returns the matching 9-slice edge-blended surface for any of the 4 terrain types."""
    piece = get_9slice_piece_name(top, bot, left, right)
    prefix = _TERRAIN_PREFIXES.get(terrain_type, terrain_type)

    # 1. Primary check (e.g. swamp_top_left.png, river_top_left.png, mountain_top_left.png, scorched_top_left.png)
    filename = f"{prefix}_{piece}.png"
    if (_ASSETS_DIR / filename).exists():
        return _load(filename)

    # 2. Secondary fallback checks
    if terrain_type == "scorched" and (_ASSETS_DIR / f"scorched_earth_{piece}.png").exists():
        return _load(f"scorched_earth_{piece}.png")
    if terrain_type == "river" and (_ASSETS_DIR / f"river_illustration_raw_{piece}.png").exists():
        return _load(f"river_illustration_raw_{piece}.png")
    if terrain_type == "mountain" and (_ASSETS_DIR / f"mountain_illustration_raw_{piece}.png").exists():
        return _load(f"mountain_illustration_raw_{piece}.png")

    return get_terrain_surface(terrain_type, is_claimed=True)


def get_swamp_piece(top: bool, bot: bool, left: bool, right: bool) -> pygame.Surface:
    """Legacy alias for get_terrain_9slice_surface('mud', ...)."""
    return get_terrain_9slice_surface("mud", top, bot, left, right)


def scorched() -> pygame.Surface:
    if (_ASSETS_DIR / "scorched_earth_center.png").exists():
        return _load("scorched_earth_center.png")
    if (_ASSETS_DIR / "scorched_earth.png").exists():
        return _load("scorched_earth.png")
    return _load("scorched.png")


def get_terrain_surface(terrain_type: str, is_claimed: bool = True) -> pygame.Surface:
    """Returns the matching terrain surface based on terrain type and claimed status."""
    if terrain_type == "river":
        return river()
    if terrain_type == "mountain":
        return mountain()
    if terrain_type == "mud":
        return mud()
    if terrain_type == "scorched":
        return scorched()
    return grass() if is_claimed else parchment()



