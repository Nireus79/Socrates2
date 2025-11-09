# Implementation Phase 3: Advanced Features

**Duration:** 4-5 weeks
**Priority:** 🟢 MEDIUM - Important for team collaboration and insights
**Team Size:** 2-3 developers
**Effort:** 160 hours
**Prerequisite:** Phase 1 & 2 completion

---

## Phase Objectives

1. **Implement team collaboration features** (real-time, permissions)
2. **Build quality metrics system** (custom metrics, trends, visualization)
3. **Implement user learning system** (adaptive questioning, embeddings)
4. **Create analytics dashboard** (usage stats, trends, insights)
5. **Build admin panel** (user management, system monitoring)

---

## Tasks Breakdown

### Task 1: Team Collaboration Features (Week 1-2)
**Effort:** 45 hours | **Owner:** Developer 1

#### 1.1 Team Management
**Files:** `models/team.py`, `agents/team_collaboration.py`, `api/teams.py`

**Current Status:** Team model exists but collaboration incomplete

**Implementation:**

```python
# Extend Team model
class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)  # Owner
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(String(20), default='active')  # active, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_members: bool = False) -> Dict[str, Any]:
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_members:
            data['members'] = [m.to_dict() for m in self.members]
        return data

# Team endpoints
@router.post("/teams")
async def create_team(
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create new team."""
    team = Team(
        user_id=current_user.id,
        name=request.name,
        description=request.description
    )
    db_auth.add(team)
    db_auth.commit()

    return {
        'success': True,
        'team_id': str(team.id),
        'message': 'Team created successfully'
    }

@router.get("/teams")
async def list_teams(
    current_user: User = Depends(get_current_active_user)
):
    """List user's teams."""
    teams = db_auth.query(Team).filter(
        Team.user_id == current_user.id
    ).all()

    return {
        'success': True,
        'teams': [t.to_dict(include_members=True) for t in teams]
    }

@router.get("/teams/{team_id}")
async def get_team(
    team_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get team details."""
    team = db_auth.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return {
        'success': True,
        'team': team.to_dict(include_members=True)
    }
```

**Subtasks:**
- [ ] Enhance Team model with full fields
- [ ] Implement team creation endpoint
- [ ] Implement team listing endpoint
- [ ] Implement team details endpoint
- [ ] Implement team update endpoint
- [ ] Implement team deletion endpoint
- [ ] Add team owner verification
- [ ] Test team management flow

**Success Criteria:**
- Teams can be created, listed, updated, deleted
- Only owner can manage team settings
- Member list displayed correctly
- Tests passing

---

#### 1.2 Team Members & Permissions
**Files:** `models/team_member.py`, `api/teams.py`

**Implementation:**

```python
class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID, primary_key=True, default=uuid4)
    team_id = Column(UUID, ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default='member')  # owner, admin, editor, viewer
    status = Column(String(20), default='active')  # active, invited, declined
    joined_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'role': self.role,
            'status': self.status,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }

# Role-based permissions
ROLE_PERMISSIONS = {
    'owner': ['manage_team', 'manage_members', 'edit_projects', 'view_all'],
    'admin': ['manage_members', 'edit_projects', 'view_all'],
    'editor': ['edit_projects', 'view_all'],
    'viewer': ['view_all']
}

# Team member endpoints
@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: str,
    email: str,
    role: str = 'editor',
    current_user: User = Depends(get_current_active_user)
):
    """Invite user to team."""
    # Verify current user is team owner/admin
    team_member = db_auth.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not team_member or team_member.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Find user by email
    user = db_auth.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create member invitation
    new_member = TeamMember(
        team_id=team_id,
        user_id=user.id,
        role=role,
        status='invited'
    )
    db_auth.add(new_member)
    db_auth.commit()

    # Send invitation email (Phase 4)
    return {
        'success': True,
        'message': 'Invitation sent',
        'member_id': str(new_member.id)
    }

@router.put("/teams/{team_id}/members/{member_id}")
async def update_team_member(
    team_id: str,
    member_id: str,
    role: str,
    current_user: User = Depends(get_current_active_user)
):
    """Update team member role."""
    # Verify authorization
    member = db_auth.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.team_id == team_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = role
    db_auth.commit()

    return {'success': True, 'member': member.to_dict()}

@router.delete("/teams/{team_id}/members/{member_id}")
async def remove_team_member(
    team_id: str,
    member_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove member from team."""
    member = db_auth.query(TeamMember).filter(
        TeamMember.id == member_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db_auth.delete(member)
    db_auth.commit()

    return {'success': True, 'message': 'Member removed'}
```

