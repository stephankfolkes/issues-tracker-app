"""Project schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project schema"""

    name: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=2, max_length=10, pattern=r"^[A-Z0-9]+$")
    description: str = Field(..., min_length=50, max_length=500)


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class Project(ProjectBase):
    """Schema for project response"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberBase(BaseModel):
    """Base project member schema"""

    user_id: int
    role: str = "member"


class ProjectMemberCreate(ProjectMemberBase):
    """Schema for adding a project member"""

    pass


class ProjectMember(ProjectMemberBase):
    """Schema for project member response"""

    id: int
    project_id: int
    joined_at: datetime

    class Config:
        from_attributes = True
