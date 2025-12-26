from abc import ABC, abstractmethod

from result import Result


class LoggerInterface(ABC):
    @abstractmethod
    def log(self, message: str, log_level: str) -> Result[bool, str]:
        pass

    @abstractmethod
    def debug(self, message: str) -> Result[bool, str]:
        pass

    @abstractmethod
    def info(self, message: str) -> Result[bool, str]:
        pass

    @abstractmethod
    def warning(self, message: str) -> Result[bool, str]:
        pass

    @abstractmethod
    def error(self, message: str) -> Result[bool, str]:
        pass
