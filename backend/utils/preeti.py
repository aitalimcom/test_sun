"""Preeti to Unicode Nepali converter utility."""

PREETI_MAP = {
    "c": "अ", "cf": "आ", "O": "इ", "pm": "ई", "p": "उ", "C": "ऋ",
    "P": "ए", "Pl": "ऐ", "cf]": "ओ", "cfW": "औ", "s": "क", "v": "ख", "u": "ग",
    "3": "घ", "ª": "ङ", "r": "च", "5": "छ", "h": "ज", "em": "झ", "n": "ञ",
    "6": "ट", "7": "ठ", "8": "ड", "9": "ढ", "0": "ण", "t": "त", "y": "थ",
    "b": "द", "w": "ध", "g": "न", "km": "फ", "a": "ब", "e": "भ",
    "d": "म", "o": "य", "j": "व", "z": "श", "if": "ष",
    "i": "स", "x": "ह", "IF": "क्ष", "q": "त्र", "7g": "ज्ञ",
    "f": "ा", "L": "ी", "F": "ृ", "E": "े",
    "EE": "ै", "f]": "ो", "fW": "ौ",
    "1": "१", "2": "२", "3": "३", "4": "४", "5": "५", "6": "६", "7": "७", "8": "८", "9": "९", "0": "०"
}

def preeti_to_unicode(text: str) -> str:
    """Convert Preeti font encoded text to standard Devanagari Unicode."""
    if not text:
        return ""
    result = text
    for preeti_char, unicode_char in PREETI_MAP.items():
        if preeti_char:
            result = result.replace(preeti_char, unicode_char)
    return result
