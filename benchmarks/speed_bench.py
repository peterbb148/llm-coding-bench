import statistics
import sys
from rich.console import Console
from rich.table import Table
from rich import box
from models import anthropic_model, openai_model, ollama_model

PROMPT = (
    "Explain the difference between BFS and DFS graph traversal algorithms. "
    "Describe the data structures each uses internally, their time and space complexity, "
    "and give a concrete example of a problem where you would prefer each one over the other."
)

RUNS = 3
MODELS = [anthropic_model, openai_model, ollama_model]

console = Console()


def benchmark_model(model_module):
    results = []
    name = model_module.MODEL_ID
    for i in range(1, RUNS + 1):
        console.print(f"  run {i}/{RUNS}...", end="")
        try:
            r = model_module.complete(PROMPT)
            results.append(r)
            console.print(f" {r.tokens_per_second:.1f} tok/s")
        except Exception as e:
            console.print(f" [red]error: {e}[/red]")
    return name, results


def mean_std(values):
    if not values:
        return 0.0, 0.0
    m = statistics.mean(values)
    s = statistics.stdev(values) if len(values) > 1 else 0.0
    return m, s


def main():
    console.print("\n[bold]Speed Benchmark[/bold] — running each model 3 times\n")

    all_results = {}
    for module in MODELS:
        console.print(f"[cyan]{module.MODEL_ID}[/cyan]")
        name, results = benchmark_model(module)
        all_results[name] = results
        console.print()

    table = Table(
        title="LLM Speed Benchmark",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("tok/s (mean)", justify="right")
    table.add_column("tok/s (±σ)", justify="right")
    table.add_column("char/s (mean)", justify="right")
    table.add_column("output tokens (mean)", justify="right")

    for model_id, results in all_results.items():
        if not results:
            table.add_row(model_id, "—", "—", "—", "—")
            continue
        tps_mean, tps_std = mean_std([r.tokens_per_second for r in results])
        cps_mean, _ = mean_std([r.chars_per_second for r in results])
        tok_mean, _ = mean_std([r.output_tokens for r in results])
        table.add_row(
            model_id,
            f"{tps_mean:.1f}",
            f"±{tps_std:.1f}",
            f"{cps_mean:.1f}",
            f"{tok_mean:.0f}",
        )

    console.print(table)
    console.print(
        "\n[dim]Note: token counts use each model's own tokenizer — "
        "char/s is the fairest cross-model comparison.[/dim]\n"
    )


if __name__ == "__main__":
    main()
