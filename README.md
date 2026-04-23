# AI Agent Eval Kit

> Sube agentes a producción con confianza — no con esperanza.

Un conjunto de evaluaciones listas para usar para agentes de IA: casos de test, script de ejecución y plantilla de registro de resultados.

## ¿Qué problema resuelve?

La mayoría de devs prueba su agente manualmente un par de veces, ve que responde bien y lo sube a producción.

Dos semanas después el agente falla y nadie sabe cuándo empezó.

Este kit te da el sistema mínimo viable para evaluar tus agentes de forma sistemática — tanto antes del primer deploy como después de cada cambio de prompt o modelo.

## Contenido

```
evals/
├── canonical/          # 10 evals que aplican a cualquier agente
│   └── evals.json
└── customer-support/   # 5 evals para agentes de soporte al cliente
    └── evals.json
eval_runner.py          # Script para ejecutar todos los evals
requirements.txt
```

## Inicio rápido

```bash
git clone https://github.com/bezael/ai-agent-eval-kit
cd ai-agent-eval-kit
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
python eval_runner.py
```

Resultado esperado:

```
✓ fmt-001: Respuesta en formato JSON válido
✓ hal-001: No alucina datos que no tiene
✓ inv-001: Manejo de input vacío
...
10/10 evals pasaron
```

## Estructura de un eval

```json
{
  "id": "fmt-001",
  "descripcion": "Respuesta en formato JSON válido",
  "input": "Dame el resumen del usuario 123",
  "expected_format": "json",
  "expected_keys": ["nombre", "email", "estado"]
}
```

Campos disponibles:

| Campo | Descripción |
|-------|-------------|
| `id` | Identificador único |
| `descripcion` | Qué prueba este eval |
| `input` | El mensaje que se envía al agente |
| `expected_format` | `json`, `text` |
| `expected_keys` | Claves requeridas si el formato es JSON |
| `expected_behavior` | `uncertainty`, `escalate`, `refuse` |
| `max_latency_ms` | Umbral de latencia en milisegundos |

## Añadir tus propios evals

1. Abre el archivo `evals.json` del dominio correspondiente (o crea uno nuevo en `evals/tu-dominio/`)
2. Añade un objeto con los campos necesarios
3. Ejecuta `python eval_runner.py --path evals/tu-dominio/evals.json`

## Integración con CI/CD

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

## Guía completa

El PDF con la explicación detallada de cada eval, criterios de paso y plantilla de registro de resultados es exclusivo para suscriptores del newsletter **Build con IA**.

→ [Suscríbete gratis y descarga el PDF](https://dominicode.com/newsletter)

---

## ¿Prefieres TypeScript?

Existe una versión equivalente del kit en TypeScript:

→ [ai-agent-eval-kit-ts](https://github.com/bezael/ai-agent-eval-kit-ts)

Mismos evals, mismo script, misma estructura — con tipado completo y `tsx`.

---

Hecho por [Bezael Pérez](https://dominicode.com) · [@dominicode](https://youtube.com/@dominicode)
