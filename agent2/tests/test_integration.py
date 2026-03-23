"""run_agent2.main の統合テスト（Claude はモック）。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import run_agent2

from tests.llm_fixtures import extended_design_llm_json

_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE = _ROOT / "fixtures" / "sample_input.json"
_OUTPUT = _ROOT / "output" / "content_brief.json"


def _assert_brief_extended(brief: dict) -> None:
    assert "product_id" in brief
    assert "product_name" in brief
    assert "total_score" in brief
    assert brief.get("input_source") == "agent1"
    ad = brief["account_design"]
    for k in ("account_type", "creator_type", "cvr_expectation", "reason"):
        assert k in ad
    for k in (
        "market_facts",
        "tiktok_account_design",
        "character_design",
        "profile_proposal",
        "voice_for_sales",
        "content_spec",
        "posting_strategy",
        "creator_requirements",
    ):
        assert k in brief


def _cleanup_output() -> None:
    if _OUTPUT.exists():
        _OUTPUT.unlink()
    tmp = _OUTPUT.with_suffix(_OUTPUT.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()


@patch("run_agent2.sheets_export.append_briefs_to_sheet", lambda *a, **k: None)
@patch("env_load.load_agent2_env", lambda *a, **k: None)
@patch("designer.anthropic.Anthropic")
def test_run_agent2_main_generates_content_brief_json(mock_anthropic):
    _cleanup_output()
    try:
        msg = MagicMock()
        msg.content = [MagicMock(text=extended_design_llm_json())]
        mock_anthropic.return_value.messages.create.return_value = msg

        env = {
            "ANTHROPIC_API_KEY": "test-key",
            "AGENT1_OUTPUT_PATH": str(_FIXTURE),
        }
        with patch.dict(os.environ, env, clear=False):
            run_agent2.main([])

        assert _OUTPUT.is_file(), "output/content_brief.json が生成されていません"
        raw = _OUTPUT.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 3
        for brief in data:
            _assert_brief_extended(brief)
    finally:
        _cleanup_output()
