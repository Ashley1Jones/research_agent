import typing


class LiteratureResult(typing.TypedDict, total=False):
    source: str
    query: str
    title: str | None
    abstract: str | None
    summary: str | None
    year: int | None
    published: str | None
    url: str | None
    citation_count: int | None
    authors: list[str | None]


class ResearchAuditState(typing.TypedDict):
    document_text: str
    claims: list[str]
    literature_queries: list[str]
    literature_results: list[LiteratureResult]
    contradictions: list[str]
    logic_gaps: list[str]
    action_items: list[str]
