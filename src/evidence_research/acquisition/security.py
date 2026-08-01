from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import unquote

_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)
_HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ј": "j",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Χ": "X",
    "α": "a", "β": "b", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "χ": "x",
})


@dataclass(frozen=True)
class SensitiveFinding:
    data_class: str
    start: int
    end: int


_SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I)),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}={0,2}\b", re.I)),
    ("api_key", re.compile(r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")),
    ("secret_assignment", re.compile(r"\b(?:api[_ -]?key|secret|password|access[_ -]?token)\s*[:=]\s*[^\s,;]{6,}", re.I)),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("payment_card", re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)")),
    ("phone", re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)")),
)


def normalize_for_detection(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).translate(_ZERO_WIDTH).translate(_HOMOGLYPHS)
    return " ".join(value.split())


def compact_for_detection(value: str) -> str:
    return re.sub(r"[^a-z0-9\u0600-\u06ff]+", "", normalize_for_detection(value).lower())


def decoded_views(value: str, *, max_payload_chars: int = 16_384) -> tuple[str, ...]:
    views: list[str] = []
    percent = unquote(value)
    if percent != value:
        views.append(percent[:max_payload_chars])
    for token in re.findall(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])", value):
        try:
            padded = token + "=" * ((4 - len(token) % 4) % 4)
            decoded = base64.b64decode(padded, validate=True)
            text = decoded.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        if text and sum(character.isprintable() for character in text) / len(text) >= 0.85:
            views.append(text[:max_payload_chars])
    for token in re.findall(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{24,}(?![0-9A-Fa-f])", value):
        if len(token) % 2:
            continue
        try:
            text = bytes.fromhex(token).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
        if text and sum(character.isprintable() for character in text) / len(text) >= 0.85:
            views.append(text[:max_payload_chars])
    return tuple(dict.fromkeys(views))


def find_sensitive_data(value: str) -> tuple[SensitiveFinding, ...]:
    findings: list[SensitiveFinding] = []
    occupied: list[tuple[int, int]] = []
    for data_class, pattern in _SENSITIVE_PATTERNS:
        for match in pattern.finditer(value):
            start, end = match.span()
            if any(start < prior_end and end > prior_start for prior_start, prior_end in occupied):
                continue
            findings.append(SensitiveFinding(data_class, start, end))
            occupied.append((start, end))
    return tuple(sorted(findings, key=lambda item: item.start))


def redact_sensitive_content(value: str) -> tuple[str, tuple[str, ...]]:
    findings = find_sensitive_data(value)
    if not findings:
        return value, ()
    pieces: list[str] = []
    cursor = 0
    classes: list[str] = []
    for finding in findings:
        pieces.append(value[cursor:finding.start])
        pieces.append(f"[REDACTED:{finding.data_class.upper()}]")
        cursor = finding.end
        classes.append(finding.data_class)
    pieces.append(value[cursor:])
    return "".join(pieces), tuple(dict.fromkeys(classes))
