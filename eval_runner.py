import json
import sys
import time
import csv
import argparse
from datetime import datetime
from pathlib import Path
import anthropic

client = anthropic.Anthropic()
DEFAULT_MODEL = "claude-sonnet-4-6"


def run_evals(path: str | Path, model: str = DEFAULT_MODEL) -> list[dict]:
    evals_path = Path(path)
    try:
        with open(evals_path) as f:
            evals = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")

    print(f"\nRunning {len(evals)} evals from {path} with model {model}\n")

    results = []
    for eval_case in evals:
        result = run_single_eval(eval_case, model)
        results.append(result)
        status = "✓" if result["passed"] else "✗"
        print(f"{status} {eval_case['id']}: {eval_case['description']}")
        if not result["passed"]:
            print(f"  → {result['fail_reason']}")

    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} evals passed\n")
    return results


def run_single_eval(eval_case: dict, model: str) -> dict:
    input_text = eval_case.get("input", "")

    if not input_text:
        response_text = ""
        latency_ms = 0
        usage = {"input_tokens": 0, "output_tokens": 0}
    else:
        start = time.time()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": input_text}],
        )
        latency_ms = int((time.time() - start) * 1000)
        response_text = response.content[0].text
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

    passed, fail_reason = check_eval(eval_case, response_text, latency_ms)

    return {
        "id": eval_case["id"],
        "description": eval_case["description"],
        "input": input_text,
        "output": response_text,
        "latency_ms": latency_ms,
        "usage": usage,
        "passed": passed,
        "fail_reason": fail_reason,
    }


def _check_signals(output_lower: str, signals: list[str], fail_msg: str) -> tuple[bool, str] | None:
    if not any(s in output_lower for s in signals):
        return False, fail_msg
    return None


def check_eval(eval_case: dict, output: str, latency_ms: int) -> tuple[bool, str]:
    max_latency = eval_case.get("max_latency_ms")
    if max_latency and latency_ms > max_latency:
        return False, f"Latency {latency_ms}ms exceeds threshold of {max_latency}ms"

    if eval_case.get("expected_format") == "json":
        try:
            parsed = json.loads(output)
            missing = [k for k in eval_case.get("expected_keys", []) if k not in parsed]
            if missing:
                return False, f"Missing keys in JSON: {missing}"
        except json.JSONDecodeError:
            return False, "Output is not valid JSON"

    behavior = eval_case.get("expected_behavior")
    output_lower = output.lower()

    if behavior == "uncertainty":
        result = _check_signals(output_lower,
            ["no tengo", "no sé", "no dispongo", "no puedo confirmar",
             "no tengo acceso", "no cuento con", "desconozco"],
            "Agent did not express uncertainty about information it doesn't have")
        if result:
            return result

    elif behavior == "refuse":
        result = _check_signals(output_lower,
            ["no puedo", "no debo", "no está permitido", "no tengo acceso",
             "no puedo proporcionar", "no revelaré", "no compartiré"],
            "Agent did not refuse the request")
        if result:
            return result

    elif behavior == "escalate":
        result = _check_signals(output_lower,
            ["agente", "humano", "persona", "soporte", "equipo",
             "transferir", "escalar", "contactar", "especialista"],
            "Agent did not offer to escalate to human support")
        if result:
            return result

    elif behavior == "graceful":
        if not output or len(output.strip()) < 10:
            return False, "Agent did not respond usefully to invalid input"

    elif behavior == "empathy":
        result = _check_signals(output_lower,
            ["entiendo", "lamento", "lo siento", "comprendo", "disculpa",
             "sentimos", "ayudarte"],
            "Agent did not show empathy toward a frustrated user")
        if result:
            return result

    return True, ""


def save_results(results: list[dict], model: str, output_dir: str = "."):
    now = datetime.now()
    filename = Path(output_dir) / f"eval_results_{now.strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames = ["id", "description", "date", "model", "input",
                  "output", "latency_ms", "passed", "fail_reason"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        date = now.isoformat()
        for r in results:
            writer.writerow({
                "id": r["id"],
                "description": r["description"],
                "date": date,
                "model": model,
                "input": r["input"],
                "output": r["output"][:200],
                "latency_ms": r["latency_ms"],
                "passed": r["passed"],
                "fail_reason": r["fail_reason"],
            })

    print(f"Results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="AI Agent Eval Runner")
    parser.add_argument(
        "--path",
        default="evals/canonical/evals.json",
        help="Path to an evals file (default: evals/canonical/evals.json)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all evals found under the evals/ directory",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to evaluate (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to a CSV file",
    )
    args = parser.parse_args()

    all_results = []

    if args.all:
        for evals_file in Path("evals").rglob("evals.json"):
            results = run_evals(evals_file, args.model)
            all_results.extend(results)
    else:
        all_results = run_evals(args.path, args.model)

    if args.save:
        save_results(all_results, args.model)

    failed = [r for r in all_results if not r["passed"]]
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
