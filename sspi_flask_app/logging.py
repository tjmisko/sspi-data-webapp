import logging
from logging.handlers import RotatingFileHandler
import os


def configure_logging(app):
    log_level = app.config.get('LOG_LEVEL', logging.DEBUG)
    formatter = logging.Formatter(
        '%(levelname)s %(pathname)s:%(lineno)d:\n\t%(message)s\t[%(asctime)s]'
    )

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Set up file handler if specified
    log_dir = app.config.get('LOG_DIR')
    handlers = [console_handler]
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'sspi.world.log'),
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)

    # Set root logger config
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)

    # Optional: silence noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
