"""
WebSocket security utilities for rate limiting and session validation
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class WebSocketRateLimiter:
    """Rate limiter for WebSocket connections"""

    def __init__(self, max_connections_per_ip: int = 10, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_connections_per_ip: Maximum connections allowed per IP in time window
            time_window: Time window in seconds for rate limiting
        """
        self.max_connections_per_ip = max_connections_per_ip
        self.time_window = time_window
        self.connections: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, ip_address: str) -> Tuple[bool, str]:
        """
        Check if connection from IP is allowed

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_allowed, reason_if_not_allowed)
        """
        current_time = time.time()

        # Clean up old connection timestamps
        self.connections[ip_address] = [
            timestamp
            for timestamp in self.connections[ip_address]
            if current_time - timestamp < self.time_window
        ]

        # Check if limit exceeded
        if len(self.connections[ip_address]) >= self.max_connections_per_ip:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return False, f"Too many connections. Maximum {self.max_connections_per_ip} connections per {self.time_window} seconds."

        # Record new connection
        self.connections[ip_address].append(current_time)
        return True, ""

    def remove_connection(self, ip_address: str):
        """Remove one connection from the count for an IP"""
        current_time = time.time()
        if ip_address in self.connections and self.connections[ip_address]:
            # Remove the oldest connection timestamp
            self.connections[ip_address] = [
                timestamp
                for timestamp in self.connections[ip_address]
                if current_time - timestamp < self.time_window
            ][1:]  # Remove first element


class SessionValidator:
    """Validates WebSocket session IDs"""

    def __init__(self):
        """Initialize session validator"""
        self.active_sessions: Dict[str, float] = {}
        self.session_timeout = 3600  # 1 hour

    def register_session(self, session_id: str):
        """Register a new conversion session"""
        self.active_sessions[session_id] = time.time()
        logger.debug(f"Registered session: {session_id}")

    def is_valid_session(self, session_id: str) -> Tuple[bool, str]:
        """
        Check if session ID is valid

        Args:
            session_id: Session ID to validate

        Returns:
            Tuple of (is_valid, reason_if_not_valid)
        """
        # Clean up expired sessions
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, timestamp in self.active_sessions.items()
            if current_time - timestamp > self.session_timeout
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]
            logger.debug(f"Expired session removed: {sid}")

        # Check if session exists
        if session_id not in self.active_sessions:
            logger.warning(f"Invalid session ID attempted: {session_id}")
            return False, "Invalid or expired session ID"

        return True, ""

    def remove_session(self, session_id: str):
        """Remove a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.debug(f"Session removed: {session_id}")


# Global instances
rate_limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)
session_validator = SessionValidator()
