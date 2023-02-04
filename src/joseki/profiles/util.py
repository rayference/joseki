"""Utility module."""
import datetime


def utcnow() -> str:
    """Get current UTC time.
    
    Returns:
        ISO 8601 formatted UTC timestamp.
    """
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()
