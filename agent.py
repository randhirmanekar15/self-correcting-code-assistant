"""Self-correcting code assistant.

Generates Python code, runs it, reads the error, rewrites, and repeats until it
passes or a retry cap is reached. The Python interpreter is the external verifier:
the model never grades its own work.

Inspired by Aman Kharwal's tutorial:
https://amanxai.com/2026/05/20/creating-a-self-correcting-code-assistant/
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import ollama

MODEL = "qwen3-coder:latest"
MAX_ATTEMPTS = 5
EXEC_TIMEOUT = 30  # seconds per run

SYSTEM = (
    "You are an expert Python engineer. Return ONLY a complete, runnable Python "
    "script that solves the task. No explanations, no markdown fences. If given an "
    "error from a previous attempt, fix the root cause."
)


def strip_fences(text: str) -> str:
    """Remove ```python ... ``` wrappers the model sometimes adds."""
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip()


def generate(task: str, prev_code: str | None, error: str | None) -> str:
    """Ask the model for code, including the previous failure if there was one."""
    user = f"Task:\n{task}\n"
    if prev_code and error:
        user += (
            f"\nYour previous code:\n{prev_code}\n"
            f"\nIt failed with this error:\n{error}\n"
            "Return a corrected full script."
        )
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    return strip_fences(response["message"]["content"])


def run_code(code: str) -> tuple[bool, str]:
    """Execute code in a subprocess and return (passed, output_or_error)."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(code)
        path = handle.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            check=False,
        )
        if proc.returncode == 0:
            return True, proc.stdout
        return False, (proc.stderr or proc.stdout)
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {EXEC_TIMEOUT}s (possible infinite loop)."
    finally:
        Path(path).unlink(missing_ok=True)


def solve(task: str, max_attempts: int = MAX_ATTEMPTS) -> bool:
    """Run the generate/execute/correct loop. Returns True if the code passed."""
    log_path = Path("run.log")
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== {time.ctime()} :: {task}\n")
        code: str | None = None
        error: str | None = None

        for attempt in range(1, max_attempts + 1):
            print(f"\n--- Attempt {attempt}/{max_attempts} ---")
            code = generate(task, code, error)
            passed, output = run_code(code)
            log.write(f"[attempt {attempt}] passed={passed}\n{code}\n--- output ---\n{output}\n")

            if passed:
                print("PASSED. Final code:\n")
                print(code)
                print("\nOutput:\n" + output)
                log.write("RESULT: passed\n")
                return True

            print("Failed:\n" + output[:500])
            error = output

        print(f"\nGave up after {max_attempts} attempts.")
        log.write("RESULT: gave up\n")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-correcting code assistant")
    parser.add_argument("task", nargs="*", help="What the code should do")
    args = parser.parse_args()
    task = " ".join(args.task) or input("Task: ")
    solve(task)


if __name__ == "__main__":
    main()
