# Phase 8: Team Collaboration

**Status:** ⏳ PENDING
**Duration:** 3-4 days
**Goal:** Enable multi-user projects with role-based questions and team conflict resolution

---

## ⚠️ CRITICAL: Read Before Implementation

**MANDATORY:** Review [CRITICAL_LESSONS_LEARNED.md](../CRITICAL_LESSONS_LEARNED.md) before starting Phase 8.

**Critical Checklist for Phase 8:**

### Models (teams, team_members, project_shares):
- [ ] Inherits from BaseModel? → Include id, created_at, updated_at in migration
- [ ] AVOID column names: metadata, query, session
- [ ] Use team_metadata NOT just "metadata" (if storing metadata)
- [ ] Use share_metadata NOT just "metadata" (if storing metadata)

### Migrations (Phase 8 migrations):
- [ ] **TWO DATABASES**: teams, team_members go to `socrates_auth`
- [ ] **TWO DATABASES**: project_shares goes to `socrates_specs`
- [ ] Add `import os` and `_should_run()` function for EACH migration
- [ ] Check DATABASE_URL contains "socrates_auth" OR "socrates_specs" (depends on table)
- [ ] Add check to BOTH upgrade() and downgrade()
- [ ] Verify BaseModel columns if model inherits

### Tests (test_phase_8_team_collaboration.py):
- [ ] Use `auth_session` NOT `db_auth` (for teams, team_members)
- [ ] Use `specs_session` NOT `db_specs` (for project_shares)
- [ ] Use `mock_claude_client` fixture, NOT @patch decorators
- [ ] DO NOT patch instance attributes

### TeamCollaborationAgent:
- [ ] Accept ServiceContainer in __init__
- [ ] Store as self.services (instance attribute)
- [ ] Get auth database via self.services.get_database_auth() (for teams)
- [ ] Get specs database via self.services.get_database_specs() (for project_shares)
- [ ] Get Claude client via self.services.get_claude_client()

**Database:** Phase 8 uses BOTH databases:
- `socrates_auth`: teams, team_members
- `socrates_specs`: project_shares

---

## 📋 Objectives

1. Create TeamCollaborationAgent
2. Implement team creation and membership management
3. Enable multi-user project collaboration
4. Implement role-based question selection
5. Detect and resolve team-level conflicts (different team members disagree)
6. Implement project sharing and permissions
7. Track team activity and contributions

---

## 🔗 Dependencies

**From Phase 1:**
- User authentication system
- Project management

**From Phase 2:**
- Socratic questioning system
- Specification extraction

**From Phase 3:**
- Conflict detection (enhanced for team conflicts)

**From Phase 6:**
- User learning (per-user profiles)

**Provides To Phase 9:**
- Multi-user foundation for advanced features
- Team activity tracking for analytics

---

## 🌐 API Endpoints

This phase implements team collaboration features. See [API_ENDPOINTS.md](../foundation_docs/API_ENDPOINTS.md) for complete API documentation.

**Implemented in Phase 8:**
- POST /api/v1/teams - Create team
- GET /api/v1/teams - List user's teams
- GET /api/v1/teams/{id} - Get team details
- POST /api/v1/teams/{id}/members - Invite team member
- DELETE /api/v1/teams/{id}/members/{user_id} - Remove team member
- POST /api/v1/teams/{id}/projects - Create team project
- GET /api/v1/teams/{id}/projects - List team projects
- POST /api/v1/projects/{id}/share - Share project with team
- GET /api/v1/projects/{id}/activity - Get project activity (all team members)

**Testing Endpoints:**
```bash
# Create team
curl -X POST http://localhost:8000/api/v1/teams \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering Team", "description": "Our dev team"}'

# Invite team member
curl -X POST http://localhost:8000/api/v1/teams/{team_id}/members \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<user_id>", "role": "developer"}'

# Create team project
curl -X POST http://localhost:8000/api/v1/teams/{team_id}/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Team Project", "description": "Collaborative project"}'
```

---

## 📦 Key Component: TeamCollaborationAgent

