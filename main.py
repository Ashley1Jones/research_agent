from dataclasses import dataclass
from functools import partial
from typing import List, TypedDict

from langgraph.graph import StateGraph, END


@dataclass(frozen=True)
class ResearchAuditConfig:
    default_claims: tuple[str, ...]
    evidence_terms: tuple[str, ...]
    architecture_terms: tuple[str, ...]
    action_prefix: str


class ResearchAuditState(TypedDict):
    document_text: str
    claims: List[str]
    logic_gaps: List[str]
    action_items: List[str]


def extract_claims(
    state: ResearchAuditState, *, audit_config: ResearchAuditConfig
) -> ResearchAuditState:
    # In a real version, this would call an LLM.
    claims = list(audit_config.default_claims)

    return {**state, "claims": claims}


def find_logic_gaps(
    state: ResearchAuditState, *, audit_config: ResearchAuditConfig
) -> ResearchAuditState:
    claims = state["claims"]

    # In a real version, this would call another LLM.
    gaps = []

    for claim in claims:
        if any(term in claim for term in audit_config.evidence_terms):
            gaps.append(f"Claim needs measurable evidence or evaluation: {claim}")

        if any(term in claim for term in audit_config.architecture_terms):
            gaps.append(
                f"Claim needs architectural justification or benchmark: {claim}"
            )

    return {**state, "logic_gaps": gaps}


def generate_action_items(
    state: ResearchAuditState, *, audit_config: ResearchAuditConfig
) -> ResearchAuditState:
    gaps = state["logic_gaps"]

    actions = [f"{audit_config.action_prefix}: {gap}" for gap in gaps]

    return {**state, "action_items": actions}


def build_workflow(config: ResearchAuditConfig):
    workflow = StateGraph(ResearchAuditState)

    workflow.add_node("extract_claims", partial(extract_claims, audit_config=config))
    workflow.add_node("find_logic_gaps", partial(find_logic_gaps, audit_config=config))
    workflow.add_node(
        "generate_action_items", partial(generate_action_items, audit_config=config)
    )

    workflow.set_entry_point("extract_claims")

    workflow.add_edge("extract_claims", "find_logic_gaps")
    workflow.add_edge("find_logic_gaps", "generate_action_items")
    workflow.add_edge("generate_action_items", END)

    return workflow.compile()


def main():
    config = ResearchAuditConfig(
        default_claims=(
            "The proposed system improves research quality.",
            "The architecture is scalable.",
            "The approach reduces hallucinations.",
        ),
        evidence_terms=("improves", "reduces"),
        architecture_terms=("scalable",),
        action_prefix="Add supporting evidence or experiment for",
    )

    app = build_workflow(config)

    initial_state: ResearchAuditState = {
        "document_text": """
        Our multi-agent research system improves research quality,
        reduces hallucinations, and provides a scalable architecture.
        """,
        "claims": [],
        "logic_gaps": [],
        "action_items": [],
    }

    result = app.invoke(initial_state)

    print("Claims:")
    for claim in result["claims"]:
        print("-", claim)

    print("\nLogic gaps:")
    for gap in result["logic_gaps"]:
        print("-", gap)

    print("\nAction items:")
    for item in result["action_items"]:
        print("-", item)


if __name__ == "__main__":
    main()
