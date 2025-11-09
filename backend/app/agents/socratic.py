"""
SocraticCounselorAgent - Generates Socratic questions to gather requirements.
"""
from typing import Dict, Any, List, Tuple
from decimal import Decimal
import json

from sqlalchemy import and_

from .base import BaseAgent
from ..models.project import Project
from ..models.session import Session
from ..models.question import Question
from ..models.specification import Specification
from ..core.dependencies import ServiceContainer


# Question categories and their priorities
QUESTION_CATEGORIES = [
    'goals',
    'requirements',
    'tech_stack',
    'scalability',
    'security',
    'performance',
    'testing',
    'monitoring',
    'data_retention',
    'disaster_recovery'
]

# Target spec count per category for 100% maturity
CATEGORY_TARGETS = {
    'goals': 10,
    'requirements': 15,
    'tech_stack': 12,
    'scalability': 8,
    'security': 10,
    'performance': 8,
    'testing': 8,
    'monitoring': 6,
    'data_retention': 5,
    'disaster_recovery': 8
}


class SocraticCounselorAgent(BaseAgent):
    """
    SocraticCounselorAgent - Generates Socratic questions to gather requirements.

    Capabilities:
    - generate_question: Generate next question based on project context
    - generate_questions_batch: Generate multiple questions at once
    """

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

            # Calculate coverage per category
            coverage = self._calculate_coverage(existing_specs)  # TODO Expected type 'list[Specification]', got 'list[Type[Specification]]' instead

            # Identify next category to focus on (lowest coverage)
            next_category = self._identify_next_category(coverage)

            # Get user learning profile for personalization
            user_behavior_patterns = {}
            try:
                from .orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                learning_result = orchestrator.route_request(
                    'learning',
                    'get_user_profile',
                    {'user_id': str(project.user_id)}
                )
                if learning_result.get('success'):
                    user_behavior_patterns = {
                        'patterns': learning_result.get('behavior_patterns', []),
                        'total_questions_asked': learning_result.get('total_questions_asked', 0),
                        'overall_response_quality': learning_result.get('overall_response_quality', 0.5)
                    }
                    self.logger.debug(f"Retrieved user learning profile: {len(user_behavior_patterns.get('patterns', []))} patterns, {user_behavior_patterns['total_questions_asked']} questions asked")
            except Exception as e:
                self.logger.warning(f"Could not retrieve user learning profile: {e}")
                user_behavior_patterns = {}

            # Build prompt for Claude with user learning context
            prompt = self._build_question_generation_prompt(
                project, existing_specs, previous_questions, next_category, user_behavior_patterns  # TODO Expected type 'list[Specification]', got 'list[Type[Specification]]' instead
            )

            # Call Claude API (separate from DB transaction)
            try:
                self.logger.debug(f"Calling Claude API to generate question for project {project_id}, category: {next_category}")
                model_name = "claude-sonnet-4-5-20250929"
                response = self.services.get_claude_client().messages.create(
                    model=model_name,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract text from response
                response_text = response.content[0].text
                self.logger.debug(f"Claude API response received: {len(response_text)} chars")
                self.logger.debug(f"Response text preview (first 200 chars): {response_text[:200]}")

                # Strip markdown code fences if present (Claude sometimes wraps in ```json ... ```)
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.startswith('```'):
                    response_text = response_text[3:]  # Remove ```
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove ```

                response_text = response_text.strip()

                self.logger.debug(f"Cleaned response text preview (first 100 chars): {response_text[:100]}")

                # Parse JSON response
                question_data = json.loads(response_text)

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Claude response as JSON: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': 'Failed to parse question from Claude API',
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

    def _calculate_coverage(self, specs: List[Specification]) -> Dict[str, float]:
        """
        Calculate coverage percentage per category.

        Args:
            specs: List of current specifications

        Returns:
            Dictionary mapping category to coverage percentage (0-100)
        """
        # Count specs per category
        spec_counts = {}
        for spec in specs:
            category = spec.category
            spec_counts[category] = spec_counts.get(category, 0) + 1

        # Calculate coverage percentage
        coverage = {}
        for category in QUESTION_CATEGORIES:
            target = CATEGORY_TARGETS[category]
            count = spec_counts.get(category, 0)
            coverage[category] = min(count / target, 1.0) * 100

        return coverage

    def _identify_next_category(self, coverage: Dict[str, float]) -> str:
        """
        Identify category with lowest coverage.

        Args:
            coverage: Dictionary mapping category to coverage percentage

        Returns:
            Category name with lowest coverage
        """
        if not coverage:
            return 'goals'  # Start with goals

        # Find category with lowest coverage
        return min(coverage, key=coverage.get)

    def _build_question_generation_prompt(
        self,
        project: Project,
        specs: List[Specification],
        previous_questions: List[Question],
        next_category: str,
        user_behavior_patterns: Dict[str, Any] = None
    ) -> str:
        """
        Build prompt for Claude to generate question.

        Args:
            project: Project instance
            specs: List of existing specifications
            previous_questions: List of previous questions
            next_category: Category to focus on
            user_behavior_patterns: Optional user learning profile

        Returns:
            Prompt string for Claude API
        """
        user_behavior_patterns = user_behavior_patterns or {}

        # Format user learning context if available
        user_learning_context = ""
        if user_behavior_patterns:
            total_q = user_behavior_patterns.get('total_questions_asked', 0)
            quality = user_behavior_patterns.get('overall_response_quality', 0.5)
            if total_q > 0:
                user_learning_context = f"""
USER LEARNING PROFILE:
- Experience: {total_q} questions answered previously
- Response quality: {quality:.0%}
- Known patterns: {len(user_behavior_patterns.get('patterns', []))} learned behavior patterns

Adapt your question style based on this user's experience level and communication style.
"""

        prompt = f"""You are a Socratic counselor helping gather requirements for a software project.

PROJECT CONTEXT:
- Name: {project.name}
- Description: {project.description or 'None provided yet'}
- Phase: {project.current_phase}
- Maturity: {project.maturity_score}%

EXISTING SPECIFICATIONS:
{self._format_specs(specs)}

PREVIOUS QUESTIONS ASKED:
{self._format_questions(previous_questions)}
{user_learning_context}
NEXT FOCUS AREA: {next_category}

TASK:
Generate the next question focusing on: {next_category}

REQUIREMENTS:
1. Ask about ONE specific aspect of {next_category}
2. Keep question concise and clear (max 2 sentences)
3. Avoid assuming solutions (no "should we use X?" questions)
4. Make it open-ended to encourage detailed answers
5. Provide context about why this question matters
6. Do NOT repeat or rephrase previous questions

IMPORTANT:
- If user hasn't described their project yet, ask about project goals/purpose
- If basic goals are known, ask progressively deeper questions
- Focus on understanding WHAT they want, not HOW to build it (yet)

Return ONLY valid JSON in this EXACT format (no additional text):
{{
  "text": "the question text",
  "category": "{next_category}",
  "context": "brief explanation of why this question matters"
}}"""

        return prompt

    def _format_specs(self, specs: List[Specification]) -> str:
        """
        Format specifications for prompt.

        Args:
            specs: List of specifications

        Returns:
            Formatted string of specifications
        """
        if not specs:
            return "None yet - this is the first interaction"

        lines = []
        for spec in specs[:20]:  # Limit to prevent huge prompts
            lines.append(f"- [{spec.category}] {spec.content}")

        return "\n".join(lines)

    def _format_questions(self, questions: List[Question]) -> str:
        """
        Format previous questions for prompt.

        Args:
            questions: List of previous questions

        Returns:
            Formatted string of questions
        """
        if not questions:
            return "None yet - this is the first question"

        lines = []
        for q in questions[:10]:  # Limit to most recent 10
            lines.append(f"- [{q.category}] {q.text}")

        return "\n".join(lines)