```python
class TeamCollaborationAgent(BaseAgent):
    """Manage team collaboration and multi-user projects"""

    def get_capabilities(self):
        return [
            'create_team',
            'add_team_member',
            'remove_team_member',
            'get_team_details',
            'create_team_project',
            'share_project',
            'get_team_activity',
            'detect_team_conflicts',
            'assign_role_based_questions'
        ]

    def _create_team(self, data):
        """Create a new team

        Args:
            data: {
                'name': str,
                'description': str,
                'created_by': UUID
            }

        Returns:
            {'success': bool, 'team_id': UUID}
        """
        # Create team
        team = Team(
            name=data['name'],
            description=data.get('description', ''),
            created_by=data['created_by'],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.db.add(team)
        self.db.flush()

        # Add creator as owner
        owner_member = TeamMember(
            team_id=team.id,
            user_id=data['created_by'],
            role='owner',
            joined_at=datetime.now(timezone.utc)
        )
        self.db.add(owner_member)

        self.db.commit()

        self.logger.info(f"Team created: {team.name} (ID: {team.id})")

        return {
            'success': True,
            'team_id': team.id,
            'name': team.name
        }

    def _add_team_member(self, data):
        """Add member to team

        Args:
            data: {
                'team_id': UUID,
                'user_id': UUID,
                'role': str ('owner', 'lead', 'developer', 'viewer'),
                'invited_by': UUID
            }

        Returns:
            {'success': bool, 'member_id': UUID}
        """
        team_id = data['team_id']
        user_id = data['user_id']
        role = data['role']
        invited_by = data['invited_by']

        # Verify inviter has permission (must be owner or lead)
        inviter_member = self.db.query(TeamMember).filter_by(
            team_id=team_id,
            user_id=invited_by
        ).first()

        if not inviter_member or inviter_member.role not in ['owner', 'lead']:
            return {
                'success': False,
                'error': 'Permission denied: Only owners and leads can invite members'
            }

        # Check if user is already a member
        existing = self.db.query(TeamMember).filter_by(
            team_id=team_id,
            user_id=user_id
        ).first()

        if existing:
            return {
                'success': False,
                'error': 'User is already a team member'
            }

        # Add team member
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.now(timezone.utc)
        )
        self.db.add(member)
        self.db.commit()

        self.logger.info(
            f"User {user_id} added to team {team_id} as {role}"
        )

        return {
            'success': True,
            'member_id': member.id,
            'role': role
        }

    def _remove_team_member(self, data):
        """Remove member from team

        Args:
            data: {
                'team_id': UUID,
                'user_id': UUID (member to remove),
                'removed_by': UUID
            }

        Returns:
            {'success': bool}
        """
        team_id = data['team_id']
        user_id = data['user_id']
        removed_by = data['removed_by']

        # Verify remover has permission (must be owner)
        remover_member = self.db.query(TeamMember).filter_by(
            team_id=team_id,
            user_id=removed_by
        ).first()

        if not remover_member or remover_member.role != 'owner':
            return {
                'success': False,
                'error': 'Permission denied: Only owners can remove members'
            }

        # Find member to remove
        member = self.db.query(TeamMember).filter_by(
            team_id=team_id,
            user_id=user_id
        ).first()

        if not member:
            return {
                'success': False,
                'error': 'User is not a team member'
            }

        # Cannot remove last owner
        if member.role == 'owner':
            owner_count = self.db.query(TeamMember).filter_by(
                team_id=team_id,
                role='owner'
            ).count()
            if owner_count <= 1:
                return {
                    'success': False,
                    'error': 'Cannot remove last owner'
                }

        # Remove member
        self.db.delete(member)
        self.db.commit()

        self.logger.info(f"User {user_id} removed from team {team_id}")

        return {
            'success': True,
            'removed_user_id': user_id
        }

    def _create_team_project(self, data):
        """Create project owned by team

        Args:
            data: {
                'team_id': UUID,
                'name': str,
                'description': str,
                'created_by': UUID
            }

        Returns:
            {'success': bool, 'project_id': UUID}
        """
        # Verify user is team member
        member = self.db.query(TeamMember).filter_by(
            team_id=data['team_id'],
            user_id=data['created_by']
        ).first()

        if not member:
            return {
                'success': False,
                'error': 'User is not a team member'
            }

        # Create project (use ProjectManagerAgent)
        project_result = self.orchestrator.route_request(
            'project',
            'create_project',
            {
                'name': data['name'],
                'description': data.get('description', ''),
                'user_id': data['created_by']
            }
        )

        if not project_result['success']:
            return project_result

        project_id = project_result['project_id']

        # Create project share record
        share = ProjectShare(
            project_id=project_id,
            team_id=data['team_id'],
            shared_by=data['created_by'],
            shared_at=datetime.now(timezone.utc),
            permissions='edit'  # Team members can edit
        )
        self.db.add(share)
        self.db.commit()

        self.logger.info(
            f"Team project created: {data['name']} (ID: {project_id})"
        )

        return {
            'success': True,
            'project_id': project_id,
            'team_id': data['team_id']
        }

    def _share_project(self, data):
        """Share existing project with team

        Args:
            data: {
                'project_id': UUID,
                'team_id': UUID,
                'shared_by': UUID,
                'permissions': str ('view' | 'edit')
            }

        Returns:
            {'success': bool, 'share_id': UUID}
        """
        project_id = data['project_id']
        team_id = data['team_id']
        shared_by = data['shared_by']

        # Verify project ownership
        project = self.db.query(Project).get(project_id)
        if project.owner_id != shared_by:
            return {
                'success': False,
                'error': 'Only project owner can share'
            }

        # Check if already shared
        existing = self.db.query(ProjectShare).filter_by(
            project_id=project_id,
            team_id=team_id
        ).first()

        if existing:
            return {
                'success': False,
                'error': 'Project already shared with this team'
            }

        # Create share
        share = ProjectShare(
            project_id=project_id,
            team_id=team_id,
            shared_by=shared_by,
            shared_at=datetime.now(timezone.utc),
            permissions=data.get('permissions', 'view')
        )
        self.db.add(share)
        self.db.commit()

        return {
            'success': True,
            'share_id': share.id
        }

    def _get_team_activity(self, data):
        """Get all team activity for a project

        Args:
            data: {'project_id': UUID}

        Returns:
            {
                'success': bool,
                'activity': List[dict],
                'team_members': List[dict],
                'contribution_stats': dict
            }
        """
        project_id = data['project_id']

        # Get project share to find team
        share = self.db.query(ProjectShare).filter_by(
            project_id=project_id
        ).first()

        if not share:
            return {
                'success': False,
                'error': 'Project not shared with any team'
            }

        # Get all team members
        team_members = self.db.query(TeamMember).filter_by(
            team_id=share.team_id
        ).all()

        # Get all interactions for this project by team members
        member_ids = [m.user_id for m in team_members]
        interactions = self.db.query(Interaction).filter(
            Interaction.project_id == project_id,
            Interaction.user_id.in_(member_ids)
        ).order_by(Interaction.timestamp.desc()).all()

        # Calculate contribution stats
        contribution_stats = {}
        for member in team_members:
            user_interactions = [
                i for i in interactions if i.user_id == member.user_id
            ]
            contribution_stats[str(member.user_id)] = {
                'username': self._get_username(member.user_id),
                'role': member.role,
                'interactions': len(user_interactions),
                'specs_contributed': self._count_specs_by_user(
                    project_id, member.user_id
                )
            }

        return {
            'success': True,
            'activity': [
                {
                    'user_id': i.user_id,
                    'username': self._get_username(i.user_id),
                    'action': i.action,
                    'timestamp': i.timestamp,
                    'details': i.details
                }
                for i in interactions
            ],
            'team_members': [
                {
                    'user_id': m.user_id,
                    'username': self._get_username(m.user_id),
                    'role': m.role,
                    'joined_at': m.joined_at
                }
                for m in team_members
            ],
            'contribution_stats': contribution_stats
        }

    def _detect_team_conflicts(self, data):
        """Detect conflicts between team members' specifications

        Args:
            data: {'project_id': UUID}

        Returns:
            {
                'success': bool,
                'team_conflicts': List[dict]
            }
        """
        project_id = data['project_id']

        # Get all specifications for this project
        specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Group specs by user (who created them)
        specs_by_user = {}
        for spec in specs:
            # Get user_id from interaction that created this spec
            interaction = self.db.query(Interaction).filter_by(
                project_id=project_id,
                action='extract_specification',
                details={'spec_id': str(spec.id)}
            ).first()

            if interaction:
                user_id = interaction.user_id
                if user_id not in specs_by_user:
                    specs_by_user[user_id] = []
                specs_by_user[user_id].append(spec)

        # Detect conflicts between users
        team_conflicts = []
        users = list(specs_by_user.keys())

        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                user1_id = users[i]
                user2_id = users[j]
                user1_specs = specs_by_user[user1_id]
                user2_specs = specs_by_user[user2_id]

                # Compare specs
                for spec1 in user1_specs:
                    for spec2 in user2_specs:
                        # Same category + key but different values = conflict
                        if (spec1.category == spec2.category and
                            spec1.key == spec2.key and
                            spec1.value != spec2.value):

                            team_conflicts.append({
                                'type': 'team_disagreement',
                                'user1_id': user1_id,
                                'user1_username': self._get_username(user1_id),
                                'user2_id': user2_id,
                                'user2_username': self._get_username(user2_id),
                                'category': spec1.category,
                                'key': spec1.key,
                                'user1_value': spec1.value,
                                'user2_value': spec2.value,
                                'description': (
                                    f"{self._get_username(user1_id)} says "
                                    f"\"{spec1.value}\" but "
                                    f"{self._get_username(user2_id)} says "
                                    f"\"{spec2.value}\""
                                )
                            })

        return {
            'success': True,
            'team_conflicts': team_conflicts,
            'conflict_count': len(team_conflicts)
        }

    def _assign_role_based_questions(self, data):
        """Assign questions based on team member's role

        Args:
            data: {
                'user_id': UUID,
                'project_id': UUID,
                'team_id': UUID
            }

        Returns:
            {
                'success': bool,
                'assigned_questions': List[dict],
                'role': str
            }
        """
        user_id = data['user_id']
        team_id = data['team_id']

        # Get user's role in team
        member = self.db.query(TeamMember).filter_by(
            team_id=team_id,
            user_id=user_id
        ).first()

        if not member:
            return {
                'success': False,
                'error': 'User is not a team member'
            }

        # Role-based question assignment
        role_question_mapping = {
            'owner': ['goals', 'requirements', 'timeline', 'constraints'],
            'lead': ['requirements', 'tech_stack', 'scalability', 'deployment'],
            'developer': ['tech_stack', 'testing', 'deployment'],
            'viewer': []  # Viewers cannot answer questions
        }

        assigned_categories = role_question_mapping.get(member.role, [])

        # Get questions for these categories
        questions = self.db.query(Question).filter(
            Question.category.in_(assigned_categories)
        ).all()

        return {
            'success': True,
            'role': member.role,
            'assigned_categories': assigned_categories,
            'assigned_questions': [
                {
                    'question_id': q.id,
                    'text': q.text,
                    'category': q.category
                }
                for q in questions
            ]
        }

    def _get_username(self, user_id):
        """Get username for user_id"""
        # Query from socrates_auth database
        user = self.db_auth.query(User).get(user_id)
        return user.username if user else f"User {user_id}"

    def _count_specs_by_user(self, project_id, user_id):
        """Count specifications contributed by user"""
        interactions = self.db.query(Interaction).filter_by(
            project_id=project_id,
            user_id=user_id,
            action='extract_specification'
        ).count()
        return interactions
```

