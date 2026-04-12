import re
from typing import Optional


PAN_REGEX = re.compile(r"^[0-9]{13,19}$")


def mask_pan(pan: str) -> str:
    """Mask the PAN except for the last four digits.

    This avoids exposing sensitive card data in API responses or logs.
    """
    safe = pan[-4:]
    masked = "*" * max(0, len(pan) - 4)
    # Group into 4-digit blocks for readability without exposing digits.
    grouped = " ".join(masked[i : i + 4] for i in range(0, len(masked), 4))
    return f"{grouped} {safe}" if grouped else safe


def luhn_check(pan: str) -> bool:
    """Validate PAN using the Luhn checksum algorithm."""
    total = 0
    reverse_digits = pan[::-1]
    for idx, char in enumerate(reverse_digits):
        digit = int(char)
        if idx % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate_pan(pan: str, require_luhn: bool = True) -> Optional[str]:
    normalized = pan.replace(" ", "").replace("-", "")
    if not PAN_REGEX.fullmatch(normalized):
        return None
    if require_luhn and not luhn_check(normalized):
        return None
    return normalized
