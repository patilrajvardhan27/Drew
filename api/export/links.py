"""Short-lived signed links that let the Adobe Express add-on fetch one export without a login cookie.

Add-ons run in a third-party iframe where Redraft's session cookie is not sent, so access is carried
by an HMAC over the document id and an expiry time instead.
"""

import hashlib
import hmac
import time

from api.core.config import Settings
from api.core.errors import AppError

LIFETIME_SECONDS = 15 * 60


def _signature(settings: Settings, document_id: str, expires: int) -> str:
    message = f"{document_id}:{expires}".encode()
    return hmac.new(settings.signing_key(), message, hashlib.sha256).hexdigest()


def sign(settings: Settings, document_id: str, now: float | None = None) -> tuple[int, str]:
    expires = int((now or time.time()) + LIFETIME_SECONDS)
    return expires, _signature(settings, document_id, expires)


def verify(
    settings: Settings, document_id: str, expires: int, signature: str, now: float | None = None
) -> None:
    expected = _signature(settings, document_id, expires)
    if not hmac.compare_digest(expected, signature):
        raise AppError(403, "This Express link is not valid.")
    if (now or time.time()) > expires:
        raise AppError(410, "This Express link has expired. Create a new one in Redraft.")
