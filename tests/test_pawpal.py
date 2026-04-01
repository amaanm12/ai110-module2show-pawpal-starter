"""
tests/test_pawpal.py
Simple unit tests for core PawPal+ logic.
"""

import sys
import os

# Allow imports from the project root regardless of where pytest is run from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


# ------------------------------------------------------------------
# Test 1 — Task Completion
# ------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    # Task should start as not completed
    assert task.completed is False

    task.mark_complete()

    # After marking complete, status should be True
    assert task.completed is True


# ------------------------------------------------------------------
# Test 2 — Task Addition
# ------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog", age=3)

    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Breakfast feeding", duration_minutes=10, priority="high"))

    assert len(pet.tasks) == 1
