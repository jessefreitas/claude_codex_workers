# Pre-requisitos

## 1. Python 3.10+

```bash
python --version  # deve ser >= 3.10
```

## 2. Claude Code CLI (Reviewer)

O Reviewer chama o Claude localmente via CLI — sem custo adicional de API.

```bash
# Instalar
npm install -g @anthropic-ai/claude-code

# Verificar
claude --version
```

> Requer conta Anthropic com acesso ao Claude Code.

## 3. GitHub Personal Access Token (Worker)

O Worker usa o GitHub Models API. Gere um token em:
`https://github.com/settings/tokens` → **Fine-grained token** com permissao `models:read`.

## 4. Dependencias Python

```bash
pip install -r requirements.txt
```

## 5. Arquivo .env

Crie um `.env` na raiz do projeto (use `.env.example` como base):

```bash
cp .env.example .env
# edite e preencha GITHUB_TOKEN
```

```env
GITHUB_TOKEN=ghp_seu_token_aqui
WORKER_MODEL=o4-mini   # opcional, este e o padrao
```

## Modelos disponiveis (GitHub Models)

| Modelo | Perfil |
|---|---|
| `o4-mini` | Melhor para codigo (padrao) |
| `o3` | Mais poderoso, mais lento |
| `gpt-4.1` | Rapido, sem raciocinio |
| `gpt-4.1-nano` | Mais barato, tasks simples |

## Verificacao rapida

```bash
python -c "from orchestrator import Orchestrator; print('OK')"
```
