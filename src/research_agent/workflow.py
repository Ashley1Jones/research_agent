import functools

import langgraph.graph

import research_agent.models
import research_agent.states


def parse_bullets(text: str | list) -> list[str]:
    """Parse a bullet-point LLM response into a clean list of strings."""
    items: list[str] = []
    lines = text if isinstance(text, list) else text.splitlines()

    for line in lines:
        cleaned = line.strip()

        if not cleaned:
            continue

        cleaned = cleaned.removeprefix("-").strip()
        cleaned = cleaned.removeprefix("*").strip()

        if cleaned:
            items.append(cleaned)

    return items


async def extract_claims(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    response = await audit_config.llm.ainvoke(f"""
        Extract the main research or technical claims from the text below.

        Return only a bullet-point list.
        Do not include explanations or headings.

        Text:
        {state["document_text"]}
        """)

    claims = parse_bullets(response.content)

    if not claims:
        claims = list(audit_config.default_claims)

    return {**state, "claims": claims}


async def find_logic_gaps(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    claims_text = "\n".join(f"- {claim}" for claim in state["claims"])

    response = await audit_config.llm.ainvoke(f"""
        Review the following claims and identify logical gaps, missing evidence,
        vague assumptions, unsupported conclusions, or places where further
        research is needed.

        Return only a bullet-point list.
        Do not include explanations or headings.

        Claims:
        {claims_text}
        """)

    logic_gaps = parse_bullets(response.content)

    return {**state, "logic_gaps": logic_gaps}


async def generate_action_items(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    gaps_text = "\n".join(f"- {gap}" for gap in state["logic_gaps"])

    response = await audit_config.llm.ainvoke(f"""
        Convert the following research gaps into clear, actionable next steps.

        Each action should begin with this prefix:
        "{audit_config.action_prefix}"

        Return only a bullet-point list.
        Do not include explanations or headings.

        Research gaps:
        {gaps_text}
        """)

    action_items = parse_bullets(response.content)

    return {**state, "action_items": action_items}


def build_workflow(config: research_agent.models.ResearchAuditConfig):
    workflow = langgraph.graph.StateGraph(research_agent.states.ResearchAuditState)

    workflow.add_node("extract_claims", functools.partial(extract_claims, audit_config=config))
    workflow.add_node("find_logic_gaps", functools.partial(find_logic_gaps, audit_config=config))
    workflow.add_node(
        "generate_action_items",
        functools.partial(generate_action_items, audit_config=config),
    )

    workflow.set_entry_point("extract_claims")

    workflow.add_edge("extract_claims", "find_logic_gaps")
    workflow.add_edge("find_logic_gaps", "generate_action_items")
    workflow.add_edge("generate_action_items", langgraph.graph.END)

    return workflow.compile()