**Subtasks:**
- [ ] Enhance TeamMember model
- [ ] Implement permission checking decorator
- [ ] Implement add member endpoint
- [ ] Implement update member role endpoint
- [ ] Implement remove member endpoint
- [ ] Implement member listing endpoint
- [ ] Add permission validation to all endpoints
- [ ] Test permission system

**Success Criteria:**
- Members can be added/removed
- Roles working correctly
- Permissions enforced
- Tests passing

---

#### 1.3 Project Sharing
**Files:** `models/project_share.py`, `api/projects.py`

**Current Issue:** Model exists but endpoints incomplete

**Implementation:**

```python
# Extend project sharing
class ProjectShare(Base):
    __tablename__ = "project_shares"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
    team_id = Column(UUID, ForeignKey("teams.id"), nullable=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    access_level = Column(String(20), default='viewer')  # viewer, editor, owner
    shared_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'team_id': str(self.team_id) if self.team_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'access_level': self.access_level,
            'shared_at': self.shared_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

# Endpoints
@router.post("/projects/{project_id}/share")
async def share_project(
    project_id: str,
    team_id: str = None,
    user_id: str = None,
    access_level: str = 'viewer',
    expires_at: datetime = None,
    current_user: User = Depends(get_current_active_user)
):
    """Share project with team or user."""
    # Verify current user owns project
    project = db_specs.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=403, detail="Not authorized")

    share = ProjectShare(
        project_id=project_id,
        team_id=team_id,
        user_id=user_id,
        access_level=access_level,
        expires_at=expires_at
    )
    db_specs.add(share)
    db_specs.commit()

    return {'success': True, 'share_id': str(share.id)}

@router.get("/projects/{project_id}/shares")
async def list_project_shares(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """List who project is shared with."""
    # Verify ownership
    shares = db_specs.query(ProjectShare).filter(
        ProjectShare.project_id == project_id
    ).all()

    return {
        'success': True,
        'shares': [s.to_dict() for s in shares]
    }
```

**Subtasks:**
- [ ] Enhance ProjectShare model
- [ ] Implement share endpoint
- [ ] Implement unshare endpoint
- [ ] Implement share listing
- [ ] Add access level checking to project endpoints
- [ ] Test project sharing flow

**Success Criteria:**
- Projects can be shared with teams/users
- Access levels enforced
- Share list displays correctly
- Tests passing

---

#### 1.4 Real-time Collaboration (Async)
**Files:** `agents/team_collaboration.py`

**Implementation (WebSocket foundation):**

```python
from fastapi import WebSocket
from typing import Set
import json

class CollaborationManager:
    """Manage real-time collaboration sessions."""

    def __init__(self):
        self.active_sessions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Connect to collaboration session."""
        await websocket.accept()
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = set()
        self.active_sessions[session_id].add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        """Disconnect from collaboration session."""
        self.active_sessions[session_id].discard(websocket)

    async def broadcast(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to all users in session."""
        if session_id in self.active_sessions:
            for connection in self.active_sessions[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

# WebSocket endpoint
@router.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Real-time collaboration websocket."""
    await collaboration_manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast to other users
            await collaboration_manager.broadcast(session_id, {
                'type': 'user_action',
                'user_id': str(current_user.id),
                'action': data.get('action'),
                'data': data.get('data'),
                'timestamp': datetime.utcnow().isoformat()
            })
    except Exception:
        pass
    finally:
        await collaboration_manager.disconnect(session_id, websocket)
```

