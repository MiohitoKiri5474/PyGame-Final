"""Sprite loading/caching for game.py's render layer. Pygame-coupled like
game.py itself - not part of the pygame-free test seam.

Asset coverage is partial: only entities with an unambiguous matching asset
get a sprite (generic NPC, the "crop" resource, Wall/Tower). Monsters and
nests have no matching art yet (hunt/ is tameable animals, not hostile
monsters) and keep their color-shape rendering."""

from pathlib import Path

import pygame

from constants import TILE_SIZE

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

_NPC_PATH = "player/villager.png"  # roles (knight/magician) aren't implemented yet - one look for all NPCs
_RESOURCE_PATHS = {"crop": "plant/vegetable.png"}
_BUILDING_PATHS = {"Wall": "building/rock.png", "Tower": "building/wood.png"}

_cache: dict[tuple[str, int], pygame.Surface] = {}


def _load_scaled(rel_path: str, height: int) -> pygame.Surface:
    key = (rel_path, height)
    if key not in _cache:
        image = pygame.image.load(str(_ASSETS_DIR / rel_path)).convert_alpha()
        w, h = image.get_size()
        width = max(1, round(w * height / h))
        _cache[key] = pygame.transform.smoothscale(image, (width, height))
    return _cache[key]


def npc_sprite() -> pygame.Surface:
    return _load_scaled(_NPC_PATH, int(TILE_SIZE * 1.5))


def resource_sprite(resource: str) -> pygame.Surface | None:
    path = _RESOURCE_PATHS.get(resource)
    return _load_scaled(path, TILE_SIZE - 6) if path else None


def building_sprite(building_type: str) -> pygame.Surface | None:
    path = _BUILDING_PATHS.get(building_type)
    return _load_scaled(path, TILE_SIZE) if path else None
