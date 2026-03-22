"""
Orquestrador principal.
Coordena workers (GitHub Models) e reviewer (Claude).
"""

from .worker import Worker
from .reviewer import Reviewer
from .utils import run_parallel


class Orchestrator:
    def __init__(self, worker_model: str = None):
        self.worker = Worker(model=worker_model)
        self.reviewer = Reviewer()

    def run(
        self,
        task: str,
        system_prompt: str = None,
        review_criteria: str = None,
        max_retries: int = 2,
        auto_retry: bool = True,
    ) -> dict:
        """
        Executa uma tarefa completa: worker gera, Claude revisa.

        Returns:
            dict com: approved, feedback, worker_output, improved_output, final_output, attempts
        """
        attempts = 0
        feedback_context = ""

        while attempts <= max_retries:
            attempts += 1

            task_with_feedback = task
            if feedback_context:
                task_with_feedback = (
                    f"{task}\n\n"
                    f"[Tentativa anterior foi reprovada. Corrija os seguintes problemas:]\n"
                    f"{feedback_context}"
                )

            worker_output = self.worker.run(task_with_feedback, system_prompt)
            review = self.reviewer.review(task, worker_output, review_criteria)
            review["attempts"] = attempts
            review["worker_output"] = worker_output

            if review["approved"]:
                return review

            if auto_retry and attempts <= max_retries:
                feedback_context = review["feedback"]
                continue

            break

        return review

    def run_parallel(self, tasks: list[dict], max_workers: int = 5) -> list[dict]:
        """
        Executa multiplas tasks independentes em paralelo (Worker + Reviewer cada uma).

        Cada task e um dict com os mesmos parametros do run():
            - task (str): obrigatorio
            - system_prompt (str, opcional)
            - review_criteria (str, opcional)
            - max_retries (int, opcional)
            - auto_retry (bool, opcional)

        Args:
            tasks: Lista de tasks independentes
            max_workers: Chamadas simultaneas ao GitHub Models (padrao: 5)

        Returns:
            Lista de resultados na mesma ordem das tasks
        """
        def _run_task(t: dict) -> dict:
            return self.run(
                task=t["task"],
                system_prompt=t.get("system_prompt"),
                review_criteria=t.get("review_criteria"),
                max_retries=t.get("max_retries", 2),
                auto_retry=t.get("auto_retry", True),
            )

        return run_parallel(_run_task, tasks, max_workers)

    def pipeline(self, steps: list[dict]) -> list[dict]:
        """
        Executa um pipeline de multiplos passos sequenciais.

        Cada step e um dict com:
            - task (str): a tarefa
            - name (str, opcional): nome do step para logging
            - system_prompt (str, opcional)
            - review_criteria (str, opcional)
            - use_previous_output (bool, opcional): injeta output anterior na tarefa
            - critical (bool, opcional): aborta pipeline se reprovar

        Returns:
            Lista com resultado de cada step
        """
        results = []
        previous_output = None

        for i, step in enumerate(steps):
            task = step["task"]

            if step.get("use_previous_output") and previous_output:
                task = f"{task}\n\nInput do passo anterior:\n{previous_output}"

            result = self.run(
                task=task,
                system_prompt=step.get("system_prompt"),
                review_criteria=step.get("review_criteria"),
                max_retries=step.get("max_retries", 2),
                auto_retry=step.get("auto_retry", True),
            )

            result["step"] = i + 1
            result["step_name"] = step.get("name", f"Step {i + 1}")
            results.append(result)

            previous_output = result["final_output"]

            if not result["approved"] and step.get("critical", False):
                print(f"[Pipeline] Step critico '{result['step_name']}' falhou. Abortando.")
                break

        return results
