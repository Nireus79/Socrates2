"""
Quality Control API Endpoints

Provides access to quality metrics, analysis, and recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4
from typing import Optional, Dict, List, Any

from ..core.security import get_current_active_user
from ..agents.orchestrator import get_orchestrator, AgentOrchestrator
from ..models import User, Project

router = APIRouter(prefix="/quality", tags=["quality"])


class QualityMetricsResponse(BaseModel):
    """Response model for quality metrics"""
    success: bool
    metrics: List[Dict[str, Any]]
    summary: Dict[str, Any]


class QualityAnalysisResponse(BaseModel):
    """Response model for quality analysis"""
    success: bool
    project_id: str
    maturity_score: int
    coverage_analysis: Dict[str, Any]
    path_recommendation: Dict[str, Any]
    overall_quality_score: float


@router.get("/project/{project_id}/metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(
    project_id: UUID4,
    metric_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Get quality metrics for a project.

    Args:
        project_id: UUID of the project
        metric_type: Optional filter by metric type (bias, coverage, path_optimization)
        current_user: Authenticated user
        orchestrator: Agent orchestrator

    Returns:
        Quality metrics and summary statistics
    """
    # Verify project ownership (simplified - should check via database)
    result = orchestrator.route_request(
        'quality',
        'get_quality_metrics',
        {
            'project_id': project_id,
            'metric_type': metric_type
        }
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to get quality metrics'))

    return QualityMetricsResponse(**result)


@router.get("/project/{project_id}/analysis", response_model=QualityAnalysisResponse)
async def get_quality_analysis(
    project_id: UUID4,
    current_user: User = Depends(get_current_active_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Get comprehensive quality analysis for a project.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        orchestrator: Agent orchestrator

    Returns:
        Complete quality analysis including coverage, path recommendations, and overall score
    """
    # Get coverage analysis
    coverage_result = orchestrator.route_request(
        'quality',
        'analyze_coverage',
        {'project_id': project_id}
    )

    # Get path recommendation
    path_result = orchestrator.route_request(
        'quality',
        'compare_paths',
        {
            'goal': 'generate_code',
            'project_id': project_id
        }
    )

    # Get project maturity score (via project agent)
    project_result = orchestrator.route_request(
        'project',
        'get_project',
        {'project_id': project_id}
    )

    if not project_result['success']:
        raise HTTPException(status_code=404, detail='Project not found')

    project_data = project_result['project']
    maturity_score = project_data['maturity_score']

    # Calculate overall quality score (weighted average)
    coverage_score = coverage_result.get('coverage_score', 0.0) if coverage_result['success'] else 0.0
    overall_quality_score = (
        maturity_score / 100 * 0.5 +  # 50% weight on maturity
        coverage_score * 0.5            # 50% weight on coverage
    )

    return QualityAnalysisResponse(
        success=True,
        project_id=str(project_id),
        maturity_score=maturity_score,
        coverage_analysis=coverage_result if coverage_result['success'] else {},
        path_recommendation=path_result if path_result['success'] else {},
        overall_quality_score=round(overall_quality_score, 2)
    )


@router.get("/project/{project_id}/recommendations")
async def get_quality_recommendations(
    project_id: UUID4,
    current_user: User = Depends(get_current_active_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Get quality improvement recommendations for a project.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        orchestrator: Agent orchestrator

    Returns:
        List of actionable recommendations to improve project quality
    """
    # Get coverage analysis for recommendations
    coverage_result = orchestrator.route_request(
        'quality',
        'analyze_coverage',
        {'project_id': project_id}
    )

    recommendations = []

    if coverage_result['success']:
        coverage_gaps = coverage_result.get('coverage_gaps', [])

        if coverage_gaps:
            recommendations.append({
                'type': 'coverage_gap',
                'priority': 'high',
                'title': 'Fill Coverage Gaps',
                'description': f'Your project has incomplete coverage in {len(coverage_gaps)} categories',
                'suggested_actions': coverage_result.get('suggested_actions', []),
                'categories': coverage_gaps
            })

        coverage_score = coverage_result.get('coverage_score', 0.0)
        if coverage_score < 0.9:
            recommendations.append({
                'type': 'improve_coverage',
                'priority': 'medium',
                'title': 'Improve Specification Coverage',
                'description': f'Current coverage is {coverage_score:.0%}. Aim for 90%+ coverage.',
                'suggested_actions': [
                    'Add more detailed specifications',
                    'Answer additional clarifying questions',
                    'Review and expand existing specifications'
                ]
            })

    # Get path recommendation
    path_result = orchestrator.route_request(
        'quality',
        'compare_paths',
        {
            'goal': 'generate_code',
            'project_id': project_id
        }
    )

    if path_result['success']:
        recommended_path = path_result.get('recommended_path', {})
        if recommended_path.get('risk') == 'HIGH':
            recommendations.append({
                'type': 'high_risk_path',
                'priority': 'critical',
                'title': 'Current Path Has High Risk',
                'description': recommended_path.get('name', 'Current approach'),
                'suggested_actions': [
                    'Complete more specifications before generating code',
                    'Follow the thorough approach to minimize rework',
                    f"Risk reduction: {path_result.get('recommendation_reason', '')}"
                ]
            })

    return {
        'success': True,
        'project_id': str(project_id),
        'recommendations': recommendations,
        'total_recommendations': len(recommendations)
    }
