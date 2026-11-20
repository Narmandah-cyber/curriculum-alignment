"""Alembic migration загвартай нийцэж буйг шалгана."""
from alembic import command
from alembic.config import Config


def test_upgrade_head(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    from app.core.config import get_settings
    get_settings.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    get_settings.cache_clear()
