import json
import time
import csv
import argparse
from datetime import datetime
from pathlib import Path
import anthropic

client = anthropic.Anthropic()
DEFAULT_MODEL = "claude-sonnet-4-6"


def run_evals(path: str, model: str = DEFAULT_MODEL) -> list[dict]:
    evals_path = Path(path)
    if not evals_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    with open(evals_path) as f:
        evals = json.load(f)

    print(f"\nEjecutando {len(evals)} evals desde {path} con modelo {model}\n")

    results = []
    for eval_case in evals:
        result = run_single_eval(eval_case, model)
        results.append(result)
        status = "✓" if result["passed"] else "✗"
        print(f"{status} {eval_case['id']}: {eval_case['descripcion']}")
        if not result["passed"]:
            print(f"  → {result['fail_reason']}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n{passed}/{len(results)} evals pasaron\n")
    return results


def run_single_eval(eval_case: dict, model: str) -> dict:
    input_text = eval_case.get("input", "")
    start = time.time()

    if not input_text:
        response_text = ""
        latency_ms = 0
        usage = {"input_tokens": 0, "output_tokens": 0}
    else:
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
        "descripcion": eval_case["descripcion"],
        "input": input_text,
        "output": response_text,
        "latency_ms": latency_ms,
        "usage": usage,
        "passed": passed,
        "fail_reason": fail_reason,
    }


def check_eval(eval_case: dict, output: str, latency_ms: int) -> tuple[bool, str]:
    # Latencia
    max_latency = eval_case.get("max_latency_ms")
    if max_latency and latency_ms > max_latency:
        return False, f"Latencia {latency_ms}ms supera el umbral de {max_latency}ms"

    # Formato JSON
    if eval_case.get("expected_format") == "json":
        try:
            parsed = json.loads(output)
            missing = [k for k in eval_case.get("expected_keys", []) if k not in parsed]
            if missing:
                return False, f"Faltan claves en el JSON: {missing}"
        except json.JSONDecodeError:
            return False, "El output no es JSON válido"

    # Comportamiento esperado
    behavior = eval_case.get("expected_behavior")
    if behavior == "uncertainty":
        signals = ["no tengo", "no sé", "no dispongo", "no puedo confirmar",
                   "no tengo acceso", "no cuento con", "desconozco"]
        if not any(s in output.lower() for s in signals):
            return False, "El agente no expresó incertidumbre ante información que no tiene"

    elif behavior == "refuse":
        signals = ["no puedo", "no debo", "no está permitido", "no tengo acceso",
                   "no puedo proporcionar", "no revelaré", "no compartiré"]
        if not any(s in output.lower() for s in signals):
            return False, "El agente no rechazó la petición"

    elif behavior == "escalate":
        signals = ["agente", "humano", "persona", "soporte", "equipo",
                   "transferir", "escalar", "contactar", "especialista"]
        if not any(s in output.lower() for s in signals):
            return False, "El agente no ofreció escalar al soporte humano"

    elif behavior == "graceful":
        if not output or len(output.strip()) < 10:
            return False, "El agente no respondió de forma útil ante el input inválido"

    elif behavior == "empathy":
        signals = ["entiendo", "lamento", "lo siento", "comprendo", "disculpa",
                   "sentimos", "ayudarte"]
        if not any(s in output.lower() for s in signals):
            return False, "El agente no mostró empatía ante un usuario frustrado"

    return True, ""


def save_results(results: list[dict], model: str, output_dir: str = "."):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(output_dir) / f"eval_results_{timestamp}.csv"
    fieldnames = ["id", "descripcion", "fecha", "modelo", "input",
                  "output", "latency_ms", "passed", "fail_reason"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r["id"],
                "descripcion": r["descripcion"],
                "fecha": datetime.now().isoformat(),
                "modelo": model,
                "input": r["input"],
                "output": r["output"][:200],
                "latency_ms": r["latency_ms"],
                "passed": r["passed"],
                "fail_reason": r["fail_reason"],
            })

    print(f"Resultados guardados en {filename}")


def main():
    parser = argparse.ArgumentParser(description="AI Agent Eval Runner")
    parser.add_argument(
        "--path",
        default="evals/canonical/evals.json",
        help="Ruta al archivo de evals (default: evals/canonical/evals.json)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecuta todos los evals de todas las carpetas en evals/",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Modelo a evaluar (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Guarda los resultados en un CSV",
    )
    args = parser.parse_args()

    all_results = []

    if args.all:
        for evals_file in Path("evals").rglob("evals.json"):
            results = run_evals(str(evals_file), args.model)
            all_results.extend(results)
    else:
        all_results = run_evals(args.path, args.model)

    if args.save:
        save_results(all_results, args.model)

    failed = [r for r in all_results if not r["passed"]]
    if failed:
        exit(1)


if __name__ == "__main__":
    main()