---

## 🧪 Critical Tests

```python
def test_create_team():
    """Test creating a team"""
    result = team_agent.process_request(
        'create_team',
        {
            'name': 'Engineering Team',
            'description': 'Our dev team',
            'created_by': user1.id
        }
    )
    assert result['success'] == True
    assert result['team_id'] is not None

    # Verify creator is owner
    member = db.query(TeamMember).filter_by(
        team_id=result['team_id'],
        user_id=user1.id
    ).first()
    assert member.role == 'owner'

def test_add_team_member():
    """Test adding member to team"""
    team = Team(name='Test Team', created_by=owner.id)
    db.add(team)
    owner_member = TeamMember(team_id=team.id, user_id=owner.id, role='owner')
    db.add(owner_member)
    db.commit()

    result = team_agent.process_request(
        'add_team_member',
        {
            'team_id': team.id,
            'user_id': developer.id,
            'role': 'developer',
            'invited_by': owner.id
        }
    )
    assert result['success'] == True

def test_non_owner_cannot_invite():
    """Test that non-owners cannot invite members"""
    team = Team(name='Test Team', created_by=owner.id)
    db.add(team)
    owner_member = TeamMember(team_id=team.id, user_id=owner.id, role='owner')
    developer_member = TeamMember(team_id=team.id, user_id=developer.id, role='developer')
    db.add_all([owner_member, developer_member])
    db.commit()

    result = team_agent.process_request(
        'add_team_member',
        {
            'team_id': team.id,
            'user_id': user3.id,
            'role': 'viewer',
            'invited_by': developer.id  # Developer trying to invite
        }
    )
    assert result['success'] == False
    assert 'Permission denied' in result['error']

def test_create_team_project():
    """Test creating project owned by team"""
    team = Team(name='Test Team', created_by=owner.id)
    db.add(team)
    member = TeamMember(team_id=team.id, user_id=owner.id, role='owner')
    db.add(member)
    db.commit()

    result = team_agent.process_request(
        'create_team_project',
        {
            'team_id': team.id,
            'name': 'Team Project',
            'description': 'Collaborative project',
            'created_by': owner.id
        }
    )
    assert result['success'] == True
    assert result['project_id'] is not None

    # Verify project is shared with team
    share = db.query(ProjectShare).filter_by(
        project_id=result['project_id'],
        team_id=team.id
    ).first()
    assert share is not None

def test_detect_team_conflicts():
    """Test detecting conflicts between team members"""
    # User 1 says: database = MySQL
    spec1 = Specification(
        project_id=project.id,
        category='tech_stack',
        key='database',
        value='MySQL',
        source='socratic_question'
    )
    interaction1 = Interaction(
        project_id=project.id,
        user_id=user1.id,
        action='extract_specification',
        details={'spec_id': str(spec1.id)}
    )

    # User 2 says: database = PostgreSQL
    spec2 = Specification(
        project_id=project.id,
        category='tech_stack',
        key='database',
        value='PostgreSQL',
        source='socratic_question'
    )
    interaction2 = Interaction(
        project_id=project.id,
        user_id=user2.id,
        action='extract_specification',
        details={'spec_id': str(spec2.id)}
    )

    db.add_all([spec1, spec2, interaction1, interaction2])
    db.commit()

    result = team_agent.process_request(
        'detect_team_conflicts',
        {'project_id': project.id}
    )

    assert result['success'] == True
    assert result['conflict_count'] == 1
    assert result['team_conflicts'][0]['type'] == 'team_disagreement'
```

