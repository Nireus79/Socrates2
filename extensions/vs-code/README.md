# Socrates - AI-Powered Specification Assistant for VS Code

[![Visual Studio Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=anthropic.socrates2)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://marketplace.visualstudio.com/items?itemName=anthropic.socrates2)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Bring your AI-generated specifications directly into VS Code. Generate code, detect conflicts, manage projects, and collaborate with your team—all without leaving your editor.

## Features

### 🚀 Quick Start
- **Seamless Authentication** - Sign in with one click, credentials stored securely
- **Project Browser** - Browse all your projects in the VS Code sidebar
- **Specification Management** - View and organize specifications by category

### 💻 Code Generation
- **One-Click Code Generation** - Generate code snippets from specifications
- **Multi-Language Support** - Python, JavaScript, Go, Java with auto-detection
- **Code Preview** - Review generated code before inserting
- **Insert or Copy** - Add code to your editor or copy to clipboard

### 🔍 Intelligent Features
- **Hover Documentation** - Hover over specification keys to see full details
- **Conflict Detection** - Real-time warnings for specification conflicts
- **Activity Feed** - See team activity and recent changes
- **Global Search** - Find specifications across all projects

### ⚙️ Configuration
- **API Server Configuration** - Connect to your Socrates instance
- **Auto-Sync** - Keep data fresh with configurable sync intervals
- **Code Gen Preferences** - Set default language and generation options
- **Theme Support** - Integrates with VS Code light/dark themes

## Installation

1. Open VS Code Extension Marketplace
2. Search for "Socrates"
3. Click Install
4. Reload VS Code

Or install from command line:
```bash
code --install-extension anthropic.socrates2
```

## Getting Started

### 1. Sign In
- Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
- Run `Socrates: Sign In`
- Enter your email and password
- Grant permission to access your projects

### 2. Select a Project
- Click on any project in the **Projects** sidebar
- Specifications for that project appear in the **Specifications** sidebar

### 3. Generate Code
**Method 1: From Specification View**
1. Right-click a specification in the sidebar
2. Click "Generate Code"
3. Select language (or auto-detect from current file)
4. Choose: Insert into Editor, Create New File, or Copy to Clipboard

**Method 2: From Editor Context Menu**
1. Right-click in any code file
2. Select "Generate Code from Specification"
3. Choose specification and language
4. Code is inserted at cursor position

### 4. View Details
- **Hover** over any specification key to see full details
- Click the info icon (ℹ️) next to specs for extended information
- View conflicts with warning badges

## Commands

### Core Commands
| Command | Shortcut | Description |
|---------|----------|-------------|
| `Socrates: Sign In` | `Ctrl+Shift+P` | Authenticate with Socrates |
| `Socrates: Sign Out` | `Ctrl+Shift+P` | Logout from Socrates |
| `Socrates: Settings` | `Ctrl+Shift+P` | Open configuration panel |

### Project Commands
| Command | Description |
|---------|-------------|
| `Socrates: Refresh Projects` | Reload projects from server |
| `Socrates: Create Project` | Create new project |
| `Socrates: Open Project` | View project details |

### Specification Commands
| Command | Description |
|---------|-------------|
| `Socrates: Refresh Specifications` | Reload specs for current project |
| `Socrates: View Specification Details` | Show spec information |
| `Socrates: Search Specifications` | Global search across all specs |
| `Socrates: Generate Code from Specification` | Create code from spec |

### Other Commands
| Command | Description |
|---------|-------------|
| `Socrates: View Project Conflicts` | Show all conflicts |
| `Socrates: Show Team Activity` | Display activity feed |

## Settings

Open extension settings via Command Palette or VS Code Settings:

### `socrates.apiUrl`
- **Type:** `string`
- **Default:** `http://localhost:8000`
- **Description:** URL of your Socrates API server

### `socrates.autoSync`
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Automatically refresh data from server

### `socrates.syncInterval`
- **Type:** `number`
- **Default:** `30000`
- **Description:** Sync interval in milliseconds (minimum: 5000)

### `socrates.codeGenLanguage`
- **Type:** `string`
- **Default:** `auto-detect`
- **Options:** `auto-detect`, `python`, `javascript`, `go`, `java`
- **Description:** Default language for code generation

### `socrates.enableConflictWarnings`
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Show warnings for specification conflicts

### `socrates.theme`
- **Type:** `string`
- **Default:** `auto`
- **Options:** `light`, `dark`, `auto`
- **Description:** Extension theme (auto follows VS Code)

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Command Palette | `Ctrl+Shift+P` / `Cmd+Shift+P` |
| Generate Code | `Alt+Ctrl+G` / `Alt+Cmd+G` |
| Quick Settings | `Alt+Ctrl+,` / `Alt+Cmd+,` |
| Refresh Projects | `F5` (in Socrates view) |

## Usage Examples

### Generate Python Function from Spec
```
1. Open a .py file
2. Right-click → "Generate Code from Specification"
3. Select "api_rate_limiter" spec
4. Language auto-detects as Python
5. Code is inserted at cursor
```

### Create New File from Spec
```
1. Press Ctrl+Shift+P
2. Type "Generate Code"
3. Select specification
4. Choose "Create New File"
5. File is created and opened
```

### Check Conflicts in Your Project
```
1. Open Socrates view (icon in activity bar)
2. Click "View Project Conflicts"
3. See all conflicts with descriptions
4. Click to navigate to related specifications
```

### Configure API Server
```
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Socrates: Settings"
3. Update API URL
4. Click "Save Settings"
5. Extension reconnects to new server
```

## Troubleshooting

### Extension won't load
- Check that VS Code version is 1.85.0 or higher
- Try reloading VS Code (`Reload Window` command)
- Check extension logs in Output panel

### Can't authenticate
- Verify your username and password
- Check that API server is running and reachable
- Confirm API URL in settings (default: `http://localhost:8000`)

### Specifications not loading
- Refresh projects with `Socrates: Refresh Projects`
- Verify you've selected a project
- Check that project has specifications defined
- Look at Output panel for error details

### Code generation fails
- Ensure file is open with recognized language
- Check that specification exists
- Verify API server is running
- See Output panel for specific error

### Performance issues
- Disable auto-sync if not needed (`socrates.autoSync: false`)
- Increase sync interval (`socrates.syncInterval: 60000`)
- Close unnecessary projects
- Check Output panel for slow operations

## Support

### Documentation
- [Socrates Documentation](https://docs.socrates2.ai)
- [Socrates API Docs](https://api.socrates2.ai/docs)
- [VS Code Extension Docs](https://docs.socrates2.ai/vscode)

### Feedback & Issues
- [Report a Bug](https://github.com/anthropics/socrates2/issues)
- [Request a Feature](https://github.com/anthropics/socrates2/issues)
- [Discussion Forum](https://github.com/anthropics/socrates2/discussions)

### Community
- [GitHub Discussions](https://github.com/anthropics/socrates2/discussions)
- [Discord Server](https://discord.gg/socrates2)
- [Twitter](https://twitter.com/socrates2)

## Release Notes

### 0.1.0 (Initial Release)
- ✨ Project browser with sidebar view
- ✨ Specification viewer with category organization
- ✨ Multi-language code generation (Python, JS, Go, Java)
- ✨ Hover documentation for specifications
- ✨ Real-time conflict detection with warnings
- ✨ Team activity feed
- ✨ Configuration panel with settings management
- ✨ Secure authentication with credential storage
- ✨ Auto-sync with configurable intervals
- ✨ Global specification search

## License

MIT License - See LICENSE file for details

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Author

Created with ❤️ by [Anthropic](https://anthropic.com)

---

**[Install Now](https://marketplace.visualstudio.com/items?itemName=anthropic.socrates2)** | **[Documentation](https://docs.socrates2.ai)** | **[Report Issue](https://github.com/anthropics/socrates2/issues)**
