"""Nepali Text Normalizer — Hraswa/Dirga, Sibilant, and Nasal unification."""

import re
from core.preeti import preeti_to_unicode, is_preeti_text

# Characters mapping dictionary for Devanagari normalization
DEVANA_NORMALIZATION = {
    # Dirga Vowels to Hraswa
    'ई': 'इ',
    'ी': 'ि',
    'ऊ': 'उ',
    'ू': 'ु',
    # Sibilants श, ष -> स
    'श': 'स',
    'ष': 'स',
    # Nasal ण -> न
    'ण': 'न',
    # Devanagari Numerals to ASCII digits
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
}


def normalize_nepali_text(text: str) -> str:
    """Normalizes Nepali text for high-recall BM25 / lexical RAG indexing & searching.

    1. Detects and converts Preeti font ASCII if present.
    2. Forces all Dirga vowels to Hraswa.
    3. Standardizes sibilants (श/ष -> स) and nasals (ण -> न).
    """
    if not text:
        return ""

    # Step 1: Preeti font conversion if legacy ASCII detected
    if is_preeti_text(text):
        text = preeti_to_unicode(text)

    # Step 2: Character-level normalization
    normalized_chars = []
    for ch in text:
        normalized_chars.append(DEVANA_NORMALIZATION.get(ch, ch))

    normalized_text = "".join(normalized_chars)

    # Remove extra spaces/newlines
    normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()
    return normalized_text
