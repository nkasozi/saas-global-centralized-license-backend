from abc import ABC, abstractmethod


class LoggerInterface(ABC):
    @abstractmethod
    def log(self, info: str, log_level: str) -> None:
        pass
