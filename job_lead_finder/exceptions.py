"""Exception classes for the Job Posting Lead Finder SDK."""


class JobLeadFinderError(Exception):
    """Base exception for all SDK errors."""


class AuthenticationError(JobLeadFinderError):
    """Raised when the Apify API token is missing or invalid."""


class ActorRunError(JobLeadFinderError):
    """Raised when the actor run fails on Apify infrastructure."""


class ActorTimeoutError(JobLeadFinderError):
    """Raised when the actor run does not finish within the allowed timeout."""
