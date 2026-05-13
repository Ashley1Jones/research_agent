import asyncio
import logging

import research_agent.service


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_vars = research_agent.service.load_env_vars()
    config = research_agent.service.build_audit_config(env_vars)
    result = await research_agent.service.run_audit(research_agent.service.DEFAULT_DOCUMENT_TEXT, config)

    logging.info("Claims:")
    for claim in result["claims"]:
        logging.info("- %s", claim)

    logging.info("\nLogic gaps:")
    for gap in result["logic_gaps"]:
        logging.info("- %s", gap)

    logging.info("\nAction items:")
    for item in result["action_items"]:
        logging.info("- %s", item)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
