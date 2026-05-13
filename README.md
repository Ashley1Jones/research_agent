# Research Agent

Research Agent is an async Python service for auditing short research or technical documents with a local Ollama-backed language model. It extracts claims, identifies logic gaps, and generates follow-up action items through a LangGraph workflow.

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

```text
.
├── Dockerfile
├── docker-compose.yml
├── development.env
├── pyproject.toml
├── scripts
│   ├── api.py
│   ├── client.py
│   └── main.py
└── src
    └── research_agent
        ├── api.py
        ├── models.py
        ├── service.py
        ├── states.py
        └── workflow.py
```

## Requirements

- Python 3.13 or newer
- `uv`
- Docker and Docker Compose, if running containerized services
- Ollama running locally or via Docker Compose
- The configured Ollama model pulled locally, by default `qwen2.5:3b`

## Configuration

Runtime configuration is stored in [development.env](development.env):

```env
MODEL_TYPE=qwen2.5:3b
MODEL_HOST_ADDRESS=localhost
MODEL_HOST_PORT=11434
API_BIND_ADDRESS=127.0.0.1
API_CLIENT_HOST_ADDRESS=127.0.0.1
API_PORT=8000
API_CLIENT_STARTUP_DELAY_SECONDS=8
```

For local execution, `MODEL_HOST_ADDRESS=localhost` targets an Ollama server running on the host machine.

For Docker Compose, the API service overrides:

```env
MODEL_HOST_ADDRESS=ollama
API_BIND_ADDRESS=0.0.0.0
```

## Setup

Install dependencies:

```bash
uv sync
```

Pull the default Ollama model:

```bash
ollama pull qwen2.5:3b
```

Start Ollama locally if you are not using Docker Compose:

```bash
ollama serve
```

## Run the CLI

```bash
set -a; . ./development.env; set +a
.venv/bin/python scripts/main.py
```

The CLI runs the built-in sample document through the workflow and logs:

- claims
- logic gaps
- action items

## Run the API Locally

Start the API:

```bash
set -a; . ./development.env; set +a
.venv/bin/python scripts/api.py
```

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

## Development

Compile-check the project:

```bash
.venv/bin/python -m py_compile scripts/main.py scripts/api.py scripts/client.py src/research_agent/*.py
```

Validate Docker Compose configuration:

```bash
docker compose --env-file development.env config
```

Build the API image:

```bash
docker compose --env-file development.env build api
```

## Troubleshooting

If the CLI or API cannot connect to Ollama, verify that Ollama is reachable:

```bash
curl http://localhost:11434/api/tags
```

If the API runs in Docker Compose but cannot reach the model, make sure the Compose override is active:

```yaml
MODEL_HOST_ADDRESS: ollama
```

If the API starts but model calls fail, confirm that the model exists in the Ollama instance used by the service:

```bash
ollama list
```

or, for Docker Compose:

```bash
docker compose --env-file development.env exec ollama ollama list
```

## TODO

- Add Postgres logging.
- Add research tool.
- Add unit tests.
- Add CI/CD checks.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
