import re
from dataclasses import dataclass

from app.guardrails.policy import (
    BLOCKED_INPUT_PATTERNS,
    PII_ENTITY_TYPES,
)


@dataclass
class FilterResult:
    is_blocked: bool
    reason: str | None = None
    sanitized_text: str | None = None


SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "API_KEY"),
    (r"(?i)password\s*[:=]\s*\S+", "PASSWORD"),
    (r"(?i)(api[_-]?key|secret[_-]?key|token)\s*[:=]\s*\S+", "API_KEY"),
    (r"(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*", "AUTH_TOKEN"),
    (r"(?i)(postgres(?:ql)?|mysql|mongodb|redis)://\S+", "DATABASE_CREDENTIAL"),
]

PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "PHONE"),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD"),
    (r"\b\d{3}[-]?\d{2}[-]?\d{4}\b", "SSN"),
]


def check_input_blocked(text: str) -> FilterResult:
    text_lower = text.lower()
    for pattern in BLOCKED_INPUT_PATTERNS:
        if pattern in text_lower:
            return FilterResult(
                is_blocked=True,
                reason=f"Request appears to attempt extraction of protected information.",
            )
    for regex, label in SECRET_PATTERNS:
        if re.search(regex, text):
            return FilterResult(
                is_blocked=True,
                reason="Input contains what appears to be sensitive credentials.",
            )
    return FilterResult(is_blocked=False)


def sanitize_output(text: str) -> FilterResult:
    sanitized = text
    redacted = False

    for regex, label in SECRET_PATTERNS:
        if re.search(regex, sanitized):
            sanitized = re.sub(regex, f"[REDACTED_{label}]", sanitized)
            redacted = True

    for regex, label in PII_PATTERNS:
        matches = re.finditer(regex, sanitized)
        for match in matches:
            value = match.group()
            if label == "EMAIL":
                parts = value.split("@")
                masked = parts[0][:2] + "***@" + parts[1]
            elif label == "PHONE":
                masked = value[:3] + "***" + value[-2:]
            elif label == "CREDIT_CARD":
                masked = "****-****-****-" + value[-4:]
            else:
                masked = f"[REDACTED_{label}]"
            sanitized = sanitized.replace(value, masked)
            redacted = True

    return FilterResult(
        is_blocked=False,
        sanitized_text=sanitized if redacted else None,
    )


def apply_guardrails(user_input: str, bot_output: str) -> tuple[FilterResult, str]:
    input_check = check_input_blocked(user_input)
    if input_check.is_blocked:
        return input_check, ""

    output_check = sanitize_output(bot_output)
    final_output = output_check.sanitized_text or bot_output
    return FilterResult(is_blocked=False), final_output
