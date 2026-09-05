from app.core.scanner import ProjectStore, Scanner
from app.core import fixer as fixer_mod
from app.core.linters import lint_file
from app.models.schemas import Bug

# Minimal Python file: only an unused import (F401), fixable by removing line 1.
# Includes a blank-line context line to exercise the applier's blank handling.
original = "import os\n\nprint(1)\n"
store = ProjectStore.get()
sid, bugs, _ = Scanner(store).scan({"add.py": original})
print("scan bugs:", [(b.category, b.line) for b in bugs])
target = next(b for b in bugs if b.category == "F401")
print("target:", target.id, target.title)

# Mocked LLM diff: removes the unused import, keeping blank + print via context.
def fake_diff(file, content, desc):
    return (
        "--- a/add.py\n+++ b/add.py\n@@ -1,3 +0,2 @@\n-import os\n \n print(1)\n",
        True,
    )
fixer_mod.generate_diff = fake_diff

change = fixer_mod.generate_fix(target, original)
assert change is not None, "generate_fix returned None"
print("patched repr:", repr(change.patched))
expected = "\nprint(1)\n"
assert change.patched == expected, f"expected {expected!r}, got {change.patched!r}"

res = fixer_mod.validate_fix(target, change)
print("lint_ok:", res.lint_ok)
print("post-fix findings:", [f.rule_id for f in lint_file(target.file, change.patched)])
assert res.lint_ok is True, "re-lint gate failed"
assert "--- a/add.py" in res.diff and "+++ b/add.py" in res.diff
print("SMOKE OK: fix + re-lint gate pass")
