import ast
import sys
import os
import csv

class VariableTypeInferer(ast.NodeVisitor):
    def __init__(self):
        self.variable_types = {}       # mapping: (filename, function or 'global', variable) -> type string
        self.function_returns = {}     # mapping: function name -> inferred return type
        self.current_function = None
        self.current_function_return_types = []
        self.current_scope = 'global'

    def visit_Assign(self, node):
        value_type = self.infer_type(node.value)
        for target in node.targets:
            self.handle_assignment_target(target, value_type)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            annotated_type = self.get_annotation_type(node.annotation)
            if annotated_type:
                self.variable_types[(self.filename, self.current_scope, node.target.id)] = annotated_type
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.current_scope = node.name
        for arg in node.args.args:
            inferred = self.get_annotation_type(arg.annotation)
            if not inferred:
                inferred = self.infer_type_from_usage(node.body, arg.arg)
            if not inferred:
                inferred = "function_param"
            self.variable_types[(self.filename, node.name, arg.arg)] = inferred

        self.current_function_return_types = []
        self.generic_visit(node)

        if self.current_function_return_types:
            preferred = next((t for t in self.current_function_return_types if t in ("dict", "list")), self.current_function_return_types[0])
            self.function_returns[node.name] = preferred
        self.current_function = None
        self.current_scope = 'global'
        self.current_function_return_types = []

    def visit_Return(self, node):
        if self.current_function is not None:
            inferred = self.infer_type(node.value)
            self.current_function_return_types.append(inferred)

    def visit_For(self, node):
        if (isinstance(node.iter, ast.Call) and 
            self.get_func_name(node.iter.func) == "enumerate" and
            isinstance(node.target, ast.Tuple) and len(node.target.elts) == 2):
            index_var, item_var = node.target.elts
            if isinstance(index_var, ast.Name):
                self.variable_types[(self.filename, self.current_scope, index_var.id)] = "int"
            if isinstance(item_var, ast.Name):
                iter_arg = node.iter.args[0]
                if isinstance(iter_arg, ast.Name):
                    list_type = self.get_type_by_name(iter_arg.id)
                    if list_type == "list":
                        self.variable_types[(self.filename, self.current_scope, item_var.id)] = "dict"
                    elif list_type.startswith("list["):
                        self.variable_types[(self.filename, self.current_scope, item_var.id)] = list_type[5:-1]
                    else:
                        self.variable_types[(self.filename, self.current_scope, item_var.id)] = "Unknown"
        else:
            if isinstance(node.target, ast.Name):
                self.variable_types[(self.filename, self.current_scope, node.target.id)] = "Unknown"
            elif isinstance(node.target, ast.Tuple):
                for elt in node.target.elts:
                    if isinstance(elt, ast.Name):
                        self.variable_types[(self.filename, self.current_scope, elt.id)] = "Unknown"
        self.generic_visit(node)

    def handle_assignment_target(self, target, value_type):
        if isinstance(target, ast.Name):
            self.variable_types[(self.filename, self.current_scope, target.id)] = value_type
        elif isinstance(target, ast.Tuple):
            for elt in target.elts:
                if isinstance(elt, ast.Name):
                    self.variable_types[(self.filename, self.current_scope, elt.id)] = "Unknown"

    def get_annotation_type(self, annotation_node):
        if isinstance(annotation_node, ast.Name):
            return annotation_node.id
        elif isinstance(annotation_node, ast.Subscript):
            if isinstance(annotation_node.value, ast.Name):
                return f"{annotation_node.value.id}[?]"
            elif isinstance(annotation_node.value, ast.Attribute):
                return f"{annotation_node.value.attr}[?]"
        elif isinstance(annotation_node, ast.Attribute):
            return annotation_node.attr
        return None

    def infer_type(self, value):
        if isinstance(value, ast.Constant):
            if isinstance(value.value, str): return "str"
            if isinstance(value.value, int): return "int"
            if isinstance(value.value, float): return "float"
            if isinstance(value.value, bool): return "bool"
            return type(value.value).__name__
        if isinstance(value, ast.Str): return "str"
        if isinstance(value, ast.Num): return "int"
        if isinstance(value, ast.List): return "list"
        if isinstance(value, ast.Dict): return "dict"
        if isinstance(value, ast.Call):
            func_name = self.get_func_name(value.func)
            if func_name in self.function_returns:
                return self.function_returns[func_name]
            if func_name in ("input",): return "str"
            if func_name in ("int", "float", "str", "list", "dict"): return func_name
            return "function_call"
        if isinstance(value, ast.BinOp):
            return self.infer_type(value.left)
        if isinstance(value, ast.ListComp):
            return "list"
        return "Unknown"

    def get_func_name(self, func_node):
        if isinstance(func_node, ast.Name): return func_node.id
        if isinstance(func_node, ast.Attribute): return func_node.attr
        return "Unknown"

    def get_type_by_name(self, var_name):
        return self.variable_types.get((self.filename, self.current_scope, var_name), "Unknown")

    def infer_type_from_usage(self, body, var_name):
        for stmt in ast.walk(ast.Module(body=body)):
            if isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Name) and stmt.value.id == var_name:
                    return self.get_type_by_name(var_name)
                if isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == var_name:
                    return self.infer_type(stmt.value)
            elif isinstance(stmt, ast.Call):
                for arg in stmt.args:
                    if isinstance(arg, ast.Name) and arg.id == var_name:
                        inferred = self.infer_type(arg)
                        if inferred != "Unknown":
                            return inferred
        return None

    def analyze_file(self, filename):
        self.filename = filename
        with open(filename, "r") as f:
            source = f.read()
        tree = ast.parse(source, filename=filename)
        self.visit(tree)


def write_report(variable_types):
    with open("variable_annotation_report.txt", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Function", "Variable Name", "Inferred Type"])
        for (fname, func, var), vartype in sorted(variable_types.items()):
            writer.writerow([fname, func, var, vartype])


def main():
    files = sys.argv[1:]
    inferer = VariableTypeInferer()
    for file in files:
        if not os.path.isfile(file):
            print(f"[ERROR] File not found: {file}")
            continue
        inferer.analyze_file(file)

    for (fname, func, var), vartype in inferer.variable_types.items():
        print(f"[DEBUG] {fname} | {func} | {var} -> {vartype}")

    write_report(inferer.variable_types)


if __name__ == "__main__":
    main()
