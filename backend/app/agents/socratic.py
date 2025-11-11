"""
SocraticCounselorAgent - Generates Socratic questions to gather requirements.

This agent orchestrates the question generation process:
1. Loads data from databases
2. Converts to plain data models
3. Uses QuestionGenerator core engine for business logic
4. Saves results back to database

The pure business logic (calculating coverage, building prompts, parsing responses)
is handled by the QuestionGenerator in the Socrates library.
This separation enables testing without database and library extraction.
"""
import json
from decimal import Decimal
from typing import Any, Dict, List

# Import from Socrates library instead of local core
from socrates import (
    QuestionGenerator,
    UserBehaviorData,
    project_db_to_data,
    questions_db_to_data,
    specs_db_to_data,
)
from sqlalchemy import and_

from ..core.action_logger import log_question
from ..core.dependencies import ServiceContainer
from ..models.project import Project
from ..models.question import Question
from ..models.session import Session
from ..models.specification import Specification
from .base import BaseAgent


class SocraticCounselorAgent(BaseAgent):
    """
    SocraticCounselorAgent - Generates Socratic questions to gather requirements.

    Capabilities:
    - generate_question: Generate next question based on project context
    - generate_questions_batch: Generate multiple questions at once

    Architecture:
    - This agent handles: Database I/O, API orchestration, validation, persistence
    - QuestionGenerator handles: Coverage calculation, prompt building, response parsing
    - Clear separation enables testing without database and library extraction
    """

    def __init__(self, agent_id: str = 'socratic', name: str = 'Socratic Counselor', services: ServiceContainer = None):
        """Initialize agent with question generator"""
        super().__init__(agent_id, name, services)
        self.question_generator = QuestionGenerator(self.logger)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'generate_question',
            'generate_questions_batch'
        ]

    def _generate_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate next Socratic question based on project context.

        Args:
            data: {
                'project_id': str (UUID),
                'session_id': str (UUID)
            }

        Returns:
            {'success': bool, 'question': dict, 'question_id': str}
        """
        project_id = data.get('project_id')
        session_id = data.get('session_id')

        # Validate
        if not project_id or not session_id:
            self.logger.warning("Validation error: missing project_id or session_id")
            return {
                'success': False,
                'error': 'project_id and session_id are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None

        try:
            db = self.services.get_database_specs()

            # Load project context
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            # Load session
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                self.logger.warning(f"Session not found: {session_id}")
                return {
                    'success': False,
                    'error': f'Session not found: {session_id}',
                    'error_code': 'SESSION_NOT_FOUND'
                }

            # Load existing specifications (limit to recent for performance)
            existing_specs = db.query(Specification).filter(
                and_(
                    Specification.project_id == project_id,
                    Specification.is_current == True
                )
            ).order_by(Specification.created_at.desc()).limit(100).all()

            # Load previous questions
            previous_questions = db.query(Question).filter(
                Question.project_id == project_id
            ).order_by(Question.created_at.desc()).limit(10).all()

            # PHASE 1: Convert DB models to plain data models (for QuestionGenerator)
            project_data = project_db_to_data(project)
            specs_data = specs_db_to_data(existing_specs)
            questions_data = questions_db_to_data(previous_questions)

            # PHASE 2: Use QuestionGenerator for pure business logic
            # Calculate coverage per category
            coverage = self.question_generator.calculate_coverage(specs_data)

            # Identify next category to focus on (lowest coverage)
            next_category = self.question_generator.identify_next_category(coverage)

            # Get user learning profile for personalization
            user_behavior = None
            try:
                from .orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                learning_result = orchestrator.route_request(
                    'learning',
                    'get_user_profile',
                    {'user_id': str(project.user_id)}
                )
                if learning_result.get('success'):
                    user_behavior = UserBehaviorData(
                        user_id=str(project.user_id),
                        total_questions_asked=learning_result.get('total_questions_asked', 0),
                        overall_response_quality=learning_result.get('overall_response_quality', 0.5),
                        patterns=learning_result.get('behavior_patterns', {}),
                        learned_from_projects=learning_result.get('learned_from_projects', 0)
                    )
                    self.logger.debug(f"Retrieved user learning profile: {user_behavior.total_questions_asked} questions asked")
            except Exception as e:
                self.logger.warning(f"Could not retrieve user learning profile: {e}")
                user_behavior = None

            # Build prompt for Claude using QuestionGenerator
            prompt = self.question_generator.build_question_generation_prompt(
                project_data, specs_data, questions_data, next_category, user_behavior
            )

            # PHASE 3: Call Claude API (Agent responsibility - not in core engine)
            try:
                self.logger.debug(f"Calling Claude API to generate question for project {project_id}, category: {next_category}")
                model_name = "claude-sonnet-4-5-20250929"
                response = self.services.get_claude_client().messages.create(
                    model=model_name,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract and parse response using QuestionGenerator
                response_text = response.content[0].text
                self.logger.debug(f"Claude API response received: {len(response_text)} chars")
                self.logger.debug(f"Response text preview (first 200 chars): {response_text[:200]}")

                # Use QuestionGenerator to parse response (handles markdown stripping, JSON parsing)
                question_data = self.question_generator.parse_question_response(response_text, next_category)

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Claude response as JSON: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': 'Failed to parse question from Claude API',
                    'error_code': 'PARSE_ERROR'
                }
            except ValueError as e:
                self.logger.error(f"Invalid question data from Claude: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': 'Invalid question data from Claude API',
                    'error_code': 'PARSE_ERROR'
                }
            except Exception as e:
                self.logger.error(f"Claude API error: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Claude API error: {str(e)}',
                    'error_code': 'API_ERROR'
                }

            # Analyze question for bias before saving
            quality_check_passed = True
            quality_score = Decimal('1.0')
            try:
                from .orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                bias_check = orchestrator.route_request(
                    'quality',
                    'analyze_question',
                    {
                        'question_text': question_data['text'],
                        'project_id': project_id
                    }
                )
                if bias_check.get('success'):
                    quality_score = Decimal(str(1.0 - bias_check.get('bias_score', 0.0)))
                    if bias_check.get('is_blocking'):
                        self.logger.warning(f"Question blocked due to bias: {bias_check.get('reason')}")
                        quality_check_passed = False
                    else:
                        self.logger.debug(f"Question passed bias check: score={bias_check.get('bias_score', 0.0):.2f}")
            except Exception as e:
                self.logger.warning(f"Could not perform bias check: {e}, proceeding with question")
                quality_check_passed = True

            # If quality check failed, return error with suggestion
            if not quality_check_passed:
                return {
                    'success': False,
                    'error': bias_check.get('reason', 'Question quality check failed'),
                    'error_code': 'QUALITY_CHECK_FAILED',
                    'suggested_alternatives': bias_check.get('suggested_alternatives', [])
                }

            # Save question
            question = Question(
                project_id=project_id,
                session_id=session_id,
                text=question_data['text'],
                category=question_data['category'],
                context=question_data.get('context'),
                quality_score=quality_score
            )

            db.add(question)
            db.commit()
            db.refresh(question)

            self.logger.info(f"Generated question {question.id} for project {project_id}, category: {question.category}, quality_score: {quality_score}")

            # Log question generation
            log_question(
                "Question generated",
                category=question.category,
                success=True,
                quality_score=float(quality_score)
            )

            return {
                'success': True,
                'question': question.to_dict(),
                'question_id': str(question.id)
            }

        except Exception as e:
            self.logger.error(f"Error generating question: {e}", exc_info=True)
            if db:
                db.rollback()
            return {
                'success': False,
                'error': f'Failed to generate question: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            pass  # Session managed by caller/dependency injection

    def _generate_questions_batch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate multiple questions at once.

        Args:
            data: {
                'project_id': str (UUID),
                'session_id': str (UUID),
                'count': int (default: 5)
            }

        Returns:
            {'success': bool, 'questions': list, 'count': int}
        """
        project_id = data.get('project_id')
        session_id = data.get('session_id')
        count = data.get('count', 5)

        if not project_id or not session_id:
            return {
                'success': False,
                'error': 'project_id and session_id are required',
                'error_code': 'VALIDATION_ERROR'
            }

        questions = []
        for _ in range(count):
            result = self._generate_question({'project_id': project_id, 'session_id': session_id})
            if result['success']:
                questions.append(result['question'])
            else:
                # If one fails, return what we have so far
                break

        return {
            'success': True,
            'questions': questions,
            'count': len(questions)
        }

