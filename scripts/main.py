import asyncio
import logging

import research_agent.service
import research_agent.logging_config


async def run() -> None:
    research_agent.logging_config.configure_logging()

    correlation_id = research_agent.logging_config.generate_correlation_id()
    token = research_agent.logging_config.set_correlation_id(correlation_id)

    env_vars = research_agent.service.load_env_vars()
    config = research_agent.service.build_audit_config(env_vars)
    result = await research_agent.service.run_audit(research_agent.service.DEFAULT_DOCUMENT_TEXT, config)

    logging.info("Claims:")
    for claim in result["claims"]:
        logging.info("- %s", claim)

    logging.info("\nLiterature queries:")
    for query in result["literature_queries"]:
        logging.info("- %s", query)

    logging.info("\nContradictions:")
    for contradiction in result["contradictions"]:
        logging.info("- %s", contradiction)

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
