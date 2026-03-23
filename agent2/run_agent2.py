"""エージェント②: コンテンツ設計書の生成と永続化。

- エージェント①: AGENT1_OUTPUT_PATH の JSON 配列
- 自然言語: -n / AGENT2_NATURAL_LANGUAGE / AGENT2_NATURAL_LANGUAGE_FILE
- 完了後: output/content_brief.json +（設定時）Google スプレッドシート追記
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import env_load

import designer
import sheets_export
from inputs.agent1 import load_agent1_json

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent
_OUTPUT_PATH = _ROOT / "output" / "content_brief.json"


def _natural_language_input() -> str:
    fp = os.environ.get("AGENT2_NATURAL_LANGUAGE_FILE", "").strip()
    if fp:
        p = Path(fp)
        if not p.is_file():
            logger.error("AGENT2_NATURAL_LANGUAGE_FILE が見つかりません: %s", fp)
            sys.exit(1)
        return p.read_text(encoding="utf-8").strip()
    return os.environ.get("AGENT2_NATURAL_LANGUAGE", "").strip()


def _load_products_from_agent1() -> list[dict]:
    raw = os.environ.get("AGENT1_OUTPUT_PATH", "").strip()
    if not raw:
        logger.error("AGENT1_OUTPUT_PATH が未設定です（自然言語なら -n を使うか AGENT2_NATURAL_LANGUAGE を設定）")
        sys.exit(1)
    path = Path(raw)
    if not path.is_absolute():
        path = (_ROOT / path).resolve()
    try:
        return load_agent1_json(path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        logger.error("エージェント①の入力を読めません: %s", e)
        sys.exit(1)


def _write_json_atomic(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def main(argv: list[str] | None = None) -> None:
    # 親が空の ANTHROPIC_API_KEY を渡しても agent2/.env で埋める
    env_load.load_agent2_env()
    parser = argparse.ArgumentParser(description="エージェント② — コンテンツ設計書生成")
    parser.add_argument(
        "-n",
        "--natural-language",
        dest="natural_language",
        default=None,
        help="エージェント①を使わず、説明文1件から設計（例: -n \"疲れに効くガジェット\"）",
    )
    args = parser.parse_args(argv)

    nl = (args.natural_language or _natural_language_input()).strip()

    if nl:
        logger.info("入力: 自然言語（1件）")
        brief = designer.design_from_natural_language(nl)
        briefs = [brief] if brief else []
    else:
        logger.info("入力: エージェント①（%s）", os.environ.get("AGENT1_OUTPUT_PATH", ""))
        products = _load_products_from_agent1()
        briefs = designer.design_all(products)

    _write_json_atomic(_OUTPUT_PATH, briefs)
    sheets_export.append_briefs_to_sheet(briefs)

    logger.info("完了: %s 件を %s に出力しました", len(briefs), _OUTPUT_PATH)


if __name__ == "__main__":
    main()
