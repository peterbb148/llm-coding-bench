import argparse
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from challenges.trapping_rain_water.tests import TEST_CASES


REFERENCE_SOLUTION = """\
def trap(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    left_max = right_max = water = 0
    while left < right:
        if height[left] < height[right]:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water
"""

PROBLEM_STATEMENT = """\
LeetCode 42 - Trapping Rain Water

Given n non-negative integers representing an elevation map where the width of each bar is
1, compute how much water it can trap after raining.
"""


@dataclass(frozen=True)
class Submission:
    name: str
    display_name: str
    branch: str
    path: str


@dataclass(frozen=True)
class TestResult:
    input_value: list[int]
    expected: int
    actual: int | None
    passed: bool
    error: str | None = None


@dataclass(frozen=True)
class QualityScore:
    correctness: int
    time_complexity: int
    space_complexity: int
    code_clarity: int
    overall: float
    rationale: str


@dataclass(frozen=True)
class SubmissionResult:
    submission: Submission
    tests: list[TestResult]
    quality: QualityScore | None

    @property
    def passed_tests(self) -> int:
        return sum(1 for test in self.tests if test.passed)


SUBMISSIONS = {
    "claude": Submission(
        name="claude",
        display_name="Claude",
        branch="origin/challenge/4-claude",
        path="challenges/trapping_rain_water/claude.py",
    ),
    "gpt5": Submission(
        name="gpt5",
        display_name="GPT-5",
        branch="origin/challenge/4-gpt5",
        path="challenges/trapping_rain_water/gpt5.py",
    ),
    "glm": Submission(
        name="glm",
        display_name="glm-4-flash",
        branch="origin/feat/4-glm-solution",
        path="challenges/trapping_rain_water/glm.py",
    ),
}

console = Console()


def run_git_show(branch: str, path: str) -> str:
    """Return a submission file from a git branch."""
    command = ["git", "show", f"{branch}:{path}"]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        raise RuntimeError(f"Could not load {path} from {branch}: {detail}") from exc
    return result.stdout


def run_candidate_tests(source: str) -> list[TestResult]:
    """Execute candidate tests in a subprocess and return structured results."""
    payload = {
        "source": source,
        "tests": [
            {"input": input_value, "expected": expected}
            for input_value, expected in TEST_CASES
        ],
    }
    script = textwrap.dedent(
        """
        import json
        import traceback

        payload = json.loads(input())
        namespace = {}
        results = []

        try:
            exec(payload["source"], namespace)
            trap = namespace["trap"]
        except Exception:
            setup_error = traceback.format_exc()
            for test in payload["tests"]:
                results.append({
                    "input": test["input"],
                    "expected": test["expected"],
                    "actual": None,
                    "passed": False,
                    "error": setup_error,
                })
            print(json.dumps(results))
            raise SystemExit(0)

        for test in payload["tests"]:
            try:
                actual = trap(list(test["input"]))
                passed = actual == test["expected"]
                error = None
            except Exception:
                actual = None
                passed = False
                error = traceback.format_exc()

            results.append({
                "input": test["input"],
                "expected": test["expected"],
                "actual": actual,
                "passed": passed,
                "error": error,
            })

        print(json.dumps(results))
        """
    )
    process = subprocess.run(
        [sys.executable, "-c", script],
        input=json.dumps(payload),
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise RuntimeError(f"Candidate test subprocess failed: {detail}")

    raw_results = json.loads(process.stdout)
    return [
        TestResult(
            input_value=result["input"],
            expected=result["expected"],
            actual=result["actual"],
            passed=result["passed"],
            error=result["error"],
        )
        for result in raw_results
    ]


def build_judge_prompt(source: str, test_results: list[TestResult]) -> str:
    """Build the LLM judge prompt from the issue #5 rubric."""
    test_summary = [
        {
            "input": result.input_value,
            "expected": result.expected,
            "actual": result.actual,
            "passed": result.passed,
            "error": result.error,
        }
        for result in test_results
    ]
    return f"""\
You are judging a Python solution for a coding benchmark.

Problem:
{PROBLEM_STATEMENT}

Reference solution:
```python
{REFERENCE_SOLUTION}
```

Candidate solution:
```python
{source}
```

Automated test results:
```json
{json.dumps(test_summary, indent=2)}
```

Score each criterion from 1 to 5:
1. correctness - does it handle all edge cases?
2. time_complexity - does it reach O(n)?
3. space_complexity - does it reach O(1)?
4. code_clarity - is it readable, well-named, and Pythonic?
5. overall - compared to the reference solution

Return strict JSON only with this shape:
{{
  "correctness": 1,
  "time_complexity": 1,
  "space_complexity": 1,
  "code_clarity": 1,
  "overall": 1.0,
  "rationale": "brief explanation"
}}
"""


def judge_with_openai(prompt: str, model: str) -> str:
    """Run the LLM judge through OpenAI."""
    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI judging.")

    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("OpenAI judge returned an empty response.")
    return content


def judge_with_anthropic(prompt: str, model: str) -> str:
    """Run the LLM judge through Anthropic."""
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic judging.")

    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise RuntimeError("Anthropic judge returned an empty response.")
    return "\n".join(text_blocks)


def parse_quality_score(raw_response: str) -> QualityScore:
    """Parse and validate a quality score returned by the LLM judge."""
    parsed = json.loads(raw_response)
    required = ["correctness", "time_complexity", "space_complexity", "code_clarity", "overall"]
    for key in required:
        if key not in parsed:
            raise ValueError(f"Judge response missing required field: {key}")

    for key in required[:-1]:
        value = parsed[key]
        if not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"Judge response field {key} must be an integer from 1 to 5.")

    overall = parsed["overall"]
    if not isinstance(overall, int | float) or not 1 <= overall <= 5:
        raise ValueError("Judge response field overall must be a number from 1 to 5.")

    return QualityScore(
        correctness=parsed["correctness"],
        time_complexity=parsed["time_complexity"],
        space_complexity=parsed["space_complexity"],
        code_clarity=parsed["code_clarity"],
        overall=float(overall),
        rationale=str(parsed.get("rationale", "")).strip(),
    )


