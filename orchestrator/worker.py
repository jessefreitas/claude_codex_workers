"""
Worker usando GitHub Models API (OpenAI-compatible).
Ideal para tarefas pesadas e repetitivas, consumindo menos tokens do Claude.
"""

from openai import OpenAI
from .config import GITHUB_TOKEN, WORKER_MODEL
from .utils import run_parallel


REASONING_MODELS = {"o1", "o1-mini", "o3", "o3-mini", "o4-mini", "o4"}


class Worker:
    def __init__(self, model: str = None):
        self.model = model or WORKER_MODEL
        self.is_reasoning = any(self.model.startswith(m) for m in REASONING_MODELS)
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=GITHUB_TOKEN,
        )

    def run(self, task: str, system_prompt: str = None, temperature: float = 0.3) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": task})

        params = {"model": self.model, "messages": messages}
        if not self.is_reasoning:
            params["temperature"] = temperature

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content

    def run_batch(self, tasks: list[str], system_prompt: str = None) -> list[str]:
        """Executa multiplas tarefas em sequencia."""
        return [self.run(task, system_prompt) for task in tasks]

    def run_parallel(self, tasks: list[str], system_prompt: str = None, max_workers: int = 5) -> list[str]:
        """
        Executa multiplas tarefas em paralelo via threads.

        Args:
            tasks: Lista de tarefas a executar
            system_prompt: Instrucao de comportamento (aplicada a todas)
            max_workers: Numero maximo de chamadas simultaneas (padrao: 5)

        Returns:
            Lista de respostas na mesma ordem das tasks
        """
        return run_parallel(lambda task: self.run(task, system_prompt), tasks, max_workers)
