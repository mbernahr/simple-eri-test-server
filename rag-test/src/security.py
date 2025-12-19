from typing import Optional

from auth import is_static_token
from config import SECURITY_REQUIREMENTS, ProviderType
from fastapi import HTTPException, Request, status


class SecurityManager:
    """Manages security aspects of the API"""

    @staticmethod
    def validate_provider_type(provider_type: Optional[str]) -> bool:
        """
        Validate if a provider type is allowed.

        Args:
            provider_type: The provider type to validate

        Returns:
            True if provider type is allowed, False otherwise
        """
        allowed_type = SECURITY_REQUIREMENTS["allowedProviderType"]

        # If ANY is allowed, all provider types are valid
        if allowed_type == ProviderType.ANY:
            return True

        # If NONE is allowed, no provider type is valid
        if allowed_type == ProviderType.NONE:
            return False

        # For SELF_HOSTED, only validate if provider_type is provided
        if allowed_type == ProviderType.SELF_HOSTED:
            if provider_type is None:
                return False
            return provider_type.upper() == ProviderType.SELF_HOSTED.value

        return False

    @staticmethod
    async def validate_request_security(request: Request) -> None:
        """
        Validate security aspects of a request.

        Args:
            request: The FastAPI request object

        Raises:
            HTTPException: If security validation fails
        """
        # Validate token
        token = request.headers.get("token")
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Prevent static tokens from being used as API tokens
        if is_static_token(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Additional security checks can be added here
        await SecurityManager._validate_rate_limit(request)
        await SecurityManager._validate_request_size(request)

    @staticmethod
    async def _validate_rate_limit(request: Request) -> None:
        """
        Validate request rate limiting.
        Currently a placeholder for future implementation.

        Args:
            request: The FastAPI request object

        Raises:
            HTTPException: If rate limit is exceeded
        """
        # TODO: Implement rate limiting
        pass

    @staticmethod
    async def _validate_request_size(request: Request) -> None:
        """
        Validate request size limits.

        Args:
            request: The FastAPI request object

        Raises:
            HTTPException: If request size exceeds limits
        """
        if request.headers.get("content-length"):
            content_length = int(request.headers.get("content-length", 0))
            if content_length > 10_000_000:  # 10MB limit
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request too large",
                )

    @staticmethod
    def sanitize_input(input_text: str) -> str:
        """
        Sanitize input text to prevent injection attacks.

        Args:
            input_text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Remove potentially dangerous characters
        # This is a basic implementation - extend based on specific needs
        dangerous_chars = ["<", ">", "{", "}", "(", ")", ";", "&", "|", "'", '"']
        sanitized = input_text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        return sanitized

    @staticmethod
    def validate_path(path: str) -> bool:
        """
        Validate a path string for potential directory traversal attacks.

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        # Check for common directory traversal patterns
        dangerous_patterns = ["../", "..\\", "%2e%2e%2f", "..", "~"]
        return not any(pattern in path for pattern in dangerous_patterns)

    @staticmethod
    def get_security_headers() -> dict:
        """
        Get security headers to be included in responses.

        Returns:
            Dictionary of security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "img-src 'self' data:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://unpkg.com; "
                "font-src 'self' data:;"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


# Global instance of the security manager
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """
    Get or create the global security manager instance.

    Returns:
        SecurityManager instance
    """
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
