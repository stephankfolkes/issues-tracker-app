"""Project service"""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectMember, ProjectRole
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectMemberCreate, ProjectUpdate


class ProjectService:
    """Service for project operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectRepository(db)

    def get_by_id(self, project_id: int) -> Project:
        """Get project by ID"""
        project = self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects"""
        return self.repo.get_all(skip, limit)

    def get_user_projects(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects for a user"""
        return self.repo.get_user_projects(user_id, skip, limit)

    def create(self, project_data: ProjectCreate, creator: User) -> Project:
        """Create a new project"""
        # Check if project key already exists
        if self.repo.get_by_key(project_data.key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project key already exists",
            )

        # Validate description is provided and meets minimum length
        if not project_data.description or len(project_data.description.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project description is required (minimum 50 characters)",
            )

        # Create project
        project = Project(
            name=project_data.name,
            key=project_data.key,
            description=project_data.description,
        )
        project = self.repo.create(project)

        # Add creator as owner
        member = ProjectMember(
            project_id=project.id,
            user_id=creator.id,
            role=ProjectRole.OWNER.value,
        )
        self.repo.add_member(member)

        return project

    def update(self, project_id: int, project_data: ProjectUpdate, user: User) -> Project:
        """Update a project"""
        project = self.get_by_id(project_id)

        # Check permissions
        self._check_owner_permission(project_id, user.id)

        # Update fields
        if project_data.name:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description

        return self.repo.update(project)

    def delete(self, project_id: int, user: User) -> None:
        """Delete a project"""
        project = self.get_by_id(project_id)

        # Check permissions
        self._check_owner_permission(project_id, user.id)

        self.repo.delete(project)

    def add_member(self, project_id: int, member_data: ProjectMemberCreate, user: User) -> ProjectMember:
        """Add a member to project"""
        project = self.get_by_id(project_id)

        # Check permissions
        self._check_owner_permission(project_id, user.id)

        # Check if already a member
        if self.repo.is_member(project_id, member_data.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member",
            )

        member = ProjectMember(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )

        return self.repo.add_member(member)

    def remove_member(self, project_id: int, user_id: int, current_user: User) -> None:
        """Remove a member from project"""
        project = self.get_by_id(project_id)

        # Check permissions
        self._check_owner_permission(project_id, current_user.id)

        member = self.repo.get_member(project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )

        # Cannot remove owner
        if member.role == ProjectRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner",
            )

        self.repo.remove_member(member)

    def check_access(self, project_id: int, user_id: int) -> bool:
        """Check if user has access to project"""
        return self.repo.is_member(project_id, user_id)

    def _check_owner_permission(self, project_id: int, user_id: int) -> None:
        """Check if user is project owner"""
        member = self.repo.get_member(project_id, user_id)
        if not member or member.role != ProjectRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can perform this action",
            )
