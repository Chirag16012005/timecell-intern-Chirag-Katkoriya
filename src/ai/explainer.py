"""LLM-backed portfolio risk explanation layer."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from google import genai

load_dotenv()


LOGGER = logging.getLogger(__name__)
SYSTEM_ROLE = "You are a thoughtful financial advisor explaining portfolio risk to a client."


def build_prompt(portfolio: dict[str, Any], tone: str) -> str:
    """Build a constrained prompt so model output is predictable and parseable."""
    tone_notes = {
        "beginner": "Use very simple language and one analogy to explain clearly in a lucid manner. Avoid finance jargon.",
        "experienced": "Use moderate detail and plain language with light terminology.",
        "expert": "Use precise technical language and discuss risk trade-offs directly.",
    }
    assets = portfolio.get("assets", [])
    lines = [f"- {a.get('name')}: {a.get('allocation_pct')}% allocation, crash {a.get('expected_crash_pct')}%" for a in assets]
    instructions = tone_notes.get(tone, tone_notes["beginner"])
    return (
        f"Tone: {tone}\n{instructions}\n\nPortfolio:\n"
        f"Total value (INR): {portfolio.get('total_value_inr')}\n"
        f"Monthly expenses (INR): {portfolio.get('monthly_expenses_inr')}\n"
        f"Asset breakdown:\n{chr(10).join(lines)}\n\n"
        "Be simple, honest, non-technical, and actionable. Avoid jargon.\n"
        "Return JSON ONLY in this exact schema:\n"
        '{"summary":"...","what_is_good":"...","what_to_improve":"...",'
        '"verdict":"Aggressive|Balanced|Conservative"}'
    )


def call_llm(prompt: str) -> str:
    """Call one provider with strict JSON output expectation."""
    model = "gemini-3-flash-preview"
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY or GOOGLE_API_KEY in environment")

    client = genai.Client(api_key=api_key)

    full_prompt = f"{SYSTEM_ROLE}\n\n{prompt}"

    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config={"temperature": 0.2, "response_mime_type": "application/json"},
    )
    if not response.text:
        raise ValueError("Gemini returned empty response text")
    return response.text


def parse_response(response: str) -> dict[str, str]:
    """Parse LLM JSON and enforce expected fields for downstream safety."""
    
    cleaned = response.strip().replace("```json", "").replace("```", "")
    parsed = json.loads(cleaned)
    required = ("summary", "what_is_good", "what_to_improve", "verdict")
    for field in required:
        if field not in parsed or not isinstance(parsed[field], str):
            raise ValueError(f"missing or invalid field: {field}")

    if parsed["verdict"] not in {"Aggressive", "Balanced", "Conservative"}:
        raise ValueError("verdict must be Aggressive, Balanced, or Conservative")

    return {field: parsed[field].strip() for field in required}


def _fallback_explanation() -> dict[str, str]:
    """Return safe fallback output when model/API/parsing fails."""
    return {
        "summary": "We could not generate a reliable explanation right now.",
        "what_is_good": "Your portfolio was received successfully for analysis.",
        "what_to_improve": "Please retry in a moment or review asset crash assumptions manually.",
        "verdict": "Balanced",
    }


def _fallback_pair() -> tuple[str, dict[str, str]]:
    """Return (raw_str, parsed_dict) tuple matching explain_portfolio's contract."""
    parsed = _fallback_explanation()
    raw = json.dumps(parsed, ensure_ascii=True, indent=2)
    return raw, parsed


def critique_explanation(explanation: dict[str, str]) -> str:
    """Ask the model to critique explanation quality for missing risks."""
    
    prompt = (
        "Critique this financial explanation for accuracy and missing risks. "
        "Keep it under 5 bullet points.\n\n"
        f"Explanation JSON:\n{json.dumps(explanation, ensure_ascii=True)}"
    )
    return call_llm(prompt)


def explain_portfolio(portfolio: dict[str, Any], tone: str = "beginner") -> tuple[str, dict[str, str]]:
    """Generate explanation and return (raw_response, parsed_dict)."""
    try:
        prompt = build_prompt(portfolio, tone)
        raw_response = call_llm(prompt)
        parsed = parse_response(raw_response)
        return raw_response, parsed
    except Exception as exc:
        LOGGER.error("Portfolio explanation failed: %s", exc)
        return _fallback_pair()
