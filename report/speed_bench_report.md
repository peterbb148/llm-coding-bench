# Speed Benchmark Report

**Date:** 2026-06-29  
**Benchmark:** `benchmarks/speed_bench.py`  
**Prompt:** BFS vs DFS explanation (graph traversal, data structures, complexity, use-case examples)  
**Runs per model:** 3  
**Metric note:** Token counts use each model's own tokenizer; `char/s` is the fairest cross-model comparison.

---

## Results

| Model                | tok/s (mean) | tok/s (±σ) | char/s (mean) | Output tokens (mean) |
|----------------------|-------------:|-----------:|--------------:|---------------------:|
| gpt-5.4              | 100.4        | ±11.3      | 400.0         | 905                  |
| glm-4.7-flash:latest | 64.3         | ±0.2       | 128.0         | 2348                 |
| claude-sonnet-4-6    | 60.9         | ±2.9       | 203.2         | 2603                 |

---

## Observations

- **gpt-5.4** is the fastest on both tok/s and char/s, reaching ~400 char/s — nearly 2× Claude and 3× GLM. Its shorter output (~905 tokens) contributes to the high tok/s, but char/s still confirms a genuine throughput advantage.
- **claude-sonnet-4-6** produces the longest responses (~2603 tokens) with moderate char/s (203 char/s), reflecting a denser, more verbose style.
- **glm-4.7-flash:latest** (local via Ollama) is remarkably consistent (±0.2 tok/s) and comparable to Claude in tok/s, but its char/s is lower due to shorter average token lengths, suggesting a different tokenization granularity.
- All models completed 3/3 runs without errors.

---

## Raw per-run data

| Model                | Run 1 (tok/s) | Run 2 (tok/s) | Run 3 (tok/s) |
|----------------------|--------------:|--------------:|--------------:|
| claude-sonnet-4-6    | 57.6          | 62.1          | 63.1          |
| gpt-5.4              | 87.4          | 107.2         | 106.6         |
| glm-4.7-flash:latest | 64.4          | 64.1          | 64.3          |