---

## 🗄️ Database Tables Used

**From DATABASE_SCHEMA_COMPLETE.md (Phase 6 tables):**

### socrates_auth Database

**teams:**
- Stores team information
- Fields: name, description, created_by, created_at

**team_members:**
- Stores team membership
- Fields: team_id, user_id, role (owner/lead/developer/viewer), joined_at

**team_invitations:**
- Stores pending team invitations
- Fields: team_id, invited_user_id, invited_by, status

### socrates_specs Database

**project_shares:**
- Stores project sharing with teams
- Fields: project_id, team_id, shared_by, permissions, shared_at

---

## ✅ Verification

- [ ] TeamCollaborationAgent created
- [ ] Team creation works
- [ ] Team member management works (add/remove)
- [ ] Role-based permissions work (owner > lead > developer > viewer)
- [ ] Team project creation works
- [ ] Project sharing works
- [ ] Team activity tracking works
- [ ] Team conflict detection works
- [ ] Role-based question assignment works
- [ ] Tests pass: `pytest tests/test_phase_8_team_collaboration.py`

---

## 📊 Success Metrics

**Phase 8 succeeds when:**
1. Multiple team members can collaborate on same project
2. Each member sees questions appropriate for their role
3. Team conflicts are detected (e.g., PM wants feature X, Tech Lead says impossible)
4. Team activity is transparent (who contributed what)
5. Permissions work correctly (viewers can't edit, etc.)

**Example Success Case:**
- Team of 4: 1 Owner, 1 Tech Lead, 2 Developers
- Owner creates team project
- Owner gets business/timeline questions
- Tech Lead gets architecture/scalability questions
- Developers get implementation/testing questions
- Tech Lead says "Use microservices", Owner says "Must be monolith" → Team conflict detected
- Team discusses and resolves conflict
- All contributions tracked and visible

---

**Previous:** [PHASE_7.md](PHASE_7.md)
**Next:** [PHASE_9.md](PHASE_9.md) - Advanced Features
