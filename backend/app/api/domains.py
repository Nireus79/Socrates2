"""
Domain API endpoints for Socrates2.

Provides REST API access to all available knowledge domains and their specifications.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.domains import get_domain_registry
from app.domains.registry import register_all_domains

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/domains", tags=["domains"])


# Initialize domains on first import
_domains_initialized = False


def ensure_domains_initialized() -> None:
    """Ensure all domains are registered before API access."""
    global _domains_initialized
    if not _domains_initialized:
        try:
            register_all_domains()
            _domains_initialized = True
            logger.info("Domain registry initialized")
        except Exception as e:
            logger.error(f"Failed to initialize domain registry: {e}")
            raise


@router.on_event("startup")
async def startup_event():
    """Initialize domains on application startup."""
    ensure_domains_initialized()


@router.get("", summary="List all available domains")
async def list_domains() -> Dict[str, Any]:
    """
    List all available Socrates2 knowledge domains.

    Returns:
        Dictionary with domain count and list of all domains with metadata
    """
    ensure_domains_initialized()
    registry = get_domain_registry()
    return registry.to_dict()


@router.get("/{domain_id}", summary="Get domain details")
async def get_domain_details(domain_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific domain.

    Args:
        domain_id: Unique domain identifier (e.g., "programming", "data_engineering")

    Returns:
        Domain metadata including name, version, description, and subsystem counts

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        available_domains = ", ".join(registry.list_domain_ids())
        raise HTTPException(
            status_code=404,
            detail=f"Domain '{domain_id}' not found. Available domains: {available_domains}",
        )

    domain = registry.get_domain(domain_id)
    return {
        "domain_id": domain.domain_id,
        "name": domain.name,
        "version": domain.version,
        "description": domain.description,
        "categories": domain.get_categories(),
        "questions": len(domain.get_questions()),
        "exporters": len(domain.get_export_formats()),
        "rules": len(domain.get_conflict_rules()),
        "analyzers": len(domain.get_quality_analyzers()),
    }


@router.get("/{domain_id}/questions", summary="Get domain questions")
async def get_domain_questions(domain_id: str) -> Dict[str, Any]:
    """
    Get all Socratic questions for a specific domain.

    Args:
        domain_id: Unique domain identifier

    Returns:
        List of questions with all metadata

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    questions = domain.get_questions()

    return {
        "domain_id": domain_id,
        "count": len(questions),
        "questions": [
            {
                "question_id": q.question_id,
                "text": q.text,
                "category": q.category,
                "difficulty": q.difficulty,
                "help_text": q.help_text,
                "example_answer": q.example_answer,
                "follow_up_questions": q.follow_up_questions,
                "dependencies": q.dependencies,
            }
            for q in questions
        ],
    }


@router.get("/{domain_id}/exporters", summary="Get domain exporters")
async def get_domain_exporters(domain_id: str) -> Dict[str, Any]:
    """
    Get all export formats for a specific domain.

    Args:
        domain_id: Unique domain identifier

    Returns:
        List of exporters with all metadata

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    exporters = domain.get_export_formats()

    return {
        "domain_id": domain_id,
        "count": len(exporters),
        "exporters": [
            {
                "format_id": e.format_id,
                "name": e.name,
                "description": e.description,
                "file_extension": e.file_extension,
                "mime_type": e.mime_type,
                "template_id": e.template_id,
            }
            for e in exporters
        ],
    }


@router.get("/{domain_id}/rules", summary="Get domain conflict rules")
async def get_domain_rules(domain_id: str) -> Dict[str, Any]:
    """
    Get all conflict detection rules for a specific domain.

    Args:
        domain_id: Unique domain identifier

    Returns:
        List of rules with all metadata

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    rules = domain.get_conflict_rules()

    return {
        "domain_id": domain_id,
        "count": len(rules),
        "rules": [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "condition": r.condition,
                "severity": r.severity,
                "message": r.message,
            }
            for r in rules
        ],
    }


@router.get("/{domain_id}/analyzers", summary="Get domain quality analyzers")
async def get_domain_analyzers(domain_id: str) -> Dict[str, Any]:
    """
    Get all quality analyzers for a specific domain.

    Args:
        domain_id: Unique domain identifier

    Returns:
        List of analyzer IDs (enabled/required analyzers)

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    analyzers = domain.get_quality_analyzers()

    return {"domain_id": domain_id, "count": len(analyzers), "analyzers": analyzers}


@router.get("/{domain_id}/metadata", summary="Get complete domain metadata")
async def get_domain_metadata(domain_id: str) -> Dict[str, Any]:
    """
    Get complete metadata for a domain including all subsystems.

    Args:
        domain_id: Unique domain identifier

    Returns:
        Comprehensive domain metadata

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    questions = domain.get_questions()
    exporters = domain.get_export_formats()
    rules = domain.get_conflict_rules()
    analyzers = domain.get_quality_analyzers()

    return {
        "domain_id": domain.domain_id,
        "name": domain.name,
        "version": domain.version,
        "description": domain.description,
        "categories": domain.get_categories(),
        "subsystems": {
            "questions": {
                "count": len(questions),
                "categories": list(set(q.category for q in questions)),
            },
            "exporters": {
                "count": len(exporters),
                "extensions": list(set(e.file_extension for e in exporters)),
            },
            "rules": {"count": len(rules), "severities": list(set(r.severity for r in rules))},
            "analyzers": {
                "count": len(analyzers),
                "enabled": len(analyzers),
            },
        },
    }


@router.get("/categories/{domain_id}", summary="Get domain categories")
async def get_domain_categories(domain_id: str) -> Dict[str, Any]:
    """
    Get specification categories for a domain.

    Args:
        domain_id: Unique domain identifier

    Returns:
        List of categories

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    categories = domain.get_categories()

    return {"domain_id": domain_id, "count": len(categories), "categories": categories}


@router.post("/{domain_id}/validate-specification", summary="Validate specification")
async def validate_specification(domain_id: str, specification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a specification against domain rules.

    Args:
        domain_id: Unique domain identifier
        specification: Specification data to validate

    Returns:
        Validation results with any conflicts or issues

    Raises:
        HTTPException: If domain not found
    """
    ensure_domains_initialized()
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

    domain = registry.get_domain(domain_id)
    rules = domain.get_conflict_rules()

    # Validate against rules (simple implementation)
    conflicts = []
    for rule in rules:
        # This is a simplified validation - real implementation would parse conditions
        # and check against specification content
        conflicts.append(
            {
                "rule_id": rule.rule_id,
                "severity": rule.severity,
                "message": rule.message,
                "status": "not_evaluated",  # Would be evaluated based on actual rule conditions
            }
        )

    return {
        "domain_id": domain_id,
        "valid": len([c for c in conflicts if c["severity"] == "error"]) == 0,
        "conflicts": conflicts,
        "specification_excerpt": f"Validating {len(specification)} fields",
    }
