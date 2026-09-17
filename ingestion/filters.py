"""Row filters for ingestion, configured by ``ingestion/filters.toml``.

A ``Filters`` object decides, for one product row, whether it is a wine to
keep or something to exclude — and why. See the TOML file for the rules.
"""

from __future__ import annotations

import re
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path

FILTERS_PATH = Path(__file__).parent / "filters.toml"

# Values of Decision.stage / Decision.excluded_by, in evaluation order.
STAGES = ("category", "vendor", "name", "keyword")


def fold(s: str | None) -> str:
    """Case- and accent-insensitive, whitespace-collapsed form of `s`."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.casefold().split())


def word_regex(term: str) -> re.Pattern[str]:
    """Whole-word / whole-phrase match: the term must not be glued to a letter
    or digit on either side, so 'port' never matches 'Portugal'."""
    parts = [re.escape(p) for p in fold(term).split()]
    return re.compile(r"(?<![a-z0-9])" + r"\s+".join(parts) + r"(?![a-z0-9])")


@dataclass(frozen=True)
class Decision:
    keep: bool
    # For kept rows: "category" (green-lit by category) or "uncategorized"
    # (no category, passed every filter). For excluded rows: which filter
    # excluded it — one of STAGES.
    stage: str
    # Human-readable reason, e.g. "category 'Beer' is not whitelisted".
    reason: str
    # The matched category / vendor entry / keyword — used for breakdown counts.
    match: str = ""
    # Keyword group name when stage == "keyword".
    group: str = ""


@dataclass
class Filters:
    category_whitelist: list[str]
    vendor_blacklist: list[str]
    name_exclude: list[str]
    keywords: dict[str, list[str]]
    path: Path | None = None

    def __post_init__(self) -> None:
        self._cats = {fold(c): c for c in self.category_whitelist}
        self._vendors = [(fold(v), v) for v in self.vendor_blacklist]
        self._names = {fold(n): n for n in self.name_exclude}
        self._kw = [
            (group, term, word_regex(term))
            for group, terms in self.keywords.items()
            for term in terms
        ]

    @classmethod
    def load(cls, path: Path = FILTERS_PATH) -> "Filters":
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(
            category_whitelist=list(data.get("categories", {}).get("whitelist", [])),
            vendor_blacklist=list(data.get("vendors", {}).get("blacklist", [])),
            name_exclude=list(data.get("names", {}).get("exclude", [])),
            keywords={k: list(v) for k, v in data.get("keywords", {}).items()},
            path=path,
        )

    def as_dict(self) -> dict:
        return {
            "path": str(self.path) if self.path else None,
            "categories": {"whitelist": self.category_whitelist},
            "vendors": {"blacklist": self.vendor_blacklist},
            "names": {"exclude": self.name_exclude},
            "keywords": self.keywords,
        }

    # -- the decision -------------------------------------------------------

    def decide(self, category: str | None, supplier: str | None, name: str | None) -> Decision:
        cat = (category or "").strip()
        if cat:
            canon = self._cats.get(fold(cat))
            if canon is not None:
                return Decision(True, "category", f"category '{cat}' is whitelisted", canon)
            return Decision(False, "category", f"category '{cat}' is not whitelisted", cat)

        sup = (supplier or "").strip()
        fsup = fold(sup)
        for fv, entry in self._vendors:
            # Exact, or the entry is the supplier's leading word(s):
            # "Cavalier" matches "Cavalier Distributing Florida" but
            # "True" does not match "Truett-Hurst".
            if fsup == fv or fsup.startswith(fv + " "):
                return Decision(False, "vendor", f"uncategorized, supplier '{sup}' is blacklisted ({entry})", entry)

        fname = fold(name)
        if fname in self._names:
            entry = self._names[fname]
            return Decision(False, "name", f"uncategorized, name '{entry}' is on the exclude list", entry)

        for group, term, rx in self._kw:
            if rx.search(fname):
                return Decision(False, "keyword", f"uncategorized, name contains '{term}' ({group})", term, group)

        return Decision(True, "uncategorized", "uncategorized, passed every filter")

    def decide_row(self, row: dict) -> Decision:
        return self.decide(row.get("product_category"), row.get("supplier_name"), row.get("name"))
