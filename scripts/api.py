import logging

import uvicorn

import research_agent.service


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_vars = research_agent.service.load_env_vars()
    uvicorn.run(
        "research_agent.api:app",
        host=env_vars.API_HOST_ADDRESS,
        port=env_vars.API_PORT,
    )


if __name__ == "__main__":
    main()
