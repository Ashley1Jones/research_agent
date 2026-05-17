# Research Agent

This project is a personal project as a first step to learn about LLM workflows and the frameworks that exists to create them. This project 'Research Agent' is a Python service for auditing short research or technical documents with a local Ollama-backed language model. It extracts claims, identifies logic gaps, and generates follow-up action items through a LangGraph workflow.

The project can be run as a local CLI, as a FastAPI service, or through Docker Compose alongside an Ollama container.

## Features

- Extracts research or technical claims from input text.
- Reviews claims for missing evidence, vague assumptions, unsupported conclusions, and other logic gaps.
- Generates action items for follow-up experiments or supporting evidence.
- Provides both CLI and HTTP API entry points.
- Uses async execution throughout the CLI, API client, FastAPI app, and LangGraph workflow.
- Supports local development with `uv`.
- Includes Docker and Docker Compose support for running the API with Ollama.

## Tech Stack

- Python 3.13+
- LangGraph
- LangChain Ollama
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- Docker Compose

## Project Structure

### Source Package

| File | Summary |
| --- | --- |
| `src/research_agent/__init__.py` | Marks `research_agent` as an importable Python package. |
| `src/research_agent/api.py` | Defines the FastAPI app, request correlation middleware, health endpoint, and `/audit` endpoint. |
| `src/research_agent/http_client.py` | Provides shared async HTTPX client helpers and request/response logging hooks for outbound HTTP calls. |
| `src/research_agent/logging_config.py` | Configures application logging and stores correlation IDs in a context variable so logs can include request context. |
| `src/research_agent/models.py` | Defines configuration, environment, request, and response models used by the CLI and API. |
| `src/research_agent/research_tools.py` | Defines async literature search tools for Semantic Scholar and arXiv, plus helper logic for normalizing tool results. |
| `src/research_agent/service.py` | Contains shared service setup, default audit inputs, environment loading, LLM configuration, and audit workflow execution. |
| `src/research_agent/states.py` | Defines TypedDict state objects passed through the LangGraph research audit workflow. |
| `src/research_agent/workflow.py` | Builds the LangGraph workflow and contains the async workflow nodes for claim extraction, literature search, contradiction detection, logic gap detection, and action item generation. |

### Scripts

| File | Summary |
| --- | --- |
| `scripts/api.py` | Starts the FastAPI application with Uvicorn using host and port values from the environment. |
| `scripts/client.py` | Calls the running API with document text, optionally waits for startup, and logs the JSON audit response. |
| `scripts/main.py` | Runs the audit workflow directly from the command line using the built-in sample document. |

## Requirements

- Python 3.13 or newer
- `uv`
- Docker and Docker Compose, if running containerized services
- Ollama running locally or via Docker Compose
- The configured Ollama model pulled locally, by default `qwen2.5:3b`

## Configuration

Runtime configuration is stored in [development.env](development.env):

For local execution, `MODEL_HOST_ADDRESS=localhost` targets an Ollama server running on the host machine.

## Setup for Development

Install dependencies:

```bash
uv sync
```

Pull the default Ollama model:

```bash
docker exec -it research-auditor-ollama ollama pull qwen2.5:3b
```

## Run with Docker Compose

Build and start the API and Ollama:

```bash
docker compose --env-file development.env up --build
```

The API is exposed on the configured `API_PORT`, defaulting to `8000`.

If the Ollama model is not already present in the `ollama_models` volume, pull it into the running Ollama container:

```bash
docker compose --env-file development.env exec ollama ollama pull qwen2.5:3b
```

Then call the API:

```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_text":"Our system improves research quality and reduces hallucinations."}'
```

Stop services:

```bash
docker compose --env-file development.env down
```

## Run the API Locally

There is a launch.json so you can launch and debug the scripts via vscode.  

Check health:

```bash
curl http://127.0.0.1:8000/health
```

Audit a document:

```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_text":"Our system improves research quality and reduces hallucinations."}'
```

## Run the API Client

In another terminal, with the API running:

```bash
set -a; . ./development.env; set +a
API_CLIENT_STARTUP_DELAY_SECONDS=0 .venv/bin/python scripts/client.py "Our system improves research quality and reduces hallucinations."
```

If no document text argument is provided, the client uses the built-in sample document.

## API

### `GET /health`

Returns:

```json
{
  "status": "ok"
}
```

### `POST /audit`

Request:

```json
{
  "document_text": "Your research or technical document text."
}
```

Response:

```json
{
  "claims": ["..."],
  "logic_gaps": ["..."],
  "action_items": ["..."]
}
```

## TODO

- Add Postgres logging.
- Add unit tests.
- Add CI/CD checks.
- More sophisticated document parsing.
- More sophisticated pipeline for extracting information from document.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
