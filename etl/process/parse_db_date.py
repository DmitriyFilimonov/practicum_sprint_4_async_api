from datetime import datetime
from zoneinfo import ZoneInfo


def parse_db_date(value: str) -> datetime:
    if "." in value:
        base, microseconds = value.split(".")
        microseconds = microseconds.ljust(6, "0")
        value = f"{base}.{microseconds}"
    return datetime.fromisoformat(value).replace(tzinfo=ZoneInfo("Etc/UTC"))