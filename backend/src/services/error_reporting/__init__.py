__all__ = ["ErrorReportingService"]


def __getattr__(name):
    if name == "ErrorReportingService":
        from src.services.error_reporting.service import ErrorReportingService
        return ErrorReportingService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
