"""
Test Phase 5: Quality Control System

Tests the QualityControllerAgent and quality gates integration.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models import Project, Specification, QualityMetric
from app.agents.quality_controller import QualityControllerAgent


def test_analyze_question_detects_bias(specs_session, service_container):
    """Test that biased questions are detected and blocked"""
    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)

    # Test biased question
    result = quality_agent.process_request('analyze_question', {
        'question_text': 'Should we use React for the frontend? It is the best framework.'
    })

    assert result['success'] == False
    assert result['is_blocking'] == True
    assert result['bias_score'] > 0.5
    assert 'solution_bias' in result['bias_types'] or 'technology_bias' in result['bias_types']
    assert 'suggested_alternatives' in result
    assert len(result['suggested_alternatives']) > 0


def test_analyze_question_allows_unbiased(specs_session, service_container):
    """Test that unbiased questions are allowed"""
    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)

    # Test unbiased question
    result = quality_agent.process_request('analyze_question', {
        'question_text': 'What are your technical requirements for the frontend?'
    })

    assert result['success'] == True
    assert result['is_blocking'] == False
    assert result['bias_score'] <= 0.5
    assert result['quality_score'] >= 0.5


def test_analyze_coverage_detects_gaps(auth_session, specs_session, test_user, service_container):
    """Test that coverage gaps are detected"""
    # Create project with insufficient coverage
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=30
    )
    specs_session.add(project)
    specs_session.commit()

    # Add only 1 spec (need 3 per category for good coverage)
    spec = Specification(
        project_id=project.id,
        category='goals',
        content='Build a web app',
        source='user_input',
        confidence=Decimal('0.9')
    )
    specs_session.add(spec)
    specs_session.commit()

    # Analyze coverage
    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('analyze_coverage', {
        'project_id': project.id
    })

    assert result['success'] == False
    assert result['is_blocking'] == True
    assert len(result['coverage_gaps']) > 5  # Many categories missing
    assert result['coverage_score'] < 0.7
    assert 'suggested_actions' in result


def test_analyze_coverage_passes_with_good_coverage(auth_session, specs_session, test_user, service_container):
    """Test that good coverage passes quality check"""
    # Create project with good coverage
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=80
    )
    specs_session.add(project)
    specs_session.commit()

    # Add 3+ specs per category for most categories
    categories = ['goals', 'requirements', 'tech_stack', 'users', 'scalability', 'security', 'deployment']
    for category in categories:
        for i in range(3):
            spec = Specification(
                project_id=project.id,
                category=category,
                content=f'{category} spec {i+1}',
                source='user_input',
                confidence=Decimal('0.9')
            )
            specs_session.add(spec)

    specs_session.commit()

    # Analyze coverage
    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('analyze_coverage', {
        'project_id': project.id
    })

    assert result['success'] == True
    assert result['is_blocking'] == False
    assert result['coverage_score'] >= 0.7
    assert len(result['coverage_gaps']) <= 3


def test_compare_paths_recommends_thorough(auth_session, specs_session, test_user, service_container):
    """Test that path optimizer recommends thorough over greedy when maturity is high"""
    # Create project with high maturity
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=85
    )
    specs_session.add(project)
    specs_session.commit()

    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('compare_paths', {
        'goal': 'generate_code',
        'project_id': project.id
    })

    assert result['success'] == True
    assert 'paths' in result
    assert len(result['paths']) >= 2
    assert result['recommended_path']['id'] == 'thorough'
    assert result['recommended_path']['risk'] in ['LOW', 'MEDIUM']


def test_compare_paths_warns_about_greedy(auth_session, specs_session, test_user, service_container):
    """Test that path optimizer warns about greedy path when maturity is low"""
    # Create project with low maturity
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=30
    )
    specs_session.add(project)
    specs_session.commit()

    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('compare_paths', {
        'goal': 'generate_code',
        'project_id': project.id
    })

    assert result['success'] == True

    # Find greedy path
    greedy_path = next((p for p in result['paths'] if p['id'] == 'greedy'), None)
    assert greedy_path is not None
    assert greedy_path['risk'] == 'HIGH'
    assert greedy_path['total_cost_tokens'] > greedy_path['direct_cost_tokens']  # Has rework cost


def test_get_quality_metrics(auth_session, specs_session, test_user, service_container):
    """Test getting quality metrics for a project"""
    # Create project
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=50
    )
    specs_session.add(project)
    specs_session.commit()

    # Create some quality metrics
    metric1 = QualityMetric(
        project_id=project.id,
        metric_type='coverage',
        metric_value=Decimal('0.75'),
        threshold=Decimal('0.7'),
        passed=True,
        details={'coverage_gaps': []},
        calculated_at=datetime.now(timezone.utc)
    )
    metric2 = QualityMetric(
        project_id=project.id,
        metric_type='question_bias',
        metric_value=Decimal('0.3'),
        threshold=Decimal('0.5'),
        passed=True,
        details={'bias_types': []},
        calculated_at=datetime.now(timezone.utc)
    )
    specs_session.add_all([metric1, metric2])
    specs_session.commit()

    # Get metrics
    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('get_quality_metrics', {
        'project_id': project.id
    })

    assert result['success'] == True
    assert len(result['metrics']) == 2
    assert result['summary']['total_metrics'] == 2
    assert result['summary']['passed_metrics'] == 2
    assert result['summary']['pass_rate'] == 1.0


def test_verify_operation_blocks_biased_question(auth_session, specs_session, test_user, service_container):
    """Test that verify_operation blocks biased questions"""
    # Create project
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=50
    )
    specs_session.add(project)
    specs_session.commit()

    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('verify_operation', {
        'agent_id': 'socratic',
        'action': 'generate_question',
        'operation_data': {
            'question_text': 'Should we use Django? It is the best framework.',
            'project_id': project.id
        }
    })

    assert result['success'] == False
    assert result['is_blocking'] == True
    assert 'bias_check' in result['quality_checks']


def test_verify_operation_blocks_premature_code_gen(auth_session, specs_session, test_user, service_container):
    """Test that verify_operation blocks code generation with insufficient coverage"""
    # Create project with low coverage
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=30
    )
    specs_session.add(project)
    specs_session.commit()

    # Add only 1 spec (insufficient)
    spec = Specification(
        project_id=project.id,
        category='goals',
        content='Build something',
        source='user_input',
        confidence=Decimal('0.9')
    )
    specs_session.add(spec)
    specs_session.commit()

    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('verify_operation', {
        'agent_id': 'code',
        'action': 'generate_code',
        'operation_data': {
            'project_id': project.id
        }
    })

    assert result['success'] == False
    assert result['is_blocking'] == True
    assert 'coverage_check' in result['quality_checks']


def test_verify_operation_allows_good_quality(auth_session, specs_session, test_user, service_container):
    """Test that verify_operation allows operations with good quality"""
    # Create project with good coverage
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=85
    )
    specs_session.add(project)
    specs_session.commit()

    # Add good coverage
    categories = ['goals', 'requirements', 'tech_stack', 'users', 'scalability', 'security', 'deployment']
    for category in categories:
        for i in range(3):
            spec = Specification(
                project_id=project.id,
                category=category,
                content=f'{category} spec {i+1}',
                source='user_input',
                confidence=Decimal('0.9')
            )
            specs_session.add(spec)
    specs_session.commit()

    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    result = quality_agent.process_request('verify_operation', {
        'agent_id': 'code',
        'action': 'generate_code',
        'operation_data': {
            'project_id': project.id
        }
    })

    assert result['success'] == True
    assert result['is_blocking'] == False


def test_quality_metrics_stored_in_database(auth_session, specs_session, test_user, service_container):
    """Test that quality metrics are persisted to database"""
    # Create project
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test",
        maturity_score=50
    )
    specs_session.add(project)
    specs_session.commit()

    # Run analysis that stores metrics
    quality_agent = QualityControllerAgent("quality", "Quality Controller", service_container)
    quality_agent.process_request('analyze_coverage', {
        'project_id': project.id
    })

    # Verify metric was stored
    metrics = specs_session.query(QualityMetric).filter_by(project_id=project.id).all()
    assert len(metrics) >= 1
    assert metrics[0].metric_type == 'coverage'
    assert metrics[0].metric_value is not None
