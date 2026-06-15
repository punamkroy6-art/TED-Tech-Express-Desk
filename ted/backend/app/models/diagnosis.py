from sqlalchemy import Column, String, DateTime, Integer, SmallInteger, Float, ForeignKey, CheckConstraint, Text, func, UUID, JSON
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class DiagnosisResult(Base):
    __tablename__ = 'diagnosis_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    run_number = Column(SmallInteger, default=1)
    
    input_error_text = Column(Text, nullable=True)
    input_device_info = Column(JSON, nullable=True)
    ocr_output = Column(JSON, nullable=True)
    
    diagnosis = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    severity = Column(String(20), nullable=True)  # 'low'|'medium'|'high'|'critical'
    
    fix_steps = Column(JSON, nullable=True)  # List of strings or dictionaries
    kb_references = Column(JSON, nullable=True)  # List of KB links
    past_ticket_refs = Column(JSON, nullable=True)  # List of tickets
    
    suggested_group = Column(String(100), nullable=True)
    action_taken = Column(String(30), nullable=True)  # 'self_resolve'|'guided'|'ticket'
    
    llm_model = Column(String(100), nullable=True)
    llm_tokens_used = Column(Integer, nullable=True)
    processing_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('confidence BETWEEN 0 AND 1', name='chk_confidence'),
    )

    # Relationships
    session = relationship("Session", backref="diagnoses")
