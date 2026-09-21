"""Commands whose tests assert the did-not-run exit (3) somewhere.

Reads the TESTS, not the source: the claim is "a command that decided nothing
exits 3", and a test asserting it is the only evidence anybody watched it.
"""
import ast, pathlib

MOD_TO_CMD = {"distinct": "distinct", "population": "population", "ran": "ran", "census": "census",
              "escapes": "escapes", "scans": "scans", "shapes": "shapes", "gap": "gap",
              "report": "report", "nightly": "nightly", "mutate": "mutate", "requirements": "questions"}
out = set()
for f in sorted(pathlib.Path("tests").glob("test_*.py")):
    text = f.read_text(encoding="utf-8")
    if "== 3" not in text:
        continue
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("qabench"):
            for a in node.names:
                if a.name in MOD_TO_CMD:
                    out.add(MOD_TO_CMD[a.name])
        if isinstance(node, ast.Import):
            for a in node.names:
                tail = a.name.split(".")[-1]
                if a.name.startswith("qabench") and tail in MOD_TO_CMD:
                    out.add(MOD_TO_CMD[tail])
for c in sorted(out):
    print(c)
