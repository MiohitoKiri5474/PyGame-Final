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
    COLOR_QUEUED_WAITING,
    COLOR_QUEUED_ASSIGNED,
    COLOR_PROGRESS_BAR,
    COLOR_EXPAND_PREVIEW_CLAIM,
    EXPAND_CLAIM_RADIUS,
)
from action_menu import ActionMenu
from audio import play_bgm, play_sfx, stop_bgm
from build_bar import BuildBar
from camera import Camera
from combat import resolve_combat
from day_night import DayNightCycle, DAY, NIGHT
from coords import tile_at, tile_center
from game_over import GameOverState
from magic import cast_fire, cast_freeze, cast_lightning
from nest import NestManager, create_initial_nests
from npc import NPC
from monster import retarget_monster, spawn_monster
from pathfinding import find_path
from settlement import evaluate_wave
from population import maybe_spawn_npc
from task import TASK_TYPES, update_npc_tasks
from extensions import hud_lines, render_fx_overlays, render_overlays, run_ticks
from tile_actions import applicable_tasks
from world import World
from priority_ui import PriorityTableUI
from skill_ui import SkillUI
from npc_status_ui import NpcStatusUI
import top_bar
import top_buttons
import magic_panel
from save import SAVE_PATH, load_checkpoint, save_checkpoint
from sprites import animal_sprite, monster_sprite, nest_sprite, npc_sprite, resource_sprite
from terrain import parchment, grass

