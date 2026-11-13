import threading
import time
from collections import deque
from collections.abc import Callable
from typing import TypeVar

from adobe.pdfservices.operation.auth.service_principal_credentials import (
    ServicePrincipalCredentials,
)
from adobe.pdfservices.operation.exception.exceptions import (
    SdkException,
    ServiceApiException,
    ServiceUsageException,
)
from adobe.pdfservices.operation.pdf_services import PDFServices
from sqlalchemy.orm import Session

from api.core import usage
from api.core.config import Settings
from api.core.errors import AppError

Result = TypeVar("Result")
MAX_ATTEMPTS = 4
WINDOW_SECONDS = 60.0


class AdobeClient:
    """The single path to Adobe: one call at a time, rate limited, retried and counted."""

    def __init__(
        self,
        settings: Settings,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        services: PDFServices | None = None,
    ):
        self._settings = settings
        self._clock = clock
        self._sleep = sleep
        self._services = services
        self._lock = threading.Lock()
        self._recent: deque[float] = deque()

    def run(
        self,
        session: Session,
        operation: usage.Operation,
        cost: int,
        job: Callable[[PDFServices], Result],
    ) -> Result:
        with self._lock:
            usage.ensure_budget(session, self._settings, cost, operation)
            result = self._with_retries(job)
            usage.record(session, cost)
            return result

    def _with_retries(self, job: Callable[[PDFServices], Result]) -> Result:
        services = self._connect()
        for attempt in range(MAX_ATTEMPTS):
            self._wait_for_slot()
            try:
                return job(services)
            except (ServiceApiException, ServiceUsageException) as exc:
                if exc.status_code == 429 and attempt < MAX_ATTEMPTS - 1:
                    self._sleep(2 ** (attempt + 1))
                    continue
                if isinstance(exc, ServiceUsageException):
                    raise AppError(429, "Adobe says the account's quota is used up.") from exc
                raise AppError(502, "Adobe PDF Services could not process this file.") from exc
            except SdkException as exc:
                raise AppError(502, "Could not reach Adobe PDF Services.") from exc
        raise AppError(503, "Adobe PDF Services is busy. Try again in a minute.")

    def _wait_for_slot(self) -> None:
        now = self._clock()
        while self._recent and now - self._recent[0] >= WINDOW_SECONDS:
            self._recent.popleft()
        if len(self._recent) >= self._settings.jobs_per_minute:
            self._sleep(WINDOW_SECONDS - (now - self._recent[0]))
            self._recent.popleft()
        self._recent.append(self._clock())

    def _connect(self) -> PDFServices:
        if self._services is None:
            if not (self._settings.adobe_client_id and self._settings.adobe_client_secret):
                raise AppError(503, "Adobe credentials are not configured on the server.")
            credentials = ServicePrincipalCredentials(
                client_id=self._settings.adobe_client_id,
                client_secret=self._settings.adobe_client_secret,
            )
            self._services = PDFServices(credentials=credentials)
        return self._services
