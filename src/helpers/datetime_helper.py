from datetime import datetime, timezone

# Compatibility shim: original file is named `datetime__helper.py` (double underscore).
# Create this file so imports using `helpers.datetime_helper` succeed.

def utcnow() -> datetime:
    return datetime.now(timezone.utc)
