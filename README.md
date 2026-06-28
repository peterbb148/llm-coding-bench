# llm-coding-bench

Benchmarks frontier LLMs (Anthropic, OpenAI) against a local model (Ollama) on two axes:

1. **Speed** — tokens/s and chars/s on a fixed prompt across all models
2. **Coding quality** — each model independently solves [LeetCode 42: Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/), judged on correctness (automated test runner) and quality (LLM judge)

## Models

| Model | Provider |
|---|---|
| `claude-sonnet-4-6` | Anthropic API |
| GPT-5.4 | OpenAI API |
| `glm-4-flash` | Ollama (local) |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
```

Ollama must be running locally with the glm-4-flash model pulled:
```bash
ollama pull glm4:flash
```

## Running

```bash
# Speed benchmark
python benchmarks/speed_bench.py

# Judge all model solutions
python judge/run_judge.py --all

# Combined report
python report/generate_report.py
```

## Structure

```
models/          # provider wrappers (Anthropic, OpenAI, Ollama)
benchmarks/      # speed_bench.py
challenges/      # problem statements, reference solutions, test cases
judge/           # test runner + LLM judge
report/          # generate_report.py, results.json, summary.md
```
