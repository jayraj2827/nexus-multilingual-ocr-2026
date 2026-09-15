"""
Python 3.10.11 Compatibility Static Verification Tests.
Scans all codebase files using AST to ensure no Python 3.11+ syntax or standard library imports are introduced.
"""

import ast
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent

# Files and directories to inspect
SOURCE_DIRS = [ROOT_DIR / "nexusocr", ROOT_DIR / "engine"]
SOURCE_FILES = [ROOT_DIR / "config.py", ROOT_DIR / "pipeline.py", ROOT_DIR / "app.py"]

PYTHON_311_FORBIDDEN_AST_NODES = [
    "TryStar",          # except* (Python 3.11+)
    "TypeAlias",        # type statement (Python 3.12+)
    "TypeVar",          # type param in AST (Python 3.12+)
    "TypeVarTuple",     # type param in AST (Python 3.12+)
    "ParamSpec",        # type param in AST (Python 3.12+)
]

PYTHON_311_NEW_STDLIB = {
    "tomllib",          # Python 3.11+
    "wsgiref.types",    # Python 3.11+
}


def get_all_python_files():
    files = list(SOURCE_FILES)
    for d in SOURCE_DIRS:
        if d.exists():
            files.extend(d.glob("**/*.py"))
    return [f for f in files if f.exists()]


def test_python_310_compatibility_ast():
    """Parses each python source file and validates AST against 3.11+ constructs."""
    py_files = get_all_python_files()
    assert len(py_files) > 0, "No python files found for compatibility inspection"

    violations = []

    for file_path in py_files:
        content = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as err:
            violations.append(f"Syntax error in {file_path}: {err}")
            continue

        for node in ast.walk(tree):
            node_type = type(node).__name__
            if node_type in PYTHON_311_FORBIDDEN_AST_NODES:
                violations.append(f"{file_path.name}:{getattr(node, 'lineno', 0)} uses Python 3.11+ node '{node_type}'")

            # Check imports for 3.11-only stdlib
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in PYTHON_311_NEW_STDLIB:
                        violations.append(f"{file_path.name}:{node.lineno} imports Python 3.11+ stdlib '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module in PYTHON_311_NEW_STDLIB:
                    violations.append(f"{file_path.name}:{node.lineno} imports from Python 3.11+ stdlib '{node.module}'")

    assert not violations, "Python 3.10.11 compatibility violations found:\n" + "\n".join(violations)
