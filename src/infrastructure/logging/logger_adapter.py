import sys

from loguru import logger as loguru_logger
from result import Err, Ok, Result

from src.config import settings
from src.core.ports.logger_interface import LoggerInterface


class LoggerAdapter(LoggerInterface):
    def __init__(self):
        self._configure_logger()

    def _configure_logger(self) -> None:
        loguru_logger.remove()
        loguru_logger.add(
            sys.stderr,
            format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level,
        )

    def log(self, message: str, log_level: str) -> Result[bool, str]:
        try:
            log_method = getattr(loguru_logger, log_level.lower())
            log_method(message)
            return Ok(True)
        except AttributeError:
            return Err(f"Invalid log level: {log_level}")
        except (IOError, OSError) as error:
            return Err(f"Failed to log message: {str(error)}")

    def debug(self, message: str) -> Result[bool, str]:
        return self.log(message, "DEBUG")

    def info(self, message: str) -> Result[bool, str]:
        return self.log(message, "INFO")

    def warning(self, message: str) -> Result[bool, str]:
        return self.log(message, "WARNING")

    def error(self, message: str) -> Result[bool, str]:
        return self.log(message, "ERROR")
