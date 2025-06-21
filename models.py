from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    log = Column(Text)
    explanation = Column(Text)
    fix = Column(Text)
