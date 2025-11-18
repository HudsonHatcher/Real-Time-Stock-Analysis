import os
from sqlalchemy import create_engine, Column, String, DateTime, Numeric, BigInteger, Date, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://stock:stockpw@db:5432/stocks")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Prices(Base):
    __tablename__ = "prices"
    ticker = Column(String, primary_key=True)
    ts = Column(DateTime(timezone=True), primary_key=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    __table_args__ = (PrimaryKeyConstraint('ticker', 'ts'),)

class Fundamentals(Base):
    __tablename__ = "fundamentals"
    ticker = Column(String, primary_key=True)
    as_of = Column(Date)
    pe_ttm = Column(Numeric(10, 2))
    market_cap = Column(Numeric(20, 2))
    fifty_two_week_high = Column(Numeric(10, 2))
    fifty_two_week_low = Column(Numeric(10, 2))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

