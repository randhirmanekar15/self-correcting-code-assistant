# Self-Correcting Code Assistant

![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Runs](https://img.shields.io/badge/runs-100%25%20local-orange)

An AI agent that writes Python, runs it, reads the error, rewrites, and repeats until the code passes — or it hits a retry cap. The Python interpreter is the **external verifier**: the model never grades its own work.

Runs fully locally on [Ollama](https://ollama.com). No API keys, no cloud, no per-token cost.

## Overview

In 2026, a single LLM call that emits code is no longer impressive — what matters is *reliability*. Recent research is blunt about it: when an LLM self-corrects using only its own reasoning, performance often doesn't improve and sometimes degrades. Self-correction is dependable only when an **external, verifiable signal** decides correctness.

Code is the perfect case. It either runs or it throws. This project builds the entire loop around that signal: generate code → execute it in a subprocess → if it crashes, capture the real traceback → feed that traceback back to the model → repeat until it passes or the retry cap trips. The model proposes; the interpreter judges.

## Features

- Generate → execute → correct loop driven by real `stderr`
- Hard retry cap so it can never loop forever
- Per-execution timeout so a bad generation can't hang the agent
- Markdown fence stripping so the model wrapping code in ` ```python ` never breaks the run
- Every attempt appended to `run.log` for auditability

## How it works

```
task ──▶ generate(code) ──▶ run_code() ──▶ pass? ──yes──▶ done
            ▲                    │
            │                   no
            └──── feed real traceback back ◀──┘   (up to MAX_ATTEMPTS)
```

The loop is the whole architecture: the model only ever sees the previous code plus the exact error, and is asked to fix the root cause.

## Tech stack

| Piece | Choice | Why |
|-------|--------|-----|
| Runtime | Ollama (local) | Free, private |
| Model | `qwen3-coder` | Strong open-weight coder, runs on consumer hardware |
| Execution | Python `subprocess` | Real interpreter = trustworthy errors |
| Safety | Retry cap + timeout + fence stripping | Bounded, predictable runs |

## Project structure

```
agent.py            # the agent: generate / run_code / solve loop
test_agent.py       # tests for pure helpers + the subprocess runner
requirements.txt
ARTICLE.md          # full write-up
```

## Installation

```bash
# 1. Install Ollama: https://ollama.com
ollama pull qwen3-coder
# 2. Install deps
pip install -r requirements.txt
```

## Usage

```bash
python agent.py "write a function that returns the first 10 prime numbers and print them"
```

Example (first-pass success):

```
PASSED. Final code:
def is_prime(n): ...
Output:
[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

## Configuration

Edit the constants at the top of `agent.py`:

| Constant | Default | Meaning |
|----------|---------|---------|
| `MODEL` | `qwen3-coder:latest` | Any Ollama model tag |
| `MAX_ATTEMPTS` | `5` | Retry cap |
| `EXEC_TIMEOUT` | `30` | Seconds per execution |

## Testing

```bash
pip install pytest
pytest        # runs without a model (pure functions + subprocess)
```

## Limitations

- "Runs without error" is not "correct" — the interpreter catches crashes, not logic bugs. Next step: generate tests and self-correct against those.
- Executing model-generated code is a security surface. Fine for your own machine and prompts; sandbox before exposing to untrusted input.

## Roadmap

- [ ] Generate unit tests and verify against them (logic correctness, not just "it ran")
- [ ] Optional Docker sandbox for execution
- [ ] Support multiple files / project scaffolds

## Credits

📖 Full write-up: [ARTICLE.md](ARTICLE.md).

Inspired by Aman Kharwal's tutorial, [Creating a Self-Correcting Code Assistant](https://amanxai.com/2026/05/20/creating-a-self-correcting-code-assistant/). Rebuilt and extended (model swap, retry cap, run log, fence stripping, execution timeout).

## Author

Built by **Randhir Manekar** — [randhirmanekar.com](https://randhirmanekar.com) · [github.com/randhirmanekar15](https://github.com/randhirmanekar15)

## License

MIT — see [LICENSE](LICENSE).
