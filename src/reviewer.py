import datetime
import json
import subprocess
from pathlib import Path
from ollama_client import call_ollama, try_extract_json
from diff_utils import parse_unified_diff, run_cmd
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=str, default=".", help="Path to the target git repository")
args = parser.parse_args()

# change working directory to target repo
os.chdir(args.repo)

OUTPUT_DIR = Path("code_review")
OUTPUT_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """
You are an expert senior software engineer and security reviewer.
Analyze the diff and surrounding code context. Return structured JSON:
{
    "quality_rating": 0-10,
    "status": "ok" or "improvements_required",
    "summary": "Short description of changes",
    "issues": [
        {"type": "...", "severity": "...", "description": "...", "file_path": "...", "line_range": "...", "suggestion": "..."}
    ],
    "recommendations": ["..."]
}
Return ONLY valid JSON.
"""


CHUNK_PROMPT = """
Review this code chunk for a PR. Focus on meaningful suggestions:
- Security vulnerabilities
- Architectural issues
- Correctness concerns
Do not just lint nor provide basic code corrections.

File path: {file_path}
Context:
{context_block}

Diff fragment:
```diff
{diff_fragment}
```
"""


def get_git_diff() -> str:
    """Run `git diff HEAD` and return its output."""
    result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr}")
    return result.stdout


def build_prompt(file_path: str, diff_fragment: str, context_block: str) -> str:
    """Combine SYSTEM_PROMPT + CHUNK_PROMPT with content."""
    return SYSTEM_PROMPT + CHUNK_PROMPT.format(
        file_path=file_path,
        context_block=context_block,
        diff_fragment=diff_fragment
    )


def get_context(file_path: str, start_line: int, num_lines: int = 30) -> str:
    """Return surrounding context lines from file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        start = max(0, start_line - num_lines // 2)
        end = min(len(lines), start_line + num_lines // 2)
        return "".join(lines[start:end])
    except Exception:
        return ""


def review_diff():
    """Main function: read git diff, split chunks, review each, save JSON report."""
    diff_text = get_git_diff()
    file_hunks = parse_unified_diff(diff_text)

    all_reviews = []

    for file_path, hunks in file_hunks.items():
        for (start_line, diff_fragment) in hunks:
            context_block = get_context(file_path, start_line)
            prompt = build_prompt(file_path, diff_fragment, context_block)

            print(f"Reviewing {file_path}:{start_line}...")
            response_text = call_ollama(prompt)
            review_json = try_extract_json(response_text)

            if not review_json:
                review_json = {
                    "error": "Model did not return valid JSON",
                    "raw_response": response_text,
                }

            review_json["file_path"] = file_path
            review_json["line_start"] = start_line
            all_reviews.append(review_json)

    # Save all results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"review_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=2)

    print(f"\n✅ Review complete. Saved results to: {output_file}")


if __name__ == "__main__":
    review_diff()