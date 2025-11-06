"""
ProjectManagerAgent - Manages project lifecycle (CRUD operations).
"""
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseAgent
from ..models.project import Project
from ..models.user import User
from ..core.dependencies import ServiceContainer


class ProjectManagerAgent(BaseAgent):
    """
    ProjectManagerAgent - Manages project lifecycle.

    Capabilities:
    - create_project: Create new project
    - get_project: Get project by ID
    - update_project: Update project fields
    - delete_project: Archive project
    - list_projects: List all projects for user
    - update_maturity: Update project maturity score
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'create_project',
            'get_project',
            'update_project',
            'delete_project',
            'list_projects',
            'update_maturity'
        ]

    def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new project.

        Args:
            data: {
                'user_id': str (UUID),
                'name': str,
                'description': str (optional)
            }

        Returns:
            {'success': bool, 'project_id': str, 'project': dict}
        """
        user_id = data.get('user_id')
        name = data.get('name')
        description = data.get('description', '')

        # Validate
        if not user_id or not name:
            return {
                'success': False,
                'error': 'user_id and name are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Check user exists (in socrates_auth database)
        user = self.services.get_database_auth().query(User).filter(User.id == user_id).first()
        if not user:
            return {
                'success': False,
                'error': f'User not found: {user_id}',
                'error_code': 'USER_NOT_FOUND'
            }

        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )

        db = self.services.get_database_specs()
        db.add(project)
        db.commit()
        db.refresh(project)

        self.logger.info(f"Created project: {project.id} for user: {user_id}")

        return {
            'success': True,
            'project_id': str(project.id),
            'project': project.to_dict()
        }

    def _get_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get project by ID.

        Args:
            data: {
                'project_id': str (UUID)
            }

        Returns:
            {'success': bool, 'project': dict}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = self.services.get_database_specs()
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'PROJECT_NOT_FOUND'
            }

        return {
            'success': True,
            'project': project.to_dict()
        }

    def _update_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update project fields.

        Args:
            data: {
                'project_id': str (UUID),
                'name': str (optional),
                'description': str (optional),
                'current_phase': str (optional),
                'status': str (optional)
            }

        Returns:
            {'success': bool, 'project': dict}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = self.services.get_database_specs()
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'PROJECT_NOT_FOUND'
            }

        # Update fields if provided
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'current_phase' in data:
            project.current_phase = data['current_phase']
        if 'status' in data:
            project.status = data['status']

        db.commit()
        db.refresh(project)

        self.logger.info(f"Updated project: {project.id}")

        return {
            'success': True,
            'project': project.to_dict()
        }

    def _delete_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Archive project (soft delete).

        Args:
            data: {
                'project_id': str (UUID)
            }

        Returns:
            {'success': bool}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = self.services.get_database_specs()
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'PROJECT_NOT_FOUND'
            }

        # Soft delete (archive)
        project.status = 'archived'
        db.commit()

        self.logger.info(f"Archived project: {project.id}")

        return {
            'success': True,
            'project_id': str(project.id)
        }

    def _list_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all projects for user.

        Args:
            data: {
                'user_id': str (UUID)
            }

        Returns:
            {'success': bool, 'projects': list, 'count': int}
        """
        user_id = data.get('user_id')

        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = self.services.get_database_specs()
        projects = db.query(Project).filter(
            Project.user_id == user_id,
            Project.status != 'archived'
        ).order_by(Project.created_at.desc()).all()

        return {
            'success': True,
            'projects': [p.to_dict() for p in projects],
            'count': len(projects)
        }

    def _update_maturity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update project maturity score.

        Args:
            data: {
                'project_id': str (UUID),
                'maturity_score': int (0-100)
            }

        Returns:
            {'success': bool, 'maturity_score': int}
        """
        project_id = data.get('project_id')
        maturity_score = data.get('maturity_score')

        if not project_id or maturity_score is None:
            return {
                'success': False,
                'error': 'project_id and maturity_score are required',
                'error_code': 'VALIDATION_ERROR'
            }

        if not (0 <= maturity_score <= 100):
            return {
                'success': False,
                'error': 'maturity_score must be between 0 and 100',
                'error_code': 'VALIDATION_ERROR'
            }

        db = self.services.get_database_specs()
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'PROJECT_NOT_FOUND'
            }

        project.maturity_score = maturity_score
        db.commit()

        self.logger.info(f"Updated maturity for project {project.id}: {maturity_score}%")

        return {
            'success': True,
            'maturity_score': maturity_score
        }
