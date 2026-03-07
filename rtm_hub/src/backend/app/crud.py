from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
import uuid

def generate_req_id() -> str:
    return f"REQ-{uuid.uuid4().hex[:6].upper()}"

def create_requirement(db: Session, req: schemas.RequirementCreate, created_by: int = 1):
    db_req = models.Requirement(
        req_id=generate_req_id(),
        title=req.title,
        description=req.description,
        priority=req.priority,
        source=req.source,
        created_by=created_by
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

def get_requirements(db: Session, skip: int = 0, limit: int = 100, 
                     status: str = None, priority: str = None, search: str = None):
    query = db.query(models.Requirement)
    
    if status:
        query = query.filter(models.Requirement.status == status)
    if priority:
        query = query.filter(models.Requirement.priority == priority)
    if search:
        query = query.filter(
            (models.Requirement.title.contains(search)) | 
            (models.Requirement.description.contains(search))
        )
    
    return query.offset(skip).limit(limit).all()

def get_requirement_by_id(db: Session, req_id: str):
    return db.query(models.Requirement).filter(models.Requirement.req_id == req_id).first()

def create_traceability_link(db: Session, from_req_id: int, link: schemas.TraceabilityLinkCreate):
    db_link = models.TraceabilityLink(
        from_requirement_id=from_req_id,
        to_artifact_id=link.to_artifact_id,
        artifact_type=link.artifact_type,
        link_type=link.link_type
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_rtm_matrix(db: Session):
    requirements = db.query(models.Requirement).all()
    rtm_data = []
    
    for req in requirements:
        links = db.query(models.TraceabilityLink).filter(
            models.TraceabilityLink.from_requirement_id == req.id
        ).all()
        
        linked_artifacts = ", ".join([
            f"{link.artifact_type}-{link.to_artifact_id}" for link in links
        ])
        
        rtm_data.append({
            "requirement_id": req.req_id,
            "title": req.title,
            "status": req.status.value,
            "priority": req.priority.value,
            "linked_artifacts": linked_artifacts,
            "last_updated": req.updated_at
        })
    
    return rtm_data