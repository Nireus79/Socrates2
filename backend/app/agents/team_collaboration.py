"""
TeamCollaborationAgent - Manages team collaboration and multi-user projects.

Optimizations (Week 3):
- Uses selectinload() for eager loading to prevent N+1 query patterns
- Eliminates unnecessary database round-trips when accessing relationships
"""
from typing import Any, Dict, List

from sqlalchemy.orm import selectinload

from ..core.dependencies import ServiceContainer
from ..models.project import Project
from ..models.project_share import ProjectShare
from ..models.team import Team
from ..models.team_member import TeamMember
from .base import BaseAgent


class TeamCollaborationAgent(BaseAgent):
    """
    TeamCollaborationAgent - Manages team collaboration features.

    Capabilities:
    - create_team: Create new team
    - add_team_member: Add member to team
    - remove_team_member: Remove member from team
    - get_team_details: Get team info with members
    - create_team_project: Create project owned by team
    - share_project: Share existing project with team
    - get_team_activity: Get team activity summary
    - detect_team_conflicts: Detect specification conflicts between team members
    - assign_role_based_questions: Assign questions based on team role
    """

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        """Initialize TeamCollaborationAgent"""
        super().__init__(agent_id, name, services)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
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

    def _create_team(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new team.

        Args:
            data: {
                'name': str,
                'description': str (optional),
                'created_by': UUID
            }

        Returns:
            {'success': bool, 'team_id': UUID}
        """
        name = data.get('name')
        description = data.get('description', '')
        created_by = data.get('created_by')

        # Validate
        if not name or not created_by:
            self.logger.warning("Validation error: missing name or created_by")
            return {
                'success': False,
                'error': 'name and created_by are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db_auth = None

        try:
            # Get auth database (teams table is in socrates_auth)
            db_auth = self.services.get_database_auth()

            # Create team
            team = Team(
                name=name,
                description=description,
                created_by=created_by
            )
            db_auth.add(team)
            db_auth.flush()

            # Add creator as owner
            owner_member = TeamMember(
                team_id=team.id,
                user_id=created_by,
                role='owner'
            )
            db_auth.add(owner_member)
            db_auth.commit()

            self.logger.info(f"Team created: {team.name} (ID: {team.id})")

            return {
                'success': True,
                'team_id': str(team.id),
                'name': team.name
            }

        except Exception as e:
            self.logger.error(f"Error creating team: {e}", exc_info=True)
            if db_auth:
                db_auth.rollback()
            return {
                'success': False,
                'error': f'Failed to create team: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db_auth:
                db_auth.close()

    def _add_team_member(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add member to team.

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
        team_id = data.get('team_id')
        user_id = data.get('user_id')
        role = data.get('role')
        invited_by = data.get('invited_by')

        # Validate
        if not all([team_id, user_id, role, invited_by]):
            self.logger.warning("Validation error: missing required fields for add_team_member")
            return {
                'success': False,
                'error': 'team_id, user_id, role, and invited_by are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db_auth = None

        try:
            # Get auth database
            db_auth = self.services.get_database_auth()

            # Verify inviter has permission (must be owner or lead)
            inviter_member = db_auth.query(TeamMember).filter_by(
                team_id=team_id,
                user_id=invited_by
            ).first()

            if not inviter_member or inviter_member.role not in ['owner', 'lead']:
                self.logger.warning(f"Permission denied: User {invited_by} cannot invite to team {team_id}")
                return {
                    'success': False,
                    'error': 'Permission denied: Only owners and leads can invite members',
                    'error_code': 'PERMISSION_DENIED'
                }

            # Check if user is already a member
            existing = db_auth.query(TeamMember).filter_by(
                team_id=team_id,
                user_id=user_id
            ).first()

            if existing:
                self.logger.warning(f"User {user_id} is already a member of team {team_id}")
                return {
                    'success': False,
                    'error': 'User is already a team member',
                    'error_code': 'ALREADY_EXISTS'
                }

            # Add team member
            member = TeamMember(
                team_id=team_id,
                user_id=user_id,
                role=role
            )
            db_auth.add(member)
            db_auth.commit()

            self.logger.info(f"User {user_id} added to team {team_id} as {role}")

            return {
                'success': True,
                'member_id': str(member.id),
                'role': role
            }

        except Exception as e:
            self.logger.error(f"Error adding member to team {team_id}: {e}", exc_info=True)
            if db_auth:
                db_auth.rollback()
            return {
                'success': False,
                'error': f'Failed to add team member: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db_auth:
                db_auth.close()

    def _remove_team_member(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove member from team.

        Args:
            data: {
                'team_id': UUID,
                'user_id': UUID (member to remove),
                'removed_by': UUID
            }

        Returns:
            {'success': bool}
        """
        team_id = data.get('team_id')
        user_id = data.get('user_id')
        removed_by = data.get('removed_by')

        # Validate
        if not all([team_id, user_id, removed_by]):
            self.logger.warning("Validation error: missing required fields for remove_team_member")
            return {
                'success': False,
                'error': 'team_id, user_id, and removed_by are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db_auth = None

        try:
            # Get auth database
            db_auth = self.services.get_database_auth()

            # Verify remover has permission (must be owner)
            remover_member = db_auth.query(TeamMember).filter_by(
                team_id=team_id,
                user_id=removed_by
            ).first()

            if not remover_member or remover_member.role != 'owner':
                self.logger.warning(f"Permission denied: User {removed_by} cannot remove from team {team_id}")
                return {
                    'success': False,
                    'error': 'Permission denied: Only owners can remove members',
                    'error_code': 'PERMISSION_DENIED'
                }

            # Find member to remove
            member = db_auth.query(TeamMember).filter_by(
                team_id=team_id,
                user_id=user_id
            ).first()

            if not member:
                self.logger.warning(f"User {user_id} is not a member of team {team_id}")
                return {
                    'success': False,
                    'error': 'User is not a team member',
                    'error_code': 'NOT_FOUND'
                }

            # Cannot remove last owner
            if member.role == 'owner':
                owner_count = db_auth.query(TeamMember).filter_by(
                    team_id=team_id,
                    role='owner'
                ).count()
                if owner_count <= 1:
                    self.logger.warning(f"Cannot remove last owner from team {team_id}")
                    return {
                        'success': False,
                        'error': 'Cannot remove last owner',
                        'error_code': 'VALIDATION_ERROR'
                    }

            # Remove member
            db_auth.delete(member)
            db_auth.commit()

            self.logger.info(f"User {user_id} removed from team {team_id}")

            return {
                'success': True,
                'removed_user_id': str(user_id)
            }

        except Exception as e:
            self.logger.error(f"Error removing member from team {team_id}: {e}", exc_info=True)
            if db_auth:
                db_auth.rollback()
            return {
                'success': False,
                'error': f'Failed to remove team member: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db_auth:
                db_auth.close()

    def _get_team_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get team details with members.

        Args:
            data: {'team_id': UUID}

        Returns:
            {'success': bool, 'team': dict, 'members': List[dict]}
        """
        team_id = data.get('team_id')

        if not team_id:
            return {
                'success': False,
                'error': 'team_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get auth database
        db_auth = self.services.get_database_auth()

        # Get team
        team = db_auth.query(Team).filter_by(id=team_id).first()
        if not team:
            return {
                'success': False,
                'error': f'Team not found: {team_id}',
                'error_code': 'NOT_FOUND'
            }

        # Get members with eager loading of User relationship (prevents N+1 query problem)
        # OPTIMIZATION: Instead of 1 query + N user lookups, this does 2 total queries
        members = db_auth.query(TeamMember).filter_by(team_id=team_id)\
            .options(selectinload(TeamMember.user)).all()

        # Get user details for members
        member_data = []
        for member in members:
            user = member.user  # Already loaded by selectinload, no additional query
            member_data.append({
                'member_id': str(member.id),
                'user_id': str(member.user_id),
                'email': user.email if user else None,
                'role': member.role,
                'joined_at': member.joined_at.isoformat()
            })

        return {
            'success': True,
            'team': team.to_dict(),  # TODO Parameter 'self' unfilled
            'members': member_data
        }

    def _create_team_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create project owned by team.

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
        team_id = data.get('team_id')
        name = data.get('name')
        description = data.get('description', '')
        created_by = data.get('created_by')

        # Validate
        if not all([team_id, name, created_by]):
            self.logger.warning("Validation error: missing required fields for create_team_project")
            return {
                'success': False,
                'error': 'team_id, name, and created_by are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db_auth = None
        db_specs = None

        try:
            # Get databases
            db_auth = self.services.get_database_auth()
            db_specs = self.services.get_database_specs()

            # Verify user is team member
            member = db_auth.query(TeamMember).filter_by(
                team_id=team_id,
                user_id=created_by
            ).first()

            if not member:
                self.logger.warning(f"Permission denied: User {created_by} is not member of team {team_id}")
                return {
                    'success': False,
                    'error': 'User is not a team member',
                    'error_code': 'PERMISSION_DENIED'
                }

            # Create project
            project = Project(
                user_id=created_by,
                name=name,
                description=description,
                current_phase='discovery',
                maturity_score=0,
                status='active'
            )
            db_specs.add(project)
            db_specs.flush()

            # Create project share record (in socrates_specs database)
            share = ProjectShare(
                project_id=project.id,
                team_id=team_id,
                shared_by=created_by,
                permission_level='admin'  # Team members have admin access
            )
            db_specs.add(share)
            db_specs.commit()

            self.logger.info(f"Team project created: {name} (ID: {project.id})")

            return {
                'success': True,
                'project_id': str(project.id),
                'team_id': str(team_id)
            }

        except Exception as e:
            self.logger.error(f"Error creating team project: {e}", exc_info=True)
            if db_specs:
                db_specs.rollback()
            return {
                'success': False,
                'error': f'Failed to create team project: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db_auth:
                db_auth.close()
            if db_specs:
                db_specs.close()

    def _share_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Share existing project with team.

        Args:
            data: {
                'project_id': UUID,
                'team_id': UUID,
                'shared_by': UUID,
                'permission_level': str ('read' | 'write' | 'admin')
            }

        Returns:
            {'success': bool, 'share_id': UUID}
        """
        project_id = data.get('project_id')
        team_id = data.get('team_id')
        shared_by = data.get('shared_by')
        permission_level = data.get('permission_level', 'read')

        # Validate
        if not all([project_id, team_id, shared_by]):
            self.logger.warning("Validation error: missing required fields for share_project")
            return {
                'success': False,
                'error': 'project_id, team_id, and shared_by are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db_specs = None

        try:
            # Get specs database
            db_specs = self.services.get_database_specs()

            # Verify project ownership
            project = db_specs.query(Project).filter_by(id=project_id).first()
            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'NOT_FOUND'
                }

            if str(project.user_id) != str(shared_by):
                self.logger.warning(f"Permission denied: User {shared_by} is not owner of project {project_id}")
                return {
                    'success': False,
                    'error': 'Only project owner can share',
                    'error_code': 'PERMISSION_DENIED'
                }

            # Check if already shared
            existing = db_specs.query(ProjectShare).filter_by(
                project_id=project_id,
                team_id=team_id
            ).first()

            if existing:
                self.logger.warning(f"Project {project_id} already shared with team {team_id}")
                return {
                    'success': False,
                    'error': 'Project already shared with this team',
                    'error_code': 'ALREADY_EXISTS'
                }

            # Create share
            share = ProjectShare(
                project_id=project_id,
                team_id=team_id,
                shared_by=shared_by,
                permission_level=permission_level
            )
            db_specs.add(share)
            db_specs.commit()

            self.logger.info(f"Project {project_id} shared with team {team_id}")

            return {
                'success': True,
                'share_id': str(share.id)
            }

        except Exception as e:
            self.logger.error(f"Error sharing project {project_id} with team {team_id}: {e}", exc_info=True)
            if db_specs:
                db_specs.rollback()
            return {
                'success': False,
                'error': f'Failed to share project: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db_specs:
                db_specs.close()

    def _get_team_activity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get team activity summary.

        Args:
            data: {'team_id': UUID}

        Returns:
            {'success': bool, 'team_members': List[dict], 'shared_projects': List[dict]}
        """
        team_id = data.get('team_id')

        if not team_id:
            return {
                'success': False,
                'error': 'team_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get databases
        db_auth = self.services.get_database_auth()
        db_specs = self.services.get_database_specs()

        # Get team members with eager loading (prevents N+1 query problem)
        # OPTIMIZATION: Loads members and their users in 2 queries instead of 1+N
        members = db_auth.query(TeamMember).filter_by(team_id=team_id)\
            .options(selectinload(TeamMember.user)).all()
        member_data = []
        for member in members:
            user = member.user  # Already loaded by selectinload, no additional query
            member_data.append({
                'user_id': str(member.user_id),
                'email': user.email if user else None,
                'role': member.role,
                'joined_at': member.joined_at.isoformat()
            })

        # Get shared projects with eager loading (prevents N+1 query problem)
        # OPTIMIZATION: Loads shares and their projects in 2 queries instead of 1+N
        shares = db_specs.query(ProjectShare).filter_by(team_id=team_id)\
            .options(selectinload(ProjectShare.project)).all()
        project_data = []
        for share in shares:
            project = share.project  # Already loaded by selectinload, no additional query
            if project:
                project_data.append({
                    'project_id': str(project.id),
                    'name': project.name,
                    'permission_level': share.permission_level,
                    'shared_at': share.shared_at.isoformat()
                })

        return {
            'success': True,
            'team_members': member_data,
            'shared_projects': project_data
        }

    def _detect_team_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect conflicts between team members' specifications.

        Note: This is a placeholder implementation. Full conflict detection
        requires the Specification model and conversation history tracking.

        Args:
            data: {'project_id': UUID}

        Returns:
            {'success': bool, 'team_conflicts': List[dict]}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Placeholder: Full implementation requires Specification model
        # and tracking which user created which spec
        return {
            'success': True,
            'team_conflicts': [],
            'conflict_count': 0,
            'note': 'Conflict detection requires Specification tracking (Phase 2)'
        }

    def _assign_role_based_questions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign questions based on team member's role.

        Args:
            data: {
                'user_id': UUID,
                'team_id': UUID
            }

        Returns:
            {'success': bool, 'assigned_categories': List[str], 'role': str}
        """
        user_id = data.get('user_id')
        team_id = data.get('team_id')

        if not all([user_id, team_id]):
            return {
                'success': False,
                'error': 'user_id and team_id are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get auth database
        db_auth = self.services.get_database_auth()

        # Get user's role in team
        member = db_auth.query(TeamMember).filter_by(
            team_id=team_id,
            user_id=user_id
        ).first()

        if not member:
            return {
                'success': False,
                'error': 'User is not a team member',
                'error_code': 'NOT_FOUND'
            }

        # Role-based question assignment
        role_question_mapping = {
            'owner': ['goals', 'requirements', 'timeline', 'constraints'],
            'lead': ['requirements', 'tech_stack', 'scalability', 'deployment'],
            'developer': ['tech_stack', 'testing', 'deployment'],
            'viewer': []  # Viewers cannot answer questions
        }

        assigned_categories = role_question_mapping.get(member.role, [])

        return {
            'success': True,
            'role': member.role,
            'assigned_categories': assigned_categories
        }
