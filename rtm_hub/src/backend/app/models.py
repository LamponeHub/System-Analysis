from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class PriorityEnum(str, enum.Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"

class StatusEnum(str, enum.Enum):
    Draft = "Draft"
    Active = "Active"
    Approved = "Approved"
    Rejected = "Rejected"

class Requirement(Base):
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    req_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.Medium)
    status = Column(Enum(StatusEnum), default=StatusEnum.Draft)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    links_from = relationship("TraceabilityLink", foreign_keys="TraceabilityLink.from_requirement_id", back_populates="from_requirement")
    links_to = relationship("TraceabilityLink", foreign_keys="TraceabilityLink.to_artifact_id", back_populates="to_requirement")
    versions = relationship("Version", back_populates="requirement")

class TraceabilityLink(Base):
    __tablename__ = "traceability_links"
    
    id = Column(Integer, primary_key=True, index=True)
    from_requirement_id = Column(Integer, ForeignKey("requirements.id"))
    to_artifact_id = Column(Integer)
    artifact_type = Column(String)  # Requirement, Task, TestCase
    link_type = Column(String)  # Derives, Satisfies, Verifies, Depends
    created_at = Column(DateTime, default=datetime.utcnow)
    
    from_requirement = relationship("Requirement", foreign_keys=[from_requirement_id], back_populates="links_from")
    to_requirement = relationship("Requirement", foreign_keys=[to_artifact_id], back_populates="links_to")

class Version(Base):
    __tablename__ = "versions"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    version_number = Column(Integer)
    changes_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    requirement = relationship("Requirement", back_populates="versions")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)