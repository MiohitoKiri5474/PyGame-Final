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
    COLOR_NIGHT_OVERLAY,
    DAY_NIGHT_FADE_SECONDS,
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
    ROLE_FARMER,
    ROLE_KNIGHT,
    ROLE_MAGE,
    FARMLAND_GROW_SECONDS,
)
import time
from action_menu import ActionMenu
from audio import play_bgm, play_sfx, set_sfx_muted, stop_bgm
from build_bar import BuildBar
from camera import Camera
from combat import resolve_combat
from day_night import DayNightCycle, DAY, NIGHT
from coords import tile_at, tile_center
from game_over import GameOverState
from highscore import load_best_score, save_best_score
from magic import cast_fire, cast_freeze, cast_lightning
from nest import NestManager, create_initial_nests
from npc import NPC
from monster import retarget_monster, spawn_monster
from pathfinding import find_path
from settlement import evaluate_wave
from population import maybe_spawn_npc
from task import TASK_TYPES, task_can_perform, update_npc_tasks
from extensions import hud_lines, render_fx_overlays, render_overlays, run_ticks
from tile_actions import applicable_tasks
from world import World
from priority_ui import PriorityTableUI
from skill_ui import SkillUI
from npc_status_ui import NpcStatusUI
from sanctuary_ui import SanctuaryUI
import top_bar
import top_buttons
import magic_panel
import minimap
from save import SAVE_PATH, load_checkpoint, save_checkpoint
from sprites import (
    animal_sprite,
    get_arrow_sprite,
    get_magic_orb_sprite,
    get_tool_sprite,
    monster_sprite,
    nest_sprite,
    npc_sprite,
    resource_sprite,
)
from tame_task import idle_spot_near_pen
from terrain import get_terrain_surface, grass, parchment

from title_screen import ConfirmOverwriteDialog, TitleScreen
from pause_menu import PauseMenu
from settings_screen import SettingsScreen

