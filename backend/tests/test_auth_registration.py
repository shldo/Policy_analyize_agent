from datetime import datetime
from types import SimpleNamespace

import pytest

from app.modules.auth import service


def _settings(secret: str | None) -> SimpleNamespace:
    return SimpleNamespace(admin_register_secret=secret, app_secret="test-app-secret")


def test_admin_registration_requires_configured_secret(monkeypatch) -> None:
    monkeypatch.setattr(service, "get_settings", lambda: _settings(None))

    with pytest.raises(ValueError, match="Invalid admin registration secret"):
        service.create_user("admin-user", "password", "admin", "anything")


@pytest.mark.parametrize("provided", [None, "", "wrong"])
def test_admin_registration_rejects_missing_or_wrong_secret(monkeypatch, provided) -> None:
    monkeypatch.setattr(service, "get_settings", lambda: _settings("expected-secret"))
    called = False

    def fail_create(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("repository must not be called")

    monkeypatch.setattr(service.user_repository, "create", fail_create)
    with pytest.raises(ValueError, match="Invalid admin registration secret"):
        service.create_user("admin-user", "password", "admin", provided)
    assert not called


def test_admin_registration_accepts_correct_secret(monkeypatch) -> None:
    monkeypatch.setattr(service, "get_settings", lambda: _settings("expected-secret"))
    monkeypatch.setattr(
        service.user_repository,
        "create",
        lambda username, password_hash, role: {
            "id": "id-1",
            "uid": "00001",
            "username": username,
            "role": role,
            "created_at": datetime.now(),
        },
    )

    user = service.create_user("admin-user", "password", "admin", "expected-secret")

    assert user["role"] == "admin"


def test_ordinary_registration_defaults_to_user_without_admin_secret(monkeypatch) -> None:
    monkeypatch.setattr(service, "get_settings", lambda: _settings(None))
    monkeypatch.setattr(
        service.user_repository,
        "create",
        lambda username, password_hash, role: {
            "id": "id-1",
            "uid": "00001",
            "username": username,
            "role": role,
            "created_at": datetime.now(),
        },
    )

    user = service.create_user("regular-user", "password")

    assert user["role"] == "user"
