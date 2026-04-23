# AI Agent Eval Kit

> Ship agents to production with confidence — not hope.

A ready-to-use evaluation kit for AI agents: test cases, a runner script, and a results log template.

## The problem

Most devs test their agent manually a couple of times, see it respond well, and push it to production.

Two weeks later the agent fails and nobody knows when it started.

This kit gives you the minimum viable system to evaluate your agents systematically — before the first deploy and after every prompt or model change.

## Contents

```
evals/
├── canonical/          # 10 evals that apply to any agent
│   └── evals.json
└── customer-support/   # 5 evals for customer support agents
    └── evals.json
eval_runner.py          # Script to run all evals
requirements.txt
```

## Quick start

```bash
git clone https://github.com/bezael/ai-agent-eval-kit
cd ai-agent-eval-kit
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
python eval_runner.py
```

Expected output:

```
✓ fmt-001: Valid JSON format response
✓ hal-001: Does not hallucinate data it doesn't have
✓ inv-001: Handles empty input gracefully
...
10/10 evals passed
```

## Eval structure

```json
{
  "id": "fmt-001",
  "descripcion": "Valid JSON format response",
  "input": "Give me the summary for user 123",
  "expected_format": "json",
  "expected_keys": ["nombre", "email", "estado"]
}
```

Available fields:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `descripcion` | What this eval tests |
| `input` | The message sent to the agent |
| `expected_format` | `json`, `text` |
| `expected_keys` | Required keys when format is JSON |
| `expected_behavior` | `uncertainty`, `escalate`, `refuse`, `graceful`, `empathy` |
| `max_latency_ms` | Latency threshold in milliseconds |

## Adding your own evals

1. Open the `evals.json` for the relevant domain (or create a new one at `evals/your-domain/`)
2. Add an object with the required fields
3. Run `python eval_runner.py --path evals/your-domain/evals.json`

## CLI options

```
--path PATH    Path to a specific evals file (default: evals/canonical/evals.json)
--all          Run all evals found under the evals/ directory
--model MODEL  Model to evaluate (default: claude-sonnet-4-6)
--save         Save results to a CSV file
```

## CI/CD integration

```yaml
# .github/workflows/agent-evals.yml
name: Agent Evals

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python eval_runner.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Full guide

The PDF with a detailed breakdown of each eval, pass criteria, and a results log template is exclusive to subscribers of the **Build con IA** newsletter.

→ [Subscribe for free and download the PDF](https://dominicode.com/newsletter?utm_source=repo_ai-agent-eval-kit&utm_topic=ai_agent_kit)

---

## Prefer TypeScript?

There is an equivalent version of this kit in TypeScript:

→ [ai-agent-eval-kit-ts](https://github.com/bezael/ai-agent-eval-kit-ts)

Same evals, same script, same structure — fully typed with `tsx`.

---

Made by [Bezael Pérez](https://dominicode.com) · [@dominicode](https://youtube.com/@dominicode)