_CAST_SPELL = {"Fire": cast_fire, "Lightning": cast_lightning, "Freeze": cast_freeze}


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Colony Defense (WIP)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 40)  # top bar's countdown number

        self.camera = Camera()
        self.paused = False
        self.running = True

        self.selected_npc: NPC | None = None
        self.build_bar = BuildBar()
        self.action_menu = ActionMenu()
        self.priority_ui = PriorityTableUI()
        self.skill_ui = SkillUI()
        self.npc_status_ui = NpcStatusUI()

        checkpoint = load_checkpoint()
        if checkpoint is not None:
            (
                self.world, self.cycle, self.nest_manager, self.monsters, self.game_over_state,
                self.skill_points_available, self._monsters_killed_this_night,
            ) = checkpoint
            if self.skill_points_available > 0:
                self.paused = True  # restore the auto-pause a full/partial clear set before save
        else:
            self._new_game()

    def _new_game(self) -> None:
        """Fresh colony from scratch - used both for a no-checkpoint startup
        and for restarting after game over (R key)."""
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

    def restart(self) -> None:
        """Only meaningful after game over - starts a brand new colony and
        clears any stale checkpoint, so relaunching the app later doesn't
        reload straight back into the game-over state that's being left."""
        if not self.game_over_state.is_over:
            return
        SAVE_PATH.unlink(missing_ok=True)
        self._new_game()
        self.camera = Camera()
        self.selected_npc = None
        self.build_bar.clear()
        self.action_menu.close()
        self.paused = False

        play_bgm(self.cycle.phase)

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
                if self.npc_status_ui.visible:
                    if event.key in (pygame.K_n, pygame.K_ESCAPE):
                        self.npc_status_ui.close()
                    continue
                if event.key == pygame.K_ESCAPE:
                    if self.action_menu.visible:
                        self.action_menu.close()
                    elif self.build_bar.selected is not None:
                        self.build_bar.clear()
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.restart()  # no-op unless game_over_state.is_over
                elif event.key == pygame.K_TAB:
                    self.build_bar.cycle()
                elif event.key == pygame.K_p:
                    self.priority_ui.toggle()
                elif event.key == pygame.K_k:
                    self.skill_ui.toggle()
                elif event.key == pygame.K_n:
                    self.npc_status_ui.toggle()
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
                    self._select_build_by_number(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.priority_ui.visible and not self.skill_ui.visible and not self.npc_status_ui.visible:
                    self.handle_click(event.pos)

    def _select_build_by_number(self, key: int) -> None:
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
            self.build_bar.select_index(idx)

    def handle_click(self, screen_pos: tuple[int, int]) -> None:
        # Top-right buttons and the magic panel are always-on-top overlay
        # controls, so they get first claim on every click - same mouse
        # actions the Space/P/K/F1-F3 hotkeys already trigger.
        button = top_buttons.handle_click(screen_pos)
        if button == "pause":
            self.paused = not self.paused
            return
        if button == "priority":
            self.priority_ui.toggle()
            return
        if button == "skill":
            self.skill_ui.toggle()
            return

        spell = magic_panel.handle_click(screen_pos, top_bar.left_box_bottom())
        if spell is not None:
            if not self.paused:  # casting affects sim state, stays frozen with everything else
                _CAST_SPELL[spell](self.world, self.monsters)
            return

        # Action menu takes first crack at every click: while it's open, a
        # click either picks one of its rows or (clicking elsewhere) just
        # closes it - either way the click is consumed, not also treated as
        # a map click underneath.
        if self.action_menu.visible:
            tile = self.action_menu.tile  # handle_click() closes the menu (clears .tile) before returning
            choice = self.action_menu.handle_click(screen_pos)
            if choice is not None and tile is not None:
                self.world.tasks.add(choice, tile)
            return

        if self.build_bar.handle_click(screen_pos):
            return

        world_x = screen_pos[0] + self.camera.x
        world_y = screen_pos[1] + self.camera.y

        clicked_npc = self._npc_at_world_pos(world_x, world_y)
        if clicked_npc is not None:
            self.selected_npc = clicked_npc
            return

        gx, gy = tile_at(world_x, world_y)
        if not self.world.grid.in_bounds(gx, gy):
            return

        # A building is armed: place it here (or fall through, if this tile
        # can't take one - can_queue rejects it silently, same as before).
        if self.build_bar.selected is not None:
            task_type = TASK_TYPES.get(self.build_bar.selected)
            if task_type is not None and task_type.can_queue(self.world, (gx, gy)):
                self.world.tasks.add(self.build_bar.selected, (gx, gy))
            return

        # Otherwise infer from what's actually on the tile: queue directly
        # when exactly one task applies, ask when there's a real choice.
        options = applicable_tasks(self.world, (gx, gy))
        if len(options) == 1:
            self.world.tasks.add(options[0], (gx, gy))
        elif len(options) > 1:
            self.action_menu.open(options, (gx, gy), screen_pos)

    def _npc_at_world_pos(self, wx: float, wy: float) -> NPC | None:
        for npc in self.world.npcs:
            if math.hypot(npc.x - wx, npc.y - wy) <= NPC_RADIUS * 1.5:
                return npc
        return None

    def _update_cursor(self) -> None:
        """Hand cursor over anything a click would actually do something
        to - the keyboard-only overlays (priority/skill/NPC-status) block
        every mouse action while open, so cursor just stays default there."""
        if self.priority_ui.visible or self.skill_ui.visible or self.npc_status_ui.visible:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            return

        pos = pygame.mouse.get_pos()
        hovering = (
            top_buttons.is_hovering(pos)
            or magic_panel.is_hovering(pos, top_bar.left_box_bottom())
            or self.build_bar.is_hovering(pos)
            or (self.action_menu.visible and self.action_menu.is_hovering(pos))
            or self._npc_at_world_pos(pos[0] + self.camera.x, pos[1] + self.camera.y) is not None
        )

        if not hovering and not self.action_menu.visible:
            gx, gy = tile_at(pos[0] + self.camera.x, pos[1] + self.camera.y)
            if self.world.grid.in_bounds(gx, gy):
                if self.build_bar.selected is not None:
                    task_type = TASK_TYPES.get(self.build_bar.selected)
                    hovering = task_type is not None and task_type.can_queue(self.world, (gx, gy))
                else:
                    hovering = bool(applicable_tasks(self.world, (gx, gy)))

        cursor = pygame.SYSTEM_CURSOR_HAND if hovering else pygame.SYSTEM_CURSOR_ARROW
        try:
            pygame.mouse.set_cursor(cursor)
        except pygame.error:
            pass  # headless/dummy video drivers (smoke tests, CI) can't create system cursors

    def update(self, dt: float) -> None:
        self._update_cursor()

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
                play_bgm("night")

            update_npc_tasks(self.world, dt)
            run_ticks(self.world, dt)

            for tile in self.nest_manager.update(dt, self.cycle.round_number, self.cycle.phase):
                monster_type = self.nest_manager.pick_monster_type()
                self.monsters.append(
                    spawn_monster(tile, self.world.grid, self.world.buildings, monster_type=monster_type)
                )
            for monster in self.monsters:
                monster.update(dt)
                if monster.has_arrived:
                    # Reached wherever it was last sent (initial spawn target,
                    # or a previous retarget) - pick a new one so monsters
                    # keep actively chasing instead of freezing in place.
                    retarget_monster(monster, self.world)

            monster_count_before_combat = len(self.monsters)
            resolve_combat(self.world.npcs, self.monsters, self.world.buildings)
            self._monsters_killed_this_night += monster_count_before_combat - len(self.monsters)
            self.world.npcs[:] = [npc for npc in self.world.npcs if not npc.is_dead]
            if self.selected_npc is not None and self.selected_npc.is_dead:
                self.selected_npc = None

            self.game_over_state.check(self.world.npcs, self.cycle.round_number)
            if self.game_over_state.is_over:
                stop_bgm()

            if transitioned and self.cycle.phase == DAY:
                play_sfx("dawn")
                play_bgm("day")
                # Full clear is judged by no monster being alive at day start
                # - evaluated here, before the retreat below clears the list,
                # so it still reflects "were they actually killed" and not
                # "did they just retreat" (both would otherwise look like a
                # full clear once retreat empties self.monsters every dawn).
                self.skill_points_available += evaluate_wave(
                    len(self.monsters) == 0, self._monsters_killed_this_night
                )
                if self.skill_points_available > 0:
                    self.paused = True
                self.monsters.clear()  # survivors retreat to their nest at dawn

            maybe_spawn_npc(self.world, self.cycle.round_number, transitioned and self.cycle.phase == DAY)

            if transitioned:
                save_checkpoint(
                    self.world, self.cycle, self.nest_manager, self.monsters, self.game_over_state,
                    self.skill_points_available, self._monsters_killed_this_night,
                )

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.render_grid()
        self.render_nests()
        render_overlays(self.screen, self.world, self.camera)  # buildings: ground layer, under characters
        self.render_animals()
        self.render_npcs()
        self.render_monsters()
        render_fx_overlays(self.screen, self.world, self.camera)  # spell flashes: stay visible over their targets
        self.render_hud()
        magic_panel.render(self.screen, self.font, self.world, top_bar.left_box_bottom())
        top_buttons.render(self.screen, self.font, self.paused, self.skill_points_available)
        self.build_bar.render(self.screen, self.font, self.world)
        self.action_menu.render(self.screen, self.font)
        self.priority_ui.render(self.screen, self.font, self.world.npcs)
        self.skill_ui.render(self.screen, self.font, self.world, self.skill_points_available)
        self.npc_status_ui.render(self.screen, self.font, self.world.npcs)
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

            # Work-in-progress bar (below the NPC) - task_progress only ticks
            # once the NPC has actually arrived at its target (task.py), so
            # this only ever shows while real work is happening, not travel.
            if npc.task is not None and npc.has_arrived:
                task_type = TASK_TYPES.get(npc.task.type)
                if task_type is not None and task_type.work_seconds > 0:
                    progress_ratio = max(0.0, min(1.0, npc.task_progress / task_type.work_seconds))
                    pbar_y = sprite_rect.bottom + 4
                    pygame.draw.rect(self.screen, COLOR_BAR_BG, pygame.Rect(bar_x, pbar_y, bar_w, bar_h))
                    pfill_w = max(0, int(bar_w * progress_ratio))
                    if pfill_w > 0:
                        pygame.draw.rect(self.screen, COLOR_PROGRESS_BAR, pygame.Rect(bar_x, pbar_y, pfill_w, bar_h))

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

        # One task per target tile in practice (can_queue rejects duplicates
        # on an already-queued tile) - built once per frame instead of
        # rescanning world.tasks.tasks for every visible tile.
        queued_by_tile = {task.target: task for task in self.world.tasks.tasks}

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

                # Queued-task marker: waiting for an NPC vs. already claimed
                # by one, so a click's effect stays visible instead of just
                # vanishing into the task queue with no on-screen trace.
                task = queued_by_tile.get((col, row))
                if task is not None:
                    color = COLOR_QUEUED_ASSIGNED if task.assigned_npc is not None else COLOR_QUEUED_WAITING
                    pygame.draw.rect(self.screen, color, rect, 3)

        if grid.in_bounds(hover_gx, hover_gy):
            self._render_expand_preview(hover_gx, hover_gy)
            hover_screen_x = hover_gx * TILE_SIZE - cam_x
            hover_screen_y = hover_gy * TILE_SIZE - cam_y
            hover_rect = pygame.Rect(hover_screen_x, hover_screen_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_HOVER_BORDER, hover_rect, 2)

    def _render_expand_preview(self, gx: int, gy: int) -> None:
        """While hovering a valid Expand target, lightly tint only the tiles
        that would newly become claimed (i.e. turn to grass) if clicked -
        already-claimed ground and the reveal-only fog ring stay untouched
        so the highlight reads as "this much new territory", not noise."""
        if "Expand" not in applicable_tasks(self.world, (gx, gy)):
            return

        cam_x, cam_y = self.camera.x, self.camera.y
        grid = self.world.grid
        claim_tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        claim_tile.fill(COLOR_EXPAND_PREVIEW_CLAIM)

        for y in range(gy - EXPAND_CLAIM_RADIUS, gy + EXPAND_CLAIM_RADIUS + 1):
            for x in range(gx - EXPAND_CLAIM_RADIUS, gx + EXPAND_CLAIM_RADIUS + 1):
                if not grid.in_bounds(x, y) or grid.get(x, y).claimed:
                    continue
                self.screen.blit(claim_tile, (x * TILE_SIZE - cam_x, y * TILE_SIZE - cam_y))

    def _hover_tile_info(self) -> str:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        gx, gy = tile_at(mouse_x + self.camera.x, mouse_y + self.camera.y)
        if not self.world.grid.in_bounds(gx, gy):
            return ""

        tile = self.world.grid.get(gx, gy)
        if not tile.revealed:
            return f"Tile ({gx}, {gy}): Fog of War (Unexplored)"

        task = next((t for t in self.world.tasks.tasks if t.target == (gx, gy)), None)
        click_hint = self._click_hint((gx, gy), already_queued=task is not None)

        if not tile.claimed:
            res_str = f" [Material: {tile.resource.capitalize()}]" if tile.resource else ""
            return f"Tile ({gx}, {gy}): Unclaimed Land{res_str}{click_hint}"

        building = next((b for b in self.world.buildings if b.x == gx and b.y == gy), None)
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

        return f"Tile ({gx}, {gy}): {info}{click_hint}"

    def _click_hint(self, tile: tuple[int, int], already_queued: bool) -> str:
        """' - Click to Gather'-style suffix so hovering a workable tile
        reads as an invitation to click, not just a status readout. Silent
        when there's nothing new a click would do: already queued, a
        building's armed (that hint lives in the build panel instead), or
        the tile genuinely has no applicable task."""
        if already_queued or self.build_bar.selected is not None:
            return ""
        options = applicable_tasks(self.world, tile)
        if not options:
            return ""
        if len(options) == 1:
            return f"  ->  Click to {options[0]}"
        return f"  ->  Click to choose: {', '.join(options)}"

    def render_hud(self) -> None:
        banner_color = COLOR_DAY_BANNER if self.cycle.phase == DAY else COLOR_NIGHT_BANNER

        build_hint = (
            f"Building: {self.build_bar.selected}  [Esc to cancel]"
            if self.build_bar.selected is not None
            else "Click a tile to work it - buttons below to build"
        )
        # PAUSED/NPC count/Skill points/Priority used to be plain-text lines
        # here - now shown by the top-right buttons (pause highlights, skill
        # lights up when points are available) and the NPC box, so they're
        # not duplicated as hint text too.
        hint_lines = [
            (build_hint, COLOR_TEXT),
            *((text, COLOR_TEXT) for text in hud_lines(self.world)),
            (self._hover_tile_info(), COLOR_TEXT),
        ]
        inventory_items = sorted(self.world.inventory.items().items())

        top_bar.render(
            self.screen, self.font, self.big_font,
            self.cycle.round_number, self.cycle.phase.upper(), self.cycle.remaining(), banner_color,
            len(self.world.npcs), inventory_items, hint_lines,
        )

    def render_game_over(self) -> None:
        if not self.game_over_state.is_over:
            return
        lines = [
            ("GAME OVER", COLOR_GAME_OVER),
            (f"Score: Round {self.game_over_state.score}", COLOR_GAME_OVER),
            ("[R] Restart", COLOR_TEXT),
        ]
        y = WINDOW_HEIGHT // 2 - 40
        for text, color in lines:
            surf = self.font.render(text, True, color)
            rect = surf.get_rect(center=(WINDOW_WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += surf.get_height() + 8