**Subtasks:**
- [ ] Set up WebSocket infrastructure
- [ ] Implement connection management
- [ ] Implement message broadcasting
- [ ] Add cursor position sharing (optional)
- [ ] Add presence indicators
- [ ] Test WebSocket connectivity
- [ ] Add reconnection logic

**Success Criteria:**
- WebSocket connections working
- Messages broadcast correctly
- Multiple users can collaborate
- Disconnections handled properly
- Tests passing

---

#### 1.5 Conflict Resolution for Concurrent Edits
**Implementation:**

```python
class EditConflictResolver:
    """Resolve conflicts from concurrent edits."""

    def resolve_spec_conflict(
        self,
        spec_id: str,
        version1: Dict,
        version2: Dict
    ) -> Dict[str, Any]:
        """Resolve specification conflicts."""
        # Use Operational Transformation or CRDT approach
        conflicts = []

        for key in version1:
            if key not in version2:
                conflicts.append({
                    'field': key,
                    'version1': version1[key],
                    'version2': None,
                    'type': 'deletion'
                })
            elif version1[key] != version2[key]:
                conflicts.append({
                    'field': key,
                    'version1': version1[key],
                    'version2': version2[key],
                    'type': 'modification'
                })

        return {
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts,
            'merge_strategy': 'manual'  # or 'auto' for simple merges
        }
```

**Subtasks:**
- [ ] Implement conflict detection
- [ ] Implement conflict resolution strategies
- [ ] Implement merge functionality
- [ ] Add version tracking
- [ ] Test conflict scenarios

**Success Criteria:**
- Conflicts detected correctly
- Resolution working
- Merge results valid
- Tests passing

---

### Task 2: Quality Metrics System (Week 2-3)
**Effort:** 40 hours | **Owner:** Developer 2

#### 2.1 Custom Quality Metrics
**Files:** `models/quality_metric.py`, `api/quality.py`

**Current Status:** Basic model exists, needs enhancement

**Implementation:**

