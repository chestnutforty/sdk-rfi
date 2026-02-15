# sdk-rfi

Python SDK for the RAND Forecasting Initiative (RFI) API.

RFI (formerly INFER) is a crowdsourced forecasting platform run by RAND Corporation,
powered by the Cultivate Labs platform. It provides access to policy-relevant forecasting
questions, crowd predictions, and forecaster comments/rationales.

## Installation

```bash
pip install sdk-rfi
# or
uv add sdk-rfi
```

## Quick Start

```python
from sdk_rfi import Client

# Set environment variables: RFI_EMAIL, RFI_PASSWORD
client = Client()

# List active questions
questions = client.questions.list()
for q in questions.questions:
    print(f"{q.id}: {q.name}")

# Get a specific question with answers and probabilities
question = client.questions.get(1234)
for answer in question.answers or []:
    print(f"  {answer.name}: {answer.probability_formatted}")

# Get individual forecasts for a question
forecasts = client.prediction_sets.list(question_id=1234)
for ps in forecasts.prediction_sets:
    print(f"  {ps.membership_username}: {ps.rationale}")

# Get comments
comments = client.comments.list(commentable_id=1234, commentable_type="Forecast::Question")
```

## Backtesting

All data-fetching methods support `cutoff_date` for backtesting:

```python
# Get data as it was available on 2025-01-01
questions = client.questions.list(cutoff_date="2025-01-01")
forecasts = client.prediction_sets.list(question_id=1234, cutoff_date="2025-01-01")
```

## Authentication

The RFI API requires OAuth2 authentication. Set these environment variables:

- `RFI_EMAIL` - Your RFI account email
- `RFI_PASSWORD` - Your RFI account password

Or pass them directly:

```python
client = Client(email="user@example.com", password="secret")
```

## Available Resources

| Resource | Methods | Backtestable |
|----------|---------|-------------|
| `questions` | `list()`, `get(id)` | Yes |
| `prediction_sets` | `list()` | Yes |
| `comments` | `list()` | Yes |

## Data Leakage Notes

- `Answer.probability` fields reflect the **current** crowd forecast, not historical
- Use `prediction_sets.list(cutoff_date=...)` to get individual forecasts before a date
- `predictions_count` and `predictors_count` are always current totals
