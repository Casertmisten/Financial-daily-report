"""Base collector class for all data collectors."""

from abc import ABC, abstractmethod
from loguru import logger


class BaseCollector(ABC):
    """Abstract base class for data collectors.

    All collectors should inherit from this class and implement the collect method.
    """

    def __init__(self, name: str):
        """Initialize the collector with a name.

        Args:
            name: The name of the collector for logging purposes.
        """
        self.name = name

    @abstractmethod
    def collect(self):
        """Collect data from the source.

        Returns:
            Collected data, typically as a list of dictionaries.

        Raises:
            DataCollectionError: If data collection fails.
        """
        pass
