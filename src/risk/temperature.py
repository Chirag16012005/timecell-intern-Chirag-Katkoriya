"""Portfolio temperature scoring for intuitive risk communication."""

from __future__ import annotations

import sys
from typing import Any

from src.risk.metrics import validate_portfolio


def _clamp(value: float, low: float, high: float) -> float:
    """Keep numeric values inside a fixed range."""
    return max(low, min(high, value))


def compute_crash_severity(portfolio: dict[str, Any]) -> float:
    """Estimate structural downside risk from allocation and crash depth."""
    validated = validate_portfolio(portfolio)
   
    raw_score = sum(
        asset["allocation_pct"] * abs(asset["expected_crash_pct"]) / 100.0
        for asset in validated["assets"]
    )
    return _clamp(raw_score, 0.0, 100.0)


def compute_runway_penalty(runway_months: float) -> float:
    """Convert personal cash runway into a risk penalty score."""
   
    if runway_months >= 24:
        return 0.0
    if runway_months <= 0:
        return 50.0
    return _clamp(50.0 * (1.0 - runway_months / 24.0), 0.0, 50.0)


def _label_for_score(score: float) -> str:
    """Map numeric temperature to a simple human-readable band."""
    if score < 30:
        return "COLD"
    if score < 60:
        return "WARM"
    if score < 80:
        return "HOT"
    return "VERY HOT"


def compute_temperature(portfolio: dict[str, Any], runway_months: float) -> tuple[float, str]:
    """Combine market crash risk and runway risk into one temperature."""
    severity = compute_crash_severity(portfolio)
    runway_penalty = compute_runway_penalty(runway_months)
    
    score = _clamp(0.6 * severity + 0.4 * runway_penalty, 0.0, 100.0)
    return round(score, 2), _label_for_score(score)


def temperature_result(portfolio: dict[str, Any], runway_months: float) -> dict[str, Any]:
    """Return the requested dictionary output shape for APIs/UI."""
    score, label = compute_temperature(portfolio, runway_months)
    return {"temperature_score": score, "temperature_label": label}


def _top_risk_contributors(portfolio: dict[str, Any], top_n: int = 2) -> list[str]:
    """List top contributors by allocation x crash magnitude."""
    validated = validate_portfolio(portfolio)
    ranked = sorted(
        validated["assets"],
        key=lambda a: a["allocation_pct"] * abs(a["expected_crash_pct"]),
        reverse=True,
    )
    return [asset["name"] for asset in ranked[:top_n]]


def print_temperature_summary(portfolio: dict[str, Any], runway_months: float) -> None:
    """Print an interview-friendly explanation of temperature and drivers."""
    score, label = compute_temperature(portfolio, runway_months)

    emoji_map = {"COLD": "🧊", "WARM": "🌤️", "HOT": "🔥", "VERY HOT": "🚨"}

    if not (sys.stdout.encoding or "").lower().startswith("utf"):
        emoji_map = {k: "" for k in emoji_map}

    top_assets = ", ".join(_top_risk_contributors(portfolio))
    runway_text = f"{runway_months:.1f} months" if runway_months >= 0 else "below 0 months"
    marker = f"{emoji_map[label]} " if emoji_map[label] else ""
    
    print(f"Portfolio Temperature: {marker}{label} ({score:.1f}/100)\n")
    print("Reason:")
    print(f"- Top crash-risk contributors: {top_assets}")
    print(f"- Estimated financial runway: {runway_text}")
