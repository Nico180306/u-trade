from functools import lru_cache
from pathlib import Path

DISPOSABLE_DOMAINS_FILE = Path(__file__).resolve().parent / "data" / "disposable_domains.txt"


@lru_cache(maxsize=1)
def _disposable_domains() -> frozenset[str]:
    lines = DISPOSABLE_DOMAINS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip().lower() for line in lines if line.strip() and not line.startswith("#")
    )


def is_disposable_email(email: str) -> bool:
    """True si el dominio (o cualquier dominio padre) está en la lista mantenida."""
    domain = email.rsplit("@", 1)[-1].strip().lower()
    labels = domain.split(".")
    blocked = _disposable_domains()
    return any(".".join(labels[i:]) in blocked for i in range(len(labels) - 1))
