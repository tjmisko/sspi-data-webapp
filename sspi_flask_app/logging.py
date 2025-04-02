import logging
from logging.handlers import RotatingFileHandler
import os


def configure_logging(app):
    # Remove any existing handlers attached to the app's logger
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # Set the logging level based on the app's configuration
    log_level = app.config.get('LOG_LEVEL', logging.INFO)
    app.logger.setLevel(log_level)

    # Define a formatter with the desired output format
    formatter = logging.Formatter(
        (
            '[%(asctime)s] %(levelname)s '
            '{%(pathname)s:%(lineno)d:1}: %(message)s'
        )
    )

    # Create a console handler and set its formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)

    # Optionally, set up a file handler if a log directory is specified
    log_dir = app.config.get('LOG_DIR')
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'sspi.world.log'),
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
