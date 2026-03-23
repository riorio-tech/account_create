"""designer モジュールのテスト（Claude API はモック）。"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import designer

from tests.llm_fixtures import extended_design_llm_json


def _sample_product() -> dict:
    return {
        "product_id": "prod_001",
        "product_name": "マッサージガン Pro",
        "category": "ガジェット",
        "price": 8980,
        "total_score": 82.5,
        "trend_label": "急騰",
        "why_selling": "在宅ワーク疲れによる需要が急増している",
        "appeal_axis": ["疲労回復", "手軽さ", "プロ仕様"],
        "target_persona": "30代男性、デスクワーカー",
        "content_hint": "使用前後の変化を見せる構成が刺さる",
        "risk": "類似品が多く差別化が必要",
    }


def _sample_match() -> dict:
    return {
        "category": "ガジェット",
        "best_creator_type": "専門系",
        "cvr_expectation": "高",
        "reason": "専門知識が購買信頼感を生む",
        "all_scores": {},
    }


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
@patch("designer.anthropic.Anthropic")
def test_design_content_returns_expected_shape(mock_anthropic):
    msg = MagicMock()
    msg.content = [MagicMock(text=extended_design_llm_json())]
    mock_anthropic.return_value.messages.create.return_value = msg

    r = designer.design_content(_sample_product(), _sample_match())

    assert r is not None
    assert r["product_id"] == "prod_001"
    assert r["input_source"] == "agent1"
    assert "market_facts" in r
    assert "tiktok_account_design" in r
    assert "character_design" in r
    assert "profile_proposal" in r
    assert "voice_for_sales" in r
    assert isinstance(r["content_spec"], dict)


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
@patch("designer.anthropic.Anthropic")
def test_design_content_retries_on_json_parse_error(mock_anthropic):
    bad = MagicMock()
    bad.content = [MagicMock(text="not valid json")]
    good = MagicMock()
    good.content = [MagicMock(text=extended_design_llm_json())]
    mock_anthropic.return_value.messages.create.side_effect = [bad, good]

    r = designer.design_content(_sample_product(), _sample_match())

    assert r is not None
    assert mock_anthropic.return_value.messages.create.call_count == 2


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
@patch("designer.anthropic.Anthropic")
def test_design_content_returns_none_after_parse_failures(mock_anthropic):
    bad_msg = MagicMock()
    bad_msg.content = [MagicMock(text="{{{invalid json")]
    mock_anthropic.return_value.messages.create.return_value = bad_msg

    r = designer.design_content(_sample_product(), _sample_match())

    assert r is None
    assert mock_anthropic.return_value.messages.create.call_count == 3
