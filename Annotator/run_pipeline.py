# run_pipeline.py

import subprocess

def main():
    print("🚀 Starting annotation pipeline using Taskfile...")
    try:
        subprocess.run(["task", "run_all"], check=True)
    except FileNotFoundError:
        print("❌ Taskfile not found or 'task' CLI tool is not installed.")
    except subprocess.CalledProcessError:
        print("❌ Taskfile execution failed.")
    else:
        print("✅ Annotation pipeline completed successfully!")
