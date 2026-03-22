"""
Exemplos de uso do orquestrador.
"""

from orchestrator import Orchestrator, Worker, Reviewer


def exemplo_simples():
    """Worker gera codigo, Claude revisa."""
    orq = Orchestrator()

    result = orq.run(
        task="Escreva uma funcao Python que valida se um CPF e valido.",
        system_prompt="Voce e um desenvolvedor Python senior. Escreva codigo limpo e com docstring.",
        review_criteria="O codigo deve: ter docstring, tratar edge cases, ser eficiente.",
    )

    print(f"Aprovado: {result['approved']}")
    print(f"Tentativas: {result['attempts']}")
    print(f"Feedback: {result['feedback']}")
    print(f"\nOutput Final:\n{result['final_output']}")


def exemplo_paralelo_worker():
    """Multiplos workers rodando ao mesmo tempo (sem review)."""
    worker = Worker()  # o4-mini por padrao

    tasks = [
        "Escreva uma funcao Python para validar email.",
        "Escreva uma funcao Python para validar CPF.",
        "Escreva uma funcao Python para validar CNPJ.",
        "Escreva uma funcao Python para validar numero de telefone BR.",
        "Escreva uma funcao Python para validar CEP.",
    ]

    print(f"Executando {len(tasks)} tasks em paralelo...")
    resultados = worker.run_parallel(
        tasks=tasks,
        system_prompt="Python senior. Codigo limpo, com docstring e type hints.",
        max_workers=5,
    )

    for i, resultado in enumerate(resultados):
        print(f"\n--- Task {i + 1} ---")
        print(resultado[:300] + "..." if len(resultado) > 300 else resultado)


def exemplo_paralelo_orquestrador():
    """Multiplas tasks independentes com Worker + Reviewer em paralelo."""
    orq = Orchestrator()

    tasks = [
        {
            "task": "Crie o schema SQL para tabela de usuarios.",
            "system_prompt": "DBA senior, PostgreSQL.",
            "review_criteria": "Deve ter PK, indexes em email e created_at, tipos corretos.",
        },
        {
            "task": "Crie o schema SQL para tabela de produtos.",
            "system_prompt": "DBA senior, PostgreSQL.",
            "review_criteria": "Deve ter PK, index em nome, campo preco como NUMERIC.",
        },
        {
            "task": "Crie o schema SQL para tabela de pedidos.",
            "system_prompt": "DBA senior, PostgreSQL.",
            "review_criteria": "Deve ter PK, FKs para usuarios e produtos, status como ENUM.",
        },
    ]

    print(f"Executando {len(tasks)} tasks com Worker+Reviewer em paralelo...")
    results = orq.run_parallel(tasks=tasks, max_workers=3)

    for i, r in enumerate(results):
        status = "APROVADO" if r["approved"] else "REPROVADO"
        print(f"\n--- Task {i + 1} [{status}] ({r['attempts']} tentativa(s)) ---")
        print(r["final_output"][:400] + "..." if len(r["final_output"]) > 400 else r["final_output"])


def exemplo_pipeline():
    """Pipeline sequencial: output de um step alimenta o proximo."""
    orq = Orchestrator()

    steps = [
        {
            "name": "Schema SQL",
            "task": "Crie o schema SQL para um sistema de vendas com clientes, produtos e pedidos.",
            "system_prompt": "DBA senior, PostgreSQL.",
            "review_criteria": "Deve ter PKs, FKs, indices e tipos corretos.",
            "critical": True,
        },
        {
            "name": "Models SQLAlchemy",
            "task": "Crie os models SQLAlchemy para o schema criado.",
            "system_prompt": "Use SQLAlchemy 2.0 com type hints.",
            "use_previous_output": True,
        },
        {
            "name": "Endpoints FastAPI",
            "task": "Crie os endpoints CRUD em FastAPI para os models.",
            "system_prompt": "Use FastAPI com async/await e Pydantic v2.",
            "use_previous_output": True,
        },
    ]

    results = orq.pipeline(steps)

    for r in results:
        status = "OK" if r["approved"] else "FALHOU"
        print(f"[{status}] Step {r['step']}: {r['step_name']} ({r['attempts']} tentativa(s))")
        if r["feedback"]:
            print(f"  Feedback: {r['feedback']}")


def exemplo_worker_direto():
    """Worker direto sem review - modelo barato para tasks simples."""
    worker = Worker(model="gpt-4.1-nano")

    resultado = worker.run(
        task="Liste 5 boas praticas de seguranca para APIs REST.",
        system_prompt="Seja conciso e direto.",
    )
    print(resultado)


def exemplo_reviewer_direto():
    """Claude direto para decisoes complexas."""
    reviewer = Reviewer()

    decisao = reviewer.decide(
        question="Qual e a melhor estrategia de cache para uma API com dados que mudam a cada 5 minutos?",
        context="Temos uma API FastAPI com Redis disponivel, ~10k requisicoes/minuto.",
    )
    print(decisao)


if __name__ == "__main__":
    print("=== Exemplo Simples ===")
    exemplo_simples()

    print("\n=== Exemplo Paralelo Worker ===")
    exemplo_paralelo_worker()

    print("\n=== Exemplo Paralelo Orquestrador ===")
    exemplo_paralelo_orquestrador()
