"""Mini fixture for the U2.1 miner tests."""

INVARIANT = "only verified provenance reaches the store"


def normalise(title: str) -> str:
    """Collapse a title to a comparable key."""
    return " ".join(title.lower().split())


def verify(refs, graph):
    """Return only the refs the graph can vouch for.

    The guard is deliberately strict: an unknown node id is dropped rather
    than trusted.
    """
    known = graph.by_id()
    return [r for r in refs if r in known]


class Miner:
    """Mines candidates and checks every citation."""

    def __init__(self, root, graph):
        self.root = root
        self.graph = graph

    def mine(self, queries):
        """Run each query and keep the verified candidates."""
        return [self.check(q) for q in queries]

    def check(self, query):
        raise NotImplementedError


def span_guard(lines, start, end):
    """True when a span fits inside the file."""
    return 1 <= start <= end <= len(lines)
