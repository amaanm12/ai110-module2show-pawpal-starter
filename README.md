# PawPal+

**PawPal+** is a pet care planning assistant built with Python and Streamlit.
It helps busy pet owners schedule daily care tasks across multiple pets, respect time constraints, detect scheduling conflicts, and automatically carry recurring tasks forward to the next day.

---

## Features

| Feature | Description |
|---|---|
| Multi-pet support | Register any number of pets with individual task lists |
| Priority scheduling | Tasks are sorted high → low priority; ties broken by duration |
| Time constraints | Only tasks that fit within the owner's available minutes are scheduled |
| HH:MM start times | Every scheduled task gets a real start time beginning at 08:00 |
| Sort by time | View the schedule in chronological order rather than priority order |
| Filter tasks | Filter the task list by pet name, completion status, or both |
| Conflict detection | Warns when two tasks have overlapping time windows |
| Recurring tasks | Completing a daily or weekly task auto-creates the next occurrence |
| Persistent state | Streamlit session state keeps all data alive across button clicks |

---

## Project structure

```
pawpal-starter/
├── app.py               # Streamlit UI (presentation layer)
├── pawpal_system.py     # Backend classes (logic layer)
├── main.py              # Terminal testing script
├── tests/
│   └── test_pawpal.py   # Automated test suite (pytest)
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10 or later
- pip

### Install

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
# or on Windows:
py -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Run the terminal demo

```bash
py main.py
```

---

## How to use the app

The app is organised into three tabs accessible from the top of the page.

### 1 — Pets tab

Add each pet with a name, species, age, and optional care notes.
Registered pets appear as metric cards showing how many tasks are pending vs. done.

### 2 — Tasks tab

Add care tasks to any registered pet.
Each task has a title, priority (`high / medium / low`), duration, frequency (`daily / weekly / as-needed`), category, and optional description.

Use the **Filter by pet** and **Filter by status** dropdowns to narrow the task table.
The table is rendered with `st.dataframe` and includes colour-coded priority badges.

### 3 — Today's Schedule tab

Click **Generate schedule** to run the scheduler.
Choose whether to view results sorted by **priority** or by **chronological start time**.

The output includes:

- **Conflict warnings** — `st.error` / `st.warning` if any two tasks overlap in time
- **Metrics row** — tasks scheduled, minutes used, and time utilisation percentage
- **Schedule table** — every accepted task with its start time, pet, priority, and due date
- **Skipped tasks table** — tasks that didn't fit, with a hint to increase available minutes

---

## Class overview

### `Task`
Represents a single care activity.

| Attribute | Type | Purpose |
|---|---|---|
| `title` | `str` | Short name |
| `duration_minutes` | `int` | How long it takes |
| `priority` | `str` | `"low"` / `"medium"` / `"high"` |
| `frequency` | `str` | `"daily"` / `"weekly"` / `"as-needed"` |
| `completed` | `bool` | Done for this cycle |
| `scheduled_time` | `str` | `"HH:MM"` set by Scheduler |
| `due_date` | `date` | Current occurrence date |

Key methods: `priority_score()`, `mark_complete()`, `reset()`, `next_due_date()`

### `Pet`
Stores pet details and owns a list of `Task` objects.

Key methods: `add_task()`, `remove_task()`, `get_pending_tasks()`, `get_completed_tasks()`, `reset_daily_tasks()`

### `Owner`
Holds available daily minutes and a list of `Pet` objects.

Key methods: `add_pet()`, `get_pet()`, `get_all_tasks()`, `get_all_pending_tasks()`

### `Scheduler`
The scheduling brain. Takes an `Owner` and operates across all their pets.

| Method | What it does |
|---|---|
| `prioritize_tasks()` | Sorts all pending tasks by priority then duration |
| `build_schedule()` | Greedy selection + assigns `HH:MM` start times |
| `sort_by_time(plan)` | Re-orders a plan chronologically using a lambda key on `"HH:MM"` strings |
| `filter_tasks(completed, pet_name)` | Filters all tasks by status and/or pet |
| `detect_conflicts(plan)` | Returns warning strings for any overlapping time windows |
| `mark_task_complete(pet, title)` | Marks task done; auto-creates next occurrence for recurring tasks |
| `get_summary(plan)` | Returns a plain-text schedule summary |

---

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
| `test_sort_by_time_returns_chronological_order` | `sort_by_time()` returns tasks in ascending `HH:MM` order |
| `test_marking_daily_task_complete_creates_next_occurrence` | Completing a daily task auto-creates a new pending task with `due_date = today + 1` |
| `test_detect_conflicts_flags_overlapping_tasks` | `detect_conflicts()` warns on overlapping windows; silent for back-to-back tasks |

### Confidence level

**4 / 5 stars**

Core scheduling logic — priority ordering, time assignment, recurrence, and conflict detection — is fully covered by tests.
One star is held back because edge cases (zero available minutes, task duration exceeding total budget, weekly recurrence spanning month boundaries) are not yet tested.


