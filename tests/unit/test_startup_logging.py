"""
A log directory the service user cannot write must never stop the app from
booting (v1.4.0 crash-looped on PermissionError creating releases/<ver>/logs).
"""
import logging
import os

import pytest
from flask import Flask

import config
from sspi_flask_app.logging import configure_logging


@pytest.fixture
def clean_root_logger():
    root = logging.getLogger()
    before = list(root.handlers)
    yield root
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            handler.close()


def _app(log_dir):
    app = Flask(__name__)
    app.config["LOG_LEVEL"] = logging.INFO
    app.config["LOG_DIR"] = log_dir
    return app


def test_should_add_file_handler_when_log_dir_is_writable(tmp_path, clean_root_logger):
    before = set(clean_root_logger.handlers)
    configure_logging(_app(str(tmp_path / "logs")))
    added = [h for h in clean_root_logger.handlers if h not in before]
    assert (tmp_path / "logs").is_dir()
    assert sorted(type(h).__name__ for h in added) == ["RotatingFileHandler", "StreamHandler"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write anywhere")
def test_should_fall_back_to_console_when_log_dir_cannot_be_created(tmp_path, clean_root_logger):
    locked = tmp_path / "release"
    locked.mkdir()
    locked.chmod(0o555)
    before = set(clean_root_logger.handlers)
    try:
        configure_logging(_app(str(locked / "logs")))
    finally:
        locked.chmod(0o755)
    added = [h for h in clean_root_logger.handlers if h not in before]
    assert not (locked / "logs").exists()
    assert [type(h).__name__ for h in added] == ["StreamHandler"]


def test_should_use_shared_logs_when_release_links_shared_dir(tmp_path, monkeypatch):
    (tmp_path / ".shared" / "logs").mkdir(parents=True)
    monkeypatch.setattr(config, "basedir", str(tmp_path))
    monkeypatch.delenv("SSPI_LOG_DIR", raising=False)
    assert config._production_log_dir() == str(tmp_path / ".shared" / "logs")


def test_should_use_logs_beside_code_when_no_shared_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "basedir", str(tmp_path))
    monkeypatch.delenv("SSPI_LOG_DIR", raising=False)
    assert config._production_log_dir() == str(tmp_path / "logs")


def test_should_prefer_env_override_when_sspi_log_dir_is_set(tmp_path, monkeypatch):
    (tmp_path / ".shared" / "logs").mkdir(parents=True)
    monkeypatch.setattr(config, "basedir", str(tmp_path))
    monkeypatch.setenv("SSPI_LOG_DIR", "/var/log/sspi")
    assert config._production_log_dir() == "/var/log/sspi"
