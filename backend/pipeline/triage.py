from backend.models.schemas import TicketClassification, DraftReply
from backend.config import settings


def should_route_to_review(
    classification: TicketClassification,
    draft: DraftReply,
) -> bool:
    return (
        classification.confidence < settings.confidence_threshold
        or draft.confidence < settings.confidence_threshold
    )