```python
class QualityMetric(Base):
    __tablename__ = "quality_metrics"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(20))  # numeric, percentage, categorical, boolean
    value = Column(Float)
    target_value = Column(Float)
    status = Column(String(20))  # green, yellow, red
    category = Column(String(50))  # coverage, clarity, completeness, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'value': self.value,
            'target_value': self.target_value,
            'status': self.status,
            'category': self.category,
            'timestamp': self.timestamp.isoformat()
        }

# Metric definitions
class MetricDefinition:
    """Define custom metric."""
    def __init__(
        self,
        name: str,
        metric_type: str,
        formula: callable,
        target: float,
        category: str
    ):
        self.name = name
        self.metric_type = metric_type
        self.formula = formula
        self.target = target
        self.category = category

BUILT_IN_METRICS = {
    'specification_coverage': MetricDefinition(
        name='Specification Coverage',
        metric_type='percentage',
        formula=lambda specs, total: (len(specs) / total * 100) if total > 0 else 0,
        target=100,
        category='completeness'
    ),
    'specification_clarity': MetricDefinition(
        name='Specification Clarity',
        metric_type='percentage',
        formula=lambda specs: sum(s.confidence for s in specs) / len(specs) * 100 if specs else 0,
        target=85,
        category='clarity'
    ),
    'conflict_resolution': MetricDefinition(
        name='Conflict Resolution Rate',
        metric_type='percentage',
        formula=lambda total, resolved: (resolved / total * 100) if total > 0 else 100,
        target=100,
        category='quality'
    ),
}

# Endpoints
@router.post("/projects/{project_id}/metrics")
async def create_metric(
    project_id: str,
    metric: CreateMetricRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create custom quality metric."""
    quality_metric = QualityMetric(
        project_id=project_id,
        metric_name=metric.name,
        metric_type=metric.metric_type,
        target_value=metric.target,
        category=metric.category
    )
    db_specs.add(quality_metric)
    db_specs.commit()

    return {
        'success': True,
        'metric_id': str(quality_metric.id),
        'metric': quality_metric.to_dict()
    }

@router.get("/projects/{project_id}/metrics")
async def list_project_metrics(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """List quality metrics for project."""
    metrics = db_specs.query(QualityMetric).filter(
        QualityMetric.project_id == project_id
    ).all()

    return {
        'success': True,
        'metrics': [m.to_dict() for m in metrics],
        'summary': {
            'total_metrics': len(metrics),
            'green_count': sum(1 for m in metrics if m.status == 'green'),
            'yellow_count': sum(1 for m in metrics if m.status == 'yellow'),
            'red_count': sum(1 for m in metrics if m.status == 'red'),
        }
    }

@router.post("/projects/{project_id}/metrics/{metric_id}/calculate")
async def calculate_metric(
    project_id: str,
    metric_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Calculate metric value."""
    metric = db_specs.query(QualityMetric).filter(
        QualityMetric.id == metric_id
    ).first()

    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Calculate based on metric type
    if metric.metric_name == 'specification_coverage':
        specs = db_specs.query(Specification).filter(
            Specification.project_id == project_id
        ).all()
        value = len(specs)
    else:
        value = 0  # Custom calculation

    # Determine status
    if metric.target_value:
        percentage = (value / metric.target_value * 100) if metric.target_value > 0 else 100
        if percentage >= 100:
            status = 'green'
        elif percentage >= 80:
            status = 'yellow'
        else:
            status = 'red'
    else:
        status = 'yellow'

    metric.value = value
    metric.status = status
    db_specs.commit()

    return {
        'success': True,
        'value': value,
        'status': status,
        'metric': metric.to_dict()
    }
```

**Subtasks:**
- [ ] Enhance QualityMetric model
- [ ] Define built-in metrics
- [ ] Implement custom metric creation
- [ ] Implement metric calculation
- [ ] Implement metric listing
- [ ] Implement metric history tracking
- [ ] Test metric system

**Success Criteria:**
- Custom metrics can be created
- Metrics calculated correctly
- Status determined properly
- History tracked
- Tests passing

---

#### 2.2 Trend Analysis
**Implementation:**

```python
class TrendAnalyzer:
    """Analyze metric trends over time."""

    def calculate_trend(
        self,
        project_id: str,
        metric_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate trend for metric."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        metrics = db_specs.query(QualityMetric).filter(
            QualityMetric.project_id == project_id,
            QualityMetric.metric_name == metric_name,
            QualityMetric.timestamp >= cutoff_date
        ).order_by(QualityMetric.timestamp).all()

        if len(metrics) < 2:
            return {'trend': 'insufficient_data', 'values': []}

        values = [m.value for m in metrics]
        trend_direction = 'increasing' if values[-1] > values[0] else 'decreasing'
        trend_rate = (values[-1] - values[0]) / len(values)

        return {
            'metric': metric_name,
            'days': days,
            'start_value': values[0],
            'end_value': values[-1],
            'trend_direction': trend_direction,
            'trend_rate': trend_rate,
            'values': values,
            'timestamps': [m.timestamp.isoformat() for m in metrics]
        }

    def get_project_health(self, project_id: str) -> Dict[str, Any]:
        """Get overall project health."""
        metrics = db_specs.query(QualityMetric).filter(
            QualityMetric.project_id == project_id
        ).all()

        if not metrics:
            return {'health_score': 0, 'status': 'unknown'}

        health_score = sum(
            100 if m.status == 'green' else 50 if m.status == 'yellow' else 0
            for m in metrics
        ) / len(metrics)

        return {
            'health_score': health_score,
            'status': 'good' if health_score >= 80 else 'fair' if health_score >= 50 else 'poor',
            'metric_count': len(metrics),
            'metrics_by_status': {
                'green': sum(1 for m in metrics if m.status == 'green'),
                'yellow': sum(1 for m in metrics if m.status == 'yellow'),
                'red': sum(1 for m in metrics if m.status == 'red')
            }
        }
```

