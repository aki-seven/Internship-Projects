import re
from typing import Optional

def validate_pan(pan: str) -> bool:
    """
    Validate PAN: must be 13-19 digits, numeric only.
    Optional Luhn check.
    """
    if not re.match(r'^\d{13,19}$', pan):
        return False
    # Optional Luhn check
    return luhn_check(pan)

def luhn_check(pan: str) -> bool:
    """
    Perform Luhn algorithm check.
    """
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(pan)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10 == 0

def mask_pan(pan: str) -> str:
    """
    Mask PAN: show last 4 digits, mask the rest with *.
    Format as **** **** **** 1234
    """
    if len(pan) < 4:
        return "****"
    masked = "*" * (len(pan) - 4) + pan[-4:]
    # Insert spaces every 4 characters
    return ' '.join([masked[i:i+4] for i in range(0, len(masked), 4)])

def sanitize_log(data: dict) -> dict:
    """
    Sanitize data for logging: mask PAN if present.
    """
    sanitized = data.copy()
    if 'pan' in sanitized:
        sanitized['pan'] = mask_pan(sanitized['pan'])
    return sanitized