import argparse
import json
import logging
import os
import time

import httpx

import research_agent.service


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "document_text",
        nargs="?",
        default=os.environ.get("DOCUMENT_TEXT", research_agent.service.DEFAULT_DOCUMENT_TEXT),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_vars = research_agent.service.load_env_vars()
    if env_vars.API_CLIENT_STARTUP_DELAY_SECONDS > 0:
        logging.info("Waiting %.1f seconds for the API to start", env_vars.API_CLIENT_STARTUP_DELAY_SECONDS)
        time.sleep(env_vars.API_CLIENT_STARTUP_DELAY_SECONDS)

    api_url = env_vars.create_api_url()

    response = httpx.post(
        f"{api_url}/audit",
        json={"document_text": args.document_text},
        timeout=120,
    )
    response.raise_for_status()

    logging.info("Audit response:\n%s", json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
