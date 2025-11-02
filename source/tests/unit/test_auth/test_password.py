import pytest

from source.auth.password import hash_password, verify_password


class TestPasswordHash:
    """Тесты для хеширования паролей"""

    def test_hash_password_generates_different_hashes(self):
        """Каждый вызов хеша создает уникальный хеш (из-за соли)"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0

    def test_hash_password_creates_valid_bcrypt_hash(self):
        """Генерируется валидный bcrypt хеш"""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_password_correct_password(self):
        """Верификация корректного пароля"""
        password = "CorrectPass123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Верификация неверного пароля"""
        password = "CorrectPass123!"
        wrong_password = "WrongPass123!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_empty_string(self):
        """Верификация пустого пароля"""
        password = ""
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        assert result is True  # Пустая строка тоже валидный пароль
        
        wrong = verify_password("not_empty", hashed)
        assert wrong is False

    def test_verify_password_with_special_characters(self):
        """Верификация пароля со специальными символами"""
        password = "P@ssw0rd! #$%^&*()+=[]{}|;:,.<>?"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("P@ssw0rd!", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Верификация чувствительна к регистру"""
        password = "CaseSensitive123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password(password.lower(), hashed) is False
        assert verify_password(password.upper(), hashed) is False

    def test_verify_password_unicode_characters(self):
        """Верификация с юникод символами"""
        password = "Пароль中文日本語🎉"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("Пароль", hashed) is False

