"""CLI commands for configuration management.

Commands for managing CLI configuration and settings.
"""

import json
from pathlib import Path

import click


@click.group(name="config")
def config():
    """Manage CLI configuration.

    Examples:
        socrates config set api_url http://api.example.com
        socrates config get api_url
        socrates config list
        socrates config init
    """
    pass


def get_config_file():
    """Get the configuration file path."""
    config_dir = Path.home() / ".socrates"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config():
    """Load configuration."""
    config_file = get_config_file()
    if config_file.exists():
        with open(config_file, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save configuration."""
    config_file = get_config_file()
    config_file.parent.mkdir(exist_ok=True)

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


@config.command(name="init")
@click.option(
    "--api-url", prompt="API URL", default="http://localhost:8000", help="Socrates API URL"
)
@click.option(
    "--editor", prompt="Preferred editor", default="nano", help="Text editor for opening files"
)
def init_config(api_url: str, editor: str):
    """Initialize configuration.

    Examples:
        socrates config init
    """
    click.echo("⚙️  Initializing configuration...")

    config = {"api_url": api_url, "editor": editor, "output_format": "table", "verbose": False}

    save_config(config)
    click.echo("✅ Configuration saved!")
    click.echo(f"Config file: {get_config_file()}")


@config.command(name="set")
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str):
    """Set a configuration value.

    Examples:
        socrates config set api_url http://api.example.com
        socrates config set output_format json
        socrates config set verbose true
    """
    config = load_config()

    # Parse boolean values
    if value.lower() in ("true", "yes", "1"):
        value = True
    elif value.lower() in ("false", "no", "0"):
        value = False

    config[key] = value
    save_config(config)

    click.echo(f"✅ Set {click.style(key, fg='cyan')} = {click.style(str(value), fg='green')}")


@config.command(name="get")
@click.argument("key")
def get_config(key: str):
    """Get a configuration value.

    Examples:
        socrates config get api_url
        socrates config get output_format
    """
    config = load_config()

    if key not in config:
        click.echo(f"❌ Configuration key not found: {key}", err=True)
        raise SystemExit(1)

    value = config[key]
    click.echo(f"{key} = {click.style(str(value), fg='green')}")


@config.command(name="list")
@click.option(
    "--format", type=click.Choice(["table", "json"]), default="table", help="Output format"
)
def list_config(format: str):
    """List all configuration values.

    Examples:
        socrates config list
        socrates config list --format json
    """
    config = load_config()

    if not config:
        click.echo("No configuration found. Run 'socrates config init' first.", err=True)
        raise SystemExit(1)

    if format == "json":
        click.echo(json.dumps(config, indent=2))
    else:
        click.echo("\n" + "=" * 50)
        click.echo("Configuration")
        click.echo("=" * 50)

        for key, value in config.items():
            click.echo(f"{key:<20} {click.style(str(value), fg='green')}")

        click.echo("=" * 50 + "\n")


@config.command(name="reset")
@click.option("--force", is_flag=True, help="Skip confirmation")
def reset_config(force: bool):
    """Reset configuration to defaults.

    Examples:
        socrates config reset
        socrates config reset --force
    """
    if not force:
        confirm = click.confirm("Reset configuration to defaults? This cannot be undone.")
        if not confirm:
            click.echo("Cancelled")
            return

    config = {
        "api_url": "http://localhost:8000",
        "editor": "nano",
        "output_format": "table",
        "verbose": False,
    }

    save_config(config)
    click.echo("✅ Configuration reset to defaults")


@config.command(name="path")
def config_path():
    """Show configuration file path.

    Examples:
        socrates config path
    """
    click.echo(f"Configuration file: {get_config_file()}")
    click.echo(f"Configuration directory: {get_config_file().parent}")


@config.command(name="validate")
def validate_config():
    """Validate configuration.

    Examples:
        socrates config validate
    """
    click.echo("✔️  Validating configuration...")

    config_file = get_config_file()

    if not config_file.exists():
        click.echo("❌ Configuration not found")
        click.echo("Run 'socrates config init' to create configuration")
        raise SystemExit(1)

    try:
        config = load_config()

        # Validate required fields
        required = ["api_url"]
        for field in required:
            if field not in config:
                click.echo(f"❌ Missing required field: {field}", err=True)
                raise SystemExit(1)

        # Validate API URL
        api_url = config.get("api_url")
        if not (api_url.startswith("http://") or api_url.startswith("https://")):
            click.echo(f"❌ Invalid API URL: {api_url}", err=True)
            raise SystemExit(1)

        click.echo("✅ Configuration is valid!")
        click.echo(f"API URL: {click.style(config['api_url'], fg='green')}")

    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON in configuration: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Error validating configuration: {e}", err=True)
        raise SystemExit(1)
