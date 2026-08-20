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

# Tile-drawn resource nodes read better as the thing actually growing there
# (a tree) rather than the harvested material - collected-resource icons
# everywhere else (inventory, build costs) keep showing what you actually
# end up holding (a log), via plain resource_sprite/_RESOURCE_PATHS above.
_MAP_RESOURCE_OVERRIDES = {
    "wood": "building/tree.png",
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


def _load_image(path: Path | str) -> pygame.Surface:
    img = pygame.image.load(str(path))
    if pygame.display.get_surface() is not None:
        try:
            img = img.convert_alpha()
        except pygame.error:
            pass
    try:
        bbox = img.get_bounding_rect()
        if 0 < bbox.width < img.get_width() or 0 < bbox.height < img.get_height():
            return img.subsurface(bbox)
    except Exception:
        pass
    return img


def _load_scaled(rel_path: str, height: int) -> pygame.Surface:
    key = (rel_path, height)
    if key not in _cache:
        image = _load_image(_ASSETS_DIR / rel_path)
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


_MAP_RESOURCE_HEIGHTS = {
    "wood": int(TILE_SIZE * 1.65),
    "raw_stone": int(TILE_SIZE * 0.65),
    "bricks": int(TILE_SIZE * 0.70),
    "marble": int(TILE_SIZE * 1.10),
    "crop": int(TILE_SIZE * 0.85),
    "berries": int(TILE_SIZE * 0.65),
    "mushrooms": int(TILE_SIZE * 0.65),
    "meat": int(TILE_SIZE * 0.75),
}


def map_resource_sprite(resource: str) -> pygame.Surface | None:
    """Like resource_sprite, but specifically for the tile drawn on the map
    itself - falls back to resource_sprite's own mapping for anything with
    no map-specific override."""
    path = _MAP_RESOURCE_OVERRIDES.get(resource, _RESOURCE_PATHS.get(resource))
    height = _MAP_RESOURCE_HEIGHTS.get(resource, int(TILE_SIZE * 0.75))
    return _load_scaled(path, height) if path else None


_BUILDING_HEIGHTS = {
    "House": int(TILE_SIZE * 2.70),
    "Tower": int(TILE_SIZE * 2.45),
    "Wall": int(TILE_SIZE * 1.25),
    "AnimalPen": int(TILE_SIZE * 0.90),
}


def building_sprite(building) -> pygame.Surface | None:
    """Takes the Building instance (not just its type) since Farmland's
    look depends on its `ready` state."""
    if building.type == "Farmland":
        path = _FARMLAND_READY_PATH if building.ready else _FARMLAND_GROWING_PATH
        return _load_scaled(path, TILE_SIZE)
    path = _BUILDING_PATHS.get(building.type)
    height = _BUILDING_HEIGHTS.get(building.type, TILE_SIZE)
    return _load_scaled(path, height) if path else None


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


_ANIMAL_HEIGHTS = {
    "FlyingSquirrel": int(TILE_SIZE * 0.60),
    "Fish": int(TILE_SIZE * 0.55),
    "WildBoar": int(TILE_SIZE * 0.70),
    "Wolf": int(TILE_SIZE * 0.72),
    "Horse": int(TILE_SIZE * 0.85),
    "Bear": int(TILE_SIZE * 0.88),
}


def animal_sprite(species: str) -> pygame.Surface | None:
    path = _ANIMAL_PATHS.get(species)
    height = _ANIMAL_HEIGHTS.get(species, int(TILE_SIZE * 0.75))
    return _load_scaled(path, height) if path else None


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


_CLOUD_RAW_SLICES: list[pygame.Surface] = []


def _load_cloud_sheet() -> list[pygame.Surface]:
    global _CLOUD_RAW_SLICES
    if _CLOUD_RAW_SLICES:
        return _CLOUD_RAW_SLICES

    path = _ASSETS_DIR / "terrain" / "cloud.png"
    if not path.exists():
        c_surf = pygame.Surface((64, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(c_surf, (245, 250, 255, 240), pygame.Rect(0, 0, 64, 32))
        _CLOUD_RAW_SLICES = [c_surf]
        return _CLOUD_RAW_SLICES

    img = _load_image(path)
    w, h = img.get_size()

    # If it's a 5x3 sprite sheet (15 clouds)
    if w >= 256 and h >= 256 and w % 5 == 0 and h % 3 == 0:
        cols, rows = 5, 3
        cw, ch = w // cols, h // rows
        for idx in range(15):
            r = idx // cols
            c = idx % cols
            cell = img.subsurface(pygame.Rect(c * cw, r * ch, cw, ch))
            # Tight bounding box crop
            min_x, max_x = cw, 0
            min_y, max_y = ch, 0
            has_pixels = False
            for y in range(0, ch, 2):
                for x in range(0, cw, 2):
                    rgba = cell.get_at((x, y))
                    if rgba[3] > 8:
                        has_pixels = True
                        if x < min_x: min_x = x
                        if x > max_x: max_x = x
                        if y < min_y: min_y = y
                        if y > max_y: max_y = y
            if has_pixels and max_x >= min_x and max_y >= min_y:
                sub = cell.subsurface(pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1))
                _CLOUD_RAW_SLICES.append(sub)
            else:
                _CLOUD_RAW_SLICES.append(cell)
    else:
        _CLOUD_RAW_SLICES = [img]

    return _CLOUD_RAW_SLICES


def cloud_sprite(index: int = 0, width: int = 48, alpha: int = 255) -> pygame.Surface:
    """Returns cloud sprite #index (0..14) from the 15-cloud sheet, scaled to requested width and alpha, fully cached."""
    slices = _load_cloud_sheet()
    idx = index % len(slices)
    key = ("cloud_sprite", idx, width, alpha)
    if key not in _cache:
        raw = slices[idx]
        rw, rh = raw.get_size()
        height = max(1, round(rh * width / rw))
        scaled = pygame.transform.smoothscale(raw, (width, height))
        if alpha < 255:
            scaled = scaled.copy()
            scaled.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        _cache[key] = scaled
    return _cache[key]




def fog_sprite(size: int = TILE_SIZE) -> pygame.Surface:
    """Returns the fog PNG sprite from assets/terrain/fog.png, scaled to requested size."""
    path = _ASSETS_DIR / "terrain" / "fog.png"
    key = ("terrain/fog.png", size)
    if key not in _cache:
        if path.exists():
            img = _load_image(path)
            _cache[key] = pygame.transform.smoothscale(img, (size, size))
        else:
            f_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(f_surf, (16, 14, 24, 255), pygame.Rect(0, 0, size, size))
            _cache[key] = f_surf
    return _cache[key]


def sun_sprite(size: int = 44) -> pygame.Surface | None:
    """Returns the custom sun PNG sprite from assets/terrain/sun.png if it exists, scaled to size."""
    path = _ASSETS_DIR / "terrain" / "sun.png"
    key = ("terrain/sun.png", size)
    if key not in _cache:
        if path.exists():
            img = _load_image(path)
            w, h = img.get_size()
            dim = max(w, h)
            width = max(1, round(w * size / dim))
            height = max(1, round(h * size / dim))
            _cache[key] = pygame.transform.smoothscale(img, (width, height))
        else:
            return None
    return _cache[key]


def moon_sprite(size: int = 38) -> pygame.Surface | None:
    """Returns the custom moon PNG sprite from assets/terrain/moon.png if it exists, scaled to size."""
    path = _ASSETS_DIR / "terrain" / "moon.png"
    key = ("terrain/moon.png", size)
    if key not in _cache:
        if path.exists():
            img = _load_image(path)
            w, h = img.get_size()
            dim = max(w, h)
            width = max(1, round(w * size / dim))
            height = max(1, round(h * size / dim))
            _cache[key] = pygame.transform.smoothscale(img, (width, height))
        else:
            return None
    return _cache[key]


# --- Menu-screen backdrop/logo/button art (assets/ui) ---------------------
# Title/pause/settings/overwrite-confirm screens: primitive shapes replaced
# with painted art, per feedback. These screens size the window's whole
# logical surface (WINDOW_WIDTH x WINDOW_HEIGHT), which stays fixed even
# when the actual display is fullscreen/resized (SDL's SCALED display mode
# letterboxes that at present() time) - so callers should keep passing
# WINDOW_WIDTH/WINDOW_HEIGHT here rather than a real window size.

# The 3 ready-to-use button-bar crops inside assets/ui/button1.png (a single
# sprite sheet, not 3 separate designs - button2.png/button3.png are
# byte-identical copies of the same sheet). Measured directly from the
# asset's alpha channel: each row's tight bounding box around its painted
# content (ornate corners included), the 3 rows separated by fully
# transparent gaps.
_BUTTON_SLOT_RECTS = {
    1: pygame.Rect(133, 30, 1268, 331),   # top row - banner flourish on the left corner
    2: pygame.Rect(153, 367, 1230, 298),  # middle row - plain vine corners both sides
    3: pygame.Rect(150, 684, 1232, 298),  # bottom row - banner flourish on the right corner
}


def _cover_scale(img: pygame.Surface, width: int, height: int) -> pygame.Surface:
    """Scales `img` up just enough that it covers a width x height box
    (like CSS background-size: cover), then crops the centered overflow -
    for a full-screen backdrop where the image's own aspect ratio won't
    usually match the window's, unlike a plain letterboxed fit."""
    w, h = img.get_size()
    scale = max(width / w, height / h)
    scaled = pygame.transform.smoothscale(img, (max(1, round(w * scale)), max(1, round(h * scale))))
    sw, sh = scaled.get_size()
    crop = pygame.Rect((sw - width) // 2, (sh - height) // 2, width, height)
    return scaled.subsurface(crop).copy()


def title_background_sprite(width: int, height: int) -> pygame.Surface | None:
    """assets/ui/start_background.png, cover-scaled to fill (width, height) -
    the title screen's own backdrop."""
    path = _ASSETS_DIR / "ui" / "start_background.png"
    key = ("ui/start_background.png", width, height)
    if key not in _cache:
        if not path.exists():
            return None
        _cache[key] = _cover_scale(_load_image(path), width, height)
    return _cache[key]


def other_background_sprite(width: int, height: int) -> pygame.Surface | None:
    """assets/ui/other_background.png, cover-scaled to fill (width, height) -
    the shared backdrop for every menu-style screen that isn't the title
    screen itself (pause menu, settings, overwrite-confirm)."""
    path = _ASSETS_DIR / "ui" / "other_background.png"
    key = ("ui/other_background.png", width, height)
    if key not in _cache:
        if not path.exists():
            return None
        _cache[key] = _cover_scale(_load_image(path), width, height)
    return _cache[key]


def title_logo_sprite(max_width: int) -> pygame.Surface | None:
    """assets/ui/logo.png, scaled to max_width wide (aspect preserved)."""
    path = _ASSETS_DIR / "ui" / "logo.png"
    key = ("ui/logo.png", max_width)
    if key not in _cache:
        if not path.exists():
            return None
        img = _load_image(path)
        w, h = img.get_size()
        height = max(1, round(h * max_width / w))
        _cache[key] = pygame.transform.smoothscale(img, (max_width, height))
    return _cache[key]


def menu_button_sprite(slot: int, width: int, height: int) -> pygame.Surface | None:
    """One of the 3 button-bar crops from assets/ui/button1.png, stretched
    to (width, height) - `slot` picks which row (1/2/3, see
    _BUTTON_SLOT_RECTS); an ordered set of buttons (e.g. the title screen's
    Start/Continue/Settings) uses 1/2/3 in order, any other, unordered
    button just uses 2."""
    path = _ASSETS_DIR / "ui" / "button1.png"
    key = ("ui/button1.png", slot, width, height)
    if key not in _cache:
        if not path.exists() or slot not in _BUTTON_SLOT_RECTS:
            return None
        # Deliberately not _load_image(): its auto-trim-to-bounding-box
        # would shift the sheet's coordinate origin, throwing off
        # _BUTTON_SLOT_RECTS (measured against the raw, untrimmed PNG).
        sheet = pygame.image.load(str(path))
        if pygame.display.get_surface() is not None:
            sheet = sheet.convert_alpha()
        crop = sheet.subsurface(_BUTTON_SLOT_RECTS[slot]).copy()
        _cache[key] = pygame.transform.smoothscale(crop, (width, height))
    return _cache[key]





