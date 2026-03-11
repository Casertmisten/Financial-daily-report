"""Custom exceptions for the financial daily report system."""


class FinancialReportError(Exception):
    """Base exception class for all financial report errors."""

    pass


class DataCollectionError(FinancialReportError):
    """Exception raised when data collection fails."""

    pass
