# apiPasswordStrength.py

import math
import string

CHAR_SETS = {
    "lower": string.ascii_lowercase,
    "upper": string.ascii_uppercase,
    "digits": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.<>?/|\\"
}


def calculate_entropy(password: str) -> float:
    # Calculate password entropy based on E = L * log2(R).

    if not password:
        return 0.0

    R = 0  # size of total char set used

    # Detect which character sets appear in the password
    for charset in CHAR_SETS.values():
        if any(c in charset for c in password):
            R += len(charset)

    L = len(password)

    if R == 0:
        return 0.0

    entropy = L * math.log2(R)
    return entropy


def get_password_strength(password: str) -> str:
    # Return 'weak', 'medium', or 'strong' based only on entropy
    entropy = calculate_entropy(password)

    # Entropy thresholds
    if entropy < 40:
        return "weak"
    elif entropy < 60:
        return "medium"
    else:
        return "strong"


# Manual test
if __name__ == "__main__":
    pw = input("Enter password: ")
    e = calculate_entropy(pw)
    print(f"Entropy: {e:.2f} bits — Strength: {get_password_strength(pw)}")
