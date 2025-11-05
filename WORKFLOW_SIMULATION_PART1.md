# User Workflow Simulation - Part 1: Registration & Project Setup

**Scenario:** John, a developer, wants to build an e-commerce platform for local artisans.

---

## 1. Registration

### User Action:
```bash
$ python cli/main.py

Welcome to Socrates - Agentic RAG System
Version 2.0

> /register

Enter username: john_developer
Enter email: john@example.com
Enter password: ********
Confirm password: ********
```

### System Internal Processing:

**Step 1: AgentOrchestrator receives request**
```python
orchestrator.route_request(
    agent_id='user',
    action='register',
    data={
        'username': 'john_developer',
        'email': 'john@example.com',
        'password': 'entered_password'
    }
)
```

**Step 2: UserManagerAgent processes registration**
```python
# Location: backend/app/agents/user_manager.py
class UserManagerAgent(BaseAgent):
    def _register(self, data):
        # 1. Validate input
        if len(data['password']) < 8:
            return {'success': False, 'error': 'Password too short'}

        # 2. Check if username exists
        existing = self.db.query(User).filter_by(username=data['username']).first()
        if existing:
            return {'success': False, 'error': 'Username already taken'}

        # 3. Hash password
        password_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())

        # 4. Create user (socrates_auth database)
        user = User(
            id=uuid4(),
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )

        # 5. Save to database
        self.db.add(user)
        self.db.commit()  # ⚠️ CRITICAL: Explicit commit before close
        self.db.refresh(user)

        # 6. Initialize user preferences (defaults)
        user_rules = UserRules(
            user_id=user.id,
            rules={
                'communication_style': 'concise',
                'preferred_roles': ['pm', 'backend'],
                'question_frequency': 'moderate'
            }
        )
        self.db.add(user_rules)
        self.db.commit()

        return {
            'success': True,
            'user_id': str(user.id),
            'username': user.username
        }
```

**Step 3: Database State (socrates_auth)**
```sql
-- Table: users
INSERT INTO users (id, username, email, password_hash, created_at)
VALUES ('user_001', 'john_developer', 'john@example.com', '$2b$12...', '2025-11-05 14:30:00');

-- Table: user_rules
INSERT INTO user_rules (id, user_id, rules, created_at)
VALUES ('rules_001', 'user_001', '{"communication_style": "concise", ...}', '2025-11-05 14:30:00');
```

### User Feedback:
```
✅ Registration successful!

User ID: user_001
Username: john_developer
Email: john@example.com

Default preferences set:
  • Communication style: Concise
  • Preferred roles: PM, Backend Developer

You can now login with: /login
```

---

## 2. Login

### User Action:
```bash
> /login

Username: john_developer
Password: ********
```

### System Internal Processing:

**Step 1: UserManagerAgent authenticates**
```python
# Location: backend/app/agents/user_manager.py
def _authenticate(self, data):
    # 1. Find user
    user = self.db.query(User).filter_by(username=data['username']).first()

    if not user:
        return {'success': False, 'error': 'Invalid credentials'}

    # 2. Verify password
    password_match = bcrypt.checkpw(
        data['password'].encode(),
        user.password_hash.encode()
    )

    if not password_match:
        return {'success': False, 'error': 'Invalid credentials'}

    # 3. Generate JWT token
    token_payload = {
        'sub': str(user.id),           # Subject (user_id)
        'username': user.username,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(minutes=30),  # Expires in 30 min
        'iat': datetime.utcnow()       # Issued at
    }

    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

    # 4. Update last login
    user.last_login = datetime.utcnow()
    self.db.commit()

    return {
        'success': True,
        'token': token,
        'user_id': str(user.id),
        'username': user.username,
        'expires_in': 1800  # seconds
    }
```

**Step 2: Store token in CLI session**
```python
# CLI stores token for future requests
session_state = {
    'token': token,
    'user_id': 'user_001',
    'username': 'john_developer',
    'expires_at': datetime.utcnow() + timedelta(minutes=30)
}
```

### User Feedback:
```
✅ Login successful!

Welcome back, john_developer!

Token expires in: 30 minutes
Session ID: cli_session_001

Available commands:
  /create project  - Create a new project
  /list            - List your projects
  /status          - Show current project status
  /help            - Show all commands
  /logout          - Logout

> _
```

---

## 3. Project Creation

### User Action:
```bash
> /create project

Project name: E-commerce Platform
Description: Online marketplace for handmade crafts by local artisans
```

### System Internal Processing:

**Step 1: Validate authentication**
```python
# CLI sends request with JWT token
headers = {'Authorization': f'Bearer {token}'}

# FastAPI dependency extracts user_id from token
def get_current_user(authorization: str = Header(...)):
    token = authorization.replace('Bearer ', '')
    payload = jwt.decode(token, SECRET_KEY)
    return payload['sub']  # Returns 'user_001'
```

**Step 2: AgentOrchestrator routes to ProjectManagerAgent**
```python
orchestrator.route_request(
    agent_id='project',
    action='create_project',
    data={
        'user_id': 'user_001',
        'name': 'E-commerce Platform',
        'description': 'Online marketplace for handmade crafts by local artisans'
    }
)
```

