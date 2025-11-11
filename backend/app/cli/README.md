# Socrates CLI - Command Line Interface

The Socrates CLI provides a command-line interface for managing projects, specifications, and configurations without using the web interface.

## Installation

### From Source
```bash
cd backend
pip install -e .
```

This installs the `socrates` command globally on your system.

### Direct Usage
```bash
cd backend
python -m app.cli [command]
# or
python socrates [command]
```

## Quick Start

### 1. Authentication
```bash
# Login to Socrates
socrates auth login

# Check login status
socrates auth status

# Show current user
socrates auth whoami
```

### 2. Project Management
```bash
# Create a new project
socrates project create --name "My Project" --description "API specification"

# List all projects
socrates project list

# Get project details
socrates project get proj_123

# Update a project
socrates project update proj_123 --name "Updated Name"

# Export project
socrates project export proj_123 --format csv --output specs.csv

# Delete a project
socrates project delete proj_123
```

### 3. Specification Management
```bash
# Create a specification
socrates spec create \
  --project proj_123 \
  --category goals \
  --key objective1 \
  --value "Build scalable API"

# List specifications
socrates spec list --project proj_123

# Filter by category
socrates spec list --project proj_123 --category goals

# Import specifications from file
socrates spec import --project proj_123 --file specs.json

# Export specifications
socrates spec export --project proj_123 --format csv --output specs.csv

# Validate specifications
socrates spec validate --project proj_123
```

### 4. Configuration
```bash
# Initialize configuration
socrates config init

# Set a configuration value
socrates config set api_url http://api.example.com

# Get a configuration value
socrates config get api_url

# List all configuration
socrates config list

# Validate configuration
socrates config validate

# Reset to defaults
socrates config reset
```

## Command Structure

```
socrates [GROUP] [COMMAND] [OPTIONS]

Groups:
  project      - Manage projects
  spec         - Manage specifications
  auth         - Authentication and credentials
  config       - Configuration management
```

## Authentication

### Environment Variables
Set these to authenticate without logging in each time:

```bash
export SOCRATES_API_KEY="sk_live_..."
export SOCRATES_API_URL="http://localhost:8000"
```

### Login Methods
1. **Interactive Login**
   ```bash
   socrates auth login
   ```

2. **Environment Variable**
   ```bash
   export SOCRATES_API_KEY="your_token"
   ```

3. **Command Flag**
   ```bash
   socrates project list --api-key "your_token"
   ```

## Detailed Commands

### Project Commands

#### Create Project
```bash
socrates project create \
  --name "My Project" \
  --description "Project description"
```

