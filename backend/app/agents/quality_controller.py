"""
QualityControllerAgent - Implements quality control and anti-greedy algorithm gates.

This agent prevents greedy algorithm decisions by:
1. Detecting bias in questions
2. Analyzing coverage gaps
3. Recommending optimal paths
4. Blocking operations that fail quality checks
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any

from ..models import Project, Specification, QualityMetric
from .base import BaseAgent


class QualityControllerAgent(BaseAgent):
    """
    Quality Control Agent - prevents greedy algorithm decisions.

    Capabilities:
    - analyze_question: Detect bias in questions
    - analyze_coverage: Check if all categories adequately covered
    - compare_paths: Recommend optimal path (thorough vs. greedy)
    - get_quality_metrics: Get quality metrics for a project
    - verify_operation: Verify if operation should proceed (used by orchestrator)
    """

    def __init__(self, agent_id: str, name: str, services=None):
        """Initialize Quality Controller Agent"""
        super().__init__(agent_id, name, services)
        self.logger = logging.getLogger(__name__)

        # Bias detection patterns
        self.solution_bias = ["should we use", "let's use", "we need to use", "you should use"]
        self.technology_bias = ["best framework", "industry standard", "everyone uses", "standard practice"]
        self.leading_patterns = ["you need", "obviously", "clearly", "of course", "the only way"]

        # Coverage categories and minimum specs per category
        self.coverage_categories = [
            'goals', 'requirements', 'tech_stack', 'users',
            'scalability', 'security', 'deployment', 'testing',
            'timeline', 'constraints'
        ]
        self.min_specs_per_category = 3

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            'analyze_question',
            'analyze_coverage',
            'compare_paths',
            'get_quality_metrics',
            'verify_operation'
        ]

    def _analyze_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze question for bias.

        Args:
            data: {
                'question_text': str,
                'project_id': UUID (optional)
            }

        Returns:
            {
                'success': bool,
                'is_blocking': bool,
                'bias_score': float (0.0-1.0),
                'bias_types': List[str],
                'reason': str (if blocking),
                'suggested_alternatives': List[str] (if blocking)
            }
        """
        question_text = data['question_text'].lower()
        project_id = data.get('project_id')

        # Detect different types of bias
        bias_types = []
        bias_count = 0

        # Check for solution bias
        solution_bias_count = sum(1 for pattern in self.solution_bias if pattern in question_text)
        if solution_bias_count > 0:
            bias_types.append('solution_bias')
            bias_count += solution_bias_count

        # Check for technology bias
        tech_bias_count = sum(1 for pattern in self.technology_bias if pattern in question_text)
        if tech_bias_count > 0:
            bias_types.append('technology_bias')
            bias_count += tech_bias_count

        # Check for leading questions
        leading_count = sum(1 for pattern in self.leading_patterns if pattern in question_text)
        if leading_count > 0:
            bias_types.append('leading_question')
            bias_count += leading_count

        # Calculate bias score (0.0 = no bias, 1.0 = extreme bias)
        bias_score = min(1.0, bias_count * 0.3)

        # Store quality metric if project_id provided
        if project_id:
            specs_session = None
            try:
                specs_session = self.services.get_database_specs()
                metric = QualityMetric(
                    project_id=project_id,
                    metric_type='question_bias',
                    metric_value=Decimal(str(bias_score)),
                    threshold=Decimal('0.5'),
                    passed=(bias_score <= 0.5),
                    details={
                        'question_text': data['question_text'],
                        'bias_types': bias_types,
                        'bias_count': bias_count
                    },
                    calculated_at=datetime.now(timezone.utc)
                )
                specs_session.add(metric)
                specs_session.commit()
                self.logger.debug(f"Stored quality metric for project {project_id}: bias_score={bias_score:.2f}")
            except Exception as e:
                self.logger.error(f"Error storing quality metric: {e}", exc_info=True)
                if specs_session:
                    specs_session.rollback()
                # Don't fail the operation if metric storage fails
            finally:
                if specs_session:
                    specs_session.close()

        # Block if bias score too high
        if bias_score > 0.5:
            alternatives = self._generate_unbiased_alternatives(question_text)
            self.logger.warning(f"Question blocked due to high bias score: {bias_score:.2f}")
            return {
                'success': False,
                'is_blocking': True,
                'bias_score': bias_score,
                'bias_types': bias_types,
                'reason': f'Question has excessive bias (score: {bias_score:.2f}). Detected: {", ".join(bias_types)}',
                'suggested_alternatives': alternatives
            }

        return {
            'success': True,
            'is_blocking': False,
            'bias_score': bias_score,
            'bias_types': bias_types,
            'quality_score': 1.0 - bias_score
        }

    def _analyze_coverage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if all categories are adequately covered.

        Args:
            data: {'project_id': UUID}

        Returns:
            {
                'success': bool,
                'is_blocking': bool,
                'coverage': Dict[str, int],  # category -> spec count
                'coverage_gaps': List[str],  # categories with < 3 specs
                'coverage_score': float (0.0-1.0),
                'reason': str (if blocking),
                'suggested_actions': List[str] (if blocking)
            }
        """
        project_id = data['project_id']
        specs_session = None

        try:
            specs_session = self.services.get_database_specs()

            # Get all specifications for this project
            specs = specs_session.query(Specification).filter_by(
                project_id=project_id
            ).all()

            # Calculate coverage per category
            coverage = {}
            for category in self.coverage_categories:
                category_specs = [s for s in specs if s.category == category]
                coverage[category] = len(category_specs)

            # Identify coverage gaps (< min specs)
            coverage_gaps = [
                cat for cat, count in coverage.items()
                if count < self.min_specs_per_category
            ]

            # Calculate overall coverage score
            total_possible = len(self.coverage_categories) * self.min_specs_per_category
            total_actual = sum(min(count, self.min_specs_per_category) for count in coverage.values())
            coverage_score = total_actual / total_possible if total_possible > 0 else 0.0

            # Store quality metric
            metric = QualityMetric(
                project_id=project_id,
                metric_type='coverage',
                metric_value=Decimal(str(coverage_score)),
                threshold=Decimal('0.7'),
                passed=(coverage_score >= 0.7),
                details={
                    'coverage': coverage,
                    'coverage_gaps': coverage_gaps
                },
                calculated_at=datetime.now(timezone.utc)
            )
            specs_session.add(metric)
            specs_session.commit()

            self.logger.debug(f"Analyzed coverage for project {project_id}: score={coverage_score:.2f}")

            # Block if too many gaps (< 70% coverage)
            if coverage_score < 0.7:
                suggested_actions = [
                    f"Ask questions about: {gap}" for gap in coverage_gaps[:3]
                ]
                self.logger.warning(f"Coverage insufficient for project {project_id}: {coverage_score:.0%}")
                return {
                    'success': False,
                    'is_blocking': True,
                    'coverage': coverage,
                    'coverage_gaps': coverage_gaps,
                    'coverage_score': coverage_score,
                    'reason': f'Insufficient coverage ({coverage_score:.0%}). Gaps: {", ".join(coverage_gaps[:5])}',
                    'suggested_actions': suggested_actions
                }

            return {
                'success': True,
                'is_blocking': False,
                'coverage': coverage,
                'coverage_gaps': coverage_gaps,
                'coverage_score': coverage_score
            }

        except Exception as e:
            self.logger.error(f"Error analyzing coverage for project {project_id}: {e}", exc_info=True)
            if specs_session:
                specs_session.rollback()
            return {
                'success': False,
                'error': f'Failed to analyze coverage: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if specs_session:
                specs_session.close()

    def _compare_paths(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare possible paths and recommend best one.

        Args:
            data: {
                'goal': str,  # e.g., 'generate_code'
                'project_id': UUID
            }

        Returns:
            {
                'success': bool,
                'paths': List[dict],  # All possible paths
                'recommended_path': dict,  # Best path
                'recommendation_reason': str
            }
        """
        goal = data['goal']
        project_id = data['project_id']
        specs_session = None

        try:
            specs_session = self.services.get_database_specs()

            # Get current project maturity
            project = specs_session.query(Project).get(project_id)
            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                return {
                    'success': False,
                    'error': 'Project not found',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            maturity_score = project.maturity_score

            # Define possible paths
            paths = []

            if goal == 'generate_code':
                # Thorough path: Complete specs -> Design -> Generate
                thorough_path = {
                    'id': 'thorough',
                    'name': 'Thorough Approach',
                    'steps': [
                        {'action': 'complete_specifications', 'estimated_tokens': 800},
                        {'action': 'design_architecture', 'estimated_tokens': 1200},
                        {'action': 'generate_code', 'estimated_tokens': 5000},
                        {'action': 'test_code', 'estimated_tokens': 1000}
                    ],
                    'direct_cost_tokens': 8000,
                    'rework_cost_tokens': 0 if maturity_score >= 80 else 2000,
                    'total_cost_tokens': 8000 if maturity_score >= 80 else 10000,
                    'risk': 'LOW' if maturity_score >= 80 else 'MEDIUM',
                    'confidence': 0.95 if maturity_score >= 80 else 0.75
                }
                paths.append(thorough_path)

                # Greedy path: Generate immediately
                greedy_path = {
                    'id': 'greedy',
                    'name': 'Greedy Approach (Skip Specs)',
                    'steps': [
                        {'action': 'generate_code', 'estimated_tokens': 5000}
                    ],
                    'direct_cost_tokens': 5000,
                    'rework_cost_tokens': 5000 if maturity_score < 80 else 2000,
                    'total_cost_tokens': 10000 if maturity_score < 80 else 7000,
                    'risk': 'HIGH' if maturity_score < 80 else 'MEDIUM',
                    'confidence': 0.4 if maturity_score < 80 else 0.65
                }
                paths.append(greedy_path)

            # Recommend lowest total cost with acceptable risk
            # Filter out high-risk paths if maturity is low
            acceptable_paths = [
                p for p in paths
                if not (p['risk'] == 'HIGH' and maturity_score < 80)
            ]

            if not acceptable_paths:
                acceptable_paths = paths  # Fallback to all paths

            recommended = min(acceptable_paths, key=lambda p: p['total_cost_tokens'])

            recommendation_reason = (
                f"Based on {maturity_score}% maturity, the {recommended['name']} "
                f"minimizes total cost ({recommended['total_cost_tokens']} tokens) "
                f"with {recommended['risk']} risk and {recommended['confidence']:.0%} confidence."
            )

            # Store quality metric
            metric = QualityMetric(
                project_id=project_id,
                metric_type='path_optimization',
                metric_value=Decimal(str(recommended['total_cost_tokens'])),
                threshold=Decimal('10000'),
                passed=(recommended['total_cost_tokens'] <= 10000),
                details={
                    'goal': goal,
                    'paths': paths,
                    'recommended_path_id': recommended['id'],
                    'maturity_score': maturity_score
                },
                calculated_at=datetime.now(timezone.utc)
            )
            specs_session.add(metric)
            specs_session.commit()

            self.logger.debug(f"Path optimization for project {project_id}: recommended {recommended['id']}")

            return {
                'success': True,
                'paths': paths,
                'recommended_path': recommended,
                'recommendation_reason': recommendation_reason
            }

        except Exception as e:
            self.logger.error(f"Error comparing paths for project {project_id}: {e}", exc_info=True)
            if specs_session:
                specs_session.rollback()
            return {
                'success': False,
                'error': f'Failed to compare paths: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if specs_session:
                specs_session.close()

    def _get_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get quality metrics for a project.

        Args:
            data: {
                'project_id': UUID,
                'metric_type': str (optional - filter by type)
            }

        Returns:
            {
                'success': bool,
                'metrics': List[dict],
                'summary': dict
            }
        """
        project_id = data['project_id']
        metric_type = data.get('metric_type')
        specs_session = None

        try:
            specs_session = self.services.get_database_specs()

            # Query metrics
            query = specs_session.query(QualityMetric).filter_by(project_id=project_id)
            if metric_type:
                query = query.filter_by(metric_type=metric_type)

            metrics = query.order_by(QualityMetric.calculated_at.desc()).all()

            # Calculate summary
            total_metrics = len(metrics)
            passed_metrics = sum(1 for m in metrics if m.passed)
            pass_rate = (passed_metrics / total_metrics) if total_metrics > 0 else 0.0

            self.logger.debug(f"Retrieved {total_metrics} quality metrics for project {project_id}")

            return {
                'success': True,
                'metrics': [m.to_dict() for m in metrics],  # TODO Parameter 'self' unfilled
                'summary': {
                    'total_metrics': total_metrics,
                    'passed_metrics': passed_metrics,
                    'failed_metrics': total_metrics - passed_metrics,
                    'pass_rate': pass_rate
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting quality metrics for project {project_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to get quality metrics: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }

        finally:
            if specs_session:
                specs_session.close()

    def _verify_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify if an operation should proceed (used by orchestrator).

        Args:
            data: {
                'agent_id': str,
                'action': str,
                'operation_data': dict
            }

        Returns:
            {
                'success': bool,
                'is_blocking': bool,
                'reason': str (if blocking),
                'quality_checks': dict
            }
        """
        agent_id = data['agent_id']
        action = data['action']
        operation_data = data.get('operation_data', {})

        quality_checks = {}

        # Check: Question generation - analyze for bias
        if agent_id == 'socratic' and action == 'generate_question':
            if 'question_text' in operation_data:
                bias_check = self._analyze_question({
                    'question_text': operation_data['question_text'],
                    'project_id': operation_data.get('project_id')
                })
                quality_checks['bias_check'] = bias_check

                if bias_check.get('is_blocking'):
                    return {
                        'success': False,
                        'is_blocking': True,
                        'reason': bias_check['reason'],
                        'quality_checks': quality_checks
                    }

        # Check: Code generation - analyze coverage
        if agent_id == 'code' and action == 'generate_code':
            if 'project_id' in operation_data:
                coverage_check = self._analyze_coverage({
                    'project_id': operation_data['project_id']
                })
                quality_checks['coverage_check'] = coverage_check

                if coverage_check.get('is_blocking'):
                    return {
                        'success': False,
                        'is_blocking': True,
                        'reason': coverage_check['reason'],
                        'quality_checks': quality_checks
                    }

        return {
            'success': True,
            'is_blocking': False,
            'quality_checks': quality_checks
        }

    def _generate_unbiased_alternatives(self, question_text: str) -> List[str]:
        """Generate unbiased alternatives for a biased question"""
        # Simple heuristic alternatives
        alternatives = []

        if "should we use" in question_text:
            alternatives.append("What are your requirements for this component?")
            alternatives.append("What factors are important to you for this decision?")

        if "best framework" in question_text:
            alternatives.append("What framework are you most familiar with?")
            alternatives.append("What are your technical constraints?")

        if not alternatives:
            alternatives.append("Could you describe your requirements more specifically?")
            alternatives.append("What problem are you trying to solve?")

        return alternatives
