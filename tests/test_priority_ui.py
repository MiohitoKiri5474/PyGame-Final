"""Unit tests for priority table UI logic (ticket 05).

Tests the claim-algorithm integration — verifying that manually setting an
NPC's priority order changes which task it claims. The UI rendering itself
is manually verified (thin pygame layer over already-tested logic).

Run with:  python -m pytest tests/test_priority_ui.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

import task as task_module
from task import TaskQueue, TaskType
from npc import NPC
from priority_ui import PriorityTableUI


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _reset_npc_ids():
    NPC._next_id = 0


def _dummy_task_types():
    """Return a dict of 4 dummy task types matching the real registered names."""
    return {
        name: TaskType(
            work_seconds=1.0,
            can_queue=lambda w, t: True,
            on_complete=lambda w, t: True,
        )
        for name in ["Gather", "Expand", "BuildWall", "BuildTower"]
    }


# ------------------------------------------------------------------
# Priority affects idle-claim (ticket 05 core requirement)
# ------------------------------------------------------------------

class TestPriorityAffectsClaim:
    """Changing NPC priority order visibly changes which task is claimed."""

    def test_npc_claims_highest_priority_task(self):
        _reset_npc_ids()
        queue = TaskQueue()
        queue.add("Gather", (0, 0))
        queue.add("BuildWall", (1, 1))

        npc = NPC(0.0, 0.0, priority=["BuildWall", "Gather"])
        claimed = queue.claim_for(npc)
        assert claimed is not None
        assert claimed.type == "BuildWall"

    def test_reordering_priority_changes_claimed_task(self):
        _reset_npc_ids()
        # First claim: Gather is highest priority
        queue = TaskQueue()
        queue.add("Gather", (0, 0))
        queue.add("BuildWall", (1, 1))

        npc = NPC(0.0, 0.0, priority=["Gather", "BuildWall"])
        claimed = queue.claim_for(npc)
        assert claimed.type == "Gather"

        # Release the claim
        claimed.assigned_npc = None

        # Reorder: now BuildWall is highest
        npc.priority = ["BuildWall", "Gather"]
        npc.task = None
        claimed2 = queue.claim_for(npc)
        assert claimed2.type == "BuildWall"

    def test_different_npcs_claim_different_tasks_by_priority(self):
        _reset_npc_ids()
        queue = TaskQueue()
        queue.add("Gather", (0, 0))
        queue.add("Expand", (1, 1))

        npc_a = NPC(0.0, 0.0, priority=["Gather", "Expand"])
        npc_b = NPC(0.0, 0.0, priority=["Expand", "Gather"])

        claim_a = queue.claim_for(npc_a)
        claim_b = queue.claim_for(npc_b)

        assert claim_a.type == "Gather"
        assert claim_b.type == "Expand"

    def test_all_four_task_types_respected(self):
        _reset_npc_ids()
        all_types = ["Gather", "Expand", "BuildWall", "BuildTower"]
        # Queue one of each
        queue = TaskQueue()
        for t in all_types:
            queue.add(t, (0, 0))

        # Reversed priority
        npc = NPC(0.0, 0.0, priority=list(reversed(all_types)))
        claimed = queue.claim_for(npc)
        assert claimed.type == "BuildTower"  # last in default, first in reversed


# ------------------------------------------------------------------
# PriorityTableUI logic (no rendering, just state)
# ------------------------------------------------------------------

class TestPriorityTableUILogic:
    """UI state management tests."""

    def test_toggle_visibility(self):
        ui = PriorityTableUI()
        assert ui.visible is False
        ui.toggle()
        assert ui.visible is True
        ui.toggle()
        assert ui.visible is False

    def test_ensure_priority_materializes_none(self, monkeypatch):
        monkeypatch.setattr(task_module, "TASK_TYPES", _dummy_task_types())
        _reset_npc_ids()
        npc = NPC(0.0, 0.0)
        assert npc.priority is None
        PriorityTableUI._ensure_priority(npc)
        assert npc.priority is not None
        assert len(npc.priority) == 4

    def test_ensure_priority_preserves_existing(self):
        _reset_npc_ids()
        npc = NPC(0.0, 0.0, priority=["BuildWall", "Gather"])
        PriorityTableUI._ensure_priority(npc)
        assert npc.priority == ["BuildWall", "Gather"]

    def test_swap_priority_up(self):
        priority = ["Gather", "Expand", "BuildWall", "BuildTower"]
        PriorityTableUI._swap_priority(priority, 2, -1)  # move BuildWall up
        assert priority == ["Gather", "BuildWall", "Expand", "BuildTower"]

    def test_swap_priority_down(self):
        priority = ["Gather", "Expand", "BuildWall", "BuildTower"]
        PriorityTableUI._swap_priority(priority, 1, +1)  # move Expand down
        assert priority == ["Gather", "BuildWall", "Expand", "BuildTower"]

    def test_swap_priority_wraps_top(self):
        priority = ["Gather", "Expand", "BuildWall"]
        PriorityTableUI._swap_priority(priority, 0, -1)  # wrap from top
        assert priority == ["BuildWall", "Expand", "Gather"]

    def test_swap_priority_wraps_bottom(self):
        priority = ["Gather", "Expand", "BuildWall"]
        PriorityTableUI._swap_priority(priority, 2, +1)  # wrap from bottom
        assert priority == ["BuildWall", "Expand", "Gather"]

    def test_swap_writes_through_to_npc(self, monkeypatch):
        """Reordering in the UI writes to the same npc.priority object."""
        monkeypatch.setattr(task_module, "TASK_TYPES", _dummy_task_types())
        _reset_npc_ids()
        npc = NPC(0.0, 0.0)
        priority = PriorityTableUI._ensure_priority(npc)
        original_first = priority[0]
        PriorityTableUI._swap_priority(priority, 0, +1)
        # npc.priority is the same list object, so mutation is visible
        assert npc.priority[0] != original_first
        assert npc.priority[1] == original_first
