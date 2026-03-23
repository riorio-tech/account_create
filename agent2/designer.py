"""matcher とプロンプトを用いて Claude でコンテンツ設計書を生成する。"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import anthropic

import env_load
from matcher import get_best_match, load_matrix
from prompts.content_design import (
    ENRICH_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_nl_user_message,
    build_user_prompt,
)

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS_DESIGN = 8192
_MAX_TOKENS_ENRICH = 2048
_MAX_JSON_RETRIES = 2

_JSON_RETRY_SUFFIX = (
    "\n\n前回の出力がJSONとしてパースできませんでした。"
    "JSONのみを返してください。余分な文字は一切不要です。"
)

_LLM_KEYS = (
    "market_facts",
    "tiktok_account_design",
    "character_design",
    "profile_proposal",
    "voice_for_sales",
    "content_spec",
    "posting_strategy",
    "creator_requirements",
)


def _extract_json_text(raw: str) -> str:
    text = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    return text


def _parse_llm_json(text: str) -> dict[str, Any]:
    cleaned = _extract_json_text(text)
    return json.loads(cleaned)


def _account_type_from_category(category: str) -> str:
    return category


def _build_brief(product: dict, match: dict, llm: dict[str, Any]) -> dict[str, Any]:
    category = product.get("category", "")
    return {
        "product_id": str(product.get("product_id", "")),
        "product_name": str(product.get("product_name", "")),
        "total_score": float(product.get("total_score", 0.0)),
        "input_source": str(product.get("_input_source", "agent1")),
        "account_design": {
            "account_type": _account_type_from_category(category),
            "creator_type": match["best_creator_type"],
            "cvr_expectation": match["cvr_expectation"],
            "reason": match["reason"],
        },
        "market_facts": llm["market_facts"],
        "tiktok_account_design": llm["tiktok_account_design"],
        "character_design": llm["character_design"],
        "profile_proposal": llm["profile_proposal"],
        "voice_for_sales": llm["voice_for_sales"],
        "content_spec": llm["content_spec"],
        "posting_strategy": llm["posting_strategy"],
        "creator_requirements": llm["creator_requirements"],
    }


def _validate_design_json(parsed: dict[str, Any]) -> None:
    for key in _LLM_KEYS:
        if key not in parsed:
            raise KeyError(key)


def design_content(product: dict, match: dict) -> dict[str, Any] | None:
    """1商品のコンテンツ設計書を生成。JSONパースに失敗した場合は最大2回リトライし、ダメなら None。"""
    env_load.load_agent2_env()
    api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not api_key:
        logger.error("ANTHROPIC_API_KEY が設定されていません")
        return None

    user_prompt = build_user_prompt(product, match)
    client = anthropic.Anthropic(api_key=api_key)

    attempt_user = user_prompt
    for attempt in range(_MAX_JSON_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS_DESIGN,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": attempt_user}],
            )
        except Exception as e:
            logger.exception("Claude API 呼び出しに失敗しました: %s", e)
            return None

        block = msg.content[0]
        raw = block.text if hasattr(block, "text") else str(block)

        try:
            parsed = _parse_llm_json(raw)
            _validate_design_json(parsed)
            return _build_brief(product, match, parsed)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(
                "コンテンツ設計のJSONパースに失敗しました (試行 %s/%s): %s",
                attempt + 1,
                _MAX_JSON_RETRIES + 1,
                e,
            )
            if attempt >= _MAX_JSON_RETRIES:
                logger.error(
                    "design_content: JSON のパースに繰り返し失敗したためスキップします product_id=%s",
                    product.get("product_id"),
                )
                return None
            attempt_user = user_prompt + _JSON_RETRY_SUFFIX

    return None


def _matrix_category_list() -> str:
    return "、".join(load_matrix()["matrix"].keys())


def enrich_natural_language_to_product(user_text: str) -> dict[str, Any] | None:
    """自然言語からエージェント①相当の product dict を1件生成する。"""
    env_load.load_agent2_env()
    api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not api_key:
        logger.error("ANTHROPIC_API_KEY が設定されていません")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    system = ENRICH_SYSTEM_PROMPT.format(categories=_matrix_category_list())
    base_user = build_nl_user_message(user_text)
    user_msg = base_user

    for attempt in range(_MAX_JSON_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS_ENRICH,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )
        except Exception as e:
            logger.exception("自然言語拡張の API 呼び出しに失敗: %s", e)
            return None

        block = msg.content[0]
        raw = block.text if hasattr(block, "text") else str(block)
        try:
            data = _parse_llm_json(raw)
            if not isinstance(data, dict):
                raise TypeError("not an object")
            for req in (
                "product_id",
                "product_name",
                "category",
                "why_selling",
                "appeal_axis",
                "target_persona",
            ):
                if req not in data:
                    raise KeyError(req)
            if data["category"] not in load_matrix()["matrix"]:
                raise ValueError(f"category が matrix に無い: {data['category']}")
            data.setdefault("price", 0)
            data.setdefault("total_score", 70.0)
            data.setdefault("trend_label", "想定")
            data.setdefault("content_hint", "")
            data.setdefault("risk", "")
            data["_input_source"] = "natural_language"
            if not str(data.get("product_id", "")).strip():
                data["product_id"] = f"nl_{int(time.time())}"
            return data
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("自然言語拡張のパース失敗 (%s/%s): %s", attempt + 1, _MAX_JSON_RETRIES + 1, e)
            if attempt >= _MAX_JSON_RETRIES:
                return None
            user_msg = base_user + _JSON_RETRY_SUFFIX

    return None


def design_from_natural_language(user_text: str) -> dict[str, Any] | None:
    """自然言語のみから1件の設計書を生成。"""
    product = enrich_natural_language_to_product(user_text)
    if not product:
        return None
    try:
        match = get_best_match(product["category"])
    except Exception:
        logger.exception("get_best_match に失敗しました")
        return None
    return design_content(product, match)


def design_all(products: list[dict]) -> list[dict]:
    """全商品を処理し、成功した設計書のみのリストを返す。"""
    out: list[dict] = []
    for product in products:
        p = dict(product)
        p.setdefault("_input_source", "agent1")
        try:
            match = get_best_match(p["category"])
        except Exception:
            logger.exception("get_best_match に失敗しました")
            continue
        brief = design_content(p, match)
        if brief is None:
            logger.warning(
                "design_content が None のためスキップ product_id=%s",
                p.get("product_id"),
            )
            continue
        out.append(brief)
    return out
