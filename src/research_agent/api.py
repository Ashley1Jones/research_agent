import fastapi
import typing

import research_agent.models
import research_agent.service


app = fastapi.FastAPI(title="Research Agent API")


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
