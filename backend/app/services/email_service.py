"""Email notification service using SendGrid.

Handles sending email notifications for various events:
- Conflict alerts
- Trial expiration reminders
- Maturity milestones
- Mention notifications
"""
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EmailService:
    """Send email notifications using SendGrid API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize email service with SendGrid API key.

        Args:
            api_key: SendGrid API key (from environment if not provided)
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            self.Mail = Mail
            self.sg = SendGridAPIClient(api_key or "")
            self.enabled = bool(api_key)
        except ImportError:
            logger.warning("sendgrid not installed - email service disabled")
            self.enabled = False
            self.sg = None
            self.Mail = None

    def _send(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled or not self.sg or not self.Mail:
            logger.warning(f"Email service disabled - not sending to {to_email}")
            return False

        try:
            message = self.Mail(
                from_email="no-reply@socrates2.com",
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.sg.send(message)

            if 200 <= response.status_code < 300:
                logger.info(f"Email sent to {to_email}: {subject}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_conflict_alert(
        self,
        user_email: str,
        project_name: str,
        conflict_details: Dict[str, Any]
    ) -> bool:
        """Send conflict detection alert email.

        Args:
            user_email: User's email address
            project_name: Project name
            conflict_details: Details about the conflict

        Returns:
            True if sent successfully
        """
        subject = f"⚠️ Conflict Detected in Project: {project_name}"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d9534f;">Conflict Detected</h2>
                <p>A specification conflict has been detected in your project:</p>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Conflict:</strong> {conflict_details.get('description', 'Unknown')}</p>
                <p><strong>Detected at:</strong> {datetime.now(timezone.utc).isoformat()}</p>
                <p>
                    <a href="https://app.socrates2.com/projects/{conflict_details.get('project_id')}"
                       style="background-color: #5cb85c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View in Socrates2
                    </a>
                </p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated message. You can manage notification preferences in your account settings.
                </p>
            </body>
        </html>
        """
        return self._send(user_email, subject, html_content)

    def send_trial_expiring(
        self,
        user_email: str,
        days_left: int,
        user_name: Optional[str] = None
    ) -> bool:
        """Send trial expiration reminder email.

        Args:
            user_email: User's email address
            days_left: Number of days until trial expires
            user_name: User's name (optional)

        Returns:
            True if sent successfully
        """
        greeting = f"Hi {user_name}," if user_name else "Hello,"

        if days_left == 0:
            subject = "🚨 Your Socrates2 trial has expired"
            message = "Your trial period has ended."
            cta_text = "Upgrade Now"
        elif days_left == 1:
            subject = "⏰ Your Socrates2 trial expires tomorrow"
            message = f"Your trial period expires tomorrow. Upgrade to continue using Socrates2."
            cta_text = "Upgrade Now"
        else:
            subject = f"⏰ Your Socrates2 trial expires in {days_left} days"
            message = f"Your trial period expires in {days_left} days."
            cta_text = "View Plans"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <p>{greeting}</p>
                <p>{message}</p>
                <p>
                    After your trial ends, you'll need a paid subscription to continue using Socrates2.
                </p>
                <p>
                    <a href="https://app.socrates2.com/billing/plans"
                       style="background-color: #5cb85c; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        {cta_text}
                    </a>
                </p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    You're receiving this because your trial period is expiring soon.
                </p>
            </body>
        </html>
        """
        return self._send(user_email, subject, html_content)

    def send_maturity_milestone(
        self,
        user_email: str,
        project_name: str,
        maturity_percent: int,
        user_name: Optional[str] = None
    ) -> bool:
        """Send maturity milestone notification email.

        Args:
            user_email: User's email address
            project_name: Project name
            maturity_percent: Project maturity percentage (50, 75, or 100)
            user_name: User's name (optional)

        Returns:
            True if sent successfully
        """
        greeting = f"Hi {user_name}," if user_name else "Hello,"

        if maturity_percent == 50:
            subject = f"🎉 {project_name} is 50% complete!"
            message = "You're halfway there! Your project is 50% complete."
            emoji = "🎯"
        elif maturity_percent == 75:
            subject = f"✨ {project_name} is 75% complete!"
            message = "Almost there! Your project is 75% complete."
            emoji = "⚡"
        else:  # 100%
            subject = f"🏆 {project_name} is complete!"
            message = "Congratulations! Your project has reached 100% maturity."
            emoji = "🏆"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <p>{greeting}</p>
                <p style="font-size: 18px; font-weight: bold;">{emoji} {message}</p>
                <p>
                    <strong>Project:</strong> {project_name}<br>
                    <strong>Maturity:</strong> {maturity_percent}%
                </p>
                <p>
                    <a href="https://app.socrates2.com/projects/{project_name.lower().replace(' ', '-')}"
                       style="background-color: #5cb85c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Project
                    </a>
                </p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated message celebrating your progress!
                </p>
            </body>
        </html>
        """
        return self._send(user_email, subject, html_content)

    def send_mention_notification(
        self,
        user_email: str,
        mentioned_by: str,
        project_name: str,
        comment_excerpt: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send mention notification email.

        Args:
            user_email: User's email address
            mentioned_by: Name of user who mentioned them
            project_name: Project name
            comment_excerpt: Excerpt from the comment (truncated)
            user_name: User's name (optional)

        Returns:
            True if sent successfully
        """
        greeting = f"Hi {user_name}," if user_name else "Hello,"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <p>{greeting}</p>
                <p><strong>{mentioned_by}</strong> mentioned you in a comment on <strong>{project_name}</strong>:</p>
                <blockquote style="border-left: 4px solid #5cb85c; padding-left: 15px; margin-left: 0; color: #666;">
                    {comment_excerpt}
                </blockquote>
                <p>
                    <a href="https://app.socrates2.com/projects/{project_name.lower().replace(' ', '-')}"
                       style="background-color: #5cb85c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Discussion
                    </a>
                </p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    You're receiving this because you were mentioned in a comment.
                </p>
            </body>
        </html>
        """
        subject = f"💬 You were mentioned by {mentioned_by}"
        return self._send(user_email, subject, html_content)

    def send_digest(
        self,
        user_email: str,
        user_name: Optional[str],
        activities: List[Dict[str, Any]],
        frequency: str = "daily"
    ) -> bool:
        """Send activity digest email.

        Args:
            user_email: User's email address
            user_name: User's name (optional)
            activities: List of activity events
            frequency: Digest frequency (daily, weekly)

        Returns:
            True if sent successfully
        """
        greeting = f"Hi {user_name}," if user_name else "Hello,"
        freq_text = "daily" if frequency == "daily" else "weekly"

        # Format activities
        activity_html = ""
        for activity in activities[:10]:  # Limit to 10 activities
            activity_html += f"""
            <li>
                <strong>{activity.get('action', 'Unknown')}</strong><br>
                {activity.get('description', 'No description')}<br>
                <small style="color: #999;">{activity.get('timestamp', 'Unknown time')}</small>
            </li>
            """

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <p>{greeting}</p>
                <p>Here's your {freq_text} digest of activities in Socrates2:</p>
                <ul style="list-style-type: none; padding: 0;">
                    {activity_html}
                </ul>
                <p>
                    <a href="https://app.socrates2.com/activity"
                       style="background-color: #5cb85c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View All Activity
                    </a>
                </p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    You can manage notification preferences in your account settings.
                </p>
            </body>
        </html>
        """
        subject = f"📋 Your Socrates2 {freq_text} digest"
        return self._send(user_email, subject, html_content)
