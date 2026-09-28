"""
backend/app/services/sanitize.py
Sanitization and PII redaction utilities before retaining memory or processing sensitive input.
Redacts full credit card numbers, CVVs, passwords, and OTPs.
"""

import re

# Regex for 13-19 digit card numbers (Visa, MC, Amex, Discover, etc.) with optional hyphens or spaces
CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")

# Regex for CVV / CVC (3-4 digits preceded or followed by cvv/cvc keyword)
CVV_PATTERN = re.compile(r"(?i)\b(?:cvv|cvc|security\s*code)\s*[:=]?\s*(\d{3,4})\b")

# Regex for OTPs / verification codes
OTP_PATTERN = re.compile(r"(?i)\b(?:otp|one[- ]time[- ]code|verification[- ]code)\s*[:=]?\s*(\d{4,8})\b")

# Regex for passwords / auth tokens
PASSWORD_PATTERN = re.compile(r"(?i)\b(?:password|passwd|pin)\s*[:=]?\s*(\S+)")


def mask_card_number(match: re.Match) -> str:
    """Masks credit card retaining only the last 4 digits."""
    raw = re.sub(r"[ -]", "", match.group(0))
    if len(raw) < 13 or len(raw) > 19:
        return match.group(0)
    return f"****-****-****-{raw[-4:]}"


def sanitize_for_memory(text: str) -> str:
    """
    Sanitizes text before writing to Hindsight memory.
    Masks payment card numbers, removes CVVs, passwords, and one-time codes.
    """
    if not text:
        return ""

    sanitized = text

    # Mask credit card numbers
    sanitized = CARD_PATTERN.sub(mask_card_number, sanitized)

    # Redact CVVs
    sanitized = CVV_PATTERN.sub("[CVV_REDACTED]", sanitized)

    # Redact OTPs
    sanitized = OTP_PATTERN.sub("[OTP_REDACTED]", sanitized)

    # Redact Passwords/PINs
    sanitized = PASSWORD_PATTERN.sub("password: [REDACTED]", sanitized)

    return sanitized
