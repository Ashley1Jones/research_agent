from typing import TypedDict


class ResearchAuditState(TypedDict):
    document_text: str
    claims: list[str]
    logic_gaps: list[str]
    action_items: list[str]
