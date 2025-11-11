"""
Programming domain implementation for Socrates2.

Defines specifications, questions, exports, and rules for software development projects.
"""

from typing import List
from ..base import BaseDomain, Question, ExportFormat, ConflictRule, SeverityLevel


class ProgrammingDomain(BaseDomain):
    """
    Software Programming domain for Socrates2.

    Handles specification and code generation for software projects.
    Supports 8+ programming languages with specialized patterns.
    """

    domain_id = "programming"
    name = "Software Programming"
    version = "1.0.0"
    description = "Specification and code generation for software development projects"

    def get_categories(self) -> List[str]:
        """Return specification categories for programming."""
        return [
            "Performance",
            "Security",
            "Scalability",
            "Usability",
            "Reliability",
            "Maintainability",
            "Accessibility",
        ]

    def get_questions(self) -> List[Question]:
        """Return Socratic questions for programming domain."""
        return [
            # Performance questions
            Question(
                question_id="perf_1",
                text="What is your target response time for critical operations?",
                category="Performance",
                difficulty="medium",
                help_text="e.g., API response: <200ms, page load: <1s",
                example_answer="API response: <200ms, page load: <3s",
            ),
            Question(
                question_id="perf_2",
                text="What is your expected throughput (requests per second)?",
                category="Performance",
                difficulty="medium",
                help_text="e.g., 1000 req/s, 100,000 events/day",
                example_answer="1000 requests per second during peak hours",
            ),
            Question(
                question_id="perf_3",
                text="What are your memory constraints?",
                category="Performance",
                difficulty="easy",
                help_text="e.g., <512MB for mobile, <4GB for server",
                example_answer="<512MB for mobile clients, <4GB per server instance",
            ),

            # Security questions
            Question(
                question_id="sec_1",
                text="What encryption standard will you use for data in transit?",
                category="Security",
                difficulty="medium",
                help_text="e.g., TLS 1.2+, AES-256",
                example_answer="TLS 1.3 for all network communication",
            ),
            Question(
                question_id="sec_2",
                text="How will you store sensitive data (passwords, tokens)?",
                category="Security",
                difficulty="hard",
                help_text="e.g., bcrypt for passwords, encrypted tokens",
                example_answer="bcrypt with salt for passwords, JWT tokens encrypted with AES-256",
            ),
            Question(
                question_id="sec_3",
                text="What authentication mechanism will you implement?",
                category="Security",
                difficulty="medium",
                help_text="e.g., OAuth 2.0, JWT, session-based",
                example_answer="JWT with 15-minute expiration and refresh tokens",
            ),

            # Scalability questions
            Question(
                question_id="scale_1",
                text="How will you handle increased load?",
                category="Scalability",
                difficulty="hard",
                help_text="e.g., horizontal scaling, caching, load balancing",
                example_answer="Horizontal scaling with auto-scaling groups and Redis caching",
            ),
            Question(
                question_id="scale_2",
                text="What caching strategy will you use?",
                category="Scalability",
                difficulty="medium",
                help_text="e.g., Redis, memcached, CDN",
                example_answer="Redis for session and API response caching with 5-minute TTL",
            ),

            # Usability questions
            Question(
                question_id="usab_1",
                text="What is your target user expertise level?",
                category="Usability",
                difficulty="easy",
                help_text="e.g., expert developers, business users, children",
                example_answer="Intermediate developers with some Python experience",
            ),
            Question(
                question_id="usab_2",
                text="What accessibility standards must you meet?",
                category="Usability",
                difficulty="medium",
                help_text="e.g., WCAG 2.1 AA, keyboard navigation",
                example_answer="WCAG 2.1 Level AA compliance",
            ),

            # Reliability questions
            Question(
                question_id="rel_1",
                text="What is your target uptime percentage?",
                category="Reliability",
                difficulty="easy",
                help_text="e.g., 99.9%, 99.99%",
                example_answer="99.9% uptime (8.76 hours downtime/year)",
            ),
            Question(
                question_id="rel_2",
                text="How will you handle errors and failures?",
                category="Reliability",
                difficulty="hard",
                help_text="e.g., retry logic, circuit breakers, graceful degradation",
                example_answer="Exponential backoff retries, circuit breakers for external APIs",
            ),

            # Maintainability questions
            Question(
                question_id="maint_1",
                text="What code style and standards will you follow?",
                category="Maintainability",
                difficulty="easy",
                help_text="e.g., PEP 8, Google style guide, linting rules",
                example_answer="PEP 8 with black formatter, isort for imports",
            ),
            Question(
                question_id="maint_2",
                text="What testing coverage do you target?",
                category="Maintainability",
                difficulty="medium",
                help_text="e.g., 80%, 90%, 100% coverage",
                example_answer="90% code coverage with unit and integration tests",
            ),
        ]

    def get_export_formats(self) -> List[ExportFormat]:
        """Return supported code generation formats."""
        return [
            ExportFormat(
                format_id="python",
                name="Python",
                description="Python class/function generation",
                file_extension=".py",
                mime_type="text/x-python",
                template_id="python_class",
            ),
            ExportFormat(
                format_id="javascript",
                name="JavaScript",
                description="JavaScript class/function generation",
                file_extension=".js",
                mime_type="text/javascript",
                template_id="js_class",
            ),
            ExportFormat(
                format_id="typescript",
                name="TypeScript",
                description="TypeScript class/interface generation",
                file_extension=".ts",
                mime_type="text/typescript",
                template_id="ts_class",
            ),
            ExportFormat(
                format_id="go",
                name="Go",
                description="Go struct/interface generation",
                file_extension=".go",
                mime_type="text/x-go",
                template_id="go_struct",
            ),
            ExportFormat(
                format_id="java",
                name="Java",
                description="Java class generation",
                file_extension=".java",
                mime_type="text/x-java-source",
                template_id="java_class",
            ),
            ExportFormat(
                format_id="rust",
                name="Rust",
                description="Rust struct generation",
                file_extension=".rs",
                mime_type="text/x-rust",
                template_id="rust_struct",
            ),
            ExportFormat(
                format_id="csharp",
                name="C#",
                description="C# class generation",
                file_extension=".cs",
                mime_type="text/x-csharp",
                template_id="csharp_class",
            ),
            ExportFormat(
                format_id="kotlin",
                name="Kotlin",
                description="Kotlin data class generation",
                file_extension=".kt",
                mime_type="text/x-kotlin",
                template_id="kotlin_dataclass",
            ),
        ]

    def get_conflict_rules(self) -> List[ConflictRule]:
        """Return conflict detection rules for programming."""
        return [
            ConflictRule(
                rule_id="perf_conflict",
                name="Performance Consistency",
                description="Response time requirements must be consistent",
                condition="response_time specifications must not contradict",
                severity=SeverityLevel.ERROR,
                message="Conflicting response time specifications",
            ),
            ConflictRule(
                rule_id="sec_conflict",
                name="Security Consistency",
                description="Security standards must align",
                condition="encryption_standard specifications must be compatible",
                severity=SeverityLevel.ERROR,
                message="Conflicting security specifications",
            ),
            ConflictRule(
                rule_id="scale_conflict",
                name="Scalability Planning",
                description="Scalability approach must be feasible",
                condition="throughput and resource constraints must align",
                severity=SeverityLevel.WARNING,
                message="Scalability specifications may be unrealistic",
            ),
            ConflictRule(
                rule_id="arch_consistency",
                name="Architectural Alignment",
                description="Architecture must support requirements",
                condition="performance targets must be achievable with proposed architecture",
                severity=SeverityLevel.ERROR,
                message="Requirements conflict with proposed architecture",
            ),
        ]

    def get_quality_analyzers(self) -> List[str]:
        """Return quality analyzers for programming domain."""
        return [
            "bias_detector",  # Universal analyzer
            "performance_validator",
            "security_validator",
            "scalability_checker",
        ]