**Options:**
- `--name` - Project name (required)
- `--description` - Project description (optional)
- `--api-key` - API key (or set SOCRATES_API_KEY)
- `--api-url` - API URL (default: http://localhost:8000)

#### List Projects
```bash
socrates project list \
  --format table  # or json \
  --api-key "token"
```

**Options:**
- `--format` - Output format: `table` or `json` (default: table)
- `--api-key` - API key
- `--api-url` - API URL

#### Get Project Details
```bash
socrates project get PROJECT_ID
```

**Options:**
- `--api-key` - API key
- `--api-url` - API URL

#### Update Project
```bash
socrates project update PROJECT_ID \
  --name "New Name" \
  --description "New description"
```

**Options:**
- `--name` - New project name
- `--description` - New description
- `--api-key` - API key
- `--api-url` - API URL

#### Export Project
```bash
socrates project export PROJECT_ID \
  --format csv \
  --output specs.csv
```

**Options:**
- `--format` - Export format: json, csv, markdown, yaml, html
- `--output` - Output file path (optional, outputs to stdout if not set)
- `--api-key` - API key
- `--api-url` - API URL

#### Delete Project
```bash
socrates project delete PROJECT_ID
```

**Options:**
- `--force` - Skip confirmation
- `--api-key` - API key
- `--api-url` - API URL

### Specification Commands

#### Create Specification
```bash
socrates spec create \
  --project PROJECT_ID \
  --category goals \
  --key objective1 \
  --value "Build API" \
  --content "Detailed description"
```

**Options:**
- `--project` - Project ID (required)
- `--category` - Category (required)
- `--key` - Specification key (required)
- `--value` - Specification value (required)
- `--content` - Detailed content (optional)
- `--api-key` - API key
- `--api-url` - API URL

#### List Specifications
```bash
socrates spec list \
  --project PROJECT_ID \
  --category goals \
  --format table \
  --limit 50
```

**Options:**
- `--project` - Project ID (required)
- `--category` - Filter by category (optional)
- `--format` - Output format: table or json (default: table)
- `--limit` - Number of results (default: 50)
- `--api-key` - API key
- `--api-url` - API URL

#### Import Specifications
```bash
socrates spec import \
  --project PROJECT_ID \
  --file specs.json \
  --format json
```

**Supported Formats:**
- `json` - JSON format
- `csv` - CSV spreadsheet
- `yaml` - YAML format

**Options:**
- `--project` - Project ID (required)
- `--file` - File path (required)
- `--format` - File format (auto-detected from extension)
- `--api-key` - API key
- `--api-url` - API URL

#### Export Specifications
```bash
socrates spec export \
  --project PROJECT_ID \
  --format csv \
  --output specs.csv \
  --category goals
```

**Supported Formats:**
- `json` - JSON with metadata
- `csv` - Spreadsheet format
- `markdown` - Documentation format
- `yaml` - Configuration format
- `html` - Styled web view

**Options:**
- `--project` - Project ID (required)
- `--format` - Export format (default: json)
- `--output` - Output file path (optional)
- `--category` - Filter by category (optional)
- `--api-key` - API key
- `--api-url` - API URL

#### Validate Specifications
```bash
socrates spec validate --project PROJECT_ID
```

Checks for conflicts, missing dependencies, and other issues.

**Options:**
- `--project` - Project ID (required)
- `--api-key` - API key
- `--api-url` - API URL

### Authentication Commands

#### Login
```bash
socrates auth login \
  --email user@example.com \
  --password (prompted if not provided)
```

Credentials are saved to `~/.socrates/credentials.json`

#### Logout
```bash
socrates auth logout
```

#### Token Management
```bash
# Generate new token
socrates auth token --generate

# Show current token (masked for security)
socrates auth token --show
```

#### Check Status
```bash
socrates auth status
```

#### Whoami
```bash
socrates auth whoami
```

### Configuration Commands

#### Initialize Configuration
```bash
socrates config init
```

Interactive setup for API URL and editor.

#### Set Configuration
```bash
socrates config set api_url http://api.example.com
socrates config set editor vim
socrates config set output_format json
socrates config set verbose true
```

#### Get Configuration
```bash
socrates config get api_url
```

#### List Configuration
```bash
socrates config list
socrates config list --format json
```

#### Validate Configuration
```bash
socrates config validate
```

Checks for required fields and valid values.

#### Reset Configuration
```bash
socrates config reset
```

## File Formats

### JSON Format
```json
{
  "specifications": [
    {
      "category": "goals",
      "key": "objective1",
      "value": "Build scalable API",
      "source": "user_input",
      "confidence": 0.95
    }
  ]
}
```

### CSV Format
```csv
category,key,value,source,confidence
goals,objective1,Build scalable API,user_input,0.95
tech_stack,framework,FastAPI,extracted,0.92
```

### YAML Format
```yaml
project_id: proj_123
specifications:
  - category: goals
    key: objective1
    value: Build scalable API
    source: user_input
    confidence: 0.95
```

### Markdown Format
```markdown
# Project Name - Specifications

## Goals
### objective1
Build scalable API
- Source: user_input (95% confidence)

## Tech Stack
### framework
FastAPI
- Source: extracted (92% confidence)
```

## Configuration

Configuration is stored in `~/.socrates/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "editor": "nano",
  "output_format": "table",
  "verbose": false
}
```

Credentials are stored in `~/.socrates/credentials.json` (user-readable only):

```json
{
  "email": "user@example.com",
  "token": "sk_live_...",
  "user_id": "user_123",
  "api_url": "http://localhost:8000"
}
```

## Examples

### Example 1: Create Project with Specifications
```bash
#!/bin/bash

# Create project
PROJECT=$(socrates project create --name "API Specification" --format json | jq -r '.id')

# Add specifications
socrates spec create \
  --project $PROJECT \
  --category goals \
  --key objective1 \
  --value "Build REST API"

socrates spec create \
  --project $PROJECT \
  --category tech_stack \
  --key framework \
  --value FastAPI

# Export as CSV
socrates spec export \
  --project $PROJECT \
  --format csv \
  --output specs.csv

echo "Project created: $PROJECT"
```

### Example 2: Batch Import and Export
```bash
#!/bin/bash

# Login
socrates auth login

# Import specifications
socrates spec import \
  --project proj_123 \
  --file input_specs.json

# Validate
socrates spec validate --project proj_123

# Export in multiple formats
for format in json csv markdown yaml html; do
  socrates spec export \
    --project proj_123 \
    --format $format \
    --output "specs.$format"
done

echo "Export complete"
```

### Example 3: Project Backup and Restore
```bash
#!/bin/bash

# Backup all projects
for proj in $(socrates project list --format json | jq -r '.[] | .id'); do
  socrates project export \
    --project $proj \
    --format json \
    --output "backup_$proj.json"
done

echo "Backup complete"
```

## Troubleshooting

### "API key required"
```bash
# Set environment variable
export SOCRATES_API_KEY="your_token"

# Or use --api-key flag
socrates project list --api-key "your_token"

# Or login
socrates auth login
```

### "File not found"
Ensure the file path is correct and readable:
```bash
socrates spec import --project proj_123 --file /path/to/specs.json
```

### "Invalid API URL"
Check your configuration:
```bash
socrates config get api_url
socrates config validate
```

### "Connection refused"
Ensure the API server is running:
```bash
# Check API status
curl -X GET http://localhost:8000/api/v1/admin/health
```

## Development

### Running from Source
```bash
cd backend
python socrates [command]
```

### Running Tests
```bash
cd backend
pytest tests/cli/
```

### Adding New Commands
1. Create command module in `app/cli/commands/`
2. Add command group to `app/cli/main.py`
3. Register in `__init__.py`

Example:
```python
# In app/cli/commands/newcommand.py
import click

@click.group(name="newcommand")
def newcommand():
    """Description of command group"""
    pass

@newcommand.command()
@click.option("--option", help="Option description")
def subcommand(option):
    """Subcommand description"""
    click.echo("Output")

# In app/cli/main.py
from .commands import newcommand
main.add_command(newcommand.newcommand)
```

## API Reference

The CLI communicates with the Socrates API. See the API documentation at `/docs` when the server is running.

## License

MIT License - See LICENSE file for details
