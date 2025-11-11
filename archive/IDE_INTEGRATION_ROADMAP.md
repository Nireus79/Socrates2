# IDE Integration Roadmap for Socrates

**Date:** November 10, 2025
**Status:** Planning Phase - Not Yet Implemented
**Priority:** Medium (Post-Phase 1)

---

## Current State

### ✅ What Exists
- **Code Generation**: Backend generates code and stores in database (`GeneratedFile` model)
- **Code Export**: ZIP file download available via HTTP endpoint (`/api/v1/code-generation/{generation_id}/download`)
- **Project Structure**: Generated files have file paths and content stored

### ❌ What's Missing
- **Direct File System Writing**: Code is never written directly to disk
- **IDE Extension**: No VS Code extension, PyCharm plugin, or IDE integration
- **Live Sync**: No real-time synchronization between IDE and Socrates backend
- **Project Import**: Cannot import existing IDE project into Socrates
- **File Watchers**: No monitoring of file changes in IDE
- **Language Server Protocol (LSP)**: No LSP implementation for IDE features

---

## Architecture

### Current Flow (Database → ZIP Download)
```
Claude API
    ↓
Code Generator Agent
    ↓
Database (GeneratedFile table)
    ↓
Export Endpoint
    ↓
ZIP File Download
    ↓
Manual extraction by user
```

### Future Flow (Database ↔ IDE Real-Time)
```
IDE (VS Code/PyCharm)
    ↕ (WebSocket)
IDE Integration Service
    ↕ (HTTP/gRPC)
Socrates Backend
    ↓
Code Generator → Database
    ↓
IDE Extension listens for changes
    ↓
Automatically syncs files to IDE workspace
```

---

## Phase 1: VS Code Extension (Basic Integration)

### 📋 Requirements
- **Language:** TypeScript (VS Code SDK)
- **Dependencies:** @types/vscode, axios, uuid
- **Architecture:** Client-side extension + backend API

### 🎯 Features
1. **Authentication**
   - Sign in to Socrates backend
   - Store bearer token in VS Code secrets API
   - Auto-refresh JWT tokens

2. **Project Management**
   - Connect IDE workspace to Socrates project
   - Sync project ID and metadata
   - Display project status in sidebar

3. **Code Synchronization**
   - Watch for generated code changes
   - Auto-download and extract to workspace
   - Option: auto-upload project files to Socrates

4. **UI Components**
   - Sidebar panel showing projects/sessions
   - Status indicator (synced/unsynced)
   - Quick actions (regenerate code, create new spec)

### 📁 File Structure
```
socrates2-vscode-extension/
├── package.json
├── tsconfig.json
├── webpack.config.js
├── src/
│   ├── extension.ts           # Entry point
│   ├── activate.ts            # Activation logic
│   ├── auth/
│   │   ├── authentication.ts  # OAuth/JWT handling
│   │   └── secrets.ts         # VS Code secrets storage
│   ├── workspace/
│   │   ├── sync.ts            # File synchronization
│   │   └── watcher.ts         # File change watcher
│   ├── ui/
│   │   ├── sidebar.ts         # Sidebar provider
│   │   ├── statusbar.ts       # Status bar updates
│   │   └── commands.ts        # Registered commands
│   ├── api/
│   │   ├── client.ts          # HTTP client
│   │   ├── projects.ts        # Project API
│   │   └── generation.ts      # Code generation API
│   └── utils/
│       ├── config.ts          # Extension config
│       └── logger.ts          # Logging
└── README.md
```

### 🔌 New Backend API Endpoints Needed
```
GET    /api/v1/extensions/auth/token      # Get/refresh token
POST   /api/v1/extensions/workspace/init  # Initialize workspace
POST   /api/v1/extensions/workspace/sync  # Sync files
POST   /api/v1/extensions/log              # Extension logging
```

### ⏱️ Estimated Time: 2-3 weeks

---

## Phase 2: PyCharm / IntelliJ Integration

