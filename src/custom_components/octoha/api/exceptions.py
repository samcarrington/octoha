"""Custom exceptions for the Octoha API client.

Exception hierarchy adapted from open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

import re

# Maximum length for sanitized error messages
_MAX_ERROR_LENGTH = 200

# Pattern to detect potential sensitive data (API keys, tokens, etc.)
_SENSITIVE_PATTERNS = re.compile(
    r"(sk_live_[a-zA-Z0-9]+|"  # API keys
    r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+|"  # JWT tokens
    r"[a-f0-9]{32,})",  # Long hex strings (potential secrets)
    re.IGNORECASE,
)


def sanitize_error_message(
    message: str,
    max_length: int = _MAX_ERROR_LENGTH,
    context: str | None = None,
) -> str:
    """Sanitize an error message for safe user display.

    Removes potentially sensitive information and truncates long messages.
    The full error should be logged separately for debugging.

    Args:
        message: The raw error message.
        max_length: Maximum length of the returned message.
        context: Optional context prefix (e.g., "Authentication failed").

    Returns:
        Sanitized error message safe for user display.

    Example:
        >>> sanitize_error_message("Invalid token: sk_live_abc123")
        "Invalid token: [REDACTED]"
    """
    if not message:
        return context or "An error occurred"

    # Remove potential sensitive data
    sanitized = _SENSITIVE_PATTERNS.sub("[REDACTED]", message)

    # Remove control characters that could be used for log injection
    sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[: max_length - 3] + "..."

    # Add context prefix if provided
    if context:
        return f"{context}: {sanitized}"

    return sanitized


def sanitize_log_message(message: str) -> str:
    """Sanitize a message for logging.

    Escapes control characters to prevent log injection attacks.

    Args:
        message: The raw message to log.

    Returns:
        Sanitized message safe for logging.
    """
    if not message:
        return ""

    # Escape control characters
    pattern = r"[\x00-\x1f\x7f-\x9f]"
    return re.sub(pattern, lambda m: f"\\x{ord(m.group()):02x}", message)


class OctopusError(Exception):
    """Base exception for Octopus API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(OctopusError):
    """Exception raised when authentication fails.

    This can occur when:
    - API key is invalid
    - Token has expired and cannot be refreshed
    - Account doesn't have API access enabled
    """


class RateLimitError(OctopusError):
    """Exception raised when API rate limit is exceeded.

    The Octopus API has rate limits. When exceeded, this exception
    is raised with information about when to retry.
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            retry_after: Seconds to wait before retrying.
            status_code: HTTP status code.
        """
        super().__init__(message, status_code)
        self.retry_after = retry_after


class ConnectionError(OctopusError):
    """Exception raised when unable to connect to the API."""


class InvalidResponseError(OctopusError):
    """Exception raised when the API returns an unexpected response format."""


class ValidationError(OctopusError):
    """Exception raised when input validation fails."""


# ============================================================================
# Input Validation Functions
# ============================================================================

# MPAN: 13 digits (Meter Point Administration Number for electricity)
_MPAN_PATTERN = re.compile(r"^\d{13}$")

# MPRN: 6-10 digits (Meter Point Reference Number for gas)
_MPRN_PATTERN = re.compile(r"^\d{6,10}$")

# Meter serial: alphanumeric, typically 10-14 characters
_METER_SERIAL_PATTERN = re.compile(r"^[A-Za-z0-9]{6,20}$")


def validate_mpan(mpan: str) -> str:
    """Validate an MPAN (Meter Point Administration Number).

    MPANs are 13-digit numbers used to identify electricity meter points.

    Args:
        mpan: The MPAN to validate.

    Returns:
        The validated MPAN (stripped of whitespace).

    Raises:
        ValidationError: If the MPAN format is invalid.

    Example:
        >>> validate_mpan("1234567890123")
        "1234567890123"
        >>> validate_mpan("invalid")
        ValidationError: Invalid MPAN format
    """
    if not mpan:
        raise ValidationError("MPAN is required")

    cleaned = mpan.strip()

    if not _MPAN_PATTERN.match(cleaned):
        raise ValidationError(
            f"Invalid MPAN format: expected 13 digits, got '{cleaned[:20]}'"
        )

    return cleaned


def validate_mprn(mprn: str) -> str:
    """Validate an MPRN (Meter Point Reference Number).

    MPRNs are 6-10 digit numbers used to identify gas meter points.

    Args:
        mprn: The MPRN to validate.

    Returns:
        The validated MPRN (stripped of whitespace).

    Raises:
        ValidationError: If the MPRN format is invalid.

    Example:
        >>> validate_mprn("1234567890")
        "1234567890"
        >>> validate_mprn("invalid")
        ValidationError: Invalid MPRN format
    """
    if not mprn:
        raise ValidationError("MPRN is required")

    cleaned = mprn.strip()

    if not _MPRN_PATTERN.match(cleaned):
        raise ValidationError(
            f"Invalid MPRN format: expected 6-10 digits, got '{cleaned[:20]}'"
        )

    return cleaned


def validate_meter_serial(serial: str) -> str:
    """Validate a meter serial number.

    Meter serials are alphanumeric, typically 10-14 characters.

    Args:
        serial: The meter serial to validate.

    Returns:
        The validated serial (stripped of whitespace).

    Raises:
        ValidationError: If the serial format is invalid.
    """
    if not serial:
        raise ValidationError("Meter serial is required")

    cleaned = serial.strip()

    if not _METER_SERIAL_PATTERN.match(cleaned):
        raise ValidationError(f"Invalid meter serial format: '{cleaned[:20]}'")

    return cleaned
