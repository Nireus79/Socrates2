"""
UserLearningAgent - Learns user behavior patterns and adapts question selection.

This agent orchestrates the user learning process:
1. Loads data from databases
2. Converts to plain data models
3. Uses LearningEngine core engine for business logic
4. Saves results back to database

The pure business logic (behavior analysis, metrics calculation)
is handled by the LearningEngine in the Socrates library.
This separation enables testing without database and library extraction.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any
import json

from ..models import UserBehaviorPattern, QuestionEffectiveness, KnowledgeBaseDocument, Project
from .base import BaseAgent
# Import from Socrates library instead of local core
from socrates import LearningEngine
from socrates import UserBehaviorData


class UserLearningAgent(BaseAgent):
    """
    User Learning Agent - learns and adapts to user behavior.

    Capabilities:
    - track_question_effectiveness: Track how effective questions are for each user
    - learn_behavior_pattern: Learn or update user behavior patterns
    - recommend_next_question: Recommend best question based on learned data
    - upload_knowledge_document: Upload and process knowledge base documents
    - get_user_profile: Get complete user learning profile

    Architecture:
    - This agent handles: Database I/O, API orchestration, validation, persistence
    - LearningEngine handles: Behavior analysis, metrics calculation, personalization
    - Clear separation enables testing without database and library extraction
    """

    def __init__(self, agent_id: str = 'learning', name: str = 'User Learning', services=None):
        """Initialize agent with learning engine"""
        super().__init__(agent_id, name, services)
        self.learning_engine = LearningEngine(self.logger)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            'track_question_effectiveness',
            'learn_behavior_pattern',
            'recommend_next_question',
            'upload_knowledge_document',
            'get_user_profile'
        ]

    def _track_question_effectiveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track how effective a question was for the user.

        Args:
            data: {
                'user_id': UUID,
                'question_template_id': str,
                'role': str (PM, BA, UX, etc.),
                'answer_length': int,
                'specs_extracted': int,
                'answer_quality': float (0-1)
            }

        Returns:
            {'success': bool, 'effectiveness_score': float}
        """
        user_id = data['user_id']
        question_template_id = data['question_template_id']
        role = data['role']
        specs_session = self.services.get_database_specs()

        # Query existing effectiveness record
        effectiveness = specs_session.query(QuestionEffectiveness).filter_by(
            user_id=user_id,
            question_template_id=question_template_id
        ).first()

        if not effectiveness:
            # Create new effectiveness record
            effectiveness = QuestionEffectiveness(
                user_id=user_id,
                question_template_id=question_template_id,
                role=role,
                times_asked=0,
                times_answered_well=0,
                average_answer_length=0,
                average_spec_extraction_count=Decimal('0.0'),
                effectiveness_score=Decimal('0.5')  # Start neutral
            )
            specs_session.add(effectiveness)

        # Update metrics
        effectiveness.times_asked += 1

        # Determine if answered well (extracted specs + good quality)
        answered_well = (
            data['specs_extracted'] > 0 and
            data['answer_quality'] > 0.6
        )
        if answered_well:
            effectiveness.times_answered_well += 1

        # Update averages (exponential moving average)
        alpha = 0.3  # Learning rate
        effectiveness.average_answer_length = int(
            alpha * data['answer_length'] +
            (1 - alpha) * (effectiveness.average_answer_length or 0)
        )
        effectiveness.average_spec_extraction_count = Decimal(str(
            alpha * data['specs_extracted'] +
            (1 - alpha) * float(effectiveness.average_spec_extraction_count)
        ))

        # Calculate effectiveness score (0-1)
        effectiveness.effectiveness_score = Decimal(str(
            effectiveness.times_answered_well / effectiveness.times_asked
            if effectiveness.times_asked > 0 else 0.5
        ))

        effectiveness.last_asked_at = datetime.now(timezone.utc)
        effectiveness.updated_at = datetime.now(timezone.utc)

        specs_session.commit()

        return {
            'success': True,
            'effectiveness_score': float(effectiveness.effectiveness_score),
            'times_asked': effectiveness.times_asked,
            'times_answered_well': effectiveness.times_answered_well
        }

    def _learn_behavior_pattern(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn or update user behavior pattern.

        Args:
            data: {
                'user_id': UUID,
                'pattern_type': str (communication_style, detail_level, etc.),
                'pattern_data': dict,
                'confidence': float (0-1),
                'project_id': UUID
            }

        Returns:
            {'success': bool, 'pattern_id': UUID}
        """
        user_id = data['user_id']
        pattern_type = data['pattern_type']
        specs_session = self.services.get_database_specs()

        # Query existing pattern
        pattern = specs_session.query(UserBehaviorPattern).filter_by(
            user_id=user_id,
            pattern_type=pattern_type
        ).first()

        if pattern:
            # Update existing pattern
            pattern.pattern_data = self._merge_pattern_data(
                pattern.pattern_data,
                data['pattern_data']
            )
            pattern.confidence = Decimal(str(min(
                1.0,
                float(pattern.confidence) + 0.1  # Increase confidence
            )))

            # Add project to learned_from list
            current_projects = pattern.learned_from_projects or []
            if data['project_id'] not in current_projects:
                pattern.learned_from_projects = current_projects + [data['project_id']]

            pattern.updated_at = datetime.now(timezone.utc)
        else:
            # Create new pattern
            pattern = UserBehaviorPattern(
                user_id=user_id,
                pattern_type=pattern_type,
                pattern_data=data['pattern_data'],
                confidence=Decimal(str(data['confidence'])),
                learned_from_projects=[data['project_id']],
                learned_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            specs_session.add(pattern)

        specs_session.commit()

        return {
            'success': True,
            'pattern_id': str(pattern.id),
            'confidence': float(pattern.confidence)
        }

    def _recommend_next_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend next question based on user learning.

        Args:
            data: {
                'user_id': UUID,
                'project_id': UUID,
                'available_questions': List[dict]
            }

        Returns:
            {
                'success': bool,
                'recommended_question': dict,
                'reason': str
            }
        """
        user_id = data['user_id']
        available_questions = data.get('available_questions', [])
        specs_session = self.services.get_database_specs()

        # Load user's question effectiveness data
        effectiveness_records = specs_session.query(QuestionEffectiveness).filter_by(
            user_id=user_id
        ).all()

        # Score each available question
        scored_questions = []
        for question in available_questions:
            # Find effectiveness record for this question
            effectiveness = next(
                (e for e in effectiveness_records
                 if e.question_template_id == question.get('template_id')),
                None
            )

            if effectiveness:
                # Use learned effectiveness score
                score = float(effectiveness.effectiveness_score) if effectiveness.effectiveness_score else 0.5
            else:
                # No data yet, use neutral score
                score = 0.5

            scored_questions.append({
                'question': question,
                'score': score,
                'times_asked': effectiveness.times_asked if effectiveness else 0
            })

        # Sort by score (descending)
        scored_questions.sort(key=lambda x: x['score'], reverse=True)

        if scored_questions:
            best = scored_questions[0]
            return {
                'success': True,
                'recommended_question': best['question'],
                'effectiveness_score': best['score'],
                'reason': f"This question has {best['score']:.0%} effectiveness based on {best['times_asked']} previous interactions"
            }

        return {
            'success': False,
            'error': 'No questions available'
        }

    def _upload_knowledge_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload and process knowledge base document.

        Args:
            data: {
                'project_id': UUID,
                'user_id': UUID,
                'filename': str,
                'content': str,
                'content_type': str,
                'file_size': int
            }

        Returns:
            {'success': bool, 'document_id': UUID}
        """
        project_id = data['project_id']
        user_id = data['user_id']
        filename = data['filename']
        content = data.get('content', '')
        content_type = data['content_type']
        file_size = data['file_size']
        specs_session = self.services.get_database_specs()

        # Create knowledge base document
        doc = KnowledgeBaseDocument(
            project_id=project_id,
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            content=content,
            embedding=None,  # TODO: Generate embedding using sentence transformer
            uploaded_at=datetime.now(timezone.utc)
        )
        specs_session.add(doc)
        specs_session.commit()

        return {
            'success': True,
            'document_id': str(doc.id),
            'filename': filename,
            'file_size': file_size
        }

    def _get_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get complete user learning profile.

        Args:
            data: {'user_id': UUID}

        Returns:
            {
                'success': bool,
                'user_id': UUID,
                'behavior_patterns': List[dict],
                'question_effectiveness': List[dict],
                'total_questions_asked': int,
                'overall_response_quality': float,
                'engagement_score': float,
                'learning_velocity': float,
                'personalization_hints': dict
            }
        """
        user_id = data['user_id']
        specs_session = self.services.get_database_specs()

        # Load behavior patterns and question effectiveness from database
        patterns = specs_session.query(UserBehaviorPattern).filter_by(
            user_id=user_id
        ).all()

        effectiveness = specs_session.query(QuestionEffectiveness).filter_by(
            user_id=user_id
        ).limit(100).all()

        # PHASE 1: Convert DB data to plain data models (for LearningEngine)
        # Extract data from effectiveness records to build user behavior
        questions_asked = [
            {
                'id': e.question_template_id,
                'times_asked': e.times_asked,
                'times_answered_well': e.times_answered_well
            }
            for e in effectiveness
        ]

        response_qualities = [
            float(e.effectiveness_score) if e.effectiveness_score else 0.5
            for e in effectiveness
        ]

        topic_interactions = [p.pattern_type for p in patterns] if patterns else []

        projects_completed = len(set(
            pid for p in patterns if p.learned_from_projects
            for pid in p.learned_from_projects
        ))

        # PHASE 2: Use LearningEngine for pure business logic
        # Build user behavior profile
        user_behavior = self.learning_engine.build_user_profile(
            user_id=str(user_id),
            questions_asked=questions_asked,
            responses_quality=response_qualities,
            topic_interactions=topic_interactions,
            projects_completed=projects_completed
        )

        # Calculate metrics using engine
        metrics = self.learning_engine.calculate_learning_metrics(user_behavior)

        # Get personalization hints
        hints = self.learning_engine.get_personalization_hints(user_behavior)

        # Return structured response with both database data and engine-calculated metrics
        return {
            'success': True,
            'user_id': str(user_id),
            'behavior_patterns': [p.to_dict() for p in patterns],
            'question_effectiveness': [e.to_dict() for e in effectiveness],
            'total_questions_asked': user_behavior.total_questions_asked,
            'overall_response_quality': user_behavior.overall_response_quality,
            'engagement_score': metrics['engagement_score'],
            'learning_velocity': metrics['learning_velocity'],
            'experience_level': metrics['experience_level'],
            'topics_explored': metrics['topics_explored'],
            'personalization_hints': hints
        }

    def _merge_pattern_data(self, existing: dict, new: dict) -> dict:
        """Merge new pattern data with existing (simple merge)"""
        merged = existing.copy()
        merged.update(new)
        return merged
