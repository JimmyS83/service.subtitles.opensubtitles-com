# -*- coding: utf-8 -*-

class ProviderError(Exception):
    u"""Exception raised by providers."""
    pass


class ConfigurationError(ProviderError):
    u"""Exception raised by providers when badly configured."""
    pass


class AuthenticationError(ProviderError):
    u"""Exception raised by providers when authentication failed."""
    pass


class ServiceUnavailable(ProviderError):
    u"""Exception raised when status is '503 Service Unavailable'."""
    pass


class DownloadLimitExceeded(ProviderError):
    u"""Exception raised by providers when download limit is exceeded."""
    pass


class TooManyRequests(ProviderError):
    u"""Exception raised by providers when too many requests are made."""
    pass
