import asyncio
import functools
import logging
import typing

import langgraph.graph

import research_agent.models
import research_agent.research_tools
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

    updated_state = {**state, "claims": claims}
    return typing.cast(research_agent.states.ResearchAuditState, updated_state)


async def plan_literature_queries(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    claims_text = "\n".join(f"- {claim}" for claim in state["claims"])

    response = await audit_config.llm.ainvoke(f"""
        Convert these research claims into {audit_config.literature_query_count} academic search queries.

        The queries should be short and suitable for arXiv or Semantic Scholar.

        Claims:
        {claims_text}

        Return only one query per line.
        """)

    queries = parse_bullets(response.content)
    updated_state = {**state, "literature_queries": queries[: audit_config.literature_query_count]}
    return typing.cast(research_agent.states.ResearchAuditState, updated_state)


async def search_literature(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    search_tasks = []

    for query in state["literature_queries"]:
        search_tasks.append(
            run_literature_tool(
                research_agent.research_tools.search_semantic_scholar,
                query,
                {"query": query, "limit": audit_config.literature_result_limit},
            )
        )
        search_tasks.append(
            run_literature_tool(
                research_agent.research_tools.search_arxiv,
                query,
                {"query": query, "max_results": audit_config.literature_result_limit},
            )
        )

    grouped_results = await asyncio.gather(*search_tasks)
    literature_results = [result for result_group in grouped_results for result in result_group]

    updated_state = {**state, "literature_results": literature_results}
    return typing.cast(research_agent.states.ResearchAuditState, updated_state)


async def run_literature_tool(
    tool: typing.Any,
    query: str,
    args: dict[str, typing.Any],
) -> list[research_agent.states.LiteratureResult]:
    try:
        results = await tool.ainvoke(args)
    except Exception as exc:
        logging.warning("Literature tool failed for args %s: %s", args, exc)
        return []

    literature_results = []
    for result in typing.cast(list[dict[str, typing.Any]], results):
        result_with_query = {**result, "query": query}
        literature_results.append(typing.cast(research_agent.states.LiteratureResult, result_with_query))

    return literature_results


async def find_contradictions(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    claims_text = "\n".join(f"- {claim}" for claim in state["claims"])
    literature_text = format_literature_results(state["literature_results"])

    if not literature_text:
        updated_state = {**state, "contradictions": ["No literature results were found to compare against the claims."]}
        return typing.cast(research_agent.states.ResearchAuditState, updated_state)

    response = await audit_config.llm.ainvoke(f"""
        Compare the research claims against the academic literature snippets.

        Identify contradictions, conflicting evidence, or places where the literature
        weakens the claims. Be specific and cite paper titles when possible.

        Return only a bullet-point list. If there are no contradictions, return one
        bullet saying no clear contradictions were found in the retrieved literature.

        Claims:
        {claims_text}

        Literature:
        {literature_text}
        """)

    contradictions = parse_bullets(response.content)
    updated_state = {**state, "contradictions": contradictions}
    return typing.cast(research_agent.states.ResearchAuditState, updated_state)


def format_literature_results(results: list[research_agent.states.LiteratureResult]) -> str:
    formatted_results = []

    for index, result in enumerate(results, start=1):
        abstract = result.get("abstract") or result.get("summary") or "No abstract available."
        formatted_results.append(
            "\n".join(
                [
                    f"{index}. Source: {result.get('source')}",
                    f"Query: {result.get('query')}",
                    f"Title: {result.get('title')}",
                    f"Year: {result.get('year') or result.get('published')}",
                    f"URL: {result.get('url')}",
                    f"Snippet: {abstract}",
                ]
            )
        )

    return "\n\n".join(formatted_results)


async def find_logic_gaps(
    state: research_agent.states.ResearchAuditState,
    *,
    audit_config: research_agent.models.ResearchAuditConfig,
) -> research_agent.states.ResearchAuditState:
    claims_text = "\n".join(f"- {claim}" for claim in state["claims"])
    contradictions_text = "\n".join(f"- {contradiction}" for contradiction in state["contradictions"])

    response = await audit_config.llm.ainvoke(f"""
        Review the following claims and identify logical gaps, missing evidence,
        vague assumptions, unsupported conclusions, or places where further
        research is needed. Use the retrieved-literature contradictions as evidence
        when they expose a gap in the claims.

        Return only a bullet-point list.
        Do not include explanations or headings.

        Claims:
        {claims_text}

        Retrieved-literature contradictions:
        {contradictions_text}
        """)

    logic_gaps = parse_bullets(response.content)

    updated_state = {**state, "logic_gaps": logic_gaps}
    return typing.cast(research_agent.states.ResearchAuditState, updated_state)


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

    updated_state = {**state, "action_items": action_items}
    return typing.cast(research_agent.states.ResearchAuditState, updated_state)


def build_workflow(config: research_agent.models.ResearchAuditConfig):
    workflow = langgraph.graph.StateGraph(research_agent.states.ResearchAuditState)

    workflow.add_node("extract_claims", functools.partial(extract_claims, audit_config=config))
    workflow.add_node("plan_literature_queries", functools.partial(plan_literature_queries, audit_config=config))
    workflow.add_node("search_literature", functools.partial(search_literature, audit_config=config))
    workflow.add_node("find_contradictions", functools.partial(find_contradictions, audit_config=config))
    workflow.add_node("find_logic_gaps", functools.partial(find_logic_gaps, audit_config=config))
    workflow.add_node(
        "generate_action_items",
        functools.partial(generate_action_items, audit_config=config),
    )

    workflow.set_entry_point("extract_claims")

    workflow.add_edge("extract_claims", "plan_literature_queries")
    workflow.add_edge("plan_literature_queries", "search_literature")
    workflow.add_edge("search_literature", "find_contradictions")
    workflow.add_edge("find_contradictions", "find_logic_gaps")
    workflow.add_edge("find_logic_gaps", "generate_action_items")
    workflow.add_edge("generate_action_items", langgraph.graph.END)

    return workflow.compile()
