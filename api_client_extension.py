"""
SocratesAPI Extension Methods
Extends the base SocratesAPI class with additional methods not yet in Socrates.py

This file contains all missing API methods organized by category.
Import these methods into SocratesAPI class.
"""

from typing import Any, Dict, List, Optional
import requests


# Mixin class with all extension methods
class SocratesAPIExtension:
    """Extension methods for SocratesAPI class - include these in SocratesAPI"""

    # ============================================================================
    # MISSING AUTHENTICATION METHODS
    # ============================================================================

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user information (whoami)"""
        try:
            response = self._request("GET", "/api/v1/auth/me")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self._request("POST", "/api/v1/auth/refresh", json={
                "refresh_token": refresh_token
            })
            data = response.json()
            if response.status_code == 200:
                self.access_token = data.get("access_token")
            return {"success": response.status_code == 200, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        try:
            response = self._request("POST", "/api/v1/auth/change-password", json={
                "current_password": current_password,
                "new_password": new_password
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_account(self, password: str, username: str) -> Dict[str, Any]:
        """Delete user account (requires password and username confirmation)"""
        try:
            response = self._request("POST", "/api/v1/auth/delete-account", json={
                "password": password,
                "confirmation": username
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # SPECIFICATION METHODS (enhanced)
    # ============================================================================

    def list_specifications(self, project_id: str) -> Dict[str, Any]:
        """List specifications (alias for list_project_specifications)"""
        return self.list_project_specifications(project_id)

    def list_project_specifications(self, project_id: str, skip: int = 0, limit: int = 100,
                                   status: Optional[str] = None) -> Dict[str, Any]:
        """List all specifications for a project"""
        try:
            params = f"?skip={skip}&limit={limit}"
            if status:
                params += f"&status={status}"
            response = self._request("GET", f"/api/v1/projects/{project_id}/specifications{params}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_specification(self, project_id: str, title: str, spec_type: str = "feature",
                            description: str = "") -> Dict[str, Any]:
        """Create a new specification"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/specifications", json={
                "title": title,
                "type": spec_type,
                "description": description
            })
            return {"success": response.status_code == 201, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_specification(self, spec_id: str) -> Dict[str, Any]:
        """Get specification details"""
        try:
            response = self._request("GET", f"/api/v1/specifications/{spec_id}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def approve_specification(self, spec_id: str) -> Dict[str, Any]:
        """Approve a specification"""
        try:
            response = self._request("POST", f"/api/v1/specifications/{spec_id}/approve")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def implement_specification(self, spec_id: str) -> Dict[str, Any]:
        """Mark specification as implemented"""
        try:
            response = self._request("POST", f"/api/v1/specifications/{spec_id}/implement")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_specification(self, spec_id: str) -> Dict[str, Any]:
        """Delete a specification"""
        try:
            response = self._request("DELETE", f"/api/v1/specifications/{spec_id}")
            return {"success": response.status_code == 204, "data": {}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # TEAM METHODS (new)
    # ============================================================================

    def create_team(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new team"""
        try:
            response = self._request("POST", "/api/v1/teams", json={
                "name": name,
                "description": description
            })
            return {"success": response.status_code == 201, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_teams(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List teams owned by current user"""
        try:
            response = self._request("GET", f"/api/v1/teams?skip={skip}&limit={limit}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get team details"""
        try:
            response = self._request("GET", f"/api/v1/teams/{team_id}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def invite_to_team(self, team_id: str, email: str, role: str = "member") -> Dict[str, Any]:
        """Invite person to team"""
        try:
            response = self._request("POST", f"/api/v1/teams/{team_id}/invite", json={
                "email": email,
                "role": role
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_team_member(self, team_id: str, email: str, role: str = "member") -> Dict[str, Any]:
        """Add existing user to team"""
        return self.invite_to_team(team_id, email, role)

    def remove_team_member(self, team_id: str, email: str) -> Dict[str, Any]:
        """Remove member from team"""
        try:
            response = self._request("DELETE", f"/api/v1/teams/{team_id}/members/{email}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_team_members(self, team_id: str) -> Dict[str, Any]:
        """List team members"""
        try:
            response = self._request("GET", f"/api/v1/teams/{team_id}/members")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_team_member_role(self, team_id: str, email: str, role: str) -> Dict[str, Any]:
        """Change team member role"""
        try:
            response = self._request("POST", f"/api/v1/teams/{team_id}/members/{email}/role", json={
                "role": role
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # DOCUMENT METHODS (new)
    # ============================================================================

    def upload_document(self, project_id: str, file_path: str) -> Dict[str, Any]:
        """Upload document to knowledge base"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self._request("POST", f"/api/v1/projects/{project_id}/documents/upload", files=files)
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_documents(self, project_id: str) -> Dict[str, Any]:
        """List project documents"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/documents")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete document"""
        try:
            response = self._request("DELETE", f"/api/v1/documents/{doc_id}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # DOMAIN METHODS (new)
    # ============================================================================

    def list_domains(self) -> Dict[str, Any]:
        """List all available domains"""
        try:
            response = self._request("GET", "/api/v1/domains")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_domain(self, domain_id: str) -> Dict[str, Any]:
        """Get domain details"""
        try:
            response = self._request("GET", f"/api/v1/domains/{domain_id}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_domain_questions(self, domain_id: str) -> Dict[str, Any]:
        """List questions for a domain"""
        try:
            response = self._request("GET", f"/api/v1/domains/{domain_id}/questions")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # CODE GENERATION METHODS (new)
    # ============================================================================

    def generate_code(self, project_id: str, language: str = "python",
                     pattern: str = "rest-api", framework: str = "",
                     features: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate code from specifications"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/code/generate", json={
                "language": language,
                "pattern": pattern,
                "framework": framework,
                "features": features or []
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_code_generations(self, project_id: str) -> Dict[str, Any]:
        """List code generations for a project"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/code/generations")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get code generation status"""
        try:
            response = self._request("GET", f"/api/v1/code/{generation_id}/status")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_generated_code(self, generation_id: str) -> Dict[str, Any]:
        """Download generated code"""
        try:
            response = self._request("GET", f"/api/v1/code/{generation_id}/download")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # QUESTION METHODS (new)
    # ============================================================================

    def create_custom_question(self, session_id: str, text: str, q_type: str = "open",
                              category: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create custom question"""
        try:
            response = self._request("POST", f"/api/v1/sessions/{session_id}/custom-question", json={
                "text": text,
                "type": q_type,
                "category": category,
                "tags": tags or []
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_domain_questions(self, domain: str) -> Dict[str, Any]:
        """List questions in a domain"""
        try:
            response = self._request("GET", f"/api/v1/domains/{domain}/questions")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def submit_question_answer(self, session_id: str, question_id: str, answer: str) -> Dict[str, Any]:
        """Submit answer to question"""
        try:
            response = self._request("POST", f"/api/v1/sessions/{session_id}/answers", json={
                "question_id": question_id,
                "answer": answer
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_question(self, question_id: str) -> Dict[str, Any]:
        """Get question details"""
        try:
            response = self._request("GET", f"/api/v1/questions/{question_id}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # WORKFLOW METHODS (new)
    # ============================================================================

    def list_workflows(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """List available workflows"""
        try:
            params = f"?domain={domain}" if domain else ""
            response = self._request("GET", f"/api/v1/workflows{params}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Get workflow details"""
        try:
            response = self._request("GET", f"/api/v1/workflows/{workflow_name}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_workflow(self, session_id: str, workflow_name: str) -> Dict[str, Any]:
        """Start a workflow"""
        try:
            response = self._request("POST", f"/api/v1/sessions/{session_id}/workflows/{workflow_name}/start")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        try:
            response = self._request("GET", f"/api/v1/workflows/{workflow_id}/status")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # EXPORT METHODS (enhanced)
    # ============================================================================

    def list_export_formats(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """List available export formats"""
        try:
            params = f"?domain={domain}" if domain else ""
            response = self._request("GET", f"/api/v1/export/formats{params}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_export(self, project_id: str, export_format: str = "json",
                       includes: Optional[List[str]] = None,
                       include_history: bool = False,
                       include_metadata: bool = True) -> Dict[str, Any]:
        """Generate export"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/export", json={
                "format": export_format,
                "includes": includes or [],
                "include_history": include_history,
                "include_metadata": include_metadata
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_export(self, export_id: str) -> Dict[str, Any]:
        """Download exported project"""
        try:
            response = self._request("GET", f"/api/v1/exports/{export_id}/download")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def schedule_export(self, project_id: str, export_format: str, frequency: str = "weekly",
                       time: str = "09:00", email_on_complete: bool = False) -> Dict[str, Any]:
        """Schedule recurring export"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/export/schedule", json={
                "format": export_format,
                "frequency": frequency,
                "time": time,
                "email_on_complete": email_on_complete
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # ADMIN METHODS (new)
    # ============================================================================

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            response = self._request("GET", "/api/v1/admin/health")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            response = self._request("GET", "/api/v1/admin/stats")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_all_users(self) -> Dict[str, Any]:
        """List all users (admin only)"""
        try:
            response = self._request("GET", "/api/v1/admin/users")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_info(self, email: str) -> Dict[str, Any]:
        """Get user information (admin only)"""
        try:
            response = self._request("GET", f"/api/v1/admin/users/{email}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_user_role(self, email: str, role: str) -> Dict[str, Any]:
        """Change user role (admin only)"""
        try:
            response = self._request("POST", f"/api/v1/admin/users/{email}/role", json={
                "role": role
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disable_user(self, email: str) -> Dict[str, Any]:
        """Disable user account (admin only)"""
        try:
            response = self._request("POST", f"/api/v1/admin/users/{email}/disable")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def enable_user(self, email: str) -> Dict[str, Any]:
        """Enable user account (admin only)"""
        try:
            response = self._request("POST", f"/api/v1/admin/users/{email}/enable")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration (admin only)"""
        try:
            response = self._request("GET", "/api/v1/admin/config")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_system_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Set system configuration (admin only)"""
        try:
            response = self._request("POST", "/api/v1/admin/config", json={
                "key": key,
                "value": value
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # ANALYTICS METHODS (new)
    # ============================================================================

    def get_analytics_dashboard(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics dashboard"""
        try:
            params = f"?user_id={user_id}" if user_id else ""
            response = self._request("GET", f"/api/v1/analytics/dashboard{params}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get project analytics"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/analytics")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user analytics"""
        try:
            response = self._request("GET", f"/api/v1/users/{user_id}/analytics")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_analytics(self, scope: str = "user", format: str = "csv",
                        period: str = "30d", fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export analytics data"""
        try:
            response = self._request("POST", "/api/v1/analytics/export", json={
                "scope": scope,
                "format": format,
                "period": period,
                "fields": fields or []
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # QUALITY METHODS (new)
    # ============================================================================

    def run_quality_checks(self, project_id: str) -> Dict[str, Any]:
        """Run quality checks on project"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/quality/check")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_quality_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get quality metrics"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/quality/metrics")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_quality_gates(self, project_id: str) -> Dict[str, Any]:
        """Get quality gates configuration"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/quality/gates")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_quality_gate(self, project_id: str, gate_name: str, threshold: str) -> Dict[str, Any]:
        """Set quality gate threshold"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/quality/gates/{gate_name}", json={
                "threshold": threshold
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def enable_quality_gate(self, project_id: str, gate_name: str) -> Dict[str, Any]:
        """Enable quality gate"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/quality/gates/{gate_name}/enable")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disable_quality_gate(self, project_id: str, gate_name: str) -> Dict[str, Any]:
        """Disable quality gate"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/quality/gates/{gate_name}/disable")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_quality_report(self, project_id: str, format: str = "pdf",
                               report_type: str = "detailed") -> Dict[str, Any]:
        """Generate quality report"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/quality/report", json={
                "format": format,
                "report_type": report_type
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # NOTIFICATION METHODS (new)
    # ============================================================================

    def list_notifications(self, filter_by: str = "unread") -> Dict[str, Any]:
        """List notifications"""
        try:
            response = self._request("GET", f"/api/v1/notifications?filter={filter_by}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        try:
            response = self._request("GET", "/api/v1/notifications/settings")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_notification_setting(self, setting_type: str, notification: str,
                                   enabled: bool) -> Dict[str, Any]:
        """Update notification setting"""
        try:
            response = self._request("POST", "/api/v1/notifications/settings", json={
                "setting_type": setting_type,
                "notification": notification,
                "enabled": enabled
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_notification_read(self, notif_id: str) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            response = self._request("POST", f"/api/v1/notifications/{notif_id}/read")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_all_notifications_read(self) -> Dict[str, Any]:
        """Mark all notifications as read"""
        try:
            response = self._request("POST", "/api/v1/notifications/read-all")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def subscribe_to_notifications(self, sub_type: str, channel: str,
                                  events: Optional[List[str]] = None) -> Dict[str, Any]:
        """Subscribe to notifications"""
        try:
            response = self._request("POST", "/api/v1/notifications/subscribe", json={
                "sub_type": sub_type,
                "channel": channel,
                "events": events or []
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # CONFLICT METHODS (new)
    # ============================================================================

    def detect_conflicts(self, project_id: str) -> Dict[str, Any]:
        """Detect specification conflicts"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/conflicts/detect")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_conflicts(self, project_id: str, filter_by: str = "unresolved") -> Dict[str, Any]:
        """List conflicts"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/conflicts?filter={filter_by}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_conflict(self, conflict_id: str) -> Dict[str, Any]:
        """Get conflict details"""
        try:
            response = self._request("GET", f"/api/v1/conflicts/{conflict_id}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resolve_conflict(self, conflict_id: str, resolution: str) -> Dict[str, Any]:
        """Resolve a conflict"""
        try:
            response = self._request("POST", f"/api/v1/conflicts/{conflict_id}/resolve", json={
                "resolution": resolution
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_conflict_patterns(self, project_id: str) -> Dict[str, Any]:
        """Analyze conflict patterns"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/conflicts/analysis")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # SEARCH METHODS (enhanced)
    # ============================================================================

    def text_search(self, project_id: str, query: str) -> Dict[str, Any]:
        """Full-text search"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/search/text?query={query}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_specifications(self, project_id: str, query: str,
                             filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search specifications"""
        try:
            params = f"?query={query}"
            response = self._request("GET", f"/api/v1/projects/{project_id}/search/specifications{params}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def advanced_search(self, project_id: str, query: str,
                       filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Advanced search with filters"""
        try:
            response = self._request("POST", f"/api/v1/projects/{project_id}/search/advanced", json={
                "query": query,
                "filters": filters or {}
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # INSIGHTS METHODS (new)
    # ============================================================================

    def get_project_insights(self, project_id: str) -> Dict[str, Any]:
        """Get project insights"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/insights")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_specification_gaps(self, project_id: str) -> Dict[str, Any]:
        """Analyze specification gaps"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/insights/gaps")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_project_risks(self, project_id: str) -> Dict[str, Any]:
        """Analyze project risks"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/insights/risks")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_project_recommendations(self, project_id: str) -> Dict[str, Any]:
        """Get project recommendations"""
        try:
            response = self._request("GET", f"/api/v1/projects/{project_id}/insights/recommendations")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # GITHUB INTEGRATION METHODS (new)
    # ============================================================================

    def get_github_connection_status(self) -> Dict[str, Any]:
        """Check GitHub connection status"""
        try:
            response = self._request("GET", "/api/v1/github/status")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def connect_github(self, auth_code: str) -> Dict[str, Any]:
        """Connect GitHub account"""
        try:
            response = self._request("POST", "/api/v1/github/connect", json={
                "auth_code": auth_code
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_from_github(self, project_id: str, repo_url: str,
                          import_items: Optional[List[str]] = None) -> Dict[str, Any]:
        """Import from GitHub repository"""
        try:
            response = self._request("POST", f"/api/v1/github/import", json={
                "project_id": project_id,
                "repo_url": repo_url,
                "import_items": import_items or ["readme", "code-structure"]
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_github_repo(self, repo_url: str) -> Dict[str, Any]:
        """Analyze GitHub repository"""
        try:
            response = self._request("POST", "/api/v1/github/analyze", json={
                "repo_url": repo_url
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_with_github(self, project_id: str, repo_url: str,
                        direction: str = "push",
                        items: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sync with GitHub"""
        try:
            response = self._request("POST", "/api/v1/github/sync", json={
                "project_id": project_id,
                "repo_url": repo_url,
                "direction": direction,
                "items": items or []
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # LLM METHODS (new - for LLM selection system)
    # ============================================================================

    def list_available_llms(self) -> Dict[str, Any]:
        """List available LLM providers and models"""
        try:
            response = self._request("GET", "/api/v1/llm/available")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_current_llm(self) -> Dict[str, Any]:
        """Get currently selected LLM/model"""
        try:
            response = self._request("GET", "/api/v1/llm/current")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def select_llm(self, provider: str, model: str) -> Dict[str, Any]:
        """Select LLM provider and model"""
        try:
            response = self._request("POST", "/api/v1/llm/select", json={
                "provider": provider,
                "model": model
            })
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_llm_costs(self) -> Dict[str, Any]:
        """Get LLM costs per model"""
        try:
            response = self._request("GET", "/api/v1/llm/costs")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_llm_usage(self, period: str = "month") -> Dict[str, Any]:
        """Get LLM usage statistics"""
        try:
            response = self._request("GET", f"/api/v1/llm/usage?period={period}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # NAMING ALIASES - For CLI compatibility
    # ============================================================================
    # These aliases map CLI method names to actual backend endpoint wrappers

    def get_projects(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Alias for list_projects() - get user's projects"""
        # This method is called by CLI but we need to use list_projects internally
        # Import here to access the parent class method
        return self.list_projects(skip, limit)

    def get_templates(self) -> Dict[str, Any]:
        """Alias for list_templates() - get available templates"""
        return self.list_templates()

    def get_teams(self) -> Dict[str, Any]:
        """Alias for list_teams() - get user's teams"""
        return self.list_teams()

    def get_team_members(self, team_id: str) -> Dict[str, Any]:
        """Alias for list_team_members() - get team members"""
        return self.list_team_members(team_id)

    def invite_team_member(self, team_id: str, email: str, role: str = "member") -> Dict[str, Any]:
        """Alias for invite_to_team() - invite user to team"""
        return self.invite_to_team(team_id, email, role)

    # ============================================================================
    # NEW COLLABORATION METHODS - Missing implementations
    # ============================================================================

    def get_collaboration_status(self, project_id: str) -> Dict[str, Any]:
        """Get collaboration status for a project"""
        try:
            response = self._request("GET", f"/api/v1/collaboration/projects/{project_id}/status")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_collaboration_activity(self, project_id: str) -> Dict[str, Any]:
        """Get collaboration activity for a project"""
        try:
            response = self._request("GET", f"/api/v1/collaboration/projects/{project_id}/activity")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_project_members(self, project_id: str) -> Dict[str, Any]:
        """Get project members/collaborators"""
        try:
            response = self._request("GET", f"/api/v1/collaboration/projects/{project_id}/collaborators")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def semantic_search(self, project_id: str, query: str) -> Dict[str, Any]:
        """Semantic search in project documents"""
        try:
            response = self._request("GET", f"/api/v1/documents/{project_id}/search?query={query}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
