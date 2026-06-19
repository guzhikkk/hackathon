from app.services.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)

class TestPasswords:

    def test_hash_not_plaintext(self):
        hashed = hash_password("password123")
        assert hashed != "password123"
        assert hashed.startswith("$2b$")  

    def test_verify_correct_password(self):
        hashed = hash_password("password123")
        assert verify_password("password123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("password123")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        hash1 = hash_password("password123")
        hash2 = hash_password("password123")
        assert hash1 != hash2
        
        assert verify_password("password123", hash1) is True
        assert verify_password("password123", hash2) is True

class TestJWT:

    def test_create_access_token(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        token = create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_pair(self):
        pair = create_token_pair("user-123")
        assert "access_token" in pair
        assert "refresh_token" in pair
        assert pair["token_type"] == "bearer"

    def test_decode_valid_token(self):
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        assert decode_token("invalid.token.here") is None

    def test_decode_empty_string(self):
        assert decode_token("") is None

    def test_verify_access_token_valid(self):
        token = create_access_token("user-123")
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_verify_access_token_rejects_refresh(self):
        token = create_refresh_token("user-123")
        assert verify_access_token(token) is None

    def test_verify_refresh_token_valid(self):
        token = create_refresh_token("user-123")
        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_verify_refresh_token_rejects_access(self):
        token = create_access_token("user-123")
        assert verify_refresh_token(token) is None

    def test_extra_data_in_access_token(self):
        token = create_access_token("user-123", extra_data={"role": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_different_users_different_tokens(self):
        token1 = create_access_token("user-1")
        token2 = create_access_token("user-2")
        assert token1 != token2
        assert decode_token(token1)["sub"] == "user-1"
        assert decode_token(token2)["sub"] == "user-2"
