"""
AI-Specific Quality Metrics
Catches defects unique to AI-generated code that traditional metrics miss.
1. Dead code detection (vulture)
2. Hallucinated import detection (importlib)
3. Code duplication detection (AST)
"""
import subprocess
import json
import ast
import sys


def measure_dead_code(code_file):
    """Detect unreachable/unused code using vulture."""
    try:
        result = subprocess.run(
            ["vulture", code_file, "--min-confidence", "80"],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        issues = []
        for line in lines:
            if line.strip():
                issues.append(line.strip())
        return {
            "metric": "dead_code",
            "total": len(issues),
            "details": issues[:10],
        }
    except Exception as e:
        return {"metric": "dead_code", "total": 0, "error": str(e)}


def measure_hallucinated_imports(code_file):
    """Check if any imports reference modules that do not exist."""
    with open(code_file, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"metric": "hallucinated_imports", "total": 0, "error": "syntax error"}

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])

    # Remove duplicates
    imports = list(set(imports))

    # Check each import
    hallucinated = []
    valid = []
    # Standard library modules that are always available
    stdlib = {
        "os", "sys", "json", "re", "math", "random", "datetime", "time",
        "collections", "itertools", "functools", "typing", "pathlib",
        "subprocess", "shutil", "tempfile", "io", "string", "copy",
        "ast", "abc", "enum", "dataclasses", "contextlib", "operator",
        "hashlib", "hmac", "secrets", "base64", "struct", "pickle",
        "sqlite3", "csv", "xml", "html", "urllib", "http", "email",
        "logging", "unittest", "doctest", "argparse", "configparser",
        "threading", "multiprocessing", "socket", "ssl", "signal",
        "statistics", "decimal", "fractions", "bisect", "heapq",
        "array", "queue", "weakref", "types", "inspect", "dis",
        "pdb", "traceback", "warnings", "textwrap", "difflib",
        "glob", "fnmatch", "linecache", "tokenize", "pprint",
        "numbers", "cmath", "array",
    }

    for imp in imports:
        if imp in stdlib:
            valid.append(imp)
            continue
        # Try to find the module
        check = subprocess.run(
            [sys.executable, "-c", f"import {imp}"],
            capture_output=True, text=True, timeout=5
        )
        if check.returncode == 0:
            valid.append(imp)
        else:
            hallucinated.append(imp)

    return {
        "metric": "hallucinated_imports",
        "total": len(hallucinated),
        "hallucinated": hallucinated,
        "valid": valid,
        "all_imports": imports,
    }


def measure_code_duplication(code_file):
    """Detect duplicated function definitions (AI often repeats functions)."""
    with open(code_file, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"metric": "code_duplication", "total": 0, "error": "syntax error"}

    # Find all function definitions
    functions = {}
    duplicates = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if name in functions:
                functions[name] += 1
                duplicates.append({
                    "function": name,
                    "count": functions[name],
                    "line": node.lineno,
                })
            else:
                functions[name] = 1

    # Also check for duplicate code blocks (simple line-based check)
    lines = source.split("\n")
    non_empty = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]

    # Find repeated consecutive blocks (3+ lines)
    repeated_blocks = 0
    for i in range(len(non_empty) - 3):
        block = non_empty[i:i+3]
        for j in range(i + 3, len(non_empty) - 3):
            if non_empty[j:j+3] == block:
                repeated_blocks += 1
                break

    return {
        "metric": "code_duplication",
        "duplicate_functions": len(duplicates),
        "duplicate_function_details": duplicates,
        "repeated_blocks": repeated_blocks,
        "total": len(duplicates) + repeated_blocks,
        "all_functions": {k: v for k, v in functions.items()},
    }


def run_all_ai_metrics(code_file):
    """Run all 3 AI-specific metrics."""
    return {
        "dead_code": measure_dead_code(code_file),
        "hallucinated_imports": measure_hallucinated_imports(code_file),
        "code_duplication": measure_code_duplication(code_file),
    }
