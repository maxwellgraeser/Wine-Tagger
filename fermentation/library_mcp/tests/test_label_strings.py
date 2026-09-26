"""Real-world label strings resolve to the right canonical entry.

Fixture: tests/fixtures/label_strings.yaml, curated from the per-country
research (seed/research/<slug>.md). Each research wave adds its country's
pairs there."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

FIXTURE = yaml.safe_load(
    (Path(__file__).resolve().parent / "fixtures" / "label_strings.yaml").read_text(encoding="utf-8"))


def _cases(kind: str) -> list[tuple[str, str, str]]:
    return [(iso, label, canon)
            for iso, sect in FIXTURE.items()
            for label, canon in (sect.get(kind) or {}).items()]


@pytest.mark.parametrize("iso,label,canonical", _cases("regions"))
def test_region_label(server, iso, label, canonical):
    r = server.lookup_region(label, iso)
    assert r["known"] and not r["is_placeholder"], r
    assert (r["canonical"], r["country"]) == (canonical, server.lookup_country(iso)["canonical"])


@pytest.mark.parametrize("iso,label,canonical", _cases("grapes"))
def test_grape_label(server, iso, label, canonical):
    g = server.lookup_grape(label)
    assert g["known"] and not g["is_placeholder"], g
    assert g["canonical"] == canonical


@pytest.mark.parametrize("label", [l for sect in FIXTURE.values() for l in sect.get("not_grapes") or []])
def test_not_a_grape(server, label):
    assert not server.lookup_grape(label)["known"]
