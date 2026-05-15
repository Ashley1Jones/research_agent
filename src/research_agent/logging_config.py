import contextvars
import logging
import uuid

_correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id",
    default=None,
)


def generate_correlation_id() -> str:
    return uuid.uuid4().hex


def set_correlation_id(correlation_id: str) -> contextvars.Token[str | None]:
    return _correlation_id_var.set(correlation_id)


def reset_correlation_id(token: contextvars.Token[str | None]) -> None:
    _correlation_id_var.reset(token)


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


def get_correlation_id() -> str | None:
    return _correlation_id_var.get()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    correlation_filter = CorrelationIdFilter()

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(correlation_filter)
