from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime

class RawEvent(BaseModel):
    """ Event received from PostHog """
    event: str
    distinct_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class UserActivity(BaseModel):
    """ Clean line item for LLM """
    time_ago: str
    action: str
    session_id: str

class UserContextResponse(BaseModel):
    """ Full prompt context """
    user_id: str
    summary: str
    user_activity: List[UserActivity] 