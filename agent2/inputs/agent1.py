"""エージェント①の出力（output_for_agent2.json 形式）を読み込む。"""

from __future__ import annotations

import json
from pathlib import Path


def load_agent1_json(path: Path) -> list[dict]:
    """
    エージェント①が出力した JSON 配列を読み込む。
    各要素は product_id, product_name, category, price, total_score 等を想定。
    """
    if not path.is_file():
        raise FileNotFoundError(str(path))
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("入力ファイルが空です")
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("入力は JSON 配列である必要があります")
    return data
