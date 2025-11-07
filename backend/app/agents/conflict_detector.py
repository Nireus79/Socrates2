"""
ConflictDetectorAgent - Detects and manages specification conflicts.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import json

from .base import BaseAgent
from ..models.specification import Specification
from ..models.conflict import Conflict, ConflictType, ConflictSeverity, ConflictStatus


class ConflictDetectorAgent(BaseAgent):
    """
    Detects conflicts between new and existing specifications.

    Responsibilities:
    - Detect contradictions in specifications
    - Analyze conflict severity
    - Manage conflict resolution
    - Track conflict history

    Used by:
    - Phase 3: ContextAnalyzerAgent (before saving specs)
    - Phase 4+: Validation before code generation
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            'detect_conflicts',
            'resolve_conflict',
            'list_conflicts',
            'get_conflict_details'
        ]

    def _detect_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect conflicts between new and existing specifications.

        Args:
            data: {
                'project_id': str,
                'new_specs': List[Dict],  # Extracted specs not yet saved
                'source_id': str  # question_id or message_id
            }

        Returns:
            {
                'success': bool,
                'conflicts_detected': bool,
                'conflicts': List[Dict],  # Details of conflicts found
                'safe_to_save': bool
            }
        """
        project_id = data.get('project_id')
        new_specs = data.get('new_specs', [])
        source_id = data.get('source_id')

        if not project_id or not new_specs:
            return {
                'success': False,
                'error': 'project_id and new_specs are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get database session
        db = self.services.get_database_specs()

        # Load existing specifications
        existing_specs = db.query(Specification).filter(
            Specification.project_id == project_id
        ).all()

        if not existing_specs:
            # No existing specs, no conflicts possible
            return {
                'success': True,
                'conflicts_detected': False,
                'conflicts': [],
                'safe_to_save': True
            }

        # Build conflict detection prompt
        prompt = self._build_conflict_detection_prompt(new_specs, existing_specs)

        # Call Claude API
        try:
            claude_client = self.services.get_claude_client()
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            conflict_analysis = json.loads(response.content[0].text)

            conflicts_found = []
            if conflict_analysis.get('conflicts_detected'):
                # Save conflicts to database
                for conflict_data in conflict_analysis.get('conflicts', []):
                    conflict = Conflict(
                        project_id=project_id,
                        type=ConflictType[conflict_data['type'].upper()],
                        description=conflict_data['description'],
                        spec_ids=conflict_data.get('spec_ids', []),
                        severity=ConflictSeverity[conflict_data['severity'].upper()],
                        status=ConflictStatus.OPEN,
                        detected_at=datetime.now(timezone.utc)
                    )
                    db.add(conflict)
                    conflicts_found.append(conflict)

                db.commit()

                # Refresh to get IDs
                for conflict in conflicts_found:
                    db.refresh(conflict)

            self.logger.info(
                f"Conflict detection for project {project_id}: "
                f"{len(conflicts_found)} conflicts found"
            )

            return {
                'success': True,
                'conflicts_detected': len(conflicts_found) > 0,
                'conflicts': [c.to_dict() for c in conflicts_found],
                'safe_to_save': len(conflicts_found) == 0
            }

        except Exception as e:
            self.logger.error(f"Error detecting conflicts: {str(e)}")
            return {
                'success': False,
                'error': f'Conflict detection failed: {str(e)}',
                'error_code': 'DETECTION_ERROR'
            }

    def _resolve_conflict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a conflict based on user decision.

        Args:
            data: {
                'conflict_id': str,
                'resolution': str,  # 'keep_old', 'replace', 'merge', 'ignore'
                'resolution_notes': str (optional)
            }

        Returns:
            {'success': bool, 'conflict': dict}
        """
        import uuid

        conflict_id = data.get('conflict_id')
        resolution = data.get('resolution')
        resolution_notes = data.get('resolution_notes', '')

        if not conflict_id or not resolution:
            return {
                'success': False,
                'error': 'conflict_id and resolution are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Validate conflict_id is a valid UUID
        try:
            conflict_uuid = uuid.UUID(conflict_id) if isinstance(conflict_id, str) else conflict_id
        except (ValueError, AttributeError):
            return {
                'success': False,
                'error': f'Invalid conflict_id format: {conflict_id}',
                'error_code': 'CONFLICT_NOT_FOUND'
            }

        valid_resolutions = ['keep_old', 'replace', 'merge', 'ignore']
        if resolution not in valid_resolutions:
            return {
                'success': False,
                'error': f'Invalid resolution. Must be one of: {valid_resolutions}',
                'error_code': 'INVALID_RESOLUTION'
            }

        # Get database session
        db = self.services.get_database_specs()

        # Load conflict
        conflict = db.query(Conflict).filter(Conflict.id == conflict_uuid).first()
        if not conflict:
            return {
                'success': False,
                'error': f'Conflict not found: {conflict_id}',
                'error_code': 'CONFLICT_NOT_FOUND'
            }

        # Update conflict
        if resolution == 'ignore':
            conflict.status = ConflictStatus.IGNORED
        else:
            conflict.status = ConflictStatus.RESOLVED

        conflict.resolution = f"{resolution}: {resolution_notes}" if resolution_notes else resolution
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by_user = True

        db.commit()
        db.refresh(conflict)

        self.logger.info(f"Conflict {conflict_id} resolved with: {resolution}")

        return {
            'success': True,
            'conflict': conflict.to_dict()
        }

    def _list_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List conflicts for a project.

        Args:
            data: {
                'project_id': str,
                'status': str (optional)  # 'open', 'resolved', 'ignored'
            }

        Returns:
            {'success': bool, 'conflicts': List[dict], 'count': int}
        """
        project_id = data.get('project_id')
        status_filter = data.get('status')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get database session
        db = self.services.get_database_specs()

        # Build query
        query = db.query(Conflict).filter(Conflict.project_id == project_id)

        if status_filter:
            try:
                status_enum = ConflictStatus[status_filter.upper()]
                query = query.filter(Conflict.status == status_enum)
            except KeyError:
                return {
                    'success': False,
                    'error': f'Invalid status: {status_filter}',
                    'error_code': 'INVALID_STATUS'
                }

        conflicts = query.order_by(Conflict.detected_at.desc()).all()

        return {
            'success': True,
            'conflicts': [c.to_dict() for c in conflicts],
            'count': len(conflicts)
        }

    def _get_conflict_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed information about a specific conflict.

        Args:
            data: {'conflict_id': str}

        Returns:
            {'success': bool, 'conflict': dict, 'specifications': List[dict]}
        """
        conflict_id = data.get('conflict_id')

        if not conflict_id:
            return {
                'success': False,
                'error': 'conflict_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get database session
        db = self.services.get_database_specs()

        # Load conflict
        conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
        if not conflict:
            return {
                'success': False,
                'error': f'Conflict not found: {conflict_id}',
                'error_code': 'CONFLICT_NOT_FOUND'
            }

        # Load related specifications
        specs = []
        if conflict.spec_ids:
            specs = db.query(Specification).filter(
                Specification.id.in_(conflict.spec_ids)
            ).all()

        return {
            'success': True,
            'conflict': conflict.to_dict(),
            'specifications': [s.to_dict() for s in specs]
        }

    def _build_conflict_detection_prompt(
        self,
        new_specs: List[Dict],
        existing_specs: List[Specification]
    ) -> str:
        """Build prompt for Claude to detect conflicts."""
        prompt = f"""Analyze these new specifications for conflicts with existing ones.

EXISTING SPECIFICATIONS:
{self._format_specs_for_prompt(existing_specs)}

NEW SPECIFICATIONS TO CHECK:
{json.dumps(new_specs, indent=2)}

TASK:
Identify any contradictions or conflicts between new and existing specifications.

CONFLICT TYPES:
- technology: Different tech choices for same purpose
- requirement: Contradicting functional requirements
- timeline: Conflicting deadlines or schedules
- resource: Incompatible resource allocations

SEVERITY LEVELS:
- critical: Complete contradiction, cannot coexist
- high: Major conflict, needs immediate resolution
- medium: Moderate conflict, should be addressed
- low: Minor inconsistency, can be resolved later

Return JSON format:
{{
  "conflicts_detected": true/false,
  "conflicts": [
    {{
      "type": "technology|requirement|timeline|resource",
      "description": "Clear description of the conflict",
      "severity": "critical|high|medium|low",
      "spec_ids": ["existing_spec_id_1", "existing_spec_id_2"],
      "new_spec_keys": ["new_spec_key"],
      "reasoning": "Why this is a conflict"
    }}
  ]
}}

If no conflicts found, return:
{{
  "conflicts_detected": false,
  "conflicts": []
}}
"""
        return prompt

    def _format_specs_for_prompt(self, specs: List[Specification]) -> str:
        """Format specifications for prompt."""
        if not specs:
            return "None"

        lines = []
        for spec in specs:
            lines.append(
                f"- [{spec.id}] {spec.category}: {spec.content} "
                f"(confidence: {spec.confidence}, source: {spec.source})"
            )
        return "\n".join(lines)
