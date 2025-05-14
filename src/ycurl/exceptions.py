"""ycurl‑specific exception hierarchy for clearer error handling."""


class YcurlError(Exception):
    """Base class for all ycurl errors."""


class ConfigNotFound(YcurlError):
    """Raised when expected configuration files are missing."""


class EndpointNotFound(YcurlError):
    """Raised when an endpoint YAML is missing."""


class InvalidCertificatePair(YcurlError):
    """Raised when certificate and key do not match."""
