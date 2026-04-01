"""
app.py
PawPal+ Streamlit UI — wired to the logic layer in pawpal_system.py.
"""

# Step 1: Import classes from the logic layer
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ------------------------------------------------------------------
# Step 2: Manage application "memory" with st.session_state
#
# Streamlit reruns the whole script on every interaction.
# We store the Owner object in session_state so it survives reruns.
# The "owner" key is checked first — if it already exists we reuse it;
# otherwise we create a fresh Owner with sensible defaults.
# ------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

# Convenience alias so the rest of the code is readable
owner: Owner = st.session_state.owner

# ------------------------------------------------------------------
# Section: Owner setup
# ------------------------------------------------------------------
st.header("Owner Settings")

col_name, col_time = st.columns(2)
with col_name:
    new_name = st.text_input("Owner name", value=owner.name)
with col_time:
    new_mins = st.number_input(
        "Available minutes today", min_value=10, max_value=480, value=owner.available_minutes, step=10
    )

if st.button("Update owner"):
    owner.name = new_name
    owner.available_minutes = new_mins
    st.success(f"Owner updated: {owner.name} ({owner.available_minutes} min available)")

st.divider()

# ------------------------------------------------------------------
# Section: Add a Pet
# Step 3 (Pet): form submission calls pet.add_pet() on the owner object
# stored in session_state, so the pet persists across reruns.
# ------------------------------------------------------------------
st.header("Add a Pet")

col_pet, col_species, col_age = st.columns(3)
with col_pet:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_species:
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
with col_age:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

notes = st.text_input("Care notes (optional)", value="")

if st.button("Add pet"):
    # Guard: don't allow duplicate pet names
    if owner.get_pet(pet_name):
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        new_pet = Pet(name=pet_name, species=species, age=int(age), notes=notes)
        owner.add_pet(new_pet)          # <-- calls Owner.add_pet() from pawpal_system.py
        st.success(f"Added {new_pet.name} the {species}!")

# Show current pets
if owner.pets:
    st.markdown("**Current pets:**")
    for pet in owner.pets:
        note_text = f" — {pet.notes}" if pet.notes else ""
        st.write(f"- **{pet.name}** ({pet.species}, age {pet.age}){note_text}")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ------------------------------------------------------------------
# Section: Add a Task to a Pet
# Step 3 (Task): form submission calls pet.add_task() so the Task
# object lives inside the Pet, which lives inside the Owner in session_state.
# ------------------------------------------------------------------
st.header("Add a Task")

if not owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]

    col1, col2, col3 = st.columns(3)
    with col1:
        target_pet = st.selectbox("Assign to pet", pet_names)
    with col2:
        task_title = st.text_input("Task title", value="Morning walk")
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
    with col6:
        category = st.selectbox(
            "Category", ["general", "feeding", "walk", "grooming", "medication", "enrichment", "hygiene"]
        )

    description = st.text_input("Description (optional)", value="")

    if st.button("Add task"):
        pet = owner.get_pet(target_pet)
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            description=description,
            category=category,
        )
        pet.add_task(new_task)          # <-- calls Pet.add_task() from pawpal_system.py
        st.success(f"Added '{task_title}' to {pet.name}.")

    # Show all current tasks grouped by pet
    all_pairs = owner.get_all_tasks()
    if all_pairs:
        st.markdown("**All tasks:**")
        rows = [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Done": task.completed,
            }
            for pet, task in all_pairs
        ]
        st.table(rows)
    else:
        st.info("No tasks yet.")

st.divider()

# ------------------------------------------------------------------
# Section: Build Schedule
# Calls Scheduler.build_schedule() and displays get_summary() output.
# ------------------------------------------------------------------
st.header("Build Today's Schedule")

if st.button("Generate schedule"):
    all_pending = owner.get_all_pending_tasks()
    if not all_pending:
        st.warning("No pending tasks to schedule. Add tasks above.")
    else:
        scheduler = Scheduler(owner=owner)   # <-- Scheduler from pawpal_system.py
        plan = scheduler.build_schedule()
        summary = scheduler.get_summary(plan)
        st.success("Schedule generated!")
        st.code(summary, language=None)

        # Mark scheduled tasks complete
        if st.session_state.get("auto_mark_complete"):
            for pet, task in plan:
                task.mark_complete()
