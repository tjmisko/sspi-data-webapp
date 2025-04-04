import logging
from logging.handlers import RotatingFileHandler
import os


def configure_logging(app):
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    log_level = app.config.get('LOG_LEVEL', logging.DEBUG)
    app.logger.setLevel(log_level)
    formatter = logging.Formatter(
        '%(levelname)s %(pathname)s:%(lineno)d:\n\t%(message)s\t[%(asctime)s]'
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logging.basicConfig(level=log_level, handlers=[console_handler])
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
        logging.getLogger().addHandler(file_handler)
