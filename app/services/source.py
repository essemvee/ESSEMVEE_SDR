from abc import ABC, abstractmethod

from app.models.discovery import DiscoveryResult
from app.models.signal import Signal


class DiscoverySource(ABC):

    @abstractmethod
    def discover(
        self,
        query: str,
    ) -> DiscoveryResult:
        pass


class SignalSource(ABC):

    @abstractmethod
    def collect(
        self,
        company_name: str,
        website: str | None = None,
    ) -> list[Signal]:
        pass