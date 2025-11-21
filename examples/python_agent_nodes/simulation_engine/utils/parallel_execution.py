"""Parallel execution utilities for simulation engine."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

from agentfield.logger import log_info

T = TypeVar("T")


async def execute_parallel(
    tasks: list[Callable[[], Any]], max_concurrent: int = 100
) -> list[Any]:
    """
    Execute multiple async tasks in parallel with concurrency limit.

    Args:
        tasks: List of async functions to execute
        max_concurrent: Maximum number of concurrent executions

    Returns:
        List of results in the same order as tasks
    """
    if not tasks:
        return []

    log_info(
        f"[execute_parallel] Executing {len(tasks)} tasks with max_concurrent={max_concurrent}"
    )

    # Process in batches to respect concurrency limit
    results: list[Any] = []
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i : i + max_concurrent]
        batch_results = await asyncio.gather(
            *[task() for task in batch], return_exceptions=True
        )
        results.extend(batch_results)

    # Count successes and failures
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = len(results) - successes
    if failures > 0:
        log_info(
            f"[execute_parallel] Completed: {successes} successes, {failures} failures"
        )

    return results


async def batch_execute(
    items: list[Any],
    func: Callable[[Any], Any],
    batch_size: int = 50,
    max_concurrent: int = 100,
) -> list[Any]:
    """
    Execute a function on a list of items in parallel batches.

    Args:
        items: List of items to process
        func: Async function to apply to each item
        batch_size: Number of items per batch
        max_concurrent: Maximum concurrent executions per batch

    Returns:
        List of results in the same order as items
    """
    if not items:
        return []

    log_info(
        f"[batch_execute] Processing {len(items)} items in batches of {batch_size}"
    )

    all_results: list[Any] = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        tasks = [lambda item=item: func(item) for item in batch]
        batch_results = await execute_parallel(tasks, max_concurrent=max_concurrent)
        all_results.extend(batch_results)

    return all_results
