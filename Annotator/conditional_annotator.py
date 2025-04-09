import os
import sys
import csv
from typing import Any, Dict

def read_python_file(file_path: str) -> str:
    """Reads a Python file."""
    try:
        with open(file_path, "r") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def infer_runtime_types(var: Any) -> str:
    """Infers runtime types dynamically."""
    try:
        var_type = type(var)
        if var_type is int:
            return "int"
        elif var_type is float:
            return "float"
        elif var_type is str:
            return "str"
        elif var_type is bool:
            return "bool"
        elif var_type is list:
            element_types = {infer_runtime_types(e) for e in var}
            return f"List[{', '.join(element_types)}]" if element_types else "List[Any]"
        elif var_type is dict:
            key_types = {infer_runtime_types(k) for k in var.keys()}
            value_types = {infer_runtime_types(v) for v in var.values()}
            return f"Dict[{', '.join(key_types)}, {', '.join(value_types)}]" if key_types and value_types else "Dict[Any, Any]"
        elif callable(var):
            return "function"
        return "Any"
    except Exception as e:
        return f"Invalid Type ({str(e)})"

def execute_and_analyze(file_path: str) -> Dict[str, str]:
    """Executes a script and analyzes variable types."""
    global_vars = {}
    try:
        exec(read_python_file(file_path), global_vars)
    except Exception as e:
        print(f"Error executing file: {e}")
        return {}

    return {var: infer_runtime_types(value) for var, value in global_vars.items() if not var.startswith("__")}

def generate_runtime_annotation_report(file_path: str, annotations: Dict[str, str]) -> None:
    """Saves analysis results as a CSV report."""
    report_path = file_path.replace(".py", "_conditional_runtime_annotation_report.csv")
    try:
        with open(report_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Variable Name", "Inferred Type"])
            for var, annotation in annotations.items():
                writer.writerow([var, annotation])
        print(f"Runtime annotation CSV report generated: {report_path}")
    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 conditional_annotator.py <file1.py> <file2.py> ...")
        sys.exit(1)

    for file_path in sys.argv[1:]:
        if os.path.exists(file_path):
            annotations = execute_and_analyze(file_path)
            if annotations:
                generate_runtime_annotation_report(file_path, annotations)
            else:
                print(f"No variables detected for annotation in {file_path}.")
        else:
            print(f"File not found: {file_path}")
