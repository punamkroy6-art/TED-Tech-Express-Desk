from sqlalchemy import Column, String, DateTime, func, UUID
import uuid
from app.database import Base

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    department = Column(String(100), nullable=True)
    manager_email = Column(String(200), nullable=True)
    freshworks_id = Column(String(100), nullable=True)
    last_seen = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
