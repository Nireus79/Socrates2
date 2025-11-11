# Phase 6: IDE Integration Implementation Guide

**Duration:** 11 weeks (75 days)
**Priority:** MEDIUM (developer experience)
**Features:** VS Code Extension (21d) | PyCharm Plugin (21d) | LSP Server (28d) | File System Write (5d)

---

## Overview

Enable developers to use Socrates directly in their IDEs:

1. **VS Code Extension** - Sidebar with projects/specs, sync to workspace
2. **PyCharm Plugin** - Same features via JetBrains platform
3. **Language Server Protocol (LSP)** - Language-agnostic IDE support
4. **Direct File Write** - Auto-sync generated files to filesystem

**Expected Impact:** 5x faster adoption among developers

**Dependencies:**
- Node.js 18+ (VS Code)
- Kotlin SDK (PyCharm)
- Python 3.10+ (LSP server)

---

## Part 1: VS Code Extension (21 days)

### Architecture

```
VS Code Extension (TypeScript)
    ↕ HTTP/WebSocket
Socrates Backend (FastAPI)
    ↓
Database (PostgreSQL)
```

### Step 1: Setup Extension Project (2 days)

**Create extension structure:**
```
socrates-vscode/
├── src/
│   ├── extension.ts           # Entry point
│   ├── activate.ts            # Activation logic
│   ├── auth/
│   │   ├── authentication.ts  # OAuth/JWT
│   │   └── secrets.ts         # VS Code secrets API
│   ├── workspace/
│   │   ├── sync.ts            # File sync
│   │   └── watcher.ts         # File watcher
│   ├── ui/
│   │   ├── sidebar.ts         # Tree view provider
│   │   ├── statusbar.ts       # Status bar
│   │   └── commands.ts        # Command handlers
│   ├── api/
│   │   ├── client.ts          # HTTP client
│   │   ├── projects.ts        # Project API calls
│   │   └── generation.ts      # Code generation API
│   └── utils/
│       ├── config.ts          # Extension config
│       └── logger.ts          # Logging
├── package.json
├── tsconfig.json
├── webpack.config.js
└── README.md
```

### Step 2: Authentication (3 days)

**File:** `src/auth/authentication.ts`

```typescript
import * as vscode from 'vscode';

export class AuthenticationProvider {
    private context: vscode.ExtensionContext;
    private apiKey: string | undefined;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    async authenticate(serverUrl: string): Promise<string> {
        // Get API key from VS Code secrets
        this.apiKey = await this.context.secrets.get('socrates.apiKey');

        if (!this.apiKey) {
            // Prompt user for API key
            this.apiKey = await vscode.window.showInputBox({
                prompt: 'Enter your Socrates API Key',
                password: true
            });

            if (this.apiKey) {
                await this.context.secrets.store('socrates.apiKey', this.apiKey);
            }
        }

        return this.apiKey || '';
    }

    getAuthHeader(): { Authorization: string } {
        return {
            Authorization: `Bearer ${this.apiKey}`
        };
    }

    async refreshToken(): Promise<void> {
        // Implement JWT refresh logic
    }
}
```

### Step 3: Sidebar UI (4 days)

**File:** `src/ui/sidebar.ts`

```typescript
import * as vscode from 'vscode';

export class SocratesProvider implements vscode.TreeDataProvider<SocratesItem> {
    private projects: Project[] = [];

    async getChildren(element?: SocratesItem): Promise<SocratesItem[]> {
        if (!element) {
            // Root: show projects
            this.projects = await this.apiClient.listProjects();
            return this.projects.map(p => new ProjectItem(p));
        }

        if (element instanceof ProjectItem) {
            // Show specs for project
            const specs = await this.apiClient.listSpecs(element.project.id);
            return specs.map(s => new SpecItem(s));
        }

        return [];
    }

    getTreeItem(element: SocratesItem): vscode.TreeItem {
        return element;
    }
}

class ProjectItem extends vscode.TreeItem {
    constructor(public project: any) {
        super(project.name, vscode.TreeItemCollapsibleState.Collapsed);
        this.description = `${project.maturity_score}%`;
    }
}

class SpecItem extends vscode.TreeItem {
    constructor(public spec: any) {
        super(`${spec.key}: ${spec.value}`, vscode.TreeItemCollapsibleState.None);
        this.description = spec.category;
    }
}
```

### Step 4: File Sync (4 days)

