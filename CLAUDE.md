# Claude Codex Orchestrator

## Objetivo

Framework de orquestracao de agentes IA com padrao Worker + Reviewer.
O Worker gera codigo via GitHub Models API (modelos de raciocinio como o4-mini, custo baixo e paralelo).
O Reviewer valida e aprova via Claude Code CLI (subprocess, sem custo de API).
Retry automatico: se o Reviewer reprova, o feedback e injetado e o Worker reexecuta.

## Stack

- **Linguagem:** Python 3.11+
- **Framework:** Nenhum (biblioteca/pacote puro)
- **Banco:** Nenhum
- **Deploy:** VPS 5.78.182.155 via script paramiko (`deploy_vps.py`)
- **Docker:** Nao
- **Packaging:** setuptools via pyproject.toml
- **Dependencias:** openai, anthropic, python-dotenv

## Arquitetura

```text
orchestrator/
  config.py         -- carrega .env, valida GITHUB_TOKEN, forca UTF-8 no Windows
  worker.py         -- Worker: chama GitHub Models API (OpenAI-compatible)
  reviewer.py       -- Reviewer: chama Claude Code CLI via subprocess
  orchestrator.py   -- Orchestrator: coordena Worker+Reviewer, retry, pipeline, paralelo
  utils.py          -- run_parallel com ThreadPoolExecutor, preserva ordem

example.py          -- exemplos de uso (task simples, paralelo, pipeline)
deploy_vps.py       -- deploy automatizado na VPS via SSH/paramiko
```

### Fluxo principal

1. `Orchestrator.run(task)` envia tarefa ao Worker (GitHub Models)
2. Worker retorna output gerado
3. Reviewer analisa via Claude Code CLI (`claude -p`)
4. Se APROVADO: retorna resultado
5. Se REPROVADO: feedback injetado no prompt, Worker reexecuta (ate max_retries)

### Modos de execucao

- `run()` -- task unica com retry automatico
- `run_parallel()` -- multiplas tasks independentes em paralelo (ThreadPoolExecutor)
- `pipeline()` -- steps sequenciais, output de um alimenta o proximo

## Convencoes

- Codigo em Python, type hints sempre que possivel
- Docstrings em todos os metodos publicos
- Sem acentos em docstrings/comentarios no codigo (compatibilidade terminal Windows)
- Comentarios e commits em portugues
- Branches: main/master (prod), feature/<nome>
- UTF-8 forcado no Windows via config.py

## Variaveis de Ambiente

Ver `.env.example`:

- `GITHUB_TOKEN` -- Personal Access Token do GitHub com permissao `models:read` (obrigatorio)
- `WORKER_MODEL` -- modelo do Worker (padrao: `o4-mini`). Opcoes: o4-mini, o3, gpt-4.1, gpt-4.1-nano
- `PYTHONUTF8` -- deve ser `1` no Windows

## Como rodar localmente

```bash
# 1. Clonar
git clone https://github.com/jessefreitas/claude_codex_workers.git
cd claude_codex_workers

# 2. Criar venv e instalar
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt

# 3. Configurar env
cp .env.example .env
# editar .env e preencher GITHUB_TOKEN

# 4. Prerequisitos
# Claude Code CLI deve estar instalado e no PATH (ver PREREQUISITES.md)

# 5. Usar
python example.py
```

## Deploy (VPS)

```bash
# Requer: paramiko instalado localmente, SSH key configurada
python deploy_vps.py
```

O script:
1. Conecta na VPS via SSH (5.78.182.155, root, key em ~/.ssh/claude_memory_vps)
2. Seta GITHUB_TOKEN em /etc/environment
3. Cria venv em /opt/orchestrator-venv
4. Instala o pacote direto do GitHub
5. Cria helper `orchestrator-new-project` para novos projetos na VPS

## Modelos disponiveis (Worker)

| Modelo       | Perfil                                          |
| ------------ | ----------------------------------------------- |
| `o4-mini`    | Melhor para codigo, raciocinio interno (padrao) |
| `o3`         | Mais poderoso, mais lento                       |
| `gpt-4.1`    | Rapido, sem raciocinio, bom para tasks simples  |
| `gpt-4.1-nano` | Mais barato, tasks triviais                  |

## Notas importantes

- O Reviewer depende do Claude Code CLI instalado localmente (`claude` no PATH)
- Modelos de raciocinio (o1, o3, o4-mini) nao aceitam parametro `temperature`
- O Worker usa o endpoint `https://models.inference.ai.azure.com` (GitHub Models)
- Para usar na VPS: `/opt/orchestrator-venv/bin/python` (nunca python3 do sistema)
