from __future__ import annotations

import inspect
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator


_TRACING_STATE: dict[str, Any] = {
    "enabled": False,
    "project_name": "curequest-patient-finance",
}


def init_tracing() -> None:
    _TRACING_STATE["enabled"] = True


@contextmanager
def span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    start = time.perf_counter()
    state = {
        "name": name,
        "attributes": dict(attributes or {}),
        "status": "ok",
    }
    try:
        yield state
    except Exception:
        state["status"] = "error"
        raise
    finally:
        state["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)


def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with span(name, attributes):
                    return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with span(name, attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_llm_call(_span: dict[str, Any], model: str, input_text: str, output_text: str, token_counts: dict[str, Any]) -> None:
    _span["llm"] = {
        "model": model,
        "input_length": len(input_text),
        "output_length": len(output_text),
        "token_counts": token_counts,
    }


def log_tool_call(_span: dict[str, Any], tool_name: str, input_args: dict[str, Any], output_result: Any) -> None:
    _span["tool"] = {
        "name": tool_name,
        "input_keys": sorted(input_args.keys()),
        "output_type": type(output_result).__name__,
    }


def log_agent_routing(_span: dict[str, Any], from_agent: str, to_agent: str, reason: str) -> None:
    _span["routing"] = {
        "from_agent": from_agent,
        "to_agent": to_agent,
        "reason": reason,
    }

