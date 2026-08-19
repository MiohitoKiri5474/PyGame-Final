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
    COLOR_GAME_OVER,
    COLOR_ANIMAL,
    ROLE_FARMER,
    ROLE_KNIGHT,
    ROLE_MAGE,
)
import time
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
from sprites import animal_sprite, monster_sprite, nest_sprite, npc_sprite, resource_sprite, get_tool_sprite
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

    def update(self, dt: float) -> None:
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

            for p in self.particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 120.0 * dt
                p["life"] -= dt
                if "rot" in p:
                    p["rot"] = (p["rot"] + p.get("vrot", 0.0) * dt) % 360
            self.particles = [p for p in self.particles if p["life"] > 0]

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
        self.render_particles()
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

    def render_particles(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        for p in self.particles:
            alpha = max(0.0, min(1.0, p["life"] / p["max_life"]))
            sx = int(p["x"] - cam_x)
            sy = int(p["y"] - cam_y)
            sz = max(2, int(p.get("size", 3.0) * alpha))

            if "rot" in p:
                # Paper Mario origami rectangular scrap
                p_surf = pygame.Surface((sz, max(2, int(sz * 1.5))), pygame.SRCALPHA)
                col = p["color"]
                p_surf.fill((col[0], col[1], col[2], int(250 * alpha)))
                rot_surf = pygame.transform.rotate(p_surf, p["rot"])
                self.screen.blit(rot_surf, rot_surf.get_rect(center=(sx, sy)))
            else:
                pygame.draw.circle(self.screen, p["color"], (sx, sy), sz)

    def render_npcs(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        bar_w = TILE_SIZE - 4
        bar_h = 4

        for npc in self.world.npcs:
            base_sx = int(npc.x - cam_x)
            base_sy = int(npc.y - cam_y)

            # Paper Mario: 2D Soft Ground Shadow
            shadow_w = 22
            shadow_h = 7
            shadow_rect = pygame.Rect(base_sx - shadow_w // 2, base_sy + 14 - shadow_h // 2, shadow_w, shadow_h)
            shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), pygame.Rect(0, 0, shadow_w, shadow_h))
            self.screen.blit(shadow_surf, shadow_rect)

            # Paper Mario: Card Flip Horizontal Scale
            flip_p = getattr(npc, "flip_progress", 1.0)
            paper_flip_scale = max(0.08, abs(math.cos(flip_p * math.pi)))

            # Animation offsets & Paper Mario Squash/Stretch
            draw_x = npc.x
            draw_y = npc.y
            tilt_angle = 0.0
            scale_x = 1.0
            scale_y = 1.0

            if getattr(npc, "is_moving", False):
                # Paper Mario: Snappy Hop & Squash Walk
                timer = getattr(npc, "anim_timer", 0.0)
                hop_phase = math.sin(timer * 16.0)
                if hop_phase > 0:
                    # Airborne hop
                    draw_y -= hop_phase * 6.0
                    scale_y = 1.0 + 0.14 * hop_phase
                    scale_x = 1.0 - 0.08 * hop_phase
                    tilt_angle = math.sin(timer * 16.0) * 8.0
                else:
                    # Landing squash
                    squash = abs(hop_phase)
                    scale_y = 1.0 - 0.16 * squash
                    scale_x = 1.0 + 0.16 * squash
                    tilt_angle = 0.0
            elif npc.task is not None:
                # Paper Mario: Origami Fold & Hammer Slam
                timer = getattr(npc, "work_anim_timer", 0.0)
                cycle = (timer % 0.90) / 0.90
                if cycle < 0.50:
                    # Wind-up: Paper card arches back & stretches high
                    p = cycle / 0.50
                    scale_y = 1.0 + 0.25 * p
                    scale_x = 1.0 - 0.15 * p
                    tilt_angle = -26.0 * p
                    draw_y -= 3.0 * p
                    offset_dir = 1.0 if getattr(npc, "facing_left", False) else -1.0
                    draw_x += offset_dir * 3.0 * p
                elif cycle < 0.65:
                    # Slam Impact: SMASH flat into ground with extreme squash!
                    strike_prog = (cycle - 0.50) / 0.15
                    scale_y = 0.65 + 0.25 * strike_prog
                    scale_x = 1.35 - 0.15 * strike_prog
                    tilt_angle = 28.0 * (1.0 - strike_prog)
                    draw_y += 2.0
                    offset_dir = -1.0 if getattr(npc, "facing_left", False) else 1.0
                    draw_x += offset_dir * 5.0

                    # Burst colorful Paper Mario Origami Confetti / Star Scraps!
                    if strike_prog < 0.25 and random.random() < 0.65:
                        confetti_colors = [
                            (255, 220, 50),   # Star Yellow
                            (255, 75, 75),    # Mario Red
                            (60, 190, 255),   # Sky Blue
                            (85, 230, 95),    # Origami Green
                            (215, 95, 255),   # Magic Violet
                            (255, 255, 255),  # Paper White
                        ]
                        tx, ty = tile_center(*npc.task.target)
                        for _ in range(3):
                            c = random.choice(confetti_colors)
                            self.particles.append({
                                "x": tx + random.uniform(-6, 6),
                                "y": ty + random.uniform(-6, 6),
                                "vx": random.uniform(-65, 65),
                                "vy": random.uniform(-85, -30),
                                "color": c,
                                "size": random.uniform(3.0, 5.0),
                                "life": 0.40,
                                "max_life": 0.40,
                                "rot": random.uniform(0, 360),
                                "vrot": random.uniform(-360, 360),
                            })
                else:
                    # Wobble Recovery: Spring back to normal card shape
                    recoil_prog = (cycle - 0.65) / 0.35
                    wobble = math.sin(recoil_prog * math.pi * 3.0) * (1.0 - recoil_prog) * 0.18
                    scale_y = 1.0 + wobble
                    scale_x = 1.0 - wobble
                    tilt_angle = wobble * 18.0
            else:
                # Gentle paper idle flutter
                draw_y += math.sin(time.monotonic() * 2.8 + npc.id) * 1.2
                tilt_angle = math.sin(time.monotonic() * 2.0 + npc.id) * 2.0

            sx = int(draw_x - cam_x)
            sy = int(draw_y - cam_y)

            # Main Body Sprite with Paper Mario transform (Flip + Scale X/Y + Rotate)
            display_facing = getattr(npc, "display_facing_left", False)
            base_sprite = npc_sprite(npc.role)
            if display_facing:
                base_sprite = pygame.transform.flip(base_sprite, True, False)
                tilt_angle = -tilt_angle

            # Apply Paper Mario Cardboard squash/stretch & flip
            final_w = max(1, int(base_sprite.get_width() * scale_x * paper_flip_scale))
            final_h = max(1, int(base_sprite.get_height() * scale_y))
            transformed_sprite = pygame.transform.smoothscale(base_sprite, (final_w, final_h))

            if abs(tilt_angle) > 0.5:
                rendered_sprite = pygame.transform.rotate(transformed_sprite, tilt_angle)
            else:
                rendered_sprite = transformed_sprite

            sprite_rect = rendered_sprite.get_rect(center=(sx, sy))
            if npc is self.selected_npc:
                pygame.draw.rect(self.screen, COLOR_NPC_SELECTED, sprite_rect.inflate(6, 6), 2, border_radius=4)
            self.screen.blit(rendered_sprite, sprite_rect)

            # Paper Mario: Tool / Weapon Overlay
            if npc.task is not None:
                tool_type = "axe"
                if npc.task.type == "Gather":
                    target_tile = (
                        self.world.grid.get(*npc.task.target)
                        if self.world.grid.in_bounds(*npc.task.target)
                        else None
                    )
                    if target_tile and target_tile.resource in ("raw_stone", "bricks", "marble"):
                        tool_type = "pickaxe"
                    elif target_tile and target_tile.resource in ("crop", "berries"):
                        tool_type = "sickle"
                    else:
                        tool_type = "axe"
                elif "Build" in npc.task.type or npc.task.type in ("Farmland", "Destroy"):
                    tool_type = "hammer"
                elif npc.task.type in ("Hunt", "Tame"):
                    if npc.role == ROLE_KNIGHT:
                        tool_type = "sword"
                    elif npc.role == ROLE_MAGE:
                        tool_type = "staff"
                    else:
                        tool_type = "sickle"

                tool_surf = get_tool_sprite(tool_type)
                timer = getattr(npc, "work_anim_timer", 0.0)
                cycle = (timer % 0.90) / 0.90

                if cycle < 0.50:
                    tool_angle = -55.0 * (cycle / 0.50)
                    hand_dx = 9.0 * paper_flip_scale
                    hand_dy = 1.0 - 5.0 * (cycle / 0.50)
                elif cycle < 0.65:
                    strike_prog = (cycle - 0.50) / 0.15
                    tool_angle = -55.0 + 130.0 * strike_prog
                    hand_dx = (9.0 + 8.0 * strike_prog) * paper_flip_scale
                    hand_dy = -4.0 + 10.0 * strike_prog
                else:
                    recoil_prog = (cycle - 0.65) / 0.35
                    tool_angle = 75.0 * (1.0 - recoil_prog)
                    hand_dx = (9.0 + 8.0 * (1.0 - recoil_prog)) * paper_flip_scale
                    hand_dy = 6.0 * (1.0 - recoil_prog)

                if display_facing:
                    hand_dx = -hand_dx
                    tool_angle = -tool_angle
                    tool_surf = pygame.transform.flip(tool_surf, True, False)

                tw = max(1, int(tool_surf.get_width() * paper_flip_scale * (1.2 if cycle < 0.65 else 1.0)))
                th = max(1, int(tool_surf.get_height() * (1.2 if cycle < 0.65 else 1.0)))
                scaled_tool = pygame.transform.smoothscale(tool_surf, (tw, th))
                rotated_tool = pygame.transform.rotate(scaled_tool, tool_angle)
                tool_pos = (sx + int(hand_dx), sy + int(hand_dy))

                # Paper Mario: Giant Star Slam Impact Arc
                if 0.50 <= cycle < 0.65:
                    trail_surf = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
                    trail_center = (TILE_SIZE, TILE_SIZE)
                    arc_rect = pygame.Rect(trail_center[0] - 18, trail_center[1] - 18, 36, 36)
                    if not display_facing:
                        pygame.draw.arc(trail_surf, (255, 255, 255, 210), arc_rect, 0.0, 2.1, 4)
                        pygame.draw.arc(trail_surf, (255, 230, 80, 240), arc_rect, 0.3, 1.7, 3)
                    else:
                        pygame.draw.arc(trail_surf, (255, 255, 255, 210), arc_rect, 1.0, 3.14, 4)
                        pygame.draw.arc(trail_surf, (255, 230, 80, 240), arc_rect, 1.4, 2.8, 3)
                    self.screen.blit(trail_surf, (tool_pos[0] - TILE_SIZE, tool_pos[1] - TILE_SIZE))

                self.screen.blit(rotated_tool, rotated_tool.get_rect(center=tool_pos))

            # Hunger bar
            bar_x = base_sx - bar_w // 2
            bar_y = base_sy - TILE_SIZE // 2 - bar_h - 4
            hunger_ratio = max(0.0, min(1.0, npc.hunger / NPC_MAX_HUNGER))
            pygame.draw.rect(self.screen, COLOR_BAR_BG, pygame.Rect(bar_x, bar_y, bar_w, bar_h))
            fill_w = max(0, int(bar_w * hunger_ratio))
            if fill_w > 0:
                pygame.draw.rect(self.screen, COLOR_HUNGER_BAR, pygame.Rect(bar_x, bar_y, fill_w, bar_h))

    def render_animals(self) -> None:
        for animal in self.world.animals:
            tx, ty = tile_at(animal.x, animal.y)
            if not self.world.grid.get(tx, ty).revealed:
                continue
            base_sx = int(animal.x - self.camera.x)
            base_sy = int(animal.y - self.camera.y)

            # Paper Mario Ground Shadow
            shadow_surf = pygame.Surface((20, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 75), pygame.Rect(0, 0, 20, 6))
            self.screen.blit(shadow_surf, (base_sx - 10, base_sy + 12))

            draw_x = animal.x
            draw_y = animal.y
            tilt_angle = 0.0
            scale_x = 1.0
            scale_y = 1.0

            if getattr(animal, "is_moving", False):
                timer = getattr(animal, "anim_timer", 0.0)
                bounce_speed = 16.0 if animal.speed > 90 else 11.0
                hop = math.sin(timer * bounce_speed)
                if hop > 0:
                    draw_y -= hop * 5.0
                    scale_y = 1.0 + 0.12 * hop
                    scale_x = 1.0 - 0.08 * hop
                    tilt_angle = hop * 6.0
                else:
                    squash = abs(hop)
                    scale_y = 1.0 - 0.14 * squash
                    scale_x = 1.0 + 0.14 * squash

            screen_x = int(draw_x - self.camera.x)
            screen_y = int(draw_y - self.camera.y)
            sprite = animal_sprite(animal.species)
            if sprite is not None:
                if getattr(animal, "facing_left", False):
                    sprite = pygame.transform.flip(sprite, True, False)
                    tilt_angle = -tilt_angle

                tw = max(1, int(sprite.get_width() * scale_x))
                th = max(1, int(sprite.get_height() * scale_y))
                transformed = pygame.transform.smoothscale(sprite, (tw, th))
                if abs(tilt_angle) > 0.5:
                    transformed = pygame.transform.rotate(transformed, tilt_angle)
                self.screen.blit(transformed, transformed.get_rect(center=(screen_x, screen_y)))
            else:
                color = COLOR_ANIMAL_DANGEROUS if animal.dangerous else COLOR_ANIMAL
                pygame.draw.circle(self.screen, color, (screen_x, screen_y), NPC_RADIUS)

    def render_monsters(self) -> None:
        for monster in self.monsters:
            base_sx = int(monster.x - self.camera.x)
            base_sy = int(monster.y - self.camera.y)

            # Paper Mario Ground Shadow
            shadow_surf = pygame.Surface((22, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), pygame.Rect(0, 0, 22, 7))
            self.screen.blit(shadow_surf, (base_sx - 11, base_sy + 13))

            draw_x = monster.x
            draw_y = monster.y
            tilt_angle = 0.0
            scale_x = 1.0
            scale_y = 1.0

            if getattr(monster, "is_moving", False):
                timer = getattr(monster, "anim_timer", 0.0)
                hop = math.sin(timer * 13.0)
                if hop > 0:
                    draw_y -= hop * 4.5
                    scale_y = 1.0 + 0.12 * hop
                    scale_x = 1.0 - 0.08 * hop
                    tilt_angle = hop * 6.0
                else:
                    squash = abs(hop)
                    scale_y = 1.0 - 0.14 * squash
                    scale_x = 1.0 + 0.14 * squash

            screen_x = int(draw_x - self.camera.x)
            screen_y = int(draw_y - self.camera.y)
            sprite = monster_sprite(monster.type)
            if sprite is not None:
                if getattr(monster, "facing_left", False):
                    sprite = pygame.transform.flip(sprite, True, False)
                    tilt_angle = -tilt_angle

                tw = max(1, int(sprite.get_width() * scale_x))
                th = max(1, int(sprite.get_height() * scale_y))
                transformed = pygame.transform.smoothscale(sprite, (tw, th))
                if abs(tilt_angle) > 0.5:
                    transformed = pygame.transform.rotate(transformed, tilt_angle)
                self.screen.blit(transformed, transformed.get_rect(center=(screen_x, screen_y)))
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
