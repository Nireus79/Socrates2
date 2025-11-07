"""
Team model for authentication database (socrates_auth).
Represents a team that can have multiple members and can be shared projects.
"""
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Team(BaseModel):
    """
    Team model - stores in socrates_auth database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - name: Team name
    - description: Optional team description
    - created_by: User who created the team (FK to users)
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)

    Relationships:
    - creator: User who created the team
    - members: TeamMember records for this team
    """
    __tablename__ = "teams"
    __table_args__ = (
        Index('idx_teams_created_by', 'created_by'),
        Index('idx_teams_created_at', 'created_at', postgresql_using='btree', postgresql_ops={'created_at': 'DESC'}),
    )

    name = Column(
        String(255),
        nullable=False,
        comment="Team name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Team description"
    )

    created_by = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        comment="User who created the team"
    )

    # Relationships (will be populated once TeamMember model is created)
    # creator = relationship("User", foreign_keys=[created_by], backref="created_teams")
    # members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of team"""
        return f"<Team(id={self.id}, name={self.name}, created_by={self.created_by})>"
