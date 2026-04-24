from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(UTC)
