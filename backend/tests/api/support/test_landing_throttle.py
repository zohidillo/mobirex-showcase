import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse


pytestmark = pytest.mark.django_db

SUPPORT_X_KEY = "test-landing-key"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def _url():
    return reverse("api_support_request_list_create")


def _post(api_client, *, x_key=None, ip="127.0.0.1", data=None):
    kwargs = {"format": "json", "REMOTE_ADDR": ip}
    if x_key is not None:
        kwargs["HTTP_X_KEY"] = x_key
    return api_client.post(_url(), data or {"request_type": "CONTACT"}, **kwargs)


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_landing_form_throttle_with_x_key_anonymous(api_client):
    """Anonymous + X-Key: 5 requests pass, 6th is throttled."""
    for i in range(5):
        resp = _post(api_client, x_key=SUPPORT_X_KEY)
        assert resp.status_code != 429, f"Request {i + 1} unexpectedly throttled"
    resp = _post(api_client, x_key=SUPPORT_X_KEY)
    assert resp.status_code == 429


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_landing_form_throttle_not_applied_for_authenticated_user(api_client, users):
    """Authenticated users bypass LandingFormThrottle entirely."""
    api_client.force_authenticate(user=users["owner"])
    for i in range(8):
        resp = _post(api_client, x_key=SUPPORT_X_KEY)
        assert resp.status_code != 429, f"Authenticated request {i + 1} was throttled"


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_landing_form_throttle_not_applied_without_x_key(api_client):
    """Anonymous caller without X-Key: permission denies (403/401), not throttle (429)."""
    for _ in range(7):
        resp = _post(api_client)
        assert resp.status_code in (401, 403)
        assert resp.status_code != 429


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_landing_form_throttle_per_ip(api_client):
    """Each IP has an independent throttle counter."""
    for _ in range(5):
        resp = _post(api_client, x_key=SUPPORT_X_KEY, ip="10.0.0.1")
        assert resp.status_code != 429

    # IP 10.0.0.1 exhausted — 6th from same IP is throttled
    resp = _post(api_client, x_key=SUPPORT_X_KEY, ip="10.0.0.1")
    assert resp.status_code == 429

    # Different IP — fresh counter, not throttled
    resp = _post(api_client, x_key=SUPPORT_X_KEY, ip="10.0.0.2")
    assert resp.status_code != 429


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["https://mobirex.uz", "https://www.mobirex.uz"],
    CORS_ALLOW_METHODS=["GET", "POST", "OPTIONS"],
    CORS_ALLOW_HEADERS=["content-type", "x-key", "authorization"],
)
def test_cors_preflight_allows_mobirex_uz(api_client):
    """OPTIONS preflight from mobirex.uz receives CORS allow headers."""
    resp = api_client.options(
        _url(),
        HTTP_ORIGIN="https://mobirex.uz",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-key",
    )
    assert resp.status_code == 200
    assert resp.get("Access-Control-Allow-Origin") == "https://mobirex.uz"
