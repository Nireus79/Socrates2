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
            self.logger.warning(f"Validation error: missing user_id or name")
            return {
                'success': False,
                'error': 'user_id and name are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db_auth = None
        db_specs = None

        try:
            # Check user exists (in socrates_auth database)
            db_auth = self.services.get_database_auth()
            user = db_auth.query(User).filter(User.id == user_id).first()  # TODO Expected type 'ColumnElement[bool] | _HasClauseElement[bool] | SQLCoreOperations[bool] | ExpressionElementRole[bool] | TypedColumnsClauseRole[bool] | () -> ColumnElement[bool] | LambdaElement', got 'bool' instead
            if not user:
                self.logger.warning(f"User not found: {user_id}")
                return {
                    'success': False,
                    'error': f'User not found: {user_id}',
                    'error_code': 'USER_NOT_FOUND'
                }

            # Create project
            db_specs = self.services.get_database_specs()
            project = Project(
                creator_id=user_id,  # Set creator_id (immutable audit trail)
                owner_id=user_id,    # Set owner_id (current owner)
                user_id=user_id,     # Deprecated but still required for backwards compatibility
                name=name,
                description=description,
                current_phase='discovery',
                maturity_score=0,
                status='active'
            )

            db_specs.add(project)
            db_specs.commit()
            db_specs.refresh(project)

            self.logger.info(f"Created project: {project.id} for user: {user_id}")

            return {
                'success': True,
                'project_id': str(project.id),
                'project': project.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Error creating project: {e}", exc_info=True)
            if db_specs:
                db_specs.rollback()
            return {
                'success': False,
                'error': f'Failed to create project: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db_auth:
                db_auth.close()
            if db_specs:
                db_specs.close()

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
            self.logger.warning("Validation error: missing project_id")
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None
        try:
            db = self.services.get_database_specs()
            project = db.query(Project).filter(Project.id == project_id).first()  # TODO Expected type 'ColumnElement[bool] | _HasClauseElement[bool] | SQLCoreOperations[bool] | ExpressionElementRole[bool] | TypedColumnsClauseRole[bool] | () -> ColumnElement[bool] | LambdaElement', got 'bool' instead

            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            return {
                'success': True,
                'project': project.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to get project: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db:
                db.close()

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
            self.logger.warning("Validation error: missing project_id")
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None
        try:
            db = self.services.get_database_specs()
            project = db.query(Project).filter(Project.id == project_id).first()  # TODO Expected type 'ColumnElement[bool] | _HasClauseElement[bool] | SQLCoreOperations[bool] | ExpressionElementRole[bool] | TypedColumnsClauseRole[bool] | () -> ColumnElement[bool] | LambdaElement', got 'bool' instead

            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            # Update fields if provided
            updates = []
            if 'name' in data:
                project.name = data['name']
                updates.append(f"name={data['name']}")
            if 'description' in data:
                project.description = data['description']
                updates.append("description updated")
            if 'current_phase' in data:
                project.current_phase = data['current_phase']
                updates.append(f"current_phase={data['current_phase']}")
            if 'status' in data:
                project.status = data['status']
                updates.append(f"status={data['status']}")

            db.commit()
            db.refresh(project)

            self.logger.info(f"Updated project {project.id}: {', '.join(updates)}")

            return {
                'success': True,
                'project': project.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {e}", exc_info=True)
            if db:
                db.rollback()
            return {
                'success': False,
                'error': f'Failed to update project: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db:
                db.close()

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
            self.logger.warning("Validation error: missing project_id")
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None
        try:
            db = self.services.get_database_specs()
            project = db.query(Project).filter(Project.id == project_id).first()  # TODO Expected type 'ColumnElement[bool] | _HasClauseElement[bool] | SQLCoreOperations[bool] | ExpressionElementRole[bool] | TypedColumnsClauseRole[bool] | () -> ColumnElement[bool] | LambdaElement', got 'bool' instead

            if not project:
                self.logger.warning(f"Project not found: {project_id}")
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

        except Exception as e:
            self.logger.error(f"Error archiving project {project_id}: {e}", exc_info=True)
            if db:
                db.rollback()
            return {
                'success': False,
                'error': f'Failed to archive project: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db:
                db.close()

    def _list_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all projects for user.

        Args:
            data: {
                'user_id': str (UUID),
                'skip': int (optional),
                'limit': int (optional)
            }

        Returns:
            {'success': bool, 'projects': list, 'total': int}
        """
        user_id = data.get('user_id')
        skip = data.get('skip', 0)
        limit = data.get('limit', 100)

        if not user_id:
            self.logger.warning("Validation error: missing user_id")
            return {
                'success': False,
                'error': 'user_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None
        try:
            db = self.services.get_database_specs()
            query = db.query(Project).filter(
                Project.user_id == user_id,  # TODO Expected type 'ColumnElement[bool] | _HasClauseElement[bool] | SQLCoreOperations[bool] | ExpressionElementRole[bool] | TypedColumnsClauseRole[bool] | () -> ColumnElement[bool] | LambdaElement', got 'bool' instead
                Project.status != 'archived'
            ).order_by(Project.created_at.desc())

            # Get total count before pagination
            total = query.count()

            # Apply pagination
            projects = query.offset(skip).limit(limit).all()

            self.logger.debug(f"Listed {len(projects)} projects for user {user_id}")

            return {
                'success': True,
                'projects': [p.to_dict() for p in projects],  # TODO Parameter 'self' unfilled
                'total': total
            }

        except Exception as e:
            self.logger.error(f"Error listing projects for user {user_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to list projects: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db:
                db.close()

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
            self.logger.warning("Validation error: missing project_id or maturity_score")
            return {
                'success': False,
                'error': 'project_id and maturity_score are required',
                'error_code': 'VALIDATION_ERROR'
            }

        if not (0 <= maturity_score <= 100):
            self.logger.warning(f"Invalid maturity_score: {maturity_score}")
            return {
                'success': False,
                'error': 'maturity_score must be between 0 and 100',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None
        try:
            db = self.services.get_database_specs()
            project = db.query(Project).filter(Project.id == project_id).first()  # TODO Expected type 'ColumnElement[bool] | _HasClauseElement[bool] | SQLCoreOperations[bool] | ExpressionElementRole[bool] | TypedColumnsClauseRole[bool] | () -> ColumnElement[bool] | LambdaElement', got 'bool' instead

            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            old_score = project.maturity_score
            project.maturity_score = maturity_score
            db.commit()

            self.logger.info(f"Updated maturity for project {project.id}: {old_score}% -> {maturity_score}%")

            return {
                'success': True,
                'maturity_score': maturity_score
            }

        except Exception as e:
            self.logger.error(f"Error updating maturity for project {project_id}: {e}", exc_info=True)
            if db:
                db.rollback()
            return {
                'success': False,
                'error': f'Failed to update maturity: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if db:
                db.close()
