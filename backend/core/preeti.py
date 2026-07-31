"""Preeti ASCII Font to Devanagari Unicode Converter."""

import re

# Direct word replacements for common Preeti font headers found in government documents
PREETI_WORD_MAP = {
    "s[ifssf]": "कृषि",
    "nflu": "सूचना",
    "tYokq": "तथा",
    "c;f/": "संचार",
    "g]kfn": "नेपाल",
    "jftfj/0f": "वातावरण",
    "zfvf": "शाखा",
    "sfof{no": "कार्यालय",
    "ljsf;": "विकास",
    "efu": "भाग",
    "bknf": "दफा",
}

# Preeti character to Devanagari mapping dictionary
PREETI_CHAR_MAP = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९',
    '!': '१', '@': '२', '#': '३', '$': '४', '%': '५',
    '^': '६', '&': '७', '*': '७', '(': '८', ')': '९',
    'a': 'ब', 'b': 'द', 'c': 'अ', 'd': 'म', 'e': 'भ',
    'f': 'ि', 'g': 'न', 'h': 'ज', 'i': 'ष', 'j': 'व',
    'k': 'प', 'l': 'ि', 'm': 'म', 'n': 'ल', 'o': 'इ',
    'p': 'उ', 'q': 'त्र', 'r': 'र', 's': 'क', 't': 'त',
    'u': 'ग', 'v': 'ट', 'w': 'ध', 'x': 'ह', 'y': 'थ',
    'z': 'श',
    'A': 'ा', 'B': 'द्य', 'C': 'ऋ', 'D': 'ध', 'E': 'भ',
    'F': 'ँ', 'G': 'ग', 'H': 'ज', 'I': 'क्ष', 'J': 'व',
    'K': 'प', 'L': 'ि', 'M': 'म', 'N': 'ल', 'O': 'इ',
    'P': 'उ', 'Q': 'त्त', 'R': 'ृ', 'S': 'क', 'T': 'त',
    'U': 'ग', 'V': 'ठ', 'W': 'ध', 'X': 'ह', 'Y': 'थ',
    'Z': 'श',
    '~': 'ञ', '`': 'ञ', '{': 'र्', '}': 'ै', '[': 'ृ',
    ']': 'े', ':': 'ः', ';': 'च', "'": 'ू', '"': 'ू',
    '<': 'न्', '>': '्र', '?': 'रु', '/': '्र', '\\': '्',
    '|': '्', '+': 'ं', '=': '०', '_': '०'
}


def preeti_to_unicode(text: str) -> str:
    """Converts a Preeti ASCII encoded string into standard Devanagari Unicode.

    Handles pre-vowel matras (f -> ि), post-vowel matras, word fixes, and digits.
    """
    if not text:
        return ""

    # Check for direct word matches first
    words = text.split()
    converted_words = []

    for word in words:
        if word in PREETI_WORD_MAP:
            converted_words.append(PREETI_WORD_MAP[word])
            continue

        # Convert character by character
        chars = list(word)
        out_chars = []
        i = 0
        n = len(chars)

        while i < n:
            ch = chars[i]

            # Handle Preeti 'f' matra (preceding short 'i' matra)
            # In Preeti, 'f' comes before the letter (e.g. 'fs' -> 'कि')
            if ch == 'f' and i + 1 < n:
                next_ch = PREETI_CHAR_MAP.get(chars[i + 1], chars[i + 1])
                out_chars.append(next_ch + 'ि')
                i += 2
                continue

            # Standard char conversion
            conv = PREETI_CHAR_MAP.get(ch, ch)
            out_chars.append(conv)
            i += 1

        converted_words.append("".join(out_chars))

    return " ".join(converted_words)


def is_preeti_text(text: str) -> bool:
    """Detects whether raw extracted text contains Preeti ASCII font signatures."""
    if not text:
        return False

    signatures = ["s[ifssf]", "nflu", "tYokq", "c;f/", "g]kfn", "zfvf", "sfof{no"]
    for sig in signatures:
        if sig in text:
            return True

    # Check ratio of ASCII symbols common in Preeti font
    ascii_symbols = sum(1 for c in text if c in "[]};'\\/|@#$%^&*")
    if len(text) > 20 and (ascii_symbols / len(text)) > 0.05:
        return True

    return False
