# I Built an AI Agent That Debugs Its Own Code

*Write → run → read the error → rewrite → repeat. Here's how I built a self-correcting code assistant that runs entirely on my own machine — and why "code that must pass tests" is the one place self-correction actually works in 2026.*

---

## Why this, why now

Through 2025, a single LLM call that spat out code was good enough for a demo. In 2026 that bar is gone. Gartner's latest read shows multi-agent and self-improving systems moving from experiments into production, with the agentic AI market projected to grow from around **$7.8B today to over $52B by 2030**, and **40% of enterprise applications expected to embed AI agents by the end of 2026** (up from under 5% in 2025).

But here's the catch most people miss. Recent research is blunt about it: when an LLM tries to **self-correct using only its own reasoning, performance often doesn't improve — and sometimes gets worse.** Self-correction is reliable in exactly one situation: when there's an **external, verifiable signal** telling the model whether it was right.

Code is the perfect case. Code either runs or it throws an error. That error is ground truth — not the model's opinion of itself. That's the whole idea behind this project: don't ask the model "are you sure?" Ask the **Python interpreter**.

## What it does

You give it a task in plain English. The agent:

1. Generates a Python script.
2. Executes it in a subprocess.
3. If it crashes, captures the real `stderr`.
4. Feeds that error back to the model and asks for a fix.
5. Repeats until the code runs clean — or it hits a retry cap.

No cloud, no API keys. It runs on [Ollama](https://ollama.com) with a local open-weight coding model.

## The stack

| Piece | Choice | Why |
|-------|--------|-----|
| Runtime | Ollama | Local, free, private |
| Model | `qwen3-coder` | One of the strongest open-weight coding models you can run on consumer hardware in 2026 |
| Execution | Python `subprocess` | Real interpreter = real, trustworthy errors |
| Safety | Per-run timeout + retry cap | A bad generation can't hang or loop forever |

A note on the model. The open-weight landscape in 2026 is crowded and genuinely good — DeepSeek V4, Qwen 3.6, Llama 4, GLM-5.2, MiniMax M3. I went with the Qwen coder line because it punches above its weight on coding benchmarks while still fitting on a normal machine. Swapping models is a one-line change, which is the point of building local-first.

## How it works

The loop is the entire architecture. Here's the core:

```python
def solve(task: str) -> None:
    code, error = None, None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        code = generate(task, code, error)      # ask the model
        ok, output = run_code(code)             # ask the interpreter

        if ok:
            print("PASSED.\n", code, "\n", output)
            return

        error = output                          # feed reality back in
```

The "ask the interpreter" step is what makes it honest:

```python
def run_code(code: str) -> tuple[bool, str]:
    # write to a temp file, run it, capture the truth
    proc = subprocess.run(
        [sys.executable, path],
        capture_output=True, text=True, timeout=EXEC_TIMEOUT,
    )
    if proc.returncode == 0:
        return True, proc.stdout
    return False, (proc.stderr or proc.stdout)
```

And when it fails, the next prompt isn't "try again" — it's the previous code plus the exact traceback:

```python
user += (
    f"\nYour previous code:\n{prev_code}\n"
    f"\nIt failed with this error:\n{error}\n"
    "Return a corrected full script."
)
```

That's the external grounding the research says you need. The model isn't grading itself; the traceback is.

## What I changed from the original tutorial

This project was inspired by Aman Kharwal's walkthrough, **["Creating a Self-Correcting Code Assistant"](https://amanxai.com/2026/05/20/creating-a-self-correcting-code-assistant/)**. I rebuilt it from scratch and made it sturdier:

- **Swapped the model** to `qwen3-coder` for stronger code generation.
- **Added a hard retry cap and a per-attempt run log**, so every loop is auditable — which, not coincidentally, is exactly the "governance and observability" pressure showing up across the 2026 agent tooling space.
- **Strip markdown fences** before execution, so the model wrapping its answer in ` ```python ` never breaks the run.
- **Timeout on every execution**, so an accidental infinite loop can't freeze the agent.

## A real run

Task: *"write a function that returns the first 10 prime numbers and print them."*

It produced a clean `is_prime` helper, ran it, and printed `[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]` on the first pass. For harder prompts where the first attempt throws, watching it read its own traceback and patch the bug is the part that actually feels like an engineer at work.

## Where it breaks (and the honest limitations)

- **"Runs without error" is not "correct."** A script can run and still do the wrong thing. The interpreter catches crashes, not logic bugs. The real next step is having it generate **tests** and self-correct against those — that's the difference between a toy and a tool.
- **Executing model-generated code is a security surface.** It's fine on my own machine for my own prompts; it is not something to expose to untrusted input without a sandbox. The 2026 Hype Cycle's emphasis on agent security exists for exactly this reason.
- **Pure self-correction has a ceiling.** Without that external verifier, the research is clear that the loop can spin without improving. The whole design leans on the interpreter being the judge.

## Takeaway

The interesting lesson isn't "LLMs can fix code." It's *when* self-correction works at all: only when something outside the model can verify the answer. Code is one of the few domains that gives you that signal for free. Build the loop around the verifier, not around the model's confidence.

**Code:** [github.com/randhirmanekar15/self-correcting-code-assistant](https://github.com/randhirmanekar15/self-correcting-code-assistant)

---

*Inspired by Aman Kharwal's tutorial, ["Creating a Self-Correcting Code Assistant"](https://amanxai.com/2026/05/20/creating-a-self-correcting-code-assistant/). I rebuilt and extended it as described above.*

### Sources
- [2026 Hype Cycle for Agentic AI — Gartner](https://www.gartner.com/en/articles/hype-cycle-for-agentic-ai)
- [Agent Self-Correction: From Reflexion to Process Reward Models — Zylos Research](https://zylos.ai/research/2026-05-12-agent-self-correction-reflexion-to-prm)
- [A Self-Healing Framework for Reliable LLM-Based Autonomous Agents — arXiv](https://arxiv.org/abs/2605.06737)
- [Best Open-Source LLMs in 2026 — Hugging Face](https://huggingface.co/blog/daya-shankar/open-source-llms)
