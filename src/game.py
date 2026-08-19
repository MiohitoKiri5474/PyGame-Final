import math
import random

import pygame

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    TILE_SIZE,
    VIEWPORT_TILES_X,
    VIEWPORT_TILES_Y,
    NPC_RADIUS,
    NPC_MAX_HUNGER,
    NEST_INITIAL_COUNT,
    COLOR_BG,
    COLOR_FOG,
    COLOR_TEXT,
    COLOR_DAY_BANNER,
    COLOR_NIGHT_BANNER,
    COLOR_NPC_SELECTED,
    COLOR_HOVER_BORDER,
    COLOR_MONSTER,
    COLOR_HUNGER_BAR,
    COLOR_BAR_BG,
    COLOR_GAME_OVER,
    COLOR_ANIMAL,
    COLOR_ANIMAL_DANGEROUS,
)
from audio import play_sfx, set_sfx_muted
from camera import Camera
from combat import resolve_combat
from day_night import DayNightCycle, DAY, NIGHT


from coords import tile_at, tile_center
from game_over import GameOverState
from magic import cast_fire, cast_freeze, cast_lightning
from nest import NestManager, create_initial_nests
from npc import NPC
from monster import spawn_monster
from pathfinding import find_path
from settlement import evaluate_wave
from population import maybe_spawn_npc
from task import TASK_TYPES, update_npc_tasks
from extensions import hud_lines, render_overlays, run_ticks
from world import World
from priority_ui import PriorityTableUI
from skill_ui import SkillUI
from save import SAVE_PATH, load_checkpoint, save_checkpoint
from sprites import animal_sprite, monster_sprite, nest_sprite, npc_sprite, resource_sprite
from terrain import parchment, grass
from title_screen import ConfirmOverwriteDialog, TitleScreen
from pause_menu import PauseMenu
from settings_screen import SettingsScreen

