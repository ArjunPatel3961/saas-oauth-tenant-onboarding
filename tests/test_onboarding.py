import pytest
from infrai_client import InfraiClient
from oauth_service import OAuthService
from models import SocialLoginInput, NewTenantResult, ExistingTenantResult


class FakeClient:
    """A fake InfraiClient that returns canned responses."""

    def __init__(self):
        self.calls = []

    def post(self, path, json=None):
        self.calls.append(("POST", path, json))
        if path == "/v1/captcha/verify":
            return {"passed": True}
        elif path == "/v1/auth/user/create":
            return {"id": "user_123", "email": json["email"]}
        elif path == "/v1/auth/session/create":
            return {"id": "session_456"}
        raise AssertionError(f"Unexpected post to {path}")

    def get(self, path, params=None):
        raise AssertionError("No get expected")


@pytest.fixture
def service():
    return OAuthService(FakeClient())


def test_new_tenant_created_for_new_domain(service):
    input = SocialLoginInput(
        provider="google",
        provider_user_id="oauth_abc",
        email="new@unknown.com",
        captcha_token="token",
    )
    result = service.login(input)
    assert isinstance(result, NewTenantResult)
    assert result.tenant_id == "tenant_unknown_com"
    assert result.user_id == "user_123"
    assert result.session_id == "session_456"


def test_existing_tenant_reused_for_known_domain(service):
    input = SocialLoginInput(
        provider="github",
        provider_user_id="oauth_def",
        email="alice@example.com",
        captcha_token="token",
    )
    result = service.login(input)
    assert isinstance(result, ExistingTenantResult)
    assert result.tenant_id == "tenant_example"
    assert not result.is_admin


def test_captcha_verify_called_first(service):
    input = SocialLoginInput(
        provider="github",
        provider_user_id="oauth_xyz",
        email="bob@unknown.org",
        captcha_token="captcha123",
    )
    service.login(input)
    assert service.client.calls[0] == ("POST", "/v1/captcha/verify", {
        "token": "captcha123",
        "vendor": "recaptcha",
        "ip": "",
        "action": "social_login",
        "score_threshold": 0.5,
    })
