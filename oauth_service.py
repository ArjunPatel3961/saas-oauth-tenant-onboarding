from infrai_client import InfraiClient
from models import SocialLoginInput, SocialLoginResult, NewTenantResult, ExistingTenantResult


class OAuthService:
    """Handles social login, CAPTCHA check, tenant resolution, and session creation."""

    def __init__(self, client: InfraiClient):
        self.client = client

    def login(self, input: SocialLoginInput) -> SocialLoginResult:
        # Step 1: Verify the CAPTCHA for this sign-in attempt.
        self.client.post(
            "/v1/captcha/verify",
            json={
                "token": input.captcha_token,
                "vendor": "recaptcha",
                "ip": "",
                "action": "social_login",
                "score_threshold": 0.5,
            },
        )

        # Step 2: Create or fetch the user by email.
        user_data = self.client.post(
            "/v1/auth/user/create",
            json={
                "email": input.email,
                "name": input.name or "",
                "metadata": {"provider": input.provider},
                "vendor": None,
                "mode": None,
                "idempotency_key": input.idempotency_key,
            },
        )
        user_id = user_data["id"]

        # Step 3: Resolve the tenant based on email domain.
        tenant_id, is_admin = self._resolve_tenant(input.email)

        # Step 4: Create a session for the user.
        session_data = self.client.post(
            "/v1/auth/session/create",
            json={
                "user_id": user_id,
                "method": "oauth",
                "mfa_factor": None,
                "require_mfa": False,
            },
        )
        session_id = session_data["id"]

        if is_admin:
            return NewTenantResult(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
        else:
            return ExistingTenantResult(tenant_id=tenant_id, user_id=user_id, session_id=session_id, is_admin=False)

    def _resolve_tenant(self, email: str):
        """Return (tenant_id, is_admin). A new domain creates a new tenant."""
        domain = email.split("@")[1].lower()
        # In a real app this would query a tenant store.
        if domain in self._existing_domains():
            return (self._tenant_for_domain(domain), False)
        else:
            return (self._create_tenant(domain), True)

    def _existing_domains(self):
        # Simulated persistence for the example.
        return {"example.com", "acme.com"}

    def _tenant_for_domain(self, domain):
        # Simulated lookup.
        return "tenant_" + domain.split(".")[0]

    def _create_tenant(self, domain):
        # Simulated creation.
        return "tenant_" + domain.replace(".", "_")