_CAST_SPELL = {"Fire": cast_fire, "Lightning": cast_lightning, "Freeze": cast_freeze}

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
        self.big_font = pygame.font.Font(None, 40)  # top bar's countdown number

        self.camera = Camera()
        self.paused = False
        self.running = True

        self.selected_npc: NPC | None = None
        self.build_bar = BuildBar()
        self.action_menu = ActionMenu()
        self.animal_menu = ActionMenu()  # separate instance: "Keep Following"/"Back to Pen", not a tile task choice
        self._follow_menu_animal_id: int | None = None
        self.priority_ui = PriorityTableUI()
        self.skill_ui = SkillUI()
        self.npc_status_ui = NpcStatusUI()
        self.sanctuary_ui = SanctuaryUI()
        self.dragging_npc: NPC | None = None
        self.drag_start_pos: tuple[int, int] | None = None
        self.is_dragging: bool = False
        self.best_score = load_best_score()  # survives restart() wiping the checkpoint - separate file on purpose

        self.state = TITLE
        self.save_exists = SAVE_PATH.exists()
        self.title_screen = TitleScreen()
        self.confirm_dialog = ConfirmOverwriteDialog()
        self.pause_menu = PauseMenu()
        self.settings_screen = SettingsScreen()
        self.fullscreen = False  # session-only, always starts windowed
        self.sfx_muted = False  # session-only, mirrors audio.py's module-level mute flag
        self._settings_return_state = TITLE  # which screen Settings' Back returns to

    def _new_game(self) -> None:
        """Fresh colony from scratch - used for a no-checkpoint startup, the
        title screen's Start/overwrite-confirm Yes, and restarting after
        game over (R key)."""
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
        self.particles = []
        self.projectiles = []
        self.dragging_npc = None
        self.drag_start_pos = None
        self.is_dragging = False

    def _start_new_game(self) -> None:
        """Title screen's Start (no save) / overwrite-confirm's Yes: those
        UI elements are all still at their fresh __init__ defaults at this
        point (nothing's been touched yet), so unlike restart() this needs
        no build_bar/action_menu/paused/selected_npc cleanup."""
        self._new_game()
        self.state = PLAYING
        play_bgm(self.cycle.phase)

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
        self.particles: list[dict] = []
        self.projectiles: list[dict] = []
        self.state = PLAYING
        play_bgm(self.cycle.phase)

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
                    pts_before = self.skill_points_available
                    self.skill_points_available = self.skill_ui.handle_key(
                        event.key, self.world, self.skill_points_available
                    )
                    if self.skill_points_available < pts_before:
                        self._spawn_skill_upgrade_fx()
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
                        self.state = PAUSE_MENU
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
                if self.game_over_state.is_over:
                    if self._game_over_restart_button_rect().collidepoint(event.pos):
                        self.restart()
                elif self.skill_ui.visible:
                    pts_before = self.skill_points_available
                    self.skill_points_available = self.skill_ui.handle_click(
                        event.pos, self.world, self.skill_points_available
                    )
                    if self.skill_points_available < pts_before:
                        self._spawn_skill_upgrade_fx()
                elif not self.priority_ui.visible and not self.npc_status_ui.visible:
                    # 1. Check if clicking deploy button on Sanctuary UI
                    deployed = self.sanctuary_ui.handle_click(event.pos, self.world)
                    if deployed is not None:
                        deployed.is_resting = False
                        if getattr(deployed, "sanctuary_orig_pos", None) is not None:
                            deployed.x, deployed.y = deployed.sanctuary_orig_pos
                        else:
                            cx, cy = self.world.grid.width // 2, self.world.grid.height // 2
                            deployed.x, deployed.y = tile_center(cx, cy)
                        deployed.path = []
                        play_sfx("dawn")
                        for _ in range(12):
                            self.particles.append({
                                "type": "star",
                                "x": deployed.x + random.uniform(-8, 8),
                                "y": deployed.y + random.uniform(-8, 8),
                                "vx": random.uniform(-40, 40),
                                "vy": random.uniform(-60, -10),
                                "color": (80, 230, 110),
                                "size": 4.0,
                                "life": 0.45,
                                "max_life": 0.45,
                                "gravity": 30.0,
                            })
                    elif not self.sanctuary_ui.is_hovering(event.pos):
                        world_x = event.pos[0] + self.camera.x
                        world_y = event.pos[1] + self.camera.y
                        clicked_npc = self._npc_at_world_pos(world_x, world_y)
                        if clicked_npc is not None and not getattr(clicked_npc, "is_resting", False):
                            self.dragging_npc = clicked_npc
                            self.drag_start_pos = event.pos
                            self.is_dragging = False
                        else:
                            self.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_npc is not None and self.drag_start_pos is not None:
                    if math.hypot(event.pos[0] - self.drag_start_pos[0], event.pos[1] - self.drag_start_pos[1]) > 6:
                        self.is_dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_dragging and self.dragging_npc is not None:
                    if self.sanctuary_ui.is_hovering(event.pos):
                        resting_count = sum(1 for n in self.world.npcs if getattr(n, "is_resting", False))
                        if resting_count < 3:
                            self.dragging_npc.is_resting = True
                            self.dragging_npc.sanctuary_orig_pos = (self.dragging_npc.x, self.dragging_npc.y)
                            if self.dragging_npc.task is not None:
                                self.dragging_npc.task.assigned_npc = None
                                self.dragging_npc.task = None
                            self.dragging_npc.path = []
                            self.dragging_npc.is_moving = False
                            play_sfx("dawn")
                            for _ in range(16):
                                self.particles.append({
                                    "type": "star",
                                    "x": float(self.sanctuary_ui.PANEL_X + self.sanctuary_ui.PANEL_WIDTH // 2 + random.uniform(-30, 30)),
                                    "y": float(self.sanctuary_ui.PANEL_Y + 40 + random.uniform(-20, 20)),
                                    "vx": random.uniform(-60, 60),
                                    "vy": random.uniform(-80, 10),
                                    "color": (90, 240, 120),
                                    "size": 5.0,
                                    "life": 0.55,
                                    "max_life": 0.55,
                                    "gravity": 40.0,
                                })
                    # If released outside sanctuary, drag is simply canceled - no map teleportation!
                    self.dragging_npc = None
                    self.is_dragging = False
                    self.drag_start_pos = None
                elif self.dragging_npc is not None:
                    self.selected_npc = self.dragging_npc
                    self.dragging_npc = None
                    self.is_dragging = False
                    self.drag_start_pos = None

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

        spell = magic_panel.handle_click(screen_pos, top_bar.left_box_bottom(self._inventory_item_count()), self.font)
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

        # Same click-consuming precedence as the tile action menu above, for
        # the "Keep Following"/"Back to Pen" popup on an already-following animal.
        if self.animal_menu.visible:
            animal_id = self._follow_menu_animal_id
            choice = self.animal_menu.handle_click(screen_pos)
            self._follow_menu_animal_id = None
            if choice == "Back to Pen" and animal_id is not None:
                self._send_animal_back_to_pen(animal_id)
            return

        if self.build_bar.handle_click(screen_pos):
            return

        world_x = screen_pos[0] + self.camera.x
        world_y = screen_pos[1] + self.camera.y

        clicked_npc = self._npc_at_world_pos(world_x, world_y)
        if clicked_npc is not None:
            self.selected_npc = clicked_npc
            return

        clicked_animal = self._tamed_animal_at_world_pos(world_x, world_y)
        if clicked_animal is not None:
            if clicked_animal.is_following:
                disabled = set() if clicked_animal.pen_tile is not None else {"Back to Pen"}
                self.animal_menu.open(["Keep Following", "Back to Pen"], None, screen_pos, disabled=disabled)
                self._follow_menu_animal_id = clicked_animal.id
            else:
                clicked_animal.is_following = True
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
        # when exactly one constructive task applies, ask when there's a real choice
        # or when the action is destructive (Destroy).
        options = applicable_tasks(self.world, (gx, gy))
        if len(options) == 1:
            if options[0] == "Destroy":
                # Demolishing an existing building or growing crop is destructive:
                # Open action menu so a single stray click doesn't accidentally demolish it!
                self.action_menu.open(options, (gx, gy), screen_pos)
            else:
                self.world.tasks.add(options[0], (gx, gy))
        elif len(options) > 1:
            self.action_menu.open(options, (gx, gy), screen_pos)


    def _npc_at_world_pos(self, wx: float, wy: float) -> NPC | None:
        for npc in self.world.npcs:
            if math.hypot(npc.x - wx, npc.y - wy) <= NPC_RADIUS * 1.5:
                return npc
        return None

    def _tamed_animal_at_world_pos(self, wx: float, wy: float):
        # Only tamed animals are click-interactive this way - a wild one
        # under the cursor still falls through to the ordinary tile-click
        # Hunt/Tame task queueing further down in handle_click().
        for animal in self.world.animals:
            if animal.is_tamed and math.hypot(animal.x - wx, animal.y - wy) <= NPC_RADIUS * 1.5:
                return animal
        return None

    def _send_animal_back_to_pen(self, animal_id: int) -> None:
        animal = next((a for a in self.world.animals if a.id == animal_id), None)
        if animal is None or animal.pen_tile is None:
            return
        animal.is_following = False
        animal.idle_target = idle_spot_near_pen(self.world, *animal.pen_tile)

    def _update_cursor(self) -> None:
        """Hand cursor over anything a click would actually do something
        to - the keyboard-only overlays (priority/skill/NPC-status) block
        every mouse action while open, so cursor just stays default there."""
        if self.priority_ui.visible or self.skill_ui.visible or self.npc_status_ui.visible:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            return

        if self.game_over_state.is_over:
            hovering = self._game_over_restart_button_rect().collidepoint(pygame.mouse.get_pos())
            cursor = pygame.SYSTEM_CURSOR_HAND if hovering else pygame.SYSTEM_CURSOR_ARROW
            try:
                pygame.mouse.set_cursor(cursor)
            except pygame.error:
                pass
            return

        pos = pygame.mouse.get_pos()
        hovering = (
            top_buttons.is_hovering(pos)
            or magic_panel.is_hovering(pos, top_bar.left_box_bottom(self._inventory_item_count()), self.font)
            or self.build_bar.is_hovering(pos)
            or self.sanctuary_ui.is_hovering(pos)
            or self.is_dragging
            or (self.action_menu.visible and self.action_menu.is_hovering(pos))
            or (self.animal_menu.visible and self.animal_menu.is_hovering(pos))
            or self._npc_at_world_pos(pos[0] + self.camera.x, pos[1] + self.camera.y) is not None
            or self._tamed_animal_at_world_pos(pos[0] + self.camera.x, pos[1] + self.camera.y) is not None
        )

        if not hovering and not self.action_menu.visible and not self.animal_menu.visible:
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
        if self.state != PLAYING:
            return
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

            for p in self.particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += p.get("gravity", 120.0) * dt
                p["life"] -= dt
                if "rot" in p:
                    p["rot"] = (p["rot"] + p.get("vrot", 0.0) * dt) % 360
            self.particles = [p for p in self.particles if p["life"] > 0]

            # Update Ranged Projectiles (Mage Arcane Orb & Tower Arrow)
            for proj in self.projectiles:
                dx = proj["target_x"] - proj["x"]
                dy = proj["target_y"] - proj["y"]
                dist = math.hypot(dx, dy)
                step = proj["speed"] * dt

                # Trail sparkle particles
                if proj["type"] == "magic_orb":
                    if random.random() < 0.65:
                        self.particles.append({
                            "type": "star",
                            "x": proj["x"] + random.uniform(-3, 3),
                            "y": proj["y"] + random.uniform(-3, 3),
                            "vx": random.uniform(-20, 20),
                            "vy": random.uniform(-20, 20),
                            "color": random.choice([(210, 100, 255), (160, 240, 255), (255, 255, 255)]),
                            "size": random.uniform(2.5, 4.0),
                            "life": 0.25,
                            "max_life": 0.25,
                            "gravity": 0.0,
                        })
                elif proj["type"] == "tower_arrow":
                    if random.random() < 0.45:
                        self.particles.append({
                            "x": proj["x"],
                            "y": proj["y"],
                            "vx": -dx * 0.05,
                            "vy": -dy * 0.05,
                            "color": (230, 230, 240),
                            "size": 2.0,
                            "life": 0.15,
                            "max_life": 0.15,
                            "gravity": 0.0,
                        })

                if dist <= step or dist < 6.0:
                    proj["arrived"] = True
                    tx, ty = proj["target_x"], proj["target_y"]
                    dmg = proj["dmg"]
                    is_npc_target = proj.get("target_is_npc", False)
                    target = proj.get("target")

                    # Damage popup number
                    col = (255, 80, 80) if is_npc_target else (255, 220, 60)
                    self.particles.append({
                        "type": "damage_num",
                        "text": f"-{int(dmg)}",
                        "x": tx + random.uniform(-4, 4),
                        "y": ty - 12,
                        "vx": random.uniform(-15, 15),
                        "vy": -55.0,
                        "color": col,
                        "life": 0.65,
                        "max_life": 0.65,
                        "gravity": 40.0,
                    })

                    if proj["type"] == "magic_orb":
                        # Arcane Starburst & Magic Sparkles
                        for _ in range(6):
                            self.particles.append({
                                "type": "star",
                                "x": tx + random.uniform(-6, 6),
                                "y": ty + random.uniform(-6, 6),
                                "vx": random.uniform(-65, 65),
                                "vy": random.uniform(-65, 30),
                                "color": random.choice([(215, 95, 255), (140, 220, 255), (255, 255, 255)]),
                                "size": random.uniform(3.0, 5.5),
                                "life": 0.35,
                                "max_life": 0.35,
                                "gravity": 30.0,
                            })
                    elif proj["type"] == "tower_arrow":
                        # Wooden Splinter & Metal Star Sparks
                        for _ in range(5):
                            self.particles.append({
                                "x": tx + random.uniform(-4, 4),
                                "y": ty + random.uniform(-4, 4),
                                "vx": random.uniform(-70, 70),
                                "vy": random.uniform(-80, -20),
                                "color": random.choice([(255, 220, 60), (180, 130, 70), (255, 255, 255)]),
                                "size": random.uniform(2.5, 4.5),
                                "life": 0.30,
                                "max_life": 0.30,
                                "rot": random.uniform(0, 360),
                                "vrot": random.uniform(-360, 360),
                            })

                    if target and getattr(target, "is_dead", False) and not getattr(target, "_death_fx_spawned", False):
                        target._death_fx_spawned = True
                        if is_npc_target:
                            self._spawn_npc_death_fx(target.x, target.y, getattr(target, "role", "villager"))
                        else:
                            self._spawn_monster_death_fx(target.x, target.y)
                else:
                    proj["x"] += (dx / dist) * step
                    proj["y"] += (dy / dist) * step

            self.projectiles = [p for p in self.projectiles if not p.get("arrived", False)]

            for tile in self.nest_manager.update(dt, self.cycle.round_number, self.cycle.phase):
                monster_type = self.nest_manager.pick_monster_type()
                self.monsters.append(
                    spawn_monster(tile, self.world.grid, self.world.buildings, monster_type=monster_type)
                )
            for monster in self.monsters:
                monster.update(dt)
                if monster.has_arrived:
                    retarget_monster(monster, self.world)

            # Trigger Death VFX for any monster that died before combat resolution (e.g. spell / burn)
            for monster in self.monsters:
                if monster.is_dead and not getattr(monster, "_death_fx_spawned", False):
                    monster._death_fx_spawned = True
                    self._spawn_monster_death_fx(monster.x, monster.y)

            # Sanctuary Resting VFX (Green healing stars)
            resting_npcs = [n for n in self.world.npcs if getattr(n, "is_resting", False)]
            for idx, npc in enumerate(resting_npcs):
                if npc.health < npc.max_health and random.random() < 0.25:
                    slot_y = self.sanctuary_ui.PANEL_Y + 42 + idx * 74
                    self.particles.append({
                        "type": "star",
                        "x": float(self.sanctuary_ui.PANEL_X + 24 + random.uniform(-6, 6)),
                        "y": float(slot_y + 20 + random.uniform(-6, 6)),
                        "vx": random.uniform(-10, 10),
                        "vy": random.uniform(-35, -15),
                        "color": random.choice([(80, 240, 120), (120, 255, 160), (255, 255, 255)]),
                        "size": random.uniform(3.0, 4.5),
                        "life": 0.45,
                        "max_life": 0.45,
                        "gravity": 10.0,
                    })

            # Auto-deployed from Sanctuary on full health: Celebratory sound & particle burst
            for npc in self.world.npcs:
                if getattr(npc, "_auto_deployed", False):
                    npc._auto_deployed = False
                    play_sfx("dawn")
                    for _ in range(16):
                        self.particles.append({
                            "type": "star",
                            "x": npc.x + random.uniform(-8, 8),
                            "y": npc.y + random.uniform(-8, 8),
                            "vx": random.uniform(-40, 40),
                            "vy": random.uniform(-60, -10),
                            "color": (80, 240, 120),
                            "size": 4.5,
                            "life": 0.50,
                            "max_life": 0.50,
                            "gravity": 30.0,
                        })

            monster_count_before_combat = len(self.monsters)


            def _on_damage(src, target, dmg):
                is_npc_target = hasattr(target, "role")
                is_mage = hasattr(src, "role") and src.role == ROLE_MAGE
                is_tower = hasattr(src, "type") and src.type == "Tower"

                if is_mage:
                    # Spawn Mage Arcane Magic Orb projectile
                    self.projectiles.append({
                        "type": "magic_orb",
                        "x": float(src.x),
                        "y": float(src.y - 6),
                        "target_x": float(target.x),
                        "target_y": float(target.y),
                        "target": target,
                        "speed": 460.0,
                        "dmg": dmg,
                        "target_is_npc": is_npc_target,
                    })
                elif is_tower:
                    # Spawn Defense Tower Arrow projectile
                    bx, by = tile_center(src.x, src.y)
                    self.projectiles.append({
                        "type": "tower_arrow",
                        "x": float(bx),
                        "y": float(by - 8),
                        "target_x": float(target.x),
                        "target_y": float(target.y),
                        "target": target,
                        "speed": 560.0,
                        "dmg": dmg,
                        "target_is_npc": is_npc_target,
                    })
                else:
                    # Melee attack: Immediate damage popup & hit confetti
                    col = (255, 80, 80) if is_npc_target else (255, 220, 60)
                    self.particles.append({
                        "type": "damage_num",
                        "text": f"-{int(dmg)}",
                        "x": target.x + random.uniform(-4, 4),
                        "y": target.y - 12,
                        "vx": random.uniform(-15, 15),
                        "vy": -55.0,
                        "color": col,
                        "life": 0.65,
                        "max_life": 0.65,
                        "gravity": 40.0,
                    })
                    confetti_colors = [
                        (255, 220, 50),
                        (255, 75, 75),
                        (255, 255, 255),
                        (255, 130, 40),
                    ]
                    for _ in range(4):
                        self.particles.append({
                            "x": target.x + random.uniform(-6, 6),
                            "y": target.y + random.uniform(-6, 6),
                            "vx": random.uniform(-75, 75),
                            "vy": random.uniform(-95, -30),
                            "color": random.choice(confetti_colors),
                            "size": random.uniform(3.0, 5.0),
                            "life": 0.35,
                            "max_life": 0.35,
                            "rot": random.uniform(0, 360),
                            "vrot": random.uniform(-360, 360),
                        })

                    if target.is_dead and not getattr(target, "_death_fx_spawned", False):
                        target._death_fx_spawned = True
                        if is_npc_target:
                            self._spawn_npc_death_fx(target.x, target.y, target.role)
                        else:
                            self._spawn_monster_death_fx(target.x, target.y)

            resolve_combat(self.world.npcs, self.monsters, self.world.buildings, on_damage=_on_damage)
            self._monsters_killed_this_night += monster_count_before_combat - len(self.monsters)

            # Trigger Death VFX for any colonist that died (hunger or combat)
            for npc in self.world.npcs:
                if npc.is_dead and not getattr(npc, "_death_fx_spawned", False):
                    npc._death_fx_spawned = True
                    self._spawn_npc_death_fx(npc.x, npc.y, npc.role)


            self.world.npcs[:] = [npc for npc in self.world.npcs if not npc.is_dead]
            if self.selected_npc is not None and self.selected_npc.is_dead:
                self.selected_npc = None

            just_ended = self.game_over_state.check(self.world.npcs, self.cycle.round_number)
            if just_ended:
                stop_bgm()
                if self.game_over_state.score > self.best_score:
                    self.best_score = self.game_over_state.score
                    save_best_score(self.best_score)

            if transitioned and self.cycle.phase == DAY:
                play_sfx("dawn")
                play_bgm("day")
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

    def _spawn_monster_death_fx(self, x: float, y: float) -> None:
        """Paper Mario: Monster Defeat Confetti Fireworks & Smoke Poof!"""
        confetti_colors = [
            (255, 220, 50),   # Star Yellow
            (255, 60, 60),    # Mario Red
            (60, 190, 255),   # Sky Blue
            (85, 230, 95),    # Origami Green
            (215, 95, 255),   # Magic Violet
            (255, 140, 30),   # Origami Orange
            (255, 255, 255),  # Paper White
        ]
        # 24 colorful confetti scraps bursting outward with rotation
        for _ in range(24):
            self.particles.append({
                "x": x + random.uniform(-6, 6),
                "y": y + random.uniform(-6, 6),
                "vx": random.uniform(-110, 110),
                "vy": random.uniform(-140, -40),
                "color": random.choice(confetti_colors),
                "size": random.uniform(3.5, 6.0),
                "life": random.uniform(0.65, 0.95),
                "max_life": 0.95,
                "rot": random.uniform(0, 360),
                "vrot": random.uniform(-400, 400),
                "gravity": 160.0,
            })
        # Expanding comic POOF smoke puff rings
        for _ in range(5):
            self.particles.append({
                "type": "poof",
                "x": x + random.uniform(-8, 8),
                "y": y + random.uniform(-8, 8),
                "vx": random.uniform(-20, 20),
                "vy": random.uniform(-30, 0),
                "radius_start": 6.0,
                "radius_end": random.uniform(22.0, 34.0),
                "color": (240, 240, 245),
                "life": 0.45,
                "max_life": 0.45,
                "gravity": 0.0,
            })
        # Floating defeat gold star
        self.particles.append({
            "type": "star",
            "x": x,
            "y": y - 8,
            "vx": 0.0,
            "vy": -45.0,
            "color": (255, 225, 60),
            "size": 8.0,
            "life": 0.75,
            "max_life": 0.75,
            "gravity": 20.0,
        })

    def _spawn_npc_death_fx(self, x: float, y: float, role: str) -> None:
        """Paper Mario: Colonist Paper Soul Ascension & Angelic Halo!"""
        # Translucent ascending paper soul
        self.particles.append({
            "type": "paper_soul",
            "x": x,
            "y": y,
            "vx": 0.0,
            "vy": -24.0,
            "role": role,
            "life": 2.2,
            "max_life": 2.2,
            "gravity": 0.0,
        })
        # Delicate halo & star sparkles shower
        soul_colors = [
            (255, 255, 255),
            (255, 235, 120),
            (160, 220, 255),
        ]
        for _ in range(16):
            self.particles.append({
                "type": "star",
                "x": x + random.uniform(-10, 10),
                "y": y + random.uniform(-12, 12),
                "vx": random.uniform(-35, 35),
                "vy": random.uniform(-60, -10),
                "color": random.choice(soul_colors),
                "size": random.uniform(3.0, 5.0),
                "life": random.uniform(1.0, 1.8),
                "max_life": 1.8,
                "gravity": -10.0,
            })
        # Soft RIP Memorial Text
        self.particles.append({
            "type": "damage_num",
            "text": f"RIP {role}...",
            "x": x,
            "y": y - 24,
            "vx": 0.0,
            "vy": -18.0,
            "color": (240, 240, 255),
            "life": 2.0,
            "max_life": 2.0,
            "gravity": 0.0,
        })

    def _spawn_skill_upgrade_fx(self) -> None:
        """Paper Mario: Radiant Skill Upgrade Starburst Banner & Confetti!"""
        play_sfx("skill_point")
        center_x = self.camera.x + WINDOW_WIDTH // 2
        center_y = self.camera.y + WINDOW_HEIGHT // 2

        self.particles.append({
            "type": "skill_banner",
            "text": "★ SKILL UPGRADED! ★",
            "x": center_x,
            "y": center_y - 80,
            "vx": 0.0,
            "vy": -12.0,
            "color": (255, 230, 80),
            "life": 1.6,
            "max_life": 1.6,
            "gravity": 0.0,
        })

        star_colors = [
            (255, 230, 70),
            (255, 255, 255),
            (100, 220, 255),
            (255, 120, 180),
            (130, 255, 130),
        ]
        for _ in range(35):
            self.particles.append({
                "type": "star",
                "x": center_x + random.uniform(-40, 40),
                "y": center_y - 80 + random.uniform(-20, 20),
                "vx": random.uniform(-160, 160),
                "vy": random.uniform(-180, 20),
                "color": random.choice(star_colors),
                "size": random.uniform(4.0, 7.0),
                "life": random.uniform(0.9, 1.4),
                "max_life": 1.4,
                "gravity": 80.0,
            })

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
        render_overlays(self.screen, self.world, self.camera)  # buildings: ground layer, under characters
        self.render_animals()
        self.render_npcs()
        self.render_monsters()
        self.render_projectiles()
        self.render_particles()
        render_fx_overlays(self.screen, self.world, self.camera)  # spell flashes: stay visible over their targets
        # Crossfades in over the first few seconds of night and back out over
        # the first few seconds of day, rather than snapping instantly at
        # the phase boundary - reuses cycle.timer (seconds into the current
        # phase), which already resets to 0 exactly on each transition.
        if self.cycle.phase == NIGHT:
            fade = min(1.0, self.cycle.timer / DAY_NIGHT_FADE_SECONDS)
        else:
            fade = max(0.0, 1.0 - self.cycle.timer / DAY_NIGHT_FADE_SECONDS)
        if fade > 0.0:
            self._render_night_overlay(fade)  # map only - HUD below draws its own opaque panels on top
        self.render_hud()
        magic_panel.render(self.screen, self.font, self.world, top_bar.left_box_bottom(self._inventory_item_count()))
        top_buttons.render(self.screen, self.font, self.paused, self.skill_points_available)
        self.build_bar.render(self.screen, self.font, self.world)
        minimap.render(self.screen, self.world.grid, self.camera, self.build_bar.panel_top())
        self.action_menu.render(self.screen, self.font)
        self.animal_menu.render(self.screen, self.font)
        self.priority_ui.render(self.screen, self.font, self.world.npcs)
        self.skill_ui.render(self.screen, self.font, self.world, self.skill_points_available)
        self.npc_status_ui.render(self.screen, self.font, self.world.npcs)

        # Right-side Healing Sanctuary Box
        is_over_sanctuary = self.is_dragging and self.sanctuary_ui.is_hovering(pygame.mouse.get_pos())
        self.sanctuary_ui.render(self.screen, self.font, self.world, is_dragging_over=is_over_sanctuary)

        # Floating Dragged Paper NPC under cursor with Paper Mario Wiggling & Dangling Animation
        if self.is_dragging and self.dragging_npc is not None:
            mpos = pygame.mouse.get_pos()
            sprite = npc_sprite(self.dragging_npc.role)
            if sprite is not None:
                t = time.monotonic()
                wiggle_rot = math.sin(t * 18.0) * 16.0 + math.cos(t * 9.0) * 5.0
                stretch_y = 1.14 + math.sin(t * 22.0) * 0.08
                squash_x = 0.88 - math.sin(t * 22.0) * 0.06
                dangle_y = 12.0 + math.sin(t * 14.0) * 3.0

                # Soft ground shadow following below
                shadow_w = int(26 + math.sin(t * 14.0) * 5.0)
                shadow_surf = pygame.Surface((shadow_w, 9), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), pygame.Rect(0, 0, shadow_w, 9))
                self.screen.blit(shadow_surf, (mpos[0] - shadow_w // 2, mpos[1] + 32))

                # Scaled and rotated dangling body
                tw = max(1, int(sprite.get_width() * squash_x))
                th = max(1, int(sprite.get_height() * stretch_y))
                scaled = pygame.transform.smoothscale(sprite, (tw, th))
                rotated = pygame.transform.rotate(scaled, wiggle_rot)
                self.screen.blit(rotated, rotated.get_rect(center=(mpos[0], int(mpos[1] + dangle_y))))

                # Panic Sweat Drop (💧) popping beside the struggling head
                sweat_x = mpos[0] + (18 if math.sin(t * 7.0) > 0 else -18)
                sweat_y = mpos[1] - 10 + math.sin(t * 12.0) * 4.0
                sweat_surf = pygame.Surface((10, 13), pygame.SRCALPHA)
                pygame.draw.polygon(sweat_surf, (110, 225, 255, 230), [(5, 1), (1, 9), (5, 12), (9, 9)])
                pygame.draw.circle(sweat_surf, (255, 255, 255, 240), (4, 5), 1)
                self.screen.blit(sweat_surf, (int(sweat_x) - 5, int(sweat_y)))


        self.render_game_over()
        pygame.display.flip()


    def render_projectiles(self) -> None:
        """Draws Paper Mario flying arcane magic orbs and feathered wooden arrows."""
        cam_x, cam_y = self.camera.x, self.camera.y
        for proj in self.projectiles:
            sx = int(proj["x"] - cam_x)
            sy = int(proj["y"] - cam_y)
            dx = proj["target_x"] - proj["x"]
            dy = proj["target_y"] - proj["y"]
            angle_deg = -math.degrees(math.atan2(dy, dx))

            if proj["type"] == "magic_orb":
                base_sprite = get_magic_orb_sprite()
                pulse = 1.0 + 0.15 * math.sin(time.monotonic() * 18.0)
                tw = max(1, int(base_sprite.get_width() * pulse))
                th = max(1, int(base_sprite.get_height() * pulse))
                scaled = pygame.transform.smoothscale(base_sprite, (tw, th))
                rot_sprite = pygame.transform.rotate(scaled, angle_deg)
                self.screen.blit(rot_sprite, rot_sprite.get_rect(center=(sx, sy)))
            elif proj["type"] == "tower_arrow":
                base_sprite = get_arrow_sprite()
                rot_sprite = pygame.transform.rotate(base_sprite, angle_deg)
                self.screen.blit(rot_sprite, rot_sprite.get_rect(center=(sx, sy)))

    def render_particles(self) -> None:

        cam_x, cam_y = self.camera.x, self.camera.y
        for p in self.particles:
            alpha = max(0.0, min(1.0, p["life"] / p["max_life"]))
            sx = int(p["x"] - cam_x)
            sy = int(p["y"] - cam_y)

            p_type = p.get("type")
            if p_type == "damage_num":
                txt = p["text"]
                col = p["color"]
                txt_surf = self.font.render(txt, True, col)
                outline_surf = self.font.render(txt, True, (15, 15, 20))
                for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
                    self.screen.blit(outline_surf, (sx + ox, sy + oy))
                self.screen.blit(txt_surf, (sx, sy))
            elif p_type == "poof":
                prog = 1.0 - alpha
                r = int(p.get("radius_start", 6.0) + (p.get("radius_end", 28.0) - p.get("radius_start", 6.0)) * prog)
                poof_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
                poof_col = (245, 245, 250, int(200 * alpha))
                pygame.draw.circle(poof_surf, poof_col, (r + 3, r + 3), r, 3)
                self.screen.blit(poof_surf, (sx - r - 3, sy - r - 3))
            elif p_type == "star":
                sz = max(2, int(p.get("size", 4.0) * (0.5 + 0.5 * alpha)))
                col = p["color"]
                star_surf = pygame.Surface((sz * 2 + 4, sz * 2 + 4), pygame.SRCALPHA)
                star_col = (col[0], col[1], col[2], int(255 * alpha))
                cx_s, cy_s = sz + 2, sz + 2
                points = [
                    (cx_s, cy_s - sz),
                    (cx_s + sz // 3, cy_s - sz // 3),
                    (cx_s + sz, cy_s),
                    (cx_s + sz // 3, cy_s + sz // 3),
                    (cx_s, cy_s + sz),
                    (cx_s - sz // 3, cy_s + sz // 3),
                    (cx_s - sz, cy_s),
                    (cx_s - sz // 3, cy_s - sz // 3),
                ]
                pygame.draw.polygon(star_surf, star_col, points)
                self.screen.blit(star_surf, (sx - sz - 2, sy - sz - 2))
            elif p_type == "paper_soul":
                role = p.get("role", "villager")
                base_sprite = npc_sprite(role)
                time_s = time.monotonic() * 4.0
                sway = math.sin(time_s) * 8.0
                ghost_w = max(1, int(base_sprite.get_width() * 0.95))
                ghost_h = max(1, int(base_sprite.get_height() * 0.95))
                scaled = pygame.transform.smoothscale(base_sprite, (ghost_w, ghost_h))
                soul_surf = pygame.Surface((ghost_w + 16, ghost_h + 16), pygame.SRCALPHA)
                soul_surf.blit(scaled, (8, 12))
                halo_rect = pygame.Rect(ghost_w // 2, 2, 16, 6)
                pygame.draw.ellipse(soul_surf, (255, 235, 100, int(230 * alpha)), halo_rect, 2)
                soul_surf.fill((255, 255, 255, int(190 * alpha)), special_flags=pygame.BLEND_RGBA_MULT)
                rotated = pygame.transform.rotate(soul_surf, sway)
                self.screen.blit(rotated, rotated.get_rect(center=(sx, sy)))
            elif p_type == "skill_banner":
                txt = p["text"]
                txt_surf = self.font.render(txt, True, p["color"])
                bg_w = txt_surf.get_width() + 24
                bg_h = txt_surf.get_height() + 12
                bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                bg_surf.fill((20, 24, 35, int(220 * alpha)))
                pygame.draw.rect(bg_surf, (255, 215, 80, int(240 * alpha)), pygame.Rect(0, 0, bg_w, bg_h), 2, border_radius=6)
                self.screen.blit(bg_surf, (sx - bg_w // 2, sy - bg_h // 2))
                self.screen.blit(txt_surf, (sx - txt_surf.get_width() // 2, sy - txt_surf.get_height() // 2))
            elif "rot" in p:
                sz = max(2, int(p.get("size", 3.0) * alpha))
                p_surf = pygame.Surface((sz, max(2, int(sz * 1.5))), pygame.SRCALPHA)
                col = p["color"]
                p_surf.fill((col[0], col[1], col[2], int(250 * alpha)))
                rot_surf = pygame.transform.rotate(p_surf, p["rot"])
                self.screen.blit(rot_surf, rot_surf.get_rect(center=(sx, sy)))
            else:
                sz = max(2, int(p.get("size", 3.0) * alpha))
                pygame.draw.circle(self.screen, p["color"], (sx, sy), sz)

    def _render_night_overlay(self, fade: float) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        r, g, b, a = COLOR_NIGHT_OVERLAY
        overlay.fill((r, g, b, int(a * fade)))
        self.screen.blit(overlay, (0, 0))

    def render_npcs(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        bar_w = TILE_SIZE - 4
        bar_h = 4

        for npc in self.world.npcs:
            if getattr(npc, "is_resting", False):
                continue
            base_sx = int(npc.x - cam_x)
            base_sy = int(npc.y - cam_y)


            # Paper Mario: 2D Soft Ground Shadow
            shadow_w = 22
            shadow_h = 7
            shadow_rect = pygame.Rect(base_sx - shadow_w // 2, base_sy + 14 - shadow_h // 2, shadow_w, shadow_h)
            shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), pygame.Rect(0, 0, shadow_w, shadow_h))
            self.screen.blit(shadow_surf, shadow_rect)

            # River / Mud Ground Footing Effects
            t_now = time.monotonic()
            if getattr(npc, "is_in_river", False):
                r_w = int(24 + math.sin(t_now * 7.0 + npc.id) * 4.0)
                water_surf = pygame.Surface((r_w, 8), pygame.SRCALPHA)
                pygame.draw.ellipse(water_surf, (160, 220, 255, 180), pygame.Rect(0, 0, r_w, 8), 2)
                self.screen.blit(water_surf, (base_sx - r_w // 2, base_sy + 10))
            elif getattr(npc, "immobilized_timer", 0.0) > 0.0:
                mud_surf = pygame.Surface((28, 12), pygame.SRCALPHA)
                pygame.draw.ellipse(mud_surf, (65, 45, 25, 220), pygame.Rect(0, 0, 28, 12))
                pygame.draw.ellipse(mud_surf, (110, 80, 50, 230), pygame.Rect(4, 2, 20, 8), 2)
                self.screen.blit(mud_surf, (base_sx - 14, base_sy + 9))


            # Paper Mario: Card Flip Horizontal Scale
            flip_p = getattr(npc, "flip_progress", 1.0)
            paper_flip_scale = max(0.08, abs(math.cos(flip_p * math.pi)))

            draw_x = npc.x
            draw_y = npc.y
            tilt_angle = 0.0
            scale_x = 1.0
            scale_y = 1.0
            display_facing = getattr(npc, "display_facing_left", False)
            is_attacking = (getattr(npc, "attack_timer", 0.0) > 0)
            ap = (1.0 - (npc.attack_timer / 0.35)) if is_attacking else 0.0

            if getattr(npc, "hit_timer", 0.0) > 0:
                # 1. Hit Hurt Reaction (Squash & Wobble)
                hp = npc.hit_timer / 0.25
                scale_x = 1.0 + 0.35 * hp
                scale_y = 1.0 - 0.30 * hp
                draw_y -= 4.0 * hp
                tilt_angle = math.sin(hp * 30.0) * 16.0
            elif is_attacking:
                # 2. Combat Attack Strike (Lunge & Weapon Swing)
                if ap < 0.40:
                    prog = ap / 0.40
                    scale_y = 1.0 + 0.25 * prog
                    scale_x = 1.0 - 0.15 * prog
                    tilt_angle = -24.0 * prog
                    draw_y -= 3.0 * prog
                else:
                    prog = (ap - 0.40) / 0.60
                    scale_y = 0.70 + 0.30 * prog
                    scale_x = 1.30 - 0.30 * prog
                    tilt_angle = 30.0 * (1.0 - prog)
                    lunge_dir = -1.0 if display_facing else 1.0
                    draw_x += lunge_dir * 8.0 * (1.0 - prog)
            elif getattr(npc, "is_moving", False):
                # 3. Hop & Squash Walk
                timer = getattr(npc, "anim_timer", 0.0)
                hop_phase = math.sin(timer * 16.0)
                if hop_phase > 0:
                    draw_y -= hop_phase * 6.0
                    scale_y = 1.0 + 0.14 * hop_phase
                    scale_x = 1.0 - 0.08 * hop_phase
                    tilt_angle = math.sin(timer * 16.0) * 8.0
                else:
                    squash = abs(hop_phase)
                    scale_y = 1.0 - 0.16 * squash
                    scale_x = 1.0 + 0.16 * squash
                    tilt_angle = 0.0
            elif npc.task is not None:
                # 4. Origami Fold & Hammer/Tool Slam
                timer = getattr(npc, "work_anim_timer", 0.0)
                cycle = (timer % 0.90) / 0.90
                if cycle < 0.50:
                    p = cycle / 0.50
                    scale_y = 1.0 + 0.25 * p
                    scale_x = 1.0 - 0.15 * p
                    tilt_angle = -26.0 * p
                    draw_y -= 3.0 * p
                    offset_dir = 1.0 if display_facing else -1.0
                    draw_x += offset_dir * 3.0 * p
                elif cycle < 0.65:
                    strike_prog = (cycle - 0.50) / 0.15
                    scale_y = 0.65 + 0.25 * strike_prog
                    scale_x = 1.35 - 0.15 * strike_prog
                    tilt_angle = 28.0 * (1.0 - strike_prog)
                    draw_y += 2.0
                    offset_dir = -1.0 if display_facing else 1.0
                    draw_x += offset_dir * 5.0

                    if strike_prog < 0.25 and random.random() < 0.65:
                        confetti_colors = [
                            (255, 220, 50),
                            (255, 75, 75),
                            (60, 190, 255),
                            (85, 230, 95),
                            (215, 95, 255),
                            (255, 255, 255),
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
                    recoil_prog = (cycle - 0.65) / 0.35
                    wobble = math.sin(recoil_prog * math.pi * 3.0) * (1.0 - recoil_prog) * 0.18
                    scale_y = 1.0 + wobble
                    scale_x = 1.0 - wobble
                    tilt_angle = wobble * 18.0
            else:
                draw_y += math.sin(time.monotonic() * 2.8 + npc.id) * 1.2
                tilt_angle = math.sin(time.monotonic() * 2.0 + npc.id) * 2.0

            sx = int(draw_x - cam_x)
            sy = int(draw_y - cam_y)

            # Main Body Sprite
            base_sprite = npc_sprite(npc.role)
            if display_facing:
                base_sprite = pygame.transform.flip(base_sprite, True, False)
                tilt_angle = -tilt_angle

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

            # Tool & Combat Weapon Overlay
            if is_attacking or npc.task is not None:
                if is_attacking:
                    tool_type = "sword" if npc.role == ROLE_KNIGHT else ("staff" if npc.role == ROLE_MAGE else "axe")
                else:
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
                if is_attacking:
                    if ap < 0.40:
                        tool_angle = -60.0 * (ap / 0.40)
                        hand_dx = 8.0 * paper_flip_scale
                        hand_dy = 1.0 - 6.0 * (ap / 0.40)
                    else:
                        strike_p = (ap - 0.40) / 0.60
                        tool_angle = -60.0 + 140.0 * strike_p
                        hand_dx = (8.0 + 10.0 * strike_p) * paper_flip_scale
                        hand_dy = -5.0 + 12.0 * strike_p
                else:
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

                tw = max(1, int(tool_surf.get_width() * paper_flip_scale * 1.15))
                th = max(1, int(tool_surf.get_height() * 1.15))
                scaled_tool = pygame.transform.smoothscale(tool_surf, (tw, th))
                rotated_tool = pygame.transform.rotate(scaled_tool, tool_angle)
                tool_pos = (sx + int(hand_dx), sy + int(hand_dy))

                # Combat & Work Slash Smear Arc
                show_arc = (is_attacking and 0.40 <= ap < 0.85) or (not is_attacking and 0.50 <= cycle < 0.65)
                if show_arc:
                    trail_surf = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
                    trail_center = (TILE_SIZE, TILE_SIZE)
                    arc_rect = pygame.Rect(trail_center[0] - 18, trail_center[1] - 18, 36, 36)
                    arc_col = (255, 240, 100, 240) if npc.role == ROLE_KNIGHT else ((200, 100, 255, 240) if npc.role == ROLE_MAGE else (255, 255, 255, 210))
                    if not display_facing:
                        pygame.draw.arc(trail_surf, (255, 255, 255, 210), arc_rect, 0.0, 2.1, 4)
                        pygame.draw.arc(trail_surf, arc_col, arc_rect, 0.3, 1.7, 3)
                    else:
                        pygame.draw.arc(trail_surf, (255, 255, 255, 210), arc_rect, 1.0, 3.14, 4)
                        pygame.draw.arc(trail_surf, arc_col, arc_rect, 1.4, 2.8, 3)
                    self.screen.blit(trail_surf, (tool_pos[0] - TILE_SIZE, tool_pos[1] - TILE_SIZE))

                self.screen.blit(rotated_tool, rotated_tool.get_rect(center=tool_pos))

                # Arcane Casting Flare at Mage staff crystal tip
                if is_attacking and npc.role == ROLE_MAGE and ap < 0.45:
                    flare_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
                    flare_r = int(6 + 3 * math.sin(time.monotonic() * 22.0))
                    pygame.draw.circle(flare_surf, (200, 100, 255, 190), (12, 12), flare_r)
                    pygame.draw.circle(flare_surf, (255, 255, 255, 240), (12, 12), 3)
                    for dx_f, dy_f in [(0, -7), (0, 7), (-7, 0), (7, 0)]:
                        pygame.draw.line(flare_surf, (255, 230, 255, 220), (12, 12), (12 + dx_f, 12 + dy_f), 1)
                    self.screen.blit(flare_surf, (tool_pos[0] - 12, tool_pos[1] - 12))


            # Environmental Status Effects: Burning Flames on NPC
            if getattr(npc, "is_burning", False):
                flame_surf = pygame.Surface((38, 48), pygame.SRCALPHA)
                # Soft heat haze aura
                pygame.draw.ellipse(flame_surf, (255, 90, 20, 100), pygame.Rect(4, 14, 30, 28))
                pygame.draw.ellipse(flame_surf, (255, 180, 40, 150), pygame.Rect(8, 18, 22, 22))

                # 4 Rising flame tongues
                flame_tongues = [
                    (-9, 6, 20.0, (255, 60, 20)),
                    (-3, 0, 24.0, (255, 140, 30)),
                    (3, 2, 22.0, (255, 210, 40)),
                    (9, 7, 18.0, (255, 80, 20)),
                ]
                for off_x, base_y, speed_f, col in flame_tongues:
                    f_h = 12 + math.sin(t_now * speed_f + off_x) * 5.0
                    f_x = 19 + off_x + math.sin(t_now * 12.0 + off_x) * 2.0
                    f_y = 34 - f_h
                    p1 = (f_x, f_y)
                    p2 = (f_x - 4, 34)
                    p3 = (f_x + 4, 34)
                    pygame.draw.polygon(flame_surf, col, [p1, p2, p3])

                # Floating glowing heat sparks
                for k in range(3):
                    emb_x = 19 + math.sin(t_now * 15.0 + k * 2.1) * 11.0
                    emb_y = 22 - ((t_now * 30.0 + k * 11.0) % 26.0)
                    pygame.draw.circle(flame_surf, (255, 245, 120, 230), (int(emb_x), int(emb_y)), 2)

                self.screen.blit(flame_surf, (base_sx - 19, base_sy - 24))

            # Mud Immobilized Countdown Badge
            if getattr(npc, "immobilized_timer", 0.0) > 0.0:
                bubble_surf = pygame.Surface((32, 16), pygame.SRCALPHA)
                pygame.draw.rect(bubble_surf, (50, 35, 20, 220), pygame.Rect(0, 0, 32, 16), border_radius=4)
                pygame.draw.rect(bubble_surf, (150, 110, 60, 240), pygame.Rect(0, 0, 32, 16), 1, border_radius=4)
                sec_txt = self.font.render(f"{npc.immobilized_timer:.1f}s", True, (255, 225, 130))
                bubble_surf.blit(sec_txt, (bubble_surf.get_width() // 2 - sec_txt.get_width() // 2, 1))
                self.screen.blit(bubble_surf, (base_sx - 16, base_sy - 38))

            # Hunger bar
            bar_x = base_sx - bar_w // 2
            bar_y = base_sy - TILE_SIZE // 2 - bar_h - 4
            hunger_ratio = max(0.0, min(1.0, npc.hunger / NPC_MAX_HUNGER))
            pygame.draw.rect(self.screen, COLOR_BAR_BG, pygame.Rect(bar_x, bar_y, bar_w, bar_h))
            fill_w = max(0, int(bar_w * hunger_ratio))
            if fill_w > 0:
                pygame.draw.rect(self.screen, COLOR_HUNGER_BAR, pygame.Rect(bar_x, bar_y, fill_w, bar_h))

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
            facing_left = getattr(animal, "facing_left", False)
            is_attacking = (getattr(animal, "attack_timer", 0.0) > 0)
            ap = (1.0 - (animal.attack_timer / 0.35)) if is_attacking else 0.0

            if getattr(animal, "hit_timer", 0.0) > 0:
                # 1. Hurt Squash & Shake
                hp = animal.hit_timer / 0.25
                scale_x = 1.0 + 0.30 * hp
                scale_y = 1.0 - 0.25 * hp
                draw_y -= 4.0 * hp
                tilt_angle = math.sin(hp * 30.0) * 15.0
            elif is_attacking:
                # 2. Retaliation Beast Strike / Claw Attack
                if ap < 0.40:
                    prog = ap / 0.40
                    scale_y = 1.0 + 0.35 * prog
                    scale_x = 1.0 - 0.20 * prog
                    tilt_angle = -22.0 * prog
                else:
                    prog = (ap - 0.40) / 0.60
                    scale_y = 0.70 + 0.30 * prog
                    scale_x = 1.30 - 0.30 * prog
                    tilt_angle = 26.0 * (1.0 - prog)
                    lunge_dir = -1.0 if facing_left else 1.0
                    draw_x += lunge_dir * 8.0 * (1.0 - prog)
            elif getattr(animal, "is_moving", False):
                # 3. Hop & Squash Walk
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
            elif getattr(animal, "is_tamed", False) and not getattr(animal, "is_following", False) and getattr(animal, "idle_target", None) is None:
                # 4. Settled Idle Hop - gentler and slower than the walk
                # bounce, just enough to read as "parked here on purpose"
                # rather than a frozen/stuck sprite once it's done walking
                # to its spot beside the pen.
                timer = getattr(animal, "anim_timer", 0.0)
                hop = max(0.0, math.sin(timer * 3.0))
                if hop > 0:
                    draw_y -= hop * 3.0
                    scale_y = 1.0 + 0.05 * hop
                    scale_x = 1.0 - 0.03 * hop

            screen_x = int(draw_x - self.camera.x)
            screen_y = int(draw_y - self.camera.y)
            sprite = animal_sprite(animal.species)
            if sprite is not None:
                if facing_left:
                    sprite = pygame.transform.flip(sprite, True, False)
                    tilt_angle = -tilt_angle

                tw = max(1, int(sprite.get_width() * scale_x))
                th = max(1, int(sprite.get_height() * scale_y))
                transformed = pygame.transform.smoothscale(sprite, (tw, th))
                if abs(tilt_angle) > 0.5:
                    transformed = pygame.transform.rotate(transformed, tilt_angle)
                self.screen.blit(transformed, transformed.get_rect(center=(screen_x, screen_y)))

                # Beast claw swipe arc on attack
                if is_attacking and 0.40 <= ap < 0.85:
                    claw_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
                    arc_rect = pygame.Rect(4, 4, 28, 28)
                    if not facing_left:
                        pygame.draw.arc(claw_surf, (255, 90, 60, 230), arc_rect, 0.2, 2.0, 3)
                    else:
                        pygame.draw.arc(claw_surf, (255, 90, 60, 230), arc_rect, 1.2, 3.0, 3)
                    self.screen.blit(claw_surf, (screen_x - 18, screen_y - 18))
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
            facing_left = getattr(monster, "display_facing_left", False)
            is_attacking = (getattr(monster, "attack_timer", 0.0) > 0)
            ap = (1.0 - (monster.attack_timer / 0.35)) if is_attacking else 0.0

            if getattr(monster, "hit_timer", 0.0) > 0:
                # 1. Monster Hurt Squash & Recoil
                hp = monster.hit_timer / 0.25
                scale_x = 1.0 + 0.35 * hp
                scale_y = 1.0 - 0.30 * hp
                draw_y -= 5.0 * hp
                tilt_angle = math.sin(hp * 30.0) * 16.0
            elif is_attacking:
                # 2. Monster Bite / Claw Attack Strike
                if ap < 0.35:
                    prog = ap / 0.35
                    scale_y = 1.0 + 0.30 * prog
                    scale_x = 1.0 - 0.20 * prog
                    tilt_angle = -20.0 * prog
                else:
                    prog = (ap - 0.35) / 0.65
                    scale_y = 0.65 + 0.35 * prog
                    scale_x = 1.35 - 0.35 * prog
                    tilt_angle = 25.0 * (1.0 - prog)
                    lunge_dir = -1.0 if facing_left else 1.0
                    draw_x += lunge_dir * 9.0 * (1.0 - prog)
            elif getattr(monster, "is_moving", False):
                # 3. Hop & Squash Walk
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
            else:
                draw_y += math.sin(time.monotonic() * 2.5 + monster.x) * 1.0

            screen_x = int(draw_x - self.camera.x)
            screen_y = int(draw_y - self.camera.y)
            sprite = monster_sprite(monster.type)
            if sprite is not None:
                if facing_left:
                    sprite = pygame.transform.flip(sprite, True, False)
                    tilt_angle = -tilt_angle

                tw = max(1, int(sprite.get_width() * scale_x))
                th = max(1, int(sprite.get_height() * scale_y))
                transformed = pygame.transform.smoothscale(sprite, (tw, th))
                if abs(tilt_angle) > 0.5:
                    transformed = pygame.transform.rotate(transformed, tilt_angle)
                self.screen.blit(transformed, transformed.get_rect(center=(screen_x, screen_y)))

                # Persistent Burn Status VFX (flame tongues & embers)
                if getattr(monster, "burn_ticks_remaining", 0) > 0:
                    t_burn = time.monotonic() * 12.0
                    burn_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
                    flame_pts = [
                        (6, 26),
                        (12, 10 + int(math.sin(t_burn) * 5)),
                        (18, 16),
                        (24, 8 + int(math.cos(t_burn) * 5)),
                        (30, 26),
                    ]
                    pygame.draw.polygon(burn_surf, (255, 70, 20, 210), flame_pts)
                    pygame.draw.polygon(burn_surf, (255, 200, 40, 240), [(p[0], p[1] + 4) for p in flame_pts])
                    self.screen.blit(burn_surf, (screen_x - 18, screen_y - 20))

                # Persistent Freeze Status VFX (translucent origami ice block & frost crystals)
                if getattr(monster, "is_frozen", False):
                    ice_box = pygame.Surface((36, 40), pygame.SRCALPHA)
                    pygame.draw.rect(ice_box, (100, 215, 255, 115), pygame.Rect(2, 2, 32, 36), border_radius=4)
                    pygame.draw.rect(ice_box, (220, 250, 255, 230), pygame.Rect(2, 2, 32, 36), 2, border_radius=4)
                    # Diagonal specular gleam line
                    pygame.draw.line(ice_box, (255, 255, 255, 220), (6, 6), (30, 30), 2)
                    self.screen.blit(ice_box, (screen_x - 18, screen_y - 20))

                # Red/Purple Claw Slash Smear Arc during monster attack
                if is_attacking and 0.35 <= ap < 0.85:
                    claw_surf = pygame.Surface((38, 38), pygame.SRCALPHA)
                    arc_rect = pygame.Rect(4, 4, 30, 30)
                    if not facing_left:
                        pygame.draw.arc(claw_surf, (255, 60, 60, 240), arc_rect, 0.2, 2.2, 4)
                        pygame.draw.arc(claw_surf, (220, 40, 160, 200), arc_rect, 0.4, 1.8, 3)
                    else:
                        pygame.draw.arc(claw_surf, (255, 60, 60, 240), arc_rect, 1.0, 3.0, 4)
                        pygame.draw.arc(claw_surf, (220, 40, 160, 200), arc_rect, 1.3, 2.7, 3)
                    self.screen.blit(claw_surf, (screen_x - 19, screen_y - 19))
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
        # rescanning world.tasks.tasks for every visible tile. task.py's own
        # per-tick purge keeps dead tasks out of the queue entirely now, but
        # this still guards the one-tick window between a task going invalid
        # mid-work and the next purge sweep picking it up.
        queued_by_tile = {
            task.target: task for task in self.world.tasks.tasks if task_can_perform(self.world, task)
        }

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
                else:
                    terrain_type = getattr(tile, "terrain", "plain")
                    surf = get_terrain_surface(terrain_type, tile.claimed)
                    self.screen.blit(surf, rect)
                    if not tile.claimed and terrain_type == "plain":
                        self.screen.blit(parchment(), rect)
                    elif not tile.claimed:
                        unclaimed_tint = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        unclaimed_tint.fill((0, 0, 0, 50))
                        self.screen.blit(unclaimed_tint, rect)


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
            if building.type == "Farmland":
                if building.ready:
                    info = "Building: Farmland (Ready to Harvest!)"
                else:
                    info = f"Building: Farmland (Growing: {int(building.growth_timer)}/{int(FARMLAND_GROW_SECONDS)}s)"
            else:
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
            if options[0] == "Destroy":
                return "  ->  Click for menu: Destroy"
            return f"  ->  Click to {options[0]}"
        return f"  ->  Click to choose: {', '.join(options)}"

    def _inventory_item_count(self) -> int:
        """Must match len(inventory_items) passed to top_bar.render() -
        magic_panel's y-position depends on both agreeing."""
        return len(self.world.inventory.items())

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
            self.screen, self.font,
            self.cycle.round_number, self.cycle.phase.upper(),
            self.cycle.remaining(), self.cycle.duration(), banner_color,
            len(self.world.npcs), inventory_items, hint_lines,
        )

    def _game_over_panel_rect(self) -> pygame.Rect:
        panel_w, panel_h = 460, 280
        return pygame.Rect((WINDOW_WIDTH - panel_w) // 2, (WINDOW_HEIGHT - panel_h) // 2, panel_w, panel_h)

    def _game_over_restart_button_rect(self) -> pygame.Rect:
        panel = self._game_over_panel_rect()
        btn_w, btn_h = 200, 48
        return pygame.Rect(panel.centerx - btn_w // 2, panel.bottom - btn_h - 24, btn_w, btn_h)

    def render_game_over(self) -> None:
        if not self.game_over_state.is_over:
            return

        panel = self._game_over_panel_rect()
        overlay = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        overlay.fill((20, 22, 28, 235))
        self.screen.blit(overlay, panel.topleft)
        pygame.draw.rect(self.screen, COLOR_GAME_OVER, panel, 3, border_radius=8)

        title_surf = self.big_font.render("GAME OVER", True, COLOR_GAME_OVER)
        self.screen.blit(title_surf, title_surf.get_rect(center=(panel.centerx, panel.top + 54)))

        score_surf = self.font.render(f"Score: Round {self.game_over_state.score}", True, COLOR_TEXT)
        self.screen.blit(score_surf, score_surf.get_rect(center=(panel.centerx, panel.top + 108)))

        best_surf = self.font.render(f"Best Score: Round {self.best_score}", True, COLOR_DAY_BANNER)
        self.screen.blit(best_surf, best_surf.get_rect(center=(panel.centerx, panel.top + 138)))

        button = self._game_over_restart_button_rect()
        hovered = button.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (48, 56, 72) if hovered else (30, 33, 40), button, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_GAME_OVER, button, 2, border_radius=6)
        btn_label = self.font.render("Restart  [R]", True, COLOR_TEXT)
        self.screen.blit(btn_label, btn_label.get_rect(center=button.center))
