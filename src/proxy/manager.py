"""
Proxy Manager.

Manages proxy lifecycle, storage, and selection.
"""

import logging
from datetime import datetime
from typing import Callable

from .entity import Proxy, ProxyConfig

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages proxies for all users.

    Handles:
    - Proxy creation and storage
    - Proxy selection/prediction
    - Cross-community proxy resolution
    """

    def __init__(self, storage=None):
        """
        Initialize the proxy manager.

        Args:
            storage: Optional storage backend (defaults to in-memory)
        """
        self._storage = storage
        self._cache: dict[str, Proxy] = {}
        self._user_proxies: dict[str, list[str]] = {}  # user_id -> proxy_ids

        # Callbacks
        self._on_create: list[Callable] = []
        self._on_activate: list[Callable] = []

    def create_proxy(
        self,
        owner_id: str,
        name: str,
        role: str,
        communities: list[str] | None = None,
        config: ProxyConfig | None = None,
    ) -> Proxy:
        """
        Create a new proxy for a user.

        Args:
            owner_id: User who owns this proxy
            name: Display name for the proxy
            role: Role description ("Nonprofit Director")
            communities: Communities this proxy operates in
            config: Optional configuration

        Returns:
            Created proxy
        """
        proxy = Proxy(
            owner_id=owner_id,
            name=name,
            role=role,
            communities=communities or [],
            config=config or ProxyConfig(),
        )

        # Store
        self._cache[proxy.id] = proxy
        if owner_id not in self._user_proxies:
            self._user_proxies[owner_id] = []
        self._user_proxies[owner_id].append(proxy.id)

        # Persist if storage available
        if self._storage:
            self._persist_proxy(proxy)

        logger.info(f"Created proxy {proxy.id} for user {owner_id}")

        # Notify
        for callback in self._on_create:
            try:
                callback(proxy)
            except Exception as e:
                logger.error(f"Create callback error: {e}")

        return proxy

    def get_proxy(self, proxy_id: str) -> Proxy | None:
        """Get a proxy by ID."""
        if proxy_id in self._cache:
            return self._cache[proxy_id]

        if self._storage:
            proxy = self._load_proxy(proxy_id)
            if proxy:
                self._cache[proxy_id] = proxy
                return proxy

        return None

    def get_user_proxies(self, user_id: str) -> list[Proxy]:
        """Get all proxies for a user."""
        proxy_ids = self._user_proxies.get(user_id, [])
        proxies = []
        for proxy_id in proxy_ids:
            proxy = self.get_proxy(proxy_id)
            if proxy:
                proxies.append(proxy)
        return proxies

    def predict_proxy(
        self,
        user_id: str,
        context: dict | None = None,
    ) -> Proxy | None:
        """
        Predict which proxy the user likely wants.

        Uses:
        - Last active proxy
        - Context (community, topic)
        - Time of day patterns

        Args:
            user_id: User to predict for
            context: Optional context hints

        Returns:
            Predicted proxy or None
        """
        proxies = self.get_user_proxies(user_id)
        if not proxies:
            return None

        if len(proxies) == 1:
            return proxies[0]

        # Context-based prediction
        if context:
            community = context.get("community")
            topic = context.get("topic")

            # Match by community
            if community:
                for proxy in proxies:
                    if community in proxy.communities:
                        return proxy

            # Match by topic history
            if topic:
                for proxy in proxies:
                    if topic in proxy.topics_discussed:
                        return proxy

        # Fall back to most recently active
        proxies.sort(key=lambda p: p.last_active, reverse=True)
        return proxies[0]

    def activate_proxy(
        self,
        proxy_id: str,
        session_id: str,
    ) -> Proxy | None:
        """
        Activate a proxy for a session.

        Args:
            proxy_id: Proxy to activate
            session_id: Session joining

        Returns:
            Activated proxy or None
        """
        proxy = self.get_proxy(proxy_id)
        if not proxy:
            return None

        proxy.activate(session_id)

        if self._storage:
            self._persist_proxy(proxy)

        logger.info(f"Activated proxy {proxy_id} for session {session_id}")

        # Notify
        for callback in self._on_activate:
            try:
                callback(proxy, session_id)
            except Exception as e:
                logger.error(f"Activate callback error: {e}")

        return proxy

    def deactivate_proxy(self, proxy_id: str) -> None:
        """Deactivate a proxy."""
        proxy = self.get_proxy(proxy_id)
        if proxy:
            proxy.deactivate()
            if self._storage:
                self._persist_proxy(proxy)

    def update_proxy(self, proxy: Proxy) -> None:
        """Update a proxy."""
        self._cache[proxy.id] = proxy
        if self._storage:
            self._persist_proxy(proxy)

    def delete_proxy(self, proxy_id: str) -> bool:
        """Delete a proxy."""
        proxy = self._cache.pop(proxy_id, None)
        if proxy:
            if proxy.owner_id in self._user_proxies:
                self._user_proxies[proxy.owner_id].remove(proxy_id)

            if self._storage:
                self._delete_from_storage(proxy_id)

            logger.info(f"Deleted proxy {proxy_id}")
            return True

        return False

    def get_proxies_for_community(self, community: str) -> list[Proxy]:
        """Get all proxies in a community."""
        return [
            proxy
            for proxy in self._cache.values()
            if community in proxy.communities
        ]

    def on_create(self, callback: Callable) -> None:
        """Register callback for proxy creation."""
        self._on_create.append(callback)

    def on_activate(self, callback: Callable) -> None:
        """Register callback for proxy activation."""
        self._on_activate.append(callback)

    def _persist_proxy(self, proxy: Proxy) -> None:
        """Persist proxy to storage."""
        if self._storage:
            try:
                self._storage.save_proxy(proxy.to_dict())
            except Exception as e:
                logger.error(f"Failed to persist proxy {proxy.id}: {e}")

    def _load_proxy(self, proxy_id: str) -> Proxy | None:
        """Load proxy from storage."""
        if self._storage:
            try:
                data = self._storage.load_proxy(proxy_id)
                if data:
                    return Proxy.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load proxy {proxy_id}: {e}")
        return None

    def _delete_from_storage(self, proxy_id: str) -> None:
        """Delete proxy from storage."""
        if self._storage:
            try:
                self._storage.delete_proxy(proxy_id)
            except Exception as e:
                logger.error(f"Failed to delete proxy {proxy_id}: {e}")


# Singleton
_manager: ProxyManager | None = None


def get_proxy_manager() -> ProxyManager:
    """Get the singleton proxy manager."""
    global _manager
    if _manager is None:
        _manager = ProxyManager()
    return _manager
