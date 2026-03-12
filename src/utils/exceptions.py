"""Custom exceptions for the financial daily report system."""


class FinancialReportError(Exception):
    """Base exception class for all financial report errors."""

    pass


class DataCollectionError(FinancialReportError):
    """Exception raised when data collection fails."""

    pass


class DataCleaningError(FinancialReportError):
    """Exception raised when data cleaning fails."""

    pass


class LLMError(FinancialReportError):
    """Exception raised when LLM call fails."""

    pass


class EmbeddingError(FinancialReportError):
    """Exception raised when embedding generation fails."""

    pass


class StorageError(FinancialReportError):
    """Exception raised when storage operation fails."""

    pass


class ReportGenerationError(FinancialReportError):
    """Exception raised when report generation fails."""

    pass
