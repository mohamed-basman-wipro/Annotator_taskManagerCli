# cli.py

from task_manager import add_task, list_tasks, flush_task, flush_all_tasks, delete_all_tasks
from tabulate import tabulate  # <-- Add this import statement to fix the error

def main() -> None:
    while True:
        print("\nTask Manager CLI")
        print("1. Add Task")
        print("2. List Tasks")
        print("3. Flush Task")
        print("4. Exit")
        
        choice = input("\nChoose an option: ")

        if choice == "1":
            description = input("Enter task description: ")
            due_date = input("Enter due date (YYYY-MM-DD): ")
            category = input("Enter category: ")
            print(add_task(description, due_date, category))
        elif choice == "2":
            tasks_table = list_tasks()
            if isinstance(tasks_table, list):
                print("\nTask Manager Dashboard\n")
                print(tabulate(tasks_table, headers=["ID", "Task", "Due Date", "Category"], tablefmt="grid"))
            else:
                print(tasks_table)  # No tasks message
        elif choice == "3":
            print("\nFlush Task Options")
            print("1. Flush a specific task by ID")
            print("2. Flush all tasks")
            sub_choice = input("Choose an option: ")

            if sub_choice == "1":
                task_id = int(input("Enter task ID to flush: "))
                print(flush_task(task_id))
            elif sub_choice == "2":
                print(flush_all_tasks())
                proceed = input()
                if proceed.strip().lower() == 'yes':
                    print(delete_all_tasks())
                else:
                    print("\nNo tasks were deleted.")
            else:
                print("\nInvalid option, please try again.")
        elif choice == "4":
            print("\nExiting Task Manager. Goodbye!")
            break
        else:
            print("\nInvalid option, please try again.")

if __name__ == "__main__":
    main()
