from sqlalchemy import Column, String, DateTime, Integer, SmallInteger, ForeignKey, CheckConstraint, func, UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(100), ForeignKey('employees.employee_id'), nullable=True, index=True)
    kiosk_id = Column(String(50), nullable=False)
    started_at = Column(DateTime, server_default=func.now(), index=True)
    ended_at = Column(DateTime, nullable=True)
    
    # We will compute duration in python or query using standard property, or map directly
    duration_secs = Column(Integer, nullable=True)
    
    auth_method = Column(String(20), nullable=True)  # 'badge' | 'sso'
    issue_type = Column(String(50), nullable=True)   # 'software'|'hardware'|'network'|'loaner'
    outcome = Column(String(30), nullable=True, index=True)      # 'resolved'|'ticket_created'|'abandoned'
    ticket_id = Column(String(100), nullable=True)
    csat_score = Column(SmallInteger, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('csat_score BETWEEN 1 AND 5', name='chk_csat_score'),
    )

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
