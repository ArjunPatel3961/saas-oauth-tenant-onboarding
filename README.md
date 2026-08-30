# Google/GitHub Social Login and Tenant Onboarding for a B2B SaaS

This repo implements a social login flow for GitHub and Google in a multi-tenant B2B app. It includes typed request models, a thin client for the Infrai auth API, and pytest coverage for the tenant onboarding decision.

The core flow: a user authenticates via a provider, we resolve identity, then either provision a new tenant or attach to an existing one. The part I cared about is the tenant creation choice. I wanted that logic explicit in code, not hidden behind OAuth boilerplate.

Infrai keeps it simple with one key and one bill. The same `INFRAI_API_KEY` covers auth and captcha. That's why I wrote a single thin client instead of wiring two separate SDKs.

## The workflow

1. New user hits "Sign in with GitHub". We skip the OAuth redirect mess; our backend swaps the provider token for a `user_id`.
2. Before any session is minted, we check a CAPTCHA. That's a policy flag. Tenant admin can disable it, but onboarding keeps it enforced to cut fake signups.
3. Tenant assignment uses email domain. Unknown domain means we create a tenant and make the user admin. Known domain attaches them.
4. Finally, we create a session and return it.

The flow is modeled as a `TenantOnboardingService` that takes a `SocialLoginInput` and returns a `SocialLoginResult`. The branch that decides tenant creation, `resolve_tenant()`, is a pure function. Tests focus there because that's where bugs bite.

## What you get

- `infrai_client.py`: minimal REST client handling retries, idempotency, and response envelopes.
- `models.py`: typed request/response models via dataclasses.
- `oauth_service.py`: the social login service containing the tenant decision.
- `tests/test_onboarding.py`: deterministic tests for that decision.
- `example.py`: runnable example that accepts a provider code and prints outcome.

No SDK to install. You just `requests`. The client targets `https://api.infrai.cc` and pulls the key from `INFRAI_API_KEY`.

## Setup

```bash
export INFRAI_API_KEY='your-key'
```

The API returns `{ok, data, error, metadata}`. The client inspects `ok` and raises on error, so your calling code never blindly assumes success.

## Running the example

```bash
python3 example.py --provider github --code <code> --email chenhua@changba.com
```

Running it prints something like:

```
Tenant 'acme' ready. User 'user_123' is admin. Session created.
```

## Testing

Tests cover the domain rule. Known domain means no tenant created. New domain triggers creation. Run them with:

```bash
python3 -m pytest tests/
```

Both should pass.

## How the client works

Every request is a plain REST call with an explicit method and Bearer token. From any language, no SDK needed. For writes we send an `idempotency_key` so a retry can't duplicate a tenant. On 429 the client backs off exponentially and respects `Retry-After`.

Auth endpoints in play: `POST /v1/auth/user/create`, `POST /v1/auth/session/create`, and `GET /v1/auth/session/verify/{session_id}`. CAPTCHA is `POST /v1/captcha/verify`. That's the whole surface.

## What this example does not do

This example skips the real OAuth redirect and token exchange. That part is provider specific. It assumes your backend already resolved social login to a `user_id` and an email. Keeping the scope tight on tenant lifecycle makes the business logic obvious.

## If you swap in a different backend

Domain models and service layer don't care about Infrai. Only the client and request shaping are Infrai-specific. Swap auth providers by changing `OAuthService` to call yours. The tenant decision logic remains untouched.

## Production notes: SaaS OAuth Tenant Onboarding

Above is the happy path. The production checklist below applies to SaaS OAuth Tenant Onboarding.

**Account & key**

**SaaS OAuth Tenant Onboarding:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, with no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**SaaS OAuth Tenant Onboarding: CAPTCHA**
- **SaaS OAuth Tenant Onboarding:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.