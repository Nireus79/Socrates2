# Phase 5: Feature Gaps Implementation Guide

**Duration:** 4 weeks (27 days)
**Priority:** MEDIUM (user experience improvements)
**Features:** 27 missing features across CLI, export, notifications, collaboration

---

## Overview

Implement remaining features from initial requirements that don't fit into core phases:

**Grouped into 4 categories:**
1. CLI Improvements (5 features, 7 days)
2. Export Formats (4 features, 5 days)
3. Notifications (5 features, 8 days)
4. Team Collaboration (5 features, 7 days)

---

## Category 1: CLI Improvements (5 features, 7 days)

### Feature 1: Rich Progress Bars (2 days)

**Implementation:** Use `rich` library for progress visualization

```python
from rich.progress import track

for item in track(items, description="Processing..."):
    # Process item
    pass
```

**Use Cases:**
- Long-running analyses
- Bulk operations
- File uploads/downloads

### Feature 2: Colorized Output (1 day)

**Implementation:** Use `rich` console for styled output

```python
from rich.console import Console
from rich.panel import Panel

console = Console()
console.print(Panel("Success!", style="bold green"))
console.print("[red]Error occurred[/red]")
```

**Apply to:**
- Error messages (red)
- Warnings (yellow)
- Success messages (green)
- Info messages (blue)

### Feature 3: Command History (1 day)

**Implementation:** Store commands in SQLite database

```python
class CommandHistory:
    def save(self, command: str):
        # Save to ~/.socrates2/history.db
        pass

    def get_last(self, n: int = 10) -> List[str]:
        # Retrieve last N commands
        pass
```

**Enable up-arrow key navigation through history**

### Feature 4: Autocomplete (2 days)

**Implementation:** Use `prompt_toolkit` for autocomplete

```python
from prompt_toolkit.completion import Completer, Completion

class SocratesCompleter(Completer):
    def get_completions(self, document, complete_event):
        # /project, /spec, /search, etc.
        pass
```

### Feature 5: Configuration Wizard (1 day)

**Implementation:** Interactive setup

```python
def setup_wizard():
    api_key = prompt("Enter OpenAI API key: ")
    default_project = prompt("Default project name: ")
    # Save to ~/.socrates2/config.ini
```

---

## Category 2: Export Formats (4 features, 5 days)

### Feature 6: Export to JSON (1 day)

```python
@router.post("/projects/{id}/export/json")
async def export_json(project_id: str, ...):
    """Export project specifications as JSON"""
    specs = get_project_specs(project_id)
    return {
        "project": project_to_dict(project),
        "specifications": [s.to_dict() for s in specs]
    }
```

### Feature 7: Export to CSV (1 day)

```python
@router.post("/projects/{id}/export/csv")
async def export_csv(project_id: str, ...):
    """Export specifications as CSV"""
    import csv
    specs = get_project_specs(project_id)
    # Create CSV with headers: key, value, category, content
```

### Feature 8: Export to Markdown (1 day)

```python
@router.post("/projects/{id}/export/markdown")
async def export_markdown(project_id: str, ...):
    """Export specifications as Markdown"""
    specs = get_project_specs(project_id)
    # Format as:
    # # Project Name
    # ## Specifications
    # ### Key: value
```

### Feature 9: Export to YAML (1 day)

```python
@router.post("/projects/{id}/export/yaml")
async def export_yaml(project_id: str, ...):
    """Export specifications as YAML"""
    import yaml
    specs = get_project_specs(project_id)
    # Format as structured YAML
```

### Feature 10: Export Project Report (PDF) (1 day)

```python
@router.post("/projects/{id}/export/pdf")
async def export_pdf(project_id: str, ...):
    """Generate PDF report with project summary"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    # Create PDF with project info, maturity, specs
```

---

## Category 3: Notifications (5 features, 8 days)

### Feature 11: Email Notifications (SendGrid) (3 days)

```python
# backend/app/services/email_service.py

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    def __init__(self, api_key: str):
        self.sg = SendGridAPIClient(api_key)

    def send_conflict_alert(self, user_email: str, conflict_info: dict):
        """Alert user about specification conflicts"""
        message = Mail(
            from_email="no-reply@socrates2.com",
            to_emails=user_email,
            subject="Conflict Detected in Your Project",
            html_content=f"<p>Conflict in project: {conflict_info['project']}</p>"
        )
        self.sg.send(message)

    def send_trial_expiring(self, user_email: str, days_left: int):
        """Remind user trial is expiring"""
        message = Mail(
            from_email="no-reply@socrates2.com",
            to_emails=user_email,
            subject=f"Your trial expires in {days_left} days",
            html_content=f"..."
        )
        self.sg.send(message)
```

### Feature 12: Conflict Detection Alerts (2 days)

**When conflicts detected:**
- Email user immediately
- Log event to analytics
- Show notification in CLI/UI

### Feature 13: Maturity Milestone Notifications (1 day)

