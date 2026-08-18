"""Sprite loading/caching for game.py's render layer. Pygame-coupled like
game.py itself - not part of the pygame-free test seam."""

from pathlib import Path

import pygame

from constants import ROLE_FARMER, ROLE_KNIGHT, ROLE_MAGE, TILE_SIZE

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

_NPC_PATHS = {
    ROLE_FARMER: "player/villager.png",
    ROLE_KNIGHT: "player/knight.png",
    ROLE_MAGE: "player/magician.png",
}
_DEFAULT_NPC_PATH = "player/villager.png"  # role-less NPC (shouldn't normally happen post-role-split)

_RESOURCE_PATHS = {
    "crop": "building/crop.png",
    "wood": "building/wood.png",
    "bricks": "building/brick.png",
    "marble": "building/marble.png",
    "berries": "magic_material/berry.png",
    "raw_stone": "magic_material/raw_stone.png",
}

_BUILDING_PATHS = {
    "Wall": "building/wall.png",
    "Tower": "building/tower.png",
    "House": "building/house.png",
    "AnimalPen": "building/animal_pen.png",
}
_FARMLAND_GROWING_PATH = "building/farmland_growing.png"
_FARMLAND_READY_PATH = "building/farmland_ready.png"

_MONSTER_PATHS = {
    "Werewolf": "monster/werewolf.png",
    "Vampire": "monster/vampire.png",
    "Zombie": "monster/zombie.png",
}
_NEST_PATH = "monster/nest.png"

_ANIMAL_PATHS = {
    "FlyingSquirrel": "hunt/flying_squirrel.png",
    "Fish": "hunt/fish.png",
    "WildBoar": "hunt/boar.png",
    "Horse": "hunt/horse.png",
    "Wolf": "hunt/wolf.png",
    "Bear": "hunt/bear.png",
}

_cache: dict[tuple[str, int], pygame.Surface] = {}


def _load_scaled(rel_path: str, height: int) -> pygame.Surface:
    key = (rel_path, height)
    if key not in _cache:
        image = pygame.image.load(str(_ASSETS_DIR / rel_path)).convert_alpha()
        w, h = image.get_size()
        width = max(1, round(w * height / h))
        _cache[key] = pygame.transform.smoothscale(image, (width, height))
    return _cache[key]


def npc_sprite(role: str | None = None) -> pygame.Surface:
    path = _NPC_PATHS.get(role, _DEFAULT_NPC_PATH)
    return _load_scaled(path, int(TILE_SIZE * 1.5))


def resource_sprite(resource: str) -> pygame.Surface | None:
    path = _RESOURCE_PATHS.get(resource)
    return _load_scaled(path, TILE_SIZE - 6) if path else None


def building_sprite(building) -> pygame.Surface | None:
    """Takes the Building instance (not just its type) since Farmland's
    look depends on its `ready` state."""
    if building.type == "Farmland":
        path = _FARMLAND_READY_PATH if building.ready else _FARMLAND_GROWING_PATH
        return _load_scaled(path, TILE_SIZE)
    path = _BUILDING_PATHS.get(building.type)
    return _load_scaled(path, TILE_SIZE) if path else None


def monster_sprite(monster_type: str | None) -> pygame.Surface | None:
    path = _MONSTER_PATHS.get(monster_type)
    return _load_scaled(path, int(TILE_SIZE * 1.3)) if path else None


def nest_sprite() -> pygame.Surface:
    return _load_scaled(_NEST_PATH, TILE_SIZE)


def animal_sprite(species: str) -> pygame.Surface | None:
    path = _ANIMAL_PATHS.get(species)
    return _load_scaled(path, int(TILE_SIZE * 1.2)) if path else None