# Game.state values. Bare-string constants mirror day_night.py's DAY/NIGHT
# pattern - they live here, not in title_screen.py, because self.state is
# Game's own field and PLAYING covers all non-title-screen gameplay, not
# just a title-screen concept.
TITLE = "title"
PLAYING = "playing"
CONFIRM_OVERWRITE = "confirm_overwrite"
PAUSE_MENU = "pause_menu"
SETTINGS = "settings"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Colony Defense (WIP)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        self.camera = Camera()
        self.paused = False
        self.running = True

        self.selected_npc: NPC | None = None
        self.selected_task_type: str | None = next(iter(TASK_TYPES), None)
        self.priority_ui = PriorityTableUI()
        self.skill_ui = SkillUI()

        self.state = TITLE
        self.save_exists = SAVE_PATH.exists()
        self.title_screen = TitleScreen()
        self.confirm_dialog = ConfirmOverwriteDialog()
        self.pause_menu = PauseMenu()
        self.settings_screen = SettingsScreen()
        self.fullscreen = False  # session-only, always starts windowed
        self.sfx_muted = False  # session-only, mirrors audio.py's module-level mute flag
        self._settings_return_state = TITLE  # which screen Settings' Back returns to

    def _start_new_game(self) -> None:
        self.world = World()
        self.cycle = DayNightCycle()
        initial_nests = create_initial_nests(
            self.world.grid.width, self.world.grid.height, NEST_INITIAL_COUNT, random.Random()
        )
        self.nest_manager = NestManager(self.world.grid.width, self.world.grid.height, initial_nests)
        self.monsters = []
        self.game_over_state = GameOverState()
        self.skill_points_available = 0
        self._monsters_killed_this_night = 0
        self.state = PLAYING

    def _continue_game(self) -> None:
        checkpoint = load_checkpoint()
        if checkpoint is None:
            # Save vanished or is corrupt since the title screen booted: drop
            # save_exists so the (now-broken) Continue button stops being
            # offered, rather than staying clickable and silently no-op'ing
            # forever - stay on title either way.
            self.save_exists = False
            return
        (
            self.world, self.cycle, self.nest_manager, self.monsters, self.game_over_state,
            self.skill_points_available, self._monsters_killed_this_night,
        ) = checkpoint
        if self.skill_points_available > 0:
            self.paused = True  # restore the auto-pause a full/partial clear set before save
        self.state = PLAYING

    def _set_fullscreen(self, enabled: bool) -> None:
        self.fullscreen = enabled
        if not enabled:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 0)
            return
        try:
            # SCALED lets SDL letterbox/scale our fixed logical resolution to
            # whatever the real display is, instead of changing the actual
            # display mode to match ours.
            self.screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.SCALED
            )
        except pygame.error:
            # SCALED needs a renderer backend some drivers don't provide
            # (e.g. the dummy driver used for headless testing, or some
            # minimal/software display setups) - fall back to plain
            # fullscreen rather than crash on toggle.
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state == TITLE:
                self._handle_title_event(event)
            elif self.state == CONFIRM_OVERWRITE:
                self._handle_confirm_event(event)
            elif self.state == PAUSE_MENU:
                self._handle_pause_menu_event(event)
            elif self.state == SETTINGS:
                self._handle_settings_event(event)
            elif event.type == pygame.KEYDOWN:
                # Priority UI and Skill UI intercept keys when open
                if self.priority_ui.visible:
                    self.priority_ui.handle_key(event.key, self.world.npcs)
                    continue
                if self.skill_ui.visible:
                    self.skill_points_available = self.skill_ui.handle_key(
                        event.key, self.world, self.skill_points_available
                    )
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.state = PAUSE_MENU
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_TAB:
                    self._cycle_selected_task_type()
                elif event.key == pygame.K_p:
                    self.priority_ui.toggle()
                elif event.key == pygame.K_k:
                    self.skill_ui.toggle()
                elif event.key == pygame.K_F1:
                    if not self.paused:  # casting affects sim state, stays frozen with everything else
                        cast_fire(self.world, self.monsters)
                elif event.key == pygame.K_F2:
                    if not self.paused:
                        cast_lightning(self.world, self.monsters)
                elif event.key == pygame.K_F3:
                    if not self.paused:
                        cast_freeze(self.world, self.monsters)
                elif event.key in (
                    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                    pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
                    pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4,
                    pygame.K_KP5, pygame.K_KP6, pygame.K_KP7, pygame.K_KP8, pygame.K_KP9,
                ):
                    self._select_task_by_number(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.priority_ui.visible and not self.skill_ui.visible:
                    self.handle_click(event.pos)

    def _handle_title_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.title_screen.handle_click(event.pos, self.save_exists)
            if action == "start":
                if self.save_exists:
                    self.state = CONFIRM_OVERWRITE
                else:
                    self._start_new_game()
            elif action == "continue":
                self._continue_game()
            elif action == "settings":
                self._settings_return_state = TITLE
                self.state = SETTINGS
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False

    def _handle_confirm_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.confirm_dialog.handle_click(event.pos)
            if action == "yes":
                self._start_new_game()
            elif action == "no":
                self.state = TITLE
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = TITLE

    def _handle_pause_menu_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.pause_menu.handle_click(event.pos)
            if action == "resume":
                self.state = PLAYING
            elif action == "settings":
                self._settings_return_state = PAUSE_MENU
                self.state = SETTINGS
            elif action == "quit":
                self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = PLAYING  # Esc closes the pause menu the same as clicking Resume

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.settings_screen.handle_click(event.pos)
            if action == "toggle_fullscreen":
                self._set_fullscreen(not self.fullscreen)
            elif action == "toggle_sfx_muted":
                self.sfx_muted = not self.sfx_muted
                set_sfx_muted(self.sfx_muted)
            elif action == "back":
                self.state = self._settings_return_state
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = self._settings_return_state

    def _select_task_by_number(self, key: int) -> None:
        key_map = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_map.get(key)
        if idx is not None:
            types = list(TASK_TYPES.keys())
            if idx < len(types):
                self.selected_task_type = types[idx]

    def _cycle_selected_task_type(self) -> None:
        types = list(TASK_TYPES.keys())
        if not types:
            self.selected_task_type = None
            return
        if self.selected_task_type not in types:
            self.selected_task_type = types[0]
            return
        next_index = (types.index(self.selected_task_type) + 1) % len(types)
        self.selected_task_type = types[next_index]

    def handle_click(self, screen_pos: tuple[int, int]) -> None:
        world_x = screen_pos[0] + self.camera.x
        world_y = screen_pos[1] + self.camera.y

        clicked_npc = self._npc_at_world_pos(world_x, world_y)
        if clicked_npc is not None:
            self.selected_npc = clicked_npc
            return

        gx, gy = tile_at(world_x, world_y)
        if not self.world.grid.in_bounds(gx, gy):
            return

        task_type = TASK_TYPES.get(self.selected_task_type) if self.selected_task_type else None
        if task_type is not None and task_type.can_queue(self.world, (gx, gy)):
            self.world.tasks.add(self.selected_task_type, (gx, gy))

    def _npc_at_world_pos(self, wx: float, wy: float) -> NPC | None:
        for npc in self.world.npcs:
            if math.hypot(npc.x - wx, npc.y - wy) <= NPC_RADIUS * 1.5:
                return npc
        return None

    def update(self, dt: float) -> None:
        if self.state != PLAYING:
            return

        if not self.priority_ui.visible and not self.skill_ui.visible:
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            self.camera.pan(dx, dy, dt)  # camera pans even while paused

        if not self.paused and not self.game_over_state.is_over:
            transitioned = self.cycle.update(dt)
            if transitioned and self.cycle.phase == NIGHT:
                self._monsters_killed_this_night = 0
                play_sfx("night_howl")

            update_npc_tasks(self.world, dt)
            run_ticks(self.world, dt)

            for tile in self.nest_manager.update(dt, self.cycle.round_number, self.cycle.phase):
                monster_type = self.nest_manager.pick_monster_type()
                self.monsters.append(
                    spawn_monster(tile, self.world.grid, self.world.buildings, monster_type=monster_type)
                )
            for monster in self.monsters:
                monster.update(dt)

            monster_count_before_combat = len(self.monsters)
            resolve_combat(self.world.npcs, self.monsters, self.world.buildings)
            self._monsters_killed_this_night += monster_count_before_combat - len(self.monsters)
            self.world.npcs[:] = [npc for npc in self.world.npcs if not npc.is_dead]
            if self.selected_npc is not None and self.selected_npc.is_dead:
                self.selected_npc = None

            self.game_over_state.check(self.world.npcs, self.cycle.round_number)

            if transitioned and self.cycle.phase == DAY:
                play_sfx("dawn")
                # Full clear is judged by no monster being alive at day start
                # (not by matching this night's spawn/kill counts - monsters
                # never despawn, so a leftover from an earlier night would
                # otherwise let killing it wrongly earn a false full-clear).
                self.skill_points_available += evaluate_wave(
                    len(self.monsters) == 0, self._monsters_killed_this_night
                )
                if self.skill_points_available > 0:
                    self.paused = True

            maybe_spawn_npc(self.world, self.cycle.round_number, transitioned and self.cycle.phase == DAY)

            if transitioned:
                save_checkpoint(
                    self.world, self.cycle, self.nest_manager, self.monsters, self.game_over_state,
                    self.skill_points_available, self._monsters_killed_this_night,
                )

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        if self.state == TITLE:
            self.title_screen.render(self.screen, self.font, self.save_exists)
            pygame.display.flip()
            return
        if self.state == CONFIRM_OVERWRITE:
            self.confirm_dialog.render(self.screen, self.font)
            pygame.display.flip()
            return
        if self.state == PAUSE_MENU:
            self.pause_menu.render(self.screen, self.font)
            pygame.display.flip()
            return
        if self.state == SETTINGS:
            self.settings_screen.render(self.screen, self.font, self.fullscreen, self.sfx_muted)
            pygame.display.flip()
            return
        self.render_grid()
        self.render_nests()
        self.render_animals()
        self.render_npcs()
        self.render_monsters()
        render_overlays(self.screen, self.world, self.camera)
        self.render_hud()
        self.priority_ui.render(self.screen, self.font, self.world.npcs)
        self.skill_ui.render(self.screen, self.font, self.world, self.skill_points_available)
        self.render_game_over()
        pygame.display.flip()

    def render_npcs(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        bar_w = TILE_SIZE - 4
        bar_h = 4

        for npc in self.world.npcs:
            sx = int(npc.x - cam_x)
            sy = int(npc.y - cam_y)

            # Body: each role now has its own distinct sprite (villager/
            # knight/magician), so no color ring is needed to tell them apart.
            sprite = npc_sprite(npc.role)
            sprite_rect = sprite.get_rect(center=(sx, sy))
            if npc is self.selected_npc:
                pygame.draw.rect(self.screen, COLOR_NPC_SELECTED, sprite_rect.inflate(4, 4), 2)
            self.screen.blit(sprite, sprite_rect)

            # Hunger bar (above the NPC)
            bar_x = sx - bar_w // 2
            bar_y = sprite_rect.top - bar_h - 4
            hunger_ratio = max(0.0, min(1.0, npc.hunger / NPC_MAX_HUNGER))
            # Background
            pygame.draw.rect(self.screen, COLOR_BAR_BG,
                             pygame.Rect(bar_x, bar_y, bar_w, bar_h))
            # Fill
            fill_w = max(0, int(bar_w * hunger_ratio))
            if fill_w > 0:
                pygame.draw.rect(self.screen, COLOR_HUNGER_BAR,
                                 pygame.Rect(bar_x, bar_y, fill_w, bar_h))

    def render_animals(self) -> None:
        for animal in self.world.animals:
            tx, ty = tile_at(animal.x, animal.y)
            if not self.world.grid.get(tx, ty).revealed:
                continue
            screen_x = int(animal.x - self.camera.x)
            screen_y = int(animal.y - self.camera.y)
            sprite = animal_sprite(animal.species)
            if sprite is not None:
                self.screen.blit(sprite, sprite.get_rect(center=(screen_x, screen_y)))
            else:
                color = COLOR_ANIMAL_DANGEROUS if animal.dangerous else COLOR_ANIMAL
                pygame.draw.circle(self.screen, color, (screen_x, screen_y), NPC_RADIUS)

    def render_monsters(self) -> None:
        for monster in self.monsters:
            screen_x = int(monster.x - self.camera.x)
            screen_y = int(monster.y - self.camera.y)
            sprite = monster_sprite(monster.type)
            if sprite is not None:
                self.screen.blit(sprite, sprite.get_rect(center=(screen_x, screen_y)))
            else:
                pygame.draw.circle(self.screen, COLOR_MONSTER, (screen_x, screen_y), NPC_RADIUS)

    def render_nests(self) -> None:
        for nest in self.nest_manager.nests:
            if not self.world.grid.get(nest.x, nest.y).revealed:
                continue
            screen_x = nest.x * TILE_SIZE - self.camera.x
            screen_y = nest.y * TILE_SIZE - self.camera.y
            rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
            sprite = nest_sprite()
            self.screen.blit(sprite, sprite.get_rect(center=rect.center))

    def render_grid(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        start_col = cam_x // TILE_SIZE
        start_row = cam_y // TILE_SIZE
        grid = self.world.grid

        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_gx, hover_gy = tile_at(mouse_x + cam_x, mouse_y + cam_y)

        for row in range(start_row, min(grid.height, start_row + VIEWPORT_TILES_Y + 2)):
            for col in range(start_col, min(grid.width, start_col + VIEWPORT_TILES_X + 2)):
                tile = grid.get(col, row)
                screen_x = col * TILE_SIZE - cam_x
                screen_y = row * TILE_SIZE - cam_y
                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)

                if not tile.revealed:
                    # Fog stays a flat overlay, not a texture - it's meant to
                    # read as "nothing to see here", not as ground you could walk on.
                    pygame.draw.rect(self.screen, COLOR_FOG, rect)
                elif tile.claimed:
                    self.screen.blit(grass(), rect)
                else:
                    self.screen.blit(parchment(), rect)

                # Material indicator for resource blocks
                if tile.revealed and tile.resource:
                    sprite = resource_sprite(tile.resource)
                    if sprite is not None:
                        center = (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2)
                        self.screen.blit(sprite, sprite.get_rect(center=center))
                    else:
                        marker_rect = pygame.Rect(screen_x + 8, screen_y + 8, TILE_SIZE - 16, TILE_SIZE - 16)
                        pygame.draw.rect(self.screen, (240, 210, 80), marker_rect, border_radius=6)
                        pygame.draw.rect(self.screen, (100, 80, 20), marker_rect, 1, border_radius=6)

        # Hover outline
        if grid.in_bounds(hover_gx, hover_gy):
            hover_screen_x = hover_gx * TILE_SIZE - cam_x
            hover_screen_y = hover_gy * TILE_SIZE - cam_y
            hover_rect = pygame.Rect(hover_screen_x, hover_screen_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_HOVER_BORDER, hover_rect, 2)

    def _hover_tile_info(self) -> str:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        gx, gy = tile_at(mouse_x + self.camera.x, mouse_y + self.camera.y)
        if not self.world.grid.in_bounds(gx, gy):
            return ""

        tile = self.world.grid.get(gx, gy)
        if not tile.revealed:
            return f"Tile ({gx}, {gy}): Fog of War (Unexplored)"

        if not tile.claimed:
            res_str = f" [Material: {tile.resource.capitalize()}]" if tile.resource else ""
            return f"Tile ({gx}, {gy}): Unclaimed Land{res_str}"

        building = next((b for b in self.world.buildings if b.x == gx and b.y == gy), None)
        task = next((t for t in self.world.tasks.tasks if t.target == (gx, gy)), None)
        npc = next((n for n in self.world.npcs if tile_at(n.x, n.y) == (gx, gy)), None)

        if building:
            info = f"Building: {building.type} (Block: {building.block}, Attack: {building.attack})"
        elif tile.resource:
            info = f"Material: {tile.resource.capitalize()}"
        else:
            info = "Claimed Land (Empty)"

        if task:
            info += f" [Queued Task: {task.type}]"
        if npc:
            role_str = f" [{npc.role}]" if npc.role else ""
            info += (
                f" | NPC{role_str} (HP: {int(npc.health)}/{int(npc.max_health)}, "
                f"Hunger: {int(npc.hunger)}/{int(NPC_MAX_HUNGER)})"
            )

        return f"Tile ({gx}, {gy}): {info}"

    def render_hud(self) -> None:
        banner_color = COLOR_DAY_BANNER if self.cycle.phase == DAY else COLOR_NIGHT_BANNER
        hover_info = self._hover_tile_info()

        options_list = []
        for i, t_name in enumerate(TASK_TYPES.keys(), start=1):
            marker = "*" if t_name == self.selected_task_type else ""
            options_list.append(f"[{i}] {t_name}{marker}")
        options_str = "  ".join(options_list)

        lines = [
            f"Round {self.cycle.round_number} - {self.cycle.phase.upper()}  ({self.cycle.remaining():.0f}s)",
            f"NPCs alive: {len(self.world.npcs)}",
            f"Skill points available: {self.skill_points_available} [K to spend]" if self.skill_points_available else "",
            "PAUSED" if self.paused else "",
            f"Tasks: {options_str}  [Keys 1-{len(TASK_TYPES)} / Tab, P for Priority]",
            hover_info,
            *hud_lines(self.world),
        ]
        y = 8
        for i, text in enumerate(lines):
            if not text:
                continue
            color = banner_color if i == 0 else COLOR_TEXT
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (8, y))
            y += surf.get_height() + 4

    def render_game_over(self) -> None:
        if not self.game_over_state.is_over:
            return
        lines = ["GAME OVER", f"Score: Round {self.game_over_state.score}"]
        y = WINDOW_HEIGHT // 2 - 40
        for text in lines:
            surf = self.font.render(text, True, COLOR_GAME_OVER)
            rect = surf.get_rect(center=(WINDOW_WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += surf.get_height() + 8
