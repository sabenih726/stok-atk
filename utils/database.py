import os
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_AVAILABLE = DATABASE_URL is not None

# Only create engine if database is available
if DATABASE_AVAILABLE:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

# Database Models
class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    item_id = Column(String(50), primary_key=True)
    item_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    initial_stock = Column(Integer, default=0)
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Float, default=0.0)
    description = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(String(50), primary_key=True)
    item_id = Column(String(50), nullable=False)
    item_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    requester_name = Column(String(200), nullable=False)
    department = Column(String(100), nullable=False)
    purpose = Column(Text)
    priority = Column(String(50), default='Normal')
    status = Column(String(50), default='Pending')
    order_date = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(200))
    approved_date = Column(DateTime)
    notes = Column(Text)

def get_db():
    """Get database session"""
    if not DATABASE_AVAILABLE:
        return None
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def create_tables():
    """Create all tables in the database"""
    if DATABASE_AVAILABLE:
        Base.metadata.create_all(bind=engine)

def init_database():
    """Initialize the database with tables"""
    if not DATABASE_AVAILABLE:
        return False
    try:
        create_tables()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
