from sqlalchemy import Column, String, DateTime, Integer, func, UUID, JSON
from app.database import Base

class AuditLog(Base):
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor = Column(String(100), nullable=True)  # 'employee_id' or 'SYSTEM'
    action = Column(String(100), nullable=False)  # e.g., 'SESSION_START'
    detail = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Fully compatible with IPv4/IPv6 and INET
    
    created_at = Column(DateTime, server_default=func.now())
