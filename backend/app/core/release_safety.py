"""Fail before connecting to a production database with unsafe auth settings."""


def validate_release_settings(settings) -> None:
    if settings.app_env.lower() != "production":
        return
    secret = settings.app_secret
    if len(secret) < 32 or secret.lower().startswith(("replace-", "development-")):
        raise ValueError("Production requires a unique APP_SECRET of at least 32 characters.")
    if settings.app_debug:
        raise ValueError("Production requires APP_DEBUG=false.")
    if not settings.database_enabled:
        raise ValueError("Production requires database persistence.")