**Subtasks:**
- [ ] Implement trend calculation
- [ ] Implement trend direction detection
- [ ] Implement health scoring
- [ ] Add historical data points
- [ ] Test trend analysis
- [ ] Add visualization support

**Success Criteria:**
- Trends calculated correctly
- Health score meaningful
- History available
- Tests passing

---

#### 2.3 Threshold Alerts
**Implementation:**

```python
class AlertManager:
    """Manage quality metric alerts."""

    async def check_thresholds(self, project_id: str) -> List[Dict[str, Any]]:
        """Check metrics against thresholds."""
        metrics = db_specs.query(QualityMetric).filter(
            QualityMetric.project_id == project_id
        ).all()

        alerts = []
        for metric in metrics:
            if metric.status == 'red':
                alerts.append({
                    'severity': 'high',
                    'metric': metric.metric_name,
                    'message': f"{metric.metric_name} below target (target: {metric.target_value}, actual: {metric.value})",
                    'timestamp': datetime.utcnow().isoformat()
                })
            elif metric.status == 'yellow':
                alerts.append({
                    'severity': 'medium',
                    'metric': metric.metric_name,
                    'message': f"{metric.metric_name} approaching threshold",
                    'timestamp': datetime.utcnow().isoformat()
                })

        return alerts

    async def send_alert(self, user_id: str, alert: Dict[str, Any]):
        """Send alert to user (email, webhook, etc.)."""
        # Implementation in Phase 4
        pass
```

**Subtasks:**
- [ ] Implement threshold checking
- [ ] Define alert severity levels
- [ ] Implement alert creation
- [ ] Implement alert notification (Phase 4)
- [ ] Test alert system

**Success Criteria:**
- Alerts created when thresholds crossed
- Severity assigned correctly
- Notification system ready for Phase 4
- Tests passing

---

### Task 3: User Learning System (Week 3-4)
**Effort:** 40 hours | **Owner:** Developer 3

#### 3.1 Embedding Generation
**Files:** `agents/user_learning.py`

**Current Issue:**
```python
# TODO: Generate embedding using sentence transformer
embedding=None
```

**Implementation:**

```python
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """Generate embeddings for questions and answers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def generate_batch_embeddings(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return [e.tolist() for e in embeddings]

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        embeddings = self.model.encode([text1, text2])
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)

# Usage in Question model
class Question(Base):
    # ... existing fields ...
    embedding = Column(ARRAY(Float))  # Store embedding vector

    def generate_embedding(self, generator: EmbeddingGenerator):
        """Generate and store embedding."""
        self.embedding = generator.generate_embedding(self.question_text)

# Store embeddings
@router.post("/projects/{project_id}/questions/{question_id}/embed")
async def generate_question_embedding(
    project_id: str,
    question_id: str,
    current_user: User = Depends(get_current_active_user),
    services: ServiceContainer = Depends(get_services)
):
    """Generate embedding for question."""
    question = db_specs.query(Question).filter(
        Question.id == question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    generator = services.get_embedding_generator()
    question.generate_embedding(generator)
    db_specs.commit()

    return {
        'success': True,
        'question_id': str(question.id),
        'embedding_generated': True
    }
```

