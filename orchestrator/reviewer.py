"""
Reviewer usando Claude Code CLI (sem precisar de API key).
Chama o `claude` instalado localmente via subprocess.
"""

import subprocess
import shutil


REVIEW_SYSTEM_PROMPT = """Voce e um revisor tecnico experiente.
Sua funcao e analisar o output de um agente worker e:
1. Identificar problemas, bugs ou inconsistencias
2. Verificar se a tarefa foi cumprida corretamente
3. Sugerir melhorias se necessario
4. Aprovar ou reprovar o resultado

Seja objetivo e direto. Responda em portugues."""


def _find_claude() -> str:
    """Localiza o executavel do Claude Code CLI no PATH."""
    path = shutil.which("claude") or shutil.which("claude.cmd")
    if not path:
        raise EnvironmentError(
            "Claude Code CLI nao encontrado. "
            "Instale em: https://claude.ai/code e certifique-se que esta no PATH."
        )
    return path


def _run_claude(prompt: str, claude_path: str) -> str:
    try:
        result = subprocess.run(
            [claude_path, "-p", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
    except FileNotFoundError:
        raise EnvironmentError(f"Claude CLI nao encontrado em: {claude_path}")

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI erro: {result.stderr}")

    return result.stdout.strip()


class Reviewer:
    def __init__(self):
        self._claude_path = _find_claude()

    def review(self, original_task: str, worker_output: str, criteria: str = None) -> dict:
        """
        Revisa o output de um worker via Claude Code CLI.

        Returns:
            dict com: approved (bool), feedback (str), improved_output (str|None), final_output (str)
        """
        prompt = f"""{REVIEW_SYSTEM_PROMPT}

## Tarefa Original
{original_task}

## Output do Worker
{worker_output}
"""
        if criteria:
            prompt += f"\n## Criterios de Avaliacao\n{criteria}\n"

        prompt += """
## Sua Analise
Avalie o output acima. Responda exatamente no formato:
APROVADO: [SIM/NAO]
FEEDBACK: [seu feedback]
OUTPUT_CORRIGIDO: [versao corrigida se necessario, ou N/A se aprovado]"""

        response = _run_claude(prompt, self._claude_path)
        return self._parse_review(response, worker_output)

    def _parse_review(self, response: str, original_output: str) -> dict:
        lines = response.strip().split("\n")
        approved = False
        feedback = ""
        improved_output = None
        output_start = None

        for i, line in enumerate(lines):
            upper = line.upper()
            if "APROVADO:" in upper:
                approved = "SIM" in upper
            elif line.upper().startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
            elif "OUTPUT_CORRIGIDO:" in upper:
                rest = line.split(":", 1)[1].strip()
                output_start = i + 1
                improved_output = rest

        if output_start is not None:
            extra = "\n".join(lines[output_start:]).strip()
            if extra:
                improved_output = f"{improved_output}\n{extra}".strip() if improved_output else extra
            if improved_output and improved_output.strip().upper() == "N/A":
                improved_output = None

        # Sem marcadores de formato → Claude aprovou sem objecoes
        if not feedback and improved_output is None:
            approved = True

        return {
            "approved": approved,
            "feedback": feedback,
            "improved_output": improved_output,
            "final_output": improved_output if improved_output else original_output,
        }

    def decide(self, question: str, context: str = None) -> str:
        """Usa Claude para tomar uma decisao ou responder uma pergunta complexa."""
        prompt = question
        if context:
            prompt = f"Contexto:\n{context}\n\nPergunta:\n{question}"
        return _run_claude(prompt, self._claude_path)
