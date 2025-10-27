import re
import subprocess

def run_cmd(cmd: str) -> str:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{proc.stderr}")
    return proc.stdout

def parse_unified_diff(diff_text: str):
    """Return mapping: file_path -> list of (start_line, diff_text)."""
    UNIFIED_FILE_HEADER_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
    HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    file_hunks = {}
    lines = diff_text.splitlines(keepends=True)
    current_file = None
    i = 0
    while i < len(lines):
        m_file = UNIFIED_FILE_HEADER_RE.match(lines[i])
        if m_file:
            current_file = m_file.group(2)
            file_hunks.setdefault(current_file, [])
            i += 1
            continue
        if current_file:
            m_hunk = HUNK_HEADER_RE.match(lines[i])
            if m_hunk:
                b_start = int(m_hunk.group(1))
                hunk_lines = [lines[i]]
                i += 1
                while (
                    i < len(lines)
                    and not UNIFIED_FILE_HEADER_RE.match(lines[i])
                    and not HUNK_HEADER_RE.match(lines[i])
                ):
                    hunk_lines.append(lines[i])
                    i += 1
                file_hunks[current_file].append((b_start, "".join(hunk_lines)))
                continue
        i += 1
    return file_hunks