**Dependencies to add:**
```
sentence-transformers>=2.3.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

**Subtasks:**
- [ ] Install sentence-transformers
- [ ] Implement embedding generation
- [ ] Add embedding field to Question model
- [ ] Implement batch embedding
- [ ] Implement similarity calculation
- [ ] Store embeddings in database
- [ ] Test embedding generation

**Success Criteria:**
- Embeddings generated correctly
- Stored in database
- Similarity calculation working
- Performance acceptable
- Tests passing

---

#### 3.2 Pattern Recognition
**Files:** `agents/user_learning.py`

**Implementation:**

```python
class PatternRecognizer:
    """Recognize user behavior patterns."""

    def analyze_user_patterns(
        self, user_id: str
    ) -> Dict[str, Any]:
        """Analyze user's question-answer patterns."""
        # Get user's Q&A history
        questions = db_specs.query(Question).filter(
            Question.user_id == user_id
        ).all()

        patterns = {
            'preferred_topics': self._find_preferred_topics(questions),
            'question_style': self._analyze_question_style(questions),
            'response_patterns': self._analyze_response_patterns(questions),
            'learning_pace': self._calculate_learning_pace(user_id),
            'confidence_trend': self._analyze_confidence_trend(questions)
        }

        return patterns

    def _find_preferred_topics(self, questions: List[Question]) -> Dict[str, int]:
        """Find topics user asks about most."""
        topics = {}
        for q in questions:
            topic = q.category or 'general'
            topics[topic] = topics.get(topic, 0) + 1
        return dict(sorted(topics.items(), key=lambda x: x[1], reverse=True))

    def _analyze_question_style(self, questions: List[Question]) -> Dict[str, Any]:
        """Analyze user's questioning style."""
        if not questions:
            return {}

        avg_length = sum(len(q.question_text) for q in questions) / len(questions)
        avg_complexity = sum(len(q.question_text.split()) for q in questions) / len(questions)

        return {
            'avg_question_length': avg_length,
            'avg_question_complexity': avg_complexity,
            'total_questions': len(questions)
        }

    def _analyze_response_patterns(self, questions: List[Question]) -> Dict[str, Any]:
        """Analyze patterns in user responses."""
        answers = [q for q in questions if q.answer]
        if not answers:
            return {}

        avg_answer_length = sum(len(a.answer) for a in answers) / len(answers)
        return {
            'total_answers': len(answers),
            'avg_answer_length': avg_answer_length,
            'detailed_answers': len([a for a in answers if len(a.answer) > 200])
        }

    def _calculate_learning_pace(self, user_id: str) -> Dict[str, Any]:
        """Calculate how fast user is learning."""
        # Get sessions
        sessions = db_specs.query(Session).filter(
            Session.user_id == user_id
        ).order_by(Session.created_at).all()

        if len(sessions) < 2:
            return {'sessions': len(sessions), 'pace': 'insufficient_data'}

        # Calculate specs per session
        specs_per_session = []
        for session in sessions:
            count = db_specs.query(Specification).filter(
                Specification.session_id == session.id
            ).count()
            specs_per_session.append(count)

        avg_specs = sum(specs_per_session) / len(specs_per_session)
        return {
            'sessions': len(sessions),
            'avg_specs_per_session': avg_specs,
            'pace': 'fast' if avg_specs > 10 else 'medium' if avg_specs > 5 else 'slow'
        }
