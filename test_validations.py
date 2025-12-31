import pytest
from validators.auth_validators import validate_password, validate_username, validate_email

class TestValidatePassword:
    """Test password validation"""
    
    def test_valid_password(self):
        """Test with a valid password"""
        valid, error = validate_password("SecurePass123!")
        assert valid is True
        assert error is None
    
    def test_valid_password_all_special_chars(self):
        """Test with various special characters"""
        passwords = [
            "Password123!",
            "Password123@",
            "Password123#",
            "Password123$",
            "Password123%",
            "Password123^",
            "Password123&",
            "Password123*",
            "Password123()",
            "Password123,.",
            "Password123?",
            'Password123"',
            "Password123:",
            "Password123{}",
            "Password123|",
            "Password123<>",
        ]
        for pwd in passwords:
            valid, error = validate_password(pwd)
            assert valid is True, f"Failed for password: {pwd}"
            assert error is None
    
    def test_password_too_short(self):
        """Test password that's too short"""
        valid, error = validate_password("Short1!")
        assert valid is False
        assert error == "Password must be at least 12 characters long"
    
    def test_password_exactly_12_chars(self):
        """Test password with exactly 12 characters"""
        valid, error = validate_password("Password123!")
        assert valid is True
        assert error is None
    
    def test_password_11_chars(self):
        """Test password with 11 characters (boundary)"""
        valid, error = validate_password("Password12!")
        assert valid is False
        assert error == "Password must be at least 12 characters long"
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter"""
        valid, error = validate_password("password123!")
        assert valid is False
        assert error == "Password must contain at least one uppercase letter"
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter"""
        valid, error = validate_password("PASSWORD123!")
        assert valid is False
        assert error == "Password must contain at least one lowercase letter"
    
    def test_password_no_digit(self):
        """Test password without digit"""
        valid, error = validate_password("PasswordOnly!")
        assert valid is False
        assert error == "Password must contain at least one digit"
    
    def test_password_no_special_char(self):
        """Test password without special character"""
        valid, error = validate_password("Password1234")
        assert valid is False
        assert error == "Password must contain at least one special character"
    
    def test_password_empty(self):
        """Test with empty password"""
        valid, error = validate_password("")
        assert valid is False
        assert error == "Password must be at least 12 characters long"
    
    def test_password_very_long(self):
        """Test with very long password"""
        long_password = "SecurePassword123!" * 10
        valid, error = validate_password(long_password)
        assert valid is True
        assert error is None
    
    def test_password_multiple_failures(self):
        """Test that first validation error is returned"""
        # Too short AND missing uppercase
        valid, error = validate_password("short1!")
        assert valid is False
        assert error == "Password must be at least 12 characters long"


class TestValidateUsername:
    """Test username validation"""
    
    def test_valid_username_lowercase(self):
        """Test valid lowercase username"""
        valid, error = validate_username("johndoe")
        assert valid is True
        assert error is None
    
    def test_valid_username_mixed_case(self):
        """Test valid mixed case username"""
        valid, error = validate_username("JohnDoe")
        assert valid is True
        assert error is None
    
    def test_valid_username_with_numbers(self):
        """Test valid username with numbers"""
        valid, error = validate_username("user123")
        assert valid is True
        assert error is None
    
    def test_valid_username_with_underscore(self):
        """Test valid username with underscore"""
        valid, error = validate_username("john_doe")
        assert valid is True
        assert error is None
    
    def test_valid_username_with_hyphen(self):
        """Test valid username with hyphen"""
        valid, error = validate_username("john-doe")
        assert valid is True
        assert error is None
    
    def test_valid_username_all_valid_chars(self):
        """Test username with all valid character types"""
        valid, error = validate_username("User_Name-123")
        assert valid is True
        assert error is None
    
    def test_username_too_short(self):
        """Test username that's too short"""
        valid, error = validate_username("ab")
        assert valid is False
        assert error == "Username must be between 3 and 25 characters"
    
    def test_username_exactly_3_chars(self):
        """Test username with exactly 3 characters (boundary)"""
        valid, error = validate_username("abc")
        assert valid is True
        assert error is None
    
    def test_username_exactly_25_chars(self):
        """Test username with exactly 25 characters (boundary)"""
        valid, error = validate_username("a" * 25)
        assert valid is True
        assert error is None
    
    def test_username_too_long(self):
        """Test username that's too long"""
        valid, error = validate_username("a" * 26)
        assert valid is False
        assert error == "Username must be between 3 and 25 characters"
    
    def test_username_with_spaces(self):
        """Test username with spaces (invalid)"""
        valid, error = validate_username("john doe")
        assert valid is False
        assert error == "Username can only contain letters, numbers, underscores, and hyphens"
    
    def test_username_with_special_chars(self):
        """Test username with invalid special characters"""
        invalid_usernames = [
            "john@doe",
            "john!doe",
            "john#doe",
            "john$doe",
            "john%doe",
            "john&doe",
            "john.doe",
        ]
        for username in invalid_usernames:
            valid, error = validate_username(username)
            assert valid is False, f"Failed for username: {username}"
            assert error == "Username can only contain letters, numbers, underscores, and hyphens"
    
    def test_username_empty(self):
        """Test with empty username"""
        valid, error = validate_username("")
        assert valid is False
        assert error == "Username must be between 3 and 25 characters"
    
    def test_username_only_numbers(self):
        """Test username with only numbers"""
        valid, error = validate_username("12345")
        assert valid is True
        assert error is None
    
    def test_username_only_underscores_hyphens(self):
        """Test username with only underscores and hyphens"""
        valid, error = validate_username("_-_-_")
        assert valid is True
        assert error is None


