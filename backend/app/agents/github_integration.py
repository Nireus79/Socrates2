"""
GitHubIntegrationAgent - Integrate with GitHub for repository analysis and import.
"""
from typing import Any, Dict, List

from ..core.dependencies import ServiceContainer
from ..models.project import Project
from ..models.specification import Specification
from .base import BaseAgent


class GitHubIntegrationAgent(BaseAgent):
    """
    GitHubIntegrationAgent - GitHub repository analysis and import.

    Capabilities:
    - import_repository: Import and analyze GitHub repository
    - list_repositories: List user's GitHub repositories (placeholder)
    - analyze_repository: Analyze repository structure
    """

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        """Initialize GitHubIntegrationAgent"""
        super().__init__(agent_id, name, services)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'import_repository',
            'list_repositories',
            'analyze_repository'
        ]

    def _import_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import GitHub repository and analyze.

        Args:
            data: {
                'user_id': UUID,
                'repo_url': str (e.g., 'https://github.com/user/repo'),
                'project_name': str (optional)
            }

        Returns:
            {
                'success': bool,
                'project_id': UUID,
                'specs_extracted': int,
                'analysis': dict
            }
        """
        user_id = data.get('user_id')
        repo_url = data.get('repo_url')
        project_name = data.get('project_name')

        if not all([user_id, repo_url]):
            return {
                'success': False,
                'error': 'user_id and repo_url are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Parse repository URL
        if not repo_url.startswith('https://github.com/'):
            return {
                'success': False,
                'error': 'Only GitHub URLs are supported (https://github.com/user/repo)',
                'error_code': 'VALIDATION_ERROR'
            }

        # Extract owner and repo name
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 5:
            return {
                'success': False,
                'error': 'Invalid GitHub URL format',
                'error_code': 'VALIDATION_ERROR'
            }

        repo_owner = parts[-2]
        repo_name = parts[-1]

        # TODO: Clone repository using GitPython
        # For now, create placeholder analysis

        analysis = self._create_placeholder_analysis(repo_owner, repo_name)

        # Create project
        if not project_name:
            project_name = f"{repo_owner}/{repo_name}"

        # Get specs database
        db_specs = self.services.get_database_specs()

        project = Project(
            user_id=user_id,
            name=project_name,
            description=f'Imported from {repo_url}',
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )
        db_specs.add(project)
        db_specs.flush()

        # Extract specifications from analysis
        specs = self._extract_specs_from_analysis(analysis)

        # Save specifications
        for spec_data in specs:
            spec = Specification(
                project_id=project.id,
                category=spec_data['category'],
                key=spec_data['key'],
                value=spec_data['value'],
                source='github_import',
                confidence=spec_data['confidence']
            )
            db_specs.add(spec)

        db_specs.commit()

        self.logger.info(
            f"Imported GitHub repository {repo_url} as project {project.id} "
            f"({len(specs)} specs extracted)"
        )

        return {
            'success': True,
            'project_id': str(project.id),
            'specs_extracted': len(specs),
            'analysis': analysis,
            'note': 'Full GitHub integration requires GitPython package and repository cloning'
        }

    def _list_repositories(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List user's GitHub repositories (placeholder).

        Args:
            data: {'user_id': UUID}

        Returns:
            {'success': bool, 'repositories': List[dict]}
        """
        # TODO: Implement GitHub API integration
        # This would require:
        # 1. GitHub OAuth token
        # 2. GitHub API client
        # 3. Pagination handling

        return {
            'success': True,
            'repositories': [],
            'message': 'GitHub repository listing not yet implemented',
            'note': 'Requires GitHub OAuth integration'
        }

    def _analyze_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze repository structure.

        Args:
            data: {'repo_url': str}

        Returns:
            {'success': bool, 'analysis': dict}
        """
        repo_url = data.get('repo_url')

        if not repo_url:
            return {
                'success': False,
                'error': 'repo_url is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Parse URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 5:
            return {
                'success': False,
                'error': 'Invalid GitHub URL format',
                'error_code': 'VALIDATION_ERROR'
            }

        repo_owner = parts[-2]
        repo_name = parts[-1]

        # Create placeholder analysis
        analysis = self._create_placeholder_analysis(repo_owner, repo_name)

        return {
            'success': True,
            'analysis': analysis,
            'note': 'Full repository analysis requires cloning and file inspection'
        }

    def _create_placeholder_analysis(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Create placeholder analysis for repository.

        In production, this would clone the repo and analyze files.
        """
        return {
            'owner': owner,
            'repository': repo,
            'languages': {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.md': 'Markdown'
            },
            'frameworks': ['Unknown (requires repository cloning)'],
            'has_tests': None,
            'has_ci': None,
            'file_count': 0,
            'note': 'Placeholder analysis - full analysis requires GitPython'
        }

    def _extract_specs_from_analysis(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract specifications from repository analysis.

        Args:
            analysis: Repository analysis data

        Returns:
            List of specification dictionaries
        """
        specs = []

        # Extract languages
        if 'languages' in analysis and analysis['languages']:
            for ext, language in analysis['languages'].items():
                if language != 'Markdown':  # Skip documentation
                    specs.append({
                        'category': 'tech_stack',
                        'key': 'language',
                        'value': language,
                        'confidence': 0.5  # Low confidence without actual file analysis
                    })

        # Extract frameworks
        if 'frameworks' in analysis and analysis['frameworks']:
            for framework in analysis['frameworks']:
                if 'Unknown' not in framework:
                    specs.append({
                        'category': 'tech_stack',
                        'key': 'framework',
                        'value': framework,
                        'confidence': 0.5
                    })

        # Add GitHub source specification
        if 'repository' in analysis:
            specs.append({
                'category': 'metadata',
                'key': 'source',
                'value': f"GitHub: {analysis.get('owner')}/{analysis.get('repository')}",
                'confidence': 1.0
            })

        return specs