**File:** `src/workspace/sync.ts`

```typescript
export class FileSyncService {
    async syncProjectToWorkspace(
        projectId: string,
        workspacePath: string
    ): Promise<void> {
        // Get generated files from API
        const files = await this.apiClient.getGeneratedFiles(projectId);

        // Write files to workspace
        for (const file of files) {
            const filePath = path.join(workspacePath, file.path);
            await this.ensureDirectoryExists(path.dirname(filePath));
            await fs.writeFile(filePath, file.content, 'utf-8');
        }

        vscode.window.showInformationMessage(
            `Synced ${files.length} files from Socrates`
        );
    }

    watchForChanges(workspacePath: string): void {
        const watcher = vscode.workspace.createFileSystemWatcher(workspacePath);

        watcher.onDidChange(async (uri) => {
            // Upload changed file back to Socrates
            const content = await fs.readFile(uri.fsPath, 'utf-8');
            await this.apiClient.uploadFile(uri.fsPath, content);
        });
    }
}
```

### Step 5: Commands & Actions (3 days)

**File:** `src/ui/commands.ts`

```typescript
export function registerCommands(context: vscode.ExtensionContext) {
    // Sync project to workspace
    vscode.commands.registerCommand('socrates.sync', async (item) => {
        const workspacePath = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (workspacePath && item instanceof ProjectItem) {
            await syncService.syncProjectToWorkspace(item.project.id, workspacePath);
        }
    });

    // Generate code for project
    vscode.commands.registerCommand('socrates.generate', async (item) => {
        if (item instanceof ProjectItem) {
            vscode.window.showInformationMessage('Generating code...');
            const result = await apiClient.generateCode(item.project.id);
            vscode.window.showInformationMessage(`Generated ${result.files_count} files`);
        }
    });

    // View spec details
    vscode.commands.registerCommand('socrates.viewSpec', async (item) => {
        if (item instanceof SpecItem) {
            const panel = vscode.window.createWebviewPanel(
                'specDetail',
                `Spec: ${item.spec.key}`,
                vscode.ViewColumn.Two
            );
            panel.webview.html = `
                <h1>${item.spec.key}</h1>
                <p>${item.spec.value}</p>
                <p>${item.spec.content}</p>
            `;
        }
    });
}
```

### Step 6: Backend API Endpoints (3 days)

**File:** `backend/app/api/extensions.py`

```python
@router.get("/extensions/projects")
async def list_projects(
    current_user: User = Depends(get_current_active_user)
):
    """List projects for IDE extension"""
    projects = db.query(Project).filter(
        Project.user_id == current_user.id
    ).all()
    return [p.to_dict() for p in projects]

@router.post("/extensions/workspace/init")
async def init_workspace(
    project_id: str,
    current_user = Depends(get_current_active_user)
):
    """Initialize workspace with project files"""
    files = db.query(GeneratedFile).filter(
        GeneratedFile.project_id == project_id
    ).all()
    return {"files": [f.to_dict() for f in files]}

@router.post("/extensions/log")
async def log_extension_event(
    event: str,
    data: dict,
    current_user = Depends(get_current_active_user)
):
    """Log extension events for analytics"""
    logger.info(f"Extension event: {event}", extra=data)
    return {"success": True}
```

### Step 7: Testing & Publishing (2 days)

**Manual Tests:**
```bash
# 1. Test authentication
# Open extension in debug mode, enter API key

# 2. Test project loading
# Should see list of projects in sidebar

# 3. Test sync
# Click "Sync Project" → should create files in workspace

# 4. Test file watching
# Edit file → should sync back to Socrates

# Publish to VS Code Marketplace
vsce package
vsce publish
```

---

## Part 2: PyCharm Plugin (21 days)

### Architecture
- Language: Kotlin (JetBrains SDK)
- Platforms: PyCharm, IntelliJ IDEA, WebStorm
- Same features as VS Code extension

### Steps (Similar to VS Code):
1. Setup IntelliJ Platform plugin project (3 days)
2. Tool window for sidebar (3 days)
3. Context menus (2 days)
4. File sync to IDE (4 days)
5. Settings/preferences (2 days)
6. Testing & publishing to JetBrains Marketplace (5 days)

---

## Part 3: Language Server Protocol (LSP) (28 days)

### Benefits
- Works with ANY LSP-compatible editor
- Rich IDE features: autocomplete, hover, go-to-definition

### Features

