# Claude Codex Workers

Framework de orquestração de agentes IA com padrão **Worker → Reviewer**.

O Worker gera código via GitHub Models (modelos de raciocínio como `o4-mini`).
O Reviewer valida e aprova via Claude Code CLI — sem custo adicional de API.

## Como funciona

```text
sua tarefa
  └→ Worker (GitHub Models / o4-mini)   ← geração barata e paralela
       └→ Reviewer (Claude Code CLI)    ← validação inteligente
            ├→ APROVADO  → retorna resultado
            └→ REPROVADO → feedback injetado → Worker reexecuta (retry)
```

## Instalação

Veja [PREREQUISITES.md](PREREQUISITES.md) para instalar as dependências do sistema.

```bash
pip install -r requirements.txt
cp .env.example .env
# edite .env e preencha GITHUB_TOKEN
```

## Uso

### Task simples com retry automático

```python
from orchestrator import Orchestrator

orq = Orchestrator()

result = orq.run(
    task="Escreva uma função Python para validar CPF.",
    system_prompt="Python sênior. Código limpo com type hints e docstring.",
    review_criteria="Deve ter docstring, tratar edge cases e ser eficiente.",
)

print(result["approved"])     # True/False
print(result["attempts"])     # numero de tentativas
print(result["final_output"]) # codigo gerado e aprovado
```

### Múltiplas tasks em paralelo

```python
results = orq.run_parallel(
    tasks=[
        {"task": "Crie schema SQL para usuarios", "review_criteria": "Deve ter PKs e indexes"},
        {"task": "Crie schema SQL para produtos", "review_criteria": "Deve ter PKs e indexes"},
        {"task": "Crie schema SQL para pedidos",  "review_criteria": "Deve ter FKs corretas"},
    ],
    max_workers=3,
)
```

### Pipeline sequencial (output de um step alimenta o próximo)

```python
results = orq.pipeline([
    {
        "name": "Schema SQL",
        "task": "Crie o schema para um sistema de vendas.",
        "critical": True,
    },
    {
        "name": "Models SQLAlchemy",
        "task": "Crie os models para o schema.",
        "use_previous_output": True,
    },
    {
        "name": "Endpoints FastAPI",
        "task": "Crie os endpoints CRUD.",
        "use_previous_output": True,
    },
])
```

### Worker direto (sem review)

```python
from orchestrator import Worker

worker = Worker(model="gpt-4.1-nano")  # modelo mais barato para tasks simples
resultado = worker.run("Liste 5 boas práticas de segurança para APIs REST.")
```

### Claude direto para decisões

```python
from orchestrator import Reviewer

reviewer = Reviewer()
decisao = reviewer.decide(
    question="Qual a melhor estratégia de cache para dados que mudam a cada 5 minutos?",
    context="API FastAPI com Redis, ~10k req/min.",
)
```

## Modelos disponíveis

| Modelo | Perfil |
| --- | --- |
| `o4-mini` | **Melhor para código** — raciocínio interno (padrão) |
| `o3` | Mais poderoso, mais lento |
| `gpt-4.1` | Rápido, sem raciocínio, bom para tasks simples |
| `gpt-4.1-nano` | Mais barato, tasks triviais |

## Estrutura

```text
orchestrator/
├── config.py        # Configuração e env vars
├── worker.py        # Worker via GitHub Models API
├── reviewer.py      # Reviewer via Claude Code CLI
├── orchestrator.py  # Coordena workflow, retry e pipeline
└── utils.py         # Executor paralelo compartilhado
example.py           # Exemplos de uso
PREREQUISITES.md     # Dependências do sistema
```

## Economia estimada

Comparando 1.000 tasks/mês versus usar apenas Claude Sonnet:

| Abordagem | Custo estimado |
| --- | --- |
| 100% Claude Sonnet | ~$33/mês |
| Worker (o4-mini) + Reviewer (Claude CLI) | ~$7–15/mês |
| **Economia** | **56–80%** |

## Licença

MIT
