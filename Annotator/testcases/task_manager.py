# task_manager.py

import json
import os
from datetime import datetime
from typing import Any

TASKS_FILE = "tasks.json"

# Load tasks from file
def load_tasks() -> Any:
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as file:
            return json.load(file)
    return []

# Save tasks to file
def save_tasks(tasks) -> None:
    with open(TASKS_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

# Add a new task
def add_task(description, due_date, category) -> str:
    tasks = load_tasks()
    new_task = {
        "id": len(tasks) + 1,
        "description": description,
        "due_date": due_date,
        "category": category
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return "\nTask added successfully!"

# List tasks sorted by due date
def list_tasks() -> str:
    tasks = load_tasks()
    if not tasks:
        return "\nNo tasks found."
    
    tasks.sort(key=lambda x: datetime.strptime(x["due_date"], "%Y-%m-%d"))
    
    table = [[task["id"], task["description"], task["due_date"], task["category"]] for task in tasks]
    return table

# Flush a specific task by ID
def flush_task(task_id) -> str:
    tasks = load_tasks()
    tasks = [task for task in tasks if task["id"] != task_id]
    
    for i, task in enumerate(tasks):
        task["id"] = i + 1

    save_tasks(tasks)
    return "\nTask removed successfully!"

# Flush all tasks from the database
def flush_all_tasks() -> str:
    tasks = load_tasks()
    if not tasks:
        return "\nNo tasks found to delete."
    
    return "This will delete all tasks from the database. Do you want to proceed? (Yes/No)"

# Delete all tasks
def delete_all_tasks() -> str:
    save_tasks([])
    return "All tasks successfully deleted."
