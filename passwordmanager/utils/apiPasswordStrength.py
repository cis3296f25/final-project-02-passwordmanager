# apiPasswordStrength.py
import math

def get_password_strength(password: str) -> str:
    # Returns: 'weak', 'medium', or 'strong' based on entropy calculation
    if not password:
        return "weak"
    
    length = len(password)
    char_set_size = 0
    
    # Detect character set
    has_lowercase = any(c.islower() for c in password)
    has_uppercase = any(c.isupper() for c in password)
    has_numbers = any(c.isdigit() for c in password)
    has_shift_numbers = any(c in "!@#$%^&*()" for c in password)
    
    # Count other symbols (not shift+number keys, not alphanumeric)
    other_symbols = set()
    for c in password:
        if not c.isalnum() and c not in "!@#$%^&*()":
            other_symbols.add(c)
    has_other_symbols = len(other_symbols) > 0
    
    # Calculate character set size
    if has_lowercase:
        char_set_size += 26
    if has_uppercase:
        char_set_size += 26
    if has_numbers:
        char_set_size += 10
    if has_shift_numbers:
        char_set_size += 10
    if has_other_symbols:
        # Industry-standard modifier for other symbols (typically ~20-30 common symbols)
        char_set_size += 20
    
    # Calculate entropy: H = length * log_2(charSetSize)
    entropy = length * math.log2(char_set_size)
    
    # Classify strength
    if entropy >= 80:
        return "strong"
    elif entropy > 40:
        return "medium"
    else:
        return "weak"
