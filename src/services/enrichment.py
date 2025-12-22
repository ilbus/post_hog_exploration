from pydantic import BaseModel
from src.core.schemas import RawEvent


class EnrichedEvent(BaseModel):
    user_id: str
    session_id: str
    semantic_label: str
    original_event: RawEvent


def enrich_event(event: RawEvent) -> EnrichedEvent:
    props = event.properties
    label = f"Triggered {event.event}"

    if event.event == "$pageview":
        path = props.get("$pathname", "unknown")
        label = f"Viewed page: {path}"

    elif event.event == "$autocapture":
        text = props.get("$element_text", "")
        if "upgrade-btn" in props.get("attr__class", ""):
            label = "Clicked 'Upgrade Plan' Button"
        elif text:
            label = f"Clicked element: '{text}'"

    return EnrichedEvent(
        user_id=event.distinct_id,
        session_id=props.get("$session_id", "global"),
        semantic_label=label,
        original_event=event,
    )
