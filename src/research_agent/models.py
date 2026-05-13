import dataclasses
import typing

import pydantic
import langchain_ollama


@dataclasses.dataclass(frozen=True)
class ResearchAuditConfig:
    llm: langchain_ollama.ChatOllama
    default_claims: tuple[str, ...]
    action_prefix: str
    literature_query_count: int
    literature_result_limit: int


class EnvVars(pydantic.BaseModel):
    MODEL_TYPE: str
    MODEL_HOST_ADDRESS: str
    MODEL_HOST_PORT: int
    API_BIND_ADDRESS: str
    API_CLIENT_HOST_ADDRESS: str
    API_PORT: int
    API_CLIENT_STARTUP_DELAY_SECONDS: float

    def create_url(self) -> str:
        return f"http://{self.MODEL_HOST_ADDRESS}:{self.MODEL_HOST_PORT}"

    def create_api_url(self) -> str:
        return f"http://{self.API_CLIENT_HOST_ADDRESS}:{self.API_PORT}"


class ResearchAuditRequest(pydantic.BaseModel):
    document_text: str


class ResearchAuditResponse(pydantic.BaseModel):
    claims: list[str]
    literature_queries: list[str]
    literature_results: list[dict[str, typing.Any]]
    contradictions: list[str]
    logic_gaps: list[str]
    action_items: list[str]
