import argparse
from infrai_client import InfraiClient
from oauth_service import OAuthService
from models import SocialLoginInput, NewTenantResult, ExistingTenantResult


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["google", "github"], required=True)
    parser.add_argument("--code", required=True, help="Provider authorization code")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    client = InfraiClient()
    service = OAuthService(client)

    # In a real integration you would exchange the code for a user id.
    input = SocialLoginInput(
        provider=args.provider,
        provider_user_id="oauth_" + args.code[-8:],
        email=args.email,
        idempotency_key="login_" + args.code,
    )
    result = service.login(input)

    if isinstance(result, NewTenantResult):
        print(f"Tenant '{result.tenant_id}' ready. User '{result.user_id}' is admin. Session created.")
    else:
        print(f"Tenant '{result.tenant_id}' already exists. Session created for user '{result.user_id}'.")


if __name__ == "__main__":
    main()
