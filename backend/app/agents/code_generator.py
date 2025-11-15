"""
CodeGeneratorAgent - Generates complete codebase from specifications.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import and_

from ..models.conflict import Conflict, ConflictStatus
from ..models.generated_file import GeneratedFile
from ..models.generated_project import GeneratedProject, GenerationStatus
from ..models.project import Project
from ..models.question import QuestionCategory
from ..models.specification import Specification
from .base import BaseAgent


class CodeGeneratorAgent(BaseAgent):
    """
    Generates complete, production-ready codebase from specifications.

    Responsibilities:
    - Enforce maturity gate (100% required)
    - Check for unresolved conflicts
    - Load and organize all specifications
    - Generate code via Claude API
    - Parse generated code into individual files
    - Save to database with traceability

    Used by:
    - Phase 4: Primary code generation
    - Phase 5+: Enhanced with quality control
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            'generate_code',
            'get_generation_status',
            'list_generations'
        ]

    def _generate_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete codebase from specifications.

        REFACTORED: Database connection released BEFORE Claude API call
        to prevent connection pool exhaustion during 30-60 second code generation.

        Args:
            data: {
                'project_id': str
            }

        Returns:
            {
                'success': bool,
                'generation_id': str,
                'total_files': int,
                'total_lines': int
            }
            OR on failure:
            {
                'success': False,
                'error': str,
                'error_code': str,
                'maturity_score': float (if MATURITY_NOT_REACHED),
                'missing_categories': list (if MATURITY_NOT_REACHED)
            }
        """
        project_id = data.get('project_id')

        # Validate
        if not project_id:
            self.logger.warning("Validation error: missing project_id")
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        try:
            # PHASE 1: Load all data from database (quick operation)
            db = self.services.get_database_specs()

            # Load project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                db.close()
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            # GATE 1: Check maturity score
            if project.maturity_score < 100.0:
                missing_categories = self._identify_missing_categories(project_id, db)
                self.logger.warning(
                    f"Project {project_id} maturity is {project.maturity_score}%, need 100%"
                )
                db.close()
                return {
                    'success': False,
                    'error': f'Project maturity is {project.maturity_score}%. Need 100% to generate code.',
                    'error_code': 'MATURITY_NOT_REACHED',
                    'maturity_score': float(project.maturity_score),
                    'missing_categories': missing_categories
                }

            # GATE 2: Check for unresolved conflicts
            unresolved_conflicts = db.query(Conflict).filter(
                and_(
                    Conflict.project_id == project_id,
                    Conflict.status == ConflictStatus.OPEN
                )
            ).count()

            if unresolved_conflicts > 0:
                self.logger.warning(
                    f"Project {project_id} has {unresolved_conflicts} unresolved conflicts"
                )
                db.close()
                return {
                    'success': False,
                    'error': f'Project has {unresolved_conflicts} unresolved conflicts. Resolve them before generating code.',
                    'error_code': 'UNRESOLVED_CONFLICTS',
                    'unresolved_count': unresolved_conflicts
                }

            # Load last generation version
            last_generation = db.query(GeneratedProject).filter(
                GeneratedProject.project_id == project_id
            ).order_by(GeneratedProject.generation_version.desc()).first()

            next_version = (last_generation.generation_version + 1) if last_generation else 1

            # Load ALL specifications (with reasonable limit for memory safety)
            specs = db.query(Specification).filter(
                and_(
                    Specification.project_id == project_id,
                    Specification.is_current == True
                )
            ).limit(1000).all()

            if not specs:
                self.logger.warning(f"No specifications found for project {project_id}")
                db.close()
                return {
                    'success': False,
                    'error': 'No specifications found for project',
                    'error_code': 'NO_SPECIFICATIONS'
                }

            # Convert project to dict for use after DB closes
            project_data = {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'maturity_score': project.maturity_score
            }

            # Convert specs to dicts for use after DB closes
            specs_data = [
                {
                    'id': str(spec.id),
                    'content': spec.content,
                    'category': spec.category,
                    'source': spec.source
                }
                for spec in specs
            ]

            # Group specifications by category
            grouped_specs = self._group_specs_by_category(specs)

            # Build comprehensive code generation prompt
            prompt = self._build_code_generation_prompt(project, grouped_specs)

            # CRITICAL: Close DB connection BEFORE Claude API call
            db.close()
            self.logger.debug(f"Database connection closed before Claude API call")

            # PHASE 2: Call GATE 3 (coverage check) with released DB connection
            coverage_check_passed = True
            coverage_details = {}
            try:
                from .orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                coverage_result = orchestrator.route_request(
                    'quality',
                    'analyze_coverage',
                    {'project_id': project_id}
                )
                if coverage_result.get('success'):
                    coverage_details = coverage_result
                    if coverage_result.get('is_blocking'):
                        self.logger.warning(f"Code generation blocked by coverage check: {coverage_result.get('reason')}")
                        coverage_check_passed = False
                    else:
                        self.logger.info(f"Coverage check passed: {coverage_result.get('coverage_score', 0):.0%}")
            except Exception as e:
                self.logger.warning(f"Could not perform coverage check: {e}, proceeding with generation")
                coverage_check_passed = True

            if not coverage_check_passed:
                return {
                    'success': False,
                    'error': coverage_details.get('reason', 'Coverage quality check failed'),
                    'error_code': 'QUALITY_CHECK_FAILED',
                    'coverage_gaps': coverage_details.get('coverage_gaps', []),
                    'suggested_actions': coverage_details.get('suggested_actions', [])
                }

            # PHASE 3: Call Claude API (NO DATABASE CONNECTION HELD!)
            code_text = None
            try:
                self.logger.debug(
                    f"Calling Claude API to generate code for project {project_id} "
                    f"with {len(specs_data)} specifications (DB connection released)"
                )
                claude_client = self.services.get_claude_client()
                response = claude_client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=16000,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract generated code
                code_text = response.content[0].text
                self.logger.debug(f"Claude API response received: {len(code_text)} chars (DB still released)")

            except Exception as e:
                self.logger.error(f"Claude API error: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Claude API error: {str(e)}',
                    'error_code': 'API_ERROR'
                }

            # PHASE 4: Process response (no DB needed)
            files = self._parse_generated_code(code_text)

            if not files:
                self.logger.warning("Failed to parse generated code into files")
                return {
                    'success': False,
                    'error': 'Failed to parse generated code',
                    'error_code': 'PARSE_ERROR'
                }

            # PHASE 5: Save to database (new connection, quick operation)
            db = self.services.get_database_specs()

            # Create generation record
            generation = GeneratedProject(
                project_id=project_id,
                generation_version=next_version,
                total_files=len(files),
                total_lines=0,
                generation_started_at=datetime.now(timezone.utc),
                generation_status=GenerationStatus.IN_PROGRESS
            )
            db.add(generation)
            db.commit()
            db.refresh(generation)

            self.logger.info(f"Started code generation for project {project_id}, version {next_version}")

            # Save files to database
            total_lines = 0
            for file_data in files:
                file_content = file_data['content']
                file_lines = len(file_content.split('\n'))
                total_lines += file_lines

                generated_file = GeneratedFile(
                    generated_project_id=generation.id,
                    file_path=file_data['path'],
                    file_content=file_content,
                    file_size=len(file_content),
                    spec_ids=file_data.get('spec_ids', [])
                )
                db.add(generated_file)

            # Update generation record
            generation.total_files = len(files)
            generation.total_lines = total_lines
            generation.generation_completed_at = datetime.now(timezone.utc)
            generation.generation_status = GenerationStatus.COMPLETED

            db.commit()
            db.refresh(generation)
            db.close()

            self.logger.info(
                f"Code generation completed for project {project_id}: "
                f"{len(files)} files, {total_lines} lines (DB connection now released)"
            )

            return {
                'success': True,
                'generation_id': str(generation.id),
                'total_files': generation.total_files,
                'total_lines': generation.total_lines,
                'generation_version': generation.generation_version
            }

        except Exception as e:
            self.logger.error(f"Error generating code for project {project_id}: {e}", exc_info=True)
            # Attempt to close DB if still open (from PHASE 5 save operation)
            try:
                if db and hasattr(db, 'is_active') and db.is_active:
                    db.rollback()
                    db.close()
            except Exception as cleanup_error:
                self.logger.debug(f"Error during exception cleanup: {cleanup_error}")

            return {
                'success': False,
                'error': f'Code generation failed: {str(e)}',
                'error_code': 'GENERATION_ERROR'
            }

        finally:
            pass  # Session managed by caller/dependency injection

    def _get_generation_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get status of a code generation.

        Args:
            data: {'generation_id': str}

        Returns:
            {'success': bool, 'generation': dict}
        """
        generation_id = data.get('generation_id')

        # Validate
        if not generation_id:
            self.logger.warning("Validation error: missing generation_id")
            return {
                'success': False,
                'error': 'generation_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None

        try:
            db = self.services.get_database_specs()
            generation = db.query(GeneratedProject).filter(
                GeneratedProject.id == generation_id
            ).first()

            if not generation:
                self.logger.warning(f"Generation not found: {generation_id}")
                return {
                    'success': False,
                    'error': f'Generation not found: {generation_id}',
                    'error_code': 'GENERATION_NOT_FOUND'
                }

            self.logger.debug(f"Retrieved generation status for {generation_id}")

            return {
                'success': True,
                'generation': generation.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Error getting generation status {generation_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to get generation status: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            pass  # Session managed by caller/dependency injection

    def _list_generations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all generations for a project.

        Args:
            data: {'project_id': str}

        Returns:
            {'success': bool, 'generations': list, 'count': int}
        """
        project_id = data.get('project_id')

        # Validate
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
            generations = db.query(GeneratedProject).filter(
                GeneratedProject.project_id == project_id
            ).order_by(GeneratedProject.generation_version.desc()).all()

            self.logger.debug(f"Listed {len(generations)} generations for project {project_id}")

            return {
                'success': True,
                'generations': [g.to_dict() for g in generations],
                'count': len(generations)
            }

        except Exception as e:
            self.logger.error(f"Error listing generations for project {project_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to list generations: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            pass  # Session managed by caller/dependency injection

    def _identify_missing_categories(self, project_id: str, db) -> List[Dict[str, Any]]:
        """Identify which categories are missing specifications."""
        # Expected minimums per category
        required_per_category = {
            QuestionCategory.GOALS: 5,
            QuestionCategory.REQUIREMENTS: 8,
            QuestionCategory.TECH_STACK: 6,
            QuestionCategory.SCALABILITY: 4,
            QuestionCategory.SECURITY: 5,
            QuestionCategory.PERFORMANCE: 4,
            QuestionCategory.TESTING: 4,
            QuestionCategory.MONITORING: 3,
            QuestionCategory.DATA_RETENTION: 3,
            QuestionCategory.DISASTER_RECOVERY: 4
        }

        # Count specs per category (with limit for memory safety)
        specs = db.query(Specification).filter(
            Specification.project_id == project_id
        ).limit(1000).all()

        category_counts = {}
        for spec in specs:
            category = spec.category
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1

        # Identify missing
        missing = []
        for category, required in required_per_category.items():
            count = category_counts.get(category, 0)
            if count < required:
                missing.append({
                    'category': category.value,
                    'current': count,
                    'required': required,
                    'gap': required - count
                })

        return missing

    def _group_specs_by_category(self, specs: List[Specification]) -> Dict[str, List[Specification]]:
        """Group specifications by category."""
        grouped = {}
        for spec in specs:
            category = spec.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(spec)
        return grouped

    def _build_code_generation_prompt(
        self,
        project: Project,
        grouped_specs: Dict[str, List[Specification]]
    ) -> str:
        """Build comprehensive prompt for code generation."""
        prompt = f"""Generate a complete, production-ready codebase based on these specifications.

PROJECT INFORMATION:
Name: {project.name}
Description: {project.description}
Maturity: {project.maturity_score}%

SPECIFICATIONS BY CATEGORY:
"""

        # Add all categories
        categories = [
            'goals', 'requirements', 'tech_stack', 'scalability',
            'security', 'performance', 'testing', 'monitoring',
            'data_retention', 'disaster_recovery'
        ]

        for category in categories:
            specs_in_category = grouped_specs.get(category, [])
            prompt += f"\n{category.upper().replace('_', ' ')} ({len(specs_in_category)} specs):\n"
            for spec in specs_in_category:
                prompt += f"- {spec.content}\n"

        prompt += """

GENERATION REQUIREMENTS:

1. Generate a complete, well-structured codebase
2. Include ALL necessary files (backend, frontend if needed, tests, config)
3. Follow best practices for the chosen tech stack
4. Include comprehensive documentation (README, API docs)
5. Add database migrations if needed
6. Include Docker configuration for easy deployment
7. Write production-quality code with proper error handling
8. Add unit and integration tests
9. Include setup and deployment instructions

OUTPUT FORMAT:
Return the code organized as individual files. Use this format:

```filepath: path/to/file.ext
<file content here>
```

For example:
```filepath: backend/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

```filepath: README.md
# Project Name

## Setup Instructions
...
```

Generate the COMPLETE codebase now:
"""

        return prompt

    def _parse_generated_code(self, code_text: str) -> List[Dict[str, Any]]:
        """
        Parse generated code text into individual files.

        Expected format:
        ```filepath: path/to/file.ext
        <content>
        ```
        """
        files = []

        # Match file blocks using regex
        pattern = r'```filepath:\s*(.+?)\n(.*?)```'
        matches = re.findall(pattern, code_text, re.DOTALL)

        for file_path, content in matches:
            file_path = file_path.strip()
            content = content.strip()

            files.append({
                'path': file_path,
                'content': content,
                'spec_ids': []  # TODO: Phase 5+ can add traceability
            })

        return files
