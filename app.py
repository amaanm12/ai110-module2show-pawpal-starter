"""
app.py
PawPal+ Streamlit UI — wired to the logic layer in pawpal_system.py.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# Sidebar — owner settings
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Pet care planning assistant")
    st.divider()

    st.subheader("Owner Settings")

    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="Jordan", available_minutes=120)

    owner: Owner = st.session_state.owner

    new_name = st.text_input("Your name", value=owner.name)
    new_mins = st.number_input(
        "Available minutes today",
        min_value=10, max_value=480,
        value=owner.available_minutes,
        step=10,
    )

    if st.button("Save settings", use_container_width=True):
        owner.name = new_name
        owner.available_minutes = int(new_mins)
        st.success("Settings saved.")

    st.divider()
    st.caption(f"Pets registered: **{len(owner.pets)}**")
    st.caption(f"Total tasks: **{len(owner.get_all_tasks())}**")
    st.caption(f"Pending tasks: **{len(owner.get_all_pending_tasks())}**")

# ===================================================================
# Main area — three tabs
# ===================================================================
tab_pets, tab_tasks, tab_schedule = st.tabs(["Pets", "Tasks", "Today's Schedule"])

# -------------------------------------------------------------------
# TAB 1 — Pets
# -------------------------------------------------------------------
with tab_pets:
    st.header("Your Pets")

    with st.form("add_pet_form", clear_on_submit=True):
        st.subheader("Add a new pet")
        col_name, col_species, col_age = st.columns(3)
        with col_name:
            pet_name = st.text_input("Pet name", placeholder="e.g. Mochi")
        with col_species:
            species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        with col_age:
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        notes = st.text_input("Care notes (optional)", placeholder="e.g. grain-free diet, indoor only")
        submitted = st.form_submit_button("Add pet", use_container_width=True)

    if submitted:
        if not pet_name.strip():
            st.warning("Please enter a pet name.")
        elif owner.get_pet(pet_name.strip()):
            st.warning(f"A pet named **{pet_name}** already exists.")
        else:
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age), notes=notes))
            st.success(f"Added **{pet_name}** the {species}!")

    st.divider()

    if not owner.pets:
        st.info("No pets yet — add one above to get started.")
    else:
        cols = st.columns(min(len(owner.pets), 3))
        for i, pet in enumerate(owner.pets):
            with cols[i % 3]:
                pending = len(pet.get_pending_tasks())
                done    = len(pet.get_completed_tasks())
                st.metric(label=f"{pet.name} ({pet.species})", value=f"{pending} pending", delta=f"{done} done")
                if pet.notes:
                    st.caption(f"Notes: {pet.notes}")

# -------------------------------------------------------------------
# TAB 2 — Tasks
# -------------------------------------------------------------------
with tab_tasks:
    st.header("Manage Tasks")

    if not owner.pets:
        st.info("Add at least one pet in the **Pets** tab before adding tasks.")
    else:
        with st.form("add_task_form", clear_on_submit=True):
            st.subheader("Add a new task")
            col1, col2, col3 = st.columns(3)
            with col1:
                target_pet = st.selectbox("Assign to", [p.name for p in owner.pets])
            with col2:
                task_title = st.text_input("Task title", placeholder="e.g. Morning walk")
            with col3:
                priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

            col4, col5, col6 = st.columns(3)
            with col4:
                duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            with col5:
                frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
            with col6:
                category = st.selectbox(
                    "Category",
                    ["general", "feeding", "walk", "grooming", "medication", "enrichment", "hygiene"],
                )
            description = st.text_input("Description (optional)")
            task_submitted = st.form_submit_button("Add task", use_container_width=True)

        if task_submitted:
            if not task_title.strip():
                st.warning("Please enter a task title.")
            else:
                pet = owner.get_pet(target_pet)
                pet.add_task(Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    description=description,
                    category=category,
                ))
                st.success(f"Added **{task_title}** to {pet.name}.")

        st.divider()

        # ----- Filter controls -----
        st.subheader("All Tasks")
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            filter_pet = st.selectbox(
                "Filter by pet",
                ["All pets"] + [p.name for p in owner.pets],
                key="filter_pet",
            )
        with fcol2:
            filter_status = st.selectbox(
                "Filter by status",
                ["All", "Pending only", "Completed only"],
                key="filter_status",
            )

        # Map UI selections to filter_tasks() arguments
        scheduler = Scheduler(owner=owner)
        pet_filter    = None if filter_pet == "All pets" else filter_pet
        status_filter = None if filter_status == "All" else (filter_status == "Completed only")
        filtered = scheduler.filter_tasks(completed=status_filter, pet_name=pet_filter)

        if not filtered:
            st.info("No tasks match the selected filters.")
        else:
            priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            rows = [
                {
                    "Pet":           pet.name,
                    "Task":          task.title,
                    "Pri":           priority_badge.get(task.priority, "") + " " + task.priority,
                    "Duration (min)": task.duration_minutes,
                    "Frequency":     task.frequency,
                    "Category":      task.category,
                    "Status":        "Done" if task.completed else "Pending",
                    "Due":           str(task.due_date),
                }
                for pet, task in filtered
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(rows)} task(s).")

# -------------------------------------------------------------------
# TAB 3 — Today's Schedule
# -------------------------------------------------------------------
with tab_schedule:
    st.header("Today's Schedule")

    if not owner.get_all_pending_tasks():
        st.info("No pending tasks to schedule. Add tasks in the **Tasks** tab.")
    else:
        sort_order = st.radio(
            "Display order",
            ["By priority (high first)", "By start time (chronological)"],
            horizontal=True,
        )

        if st.button("Generate schedule", type="primary", use_container_width=True):
            scheduler = Scheduler(owner=owner)
            plan = scheduler.build_schedule()

            # Optionally re-sort by time
            display_plan = (
                scheduler.sort_by_time(plan)
                if sort_order == "By start time (chronological)"
                else plan
            )

            # ---- Conflict detection ----
            conflicts = scheduler.detect_conflicts(plan)
            if conflicts:
                st.error(f"**{len(conflicts)} scheduling conflict(s) detected:**")
                for warning in conflicts:
                    st.warning(warning)
            else:
                st.success("No scheduling conflicts detected.")

            st.divider()

            # ---- Schedule table ----
            total_used = sum(t.duration_minutes for _, t in plan)
            time_pct   = int(total_used / owner.available_minutes * 100)

            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("Tasks scheduled", len(plan))
            mcol2.metric("Minutes used",    f"{total_used} / {owner.available_minutes}")
            mcol3.metric("Time utilisation", f"{time_pct}%")

            st.subheader("Scheduled tasks")
            priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            sched_rows = [
                {
                    "Start":          task.scheduled_time,
                    "Pet":            pet.name,
                    "Task":           task.title,
                    "Priority":       priority_badge.get(task.priority, "") + " " + task.priority,
                    "Duration (min)": task.duration_minutes,
                    "Frequency":      task.frequency,
                    "Due":            str(task.due_date),
                }
                for pet, task in display_plan
            ]
            st.dataframe(sched_rows, use_container_width=True, hide_index=True)

            # ---- Skipped tasks ----
            plan_ids  = {id(t) for _, t in plan}
            all_pend  = scheduler.prioritize_tasks()
            skipped   = [(p, t) for p, t in all_pend if id(t) not in plan_ids]
            if skipped:
                st.divider()
                st.subheader("Skipped tasks (not enough time)")
                skip_rows = [
                    {
                        "Pet":            pet.name,
                        "Task":           task.title,
                        "Priority":       priority_badge.get(task.priority, "") + " " + task.priority,
                        "Duration (min)": task.duration_minutes,
                    }
                    for pet, task in skipped
                ]
                st.dataframe(skip_rows, use_container_width=True, hide_index=True)
                st.caption(
                    f"{len(skipped)} task(s) skipped. "
                    f"Increase available minutes in the sidebar to fit more."
                )
