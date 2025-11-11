"""CLI commands for authentication and account management.

Commands for user login, logout, and API key management.
"""
import click
import json
from pathlib import Path
import os


@click.group(name="auth")
def auth():
    """Manage authentication and API credentials.

    Examples:
        socrates auth login
        socrates auth logout
        socrates auth token --generate
        socrates auth status
    """
    pass


def get_config_dir():
    """Get the Socrates configuration directory."""
    config_dir = Path.home() / ".socrates"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_credentials_file():
    """Get the credentials file path."""
    return get_config_dir() / "credentials.json"


def load_credentials():
    """Load stored credentials."""
    creds_file = get_credentials_file()
    if creds_file.exists():
        with open(creds_file, "r") as f:
            return json.load(f)
    return {}


def save_credentials(credentials):
    """Save credentials to file."""
    creds_file = get_credentials_file()
    # Make file readable only by user
    creds_file.parent.chmod(0o700)

    with open(creds_file, "w") as f:
        json.dump(credentials, f, indent=2)
    creds_file.chmod(0o600)


@auth.command(name="login")
@click.option("--email", prompt="Email", help="Email address")
@click.option("--password", prompt=True, hide_input=True, help="Password")
@click.option("--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000",
              help="API base URL")
def login(email: str, password: str, api_url: str):
    """Authenticate with Socrates2 and save credentials.

    Examples:
        socrates auth login
        socrates auth login --email user@example.com
    """
    click.echo("🔐 Authenticating...")

    try:
        # This would call the actual login API
        # Placeholder token
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        user_id = "user_123"

        # Save credentials
        credentials = {
            "email": email,
            "token": token,
            "user_id": user_id,
            "api_url": api_url
        }
        save_credentials(credentials)

        click.echo(f"✅ Logged in successfully as {click.style(email, fg='green')}")
        click.echo(f"API Key saved to {get_credentials_file()}")

    except Exception as e:
        click.echo(f"❌ Authentication failed: {e}", err=True)
        raise SystemExit(1)


@auth.command(name="logout")
def logout():
    """Remove stored credentials.

    Examples:
        socrates auth logout
    """
    creds_file = get_credentials_file()

    if not creds_file.exists():
        click.echo("Not logged in")
        return

    confirm = click.confirm("Remove stored credentials?")
    if confirm:
        creds_file.unlink()
        click.echo("✅ Logged out successfully")
    else:
        click.echo("Cancelled")


@auth.command(name="token")
@click.option("--generate", is_flag=True, help="Generate a new API token")
@click.option("--show", is_flag=True, help="Show current token")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option("--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000",
              help="API base URL")
def manage_token(generate: bool, show: bool, api_key: str, api_url: str):
    """Manage API tokens.

    Examples:
        socrates auth token --generate
        socrates auth token --show
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    if generate:
        click.echo("🔑 Generating new API token...")

        try:
            # This would call the actual API
            new_token = "sk_live_" + "new_token_here"

            # Update credentials
            creds = load_credentials()
            creds["token"] = new_token
            save_credentials(creds)

            click.echo(f"✅ New API token generated!")
            click.echo(f"Token: {click.style(new_token[:20] + '...', fg='green')}")

        except Exception as e:
            click.echo(f"❌ Error generating token: {e}", err=True)
            raise SystemExit(1)

    elif show:
        creds = load_credentials()
        if not creds:
            click.echo("Not logged in. Run 'socrates auth login' first.", err=True)
            raise SystemExit(1)

        token = creds.get("token", "").replace("Bearer ", "")
        # Show only first and last parts for security
        if len(token) > 40:
            display_token = token[:20] + "..." + token[-10:]
        else:
            display_token = token

        click.echo(f"Current token: {click.style(display_token, fg='green')}")

    else:
        click.echo("Use --generate or --show", err=True)
        raise SystemExit(1)


@auth.command(name="status")
def status():
    """Show authentication status.

    Examples:
        socrates auth status
    """
    creds = load_credentials()

    if not creds:
        click.echo("❌ Not logged in")
        click.echo("Run 'socrates auth login' to authenticate")
        raise SystemExit(1)

    click.echo("✅ Logged in")
    click.echo(f"Email: {click.style(creds.get('email', 'Unknown'), fg='green')}")
    click.echo(f"User ID: {creds.get('user_id', 'Unknown')}")
    click.echo(f"API URL: {creds.get('api_url', 'Unknown')}")

    # Check token validity
    token = creds.get("token", "")
    if token:
        if len(token) > 40:
            click.echo(f"Token: {token[:20]}...{token[-10:]}")
        else:
            click.echo(f"Token: {token}")


@auth.command(name="whoami")
def whoami():
    """Show current user information.

    Examples:
        socrates auth whoami
    """
    creds = load_credentials()

    if not creds:
        click.echo("❌ Not logged in", err=True)
        raise SystemExit(1)

    email = creds.get("email", "Unknown")
    user_id = creds.get("user_id", "Unknown")

    click.echo(f"User: {email}")
    click.echo(f"ID: {user_id}")
