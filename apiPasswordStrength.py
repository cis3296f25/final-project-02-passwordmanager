# apiPasswordStrength.py

def get_password_score(password: str) -> int:
    # Returns a strength score from 0–5
    score = 0

    if len(password) >= 8:
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c in "@$!%*?&#" for c in password):
        score += 1

    return score


def get_password_strength(password: str) -> str:
    #Returns: 'weak', 'medium', or 'strong'
    score = get_password_score(password)

    if score <= 2:
        return "weak"
    elif score in (3, 4):
        return "medium"
    else:
        return "strong"


""" if __name__ == "__main__":
    test_pw = input("Enter password to test: ")
    print(check_password_strength(test_pw)) """
