"""
ContextAnalyzerAgent - Extracts specifications from user answers.
"""
import json
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import and_

from ..core.action_logger import ActionLogger, log_specs
from ..models.project import Project
from ..models.question import Question
from ..models.session import Session
from ..models.specification import Specification
from .base import BaseAgent

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


class ContextAnalyzerAgent(BaseAgent):
    """
    ContextAnalyzerAgent - Extracts specifications from user answers.

    Capabilities:
    - extract_specifications: Extract specs from user answer to a question
    - analyze_context: Analyze conversation context (Phase 3)
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'extract_specifications',
            'analyze_context'
        ]

    def _extract_specifications(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specifications from user answer.

        REFACTORED: Database connection released BEFORE Claude API calls
        to prevent connection pool exhaustion during 10-20 second extraction.

        Args:
            data: {
                'session_id': str (UUID),
                'question_id': str (UUID),
                'answer': str,
                'user_id': str (UUID) - for audit
            }

        Returns:
            {
                'success': bool,
                'specs_extracted': int,
                'specifications': list,
                'maturity_score': float
            }
        """
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        answer = data.get('answer')

        # Validate
        if not all([session_id, question_id, answer]):
            self.logger.warning("Validation error: missing session_id, question_id, or answer")
            return {
                'success': False,
                'error': 'session_id, question_id, and answer are required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None

        try:
            # PHASE 1: Load all data from database (quick operation)
            db = self.services.get_database_specs()

            # Load context
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                self.logger.warning(f"Session not found: {session_id}")
                db.close()
                return {
                    'success': False,
                    'error': f'Session not found: {session_id}',
                    'error_code': 'SESSION_NOT_FOUND'
                }

            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                self.logger.warning(f"Question not found: {question_id}")
                db.close()
                return {
                    'success': False,
                    'error': f'Question not found: {question_id}',
                    'error_code': 'QUESTION_NOT_FOUND'
                }

            project = db.query(Project).filter(Project.id == session.project_id).first()
            if not project:
                self.logger.warning(f"Project not found: {session.project_id}")
                db.close()
                return {
                    'success': False,
                    'error': f'Project not found: {session.project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            # Load existing specs (limit to recent for performance)
            existing_specs = db.query(Specification).filter(
                and_(
                    Specification.project_id == project.id,
                    Specification.is_current == True
                )
            ).order_by(Specification.created_at.desc()).limit(100).all()

            # Convert to dicts for use after DB closes
            project_data = {
                'id': str(project.id),
                'name': project.name,
                'maturity_score': project.maturity_score
            }
            question_data = {
                'id': str(question.id),
                'text': question.text,
                'category': question.category
            }
            existing_specs_data = [
                {
                    'category': spec.category,
                    'content': spec.content
                }
                for spec in existing_specs
            ]

            # Build extraction prompt
            prompt = self._build_extraction_prompt(question, answer, existing_specs)

            # CRITICAL: Close DB connection BEFORE Claude API call
            db.close()
            self.logger.debug(f"Database connection closed before Claude API call for extraction")

            # PHASE 2: Call Claude API (NO DATABASE CONNECTION HELD!)
            extracted_specs = []
            try:
                self.logger.debug(f"Calling Claude API to extract specs from answer (question: {question_id})")
                response = self.services.get_claude_client().messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract text from response
                response_text = response.content[0].text
                self.logger.debug(f"Claude API response received: {len(response_text)} chars (DB still released)")

                # Handle markdown-wrapped JSON (Claude sometimes wraps JSON in ```json...``` blocks)
                if response_text.startswith("```"):
                    # Extract JSON from markdown code block
                    lines = response_text.split("\n")
                    json_lines = []
                    in_json_block = False
                    for line in lines:
                        if line.startswith("```json"):
                            in_json_block = True
                            continue
                        elif line.startswith("```"):
                            in_json_block = False
                            continue
                        if in_json_block:
                            json_lines.append(line)
                    response_text = "\n".join(json_lines)

                # Parse JSON response
                extracted_specs = json.loads(response_text)

                # Ensure it's a list
                if not isinstance(extracted_specs, list):
                    raise ValueError("Expected list of specifications")

                self.logger.info(f"Claude extracted {len(extracted_specs)} specifications")

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Claude response as JSON: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': 'Failed to parse specifications from Claude API response',
                    'error_code': 'PARSE_ERROR'
                }
            except Exception as e:
                self.logger.error(f"Claude API error: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Claude API error: {str(e)}',
                    'error_code': 'API_ERROR'
                }

            # PHASE 3: Check for conflicts (with released DB connection)
            # Convert extracted specs to format expected by conflict detector
            specs_for_conflict_check = []
            for spec_data in extracted_specs:
                # Use key/value if provided, otherwise fallback to content
                conflict_key = spec_data.get('key')
                conflict_value = spec_data.get('value')

                if not conflict_key or not conflict_value:
                    # Fallback for backward compatibility
                    content = spec_data.get('content', '')
                    conflict_key = conflict_key or content[:50]
                    conflict_value = conflict_value or content

                specs_for_conflict_check.append({
                    'category': spec_data.get('category', question_data['category']),
                    'key': conflict_key,
                    'value': conflict_value,
                    'confidence': spec_data.get('confidence', 0.9)
                })

            # Get orchestrator and check for conflicts (no DB connection held)
            conflicts_detected = False
            conflicts_list = []
            try:
                from .orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                conflict_result = orchestrator.route_request(
                    agent_id='conflict',
                    action='detect_conflicts',
                    data={
                        'project_id': str(project_data['id']),
                        'new_specs': specs_for_conflict_check,
                        'source_id': str(question_id)
                    }
                )

                # If conflicts detected, return them without saving
                if conflict_result.get('conflicts_detected'):
                    self.logger.warning(
                        f"Conflicts detected for project {project_data['id']}: "
                        f"{len(conflict_result.get('conflicts', []))} conflicts"
                    )
                    conflicts_detected = True
                    conflicts_list = conflict_result.get('conflicts', [])

            except Exception as e:
                # Conflict detection failed, but we can still proceed
                self.logger.warning(f"Conflict detection failed, proceeding anyway: {e}")

            # If conflicts detected, return before saving
            if conflicts_detected:
                return {
                    'success': False,
                    'conflicts_detected': True,
                    'conflicts': conflicts_list,
                    'message': 'Specifications contain conflicts. Please resolve before proceeding.',
                    'specs_extracted': 0
                }

            # PHASE 4: Process results (no DB needed)
            processed_specs = []
            for spec_data in extracted_specs:
                # Extract key and value with fallback for backward compatibility
                spec_key = spec_data.get('key')
                spec_value = spec_data.get('value')

                # Fallback: if Claude didn't provide key/value, generate from content
                if not spec_key or not spec_value:
                    content = spec_data.get('content', '')
                    # Generate key from first few words
                    key_words = content[:50].lower().replace(' ', '_')
                    key_words = ''.join(c for c in key_words if c.isalnum() or c == '_')
                    spec_key = spec_key or key_words or f"spec_{question_data['category']}"
                    spec_value = spec_value or content or spec_key

                processed_specs.append({
                    'category': spec_data.get('category', question_data['category']),
                    'key': spec_key,
                    'value': spec_value,
                    'content': spec_data.get('content'),
                    'confidence': spec_data.get('confidence', 0.9),
                    'reasoning': spec_data.get('reasoning')
                })

            # PHASE 5: Save to database (new connection)
            db = self.services.get_database_specs()

            saved_specs = []
            for spec_data in processed_specs:
                spec = Specification(
                    project_id=project_data['id'],
                    session_id=session_id,
                    category=spec_data['category'],
                    key=spec_data['key'],
                    value=spec_data['value'],
                    content=spec_data['content'],
                    source='extracted',
                    confidence=Decimal(str(spec_data['confidence'])),
                    is_current=True,
                    spec_metadata={
                        'question_id': str(question_id),
                        'reasoning': spec_data['reasoning']
                    }
                )
                db.add(spec)
                saved_specs.append(spec)

            # Commit all specifications
            db.commit()
            self.logger.info(f"Saved {len(saved_specs)} specifications to database")

            # Log specs extraction
            log_specs(
                "Specifications extracted and saved",
                count=len(saved_specs),
                success=True,
                question_category=question_data['category']
            )

            # Refresh to get IDs
            for spec in saved_specs:
                db.refresh(spec)

            # Update maturity score (need fresh project query)
            project = db.query(Project).filter(Project.id == project_data['id']).first()
            old_maturity = project.maturity_score
            new_maturity = self._calculate_maturity(project_data['id'], db)
            project.maturity_score = new_maturity
            db.commit()
            db.close()

            self.logger.info(
                f"Extracted {len(saved_specs)} specs from answer to question {question_id}. "
                f"Maturity: {old_maturity}% -> {new_maturity}% (DB connection now released)"
            )

            # Log maturity update
            ActionLogger.progress(
                100, 100,
                f"Project maturity updated: {old_maturity}% → {new_maturity}%",
                specs=len(saved_specs)
            )

            return {
                'success': True,
                'specs_extracted': len(saved_specs),
                'specifications': [s.to_dict() for s in saved_specs],
                'maturity_score': float(new_maturity)
            }

        except Exception as e:
            self.logger.error(f"Error extracting specifications: {e}", exc_info=True)
            # Attempt to close DB if still open
            try:
                if db and hasattr(db, 'is_active') and db.is_active:
                    db.rollback()
                    db.close()
            except Exception as cleanup_error:
                self.logger.debug(f"Error during exception cleanup: {cleanup_error}")

            return {
                'success': False,
                'error': f'Failed to extract specifications: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            pass  # Session managed by caller/dependency injection

    def _analyze_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze conversation context.
        (Placeholder for Phase 3 expansion)

        Args:
            data: {
                'session_id': str (UUID)
            }

        Returns:
            {'success': bool, 'analysis': dict}
        """
        session_id = data.get('session_id')

        if not session_id:
            return {
                'success': False,
                'error': 'session_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # TODO: Phase 3 - Implement context analysis
        return {
            'success': True,
            'analysis': {
                'message': 'Context analysis will be implemented in Phase 3'
            }
        }

    def _build_extraction_prompt(
        self,
        question: Question,
        answer: str,
        existing_specs: List[Specification]
    ) -> str:
        """
        Build prompt for specification extraction.

        Args:
            question: Question instance
            answer: User's answer
            existing_specs: List of existing specifications

        Returns:
            Prompt string for Claude API
        """
        prompt = f"""Extract structured specifications from the user's answer to a question.

QUESTION ASKED:
"{question.text}"

QUESTION CATEGORY: {question.category}

USER ANSWER:
"{answer}"

EXISTING SPECIFICATIONS:
{self._format_existing_specs(existing_specs[:30])}

TASK:
Extract ALL specifications mentioned in the answer. Be thorough - extract:
- Explicit statements (user directly said X)
- Implied requirements (user mentioned Y, which implies Z)
- Technical choices (user wants to use technology T)
- Constraints (user mentioned limitation L)

Return ONLY valid JSON array (no additional text):
[
  {{
    "category": "appropriate_category",
    "key": "short_identifier_snake_case",
    "value": "the_specification_value",
    "content": "clear, specific specification statement (optional detailed notes)",
    "confidence": 0.X,
    "reasoning": "why this was extracted and how confident we are"
  }}
]

KEY/VALUE FORMAT:
- key: Short identifier (3-5 words, snake_case, e.g., "concurrent_users_target")
- value: The actual specification value (e.g., "2 concurrent users", "PostgreSQL 17", "JWT tokens")
- content: Optional detailed notes or context (can be same as value if no additional details)

CATEGORIES:
- goals: Project purpose, objectives, success criteria
- requirements: Functional and non-functional requirements
- tech_stack: Technologies, frameworks, languages
- scalability: Load handling, growth expectations
- security: Authentication, authorization, data protection
- performance: Speed, latency, throughput requirements
- testing: Testing strategy, coverage requirements
- monitoring: Logging, metrics, alerting
- data_retention: Data storage, backup, retention policies
- disaster_recovery: Failover, redundancy, recovery plans

CONFIDENCE SCORES:
- 1.0: User explicitly stated this
- 0.8-0.9: Strongly implied by user's answer
- 0.6-0.7: Reasonable inference from context
- 0.4-0.5: Weak inference, might need confirmation

IMPORTANT:
- Include EVERY piece of information, even if small
- Use category that best fits (may differ from question category)
- Be specific in content (avoid vague statements)
- If answer provides no extractable specs, return empty array []
"""

        return prompt

    def _format_existing_specs(self, specs: List[Specification]) -> str:
        """
        Format existing specifications for prompt.

        Args:
            specs: List of specifications

        Returns:
            Formatted string
        """
        if not specs:
            return "None yet - this is the first specification extraction"

        lines = []
        for spec in specs:
            lines.append(f"- [{spec.category}] {spec.content}")

        return "\n".join(lines)

    def _calculate_maturity(self, project_id: str, db) -> int:
        """
        Calculate project maturity based on specification coverage.

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            Maturity score (0-100)
        """
        specs = db.query(Specification).filter(
            Specification.project_id == project_id,
            Specification.is_current == True
        ).all()

        # Count per category with confidence weighting
        category_scores = {}
        for spec in specs:
            category = spec.category
            if category not in category_scores:
                category_scores[category] = 0

            # Add confidence-weighted score
            confidence = float(spec.confidence) if spec.confidence else 0.9
            category_scores[category] += confidence

        # Calculate weighted maturity
        total_weight = sum(CATEGORY_TARGETS.values())  # 90
        total_score = 0

        for category, max_score in CATEGORY_TARGETS.items():
            score = min(category_scores.get(category, 0), max_score)
            total_score += score

        maturity = (total_score / total_weight) * 100
        return round(maturity)
