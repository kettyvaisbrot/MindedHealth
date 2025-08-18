from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def parse_date_from_str(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Failed to parse date from string: {date_str}")
        return None