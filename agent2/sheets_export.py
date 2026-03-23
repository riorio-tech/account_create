"""生成した設計書を Google スプレッドシートに追記する（項目ごとに列分割）。"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MAX_CELL = 45000
_ALT_SUFFIX = "_v2_structured"


def _cell_text(s: str) -> str:
    if len(s) <= _MAX_CELL:
        return s
    return s[: _MAX_CELL - 20] + "…(truncated)"


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        lines: list[str] = []
        for x in value:
            if isinstance(x, (str, int, float, bool)):
                lines.append(str(x))
            else:
                lines.append(json.dumps(x, ensure_ascii=False))
        return "\n".join(lines)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _get(d: Any, *keys: str, default: str = "") -> str:
    if not isinstance(d, dict):
        return default
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return _as_text(cur)


def _extra_json(obj: Any, known: frozenset[str]) -> str:
    if not isinstance(obj, dict):
        return ""
    extra = {k: v for k, v in obj.items() if k not in known and v not in (None, "", [], {})}
    if not extra:
        return ""
    return _cell_text(json.dumps(extra, ensure_ascii=False))


# 1 行目の列定義（順序固定）。LLM が追加したキーは *_extra_json に退避
SHEET_HEADERS: tuple[str, ...] = (
    "generated_at_utc",
    "input_source",
    "product_id",
    "product_name",
    "total_score",
    # account_design
    "ad_account_type",
    "ad_creator_type",
    "ad_cvr_expectation",
    "ad_reason",
    # market_facts
    "mf_summary",
    "mf_hypotheses",
    "mf_evidence_notes",
    "mf_extra_json",
    # tiktok_account_design
    "tt_positioning",
    "tt_value_proposition",
    "tt_content_pillars",
    "tt_target_audience",
    "tt_differentiation",
    "tt_extra_json",
    # character_design
    "ch_persona_label",
    "ch_personality",
    "ch_visual_direction",
    "ch_backstory_hint",
    "ch_do_dont",
    "ch_extra_json",
    # profile_proposal
    "pr_bio_text",
    "pr_icon_image_brief",
    "pr_header_image_brief",
    "pr_extra_json",
    # voice_for_sales
    "vs_voice_summary",
    "vs_why_converts",
    "vs_sample_phrases",
    "vs_avoid",
    "vs_extra_json",
    # content_spec
    "cs_voice_tone",
    "cs_core_color",
    "cs_hook_template",
    "cs_script_outline",
    "cs_bgm_direction",
    "cs_caption_template",
    "cs_hashtag_strategy",
    "cs_extra_json",
    # posting_strategy
    "ps_best_time_slots",
    "ps_frequency",
    "ps_ab_test_axis",
    "ps_extra_json",
    # creator_requirements
    "cr_follower_range",
    "cr_vibe_keywords",
    "cr_age_range",
    "cr_gender",
    "cr_extra_json",
    # 完全バックアップ（長い場合は切り詰め）
    "brief_json",
)

_KNOWN_MF = frozenset({"summary", "hypotheses", "evidence_notes"})
_KNOWN_TT = frozenset(
    {"positioning", "value_proposition", "content_pillars", "target_audience", "differentiation"}
)
_KNOWN_CH = frozenset({"persona_label", "personality", "visual_direction", "backstory_hint", "do_dont"})
_KNOWN_PR = frozenset({"bio_text", "icon_image_brief", "header_image_brief"})
_KNOWN_VS = frozenset({"voice_summary", "why_converts", "sample_phrases", "avoid"})
_KNOWN_CS = frozenset(
    {
        "voice_tone",
        "core_color",
        "hook_template",
        "script_outline",
        "bgm_direction",
        "caption_template",
        "hashtag_strategy",
    }
)
_KNOWN_PS = frozenset({"best_time_slots", "frequency", "ab_test_axis"})
_KNOWN_CR = frozenset({"follower_range", "vibe_keywords", "age_range", "gender"})


def brief_to_row(brief: dict[str, Any], generated_at_utc: str) -> list[str]:
    """1 件の設計書をスプレッドシート 1 行分の文字列リストにする。"""
    ad = brief.get("account_design") or {}
    mf = brief.get("market_facts") or {}
    tt = brief.get("tiktok_account_design") or {}
    ch = brief.get("character_design") or {}
    pr = brief.get("profile_proposal") or {}
    vs = brief.get("voice_for_sales") or {}
    cs = brief.get("content_spec") or {}
    ps = brief.get("posting_strategy") or {}
    cr = brief.get("creator_requirements") or {}

    row: list[str] = [
        generated_at_utc,
        _as_text(brief.get("input_source")),
        _as_text(brief.get("product_id")),
        _as_text(brief.get("product_name")),
        _as_text(brief.get("total_score")),
        _get(ad, "account_type"),
        _get(ad, "creator_type"),
        _get(ad, "cvr_expectation"),
        _get(ad, "reason"),
        _get(mf, "summary"),
        _as_text(mf.get("hypotheses")),
        _as_text(mf.get("evidence_notes")),
        _extra_json(mf, _KNOWN_MF),
        _get(tt, "positioning"),
        _get(tt, "value_proposition"),
        _as_text(tt.get("content_pillars")),
        _get(tt, "target_audience"),
        _get(tt, "differentiation"),
        _extra_json(tt, _KNOWN_TT),
        _get(ch, "persona_label"),
        _as_text(ch.get("personality")),
        _get(ch, "visual_direction"),
        _get(ch, "backstory_hint"),
        _as_text(ch.get("do_dont")),
        _extra_json(ch, _KNOWN_CH),
        _get(pr, "bio_text"),
        _get(pr, "icon_image_brief"),
        _get(pr, "header_image_brief"),
        _extra_json(pr, _KNOWN_PR),
        _get(vs, "voice_summary"),
        _get(vs, "why_converts"),
        _as_text(vs.get("sample_phrases")),
        _get(vs, "avoid"),
        _extra_json(vs, _KNOWN_VS),
        _get(cs, "voice_tone"),
        _as_text(cs.get("core_color")),
        _get(cs, "hook_template"),
        _as_text(cs.get("script_outline")),
        _get(cs, "bgm_direction"),
        _get(cs, "caption_template"),
        _get(cs, "hashtag_strategy"),
        _extra_json(cs, _KNOWN_CS),
        _as_text(ps.get("best_time_slots")),
        _get(ps, "frequency"),
        _get(ps, "ab_test_axis"),
        _extra_json(ps, _KNOWN_PS),
        _get(cr, "follower_range"),
        _as_text(cr.get("vibe_keywords")),
        _get(cr, "age_range"),
        _get(cr, "gender"),
        _extra_json(cr, _KNOWN_CR),
        _cell_text(json.dumps(brief, ensure_ascii=False)),
    ]

    assert len(row) == len(SHEET_HEADERS)
    return [_cell_text(x) for x in row]


def _header_row_matches(existing_first: list[str]) -> bool:
    if len(existing_first) != len(SHEET_HEADERS):
        return False
    return [str(x) for x in existing_first] == list(SHEET_HEADERS)


def append_briefs_to_sheet(briefs: list[dict]) -> None:
    """
    GOOGLE_SHEETS_CREDENTIALS_PATH（サービスアカウントJSON）と GOOGLE_SHEET_ID が揃っていれば追記。
    スプレッドシートはサービスアカウントのメールアドレスに共有済みであること。
    """
    cred_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "").strip()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()
    ws_name = (os.environ.get("GOOGLE_SHEET_WORKSHEET") or "agent2_briefs").strip()

    if not cred_path or not sheet_id:
        logger.info("Google スプレッドシート未設定のため追記スキップ")
        return

    cred_file = Path(cred_path)
    if not cred_file.is_file():
        logger.error("認証ファイルが見つかりません: %s", cred_path)
        return

    try:
        import gspread
    except ImportError:
        logger.error("gspread / google-auth が未インストールです。pip install gspread google-auth")
        return

    gc = gspread.service_account(filename=str(cred_file))
    sh = gc.open_by_key(sheet_id)

    try:
        ws = sh.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=ws_name, rows=3000, cols=len(SHEET_HEADERS))
        ws.append_row(list(SHEET_HEADERS), value_input_option="USER_ENTERED")
    else:
        rows = ws.get_all_values()
        if not rows:
            ws.append_row(list(SHEET_HEADERS), value_input_option="USER_ENTERED")
        elif not _header_row_matches([str(c) for c in rows[0]]):
            alt_title = (ws_name + _ALT_SUFFIX)[:99]
            logger.warning(
                "ワークシート「%s」の 1 行目が新しい列定義と一致しません。"
                "構造化列用に「%s」へ追記します（旧シートのデータはそのまま残ります）。",
                ws_name,
                alt_title,
            )
            try:
                ws = sh.worksheet(alt_title)
            except gspread.WorksheetNotFound:
                ws = sh.add_worksheet(title=alt_title, rows=3000, cols=len(SHEET_HEADERS))
                ws.append_row(list(SHEET_HEADERS), value_input_option="USER_ENTERED")
            else:
                rows_alt = ws.get_all_values()
                if not rows_alt:
                    ws.append_row(list(SHEET_HEADERS), value_input_option="USER_ENTERED")
                elif not _header_row_matches([str(c) for c in rows_alt[0]]):
                    logger.error(
                        "ワークシート「%s」のヘッダが想定と異なります。"
                        "1 行目を手動で合わせるか、別の GOOGLE_SHEET_WORKSHEET を指定してください。",
                        alt_title,
                    )
                    return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [brief_to_row(b, now) for b in briefs]

    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info("スプレッドシートに %s 行追記しました（%s）", len(rows), ws.title)

