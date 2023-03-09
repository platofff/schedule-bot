from datetime import datetime, timezone


def utc_timestamp_ms() -> int:
    dt = datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    return round(utc_time.timestamp() * 1000)


def js_weekday(dt: datetime) -> int:
    w = dt.weekday() + 1
    if w == 7:
        return 0
    return w
