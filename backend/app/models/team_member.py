"""
TeamMember model for authentication database (socrates_auth).
Represents membership of a user in a team with a specific role.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..core.database import Base


class TeamMember(Base):
    """
    TeamMember model - stores in socrates_auth database.

    Note: This model does NOT inherit from BaseModel because it uses
    joined_at instead of created_at, and doesn't need updated_at.

    Fields:
    - id: UUID primary key
    - team_id: Foreign key to teams table
    - user_id: Foreign key to users table
    - role: Member role (owner, lead, developer, viewer)
    - joined_at: Timestamp when member joined the team

    Relationships:
    - team: Team this membership belongs to
    - user: User who is a member
    """
    __tablename__ = "team_members"
    __table_args__ = (
        Index('idx_team_members_team_id', 'team_id'),
        Index('idx_team_members_user_id', 'user_id'),
        Index('idx_team_members_role', 'role'),
        UniqueConstraint('team_id', 'user_id', name='team_members_unique'),
        CheckConstraint("role IN ('owner', 'lead', 'developer', 'viewer')", name='team_members_role_valid'),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key (UUID)"
    )

    team_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('teams.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to teams table"
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to users table"
    )

    role = Column(
        String(50),
        nullable=False,
        comment="Member role: owner, lead, developer, viewer"
    )

    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when member joined the team"
    )

    # Relationships (will be populated once relationships are defined)
    # team = relationship("Team", back_populates="members")
    # user = relationship("User", backref="team_memberships")

    def to_dict(self, exclude_fields: set = None) -> dict:
        """
        Convert model instance to dictionary.

        Args:
            exclude_fields: Set of field names to exclude

        Returns:
            Dictionary representation of model
        """
        exclude_fields = exclude_fields or set()
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert UUID and datetime to string for JSON serialization
                if isinstance(value, uuid.UUID):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()

                result[column.name] = value

        return result

    def __repr__(self):
        """String representation of team member"""
        return f"<TeamMember(id={self.id}, team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"
