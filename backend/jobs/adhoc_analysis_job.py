from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from app.config import get_settings
from app.services.adhoc_analysis import run_adhoc_analysis
from app.services.query_runs import get_query_run, put_query_results, update_query_run


def run(query_run_id: str) -> dict:
    query_run = get_query_run(query_run_id)
    if not query_run:
        raise ValueError(f"query_run {query_run_id} not found")

    update_query_run(
        query_run_id,
        status="running",
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        error=None,
    )
    try:
        budget_seconds = max(30, get_settings().query_budget_seconds)
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_adhoc_analysis, query_run)
        try:
            result = future.result(timeout=budget_seconds)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        put_query_results(query_run_id, result)
        update_query_run(
            query_run_id,
            status="completed",
            completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            coverage=result.get("coverage", {}),
            quality=result.get("quality", {}),
        )
        return result
    except FutureTimeoutError:
        message = (
            "La consulta excedió el presupuesto de tiempo configurado. "
            "Intentá nuevamente con menor alcance."
        )
        update_query_run(
            query_run_id,
            status="failed",
            completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            error=message,
        )
        raise TimeoutError(message)
    except Exception as exc:  # noqa: BLE001
        update_query_run(
            query_run_id,
            status="failed",
            completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            error=str(exc),
        )
        raise


if __name__ == "__main__":
    raise SystemExit("Use python -c 'from jobs.adhoc_analysis_job import run; run(<id>)'")
