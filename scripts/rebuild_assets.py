#!/usr/bin/env python
"""Rebuild static assets (CSS/JS bundles) without starting the server."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_assets import Environment
from sspi_flask_app.assets import compile_static_assets


def rebuild_assets():
    """Create a minimal Flask app context and rebuild all static assets."""
    app = Flask(
        __name__,
        static_folder=str(project_root / "sspi_flask_app" / "static"),
        template_folder=str(project_root / "sspi_flask_app" / "templates"),
    )

    # Register the client blueprint to set up static paths
    from sspi_flask_app.client.routes import client_bp
    app.register_blueprint(client_bp)

    assets = Environment(app)
    assets.auto_build = True
    assets.debug = False  # Ensure minification happens

    with app.app_context():
        compile_static_assets(assets)

    print("Asset rebuild complete.")


if __name__ == "__main__":
    rebuild_assets()
