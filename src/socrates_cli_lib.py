"""
Socrates CLI as a Python Library
Allows IDE integration and programmatic access to CLI commands

Usage:
    from socrates_cli_lib import SocratesCLI
    cli = SocratesCLI(api_url="http://localhost:8000")
    result = cli.register("john", "doe", "johndoe", "password", "john@example.com")
"""

from typing import Any, Dict, List, Optional
from Socrates import SocratesAPI, SocratesConfig


class SocratesCLI:
    """Python library interface to Socrates CLI for IDE integration"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize CLI library"""
        self.api_url = api_url
        self.config = SocratesConfig()
        self.api = SocratesAPI(api_url, None)  # Console set to None for library mode
        self.api.set_config(self.config)

        # Load saved tokens if available
        if self.config.get("access_token"):
            self.api.set_token(self.config.get("access_token"))
        if self.config.get("refresh_token"):
            self.api.set_refresh_token(self.config.get("refresh_token"))

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================

    def register(self, name: str, surname: str, username: str,
                password: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Register new user"""
        return self.api.register(username, name, surname, email or "", password)

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """Login to Socrates"""
        result = self.api.login(username_or_email, password)
        if result.get("success"):
            # Save tokens
            self.config.set("access_token", result["data"].get("access_token"))
            if result["data"].get("refresh_token"):
                self.config.set("refresh_token", result["data"].get("refresh_token"))
        return result

    def logout(self) -> Dict[str, Any]:
        """Logout"""
        result = self.api.logout()
        # Clear tokens
        self.config.clear()
        return result

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info"""
        return self.api.get_current_user()

    # ========================================================================
    # PROJECTS
    # ========================================================================

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create project"""
        return self.api.create_project(name, description)

    def list_projects(self) -> Dict[str, Any]:
        """List projects"""
        return self.api.list_projects()

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details"""
        return self.api.get_project(project_id)

    def update_project(self, project_id: str, name: Optional[str] = None,
                      description: Optional[str] = None) -> Dict[str, Any]:
        """Update project"""
        return self.api.update_project(project_id, name, description)

    def archive_project(self, project_id: str) -> Dict[str, Any]:
        """Archive project"""
        return self.api.archive_project(project_id)

    def restore_project(self, project_id: str) -> Dict[str, Any]:
        """Restore archived project"""
        return self.api.restore_project(project_id)

    def destroy_project(self, project_id: str) -> Dict[str, Any]:
        """Permanently delete project"""
        return self.api.destroy_project(project_id)

    # ========================================================================
    # SESSIONS
    # ========================================================================

    def start_session(self, project_id: str) -> Dict[str, Any]:
        """Start Socratic session"""
        return self.api.start_session(project_id)

    def get_next_question(self, session_id: str) -> Dict[str, Any]:
        """Get next Socratic question"""
        return self.api.get_next_question(session_id)

    def submit_answer(self, session_id: str, question_id: str,
                     answer: str) -> Dict[str, Any]:
        """Submit answer to question"""
        return self.api.submit_answer(session_id, question_id, answer)

    def send_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send chat message"""
        return self.api.send_chat_message(session_id, message)

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End session"""
        return self.api.end_session(session_id)

    def list_sessions(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """List sessions"""
        if project_id:
            return self.api.list_sessions(project_id)
        # Get all sessions - need to call API directly
        return self.api._request("GET", "/api/v1/sessions").json()

    def set_session_mode(self, session_id: str, mode: str) -> Dict[str, Any]:
        """Set session mode (socratic or direct_chat)"""
        return self.api.set_session_mode(session_id, mode)

    # ========================================================================
    # SPECIFICATIONS
    # ========================================================================

    def create_specification(self, project_id: str, title: str,
                            spec_type: str = "feature",
                            description: str = "") -> Dict[str, Any]:
        """Create specification"""
        return self.api.create_specification(project_id, title, spec_type, description)

    def list_specifications(self, project_id: str) -> Dict[str, Any]:
        """List specifications"""
        return self.api.list_specifications(project_id)

    def get_specification(self, spec_id: str) -> Dict[str, Any]:
        """Get specification"""
        return self.api.get_specification(spec_id)

    def approve_specification(self, spec_id: str) -> Dict[str, Any]:
        """Approve specification"""
        return self.api.approve_specification(spec_id)

    def implement_specification(self, spec_id: str) -> Dict[str, Any]:
        """Mark as implemented"""
        return self.api.implement_specification(spec_id)

    def delete_specification(self, spec_id: str) -> Dict[str, Any]:
        """Delete specification"""
        return self.api.delete_specification(spec_id)

    # ========================================================================
    # TEAMS
    # ========================================================================

    def create_team(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create team"""
        return self.api.create_team(name, description)

    def list_teams(self) -> Dict[str, Any]:
        """List teams"""
        return self.api.list_teams()

    def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get team details"""
        return self.api.get_team(team_id)

    def invite_to_team(self, team_id: str, email: str) -> Dict[str, Any]:
        """Invite to team"""
        return self.api.invite_to_team(team_id, email)

    def list_team_members(self, team_id: str) -> Dict[str, Any]:
        """List team members"""
        return self.api.list_team_members(team_id)

    # ========================================================================
    # DOCUMENTS
    # ========================================================================

    def upload_document(self, project_id: str, file_path: str) -> Dict[str, Any]:
        """Upload document"""
        return self.api.upload_document(project_id, file_path)

    def list_documents(self, project_id: str) -> Dict[str, Any]:
        """List documents"""
        return self.api.list_documents(project_id)

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete document"""
        return self.api.delete_document(doc_id)

    # ========================================================================
    # CODE GENERATION
    # ========================================================================

    def generate_code(self, project_id: str, language: str = "python",
                     pattern: str = "rest-api") -> Dict[str, Any]:
        """Generate code"""
        return self.api.generate_code(project_id, language, pattern)

    def list_code_generations(self, project_id: str) -> Dict[str, Any]:
        """List code generations"""
        return self.api.list_code_generations(project_id)

    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get generation status"""
        return self.api.get_generation_status(generation_id)

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get analytics dashboard"""
        return self.api.get_analytics_dashboard()

    def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get project analytics"""
        return self.api.get_project_analytics(project_id)

    # ========================================================================
    # QUALITY
    # ========================================================================

    def run_quality_checks(self, project_id: str) -> Dict[str, Any]:
        """Run quality checks"""
        return self.api.run_quality_checks(project_id)

    def get_quality_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get quality metrics"""
        return self.api.get_quality_metrics(project_id)

    # ========================================================================
    # INSIGHTS
    # ========================================================================

    def get_project_insights(self, project_id: str) -> Dict[str, Any]:
        """Get project insights"""
        return self.api.get_project_insights(project_id)

    def analyze_specification_gaps(self, project_id: str) -> Dict[str, Any]:
        """Analyze gaps"""
        return self.api.analyze_specification_gaps(project_id)

    def analyze_project_risks(self, project_id: str) -> Dict[str, Any]:
        """Analyze risks"""
        return self.api.analyze_project_risks(project_id)

    # ========================================================================
    # GITHUB
    # ========================================================================

    def import_from_github(self, project_id: str, repo_url: str) -> Dict[str, Any]:
        """Import from GitHub"""
        return self.api.import_from_github(project_id, repo_url)

    def analyze_github_repo(self, repo_url: str) -> Dict[str, Any]:
        """Analyze GitHub repo"""
        return self.api.analyze_github_repo(repo_url)

    # ========================================================================
    # LLM SELECTION
    # ========================================================================

    def list_available_llms(self) -> Dict[str, Any]:
        """List available LLM models"""
        return self.api.list_available_llms()

    def get_current_llm(self) -> Dict[str, Any]:
        """Get currently selected LLM"""
        return self.api.get_current_llm()

    def select_llm(self, provider: str, model: str) -> Dict[str, Any]:
        """Select LLM provider and model"""
        return self.api.select_llm(provider, model)

    def get_llm_usage(self) -> Dict[str, Any]:
        """Get LLM usage"""
        return self.api.get_llm_usage()

    # ========================================================================
    # SEARCH & UTILITIES
    # ========================================================================

    def search(self, query: str, resource_type: Optional[str] = None) -> Dict[str, Any]:
        """Search across projects"""
        return self.api.search(query, resource_type)

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health"""
        return self.api.get_system_health()

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return bool(self.api.access_token)

    def clear_cache(self) -> None:
        """Clear local cache"""
        self.config.clear()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        return self.config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set config value"""
        self.config.set(key, value)


# Convenience function for IDE plugins
def create_socrates_cli(api_url: str = "http://localhost:8000") -> SocratesCLI:
    """Factory function to create CLI instance"""
    return SocratesCLI(api_url)


__all__ = ["SocratesCLI", "create_socrates_cli"]