**When project reaches milestones:**
- 50% maturity: "Halfway there!" notification
- 75% maturity: "Almost complete!" notification
- 100% maturity: "Project complete!" celebration

### Feature 14: Trial Expiration Reminders (1 day)

**Send at:**
- 7 days before expiry
- 3 days before expiry
- 1 day before expiry
- On expiry day

### Feature 15: Webhook Notifications (1 day)

```python
# Allow users to set custom webhook URLs for events
@router.post("/projects/{id}/webhooks/create")
async def create_webhook(
    project_id: str,
    event_type: str,  # conflict_detected, maturity_updated, etc.
    webhook_url: str
):
    """Create webhook subscription"""
    webhook = Webhook(
        project_id=project_id,
        event_type=event_type,
        url=webhook_url,
        active=True
    )
    db.add(webhook)
    db.commit()
```

---

## Category 4: Team Collaboration (5 features, 7 days)

### Feature 16: Real-Time Collaboration (WebSockets) (2 days)

```python
from fastapi import WebSocket

@router.websocket("/ws/project/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket for real-time spec updates"""
    await websocket.accept()

    while True:
        data = await websocket.receive_json()
        # Broadcast to other connected users
        await manager.broadcast(
            f"project:{project_id}",
            data
        )
```

### Feature 17: Comment Threads on Specs (2 days)

```python
class SpecificationComment(Base):
    __tablename__ = "specification_comments"

    id = Column(UUID, primary_key=True)
    specification_id = Column(UUID, ForeignKey("specifications.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
```

### Feature 18: @mentions in Comments (2 days)

```python
# Parse mentions in comments
@staticmethod
def extract_mentions(text: str) -> List[str]:
    import re
    pattern = r'@(\w+)'
    return re.findall(pattern, text)

# Send notifications when mentioned
def notify_mentions(comment: SpecificationComment):
    mentions = extract_mentions(comment.content)
    for username in mentions:
        user = get_user_by_username(username)
        email_service.send_mention_notification(
            user.email,
            f"You were mentioned in a comment"
        )
```

### Feature 19: Activity Feed (2 days)

```python
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String(50))  # spec_added, spec_updated, comment_added, etc.
    resource_type = Column(String(50))
    resource_id = Column(UUID)
    timestamp = Column(DateTime(timezone=True))

@router.get("/projects/{id}/activity")
async def get_activity_feed(project_id: str, limit: int = 50):
    """Get recent project activity"""
    activities = db.query(ActivityLog).filter(
        ActivityLog.project_id == project_id
    ).order_by(
        ActivityLog.timestamp.desc()
    ).limit(limit).all()
    return activities
```

### Feature 20: Notification Preferences (1 day)

```python
class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    email_on_conflict = Column(Boolean, default=True)
    email_on_maturity = Column(Boolean, default=True)
    email_on_mention = Column(Boolean, default=True)
    digest_frequency = Column(String(20))  # real_time, daily, weekly, off

@router.post("/notifications/preferences")
async def update_preferences(
    preferences: NotificationPreferences,
    current_user = Depends(get_current_active_user)
):
    """Update user notification preferences"""
```

---

## Remaining 7 Features (7 days)

### Feature 21: Project Templates
- Pre-built project templates (API spec, architecture design, requirements)
- Save current project as template
- Clone from template

### Feature 22: Bulk Operations
- Bulk export multiple projects
- Bulk delete specifications
- Bulk update category

### Feature 23: Advanced Filters
- Filter by maturity range
- Filter by creation date
- Filter by last updated
- Saved filters

### Feature 24: Custom Reports
- User-defined report format
- Schedule report emails (daily/weekly)
- Export reports as PDF/Excel

### Feature 25: API Webhooks
- Subscribe to project events
- Receive POST on spec changes
- Custom payload templates

### Feature 26: Audit Logging Enhancements
- Track all specification changes (who changed what)
- Restore previous specification versions
- Change history view

### Feature 27: Performance Optimizations
- Query result caching (Redis)
- Lazy-load specifications
- Database query optimization
- API response compression

---

## Implementation Priority

**Must-Have (Phase 5a):**
1. Email notifications
2. Colorized CLI output
3. Export to JSON/CSV/Markdown

**Nice-to-Have (Phase 5b):**
4. WebSocket real-time collaboration
5. Comment threads
6. Activity feed

**Polish (Phase 5c):**
7. Autocomplete
8. Command history
9. Performance optimizations

---

## Testing Checklist

- [ ] All export formats produce valid files
- [ ] Emails send correctly (SendGrid)
- [ ] WebSocket connections persist
- [ ] Mentions parse correctly
- [ ] Activity feed shows correct events
- [ ] Notification preferences enforced
- [ ] Performance queries <500ms

---

## Next Phase

Once Phase 5 completes: Move to **Phase 6 (IDE Integration)** for VS Code/PyCharm extensions and LSP.
