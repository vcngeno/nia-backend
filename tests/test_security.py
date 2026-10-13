import pytest
from pydantic import ValidationError

from auth import hash_password, verify_password
from routers.children import ChildCreate, ChildPINLogin
from routers.conversation import ChatMessage
from models import GradeLevel
from rate_limit import InMemoryRateLimiter


def test_child_pin_is_hashed_and_verifiable():
    pin = "1234"
    pin_hash = hash_password(pin)

    assert pin_hash != pin
    assert verify_password(pin, pin_hash)
    assert not verify_password("0000", pin_hash)


@pytest.mark.parametrize("pin", ["123", "12345", "12ab", "１２３４", ""])
def test_child_pin_must_be_four_ascii_digits(pin):
    with pytest.raises(ValidationError):
        ChildPINLogin(child_id=1, pin=pin)


def test_child_creation_validates_pin_and_age():
    child = ChildCreate(
        name="Alex",
        age=10,
        grade_level=GradeLevel.GRADE_5,
        pin="1234",
    )

    assert child.pin == "1234"

    with pytest.raises(ValidationError):
        ChildCreate(
            name="Alex",
            age=10,
            grade_level=GradeLevel.GRADE_5,
            pin="123",
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"child_id": 1, "message": "   "},
        {"child_id": 1, "message": "x" * 4001},
        {"child_id": 0, "message": "hello"},
        {"child_id": 1, "message": "hello", "conversation_id": 0},
        {"child_id": 1, "message": "hello", "depth_level": 6},
    ],
)
def test_chat_input_is_bounded(payload):
    with pytest.raises(ValidationError):
        ChatMessage(**payload)


def test_chat_input_is_trimmed():
    chat = ChatMessage(child_id=1, message="  hello  ")

    assert chat.message == "hello"


def test_rate_limiter_rejects_requests_after_limit():
    limiter = InMemoryRateLimiter()
    for _ in range(2):
        limiter.check("test", limit=2, window_seconds=60)

    with pytest.raises(Exception) as error:
        limiter.check("test", limit=2, window_seconds=60)

    assert error.value.status_code == 429
