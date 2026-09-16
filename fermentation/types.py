"""Shared dataclasses for the fermentation pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    id: str
    name: str
    sku: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    supply_price: Optional[float]
    retail_price: Optional[float]
    supplier: Optional[str]
    items_sold: Optional[int]
    margin_pct: Optional[float]
    sale_count: Optional[int]
    customer_count: Optional[int]
    avg_sale_value: Optional[float]


@dataclass
class Snippet:
    source: str
    domain: str
    body: str
    url: str


@dataclass
class ScoredSnippet:
    snippet: Snippet
    match_score: int
    cleaned_body: str
    dropped_reason: Optional[str] = None  # "producer_absent" | "unscored" | None
    in_context: bool = False              # made the top-N cut into web_context
    facts: list[str] = field(default_factory=list)  # scorer's claim: subset of grape/region/producer


@dataclass
class ParsedTags:
    """Mirror of submit_tags 'normalized' block."""
    country: Optional[str]
    region: list[str] = field(default_factory=list)
    grapes: list[str] = field(default_factory=list)
    is_blend: Optional[bool] = None
    organic: Optional[bool] = None
    confidence: Optional[int] = None
    category: Optional[str] = None  # Red/White/Rose/Sparkling, only filled when the CSV had none
