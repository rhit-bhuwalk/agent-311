"""
In-memory storage for messages and requests.
In production, replace this with a real database (PostgreSQL, MongoDB, etc.)
"""
from typing import List, Dict, Any, Optional


class Storage:
    """In-memory storage singleton."""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.requests: List[Dict[str, Any]] = []


# Global storage instance
storage = Storage()


def add_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new message to storage."""
    storage.messages.append(message)
    return message


def add_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new request to storage."""
    storage.requests.append(request)
    return request


def get_messages() -> List[Dict[str, Any]]:
    """Get all messages."""
    return storage.messages


def get_requests() -> List[Dict[str, Any]]:
    """Get all requests."""
    return storage.requests


def get_message_by_id(message_id: str) -> Optional[Dict[str, Any]]:
    """Get message by ID."""
    for msg in storage.messages:
        if msg.get('id') == message_id:
            return msg
    return None


def update_request_status(
    request_id: str,
    status: str,
    sf311_case_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update request status."""
    for request in storage.requests:
        if request.get('id') == request_id:
            request['status'] = status
            if sf311_case_id:
                request['sf311CaseId'] = sf311_case_id
            return request
    return None


def clear_all():
    """Clear all data (for testing)."""
    storage.messages.clear()
    storage.requests.clear()
