"""
main.py
Testing ground — verifies sorting, filtering, recurring tasks, and conflict detection.
"""

from pawpal_system import Owner, Pet, Task, Scheduler

# ============================================================
# Setup
# ============================================================
jordan = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

jordan.add_pet(mochi)
jordan.add_pet(luna)

# Add tasks OUT OF ORDER intentionally (to prove sort_by_time works)
mochi.add_task(Task("Evening walk",      duration_minutes=25, priority="medium", frequency="daily",   category="walk"))
mochi.add_task(Task("Breakfast feeding", duration_minutes=10, priority="high",   frequency="daily",   category="feeding"))
mochi.add_task(Task("Brush coat",        duration_minutes=15, priority="low",    frequency="weekly",  category="grooming"))
mochi.add_task(Task("Morning walk",      duration_minutes=30, priority="high",   frequency="daily",   category="walk"))

luna.add_task(Task("Breakfast feeding",  duration_minutes=5,  priority="high",   frequency="daily",   category="feeding"))
luna.add_task(Task("Playtime",           duration_minutes=20, priority="medium", frequency="daily",   category="enrichment"))
luna.add_task(Task("Litter box",         duration_minutes=10, priority="medium", frequency="daily",   category="hygiene"))

scheduler = Scheduler(owner=jordan)

# ============================================================
# STEP 2A — Build schedule and print by PRIORITY (default)
# ============================================================
print("=" * 60)
print("  TODAY'S SCHEDULE  (sorted by priority)")
print("=" * 60)
plan = scheduler.build_schedule()
print(scheduler.get_summary(plan))

# ============================================================
# STEP 2B — Sort the same plan by HH:MM start time
# ============================================================
print()
print("=" * 60)
print("  TODAY'S SCHEDULE  (sorted by scheduled time)")
print("=" * 60)
sorted_plan = scheduler.sort_by_time(plan)
for pet, task in sorted_plan:
    print(f"  {task.scheduled_time}  [{pet.name}] {task.title} ({task.duration_minutes} min)")

# ============================================================
# STEP 2C — Filter tasks
# ============================================================
print()
print("=" * 60)
print("  FILTER: all Mochi tasks")
print("=" * 60)
mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")
for pet, task in mochi_tasks:
    status = "done" if task.completed else "pending"
    print(f"  [{pet.name}] {task.title} — {status}")

print()
print("=" * 60)
print("  FILTER: pending tasks only (all pets)")
print("=" * 60)
pending = scheduler.filter_tasks(completed=False)
for pet, task in pending:
    print(f"  [{pet.name}] {task.title}")

# ============================================================
# STEP 3 — Recurring tasks: mark complete, check next occurrence
# ============================================================
print()
print("=" * 60)
print("  RECURRING TASKS — mark complete and auto-schedule next")
print("=" * 60)

ok, msg = scheduler.mark_task_complete("Mochi", "Morning walk")
print(f"  {msg}")

ok, msg = scheduler.mark_task_complete("Luna", "Breakfast feeding")
print(f"  {msg}")

# Show Mochi's task list — should see completed + a new pending occurrence
print()
print("  Mochi's tasks after marking 'Morning walk' complete:")
for t in mochi.tasks:
    print(f"    {t}")

# ============================================================
# STEP 4 — Conflict detection
# ============================================================
print()
print("=" * 60)
print("  CONFLICT DETECTION")
print("=" * 60)

# Force two tasks onto the same start time to trigger a conflict warning
conflict_pet = Pet(name="Buddy", species="dog", age=2)
task_a = Task("Vet appointment", duration_minutes=60, priority="high", frequency="as-needed")
task_b = Task("Bath time",       duration_minutes=30, priority="high", frequency="as-needed")

# Manually assign overlapping times (both start at 09:00)
task_a.scheduled_time = "09:00"
task_b.scheduled_time = "09:00"

conflict_plan = [(conflict_pet, task_a), (conflict_pet, task_b)]

conflicts = scheduler.detect_conflicts(conflict_plan)
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

# Also verify the real plan has no conflicts
real_conflicts = scheduler.detect_conflicts(plan)
print()
print(f"  Conflicts in today's real plan: {len(real_conflicts)} (expected 0)")
print("=" * 60)
