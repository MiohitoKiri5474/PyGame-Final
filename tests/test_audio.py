import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

import audio
from gather_task import _on_complete
from task import Task, update_npc_tasks
from world import World
from npc import NPC


class TestAudioSFX:
    def test_play_sfx_safe_when_mixer_uninitialized(self):
        # All 9 sound effects should be safely callable
        for name in ("chop", "gather", "mine", "build", "lightning", "fire", "freeze", "night_howl", "dawn"):
            audio.play_sfx(name)
        audio.play_sfx("non_existent_sfx")

    def test_gather_task_triggers_sound_safely(self):
        world = World()
        # Test wood chopping trigger
        tile_wood = world.grid.get(5, 5)
        tile_wood.claimed = True
        tile_wood.resource = "wood"

        task_wood = Task(type="Gather", target=(5, 5))
        assert _on_complete(world, task_wood) is True
        assert tile_wood.resource is None
        assert world.inventory.get("wood") >= 1

        # Test crop gathering trigger
        tile_crop = world.grid.get(6, 6)
        tile_crop.claimed = True
        tile_crop.resource = "crop"

        task_crop = Task(type="Gather", target=(6, 6))
        assert _on_complete(world, task_crop) is True
        assert tile_crop.resource is None
        assert world.inventory.get("crop") >= 1

    def test_work_progress_sound_trigger_paths(self):
        world = World()
        tile_mine = world.grid.get(7, 7)
        tile_mine.claimed = True
        tile_mine.resource = "bricks"

        npc = NPC(x=7 * 32 + 16, y=7 * 32 + 16)
        task_mine = Task(type="Gather", target=(7, 7), assigned_npc=npc)
        npc.task = task_mine
        world.npcs.append(npc)
        world.tasks.tasks.append(task_mine)

        # First tick starts rhythmic work SFX
        update_npc_tasks(world, 0.1)
        assert getattr(npc, "work_sfx_timer", 0.0) > 0.0
