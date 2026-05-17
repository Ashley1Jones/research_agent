import logging
import time
import typing

import httpx

import research_agent.logging_config

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=None, write=30.0, pool=10.0)


async def log_http_request(request: httpx.Request) -> None:
    request.extensions["start_time"] = time.perf_counter()

    logging.info(
        "http_request_started method=%s url=%s",
        request.method,
        str(request.url),
        extra={
            "correlation_id": research_agent.logging_config.get_correlation_id(),
            "method": request.method,
            "url": str(request.url),
        },
    )


async def log_http_response(response: httpx.Response) -> None:
    start_time = response.request.extensions.get("start_time")
    duration_ms = None

    if isinstance(start_time, int | float):
        duration_ms = int((time.perf_counter() - start_time) * 1000)

    logging.info(
        "http_request_completed method=%s url=%s status_code=%s duration_ms=%s",
        response.request.method,
        str(response.request.url),
        response.status_code,
        duration_ms,
        extra={
            "correlation_id": research_agent.logging_config.get_correlation_id(),
            "method": response.request.method,
            "url": str(response.request.url),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )


def create_async_client_kwargs(timeout: httpx.Timeout | None = None) -> dict[str, typing.Any]:
    return {
        "timeout": timeout or DEFAULT_TIMEOUT,
        "event_hooks": {
            "request": [log_http_request],
            "response": [log_http_response],
        },
    }


def create_async_client(timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout or DEFAULT_TIMEOUT,
        event_hooks={
            "request": [log_http_request],
            "response": [log_http_response],
        },
    )
