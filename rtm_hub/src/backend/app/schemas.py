from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .models import PriorityEnum, StatusEnum

class RequirementBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.Medium
    source: Optional[str] = None

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    source: Optional[str] = None

class Requirement(RequirementBase):
    id: int
    req_id: str
    status: StatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TraceabilityLinkCreate(BaseModel):
    to_artifact_id: int
    artifact_type: str
    link_type: str

class TraceabilityLink(BaseModel):
    id: int
    from_requirement_id: int
    to_artifact_id: int
    artifact_type: str
    link_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class RTMExport(BaseModel):
    requirement_id: str
    title: str
    status: str
    priority: str
    linked_artifacts: str
    last_updated: datetime