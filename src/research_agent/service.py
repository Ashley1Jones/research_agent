import os

import langchain_ollama

import research_agent.models
import research_agent.states
import research_agent.workflow


DEFAULT_DOCUMENT_TEXT = """
Our multi-agent research system improves research quality,
reduces hallucinations, and provides a scalable architecture.
The system will outperform existing single-agent approaches.
"""

DEFAULT_CLAIMS = (
    "The proposed system improves research quality.",
    "The architecture is scalable.",
    "The approach reduces hallucinations.",
)

ACTION_PREFIX = "Add supporting evidence or experiment for"


def load_env_vars() -> research_agent.models.EnvVars:
    return research_agent.models.EnvVars.model_validate(dict(os.environ))


def build_audit_config(env_vars: research_agent.models.EnvVars) -> research_agent.models.ResearchAuditConfig:
    llm = langchain_ollama.ChatOllama(
        model=env_vars.MODEL_TYPE,
        base_url=env_vars.create_url(),
        temperature=0,
    )

    return research_agent.models.ResearchAuditConfig(
        llm=llm,
        default_claims=DEFAULT_CLAIMS,
        action_prefix=ACTION_PREFIX,
    )


def run_audit(
    document_text: str,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    app = research_agent.workflow.build_workflow(audit_config)

    initial_state: research_agent.states.ResearchAuditState = {
        "document_text": document_text,
        "claims": [],
        "logic_gaps": [],
        "action_items": [],
    }

    return app.invoke(initial_state)