class TestValidateEmail:
    """Test email validation"""
    
    def test_valid_email_basic(self):
        """Test valid basic email"""
        valid, error = validate_email("user@example.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_with_dots(self):
        """Test valid email with dots in local part"""
        valid, error = validate_email("user.name@example.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_with_plus(self):
        """Test valid email with plus sign"""
        valid, error = validate_email("user+tag@example.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_with_numbers(self):
        """Test valid email with numbers"""
        valid, error = validate_email("user123@example456.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_subdomain(self):
        """Test valid email with subdomain"""
        valid, error = validate_email("user@mail.example.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_with_hyphen(self):
        """Test valid email with hyphen in domain"""
        valid, error = validate_email("user@ex-ample.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_with_underscore(self):
        """Test valid email with underscore in local part"""
        valid, error = validate_email("user_name@example.com")
        assert valid is True
        assert error is None
    
    def test_valid_email_long_tld(self):
        """Test valid email with longer TLD"""
        valid, error = validate_email("user@example.museum")
        assert valid is True
        assert error is None
    
    def test_email_no_at_symbol(self):
        """Test email without @ symbol"""
        valid, error = validate_email("userexample.com")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_no_domain(self):
        """Test email without domain"""
        valid, error = validate_email("user@")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_no_local_part(self):
        """Test email without local part"""
        valid, error = validate_email("@example.com")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_no_tld(self):
        """Test email without TLD"""
        valid, error = validate_email("user@example")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_invalid_tld_too_short(self):
        """Test email with TLD that's too short"""
        valid, error = validate_email("user@example.c")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_multiple_at_symbols(self):
        """Test email with multiple @ symbols"""
        valid, error = validate_email("user@@example.com")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_spaces(self):
        """Test email with spaces"""
        valid, error = validate_email("user name@example.com")
        assert valid is False
        assert error == "Invalid email format"
    
    def test_email_empty(self):
        """Test with empty email"""
        valid, error = validate_email("")
        assert valid is False
        assert error == "Invalid email address"
    
    def test_email_none(self):
        """Test with None email"""
        valid, error = validate_email(None)
        assert valid is False
        assert error == "Invalid email address"
    
    def test_email_too_long(self):
        """Test email that exceeds 254 characters"""
        long_email = "a" * 250 + "@example.com"
        valid, error = validate_email(long_email)
        assert valid is False
        assert error == "Invalid email address"
    
    def test_email_exactly_254_chars(self):
        """Test email with exactly 254 characters (boundary)"""
        # Create email that's exactly 254 characters
        local_part = "a" * 240
        email = f"{local_part}@example.com"  # 240 + 1 + 11 + 1 + 3 = 256
        email = "a" * 241 + "@example.com"  # 253 chars total
        valid, error = validate_email(email)
        assert valid is True
        assert error is None
    
    def test_email_with_consecutive_dots(self):
        """Test email with consecutive dots (technically invalid but passes basic regex)"""
        valid, error = validate_email("user..name@example.com")
        assert valid is True
    
    def test_email_starting_with_dot(self):
        """Test email starting with dot"""
        valid, error = validate_email(".user@example.com")
        assert valid is True
    
    def test_email_ending_with_dot(self):
        """Test email ending with dot in local part"""
        valid, error = validate_email("user.@example.com")
        assert valid is True


# Run with: pytest test_validation.py -v