def score_with_llm(
    source: str,
    test_results: list[TestResult],
    judge_provider: str,
    judge_model: str,
) -> QualityScore:
    """Score a candidate solution with the configured LLM judge."""
    prompt = build_judge_prompt(source, test_results)
    if judge_provider == "openai":
        raw_response = judge_with_openai(prompt, judge_model)
    elif judge_provider == "anthropic":
        raw_response = judge_with_anthropic(prompt, judge_model)
    else:
        raise ValueError(f"Unsupported judge provider: {judge_provider}")
    return parse_quality_score(raw_response)


def evaluate_submission(
    submission: Submission,
    correctness_only: bool,
    judge_provider: str,
    judge_model: str,
) -> SubmissionResult:
    """Load, test, and score one submission."""
    source = run_git_show(submission.branch, submission.path)
    test_results = run_candidate_tests(source)
    quality = None
    if not correctness_only:
        quality = score_with_llm(source, test_results, judge_provider, judge_model)
    return SubmissionResult(submission=submission, tests=test_results, quality=quality)


def render_scorecard(results: list[SubmissionResult]) -> None:
    """Print the combined scorecard."""
    table = Table(title="Coding Judge - Trapping Rain Water", box=box.ROUNDED, show_lines=True)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Tests", justify="right")
    table.add_column("Correct", justify="right")
    table.add_column("Time", justify="right")
    table.add_column("Space", justify="right")
    table.add_column("Clarity", justify="right")
    table.add_column("Overall", justify="right")

    for result in results:
        quality = result.quality
        if quality is None:
            values = ["-", "-", "-", "-", "-"]
        else:
            values = [
                str(quality.correctness),
                str(quality.time_complexity),
                str(quality.space_complexity),
                str(quality.code_clarity),
                f"{quality.overall:.1f}",
            ]

        table.add_row(
            result.submission.display_name,
            f"{result.passed_tests}/{len(result.tests)}",
            *values,
        )

    console.print(table)


def render_details(results: list[SubmissionResult]) -> None:
    """Print per-submission test failures and judge rationale."""
    for result in results:
        failed = [test for test in result.tests if not test.passed]
        console.print(f"\n[bold]{result.submission.display_name}[/bold]")
        console.print(f"Source: {result.submission.branch}:{result.submission.path}")
        if failed:
            for test in failed:
                console.print(
                    f"[red]FAIL[/red] input={test.input_value} "
                    f"expected={test.expected} actual={test.actual}"
                )
                if test.error:
                    console.print(test.error)
        else:
            console.print("[green]All tests passed.[/green]")

        if result.quality and result.quality.rationale:
            console.print(f"[dim]{result.quality.rationale}[/dim]")


def selected_submissions(args: argparse.Namespace) -> list[Submission]:
    """Return the submission set requested by the CLI."""
    if args.all:
        return list(SUBMISSIONS.values())
    if args.model:
        return [SUBMISSIONS[args.model]]
    raise ValueError("Specify a model name or --all.")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Judge model solutions for issue #5.")
    parser.add_argument("model", nargs="?", choices=sorted(SUBMISSIONS))
    parser.add_argument("--all", action="store_true", help="Judge all configured submissions.")
    parser.add_argument(
        "--correctness-only",
        action="store_true",
        help="Run only the subprocess correctness tests without calling an LLM judge.",
    )
    parser.add_argument(
        "--judge-provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="Provider to use for LLM quality judging.",
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-4o",
        help="Model to use for quality judging.",
    )
    parser.add_argument("--details", action="store_true", help="Print test details and rationales.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    submissions = selected_submissions(args)
    results = [
        evaluate_submission(
            submission=submission,
            correctness_only=args.correctness_only,
            judge_provider=args.judge_provider,
            judge_model=args.judge_model,
        )
        for submission in submissions
    ]
    render_scorecard(results)
    if args.details:
        render_details(results)


if __name__ == "__main__":
    main()
