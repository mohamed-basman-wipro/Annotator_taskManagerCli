import os
import csv
import re

ROOT = "."
TESTCASES = "testcases"
FINAL_REPORT = "combined_final_report.csv"

def collect_files():
    files = {
        "righttyper": [],
        "variable": None,
        "ast": [],
        "conditional": [],
    }

    for folder in [ROOT, TESTCASES]:
        for fname in os.listdir(folder):
            path = os.path.join(folder, fname)
            if fname.endswith("_righttyper.out"):
                files["righttyper"].append(path)
            elif fname == "variable_annotation_report.txt":
                files["variable"] = path
            elif fname.endswith("_AST_report.csv"):
                files["ast"].append(path)
            elif fname.endswith("_conditional_runtime_annotation_report.csv"):
                files["conditional"].append(path)
    return files

def parse_variable_report(path):
    if not path: return []
    rows = []
    with open(path) as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) != 4:
                continue
            fullpath, func, var, vtype = parts
            module = os.path.basename(fullpath)
            rows.append((module, func, "-", "-", "-", "Variable_Annotator", var, vtype))
    return rows

def parse_csv_report(path, label):
    rows = []
    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader, [])
        for row in reader:
            if label == "AST":
                file, var_func, vtype = row
                module = os.path.basename(file)
                # Check if it’s a function argument type
                if "(arg:" in var_func:
                    func, arg = re.findall(r"(\w+)\s*\(arg:\s*(\w+)\)", var_func)[0]
                    rows.append((module, func, "-", arg, vtype, "AST", "-", "-"))
                else:
                    rows.append((module, "-", "-", "-", "-", "AST", var_func, vtype))
            elif label == "Conditional":
                var_name, inferred_type = row
                module = os.path.basename(path).replace("_conditional_runtime_annotation_report.csv", ".py")
                rows.append((module, var_name if var_name not in ("json", "os", "datetime", "Any", "TASKS_FILE") else "-", "-", "-", "-", "Conditional", var_name, inferred_type))
    return rows

def parse_righttyper(path):
    results = []
    current_module = os.path.basename(path).replace("_righttyper.out", ".py")
    current_function = ""
    return_type = ""
    params = []

    with open(path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("- def "):
            func_match = re.match(r"- def (\w+)\((.*?)\)(?: -> (.*))?:", line)
            if func_match:
                current_function = func_match.group(1)
                args = func_match.group(2)
                return_type = func_match.group(3) or "-"
                params = [p.strip() for p in args.split(",") if p.strip()]
        elif line.startswith("+ def "):
            annot_match = re.match(r"\+ def (\w+)\((.*?)\) -> (.+):", line)
            if annot_match:
                current_function = annot_match.group(1)
                args = annot_match.group(2)
                return_type = annot_match.group(3)
                args = [a.strip() for a in args.split(",") if a.strip()]
                for a in args:
                    if ": " in a:
                        var, vtype = a.split(": ")
                        results.append((
                            current_module,
                            current_function,
                            "-",
                            var,
                            vtype,
                            "RightTyper",
                            "-",
                            "-"
                        ))
                results.append((
                    current_module,
                    current_function,
                    return_type,
                    "-",
                    "-",
                    "RightTyper",
                    "-",
                    "-"
                ))
    return results

def generate_combined_report():
    files = collect_files()
    final_rows = []

    for path in files["righttyper"]:
        final_rows.extend(parse_righttyper(path))

    final_rows.extend(parse_variable_report(files["variable"]))

    for path in files["ast"]:
        final_rows.extend(parse_csv_report(path, "AST"))

    for path in files["conditional"]:
        final_rows.extend(parse_csv_report(path, "Conditional"))

    with open(FINAL_REPORT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "SL_No",
            "Module",
            "Function",
            "Function_Return_Type",
            "Function_Arguments",
            "Function_Argument_Type",
            "Annotator_Type",
            "Variable_Name",
            "Variable_Type"
        ])
        for i, row in enumerate(final_rows, start=1):
            writer.writerow([i] + list(row))

    print(f"[+] Final report generated: {FINAL_REPORT}")

if __name__ == "__main__":
    generate_combined_report()
