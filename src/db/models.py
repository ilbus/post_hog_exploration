from sqlalchemy import Column, DateTime, Integer, String, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class EventModel(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    semantic_label = Column(String) 
    raw_payload = Column(JSON)
    created_at = Column(DateTime)