### 🎯 Similar to VS Code but:
- **Language:** Kotlin/Java (JetBrains SDK)
- **IDE Compatibility:** PyCharm, IntelliJ IDEA, WebStorm
- **Dependencies:** IntelliJ Platform SDK

### Features
- Same as VS Code extension
- Right-click context menu for quick actions
- Integrated debugging with Socrates specs

### ⏱️ Estimated Time: 3-4 weeks

---

## Phase 3: Language Server Protocol (LSP)

### 🎯 Benefits
- **Language-Agnostic**: Works with any LSP-compatible editor
- **Rich IDE Features**:
  - Autocomplete based on specs
  - Hover documentation from specifications
  - Go-to-definition for components
  - Find-all-references across project
  - Rename refactoring

### Architecture
```
LSP Server (Python FastAPI)
    ↕
IDE (any LSP client)

Supported Methods:
- initialize
- textDocument/definition
- textDocument/references
- textDocument/hover
- textDocument/completion
- workspace/symbol
```

### ⏱️ Estimated Time: 4-5 weeks

---

## Phase 4: File System Direct Write

### 🔄 Current Limitations
**Database-First Approach:**
- Generated code stored in PostgreSQL
- Users must download and extract ZIP
- No automatic project structure creation

### ✨ Proposed Solution
**Optional File System Writing:**
- Add `file_write` permission flag to projects
- When enabled: automatically write files to designated directory
- Watch for changes and sync back to database
- Requires:
  - User grants file system access permission
  - Project linked to local filesystem path
  - Real-time file watcher (watchdog library)

### Implementation
```python
# New model: ProjectFileSystem
class ProjectFileSystem:
    project_id: UUID
    local_path: str  # User's workspace directory
    auto_sync: bool
    write_enabled: bool
    last_sync: DateTime
    permission_hash: str  # Hash of user approval

# New endpoint
POST /api/v1/projects/{id}/link-workspace
{
    "local_path": "C:\\Users\\user\\Projects\\MyProject",
    "auto_sync": true
}
```

### ⏱️ Estimated Time: 2-3 weeks

---

## Implementation Roadmap

```
Timeline:
│
├─ Weeks 1-3   Phase 1: VS Code Extension
├─ Weeks 4-7   Phase 2: PyCharm Integration
├─ Weeks 8-12  Phase 3: LSP Server
└─ Weeks 13-15 Phase 4: File System Write

Total: ~15 weeks (3.5 months)
```

---

## Dependencies to Add

### Backend
```python
# pyproject.toml additions for LSP
python-lsp-server = "^1.7.0"      # LSP server
pygls = "^1.2.0"                  # LSP protocol implementation
watchdog = "^4.0.0"               # File system watching
```

### Frontend (VS Code)
```json
{
  "@types/vscode": "^1.85.0",
  "axios": "^1.7.0",
  "uuid": "^9.0.1"
}
```

---

## Security Considerations

1. **API Keys**: Store extension API keys in VS Code secrets, not config
2. **File Access**: Require explicit user permission for file write
3. **CORS**: Handle CORS properly for IDE extensions
4. **Token Refresh**: Auto-refresh JWT tokens silently
5. **Audit Logging**: Log all IDE-initiated code changes

---

## Success Criteria

- [  ] VS Code extension published on marketplace
- [  ] 100+ downloads in first month
- [  ] File sync works reliably (>99% success)
- [  ] Auto-sync latency < 2 seconds
- [  ] Zero data loss during sync operations
- [  ] PyCharm extension available
- [  ] LSP server supports all major editors

---

## Notes for Future Implementation

1. **Start with VS Code**: Largest market share among Python developers
2. **Use existing libraries**: Don't reinvent LSP, use pygls
3. **Test file sync**: Extensively test file sync for race conditions
4. **Document security**: File access is a security concern
5. **Monitor performance**: Watch for slowdowns with large projects

---

## References

- [VS Code Extension Development](https://code.visualstudio.com/api)
- [IntelliJ Platform SDK](https://plugins.jetbrains.com/docs/intellij)
- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
- [Watchdog Library](https://watchdog.readthedocs.io/)
