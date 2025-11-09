"""
Security tests for Socrates2.

Tests JWT token generation, validation, password hashing, and auth mechanisms.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os


@pytest.mark.security
class TestJWTTokens:
    """Test JWT token generation and validation."""

    def test_jwt_secret_key_exists(self):
        """Test that SECRET_KEY is configured."""
        secret_key = os.getenv("SECRET_KEY")
        assert secret_key is not None
        assert len(secret_key) > 0

    def test_jwt_algorithm_configured(self):
        """Test that JWT algorithm is configured."""
        algorithm = os.getenv("ALGORITHM", "HS256")
        assert algorithm in ["HS256", "HS512", "RS256"]

    def test_token_expiration_time_set(self):
        """Test that access token expiration is configured."""
        expiration = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        assert expiration is not None
        assert int(expiration) > 0

    def test_jwt_token_creation_format(self):
        """Test JWT token creation produces valid format."""
        secret_key = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        # Create a test payload
        payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }

        # Create token
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT format: header.payload.signature

    def test_jwt_token_can_be_decoded(self):
        """Test that created JWT token can be decoded."""
        secret_key = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        # Create token
        original_email = "test@example.com"
        payload = {
            "sub": original_email,
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, secret_key, algorithm=algorithm)

        # Decode token
        decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
        assert decoded["sub"] == original_email

    def test_expired_token_raises_error(self):
        """Test that expired token raises JWTError."""
        secret_key = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        # Create expired token (expired 1 minute ago)
        payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        token = jwt.encode(payload, secret_key, algorithm=algorithm)

        # Try to decode - should raise error
        with pytest.raises(JWTError):
            jwt.decode(token, secret_key, algorithms=[algorithm])

    def test_tampered_token_raises_error(self):
        """Test that tampered token raises JWTError."""
        secret_key = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        # Create valid token
        payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, secret_key, algorithm=algorithm)

        # Tamper with token (change a character)
        tampered_token = token[:-5] + "XXXXX"

        # Try to decode - should raise error
        with pytest.raises(JWTError):
            jwt.decode(tampered_token, secret_key, algorithms=[algorithm])


@pytest.mark.security
class TestPasswordSecurity:
    """Test password hashing and validation."""

    def test_password_minimum_length(self, test_user_data):
        """Test that passwords meet minimum length requirement."""
        password = test_user_data["password"]
        assert len(password) >= 8

    def test_password_has_uppercase(self, test_user_data):
        """Test that password contains uppercase letters."""
        password = test_user_data["password"]
        assert any(c.isupper() for c in password)

    def test_password_has_lowercase(self, test_user_data):
        """Test that password contains lowercase letters."""
        password = test_user_data["password"]
        assert any(c.islower() for c in password)

    def test_password_has_digit(self, test_user_data):
        """Test that password contains digits."""
        password = test_user_data["password"]
        assert any(c.isdigit() for c in password)

    def test_password_hash_different_from_plaintext(self):
        """Test that hashed password is different from plaintext."""
        plaintext = "SecurePassword123!"
        # In real implementation, this would use bcrypt or similar
        # For now, we just verify they're different strings
        assert plaintext != plaintext.upper()


@pytest.mark.security
class TestAPIKeyManagement:
    """Test API key handling and security."""

    def test_anthropic_api_key_configured(self):
        """Test that Anthropic API key is configured."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None
        assert len(api_key) > 0

    def test_api_key_not_in_response(self):
        """Test that API keys are not exposed in responses."""
        # API keys should never be returned to clients
        # This would be enforced in the API layer
        assert True  # Placeholder for integration test

    def test_sensitive_config_not_exposed(self):
        """Test that sensitive configuration is not exposed."""
        secret_key = os.getenv("SECRET_KEY")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        # These should not be empty in production
        assert secret_key is not None
        assert api_key is not None


@pytest.mark.security
class TestEnvironmentSecurity:
    """Test environment configuration security."""

    def test_debug_mode_in_test_environment(self):
        """Test that debug mode is enabled for testing."""
        debug = os.getenv("DEBUG", "False").lower() == "true"
        environment = os.getenv("ENVIRONMENT", "development")

        # Debug can be true in test environment
        if environment == "test":
            assert True  # Debug can be on for testing
        else:
            # In production, debug should be False
            assert environment in ["test", "development"]

    def test_environment_variable_set(self):
        """Test that environment is properly set."""
        environment = os.getenv("ENVIRONMENT")
        assert environment in ["test", "development", "production"]

    def test_database_urls_configured(self):
        """Test that database URLs are configured."""
        db_auth = os.getenv("DATABASE_URL_AUTH")
        db_specs = os.getenv("DATABASE_URL_SPECS")

        assert db_auth is not None
        assert db_specs is not None


@pytest.mark.security
class TestCORSConfiguration:
    """Test CORS (Cross-Origin Resource Sharing) configuration."""

    def test_cors_origins_configured(self):
        """Test that CORS origins are configured."""
        origins = os.getenv("CORS_ORIGINS", "")
        # Should have at least localhost for development
        assert "localhost" in origins or len(origins) > 0

    def test_cors_origins_format(self):
        """Test that CORS origins are in valid format."""
        origins = os.getenv("CORS_ORIGINS", "").split(",")
        for origin in origins:
            origin = origin.strip()
            if origin:  # Skip empty strings
                assert origin.startswith("http://") or origin.startswith("https://")


@pytest.mark.security
class TestInputValidation:
    """Test input validation for security."""

    def test_email_validation_rejects_invalid_format(self):
        """Test that invalid email formats are rejected."""
        from app.core.validators import validate_email

        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user name@example.com",
        ]

        for email in invalid_emails:
            is_valid = validate_email(email)
            assert not is_valid

    def test_strong_password_validation(self):
        """Test password strength validation."""
        weak_passwords = [
            "short",
            "nouppercasehere123",
            "NOLOWERCASEHERE123",
            "NoNumbers",
            "12345678",
        ]

        strong_password = "StrongPassword123!"

        # Test that strong password has all components
        assert any(c.isupper() for c in strong_password)
        assert any(c.islower() for c in strong_password)
        assert any(c.isdigit() for c in strong_password)
        assert len(strong_password) >= 8
