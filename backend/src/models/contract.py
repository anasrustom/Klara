from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.config.database import Base
import enum
import uuid

class ContractStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class FileType(enum.Enum):
    pdf = "pdf"
    docx = "docx"

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ContractStatus), nullable=False, default=ContractStatus.pending)
    
    # Extracted data
    governing_law = Column(String)
    jurisdiction = Column(String)
    industry = Column(String)
    contract_type = Column(String)
    tags = Column(Text)  # JSON string array
    
    # AI Analysis
    summary = Column(Text)
    purpose = Column(Text)
    scope = Column(Text)
    analysis_json = Column(Text)  # Full model output, kept so nothing is lost
    analysis_error = Column(Text)
    
    # Source text, kept so the search index can be rebuilt after a restart
    language = Column(String)
    pages = Column(Integer)
    extracted_text = Column(Text)
    page_offsets = Column(Text)  # JSON int array: start char of each page
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parties = relationship("ContractParty", back_populates="contract", cascade="all, delete-orphan")
    key_dates = relationship("KeyDate", back_populates="contract", cascade="all, delete-orphan")
    financial_terms = relationship("FinancialTerm", back_populates="contract", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")

class PartyType(enum.Enum):
    individual = "individual"
    organization = "organization"

class PartyRole(enum.Enum):
    client = "client"
    vendor = "vendor"
    partner = "partner"
    other = "other"

class ContractParty(Base):
    __tablename__ = "contract_parties"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(PartyType), nullable=False)
    role = Column(Enum(PartyRole), nullable=False)
    source_page = Column(Integer)
    source_snippet = Column(Text)
    
    contract = relationship("Contract", back_populates="parties")

class DateType(enum.Enum):
    effective_date = "effective_date"
    expiration_date = "expiration_date"
    renewal_date = "renewal_date"
    milestone = "milestone"
    other = "other"

class KeyDate(Base):
    __tablename__ = "key_dates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    date_type = Column(Enum(DateType), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(Text)
    source_page = Column(Integer)
    source_snippet = Column(Text)
    
    contract = relationship("Contract", back_populates="key_dates")

class TermType(enum.Enum):
    payment = "payment"
    penalty = "penalty"
    deposit = "deposit"
    other = "other"

class FinancialTerm(Base):
    __tablename__ = "financial_terms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    term_type = Column(Enum(TermType), nullable=False)
    amount = Column(Float)  # Null when the contract states a term without a figure
    currency = Column(String)  # Only what the contract states; never assumed
    schedule = Column(String)
    description = Column(Text)
    source_page = Column(Integer)
    source_snippet = Column(Text)
    
    contract = relationship("Contract", back_populates="financial_terms")
