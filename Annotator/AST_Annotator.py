import ast
import os
import sys
import csv
from typing import List, Dict

def infer_type(node):
    """Infers type based on AST nodes."""
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    elif isinstance(node, ast.List):
        element_types = {infer_type(e) for e in node.elts}
        return f"List[{', '.join(element_types)}]"
    elif isinstance(node, ast.Dict):
        key_types = {infer_type(k) for k in node.keys}
        value_types = {infer_type(v) for v in node.values}
        return f"Dict[{', '.join(key_types)} : {', '.join(value_types)}]"
    return 'Unknown'

def analyze_code_for_types(file_path):
    """Analyzes Python file for type hints and returns structured data."""
    try:
        with open(file_path, 'r') as file:
            code = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    tree = ast.parse(code)
    annotations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    type_hint = infer_type(node.value)
                    annotations.append([file_path, target.id, type_hint])
        elif isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if not arg.annotation:
                    annotations.append([file_path, f"{node.name} (arg: {arg.arg})", "Missing Type Hint"])
            if not node.returns:
                annotations.append([file_path, f"{node.name} (return)", "Missing Return Type Hint"])
    return annotations

def generate_report(file_path, annotations):
    """Generates a structured CSV report."""
    report_file = file_path.replace('.py', '_AST_report.csv')
    try:
        with open(report_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["File", "Variable/Function", "Type Hint"])
            writer.writerows(annotations)
        print(f"Annotation report generated at {report_file}")
    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 AST_Annotator.py <file1.py> <file2.py> ...")
        sys.exit(1)

    for file_path in sys.argv[1:]:
        if os.path.exists(file_path):
            annotations = analyze_code_for_types(file_path)
            generate_report(file_path, annotations)
        else:
            print(f"File not found: {file_path}")
