"""CLI entry point to run all fintech tasks from one interface."""

from __future__ import annotations

import argparse
import logging
from pprint import pprint
from typing import Any

from src.ai.explainer import explain_portfolio
from src.classification.market_data import fetch_crypto_price, fetch_stock_price, format_table
from src.risk.metrics import compute_risk_metrics
from src.risk.temperature import compute_temperature


PORTFOLIO: dict[str, Any] = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}


def fetch_market_data() -> list[dict[str, Any]]:
    """Fetch market prices used by Task 2."""
    return [
        fetch_crypto_price("bitcoin"),
        fetch_stock_price("^NSEI"),
        fetch_stock_price("GC=F"),
    ]


def run_task1() -> None:
    """Task 1: Portfolio risk calculator."""
    try:
        print("\nTask 1 - Portfolio Risk Calculator")
        metrics = compute_risk_metrics(PORTFOLIO)
        pprint(metrics)
    except Exception as exc:
        print(f"[Task 1 Error] Unable to compute risk metrics: {exc}")


def run_task2() -> None:
    """Task 2: Market data fetch."""
    try:
        print("\nTask 2 - Market Data Fetch")
        market_rows = fetch_market_data()
        format_table(market_rows)
    except Exception as exc:
        print(f"[Task 2 Error] Unable to fetch market data: {exc}")


def run_task3() -> None:
    """Task 3: AI portfolio explainer."""
    try:
        print("\nTask 3 - AI Portfolio Explainer")
        print("Raw LLM response:")
        explanation = explain_portfolio(PORTFOLIO, tone="beginner")
        print("\nParsed Output:")
        pprint(explanation)
    except Exception as exc:
        print(f"[Task 3 Error] Unable to generate AI explanation: {exc}")


def run_task4() -> None:
    """Task 4: Portfolio temperature using runway from Task 1."""
    try:
        print("\nTask 4 - Portfolio Temperature")
        metrics = compute_risk_metrics(PORTFOLIO)
        runway_months = float(metrics["severe_crash"]["runway_months"])
        score, label = compute_temperature(PORTFOLIO, runway_months)
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


def _run_selected_task(task: int) -> None:
    """Dispatch selected task number."""
    task_map = {
        1: run_task1,
        2: run_task2,
        3: run_task3,
        4: run_task4,
    }
    runner = task_map.get(task)
    if runner is None:
        print(f"Invalid task '{task}'. Choose 1, 2, 3, or 4.")
        return
    runner()


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run fintech CLI tasks.")
    parser.add_argument(
        "--task",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run a specific task directly (1-4).",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for interactive and argument-based execution."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = _parse_args()

    if args.task is not None:
        _run_selected_task(args.task)
        return

    _print_menu()
    choice = input("Enter task number (1-4): ").strip()
    try:
        _run_selected_task(int(choice))
    except ValueError:
        print(f"Invalid input '{choice}'. Please enter a number from 1 to 4.")


if __name__ == "__main__":
    main()
