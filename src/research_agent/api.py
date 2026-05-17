import logging
import time

import fastapi
import typing

import research_agent.logging_config
import research_agent.models
import research_agent.service


research_agent.logging_config.configure_logging()

app = fastapi.FastAPI(title="Research Agent API")


@app.middleware("http")
async def correlation_id_middleware(request: fastapi.Request, call_next: typing.Any) -> fastapi.Response:
    start_time = time.perf_counter()
    correlation_id = request.headers.get("x-correlation-id") or research_agent.logging_config.generate_correlation_id()
    token = research_agent.logging_config.set_correlation_id(correlation_id)
    request.state.correlation_id = correlation_id

    try:
        logging.info("Request started")
        response: fastapi.Response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        logging.info("Request finished")
        end_time = time.perf_counter()
        logging.info(f"Request took: {end_time - start_time:.4f} seconds.")
        return response
    finally:
        research_agent.logging_config.reset_correlation_id(token)


def get_audit_config() -> research_agent.models.ResearchAuditConfig:
    if not hasattr(app.state, "audit_config"):
        env_vars = research_agent.service.load_env_vars()
        app.state.audit_config = research_agent.service.build_audit_config(env_vars)

    return typing.cast(research_agent.models.ResearchAuditConfig, app.state.audit_config)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/audit", response_model=research_agent.models.ResearchAuditResponse)
async def audit(request: research_agent.models.ResearchAuditRequest) -> research_agent.models.ResearchAuditResponse:
    audit_config = get_audit_config()
    result = await research_agent.service.run_audit(
        document_text=request.document_text,
        audit_config=audit_config,
    )

    return research_agent.models.ResearchAuditResponse(
        claims=result["claims"],
        literature_queries=result["literature_queries"],
        literature_results=typing.cast(list[dict[str, typing.Any]], result["literature_results"]),
        contradictions=result["contradictions"],
        logic_gaps=result["logic_gaps"],
        action_items=result["action_items"],
    )
