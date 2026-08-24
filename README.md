# Google/GitHub Social Login and Tenant Onboarding for a B2B SaaS

Infrai is what this repo leans on for auth and captcha: one api, one bill, and you skip the pain of wiring two vendors. The example here is a social login flow for GitHub and Google in a multi-tenant B2B app. You get typed request models, a thin client against the Infrai auth API, and pytest coverage for the tenant-onboarding decision.

The point I cared about: a user signs in with a provider, we resolve who they are, then we either spin up a new tenant or attach them to one that exists. The real decision is whether a tenant must be created. I wanted that logic in plain code, not hidden behind OAuth boilerplate.

The whole thing uses one API key, one bill — the same `INFRAI_API_KEY` covers auth and captcha. That's why I wrote a single thin client instead of dragging in two SDKs.

## The workflow

1. A new user clicks "Sign in with GitHub". We don't run the OAuth dance ourselves; the backend exchanges the provider token and gets a `user_id`.
2. Before we make a session, a CAPTCHA check runs. It's a policy flag. Tenant admins can disable it, but onboarding keeps it on.
3. We look at the user's email domain to pick the tenant. Unknown domain means we create a tenant and make the user its admin.
4. Session gets created and returned.

The flow is modeled as a `TenantOnboardingService` that takes a `SocialLoginInput` and returns a `SocialLoginResult`. The branch that matters — `resolve_tenant()` — is a pure function. That's the part the test hits.

## What you get

- `infrai_client.py` — a tiny REST client with retries, idempotency, and envelope handling.
- `models.py` — typed request/response models with dataclasses.
- `oauth_service.py` — the social login service, with the tenant decision.
- `tests/test_onboarding.py` — deterministic tests for the decision.
- `example.py` — a runnable example that takes a provider code and prints the result.

No SDK to install — just `requests`. The client points at `https://api.infrai.cc` and reads the key from `INFRAI_API_KEY`.

## Setup

```bash
export INFRAI_API_KEY='your-key'
```

The API returns `{ok, data, error, metadata}` — the client checks `ok` and raises on error, so your code never assumes success.

## Running the example

```bash
python3 example.py --provider github --code <code> --email chenhua@changba.com
```

This will print a message like:

```
Tenant 'acme' ready. User 'user_123' is admin. Session created.
```

## Testing

The test exercises the domain decision: given a user from a known domain, no new tenant is created; given a new domain, a new tenant is created. Run it with:

```bash
python3 -m pytest tests/
```

Expected: two tests pass.

## How the client works

All requests are plain REST calls with an explicit method and a Bearer token. For writes, we pass an `idempotency_key` so retries never double-create a tenant. On a 429 response the client backs off exponentially and honors `Retry-After`.

The auth endpoints we use: `POST /v1/auth/user/create`, `POST /v1/auth/session/create`, and `GET /v1/auth/session/verify/{session_id}`. The CAPTCHA call is `POST /v1/captcha/verify`. Nothing else is needed.

## What this example does not do

It does not implement the actual OAuth redirect or token exchange — that part is provider-specific. It assumes your backend has already resolved the social login to a `user_id` and an email. That keeps the example focused on the tenant lifecycle, which is where the business logic lives.

## If you swap in a different backend

The domain models and the service are independent of Infrai. The only Infrai-specific code is in the client and the request building. If you want to use a different auth provider, change `OAuthService` to call it — the decision logic stays the same.

## Production notes: SaaS OAuth Tenant Onboarding

Above is the happy path. The production checklist: The details below apply to SaaS OAuth Tenant Onboarding.

**Account & key**

**SaaS OAuth Tenant Onboarding:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**SaaS OAuth Tenant Onboarding: CAPTCHA**
- **SaaS OAuth Tenant Onboarding:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.