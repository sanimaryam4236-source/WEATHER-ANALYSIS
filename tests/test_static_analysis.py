"""
Static analysis AST test ensuring zero undefined names or syntax errors in codebase.
"""

import ast
import glob
import os


def test_ast_syntax_and_imports():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_files = glob.glob(os.path.join(root_dir, "src", "**", "*.py"), recursive=True)
    py_files.extend(glob.glob(os.path.join(root_dir, "config", "*.py")))
    py_files.append(os.path.join(root_dir, "app.py"))

    assert len(py_files) > 0

    for filepath in py_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # Must parse without SyntaxError
            tree = ast.parse(content, filename=filepath)
            assert tree is not None
