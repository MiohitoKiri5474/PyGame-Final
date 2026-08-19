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
        raw = pygame.image.load(str(_ASSETS_DIR / filename)).convert()
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
    if (_ASSETS_DIR / "swamp.png").exists():
        return _load("swamp.png")
    return _load("mud.png")


def scorched() -> pygame.Surface:
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

