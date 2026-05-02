# Timecell Intern Technical Test — Chirag Katkoriya

> AI-assisted wealth management toolkit for portfolio risk analysis, crash simulation, live market data, and intelligent financial insights — built in Python for the **Timecell.ai Summer Internship 2025** assessment.

This repo is my submission for the four-task technical test. Everything ships as a single CLI (`main.py`) with a small, well-separated package layout under `src/` so each task can be evaluated in isolation or as one cohesive product.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Task 1 — Portfolio Risk Calculator](#task-1--portfolio-risk-calculator-30-pts)
4. [Task 2 — Live Market Data Fetch](#task-2--live-market-data-fetch-20-pts)
5. [Task 3 — AI-Powered Portfolio Explainer](#task-3--ai-powered-portfolio-explainer-30-pts)
6. [Task 4 — Portfolio Temperature (The Open Problem)](#task-4--portfolio-temperature-the-open-problem-20-pts)
7. [How I Used AI Tools](#how-i-used-ai-tools)
8. [Design Choices & Trade-offs](#design-choices--trade-offs)
9. [What Was Hardest](#what-was-hardest)

---

## Quick Start

### 1. Clone & enter the repo

```bash
git clone https://github.com/<your-username>/timecell-intern-Chirag-Katkoriya.git
cd timecell-intern-Chirag-Katkoriya
```

### 2. Create a virtual environment (Python 3.10+)

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API key (only needed for Task 3)

Create a `.env` file in the repo root:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

You can grab a free key from [Google AI Studio](https://aistudio.google.com/). Tasks 1, 2, and 4 work without any API key.

### 5. Run the CLI

**Fully interactive menu** — asks you for the portfolio file, the task, and (for Task 3) the tone:

```bash
python main.py
# Portfolio JSON path (Enter for built-in default, or e.g. samples/conservative.json): samples/aggressive.json
# Select Task: 1 -> ...  2 -> ...  3 -> ...  4 -> ...
# Enter task number (1-4): 3
# Choose tone for Task 3 [beginner / experienced / expert] (default: beginner): expert
```

If you give a path that doesn't exist or fails validation, the prompt re-asks instead of crashing. Press Enter at the portfolio prompt to use the built-in default.

Run a specific task directly:

```bash
python main.py --task 1   # Portfolio Risk Calculator
python main.py --task 2   # Live Market Data Fetch
python main.py --task 3   # AI Portfolio Explainer
python main.py --task 4   # Portfolio Temperature
```

**Use your own portfolio** (any valid JSON file matching the schema in `samples/default.json`):

```bash
python main.py --task 1 --portfolio samples/conservative.json
python main.py --task 4 --portfolio samples/aggressive.json
```

**Switch the LLM tone for Task 3** (bonus feature). Two ways:

```bash
# 1. Pass --tone on the command line (skips the prompt):
python main.py --task 3 --portfolio samples/aggressive.json --tone expert
python main.py --task 3 --portfolio samples/conservative.json --tone beginner
```

```bash
# 2. Interactive menu — picking Task 3 will ask you which tone to use.
python main.py
# Select Task: 3
# Choose tone for Task 3 [beginner / experienced / expert] (default: beginner): expert
```

The interactive tone prompt only fires when Task 3 is selected; Tasks 1, 2, and 4 don't use tone, so they aren't asked.

The repo ships three sample portfolios in `samples/`:

| File | Profile |
| --- | --- |
| `samples/default.json` | The original PDF example (1 Cr, 80K expenses) |
| `samples/conservative.json` | 50 L · 60K expenses · FD-heavy, low risk |
| `samples/aggressive.json` | 25 L · 1 L expenses · 95% crypto + small-cap, high risk |

---

## Project Structure

```text
timecell-intern-Chirag-Katkoriya/
├── main.py                          # Unified CLI: --task, --portfolio, --tone, interactive menu
├── requirements.txt                 # yfinance, requests, google-genai, python-dotenv
├── .env                             # GEMINI_API_KEY (gitignored)
├── .gitignore
├── README.md
├── samples/                         # Drop-in JSON portfolios for the --portfolio flag
│   ├── default.json                 # PDF example (1 Cr, 80K expenses)
│   ├── conservative.json            # FD-heavy, low risk
│   └── aggressive.json              # 95% crypto + small-cap, high risk
└── src/
    ├── risk/
    │   ├── metrics.py               # Task 1 — severe + moderate crash metrics, allocation chart
    │   └── temperature.py           # Task 4 — portfolio temperature score (open problem)
    ├── classification/
    │   └── market_data.py           # Task 2 — yfinance + CoinGecko fetch and CLI table
    └── ai/
        └── explainer.py             # Task 3 — Gemini-powered explainer + critique loop
```

Each module has a single responsibility, pure helper functions, and validation at the boundary so the rest of the code can assume clean inputs.

---

## Task 1 — Portfolio Risk Calculator (30 pts)

**File:** `src/risk/metrics.py`

`compute_risk_metrics(portfolio)` returns a dictionary containing **two scenarios side by side**:

- `severe_crash` — uses each asset's full `expected_crash_pct`
- `moderate_crash` — bonus scenario where every crash magnitude is halved (× 0.5)

Each scenario reports:

| Field | Meaning |
| --- | --- |
| `post_crash_value` | Total INR value remaining after the modeled crash |
| `runway_months` | `post_crash_value / monthly_expenses_inr` |
| `ruin_test` | `'PASS'` if runway > 12 months, else `'FAIL'` |
| `largest_risk_asset` | Asset with the highest `allocation_pct × abs(expected_crash_pct)` |
| `concentration_warning` | `True` if any single asset exceeds 40% allocation |

### Edge cases handled

- Portfolio dict missing required fields → `ValueError`
- Allocations not summing to ~100% (±1%) → `ValueError`
- Negative or non-numeric values → `ValueError`
- Booleans masquerading as numbers (`isinstance(True, int) == True` in Python) → explicitly excluded
- `monthly_expenses_inr == 0` → runway returns `inf` instead of dividing by zero
- Crashes that would push an asset below zero → floored at 0 (`max(0, 1 + crash/100)`) because an asset cannot owe you money

### Bonus features

- ✅ **Side-by-side scenarios** (severe vs moderate) returned in one call
- ✅ **CLI bar chart** auto-printed by `python main.py --task 1` via `print_allocation_chart(portfolio)`. Pure Unicode/ASCII (no matplotlib), with an ASCII fallback for non-UTF terminals.

### Example output (severe + moderate, real run)

```text
Task 1 - Portfolio Risk Calculator
{'moderate_crash': {'concentration_warning': False,
                    'largest_risk_asset': 'BTC',
                    'post_crash_value': 7850000.0,
                    'ruin_test': 'PASS',
                    'runway_months': 98.12},
 'severe_crash': {'concentration_warning': False,
                  'largest_risk_asset': 'BTC',
                  'post_crash_value': 5700000.0,
                  'ruin_test': 'PASS',
                  'runway_months': 71.25}}

Allocation breakdown:
BTC      ##########                         30%
NIFTY50  #############                      40%
GOLD     #######                            20%
CASH     ###                                10%
```

The math checks out: BTC contributes the most "crash damage" (30% × 80% = 2400) so it is the largest risk asset; NIFTY50 sits at exactly 40% which is **not** `> 40%`, so `concentration_warning` is correctly `False`.

---

## Task 2 — Live Market Data Fetch (20 pts)

**File:** `src/classification/market_data.py`

Fetches three real, live prices from **free public APIs**:

| Asset | Source | Why |
| --- | --- | --- |
| Bitcoin (BTC) | [CoinGecko](https://www.coingecko.com/en/api) public endpoint | No key required, satisfies the crypto requirement |
| NIFTY 50 (`^NSEI`) | [Yahoo Finance](https://pypi.org/project/yfinance/) via `yfinance` | Satisfies the index/stock requirement |
| Gold Futures (`GC=F`) | Yahoo Finance | Adds an additional commodity dimension relevant to Indian wealth |

### Reliability behavior

- Each fetch is wrapped in its own `try/except`. **One failure never crashes the others.**
- Network timeouts are bounded (`timeout=10`).
- HTTP errors are surfaced via `response.raise_for_status()` and logged with the asset name.
- Failed assets still appear in the table as `N/A` so the user sees what was attempted.
- Timestamps are rendered in **IST** using `zoneinfo.ZoneInfo("Asia/Kolkata")` — important for an Indian wealth product.

### Example output (real run)

```text
Asset Prices - fetched at 2026-04-30 21:18:09 IST

+---------+----------+----------+
| Asset   | Price    | Currency |
+---------+----------+----------+
| BITCOIN | 76360.00 | USD      |
| ^NSEI   | 23997.55 | INR      |
| GC=F    | 4630.30  | USD      |
+---------+----------+----------+
```

The table renderer auto-detects whether the terminal supports UTF-8 box-drawing characters; if not, it falls back to plain `+`, `-`, and `|` — useful for Windows terminals and CI logs.

---

## Task 3 — AI-Powered Portfolio Explainer (30 pts)

**Files:** `src/ai/explainer.py` (logic) + `main.py::run_task3` (CLI wrapper).
**Provider chosen:** **Google Gemini** (`gemini-3-flash-preview`) via the official `google-genai` SDK.

### Why Gemini?

- Free tier with a generous quota — easy for a reviewer to reproduce without paying.
- Native `response_mime_type="application/json"` flag forces structured JSON output, which removes a whole class of post-processing bugs.
- Low latency on the Flash family — keeps the CLI snappy.

### The script accepts arbitrary portfolios (PDF requirement)

`explain_portfolio(portfolio, tone)` is a pure function that takes any dict matching the schema, and the CLI exposes this via `--portfolio path/to/file.json`. There is **no hardcoded portfolio in the call path** — the constant `DEFAULT_PORTFOLIO` is only used when the user passes nothing. Every input is validated through `validate_portfolio()` (the same validator Task 1 uses) before it ever reaches the LLM, so a malformed file fails loudly with a readable error rather than silently returning garbage.

Try it:

```bash
python main.py --task 3 --portfolio samples/conservative.json --tone beginner
python main.py --task 3 --portfolio samples/aggressive.json   --tone expert
```

The two runs produce visibly different summaries and verdicts because the LLM is fed completely different numbers — proof that the script genuinely consumes the input file.

### Prompt engineering approach

The prompt is **deterministic, structured, and tone-aware**. It is built in three layers:

1. **System role** — frames the model as a thoughtful financial advisor:
   ```text
   "You are a thoughtful financial advisor explaining portfolio risk to a client."
   ```
2. **Tone modifier** — three switchable tones (`beginner`, `experienced`, `expert`) implemented as a small dictionary of style instructions. This is the **bonus "configurable tone"** feature.
3. **Schema lock** — the prompt explicitly demands a JSON object with exactly four fields:
   ```json
   {
     "summary": "...",
     "what_is_good": "...",
     "what_to_improve": "...",
     "verdict": "Aggressive|Balanced|Conservative"
   }
   ```

`temperature=0.2` is set on the API call so output stays consistent across runs.

### What I tried, what worked, what I changed

| Iteration | Approach | Result |
| --- | --- | --- |
| v1 | Free-form prompt: "Explain this portfolio's risk." | Output was floral, inconsistent, sometimes used jargon, hard to parse |
| v2 | Asked for "summary, good, bad, verdict" in plain text with bullet points | Better, but parsing was fragile — model occasionally added headings or markdown |
| v3 (current) | **Schema-locked JSON** + `response_mime_type="application/json"` + tone instructions + low temperature | Consistent, parseable, tone-appropriate. ~100% parse success in my testing. |

The biggest single win was switching to `response_mime_type="application/json"`. It eliminated markdown fences, preambles ("Sure! Here's…"), and trailing commentary in one line of code.

### Robustness

- `parse_response()` strips stray ` ```json ` fences (defensive — even though the MIME flag should prevent them)
- Validates every required field is present and is a string
- Validates `verdict` is one of the three allowed values
- If the API call or parsing fails, `_fallback_pair()` returns `(raw_json_string, parsed_dict)` so the function's `tuple[str, dict]` contract is preserved on the error path too
- `critique_explanation()` implements the **bonus second LLM call** and is invoked automatically by `run_task3()` after the main explanation

### Sample output (real run, abridged)

The CLI prints the raw response, the parsed structure, **and** the second-pass critique:

```text
Task 3 - AI Portfolio Explainer
Raw LLM response:
{
  "summary": "You have built a strong savings pot of 1 Crore... If a major
  market storm hits, your 1 Crore could suddenly shrink to 57 Lakhs...",
  "what_is_good": "You have been smart enough to keep 10 Lakhs in cash and
  20 Lakhs in gold. This acts like a life jacket...",
  "what_to_improve": "Right now, 70% of your money is in things that can
  drop in value very quickly, especially Bitcoin and the stock market...",
  "verdict": "Aggressive"
}

Parsed Output:
{'summary': '...', 'what_is_good': '...', 'what_to_improve': '...',
 'verdict': 'Aggressive'}

Critique of the explanation:
{
  "critique": [
    "The 43% drawdown estimate is mathematically sound but underestimates
     Bitcoin's specific tail risk (80%+ drawdowns).",
    "The explanation ignores inflation risk; 10 Lakhs in cash loses
     purchasing power over time.",
    "Misses 'Sequence of Returns Risk' — early crashes during the
     withdrawal phase can permanently deplete the portfolio.",
    "Misses concentration risk if the 70% is heavily Bitcoin-weighted."
  ]
}
```

---

## Task 4 — Portfolio Temperature (The Open Problem) (20 pts)

**File:** `src/risk/temperature.py`

### What I built and why

I built a **Portfolio Temperature** score — a single 0–100 number with a human label (`COLD`, `WARM`, `HOT`, `VERY HOT`) that fuses **market structural risk** with **personal life runway**.

This directly maps to the language Timecell uses on its website ("portfolio temperature"). The motivation: most retail risk metrics either describe the market (volatility, drawdown) **or** describe the person (savings, expenses) — never both. A 1-Cr portfolio that is 80% BTC is dangerous for someone with ₹50K monthly expenses, but catastrophic for someone with ₹5L. A single number that captures both is something a wealth advisor can actually act on.

### How the score is built

```text
temperature = 0.6 × crash_severity   +   0.4 × runway_penalty
```

- **`crash_severity`** — sum of `allocation_pct × abs(expected_crash_pct) / 100` across assets, clamped to 0–100. Captures structural downside.
- **`runway_penalty`** — 0 if runway ≥ 24 months, scaling linearly up to 50 as runway falls toward 0. Captures personal vulnerability.
- The 60/40 weighting is intentional: portfolio structure dominates, but life runway has a real say.

### Output (real run)

```text
Task 4 - Portfolio Temperature
Using severe-crash runway from Task 1: 71.25 months
Temperature Score: 25.80
Temperature Label: COLD
```

Math walkthrough for the sample portfolio:

- `crash_severity = (30×80 + 40×40 + 20×15 + 10×0) / 100 = 43.0`
- `runway = 71.25 ≥ 24` → `runway_penalty = 0`
- `temperature = 0.6 × 43.0 + 0.4 × 0 = 25.80` → label `COLD`

The runway penalty here is 0 because the portfolio still survives a severe crash for 5+ years. If monthly expenses doubled, runway would halve and the label would shift toward `WARM` — which is exactly the kind of personalised insight the metric is designed to surface.

The module also exposes `print_temperature_summary()` which lists the **top crash-risk contributors** (by `allocation × crash magnitude`) so the user understands *why* the temperature is what it is — not just the score.

### Why this is worth building

A score on its own is decoration. A score with **drivers** is a decision. That's the difference between a dashboard and an advisor — and it's the gap Timecell is trying to close.

---

## How I Used AI Tools

I used **Cursor + ChatGPT** throughout, deliberately and transparently:

- **Scaffolding & boilerplate** — let the AI generate first drafts of validation logic, table renderers, and argparse setup, then trimmed everything I didn't need.
- **Edge-case brainstorming** — asked "what could break this function?" to AI so that it could include all edge cases and then I reviewed it.
- **Prompt iteration for Task 3** — I literally pasted my draft prompt into a separate ChatGPT chat and asked it to roleplay as the model and critique its own response.
- **Code review** — after each task, I asked the AI to point out unclear naming and dead code. Several function renames in `metrics.py` came from that pass.

---

## Design Choices & Trade-offs

- **One CLI, four tasks.** A unified `main.py` keeps the reviewer experience simple — one command runs everything. Each task is also independently importable from `src/` for testing.
- **Validation at boundaries.** `validate_portfolio()` is the only function that produces normalized data; everything downstream assumes clean input. This avoids defensive checks scattered through the codebase.
- **Pure functions where possible.** `compute_post_crash_value`, `compute_runway`, `compute_temperature` etc. are pure — they take inputs, return outputs, no I/O. That makes them trivial to test.
- **Side-by-side crash scenarios as the default return shape.** Even though only one was required, returning both severe and moderate makes the API more useful with negligible cost.
- **UTF-8 fallbacks.** Both the table renderer and the bar chart degrade to plain ASCII on terminals that don't support box-drawing or block characters — important on Windows PowerShell.


### Things I'd build next given more time

- A proper `pytest` suite (current validation is hand-tested via the CLI)
- A small FastAPI wrapper so the same logic can power a web UI
- Caching for the market data fetch (e.g. 60-second TTL) to be polite to free APIs


---

## What Was Hardest

The hardest part includes **Task 3's prompt engineering**, not the code. Getting the model to return *parseable, consistent, on-tone* output — every time, across portfolios — took more iteration than other tasks. The breakthroughs were (1) using Gemini's `response_mime_type="application/json"` instead of trying to wrangle markdown, (2) lowering temperature to 0.2 for determinism. Some of the Gemini Models were not giving repsonse properly or taking too much time, due to excess traffic and hence I had to change the model to a different one, gemini-3-preview, I got this model by checking through the official documentation.

The other thing was a small but real one: deciding **how to weight** structural vs personal risk in Task 4. There is no objectively correct answer — 60/40 is a defensible default, but a real product would let the user tune it. Recognizing that the *interface* matters more than the *exact number* was the lesson.

---

**Submission for:** Timecell.ai Summer Internship 2025 Technical Assessment
**Author:** Chirag Katkoriya
