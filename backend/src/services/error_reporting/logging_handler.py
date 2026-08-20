import logging
import traceback


class TelegramLoggingHandler(logging.Handler):
    _LEVEL_MAP = {
        logging.DEBUG: "INFO",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def emit(self, record):
        try:
            if record.name.startswith("src.services.error_reporting"):
                return
            source = "BACKEND_CELERY" if record.name.startswith("celery") else "BACKEND"
            from src.services.error_reporting.service import ErrorReportingService
            ErrorReportingService.report_error(
                source=source,
                severity=self._map_level(record.levelno),
                kind="EXCEPTION",
                error_type=record.levelname,
                error_message=self.format(record),
                stack_trace=self._extract_stack(record),
                context={"logger": record.name, "module": record.module},
            )
        except Exception:
            pass

    def _map_level(self, levelno):
        return self._LEVEL_MAP.get(levelno, "ERROR")

    @staticmethod
    def _extract_stack(record):
        if record.exc_info:
            return "".join(traceback.format_exception(*record.exc_info))
        return None
