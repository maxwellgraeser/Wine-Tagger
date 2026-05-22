"""Debug output helpers — write per-product JSON snapshots of each pipeline stage.

All four helpers accept `enabled: bool` and no-op when False so they can be
called unconditionally from ferment.py with zero overhead in normal runs.

Output layout (relative to this package):

    fermentation/output/
      search/{product_id}.json
      scorer/{product_id}.json
      tagger/{product_id}.json
      final/{product_id}.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional

from .types import ParsedTags, Product, ScoredSnippet, Snippet

_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"


def _dump(stage: str, product_id: str, payload: dict) -> None:
    stage_dir = _OUTPUT_ROOT / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    path = stage_dir / f"{product_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=_json_default)


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    return str(obj)


def _as_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if is_dataclass(obj):
        return asdict(obj)
    return obj


def write_search_output(
    product: Product,
    snippets: list[Snippet],
    *,
    enabled: bool,
    query_count: Optional[int] = None,
) -> None:
    """Persist the raw snippet list returned by searcher.gather_snippets."""
    if not enabled:
        return
    payload = {
        "product_id": product.id,
        "query_count": query_count,
        "raw_snippet_count": len(snippets),
        "snippets": [asdict(s) for s in snippets],
    }
    _dump("search", product.id, payload)


def write_scorer_output(
    product: Product,
    scored: list[ScoredSnippet],
    web_context: Optional[str],
    *,
    enabled: bool,
    input_count: Optional[int] = None,
) -> None:
    """Persist the scored+gated snippet list and assembled web_context."""
    if not enabled:
        return
    producer_gate_dropped = sum(
        1 for s in scored if s.dropped_reason == "producer_absent"
    )
    payload = {
        "product_id": product.id,
        "input_count": input_count if input_count is not None else len(scored),
        "producer_gate_dropped": producer_gate_dropped,
        "scored_snippets": [
            {
                "source": s.snippet.source,
                "domain": s.snippet.domain,
                "url": s.snippet.url,
                "body": s.cleaned_body,
                "match_score": s.match_score,
                "dropped_reason": s.dropped_reason,
            }
            for s in scored
        ],
        "web_context_built": web_context is not None,
        "web_context": web_context,
    }
    _dump("scorer", product.id, payload)


def write_tagger_output(
    product: Product,
    transcript: list[dict],
    *,
    enabled: bool,
    success: Optional[bool] = None,
) -> None:
    """Persist the MCP tool-call transcript returned by tagger.infer_tags."""
    if not enabled:
        return
    submit_attempts = sum(
        1
        for m in transcript
        if isinstance(m, dict)
        and m.get("role") == "tool"
        and m.get("name") == "submit_tags"
    )
    payload = {
        "product_id": product.id,
        "submit_attempts": submit_attempts,
        "success": success,
        "transcript": transcript,
    }
    _dump("tagger", product.id, payload)


def write_final_output(
    product: Product,
    normalized: Optional[ParsedTags],
    tag_status: str,
    *,
    enabled: bool,
) -> None:
    """Persist the final normalized block + tag_status written to the DB."""
    if not enabled:
        return
    payload = {
        "product_id": product.id,
        "tag_status": tag_status,
        "normalized": _as_dict(normalized),
    }
    _dump("final", product.id, payload)