```

**Subtasks:**
- [ ] Implement topic preference analysis
- [ ] Implement question style analysis
- [ ] Implement response pattern analysis
- [ ] Implement learning pace calculation
- [ ] Store patterns in database
- [ ] Test pattern recognition
- [ ] Validate accuracy

**Success Criteria:**
- Patterns identified correctly
- Stored in UserBehaviorPattern
- Analysis accurate and useful
- Tests passing

---

#### 3.3 Adaptive Questioning
**Implementation:**

```python
class AdaptiveQuestioningEngine:
    """Generate adaptive questions based on user learning."""

    def generate_adaptive_question(
        self,
        user_id: str,
        project_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Generate question adapted to user."""
        # Get user patterns
        patterns = PatternRecognizer().analyze_user_patterns(user_id)

        # Get existing coverage
        coverage = self._calculate_coverage(project_id)

        # Determine best next topic
        next_topic = self._select_best_topic(patterns, coverage)

        # Generate question
        prompt = self._build_adaptive_prompt(
            project_id,
            next_topic,
            patterns,
            coverage
        )

        # Use LLM to generate
        llm = services.get_llm_provider()
        question_text = llm.generate_text(prompt)

        return {
            'question_text': question_text,
            'topic': next_topic,
            'difficulty': self._estimate_difficulty(patterns),
            'adaptive': True
        }

    def _select_best_topic(
        self,
        patterns: Dict,
        coverage: Dict
    ) -> str:
        """Select topic to ask about."""
        # Prefer underexplored topics
        preferred = patterns.get('preferred_topics', {})
        uncovered = [t for t, cov in coverage.items() if cov < 0.5]

        if uncovered:
            # Ask about uncovered but preferred topic if possible
            for topic in uncovered:
                if topic in preferred:
                    return topic
            return uncovered[0]

        return list(preferred.keys())[0] if preferred else 'general'

    def _estimate_difficulty(self, patterns: Dict) -> str:
        """Estimate appropriate difficulty level."""
        pace = patterns.get('learning_pace', {}).get('pace', 'medium')
        return 'advanced' if pace == 'fast' else 'intermediate' if pace == 'medium' else 'basic'
```

**Subtasks:**
- [ ] Implement topic selection logic
- [ ] Implement difficulty estimation
- [ ] Implement adaptive prompt building
- [ ] Integrate with LLM
- [ ] Test adaptive questions
- [ ] Validate user feedback

**Success Criteria:**
- Questions adapted to user
- Topics selected intelligently
- Difficulty appropriate
- User satisfaction improves
- Tests passing

---

### Task 4: Analytics Dashboard (Week 4)
**Effort:** 25 hours | **Owner:** Developer 2 (parallel with metrics)

#### 4.1 Analytics Data Collection
**Implementation:**

```python
class AnalyticsCollector:
    """Collect analytics data."""

    def track_event(
        self,
        user_id: str,
        event_type: str,
        metadata: Dict[str, Any] = None
    ):
        """Track user event."""
        event = {
            'user_id': user_id,
            'event_type': event_type,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }

        # Store in analytics database or log
        logger.info(f"Event: {event_type}", extra=event)

    def track_project_usage(self, user_id: str, project_id: str):
        """Track project access."""
        self.track_event(user_id, 'project_accessed', {
            'project_id': project_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    def track_session_completion(
        self,
        user_id: str,
        session_id: str,
        specs_count: int,
        duration_minutes: int
    ):
        """Track session completion."""
        self.track_event(user_id, 'session_completed', {
            'session_id': session_id,
            'specs_extracted': specs_count,
            'duration_minutes': duration_minutes
        })
```

**Subtasks:**
- [ ] Implement event tracking
- [ ] Add tracking calls to endpoints
- [ ] Store analytics data
- [ ] Test event collection

**Success Criteria:**
- Events tracked correctly
- Data stored properly
- Performance not impacted
- Tests passing

---

#### 4.2 Analytics Endpoints
**Endpoints:**
- `GET /api/v1/analytics/user` - User statistics
- `GET /api/v1/analytics/projects` - Project statistics
- `GET /api/v1/analytics/timeline` - Usage timeline

**Subtasks:**
- [ ] Implement user stats endpoint
- [ ] Implement project stats endpoint
- [ ] Implement timeline endpoint
- [ ] Test analytics endpoints

**Success Criteria:**
- All endpoints working
- Data aggregated correctly
- Performance acceptable
- Tests passing

---

### Task 5: Admin Panel Backend (Week 4-5)
**Effort:** 30 hours | **Owner:** Developer 3 (parallel with learning)

#### 5.1 Admin Endpoints
**Files:** `api/admin.py`

**Implementation:**

```python
@router.get("/admin/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """List all users (admin only)."""
    users = db_auth.query(User).offset(skip).limit(limit).all()
    total = db_auth.query(User).count()

    return {
        'success': True,
        'users': [u.to_dict() for u in users],
        'total': total,
        'skip': skip,
        'limit': limit
    }

@router.get("/admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get user details (admin only)."""
    user = db_auth.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user stats
    project_count = db_specs.query(Project).filter(
        Project.user_id == user_id
    ).count()

    session_count = db_specs.query(Session).filter(
        Session.user_id == user_id
    ).count()

    spec_count = db_specs.query(Specification).filter(
        Specification.user_id == user_id
    ).count()

    return {
        'success': True,
        'user': user.to_dict(),
        'stats': {
            'projects': project_count,
            'sessions': session_count,
            'specifications': spec_count
        }
    }

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete user and related data (admin only)."""
    user = db_auth.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cascade delete (or soft delete)
    db_auth.delete(user)
    db_auth.commit()

    return {'success': True, 'message': 'User deleted'}

@router.get("/admin/system")
async def system_stats(
    current_user: User = Depends(get_current_admin_user)
):
    """Get system statistics."""
    return {
        'success': True,
        'stats': {
            'total_users': db_auth.query(User).count(),
            'total_projects': db_specs.query(Project).count(),
            'total_sessions': db_specs.query(Session).count(),
            'total_specifications': db_specs.query(Specification).count(),
            'total_conflicts': db_specs.query(Conflict).count(),
        },
        'database': {
            'auth_connection': 'ok',
            'specs_connection': 'ok'
        }
    }

@router.get("/admin/logs")
async def system_logs(
    level: str = 'error',
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """Get system logs (admin only)."""
    # Implementation depends on logging setup
    # Could use ElasticSearch, file logs, or database
    return {
        'success': True,
        'logs': [],
        'level': level
    }
```

**Subtasks:**
- [ ] Implement user listing
- [ ] Implement user details
- [ ] Implement user deletion
- [ ] Implement system stats
- [ ] Implement logging view
- [ ] Add admin permission checking
- [ ] Test admin endpoints

**Success Criteria:**
- All admin endpoints working
- Data aggregated correctly
- Permissions enforced
- Tests passing

---

## Phase Deliverables

### Code Changes
- [ ] Team collaboration fully implemented
- [ ] Quality metrics system with trends
- [ ] User learning with embeddings
- [ ] Analytics data collection
- [ ] Admin panel backend

### Tests
- [ ] 100+ new unit tests
- [ ] Integration tests for all features
- [ ] Real-time collaboration tests
- [ ] Analytics tests
- [ ] 85%+ code coverage

### Documentation
- [ ] Team collaboration guide
- [ ] Quality metrics documentation
- [ ] Analytics guide
- [ ] Admin panel documentation
- [ ] Permission system documentation

### Dependencies to Add
```
sentence-transformers>=2.3.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

---

## Success Criteria

### Must Have
- ✅ Team management working
- ✅ Project sharing functional
- ✅ Quality metrics system
- ✅ Admin panel with user management

### Should Have
- ✅ Real-time collaboration (WebSocket)
- ✅ User learning system
- ✅ Analytics collection
- ✅ Trend analysis

### Nice to Have
- ✅ Advanced permissions
- ✅ Alert system
- ✅ Admin dashboard UI (Phase 4)

---

## Timeline

| Week | Task | Status |
|------|------|--------|
| 1-2 | Team collaboration | 🔄 |
| 2-3 | Quality metrics | 🔄 |
| 3-4 | User learning | 🔄 |
| 4 | Analytics backend | 🔄 |
| 4-5 | Admin panel | 🔄 |

---

## Notes for Next Phase

- Phase 3 builds sophisticated features
- User learning requires careful testing
- Real-time collaboration needs load testing
- Analytics foundation for Phase 4 dashboard
- Admin panel UI can be web-based (Phase 4)

---

**End of IMPLEMENTATION_PHASE_3.md**
