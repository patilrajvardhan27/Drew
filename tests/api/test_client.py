import pytest
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException
from sqlalchemy.orm import Session

from api.adobe.client import AdobeClient
from api.adobe.extract import extract_cost
from api.adobe.html_to_pdf import html_to_pdf_cost
from api.core.db import get_engine, init_db
from api.core.errors import AppError
from api.core.usage import used_this_month


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def session(settings):
    init_db()
    with Session(get_engine()) as db:
        yield db


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def adobe_client(settings, clock):
    return AdobeClient(settings, clock=clock, sleep=clock.sleep, services=object())


def rate_limited():
    return ServiceApiException("slow down", "req-1", status_code=429)


def test_costs_follow_adobe_pricing():
    assert [extract_cost(p) for p in (1, 5, 6, 8, 50)] == [1, 1, 2, 2, 10]
    assert [html_to_pdf_cost(p) for p in (1, 50, 51)] == [1, 1, 2]


def test_retries_429_with_backoff_then_counts(adobe_client, session, clock):
    attempts = iter([rate_limited(), rate_limited(), "ok"])

    def job(_):
        outcome = next(attempts)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    assert adobe_client.run(session, "extract", 2, job) == "ok"
    assert clock.sleeps == [2, 4]
    assert used_this_month(session) == 2


def test_gives_up_after_repeated_429(adobe_client, session):
    def job(_):
        raise rate_limited()

    with pytest.raises(AppError) as error:
        adobe_client.run(session, "extract", 1, job)
    assert error.value.status == 502
    assert used_this_month(session) == 0


def test_extract_stops_at_the_cap_but_export_still_runs(adobe_client, session):
    adobe_client.run(session, "extract", 450, lambda _: None)

    with pytest.raises(AppError) as error:
        adobe_client.run(session, "extract", 1, lambda _: None)
    assert error.value.status == 429
    assert adobe_client.run(session, "export", 1, lambda _: "pdf") == "pdf"


def test_waits_when_the_minute_is_full(adobe_client, session, settings, clock):
    for _ in range(settings.jobs_per_minute + 1):
        adobe_client.run(session, "export", 0, lambda _: None)

    assert clock.sleeps == [60.0]


def test_missing_credentials(settings, session):
    with pytest.raises(AppError) as error:
        AdobeClient(settings).run(session, "extract", 1, lambda _: None)
    assert error.value.status == 503
