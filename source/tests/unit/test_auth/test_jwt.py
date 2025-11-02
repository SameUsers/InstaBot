import pytest
import jwt
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from source.auth.jwt import TokenService, token_service
from source.conf import settings
from source.core.exceptions import TokenServiceError, InvalidTokenVersionError
from source.core.constants import AccessTokenRows, RefreshTokenRows


class TestTokenGeneration:
    """Тесты для генерации токенов"""

    def test_generate_access_token(self):
        """Генерация access token"""
        user_id = uuid4()
        email = "test@example.com"
        username = "testuser"
        permissions = "user"
        
        token = TokenService._generate_access_token(
            user_id, email, username, permissions
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        decoded = jwt.decode(
            token, 
            settings.access_token_secret, 
            algorithms=[settings.code_algorithm]
        )
        
        assert decoded[AccessTokenRows.sub] == str(user_id)
        assert decoded[AccessTokenRows.sub_email] == email
        assert decoded[AccessTokenRows.username] == username
        assert decoded[AccessTokenRows.permissions] == permissions
        assert decoded.get(AccessTokenRows.exp) is not None

    def test_generate_refresh_token(self):
        """Генерация refresh token"""
        user_id = uuid4()
        token_version = 1
        
        token = TokenService._generate_refresh_token(user_id, token_version)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        decoded = jwt.decode(
            token,
            settings.refresh_token_secret,
            algorithms=[settings.code_algorithm]
        )
        
        assert decoded[RefreshTokenRows.sub] == str(user_id)
        assert decoded[RefreshTokenRows.token_version] == token_version
        assert decoded.get(RefreshTokenRows.exp) is not None

    def test_access_token_expiration(self):
        """Access token содержит корректное время истечения"""
        user_id = uuid4()
        token = TokenService._generate_access_token(
            user_id, "test@example.com", "user", "user"
        )
        
        decoded = jwt.decode(
            token,
            settings.access_token_secret,
            algorithms=[settings.code_algorithm]
        )
        
        exp_timestamp = decoded[AccessTokenRows.exp]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        expected_exp = now + timedelta(minutes=settings.access_token_exp)
        
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60  # Разница не более минуты

    def test_refresh_token_expiration(self):
        """Refresh token содержит корректное время истечения"""
        user_id = uuid4()
        token = TokenService._generate_refresh_token(user_id, 1)
        
        decoded = jwt.decode(
            token,
            settings.refresh_token_secret,
            algorithms=[settings.code_algorithm]
        )
        
        exp_timestamp = decoded[RefreshTokenRows.exp]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        expected_exp = now + timedelta(days=settings.refresh_token_exp)
        
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 86400  # Разница не более суток


class TestTokenDecoding:
    """Тесты для декодирования токенов"""

    def test_decode_valid_refresh_token(self):
        """Декодирование валидного refresh token"""
        user_id = uuid4()
        token_version = 5
        token = TokenService._generate_refresh_token(user_id, token_version)
        
        payload = TokenService._decode_refresh_token(token)
        
        assert payload[RefreshTokenRows.sub] == str(user_id)
        assert payload[RefreshTokenRows.token_version] == token_version

    def test_decode_expired_refresh_token(self):
        """Декодирование истекшего refresh token"""
        user_id = uuid4()
        expired_token = jwt.encode(
            {
                RefreshTokenRows.sub: str(user_id),
                RefreshTokenRows.token_version: 1,
                RefreshTokenRows.exp: int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
            },
            settings.refresh_token_secret,
            algorithm=settings.code_algorithm
        )
        
        with pytest.raises(TokenServiceError) as exc_info:
            TokenService._decode_refresh_token(expired_token)
        
        assert "Refresh token expired" in str(exc_info.value)

    def test_decode_invalid_token_format(self):
        """Декодирование невалидного формата токена"""
        invalid_token = "not.a.valid.token"
        
        with pytest.raises(TokenServiceError) as exc_info:
            TokenService._decode_refresh_token(invalid_token)
        
        assert "Invalid refresh token" in str(exc_info.value)

    def test_decode_token_wrong_secret(self):
        """Декодирование токена с неверным секретом"""
        user_id = uuid4()
        token = TokenService._generate_refresh_token(user_id, 1)
        
        # JWT.decode с неправильным секретом должен выбросить InvalidSignatureError
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                token,
                "wrong_secret",
                algorithms=[settings.code_algorithm]
            )


class TestExtractTokenData:
    """Тесты для извлечения данных из токена"""

    def test_extract_valid_token_data(self):
        """Извлечение валидных данных из токена"""
        user_id = uuid4()
        token_version = 3
        
        payload = {
            RefreshTokenRows.sub: str(user_id),
            RefreshTokenRows.token_version: token_version
        }
        
        extracted_user_id, extracted_version = TokenService._extract_token_data(payload)
        
        assert extracted_user_id == str(user_id)
        assert extracted_version == token_version

    def test_extract_missing_user_id(self):
        """Извлечение данных с отсутствующим user_id"""
        payload = {
            RefreshTokenRows.token_version: 1
        }
        
        with pytest.raises(TokenServiceError) as exc_info:
            TokenService._extract_token_data(payload)
        
        assert "Payload missing fields" in str(exc_info.value)

    def test_extract_missing_token_version(self):
        """Извлечение данных с отсутствующим token_version"""
        payload = {
            RefreshTokenRows.sub: str(uuid4())
        }
        
        with pytest.raises(TokenServiceError) as exc_info:
            TokenService._extract_token_data(payload)
        
        assert "Payload missing fields" in str(exc_info.value)

    def test_extract_empty_payload(self):
        """Извлечение данных из пустого payload"""
        payload = {}
        
        with pytest.raises(TokenServiceError) as exc_info:
            TokenService._extract_token_data(payload)
        
        assert "Payload missing fields" in str(exc_info.value)


class TestValidateTokenVersion:
    """Тесты для валидации версии токена"""

    def test_validate_matching_token_version(self):
        """Валидация совпадающих версий токена"""
        TokenService._validate_token_version(1, 1)
        TokenService._validate_token_version(5, 5)
        TokenService._validate_token_version(0, 0)

    def test_validate_mismatched_token_version(self):
        """Валидация несовпадающих версий токена"""
        with pytest.raises(InvalidTokenVersionError) as exc_info:
            TokenService._validate_token_version(1, 2)
        
        assert "Refresh token is expired or invalid" in str(exc_info.value)


class TestRegisterTokens:
    """Тесты для регистрации токенов"""

    @pytest.mark.asyncio
    async def test_register_tokens_returns_both_tokens(self):
        """Регистрация возвращает оба токена"""
        user_id = uuid4()
        email = "test@example.com"
        username = "testuser"
        permissions = "admin"
        token_version = 0
        
        result = await TokenService.register_tokens(
            email=email,
            username=username,
            user_id=user_id,
            permissions=permissions,
            refresh_token_version=token_version
        )
        
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert len(result.access_token) > 0
        assert len(result.refresh_token) > 0
        
        # Проверяем, что токены декодируются
        access_decoded = jwt.decode(
            result.access_token,
            settings.access_token_secret,
            algorithms=[settings.code_algorithm]
        )
        assert access_decoded[AccessTokenRows.sub_email] == email
        
        refresh_decoded = jwt.decode(
            result.refresh_token,
            settings.refresh_token_secret,
            algorithms=[settings.code_algorithm]
        )
        assert refresh_decoded[RefreshTokenRows.token_version] == token_version

