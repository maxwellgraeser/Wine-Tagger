"""`output/wines.json` — the fermentation output store.

One JSON document holding every wine with its catalog fields, sales stats,
canonical tags, and per-phase status. Replaces the old SQLite `wines.db`.
The cellar web app reads it directly and writes tag edits back through
`update_wine_tags`, which marks the row `manual` so reruns never overwrite it.

Shape:
{
  "version": 2,
  "generated_at": "...",
  "last_run_id": "20260915-131500",
  "source_csv": ".../combined.csv",
  "wines": [ { ...see `wine_from_product`... } ]
}
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .paths import WINES_JSON
from .types import ParsedTags, Product

STORE_VERSION = 2


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def empty_store() -> dict:
    return {
        "version": STORE_VERSION,
        "generated_at": _now(),
        "last_run_id": None,
        "source_csv": None,
        "wines": [],
    }


def load_store(path: Path = WINES_JSON) -> dict:
    if not path.exists():
        return empty_store()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty_store()
    if not isinstance(data, dict) or "wines" not in data:
        return empty_store()
    return data


def save_store(store: dict, path: Path = WINES_JSON) -> None:
    """Atomic write so a reader (the web app) never sees a half file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    store["generated_at"] = _now()
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".wines-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def wine_from_product(product: Product) -> dict:
    """A fresh, untagged row for `product`."""
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "category": product.category,
        "supply_price": product.supply_price,
        "retail_price": product.retail_price,
        "supplier": product.supplier,
        "brand": product.brand,
        "country": None,
        "region": [],
        "grapes": [],
        "is_blend": None,
        "organic": False,
        "confidence": None,
        "web_context": None,
        "tags_raw": None,
        "tag_status": "pending",   # pending | auto | needs_review | manual
        "sales": {
            "items_sold": product.items_sold,
            "margin_pct": product.margin_pct,
            "sale_count": product.sale_count,
            "customer_count": product.customer_count,
            "avg_sale_value": product.avg_sale_value,
        },
        "run_id": None,
        "phase_status": {"search": None, "score": None, "tag": None},
        "created_at": _now(),
        "updated_at": _now(),
    }


def find_wine(store: dict, product_id: str) -> Optional[dict]:
    for w in store["wines"]:
        if w.get("id") == product_id:
            return w
    return None


def ensure_wine(store: dict, product: Product) -> dict:
    """Return the store row for `product`, creating it if missing. Catalog
    and sales fields are refreshed from the CSV every time; tags are not."""
    row = find_wine(store, product.id)
    fresh = wine_from_product(product)
    if row is None:
        store["wines"].append(fresh)
        return fresh
    for key in ("name", "sku", "category", "supply_price", "retail_price", "supplier", "brand", "sales"):
        row[key] = fresh[key]
    row.setdefault("phase_status", {"search": None, "score": None, "tag": None})
    return row


def build_tags_raw(normalized: Optional[ParsedTags], organic: bool) -> Optional[str]:
    """Semicolon-delimited human-readable tag string."""
    if normalized is None:
        return None
    parts: list[str] = []
    if normalized.country:
        parts.append(normalized.country)
    parts.extend(r for r in (normalized.region or []) if r)
    parts.extend(normalized.grapes or [])
    if normalized.is_blend is True:
        parts.append("Blend")
    elif normalized.is_blend is False:
        parts.append("Single Varietal")
    if organic:
        parts.append("Organic")
    return "; ".join(parts) if parts else None


def apply_tags(
    row: dict,
    normalized: Optional[ParsedTags],
    web_context: Optional[str],
    tag_status: str,
    organic: bool,
    run_id: str,
) -> None:
    """Write the tagger result onto a store row."""
    if normalized is not None:
        row["country"] = normalized.country
        row["region"] = list(normalized.region or [])
        row["grapes"] = list(normalized.grapes or [])
        row["is_blend"] = normalized.is_blend
        row["confidence"] = normalized.confidence
    else:
        row["country"] = None
        row["region"] = []
        row["grapes"] = []
        row["is_blend"] = None
        row["confidence"] = None
    row["organic"] = bool(organic)
    row["web_context"] = web_context
    row["tags_raw"] = build_tags_raw(normalized, organic)
    row["tag_status"] = tag_status
    row["run_id"] = run_id
    row["updated_at"] = _now()


def update_wine_tags(store: dict, product_id: str, **fields) -> Optional[dict]:
    """Manual edit from the web app. Accepts country, region, grapes,
    is_blend, organic, confidence, tag_status. Marks the row `manual`
    unless a tag_status is supplied explicitly."""
    row = find_wine(store, product_id)
    if row is None:
        return None
    for key in ("country", "is_blend", "confidence"):
        if key in fields:
            row[key] = fields[key]
    for key in ("region", "grapes"):
        if key in fields:
            row[key] = list(fields[key] or [])
    if "organic" in fields:
        row["organic"] = bool(fields["organic"])
    row["tag_status"] = fields.get("tag_status") or "manual"
    tags = ParsedTags(
        country=row.get("country"),
        region=list(row.get("region") or []),
        grapes=list(row.get("grapes") or []),
        is_blend=row.get("is_blend"),
        organic=row.get("organic"),
        confidence=row.get("confidence"),
    )
    row["tags_raw"] = build_tags_raw(tags, bool(row.get("organic")))
    row["updated_at"] = _now()
    return row


def reset_manual(store: dict) -> int:
    """Flip every `manual` row back to `pending` so the next fermentation
    run re-searches/scores/tags it instead of skipping it. Returns the
    count of rows changed."""
    n = 0
    for row in store["wines"]:
        if row.get("tag_status") == "manual":
            row["tag_status"] = "pending"
            row["updated_at"] = _now()
            n += 1
    return n


def export_rows(store: dict) -> list[dict]:
    """Lightspeed export rows: id, name, tags (country; regions; grapes)."""
    out = []
    for w in store["wines"]:
        parts = []
        if w.get("country"):
            parts.append(w["country"])
        parts.extend(r for r in (w.get("region") or []) if r)
        parts.extend(g for g in (w.get("grapes") or []) if g)
        out.append({"id": w["id"], "name": w["name"], "tags": "; ".join(parts)})
    return out


def parsed_tags_to_dict(tags: Optional[ParsedTags]) -> Optional[dict]:
    return asdict(tags) if tags is not None else None
