import re


NON_ALPHANUMERIC_PATTERN = re.compile(r"[^a-z0-9]+")
WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_item_name(name: str) -> str:
    """
    Convert an item name into a consistent format for matching.
    """

    normalized_name = name.casefold().strip()

    normalized_name = NON_ALPHANUMERIC_PATTERN.sub(
        " ",
        normalized_name,
    )

    normalized_name = WHITESPACE_PATTERN.sub(
        " ",
        normalized_name,
    )

    return normalized_name.strip()
