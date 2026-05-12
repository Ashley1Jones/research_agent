from dataclasses import dataclass

import pydantic
from langchain_ollama import ChatOllama


@dataclass(frozen=True)
class ResearchAuditConfig:
    llm: ChatOllama
    default_claims: tuple[str, ...]
    action_prefix: str


class EnvVars(pydantic.BaseModel):
    MODEL_TYPE: str
    MODEL_HOST_ADDRESS: str
    MODEL_HOST_PORT: int

    def create_url(self) -> str:
        return f"http://{self.MODEL_HOST_ADDRESS}:{self.MODEL_HOST_PORT}"
