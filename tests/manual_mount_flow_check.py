"""One-off headless script driving Game.handle_click() through the full
mount flow: idle -> follow -> Ride -> Dismount -> Back to Pen, asserting
state at each step. Not part of the pytest suite (matches smoke_render.py's
own "not unit tested, verified via a headless script" precedent for the
pygame-coupled game.py seam) - run manually during development:

  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/manual_mount_flow_check.py
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pygame

from animal import Animal
from constants import MOUNTED_SPEED_BONUS
from game import Game


def _click(game: Game, world_pos: tuple[float, float]) -> None:
    screen_pos = (int(world_pos[0] - game.camera.x), int(world_pos[1] - game.camera.y))
    game.handle_click(screen_pos)


def main() -> None:
    game = Game()
    game._start_new_game()

    npc = game.world.npcs[0]
    # Offset from the NPC so the idle/following-stage clicks land on the
    # animal, not the NPC standing beneath it - they only need to actually
    # overlap once mounted (step 4 below).
    horse = Animal(npc.x + 60, npc.y, species="Horse", speed=140.0, dangerous=False, health=40)
    horse.is_tamed = True
    horse.tamer_npc_id = npc.id
    game.world.animals.append(horse)

    game.render()  # exercise the ordinary PLAYING-state render path once

    # 1. Idle -> click starts following (no menu, single click = follow)
    _click(game, (horse.x, horse.y))
    assert horse.is_following is True, "click on idle tamed animal should start following"
    assert not game.animal_menu.visible
    print("idle -> follow OK")

    # 2. Following -> click opens the menu with Ride enabled (Horse is mountable)
    _click(game, (horse.x, horse.y))
    assert game.animal_menu.visible, "click on a following animal should open its menu"
    assert game.animal_menu.options == ["Keep Following", "Ride", "Back to Pen"]
    assert "Ride" not in game.animal_menu.disabled
    print("follow -> menu (Ride enabled) OK")

    # 3. Choose Ride
    menu_screen_pos = game.animal_menu.screen_pos
    ride_row_pos = (menu_screen_pos[0] + 5, menu_screen_pos[1] + 1 * 30 + 5)  # row index 1 = "Ride"
    game.handle_click(ride_row_pos)
    assert horse.is_mounted is True
    assert horse.is_following is True
    print("Ride OK")

    # 4. While mounted, clicking the (overlapping) rider+horse position must
    #    reach the horse, not the rider - this is the _npc_at_world_pos fix.
    #    (animal.update() is what actually snaps horse.x/y to the rider each
    #    tick in real gameplay - simulate one tick's worth here.)
    horse.x, horse.y = npc.x, npc.y
    _click(game, (horse.x, horse.y))
    assert game.animal_menu.visible, "click on a mounted horse should open its menu, not select the rider"
    assert game.animal_menu.options == ["Dismount", "Back to Pen"]
    assert game.selected_npc is not npc, "must not have fallen through to NPC selection"
    print("mounted click-through-to-horse OK")

    # 5. Dismount
    menu_screen_pos = game.animal_menu.screen_pos
    dismount_row_pos = (menu_screen_pos[0] + 5, menu_screen_pos[1] + 0 * 30 + 5)  # row 0 = "Dismount"
    game.handle_click(dismount_row_pos)
    assert horse.is_mounted is False
    assert horse.is_following is True  # dismount keeps it following, doesn't send it home
    print("Dismount OK")

    # 6. Back to Pen must also clear is_mounted (requires a pen_tile - the
    #    helper is a no-op without one, matching the UI's own disabled-row rule)
    horse.is_mounted = True  # simulate remounting without going through the menu again
    horse.pen_tile = (3, 3)
    game._send_animal_back_to_pen(horse.id)
    assert horse.is_mounted is False
    print("Back to Pen clears is_mounted OK")

    # 7. tick_pen_production actually grants the speed bonus while mounted
    from tame_task import _tick_pen_production

    horse.is_mounted = True
    horse.is_following = True
    npc.base_speed = 120.0
    _tick_pen_production(game.world, 0.1)
    assert npc.speed == 120.0 + MOUNTED_SPEED_BONUS
    print(f"mounted speed bonus applied OK (npc.speed={npc.speed})")

    print("\nAll mount-flow checks passed.")


if __name__ == "__main__":
    main()
