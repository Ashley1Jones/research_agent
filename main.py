import os
import logging

from langchain_ollama import ChatOllama

from research_agent.models import EnvVars, ResearchAuditConfig
from research_agent.states import ResearchAuditState
from research_agent.workflow import build_workflow


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_vars = EnvVars.model_validate(dict(os.environ))

    llm = ChatOllama(
        model=env_vars.MODEL_TYPE,
        base_url=env_vars.create_url(),
        temperature=0,
    )

    config = ResearchAuditConfig(
        llm=llm,
        default_claims=(
            "The proposed system improves research quality.",
            "The architecture is scalable.",
            "The approach reduces hallucinations.",
        ),
        action_prefix="Add supporting evidence or experiment for",
    )

    app = build_workflow(config)

    initial_state: ResearchAuditState = {
        "document_text": """
        Our multi-agent research system improves research quality,
        reduces hallucinations, and provides a scalable architecture.
        The system will outperform existing single-agent approaches.
        """,
        "claims": [],
        "logic_gaps": [],
        "action_items": [],
    }

    result = app.invoke(initial_state)

    logging.info("Claims:")
    for claim in result["claims"]:
        logging.info("- %s", claim)

    logging.info("\nLogic gaps:")
    for gap in result["logic_gaps"]:
        logging.info("- %s", gap)

    logging.info("\nAction items:")
    for item in result["action_items"]:
        logging.info("- %s", item)


if __name__ == "__main__":
    main()
