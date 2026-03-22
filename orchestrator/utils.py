from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable


def run_parallel(fn: Callable, items: list, max_workers: int) -> list:
    """
    Executa fn(item) para cada item em paralelo, preservando ordem.
    Propaga a primeira excecao encontrada com contexto do indice.
    """
    results = [None] * len(items)
    errors = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fn, item): i for i, item in enumerate(items)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                errors[idx] = e

    if errors:
        first_idx, first_err = next(iter(sorted(errors.items())))
        raise RuntimeError(f"Task {first_idx} falhou: {first_err}") from first_err

    return results
