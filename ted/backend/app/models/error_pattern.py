import json
from sqlalchemy import Column, String, DateTime, SmallInteger, Float, Boolean, Text, func, UUID, JSON
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from app.database import Base

class SQLiteCompatibleArray(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, item_type=String, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is None:
            return None
        return json.loads(value)

class ErrorPattern(Base):
    __tablename__ = 'error_patterns'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_code = Column(String(100), nullable=True)
    keywords = Column(SQLiteCompatibleArray(String), nullable=False)  # array of search terms
    os_platform = Column(String(50), nullable=True, index=True)  # 'windows'|'macos'|'linux'|'any'
    category = Column(String(100), nullable=True, index=True)  # 'bsod'|'network'|'auth'|'driver'...
    severity = Column(String(20), default='medium')
    description = Column(Text, nullable=True)
    fix_steps = Column(JSON, nullable=False)  # list of step dicts
    estimated_mins = Column(SmallInteger, nullable=True)
    success_rate = Column(Float, nullable=True)
    source = Column(String(30), nullable=True)  # 'manual'|'imported'|'ml_generated'
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