**Step 3: ProjectManagerAgent creates project**
```python
# Location: backend/app/agents/project_manager.py
def _create_project(self, data):
    # 1. Create project (socrates_specs database)
    project = Project(
        id=uuid4(),
        owner_id=data['user_id'],
        name=data['name'],
        description=data['description'],
        phase='discovery',      # Start in Discovery phase
        status='active',
        created_at=datetime.utcnow()
    )

    self.db.add(project)
    self.db.commit()
    self.db.refresh(project)

    # 2. Initialize maturity tracking (10 categories, all at 0%)
    maturity_categories = [
        'goals', 'requirements', 'tech_stack', 'scalability',
        'security', 'testing', 'deployment', 'monitoring',
        'team_structure', 'timeline'
    ]

    for category in maturity_categories:
        maturity = MaturityTracking(
            id=uuid4(),
            project_id=project.id,
            category=category,
            score=0.0,
            last_updated=datetime.utcnow()
        )
        self.db.add(maturity)

    self.db.commit()

    # 3. Create first session (Socratic mode by default)
    session = Session(
        id=uuid4(),
        project_id=project.id,
        mode='socratic',        # Start in Socratic mode
        status='active',
        created_at=datetime.utcnow()
    )

    self.db.add(session)
    self.db.commit()
    self.db.refresh(session)

    # 4. Log project creation in conversation history
    history = ConversationHistory(
        id=uuid4(),
        session_id=session.id,
        type='system',
        content=f'Project "{project.name}" created. Starting Discovery phase.',
        created_at=datetime.utcnow()
    )

    self.db.add(history)
    self.db.commit()

    return {
        'success': True,
        'project_id': str(project.id),
        'project_name': project.name,
        'phase': project.phase,
        'session_id': str(session.id),
        'mode': session.mode
    }
```

**Step 4: Database State (socrates_specs)**
```sql
-- Table: projects
INSERT INTO projects (id, owner_id, name, description, phase, status, created_at)
VALUES ('proj_001', 'user_001', 'E-commerce Platform',
        'Online marketplace for handmade crafts by local artisans',
        'discovery', 'active', '2025-11-05 14:35:00');

-- Table: maturity_tracking (10 records, one per category)
INSERT INTO maturity_tracking (id, project_id, category, score, last_updated)
VALUES
  ('mat_001', 'proj_001', 'goals', 0.0, '2025-11-05 14:35:00'),
  ('mat_002', 'proj_001', 'requirements', 0.0, '2025-11-05 14:35:00'),
  ('mat_003', 'proj_001', 'tech_stack', 0.0, '2025-11-05 14:35:00'),
  ('mat_004', 'proj_001', 'scalability', 0.0, '2025-11-05 14:35:00'),
  ('mat_005', 'proj_001', 'security', 0.0, '2025-11-05 14:35:00'),
  ('mat_006', 'proj_001', 'testing', 0.0, '2025-11-05 14:35:00'),
  ('mat_007', 'proj_001', 'deployment', 0.0, '2025-11-05 14:35:00'),
  ('mat_008', 'proj_001', 'monitoring', 0.0, '2025-11-05 14:35:00'),
  ('mat_009', 'proj_001', 'team_structure', 0.0, '2025-11-05 14:35:00'),
  ('mat_010', 'proj_001', 'timeline', 0.0, '2025-11-05 14:35:00');

-- Table: sessions
INSERT INTO sessions (id, project_id, mode, status, created_at)
VALUES ('sess_001', 'proj_001', 'socratic', 'active', '2025-11-05 14:35:00');

-- Table: conversation_history
INSERT INTO conversation_history (id, session_id, type, content, created_at)
VALUES ('msg_001', 'sess_001', 'system',
        'Project "E-commerce Platform" created. Starting Discovery phase.',
        '2025-11-05 14:35:00');
```

### User Feedback:
```
✅ Project created successfully!

Project Details:
  • Name: E-commerce Platform
  • ID: proj_001
  • Phase: Discovery (Phase 1 of 4)
  • Status: Active

Maturity: 0% (0/10 categories)
  • Goals: 0%
  • Requirements: 0%
  • Tech stack: 0%
  • Scalability: 0%
  • Security: 0%
  • Testing: 0%
  • Deployment: 0%
  • Monitoring: 0%
  • Team structure: 0%
  • Timeline: 0%

Session: sess_001 (Socratic Mode)

─────────────────────────────────────────────────────────────

The system will now guide you through specification gathering
using Socratic questioning from 7 professional roles.

You can:
  • Answer questions as they come
  • Toggle to Direct Chat mode: /toggle
  • Check status anytime: /status
  • View specifications: /specs

Preparing first question...
⏳ Generating...
```

---

## Summary of Part 1

### What Happened:
1. ✅ User registered (UserManagerAgent → socrates_auth database)
2. ✅ User logged in (JWT token generated, 30-minute expiry)
3. ✅ Project created (ProjectManagerAgent → socrates_specs database)
4. ✅ Maturity tracking initialized (10 categories at 0%)
5. ✅ First session created (Socratic mode)

### Database State After Part 1:

**socrates_auth:**
- 1 user record
- 1 user_rules record

**socrates_specs:**
- 1 project record
- 10 maturity_tracking records
- 1 session record
- 1 conversation_history record

### Agents Used:
1. **UserManagerAgent** - Registration, authentication
2. **ProjectManagerAgent** - Project creation, initialization

### Next: Part 2
- First Socratic question generation
- User answers (vague)
- Spec extraction
- Vagueness detection
- Follow-up questions

---

**Reference:**
- [VISION.md](./VISION.md) - Project goals
- [USER_WORKFLOW.md](./USER_WORKFLOW.md) - Complete workflow documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
