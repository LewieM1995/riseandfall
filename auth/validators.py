import re

def validate_password(password: str) -> tuple[bool, str | None]:
    """Validate password complexity and return specific error messages"""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, None

def validate_username(username: str) -> tuple[bool, str | None]:
    """Validate username format"""
    if len(username) < 3 or len(username) > 25:
        return False, "Username must be between 3 and 25 characters"
    
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_email(email: str) -> tuple[bool, str | None]:
    """Validate email format"""
    if not email or len(email) > 254:
        return False, "Invalid email address"
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, None