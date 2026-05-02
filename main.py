"""CLI entry point to run all fintech tasks from one interface."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from pprint import pprint
from typing import Any

from src.ai.explainer import critique_explanation, explain_portfolio
from src.classification.market_data import fetch_crypto_price, fetch_stock_price, format_table
from src.risk.metrics import compute_risk_metrics, print_allocation_chart, validate_portfolio
from src.risk.temperature import compute_temperature


DEFAULT_PORTFOLIO: dict[str, Any] = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}

VALID_TONES = ("beginner", "experienced", "expert")


def load_portfolio(path: str | None) -> dict[str, Any]:
    """Load and validate a portfolio from a JSON file, or fall back to the default."""
    if not path:
        return DEFAULT_PORTFOLIO
    
    portfolio_path = Path(path)

    if not portfolio_path.is_file():
        raise FileNotFoundError(f"portfolio file not found: {portfolio_path}")
    with portfolio_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
  
    validate_portfolio(data)
    return data


def fetch_market_data() -> list[dict[str, Any]]:
    """Fetch market prices used by Task 2."""
    return [
        fetch_crypto_price("bitcoin"),
        fetch_stock_price("^NSEI"),
        fetch_stock_price("GC=F"),
    ]


def run_task1(portfolio: dict[str, Any]) -> None:
    """Task 1: Portfolio risk calculator."""
    try:
        print("\nTask 1 - Portfolio Risk Calculator")
        metrics = compute_risk_metrics(portfolio)
        pprint(metrics)
        print("\nAllocation breakdown:")
        print_allocation_chart(portfolio)
    except Exception as exc:
        print(f"[Task 1 Error] Unable to compute risk metrics: {exc}")


def run_task2() -> None:
    """Task 2: Market data fetch (independent of any specific portfolio)."""
    try:
        print("\nTask 2 - Market Data Fetch")
        market_rows = fetch_market_data()
        format_table(market_rows)
    except Exception as exc:
        print(f"[Task 2 Error] Unable to fetch market data: {exc}")


def run_task3(portfolio: dict[str, Any], tone: str = "beginner") -> None:
    """Task 3: AI portfolio explainer."""
    try:
        print(f"\nTask 3 - AI Portfolio Explainer (tone: {tone})")
        raw_response, parsed_response = explain_portfolio(portfolio, tone=tone)
        print("Raw LLM response:")
        print(raw_response)
        print("\nParsed Output:")
        pprint(parsed_response)
        # Bonus: second LLM call that critiques the first explanation for missing risks.
        print("\nCritique of the explanation:")
        try:
            print(critique_explanation(parsed_response))
        except Exception as critique_exc:
            print(f"[Critique skipped] {critique_exc}")
    except Exception as exc:
        print(f"[Task 3 Error] Unable to generate AI explanation: {exc}")


def run_task4(portfolio: dict[str, Any]) -> None:
    """Task 4: Portfolio temperature using runway from Task 1."""
    try:
        print("\nTask 4 - Portfolio Temperature")
        metrics = compute_risk_metrics(portfolio)
        runway_months = float(metrics["severe_crash"]["runway_months"])
        score, label = compute_temperature(portfolio, runway_months)
        print(f"Using severe-crash runway from Task 1: {runway_months:.2f} months")
        print(f"Temperature Score: {score:.2f}")
        print(f"Temperature Label: {label}")
    except Exception as exc:
        print(f"[Task 4 Error] Unable to compute portfolio temperature: {exc}")


def _print_menu() -> None:
    """Display task menu."""
    print("Select Task:")
    print("1 -> Portfolio Risk Calculator")
    print("2 -> Market Data Fetch")
    print("3 -> AI Portfolio Explainer")
    print("4 -> Portfolio Temperature")


def _prompt_tone(default: str) -> str:
    """Prompt the user to pick an LLM tone for Task 3, falling back to default."""
    options = " / ".join(VALID_TONES)
    raw = input(f"Choose tone for Task 3 [{options}] (default: {default}): ").strip().lower()
    if not raw:
        return default
   
    first_token = raw.split()[0]
    if first_token not in VALID_TONES:
        print(f"Unknown tone '{first_token}'. Falling back to '{default}'.")
        return default
    return first_token


def _prompt_portfolio_path(initial_path: str | None) -> tuple[dict[str, Any], str]:
    """Interactively ask for a portfolio JSON path, retrying until it loads.

    Returns (portfolio_dict, source_label) so the caller can report what was loaded.
    If the user passed --portfolio on the CLI, that wins and we skip the prompt.
    """
    if initial_path is not None:
        return load_portfolio(initial_path), initial_path

    while True:
        raw = input(
            "Portfolio JSON path (Enter for built-in default, or e.g. samples/conservative.json): "
        ).strip().strip('"').strip("'")
        if not raw:
            return load_portfolio(None), "built-in default"
        try:
            return load_portfolio(raw), raw
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            print(f"[Portfolio Error] {exc}. Please try again or press Enter for default.")


def _run_selected_task(task: int, portfolio: dict[str, Any], tone: str) -> None:
    """Dispatch selected task number with the loaded portfolio."""
    if task == 1:
        run_task1(portfolio)
    elif task == 2:
        run_task2()
    elif task == 3:
        run_task3(portfolio, tone=tone)
    elif task == 4:
        run_task4(portfolio)
    else:
        print(f"Invalid task '{task}'. Choose 1, 2, 3, or 4.")


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run Timecell intern test tasks. Pass --portfolio to use your own input.",
    )
    parser.add_argument(
        "--task",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run a specific task directly (1-4).",
    )
    parser.add_argument(
        "--portfolio",
        type=str,
        default=None,
        help="Path to a JSON portfolio file (e.g. samples/conservative.json). Defaults to a built-in sample.",
    )
    parser.add_argument(
        "--tone",
        type=str,
        choices=list(VALID_TONES),
        default="beginner",
        help="Tone for the Task 3 LLM explanation: beginner, experienced, or expert.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for interactive and argument-based execution."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
   
    for noisy in ("httpx", "httpcore", "google_genai", "google.genai", "urllib3", "yfinance"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    args = _parse_args()

    if args.task is not None:
        try:
            portfolio = load_portfolio(args.portfolio)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            print(f"[Portfolio Error] {exc}")
            return
        print(f"Portfolio source: {args.portfolio if args.portfolio else 'built-in default'}")
        _run_selected_task(args.task, portfolio, args.tone)
        return

    try:
        portfolio, source = _prompt_portfolio_path(args.portfolio)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"[Portfolio Error] {exc}")
        return
    print(f"Portfolio source: {source}")

    _print_menu()
    choice = input("Enter task number (1-4): ").strip()

    try:
        task = int(choice)
    except ValueError:
        print(f"Invalid input '{choice}'. Please enter a number from 1 to 4.")
        return

    tone = _prompt_tone(args.tone) if task == 3 else args.tone
    _run_selected_task(task, portfolio, tone)


if __name__ == "__main__":
    main()
