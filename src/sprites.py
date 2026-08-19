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
    "meat": "building/meat.png",
    "mushrooms": "building/mushroom.png",
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


def building_icon(building_type: str, height: int) -> pygame.Surface | None:
    """Sprite for a building *type* with no instance to inspect - used by the
    build bar's buttons. Farmland shows its ready look as the menu icon."""
    if building_type == "Farmland":
        return _load_scaled(_FARMLAND_READY_PATH, height)
    path = _BUILDING_PATHS.get(building_type)
    return _load_scaled(path, height) if path else None


def monster_sprite(monster_type: str | None) -> pygame.Surface | None:
    path = _MONSTER_PATHS.get(monster_type)
    return _load_scaled(path, int(TILE_SIZE * 1.3)) if path else None


def nest_sprite() -> pygame.Surface:
    return _load_scaled(_NEST_PATH, TILE_SIZE)


def animal_sprite(species: str) -> pygame.Surface | None:
    path = _ANIMAL_PATHS.get(species)
    return _load_scaled(path, int(TILE_SIZE * 1.2)) if path else None


_TOOL_CACHE: dict[str, pygame.Surface] = {}

def get_tool_sprite(tool_type: str) -> pygame.Surface:
    """Returns a crisp, themed pixel-art tool/weapon surface for action animations."""
    if tool_type in _TOOL_CACHE:
        return _TOOL_CACHE[tool_type]

    surf = pygame.Surface((28, 28), pygame.SRCALPHA)

    if tool_type == "axe":
        # Wooden handle
        pygame.draw.line(surf, (110, 70, 30), (6, 22), (18, 6), 3)
        # Steel axe head
        pygame.draw.polygon(surf, (190, 200, 215), [(14, 6), (24, 2), (22, 14), (16, 12)])
        pygame.draw.polygon(surf, (130, 140, 155), [(14, 6), (18, 5), (17, 11), (15, 10)])
    elif tool_type == "pickaxe":
        # Wooden handle
        pygame.draw.line(surf, (110, 70, 30), (6, 22), (18, 6), 3)
        # Curved double-pick head
        pygame.draw.polygon(surf, (190, 200, 215), [(10, 3), (25, 3), (23, 7), (14, 8)])
        pygame.draw.polygon(surf, (160, 170, 185), [(14, 8), (17, 16), (14, 15), (12, 9)])
    elif tool_type == "sickle":
        # Handle
        pygame.draw.line(surf, (110, 70, 30), (6, 22), (12, 14), 3)
        # Curved harvesting blade
        pygame.draw.arc(surf, (220, 200, 90), pygame.Rect(8, 2, 16, 16), 0.5, 3.8, 3)
    elif tool_type == "hammer":
        # Handle
        pygame.draw.line(surf, (110, 70, 30), (6, 22), (18, 8), 3)
        # Heavy steel hammer head
        pygame.draw.rect(surf, (150, 160, 175), pygame.Rect(14, 4, 10, 7), border_radius=2)
        pygame.draw.rect(surf, (190, 200, 215), pygame.Rect(15, 5, 8, 4))
    elif tool_type == "sword":
        # Hilt & Crossguard
        pygame.draw.line(surf, (90, 60, 30), (5, 23), (9, 19), 3)
        pygame.draw.line(surf, (210, 180, 60), (6, 16), (13, 23), 3)
        # Gleaming double-edged silver blade
        pygame.draw.polygon(surf, (230, 240, 255), [(9, 17), (25, 1), (17, 9)])
        pygame.draw.polygon(surf, (170, 190, 215), [(9, 17), (25, 1), (11, 19)])
    elif tool_type == "staff":
        # Ancient staff shaft
        pygame.draw.line(surf, (70, 45, 25), (4, 24), (20, 6), 3)
        # Glowing Arcane Crystal Orb
        pygame.draw.circle(surf, (160, 90, 240), (21, 5), 5)
        pygame.draw.circle(surf, (230, 190, 255), (21, 5), 3)
    else:
        # Default generic hand / tool
        pygame.draw.circle(surf, (220, 180, 140), (14, 14), 4)

    _TOOL_CACHE[tool_type] = surf
    return _TOOL_CACHE[tool_type]


_PROJECTILE_CACHE: dict[str, pygame.Surface] = {}


def get_arrow_sprite() -> pygame.Surface:
    """Returns a crisp Paper Mario style pixel-art flying wooden arrow."""
    if "arrow" in _PROJECTILE_CACHE:
        return _PROJECTILE_CACHE["arrow"]

    surf = pygame.Surface((26, 12), pygame.SRCALPHA)
    # Wooden shaft
    pygame.draw.line(surf, (140, 95, 45), (4, 6), (19, 6), 2)
    # Steel arrowhead
    pygame.draw.polygon(surf, (220, 230, 245), [(18, 2), (25, 6), (18, 10)])
    pygame.draw.polygon(surf, (150, 165, 185), [(18, 6), (25, 6), (18, 10)])
    # Feather fletching (Paper Mario red/white feathers)
    pygame.draw.polygon(surf, (255, 65, 65), [(2, 2), (8, 6), (4, 6)])
    pygame.draw.polygon(surf, (245, 245, 245), [(2, 10), (8, 6), (4, 6)])

    _PROJECTILE_CACHE["arrow"] = surf
    return surf


def get_magic_orb_sprite() -> pygame.Surface:
    """Returns a glowing, multi-layer arcane magic orb with star core."""
    if "magic_orb" in _PROJECTILE_CACHE:
        return _PROJECTILE_CACHE["magic_orb"]

    surf = pygame.Surface((24, 24), pygame.SRCALPHA)
    # Outer mystic aura
    pygame.draw.circle(surf, (150, 60, 230, 160), (12, 12), 10)
    # Vibrant magenta-violet ring
    pygame.draw.circle(surf, (215, 95, 255, 220), (12, 12), 7)
    # Glowing stellar cyan/white core
    pygame.draw.circle(surf, (180, 240, 255), (12, 12), 4)
    pygame.draw.circle(surf, (255, 255, 255), (12, 12), 2)

    # 4-point radiant star sparkle
    for dx, dy in [(0, -9), (0, 9), (-9, 0), (9, 0)]:
        pygame.draw.line(surf, (255, 240, 255, 220), (12, 12), (12 + dx, 12 + dy), 1)

    _PROJECTILE_CACHE["magic_orb"] = surf
    return surf


