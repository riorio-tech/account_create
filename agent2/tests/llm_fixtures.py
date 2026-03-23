"""テスト用の Claude 応答 JSON（拡張スキーマ）。"""

from __future__ import annotations

import json


def extended_design_llm_json() -> str:
    return json.dumps(
        {
            "market_facts": {
                "summary": "要約",
                "demand_signals": ["需要1"],
                "competitive_angle": "差別化",
                "assumptions": "前提",
            },
            "tiktok_account_design": {
                "positioning": "立ち位置",
                "value_proposition": "約束",
                "content_pillars": ["柱1", "柱2", "柱3"],
                "visual_mood": "ムード",
            },
            "character_design": {
                "persona_label": "キャラ",
                "personality": ["親しみ"],
                "backstory_one_liner": "背景",
                "do_and_dont": {"do": ["する"], "dont": ["しない"]},
            },
            "profile_proposal": {
                "bio_text": "プロフィール文",
                "icon_image_brief": "アイコン指示",
                "header_image_brief": "ヘッダー指示",
            },
            "voice_for_sales": {
                "voice_summary": "声の説明",
                "pace_energy": "テンポ",
                "emotional_tone": "トーン",
                "why_converts": "売れる理由",
                "sample_hook_lines": ["フック1", "フック2"],
            },
            "content_spec": {
                "voice_tone": "落ち着いた低め",
                "core_color": ["#111111", "#222222", "#333333"],
                "hook_template": "テストフック",
                "script_outline": ["s1", "s2", "s3", "s4", "s5"],
                "bgm_direction": "ローファイ",
                "caption_template": "キャプション",
                "hashtag_strategy": {
                    "primary": ["#a"],
                    "niche": ["#b"],
                    "trending": ["#c"],
                },
            },
            "posting_strategy": {
                "best_time_slots": ["07:00-09:00"],
                "frequency": "1日1本",
                "ab_test_axis": "フック",
            },
            "creator_requirements": {
                "follower_range": "1万〜10万",
                "age_range": "20代〜30代",
                "gender": "女性",
                "vibe_keywords": ["ナチュラル"],
            },
        },
        ensure_ascii=False,
    )
