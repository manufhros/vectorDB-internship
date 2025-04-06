import logging

from vector_store.app.db.memory_store import InMemoryStore

logger = logging.getLogger(__name__)

try:
    store = InMemoryStore()
except Exception:
    logger.exception("❌ Failed to initialize InMemoryStore")
    raise
