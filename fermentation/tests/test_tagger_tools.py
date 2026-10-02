"""The tagger's tool surface: what the model is told and shown, per setting.
Starts the library MCP server, so it skips when library.db is not built."""

from __future__ import annotations

import pytest

from fermentation import evidence, settings, tagger
from fermentation.constants import SYSTEM_PROMPT_MCP

needs_library = pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")


def test_system_prompt_drops_colour_only_when_hidden():
    assert tagger.system_prompt(True) == SYSTEM_PROMPT_MCP
    hidden = tagger.system_prompt(False)
    assert "color" not in hidden
    assert "lookup_grape(name)              -> {canonical, origin, synonyms[]" in hidden
    assert "lookup_sub_regions(region)" in hidden


@needs_library
@pytest.mark.parametrize("grape_color", [True, False])
def test_session_tools_follow_the_colour_setting(grape_color):
    with tagger.library_mcp_session(grape_color=grape_color) as s:
        tools = {t["function"]["name"]: t["function"] for t in s.tools}
        assert ("color" in tools["lookup_grape"]["description"]) is grape_color
        assert ("color" in s.call_tool("lookup_grape", {"name": "Hondarrabi Beltza"})) is grape_color
        assert list(tools["lookup_sub_regions"]["parameters"]["properties"]) == ["region"]
        assert "Barolo" in s.call_tool("lookup_sub_regions", {"region": "Langhe"})["sub_regions"]


def test_lookup_grape_color_setting(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    assert settings.lookup_grape_color() is True
    settings.save_settings({"lookup_grape_color": False})
    assert settings.lookup_grape_color() is False
    (tmp_path / "settings.json").write_text('{"lookup_grape_color": "off"}')
    assert settings.lookup_grape_color() is False
    (tmp_path / "settings.json").write_text('{"lookup_grape_color": "maybe"}')
    assert settings.lookup_grape_color() is True
