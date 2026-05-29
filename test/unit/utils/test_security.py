from app.utils.security import hash_password, verify_password


def test_hash_and_verify_password_roundtrip():
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert verify_password("secret", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("secret")
    assert verify_password("wrong", hashed) is False


def test_verify_password_handles_invalid_hash():
    assert verify_password("secret", "not-a-valid-hash") is False

