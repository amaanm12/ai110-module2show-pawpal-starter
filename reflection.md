# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML design included four classes:

- **Task** — responsible for holding all data about a single care activity: its title, duration, priority, and completion status. It had no knowledge of pets or owners; it was a pure data object with a few state-change methods (`mark_complete`, `reset`).
- **Pet** — responsible for storing a pet's identity (name, species, age, notes) and owning a list of `Task` objects. It handled all task-level operations that were scoped to one pet (add, remove, filter by status).
- **Owner** — responsible for registering pets and providing a unified cross-pet view of all tasks. It held the "available minutes" constraint and was the single entry point for the scheduler.
- **Scheduler** — responsible for all scheduling intelligence: retrieving tasks, sorting by priority, building the daily plan, and returning results. It depended on `Owner` but had no direct coupling to `Pet` or `Task` internals.

A fifth class, `Schedule`, was sketched as a container for the ordered plan, but it was removed early (see 1b).

**b. Design changes**

Yes, the design changed in two notable ways.

First, the `Schedule` class was removed. Initially it was meant to hold the ordered list of tasks and an `is_feasible()` method. During implementation it became clear that this was unnecessary indirection — the `Scheduler` itself could return a plain `list[tuple[Pet, Task]]` and that was both simpler and more flexible (e.g., it could be re-sorted without creating a new object). Removing it reduced the class count from five to four without losing any functionality.

Second, `Task` grew three new attributes (`scheduled_time`, `due_date`, `frequency`) that were not in the original sketch. `scheduled_time` was needed so the UI could display a real `HH:MM` start time rather than just a position in a list. `due_date` and `frequency` were needed to support recurring task creation. These were additive changes that didn't break the original interface.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints:

1. **Time** — the owner's `available_minutes` acts as a hard budget. No task is added to the plan if it would exceed the remaining time.
2. **Priority** — tasks are ranked `high > medium > low`. Within the same priority level, shorter tasks are preferred (they act as a tiebreaker, maximising the number of tasks that fit).

Priority was treated as the dominant constraint because the scenario describes a "busy owner" who needs to guarantee that high-importance tasks (medication, feeding) always happen — time can be tight, but critical care should never be skipped simply because a low-priority grooming task was scheduled first.

**b. Tradeoffs**

The scheduler uses a **greedy algorithm**: it picks the highest-priority task first and keeps going until time runs out. This is simple and fast, but it is not globally optimal. For example, if the budget is 30 minutes and there is one high-priority 25-minute task and two medium-priority 15-minute tasks, the greedy approach picks the 25-minute task (leaving only 5 minutes, so no more tasks fit) instead of the two 15-minute tasks (which would use all 30 minutes and complete two items).

This tradeoff is reasonable for the pet care scenario because the whole point of the priority system is that a high-priority task *should* displace lower-priority ones. An owner who marks "give medication" as high priority genuinely wants it to happen even if it costs them a grooming slot. A globally optimal packing algorithm would undermine that intent.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used at every stage of the project:

- **Design** — brainstorming the initial class responsibilities and deciding where the `Schedule` class added value versus unnecessary complexity.
- **Implementation** — generating method stubs, filling in logic for `sort_by_time` (using a lambda key on `"HH:MM"` strings), `detect_conflicts` (the pairwise overlap condition `s1 < e2 and s2 < e1`), and the `timedelta`-based recurrence logic.
- **UI wiring** — translating `Scheduler` method calls into `st.dataframe`, `st.metric`, and `st.success/warning/error` components.
- **Testing** — drafting test cases that covered both the happy path and a non-obvious edge (back-to-back tasks should *not* be flagged as a conflict).

The most helpful prompts were specific and scoped: "implement `detect_conflicts` so it returns warning strings rather than raising exceptions" produced cleaner output than vague prompts like "add conflict detection." Asking AI to explain *why* it chose a particular approach (e.g., why lexicographic comparison works for zero-padded `HH:MM` strings) was also valuable.

**b. Judgment and verification**

When AI first suggested the `detect_conflicts` overlap condition, it used `s1 <= e2 and s2 <= e1`. I changed `<=` to `<` because two tasks that share only an endpoint (one ends at 09:00, the next starts at 09:00) are back-to-back, not overlapping — a real schedule works exactly like that.

I verified this by writing the `test_detect_conflicts_flags_overlapping_tasks` test with an explicit back-to-back case (`"08:00"` + 30 min, then `"08:30"` + 30 min) and confirming that zero warnings were returned. If I had accepted the `<=` version, that test would have flagged a false conflict for every consecutive pair of tasks in the daily plan.

---

## 4. Testing and Verification

**a. What you tested**

Five behaviors were tested:

1. **Task completion** — `mark_complete()` flips `completed` from `False` to `True`. Tested because this is the most fundamental state change in the system; if it breaks, nothing else works.
2. **Task addition** — `add_task()` grows the pet's task list by exactly one. Tested because the UI and scheduler both depend on tasks persisting inside `Pet`.
3. **Sorting correctness** — after `build_schedule()` assigns times and `sort_by_time()` reorders the plan, each task's `scheduled_time` must be `<=` the next. Tested because the "chronological view" in the UI is meaningless if the sort is wrong.
4. **Recurrence logic** — completing a daily task must produce a new pending task with `due_date = today + 1`. Tested because this is the most complex side effect in the system and silently failing would cause tasks to disappear permanently.
5. **Conflict detection** — overlapping windows produce a warning; back-to-back windows do not. Tested as both a positive and negative case to prevent both false negatives and false positives.

**b. Confidence**

Confidence: **4 / 5**. The core scheduling loop works correctly across all tested scenarios. The remaining uncertainty is around untested edge cases:

- An owner with fewer available minutes than any single task (the plan would be empty — is that communicated clearly to the user?).
- A weekly task completed near the end of a month — `due_date + timedelta(weeks=1)` crosses a month boundary correctly because `timedelta` handles that, but it has not been explicitly tested.
- Two pets with tasks that together exactly fill `available_minutes` — the greedy algorithm should handle this, but it has not been tested with a tight-fit scenario.

---

## 5. Reflection

**a. What went well**

The separation between the logic layer (`pawpal_system.py`) and the UI layer (`app.py`) worked very well. Because `Scheduler` returned plain Python lists and the `Owner`/`Pet`/`Task` objects had no Streamlit imports, it was straightforward to test the backend in isolation and then wire it to the UI independently. The same `Scheduler.build_schedule()` call powers both `main.py` (terminal output) and `app.py` (interactive table) without any duplication.

**b. What you would improve**

The main thing to improve would be giving tasks explicit `start_time` inputs in the UI rather than always starting the schedule at 08:00 AM. Real pet care doesn't all happen in one block — a dog might need a walk at 07:00, medication at 12:00, and feeding at 18:00. Supporting fixed-time constraints would make the conflict detection genuinely useful rather than a demonstration feature.

A second improvement would be persistent storage (a JSON file or a small SQLite database) so that the schedule survives closing the browser tab.

**c. Key takeaway**

The most important thing learned was that **AI is most useful when you already have a clear mental model of what you want**. When a prompt was vague ("add sorting"), the AI produced something that worked but didn't fit the design (it sorted in place rather than returning a new list). When the prompt was precise ("implement `sort_by_time(plan)` that takes a list of `(Pet, Task)` tuples and returns them sorted by `task.scheduled_time` using a lambda key — tasks without a time should sort to the end"), the output was correct, well-named, and needed no changes. Investing time in design before opening a chat window consistently produced better results than trying to use AI to figure out the design.
