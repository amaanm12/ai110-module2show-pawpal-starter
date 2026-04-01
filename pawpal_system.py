"""
pawpal_system.py
Logic layer for PawPal+ — backend classes for the pet care scheduling system.
"""

from datetime import date, timedelta


class Task:
    """
    Represents a single pet care activity.

    Attributes:
        title            - short name for the task
        description      - longer explanation of what the task involves
        duration_minutes - how long the task takes
        frequency        - how often it should occur ("daily", "weekly", "as-needed")
        priority         - urgency level ("low", "medium", "high")
        category         - type of care ("feeding", "walk", "grooming", "medication", "general")
        completed        - whether the task has been done for the current cycle
        scheduled_time   - "HH:MM" string assigned by the Scheduler during build_schedule()
        due_date         - the date this occurrence is due (datetime.date)
    """

    PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str = "medium",
        frequency: str = "daily",
        description: str = "",
        category: str = "general",
        due_date: date = None,
    ):
        self.title = title
        self.description = description
        self.duration_minutes = duration_minutes
        self.frequency = frequency          # "daily", "weekly", "as-needed"
        self.priority = priority            # "low", "medium", "high"
        self.category = category
        self.completed = False
        self.scheduled_time: str | None = None  # "HH:MM", set by Scheduler.build_schedule()
        self.due_date: date = due_date or date.today()

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    def priority_score(self) -> int:
        """Return a numeric score for priority (higher = more urgent)."""
        return self.PRIORITY_MAP.get(self.priority, 0)

    def mark_complete(self):
        """Mark this task as done for the current cycle."""
        self.completed = True

    def reset(self):
        """Reset completion status and scheduled time (e.g. start of a new day)."""
        self.completed = False
        self.scheduled_time = None

    def next_due_date(self) -> date | None:
        """
        Return the due date for the next occurrence using timedelta.
        Returns None for "as-needed" tasks (they don't auto-recur).
        """
        if self.frequency == "daily":
            return self.due_date + timedelta(days=1)
        if self.frequency == "weekly":
            return self.due_date + timedelta(weeks=1)
        return None  # "as-needed" tasks do not auto-schedule

    def __repr__(self):
        status = "done" if self.completed else "pending"
        time_str = f" @{self.scheduled_time}" if self.scheduled_time else ""
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, freq={self.frequency}, "
            f"due={self.due_date}, status={status}{time_str})"
        )


# ---------------------------------------------------------------------------


class Pet:
    """
    Stores a pet's details and its list of care tasks.

    Attributes:
        name    - pet's name
        species - e.g. "dog", "cat", "rabbit"
        age     - age in years
        notes   - any extra care notes (allergies, special needs, etc.)
        tasks   - list of Task objects assigned to this pet
    """

    def __init__(self, name: str, species: str, age: int, notes: str = ""):
        self.name = name
        self.species = species
        self.age = age
        self.notes = notes
        self.tasks: list[Task] = []

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task):
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """
        Remove the first task whose title matches (case-insensitive).
        Returns True if a task was removed, False if not found.
        """
        for i, task in enumerate(self.tasks):
            if task.title.lower() == title.lower():
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> list[Task]:
        """Return all tasks that have been completed."""
        return [t for t in self.tasks if t.completed]

    def reset_daily_tasks(self):
        """Reset completion status for all daily tasks (call at start of each day)."""
        for task in self.tasks:
            if task.frequency == "daily":
                task.reset()

    def __repr__(self):
        return (
            f"Pet(name='{self.name}', species='{self.species}', "
            f"age={self.age}, tasks={len(self.tasks)})"
        )


# ---------------------------------------------------------------------------


