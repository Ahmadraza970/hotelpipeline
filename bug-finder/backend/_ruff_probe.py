from app.core.linters import lint_python_ruff, _ruff_cmd

snippet = "import os\n\ndef add(a, b):\n    return a + b\n\nprint(missing_var)\n"
print("ruff_cmd:", _ruff_cmd())
findings = lint_python_ruff("add.py", snippet)
print("findings:", len(findings))
for f in findings:
    print(f"  {f.rule_id} {f.severity} line={f.line} col={f.column} :: {f.message}")
