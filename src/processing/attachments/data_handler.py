import re
from rapidfuzz import fuzz
import re


def regex_match(text, pattern):
    """
    Performs a regex-based flexible match for the pattern in the text.

    Args:
        text (str): The text to search.
        pattern (str): The pattern to match.

    Returns:
        bool: True if a match is found, False otherwise.
    """
    flexible_pattern = re.escape(pattern).replace(r"\-", "[-\s]?").replace(r"\s", r"\s*")
    return bool(re.search(flexible_pattern, text, re.IGNORECASE))


def fuzzy_match(text, pattern, threshold=90):
    """
    Performs a fuzzy match using the rapidfuzz library.

    Args:
        text (str): The text to search.
        pattern (str): The pattern to match.
        threshold (int): The minimum similarity ratio to consider a match.

    Returns:
        bool: True if a match is found above the threshold, False otherwise.
    """
    return fuzz.partial_ratio(text, pattern) >= threshold


