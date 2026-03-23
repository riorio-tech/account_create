"""sheets_export の行組み立てテスト（gspread は呼ばない）。"""

from __future__ import annotations

from sheets_export import SHEET_HEADERS, _as_text, _extra_json, brief_to_row


def test_brief_to_row_matches_header_count():
    minimal = {
        "product_id": "p1",
        "product_name": "テスト商品",
        "total_score": 80.0,
        "input_source": "agent1",
        "account_design": {
            "account_type": "ガジェット",
            "creator_type": "専門系",
            "cvr_expectation": "高",
            "reason": "理由",
        },
        "market_facts": {"summary": "要約", "hypotheses": ["a", "b"]},
        "tiktok_account_design": {"positioning": "ポジ", "content_pillars": ["A", "B"]},
        "character_design": {"persona_label": "主婦の味方", "personality": ["優しい"]},
        "profile_proposal": {"bio_text": "bio", "icon_image_brief": "icon"},
        "voice_for_sales": {"voice_summary": "落ち着いた声"},
        "content_spec": {"voice_tone": "明るく", "hook_template": "フック"},
        "posting_strategy": {"frequency": "週3", "best_time_slots": ["20時"]},
        "creator_requirements": {"follower_range": "1万〜", "vibe_keywords": ["自然"]},
    }
    row = brief_to_row(minimal, "2026-01-01T00:00:00Z")
    assert len(row) == len(SHEET_HEADERS)
    assert row[0] == "2026-01-01T00:00:00Z"
    assert "要約" in row[SHEET_HEADERS.index("mf_summary")]
    assert "ポジ" in row[SHEET_HEADERS.index("tt_positioning")]
    assert "brief_json" in SHEET_HEADERS


def test_as_text_list_joins_lines():
    assert _as_text(["x", "y"]) == "x\ny"


def test_extra_json_unknown_keys():
    d = {"summary": "s", "unknown": {"nested": 1}}
    ex = _extra_json(d, frozenset({"summary"}))
    assert "unknown" in ex