class Owner:
    """
    Manages multiple pets and provides a unified view of all their tasks.

    Attributes:
        name              - owner's name
        available_minutes - total care time available today (in minutes)
        pets              - list of Pet objects belonging to this owner
    """

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    # ------------------------------------------------------------------
    # Pet management
    # ------------------------------------------------------------------

    def add_pet(self, pet: Pet):
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """
        Remove the first pet whose name matches (case-insensitive).
        Returns True if removed, False if not found.
        """
        for i, pet in enumerate(self.pets):
            if pet.name.lower() == name.lower():
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, name: str) -> Pet | None:
        """Return the Pet object with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    # ------------------------------------------------------------------
    # Cross-pet task access
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs where the task is not yet completed."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]

    def __repr__(self):
        return (
            f"Owner(name='{self.name}', available_minutes={self.available_minutes}, "
            f"pets={[p.name for p in self.pets]})"
        )


# ---------------------------------------------------------------------------


class Scheduler:
    """
    The 'brain' of PawPal+.

    Retrieves tasks from all of an owner's pets, organises them by priority,
    assigns HH:MM start times, detects conflicts, and handles recurring tasks.
    """

    # Day starts at 8:00 AM (480 minutes from midnight)
    START_MINUTES = 8 * 60

    def __init__(self, owner: Owner):
        self.owner = owner

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all pending (pet, task) pairs across all pets."""
        return self.owner.get_all_pending_tasks()

    # ------------------------------------------------------------------
    # Organisation
    # ------------------------------------------------------------------

    def prioritize_tasks(self) -> list[tuple[Pet, Task]]:
        """
        Sort all pending tasks by:
          1. Priority score (high → low)
          2. Duration (shorter tasks first as a tiebreaker)
        """
        return sorted(
            self.get_all_tasks(),
            key=lambda pt: (-pt[1].priority_score(), pt[1].duration_minutes),
        )

    def sort_by_time(self, plan: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """
        Sort a plan (list of (pet, task) pairs) by each task's scheduled_time in
        "HH:MM" format using a lambda key.  Tasks without a time sort to the end.
        """
        return sorted(
            plan,
            key=lambda pt: pt[1].scheduled_time if pt[1].scheduled_time else "99:99",
        )

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Filter all (pet, task) pairs across every pet.

        Args:
            completed: True  → only completed tasks
                       False → only pending tasks
                       None  → all tasks (no filter)
            pet_name:  if given, restrict to that pet (case-insensitive)

        Returns a list of matching (pet, task) pairs.
        """
        results = []
        for pet, task in self.owner.get_all_tasks():
            if completed is not None and task.completed != completed:
                continue
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            results.append((pet, task))
        return results

    # ------------------------------------------------------------------
    # Scheduling — assigns HH:MM times to each task
    # ------------------------------------------------------------------

    def build_schedule(self) -> list[tuple[Pet, Task]]:
        """
        Greedily select tasks (highest priority first) until the owner's
        available time is exhausted.  Each accepted task gets a 'scheduled_time'
        string in "HH:MM" format calculated by advancing from START_MINUTES.

        Returns an ordered list of (pet, task) pairs.
        """
        time_remaining = self.owner.available_minutes
        current_offset = self.START_MINUTES   # minutes from midnight
        plan: list[tuple[Pet, Task]] = []

        for pet, task in self.prioritize_tasks():
            if task.duration_minutes <= time_remaining:
                hours, mins = divmod(current_offset, 60)
                task.scheduled_time = f"{hours:02d}:{mins:02d}"
                plan.append((pet, task))
                time_remaining -= task.duration_minutes
                current_offset += task.duration_minutes

        return plan

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, plan: list[tuple[Pet, Task]]) -> list[str]:
        """
        Check every pair of tasks in the plan for overlapping time windows.

        Two tasks conflict when one starts before the other ends:
            start_A < end_B  AND  start_B < end_A

        Returns a list of human-readable warning strings.
        An empty list means no conflicts.
        """
        warnings: list[str] = []

        # Build (start_min, end_min, pet, task) tuples for tasks that have a time
        timed = []
        for pet, task in plan:
            if task.scheduled_time is None:
                continue
            h, m = map(int, task.scheduled_time.split(":"))
            start = h * 60 + m
            end = start + task.duration_minutes
            timed.append((start, end, pet, task))

        # Compare every unique pair
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                s1, e1, p1, t1 = timed[i]
                s2, e2, p2, t2 = timed[j]
                if s1 < e2 and s2 < e1:          # overlap condition
                    warnings.append(
                        f"WARNING: [{p1.name}] '{t1.title}' ({t1.scheduled_time}, "
                        f"{t1.duration_minutes}min) overlaps with "
                        f"[{p2.name}] '{t2.title}' ({t2.scheduled_time}, {t2.duration_minutes}min)"
                    )

        return warnings

    # ------------------------------------------------------------------
    # Task management — with auto-recurring support
    # ------------------------------------------------------------------

    def mark_task_complete(self, pet_name: str, task_title: str) -> tuple[bool, str]:
        """
        Mark a specific pending task as complete.

        If the task is "daily" or "weekly", automatically creates the next
        occurrence (using timedelta) and adds it back to the pet's task list.

        Returns:
            (True,  message)  — task found and marked complete
            (False, message)  — pet or task not found
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False, f"No pet named '{pet_name}' found."

        for task in pet.tasks:
            if task.title.lower() == task_title.lower() and not task.completed:
                task.mark_complete()
                msg = f"'{task.title}' marked complete for {pet.name}."

                # Auto-schedule the next occurrence for recurring tasks
                next_date = task.next_due_date()
                if next_date is not None:
                    next_task = Task(
                        title=task.title,
                        duration_minutes=task.duration_minutes,
                        priority=task.priority,
                        frequency=task.frequency,
                        description=task.description,
                        category=task.category,
                        due_date=next_date,
                    )
                    pet.add_task(next_task)
                    msg += f" Next occurrence auto-scheduled for {next_date}."

                return True, msg

        return False, f"No pending task '{task_title}' found for {pet_name}."

    def reset_day(self):
        """Reset all daily tasks across every pet (call at the start of a new day)."""
        for pet in self.owner.pets:
            pet.reset_daily_tasks()

    # ------------------------------------------------------------------
    # Summary / explanation
    # ------------------------------------------------------------------

    def get_summary(self, plan: list[tuple[Pet, Task]] = None) -> str:
        """
        Return a human-readable summary of the scheduled plan.
        If no plan is provided, one is built automatically.
        """
        if plan is None:
            plan = self.build_schedule()

        if not plan:
            return (
                f"No tasks fit within {self.owner.name}'s "
                f"{self.owner.available_minutes} available minutes today."
            )

        total_minutes = sum(task.duration_minutes for _, task in plan)
        lines = [
            f"Daily care plan for {self.owner.name} "
            f"({total_minutes}/{self.owner.available_minutes} min used)",
            "-" * 55,
        ]

        for i, (pet, task) in enumerate(plan, start=1):
            reason = f"priority={task.priority}"
            if task.frequency == "daily":
                reason += ", required daily"
            time_str = f" @{task.scheduled_time}" if task.scheduled_time else ""
            desc_str = f" - {task.description}" if task.description else ""
            lines.append(
                f"{i}. [{pet.name}] {task.title}{time_str} "
                f"({task.duration_minutes} min) [{reason}]{desc_str}"
            )

        # Show tasks that didn't make the cut
        plan_ids = {id(task) for _, task in plan}
        skipped = [(pet, task) for pet, task in self.prioritize_tasks() if id(task) not in plan_ids]
        if skipped:
            lines.append("")
            lines.append("Skipped (not enough time):")
            for pet, task in skipped:
                lines.append(f"  - [{pet.name}] {task.title} ({task.duration_minutes} min)")

        return "\n".join(lines)

    def __repr__(self):
        return f"Scheduler(owner='{self.owner.name}', pets={len(self.owner.pets)})"
