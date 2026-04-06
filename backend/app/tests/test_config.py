from app.core.config import Settings


def test_settings_parse_single_cors_origin_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("CORS_ORIGINS=http://localhost:5173\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.cors_origins == ["http://localhost:5173"]


def test_settings_parse_multiple_cors_origins_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "CORS_ORIGINS=http://localhost:5173,http://localhost:3000\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:3000"]
