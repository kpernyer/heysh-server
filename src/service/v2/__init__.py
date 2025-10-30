"""API v2 - Clean RESTful API focused on domain concepts."""

from .routes_config import router as config_router
from .routes_digital_twins import router as digital_twins_router
from .routes_inbox import router as inbox_router
from .routes_knowledge_base import router as knowledge_base_router
from .routes_memberships import router as memberships_router
from .routes_topics import router as topics_router
from .routes_workflows import router as workflows_router

__all__ = [
    "topics_router",
    "memberships_router",
    "knowledge_base_router",
    "inbox_router",
    "digital_twins_router",
    "workflows_router",
    "config_router",
]

# API v2 Features:
# - Clean RESTful design
# - Focused on domain concepts (Topics, Memberships, Knowledge Base)
# - Proper content negotiation
# - Consistent resource naming
# - Role-based access control (Owner, Controller, Contributor, Member)
# - Support for HITL workflows via Inbox
# - Digital Twin user representations
# - Read-only workflow access