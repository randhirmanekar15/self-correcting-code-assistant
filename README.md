# Self-Correcting Code Assistant

An AI agent that writes Python, runs it, reads the error, rewrites, and repeats until the code passes — or it hits a retry cap. The Python interpreter is the **external verifier**: the model never grades its own work.

Runs fully locally on [Ollama](https://ollama.com). No API keys, no cloud.

## Why it works

Research in 2026 is clear that LLM self-correction is only reliable when an *external* signal decides correctness. Code is the perfect case: it runs or it throws. This agent feeds the real traceback back to the model on every failed attempt.

## Stack

| Piece | Choice |
|-------|--------|
| Runtime | Ollama (local) |
| Model | `qwen3-coder` |
| Execution | Python `subprocess` with a timeout |
| Safety | Retry cap + per-run timeout + fence stripping |

## Setup

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

Every attempt is appended to `run.log`.

## Test

```bash
pip install pytest
pytest        # tests run without a model (pure functions + subprocess)
```

## Configuration

Edit the constants at the top of `agent.py`:

- `MODEL` — any Ollama model tag
- `MAX_ATTEMPTS` — retry cap (default 5)
- `EXEC_TIMEOUT` — seconds per execution (default 30)

## Limitations

- "Runs without error" is not "correct" — the interpreter catches crashes, not logic bugs. A natural next step is generating tests and self-correcting against those.
- Executing model-generated code is a security surface. Fine for your own machine and your own prompts; sandbox it before exposing to untrusted input.

---

Inspired by Aman Kharwal's tutorial, [Creating a Self-Correcting Code Assistant](https://amanxai.com/2026/05/20/creating-a-self-correcting-code-assistant/). Rebuilt and extended (model swap, retry cap, run log, fence stripping, execution timeout).

MIT licensed.
