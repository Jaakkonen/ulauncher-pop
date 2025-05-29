from __future__ import annotations

import logging
import unicodedata
from difflib import Match, SequenceMatcher
from functools import lru_cache

logger = logging.getLogger()


def _get_matching_blocks_native(query: str, text: str) -> list[Match]:
    return SequenceMatcher(None, query, text).get_matching_blocks()


# Using Levenshtein is ~10x faster, but some older distro releases might not package Levenshtein
# with these methods. So we fall back on difflib.SequenceMatcher (native Python library) to be sure.
try:
    from Levenshtein import editops, matching_blocks  # type: ignore[import-not-found]

    def _get_matching_blocks(query, text):
        return matching_blocks(editops(query, text), query, text)

except ImportError:
    logger.info(
        "Using fuzzy-matching with Native Python SequenceMatcher module. "
        "optional dependency 'python-Levenshtein' is recommended for better performance"
    )
    _get_matching_blocks = _get_matching_blocks_native


# convert strings to easily typable ones without accents, so ex "motorhead" matches "motörhead"
def _normalize(string: str) -> str:
    return unicodedata.normalize("NFD", string.casefold()).encode("ascii", "ignore").decode("utf-8")


@lru_cache(maxsize=1000)
def get_matching_blocks(query: str, text: str) -> tuple[list, int]:
    """
    Uses our _get_matching_blocks wrapper method to find the blocks using "Longest Common Substrings",
    :returns: list of tuples, containing the index and matching block, number of characters that matched
    """
    blocks = _get_matching_blocks(_normalize(query), _normalize(text))[:-1]
    output = []
    total_len = 0
    for _, text_index, length in blocks:
        output.append((text_index, text[text_index : text_index + length]))
        total_len += length
    return output, total_len


