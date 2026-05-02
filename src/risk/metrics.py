"""Portfolio risk metrics for severe and moderate crash scenarios."""

from __future__ import annotations

from math import isclose
import sys
from typing import Any


def _is_number(value: Any) -> bool:
    """Return True for int/float values, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_portfolio_fields(portfolio: dict[str, Any]) -> None:
    """Ensure required top-level fields are present."""
    for field_name in ("total_value_inr", "monthly_expenses_inr", "assets"):
        if field_name not in portfolio:
            raise ValueError(f"missing required field: {field_name}")


def _validate_asset_fields(asset: dict[str, Any]) -> None:
    """Ensure each asset has all required fields."""

    for field_name in ("name", "allocation_pct", "expected_crash_pct"):
        if field_name not in asset:
            raise ValueError(f"missing asset field: {field_name}")


def _normalize_asset(asset: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one asset row."""
    _validate_asset_fields(asset)
    name = asset["name"]
    allocation_pct = asset["allocation_pct"]
    expected_crash_pct = asset["expected_crash_pct"]

    if not isinstance(name, str) or not name.strip():
        raise ValueError("asset name must be a non-empty string")
    
    if not _is_number(allocation_pct) or not _is_number(expected_crash_pct):
        raise ValueError("asset allocation_pct and expected_crash_pct must be numeric")
    
    if float(allocation_pct) < 0:
        raise ValueError("asset allocation_pct cannot be negative")
    return {
        "name": name.strip(),
        "allocation_pct": float(allocation_pct),
        "expected_crash_pct": float(expected_crash_pct),
    }


def _normalize_assets(assets: list[Any]) -> list[dict[str, Any]]:
    """Validate the asset list and normalize all entries."""

    if not isinstance(assets, list) or not assets:
        raise ValueError("assets must be a non-empty list")
    
    normalized_assets: list[dict[str, Any]] = []

    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("each asset must be a dictionary")
        normalized_assets.append(_normalize_asset(asset))

    allocation_total = sum(asset["allocation_pct"] for asset in normalized_assets)

    if not isclose(allocation_total, 100.0, abs_tol=1.0):
        raise ValueError("asset allocations must sum to approximately 100%")
    return normalized_assets


def validate_portfolio(portfolio: dict[str, Any]) -> dict[str, Any]:
    """Validate portfolio payload before financial calculations."""
    if not isinstance(portfolio, dict):
        raise ValueError("portfolio must be a dictionary")
    
    _require_portfolio_fields(portfolio)

    total_value = portfolio["total_value_inr"]

    monthly_expenses = portfolio["monthly_expenses_inr"]

    if not _is_number(total_value) or not _is_number(monthly_expenses):
        raise ValueError("total_value_inr and monthly_expenses_inr must be numeric")
    
    if float(total_value) < 0 or float(monthly_expenses) < 0:
        raise ValueError("total_value_inr and monthly_expenses_inr must be non-negative")
    
    return {
        "total_value_inr": float(total_value),
        "monthly_expenses_inr": float(monthly_expenses),
        "assets": _normalize_assets(portfolio["assets"]),
    }


def compute_post_crash_value(portfolio: dict[str, Any]) -> float:
    """Compute total remaining value after modeled crashes."""
    
    total_value = portfolio["total_value_inr"]
    post_crash_value = 0.0
    for asset in portfolio["assets"]:
        asset_value = total_value * (asset["allocation_pct"] / 100.0)
       
        survival_factor = max(0.0, 1.0 + asset["expected_crash_pct"] / 100.0)
        post_crash_value += asset_value * survival_factor
    return post_crash_value


def compute_runway(post_crash_value: float, monthly_expenses: float) -> float:
    """Convert remaining capital into expense runway (months)."""
    if monthly_expenses == 0:
        return float("inf")
    return post_crash_value / monthly_expenses


def find_largest_risk_asset(portfolio: dict[str, Any]) -> str:
    """Return the asset with highest allocation * crash magnitude."""
    largest_name = ""
    largest_score = float("-inf")
    for asset in portfolio["assets"]:
        # Larger positions with deeper drawdowns dominate crash damage.
        risk_score = asset["allocation_pct"] * abs(asset["expected_crash_pct"])
        if risk_score > largest_score:
            largest_score = risk_score
            largest_name = asset["name"]
    return largest_name


def check_concentration(portfolio: dict[str, Any]) -> bool:
    """Flag concentration risk when any asset exceeds 40% allocation."""
    return any(asset["allocation_pct"] > 40.0 for asset in portfolio["assets"])


def scale_crash(portfolio: dict[str, Any], factor: float) -> dict[str, Any]:
    """Scale each asset crash percentage for alternate scenarios."""
    scaled_assets: list[dict[str, Any]] = []
    for asset in portfolio["assets"]:
        scaled_assets.append(
            {
                "name": asset["name"],
                "allocation_pct": asset["allocation_pct"],
                "expected_crash_pct": asset["expected_crash_pct"] * factor,
            }
        )
    return {
        "total_value_inr": portfolio["total_value_inr"],
        "monthly_expenses_inr": portfolio["monthly_expenses_inr"],
        "assets": scaled_assets,
    }


def _build_scenario_metrics(portfolio: dict[str, Any]) -> dict[str, Any]:
    """Build output for one crash scenario."""
    raw_value = compute_post_crash_value(portfolio)
    raw_runway = compute_runway(raw_value, portfolio["monthly_expenses_inr"])
    return {
        "post_crash_value": round(raw_value, 2),
        "runway_months": round(raw_runway, 2),
        "ruin_test": "PASS" if raw_runway > 12 else "FAIL",
        "largest_risk_asset": find_largest_risk_asset(portfolio),
        "concentration_warning": check_concentration(portfolio),
    }


def print_allocation_chart(portfolio: dict[str, Any]) -> None:
    """Print a simple ASCII/Unicode allocation bar chart for CLI."""
    validated = validate_portfolio(portfolio)
    name_width = max(len(asset["name"]) for asset in validated["assets"])

    block = "█" if (sys.stdout.encoding or "").lower().startswith("utf") else "#"

    for asset in validated["assets"]:
        bar_len = max(1, int(round(asset["allocation_pct"] / 3.0)))
        bar = block * bar_len
        print(f"{asset['name']:<{name_width}}  {bar:<34} {asset['allocation_pct']:.0f}%")


def compute_risk_metrics(portfolio: dict[str, Any]) -> dict[str, Any]:
    """Compute severe and moderate crash metrics for a portfolio."""

    validated = validate_portfolio(portfolio)
    severe = _build_scenario_metrics(validated)
    moderate = _build_scenario_metrics(scale_crash(validated, 0.5))

    return {"severe_crash": severe, "moderate_crash": moderate}
