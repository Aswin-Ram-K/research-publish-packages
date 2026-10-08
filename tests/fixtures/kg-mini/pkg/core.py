"""Core domain logic for kg-mini."""
from pkg.util import DEFAULT_RETRIES, clamp, slugify


class Job:
    """A named unit of work with a retry budget."""

    def __init__(self, name: str, retries: int = DEFAULT_RETRIES) -> None:
        self.name = name
        self.retries = clamp(retries)

    def key(self) -> str:
        """Stable identifier for this job."""
        return slugify(self.name)

    def describe(self) -> str:
        return f"{self.key()}:{self.retries}"


def run_job(name: str, retries: int = DEFAULT_RETRIES) -> str:
    """Build a Job and return its description."""
    return Job(name, retries).describe()
