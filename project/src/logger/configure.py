import logging

from ..settings.settings import LoggerSettings


def configure_logger():
    logger_settings = LoggerSettings()

    logging.basicConfig(
        level=logger_settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
