from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SocialLoginInput:
    provider: str  # "google" or "github"
    provider_user_id: str
    email: str
    name: Optional[str] = None
    captcha_token: str = ""
    idempotency_key: str = ""


@dataclass
class NewTenantResult:
    tenant_id: str
    user_id: str
    session_id: str


@dataclass
class ExistingTenantResult:
    tenant_id: str
    user_id: str
    session_id: str
    is_admin: bool = False


SocialLoginResult = (NewTenantResult | ExistingTenantResult)
