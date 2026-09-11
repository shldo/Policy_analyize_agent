from types import SimpleNamespace

import pytest

from app.core.release_safety import validate_release_settings


@pytest.mark.parametrize(
    "changes",
    [
        {"app_secret": "development-only-change-me"},
        {"app_secret": "replace-with-a-long-random-secret"},
        {"app_debug": True},
        {"database_enabled": False},
    ],
)
def test_rejects_unsafe_production(changes):
    values = dict(app_env="production", app_secret="a" * 40, app_debug=False, database_enabled=True)
    values.update(changes)
    with pytest.raises(ValueError):
        validate_release_settings(SimpleNamespace(**values))


def test_development_unchanged():
    validate_release_settings(SimpleNamespace(app_env="development"))


def test_safe_production():
    validate_release_settings(
        SimpleNamespace(
            app_env="production", app_secret="a" * 40, app_debug=False, database_enabled=True
        )
    )


def test_production_registration_closed(monkeypatch):
    import asyncio

    from fastapi import HTTPException

    from app.modules.auth import router
    from app.modules.auth.schemas import AuthRequest

    monkeypatch.setattr(
        router,
        "get_settings",
        lambda: SimpleNamespace(app_env="production", registration_enabled=None),
    )
    with pytest.raises(HTTPException) as error:
        asyncio.run(router.register(AuthRequest(username="someone", password="password")))
    assert error.value.status_code == 403
