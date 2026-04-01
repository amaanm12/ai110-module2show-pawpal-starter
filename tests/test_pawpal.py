"""
tests/test_pawpal.py
Automated test suite for core PawPal+ logic.
"""

import sys
import os
from datetime import date, timedelta

# Allow imports from the project root regardless of where pytest is run from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Owner, Scheduler


# ------------------------------------------------------------------
# Test 1 — Task Completion
# ------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    assert task.completed is False

    task.mark_complete()

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


# ------------------------------------------------------------------
# Test 3 — Sorting Correctness
# ------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """
    Tasks added out of order should be returned in HH:MM chronological
    order after build_schedule() assigns times and sort_by_time() is called.
    """
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    # Add tasks in reverse-priority order so their scheduled times will also
    # be assigned in a non-trivial order — low priority gets time last.
    pet.add_task(Task("Evening walk",      duration_minutes=25, priority="low",    frequency="daily"))
    pet.add_task(Task("Breakfast feeding", duration_minutes=10, priority="high",   frequency="daily"))
    pet.add_task(Task("Playtime",          duration_minutes=20, priority="medium", frequency="daily"))

    scheduler = Scheduler(owner=owner)
    plan = scheduler.build_schedule()           # assigns HH:MM to each task
    sorted_plan = scheduler.sort_by_time(plan)  # re-orders by those times

    times = [task.scheduled_time for _, task in sorted_plan]

    # Each time must be <= the next one (chronological order)
    for i in range(len(times) - 1):
        assert times[i] <= times[i + 1], (
            f"Time out of order: {times[i]} should come before {times[i + 1]}"
        )


# ------------------------------------------------------------------
# Test 4 — Recurrence Logic
# ------------------------------------------------------------------

def test_marking_daily_task_complete_creates_next_occurrence():
    """
    Completing a daily task should automatically add a new pending Task
    with a due_date of today + 1 day to the pet's task list.
    """
    today = date.today()
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(pet)

    pet.add_task(Task(
        title="Breakfast feeding",
        duration_minutes=5,
        priority="high",
        frequency="daily",
        due_date=today,
    ))

    scheduler = Scheduler(owner=owner)
    success, _ = scheduler.mark_task_complete("Luna", "Breakfast feeding")

    assert success is True

    # The original task should now be completed
    original = next(t for t in pet.tasks if t.due_date == today)
    assert original.completed is True

    # A new pending task for tomorrow should have been created
    tomorrow = today + timedelta(days=1)
    next_occurrences = [t for t in pet.tasks if t.due_date == tomorrow and not t.completed]
    assert len(next_occurrences) == 1, "Expected exactly one new pending task for tomorrow"
    assert next_occurrences[0].title == "Breakfast feeding"


# ------------------------------------------------------------------
# Test 5 — Conflict Detection
# ------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """
    Two tasks manually assigned the same start time should be flagged
    as a conflict; tasks with non-overlapping times should not be flagged.
    """
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Buddy", species="dog", age=2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)

    # --- overlapping case ---
    task_a = Task("Vet appointment", duration_minutes=60, priority="high", frequency="as-needed")
    task_b = Task("Bath time",       duration_minutes=30, priority="high", frequency="as-needed")
    task_a.scheduled_time = "09:00"
    task_b.scheduled_time = "09:00"   # same start → guaranteed overlap

    conflicts = scheduler.detect_conflicts([(pet, task_a), (pet, task_b)])

    assert len(conflicts) == 1, "Expected exactly one conflict warning"
    assert "overlaps" in conflicts[0]

    # --- non-overlapping case ---
    task_c = Task("Morning walk", duration_minutes=30, priority="high", frequency="daily")
    task_d = Task("Evening walk", duration_minutes=30, priority="medium", frequency="daily")
    task_c.scheduled_time = "08:00"
    task_d.scheduled_time = "09:00"   # starts exactly when task_c ends → no overlap

    no_conflicts = scheduler.detect_conflicts([(pet, task_c), (pet, task_d)])

    assert len(no_conflicts) == 0, "Expected no conflicts for back-to-back tasks"
