"""
Configuração do orquestrador.
Lê variáveis de ambiente do arquivo .env
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Força UTF-8 no Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Token GitHub Models
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Modelo worker padrão
WORKER_MODEL = os.getenv("WORKER_MODEL", "o4-mini")

# Validação
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN não definido no .env")
