"""
Script de deploy do orquestrador na VPS.
Instala o pacote globalmente para todos os projetos usarem.
"""

import os
import paramiko
import sys
import io

# Força UTF-8 no terminal Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VPS_HOST = "5.78.182.155"
VPS_USER = "root"
SSH_KEY = r"C:\Users\Skycracker\.ssh\claude_memory_vps"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or input("GITHUB_TOKEN: ").strip()
REPO_URL = "https://github.com/jessefreitas/claude_codex_workers.git"


def run(client: paramiko.SSHClient, cmd: str, desc: str = "") -> str:
    if desc:
        print(f"  >> {desc}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(f"     {out[:300]}")
    if err and "WARNING" not in err.upper():
        print(f"     [WARN] {err[:300]}")
    return out


def main():
    print(f"Conectando à VPS {VPS_HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VPS_HOST, username=VPS_USER, key_filename=SSH_KEY)
    print("Conectado.\n")

    # 1. Setar GITHUB_TOKEN globalmente
    run(client,
        f'grep -q "GITHUB_TOKEN" /etc/environment || echo "GITHUB_TOKEN={GITHUB_TOKEN}" >> /etc/environment',
        "Setando GITHUB_TOKEN em /etc/environment")
    run(client,
        f'sed -i "s|GITHUB_TOKEN=.*|GITHUB_TOKEN={GITHUB_TOKEN}|" /etc/environment',
        "Atualizando GITHUB_TOKEN se já existia")

    # 2. Garantir Python 3.11+ e pip
    run(client, "python3 --version", "Verificando Python")
    run(client, "pip3 --version || apt-get install -y python3-pip", "Verificando pip")

    # 3. Instalar em venv compartilhado em /opt/orchestrator-venv
    run(client, "apt-get install -y python3-venv git --quiet", "Instalando python3-venv e git")
    run(client, "python3 -m venv /opt/orchestrator-venv", "Criando venv em /opt/orchestrator-venv")
    run(client,
        f"/opt/orchestrator-venv/bin/pip install git+{REPO_URL} --upgrade --quiet",
        "Instalando claude-codex-orchestrator no venv")

    # 4. Verificar instalação
    out = run(client,
        '/opt/orchestrator-venv/bin/python -c "from orchestrator import Orchestrator, Worker, Reviewer; print(\'OK\')"',
        "Verificando import do pacote")

    if "OK" in out:
        print("\n✓ Pacote instalado com sucesso na VPS!")
    else:
        print("\n✗ Erro na verificação do import. Verifique os logs acima.")
        sys.exit(1)

    # 5. Criar template .env para novos projetos
    run(client, f"""cat > /opt/orchestrator.env.example << 'EOF'
# Copie este arquivo para o seu projeto como .env
GITHUB_TOKEN={GITHUB_TOKEN}
WORKER_MODEL=o4-mini
PYTHONUTF8=1
EOF""", "Criando template .env em /opt/orchestrator.env.example")

    # 6. Criar script helper para novos projetos
    run(client, r"""cat > /usr/local/bin/orchestrator-new-project << 'SCRIPT'
#!/bin/bash
# Uso: orchestrator-new-project /caminho/do/projeto
PROJECT_DIR=${1:-$(pwd)}
echo "Configurando orquestrador em: $PROJECT_DIR"
python3 -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/pip" install git+https://github.com/jessefreitas/claude_codex_workers.git --quiet
cp /opt/orchestrator.env.example "$PROJECT_DIR/.env.example" 2>/dev/null || true
echo "Pronto! Use: source $PROJECT_DIR/.venv/bin/activate"
SCRIPT
chmod +x /usr/local/bin/orchestrator-new-project""",
        "Criando helper /usr/local/bin/orchestrator-new-project")

    print("\n--- COMO USAR EM NOVOS PROJETOS NA VPS ---")
    print("  orchestrator-new-project /caminho/do/projeto")
    print("  ou: /opt/orchestrator-venv/bin/pip install ...")
    print("  ou local: pip install git+https://github.com/jessefreitas/claude_codex_workers.git")
    print("-------------------------------------------")

    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
