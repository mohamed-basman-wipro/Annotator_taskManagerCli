import sys
import os
import ast
import inspect
import runpy
from types import FrameType
from typing import Any, Union, get_type_hints
from collections import defaultdict

traced_calls: dict[str, dict[str, list[list[Any]]]] = defaultdict(lambda: defaultdict(list))
traced_returns: dict[str, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))

def tracefunc(frame: FrameType, event: str, arg: Any):
    if event not in {"call", "return"}:
        return

    filename = frame.f_code.co_filename
    func_name = frame.f_code.co_name

    if filename.startswith(sys.prefix) or 'site-packages' in filename:
        return

    if not os.path.exists(filename):
        return

    if event == "call":
        args_info = inspect.getargvalues(frame)
        arg_values = [args_info.locals[arg] for arg in args_info.args]
        traced_calls[filename][func_name].append(arg_values)
    elif event == "return":
        traced_returns[filename][func_name].append(arg)

    return tracefunc

sys.setprofile(tracefunc)

# Run target file interactively
input_file = sys.argv[1]
input_basename = os.path.splitext(os.path.basename(input_file))[0]  # <-- Extract name for file output
sys.argv = sys.argv[1:]
runpy.run_path(input_file, run_name="__main__")

sys.setprofile(None)

# ---------- Type Inference Helpers ----------

def merge_types(types: list[str]) -> str:
    types = list(set(types))
    if len(types) == 1:
        return types[0]
    return f"Union[{', '.join(sorted(types))}]"

def infer_type(value: Any) -> str:
    if value is None:
        return "None"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "str"
    elif isinstance(value, list):
        if not value:
            return "list[Any]"
        inner_types = [infer_type(v) for v in value]
        return f"list[{merge_types(inner_types)}]"
    elif isinstance(value, dict):
        if not value:
            return "dict[Any, Any]"
        ktypes = [infer_type(k) for k in value.keys()]
        vtypes = [infer_type(v) for v in value.values()]
        return f"dict[{merge_types(ktypes)}, {merge_types(vtypes)}]"
    return "Any"

def build_signature(func: Any, args_examples: list[list[Any]], return_values: list[Any]) -> str:
    sig = inspect.signature(func)
    params = []

    for i, (name, param) in enumerate(sig.parameters.items()):
        values = [args[i] for args in args_examples if len(args) > i]
        if values:
            param_type = merge_types([infer_type(v) for v in values])
        else:
            param_type = "Any"
        params.append(f"{name}: {param_type}")

    if return_values:
        return_type = merge_types([infer_type(rv) for rv in return_values])
    else:
        return_type = "Any"

    return f"def {func.__name__}({', '.join(params)}) -> {return_type}:", sig

# ---------- Report Generation ----------

out_lines = []

for filepath, functions in traced_calls.items():
    out_lines.append(f"{filepath}:")
    out_lines.append("=" * 42)
    out_lines.append("")

    with open(filepath) as f:
        source = f.read()
        tree = ast.parse(source)

    func_defs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    module_globals = {}
    exec(compile(tree, filepath, "exec"), module_globals)

    for func_name, args_list in functions.items():
        if func_name not in module_globals:
            continue

        func_obj = module_globals[func_name]
        new_sig, old_sig = build_signature(
            func_obj,
            args_list,
            traced_returns[filepath].get(func_name, [])
        )

        old_sig_str = str(old_sig).replace("(<", "(").replace(">)", ")")

        out_lines.append(func_name)
        out_lines.append("")
        out_lines.append("  # Inferred type signature")
        out_lines.append(f"- def {func_name}{old_sig_str}:")
        out_lines.append(f"+ {new_sig}")
        out_lines.append("")

# ---------- Save Report to <inputfilename>_righttyper.out ----------

output_file = f"{input_basename}_righttyper.out"
with open(output_file, "w") as f:
    f.write("\n".join(out_lines))

print(f"[+] All done! Output saved to {output_file}")
