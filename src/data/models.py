from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for simplicity, can be changed to PostgreSQL in production
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./maritime.db")

# Configure connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800  # Recycle connections after 30 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class AISMessage(Base):
    __tablename__ = "ais_messages"

    id = Column(Integer, primary_key=True, index=True)
    mmsi = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    course = Column(Float)
    heading = Column(Float)
    raw_message = Column(String)
    message_type = Column(Integer)
    status = Column(Integer, nullable=True)

    # Create composite indexes for efficient queries
    __table_args__ = (
        Index('idx_mmsi_timestamp', 'mmsi', 'timestamp'),
        Index('idx_lat_lon', 'latitude', 'longitude'),
        Index('idx_timestamp', 'timestamp'),
        Index('idx_mmsi_status', 'mmsi', 'status')
    )

class Vessel(Base):
    __tablename__ = "vessels"

    mmsi = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    vessel_type = Column(Integer, nullable=True)
    length = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_vessel_type', 'vessel_type'),
        Index('idx_created_at', 'created_at')
    )

class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String)

    __table_args__ = (
        Index('idx_port_location', 'latitude', 'longitude'),
        Index('idx_country', 'country')
    )

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully") 