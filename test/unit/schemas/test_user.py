import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserOut
from test.factories import make_user


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", username="user", password="secret", full_name="Name")


def test_user_out_from_model():
    user = make_user()
    result = UserOut.model_validate(user)
    assert result.id == user.id
    assert result.email == user.email