**1. Hover Documentation (3 days)**
```python
# Spec name → show value + content in hover
"textDocument/hover"
```

**2. Autocomplete (5 days)**
```python
# Complete spec keys/values
"textDocument/completion"
```

**3. Go-to-Definition (3 days)**
```python
# Jump from reference to spec definition
"textDocument/definition"
```

**4. Find References (3 days)**
```python
# Find all uses of a spec
"textDocument/references"
```

**5. Workspace Symbol (3 days)**
```python
# Search all specs in workspace
"workspace/symbol"
```

### Implementation

**File:** `backend/app/services/lsp_server.py`

```python
from pygls.server import LanguageServer
from pygls.protocol import LanguageServerProtocol

app = LanguageServer("socrates-lsp", "v0.1.0")

@app.feature("textDocument/hover")
def hover(ls: LanguageServer, params):
    """Hover over spec reference to see details"""
    document = ls.workspace.get_document(params.textDocument.uri)
    word = get_word_at_position(document, params.position)

    spec = find_spec(word)
    if spec:
        return Hover(contents=f"**{spec.key}**: {spec.value}")

    return None

@app.feature("textDocument/completion")
def completion(ls, params):
    """Auto-complete spec keys"""
    specs = get_all_specs()
    return [
        CompletionItem(label=s.key, detail=s.value)
        for s in specs
    ]
```

---

## Part 4: Direct File System Write (5 days)

### Model

```python
class ProjectFileSystem(Base):
    project_id = Column(UUID, ForeignKey("projects.id"))
    local_path = Column(String(500))  # /home/user/projects/MyProject
    auto_sync = Column(Boolean, default=True)
    write_enabled = Column(Boolean, default=False)
    last_sync = Column(DateTime(timezone=True))
    permission_hash = Column(String(255))  # SHA256 of user approval
```

### Implementation

```python
@router.post("/projects/{id}/link-workspace")
async def link_workspace(
    project_id: str,
    local_path: str,
    current_user = Depends(get_current_active_user)
):
    """Link project to local filesystem"""
    # Verify path exists and is writable
    if not os.path.exists(local_path) or not os.access(local_path, os.W_OK):
        raise HTTPException(status_code=400, detail="Invalid path")

    # Create ProjectFileSystem record
    fs = ProjectFileSystem(
        project_id=project_id,
        local_path=local_path,
        write_enabled=True
    )
    db.add(fs)
    db.commit()

    # Start watching directory
    watcher = watchdog.observers.Observer()
    handler = FileChangeHandler(project_id)
    watcher.schedule(handler, local_path)
    watcher.start()

    return {"success": True, "path": local_path}
```

---

## Database Changes

**Migration:** `036_create_extension_tables.py`

```python
class ExtensionSession(Base):
    __tablename__ = "extension_sessions"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    extension_type = Column(String(20))  # vscode, pycharm, lsp
    token = Column(String(255))
    last_activity = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))
```

---

## Cost Analysis

**Development:**
- VS Code: 3 weeks ($15k)
- PyCharm: 3 weeks ($15k)
- LSP: 4 weeks ($20k)
- Testing/Polish: 2 weeks ($10k)
- **Total:** $60k

**Publishing:**
- VS Code Marketplace: Free
- JetBrains Marketplace: Free
- Support overhead: ~5 hours/week

---

## Testing Checklist

- [ ] VS Code extension loads without errors
- [ ] PyCharm plugin appears in marketplace
- [ ] LSP server starts correctly
- [ ] Hover shows spec details
- [ ] Autocomplete suggests specs
- [ ] Go-to-definition jumps to spec file
- [ ] File sync works bidirectionally
- [ ] No performance degradation in IDE

---

## Deployment

**GitHub Releases:**
- Tag: v1.0.0
- Upload extension artifacts

**Marketplace Publishing:**
```bash
# VS Code
vsce publish --pat <token>

# PyCharm
gradle publishPlugin
```

---

## Next Steps After Phase 6

All core features implemented. Move to:
- **Library Extraction:** Extract core algorithms to `socrates-ai` PyPI package
- **Production Deployment:** Docker, Kubernetes, CDN
- **Growth:** Marketing, sales, community

---

## Success Metrics

- [ ] 1000+ VS Code downloads in first month
- [ ] 500+ PyCharm installs
- [ ] LSP adopted by 3+ editor communities
- [ ] File sync success rate >99%
- [ ] Average rating >4.5 stars
