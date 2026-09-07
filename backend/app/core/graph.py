"""Resilient Neo4j graph database adapter with graceful offline fallback.
Ensures zero-crash operation when Neo4j is active or unavailable.
"""
from typing import List, Dict, Any, Optional
from app.core.config import get_settings

settings = get_settings()

_driver = None


def _get_neo4j_driver():
    global _driver
    if _driver is not None:
        return _driver

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=1.0,
            max_connection_lifetime=60
        )
        driver.verify_connectivity()
        _driver = driver
    except Exception:
        _driver = False  # Neo4j unavailable

    return _driver


class GraphClient:
    """Unified Neo4j graph interface with automatic fallback."""

    @property
    def is_available(self) -> bool:
        driver = _get_neo4j_driver()
        return driver is not False and driver is not None

    def query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run Cypher query if Neo4j is connected, else return empty list."""
        driver = _get_neo4j_driver()
        if not driver:
            return []

        try:
            with driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]
        except Exception:
            return []

    def sync_scheme_node(self, scheme_id: str, name: str, ministry: str) -> bool:
        """Create or update scheme node in graph database."""
        driver = _get_neo4j_driver()
        if not driver:
            return False

        cypher = """
        MERGE (s:Scheme {id: $scheme_id})
        SET s.name = $name, s.ministry = $ministry, s.updated_at = timestamp()
        RETURN s.id AS id
        """
        try:
            res = self.query(cypher, {"scheme_id": scheme_id, "name": name, "ministry": ministry})
            return len(res) > 0
        except Exception:
            return False

    def close(self):
        global _driver
        if _driver and _driver is not False:
            try:
                _driver.close()
            except Exception:
                pass
            _driver = None


_graph_instance = GraphClient()


def get_graph_client() -> GraphClient:
    """Get the singleton graph client."""
    return _graph_instance
