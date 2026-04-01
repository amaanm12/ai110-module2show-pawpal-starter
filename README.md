# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

### Run the test suite

```bash
py -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Test | What it verifies |
|---|---|
| `test_mark_complete_changes_status` | `Task.mark_complete()` flips `completed` from `False` to `True` |
| `test_add_task_increases_pet_task_count` | `Pet.add_task()` grows the task list by exactly one |
| `test_sort_by_time_returns_chronological_order` | `Scheduler.sort_by_time()` returns tasks in ascending `HH:MM` order after `build_schedule()` assigns start times |
| `test_marking_daily_task_complete_creates_next_occurrence` | Completing a daily task auto-creates a new pending task with `due_date = today + 1 day` |
| `test_detect_conflicts_flags_overlapping_tasks` | `Scheduler.detect_conflicts()` returns a warning for overlapping windows and no warning for back-to-back tasks |

### Confidence level

**4 / 5 stars**

The core scheduling logic — priority ordering, time assignment, recurrence, and conflict detection — is fully covered. One star is held back because edge cases like an owner with zero available minutes, tasks whose duration exceeds the total budget, or weekly recurrence spanning month boundaries are not yet tested.
