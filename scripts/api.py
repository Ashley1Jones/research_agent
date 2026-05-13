import asyncio
import logging

import uvicorn

import research_agent.service


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_vars = research_agent.service.load_env_vars()
    config = uvicorn.Config(
        app="research_agent.api:app",
        host=env_vars.API_BIND_ADDRESS,
        port=env_vars.API_PORT,
    )
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
