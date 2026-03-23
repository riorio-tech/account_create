"""config/matrix.json を読み、カテゴリに対する最適クリエイタータイプを判定する。"""

from __future__ import annotations

import json
from pathlib import Path

_MATRIX_PATH = Path(__file__).resolve().parent / "config" / "matrix.json"

_CREATOR_TYPE_ORDER = ("専門系", "エンタメ系", "日常系", "ライフスタイル系")

_CVR_ORDER = {"最高": 4, "高": 3, "中": 2, "低": 1}


def load_matrix() -> dict:
    """config/matrix.json を読み込んで返す。存在しない場合は FileNotFoundError。"""
    if not _MATRIX_PATH.is_file():
        raise FileNotFoundError(str(_MATRIX_PATH))
    with _MATRIX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _cvr_rank(cvr: str) -> int:
    if cvr not in _CVR_ORDER:
        raise ValueError(f"不明なCVR値: {cvr!r}")
    return _CVR_ORDER[cvr]


def _all_scores_for_category(matrix: dict, category: str) -> dict[str, str]:
    row = matrix["matrix"][category]
    return {ct: row[ct]["cvr"] for ct in _CREATOR_TYPE_ORDER}


def _match_dict(matrix: dict, category: str, creator_type: str) -> dict:
    row = matrix["matrix"][category][creator_type]
    return {
        "category": category,
        "best_creator_type": creator_type,
        "cvr_expectation": row["cvr"],
        "reason": row["reason"],
        "all_scores": _all_scores_for_category(matrix, category),
    }


def _sorted_creator_types(matrix: dict, category: str) -> list[str]:
    """CVR降順、同率は _CREATOR_TYPE_ORDER の順。"""
    row = matrix["matrix"][category]

    def key(ct: str) -> tuple[int, int]:
        return (-_cvr_rank(row[ct]["cvr"]), _CREATOR_TYPE_ORDER.index(ct))

    return sorted(_CREATOR_TYPE_ORDER, key=key)


def get_best_match(category: str) -> dict:
    """CVR が最も高いクリエイタータイプを返す。同率は定義順で先のタイプを採用。"""
    matrix = load_matrix()
    if category not in matrix["matrix"]:
        raise ValueError(f"カテゴリ '{category}' はmatrix.jsonに存在しません")
    ordered = _sorted_creator_types(matrix, category)
    best = ordered[0]
    return _match_dict(matrix, category, best)


def get_top_matches(category: str, top_n: int = 2) -> list[dict]:
    """CVR 上位。同率は同順位をすべて含め、カット位置と同じCVRは全件含める。"""
    if top_n < 1:
        raise ValueError("top_n は 1 以上である必要があります")
    matrix = load_matrix()
    if category not in matrix["matrix"]:
        raise ValueError(f"カテゴリ '{category}' はmatrix.jsonに存在しません")

    ordered = _sorted_creator_types(matrix, category)
    if not ordered:
        return []

    # 先頭 top_n スロットを取り、最後に含まれた CVR と同じものはすべて含める
    cutoff_idx = top_n - 1
    last_cvr = matrix["matrix"][category][ordered[cutoff_idx]]["cvr"]
    result_types: list[str] = []
    for ct in ordered:
        if len(result_types) < top_n:
            result_types.append(ct)
        elif matrix["matrix"][category][ct]["cvr"] == last_cvr:
            result_types.append(ct)
        else:
            break

    return [_match_dict(matrix, category, ct) for ct in result_types]
