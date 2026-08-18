import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

import audio
from gather_task import _on_complete
from task import Task
from world import World


class TestAudioSFX:
    def test_play_sfx_safe_when_mixer_uninitialized(self):
        # Should not throw any exceptions even if mixer is not initialized
        audio.play_sfx("chop")
        audio.play_sfx("gather")
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
