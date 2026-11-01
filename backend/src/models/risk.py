from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from src.config.database import Base
import enum
import uuid

class RiskType(enum.Enum):
    missing_clause = "missing_clause"
    unusual_clause = "unusual_clause"
    non_standard = "non_standard"
    inconsistency = "inconsistency"
    compliance = "compliance"

class RiskSeverity(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    risk_type = Column(Enum(RiskType), nullable=False)
    severity = Column(Enum(RiskSeverity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    clause_reference = Column(String)
    
    # Where the finding came from in the contract text
    source_chunk_id = Column(String)
    source_page = Column(Integer)
    source_snippet = Column(Text)
    
    contract = relationship("Contract", back_populates="risks")
