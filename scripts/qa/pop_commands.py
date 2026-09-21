"""Every command `python -m qabench` dispatches, from the dispatch itself.

AST, not a grep of the help text: the help text is a recorded conclusion and
this repo's own ledger carries the day it was wrong.
"""
import ast, pathlib, sys

tree = ast.parse(pathlib.Path("qabench/__main__.py").read_text(encoding="utf-8"))
out = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "cmd":
        for c in node.comparators:
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                out.add(c.value)
    if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "name":
        for c in node.comparators:                      # `stage <name>` sub-dispatch
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                out.add("stage " + c.value)
for c in sorted(out):
    print(c)
