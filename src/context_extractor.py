import ast
from pathlib import Path

SURROUNDING_LINES = 20

def read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")

def python_enclosing_node(source: str, target_line: int) -> str:
    """Get surrounding function/class for the diff line."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return line_surrounding(source, target_line)
    candidate = None
    for node in ast.walk(tree):
        if hasattr(node, "lineno"):
            end_lineno = getattr(node, "end_lineno", node.lineno)
            if node.lineno <= target_line <= end_lineno:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    candidate = node
                    break
                candidate = node
    if candidate:
        start = candidate.lineno - 1
        end = getattr(candidate, "end_lineno", candidate.lineno)
        src_lines = source.splitlines()
        return "\n".join(src_lines[max(0, start - 2): min(len(src_lines), end + 2)])
    return line_surrounding(source, target_line)

def line_surrounding(source: str, target_line: int) -> str:
    lines = source.splitlines()
    idx = max(0, target_line - 1)
    start = max(0, idx - SURROUNDING_LINES)
    end = min(len(lines), idx + SURROUNDING_LINES + 1)
    return "\n".join(lines[start:end])
