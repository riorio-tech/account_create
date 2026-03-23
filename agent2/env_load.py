"""agent2/.env を読み込む。

親プロセス（uvicorn 等）が ANTHROPIC_API_KEY を空文字で渡していると、
python-dotenv のデフォルト（override=False）では .env の値が無視される。
未設定または空のキーだけ .env で埋める。

subprocess.run(..., env=...) 用に os.environ のコピーへも同じルールでマージする。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

_AGENT2_ROOT = Path(__file__).resolve().parent


def agent2_env_file() -> Path:
    return _AGENT2_ROOT / ".env"


def merge_agent2_dotenv_into(env: MutableMapping[str, str]) -> None:
    path = agent2_env_file()
    if not path.is_file():
        return
    try:
        from dotenv import dotenv_values
    except ImportError:
        return

    values = dotenv_values(path, encoding="utf-8-sig")

    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if not value:
            continue
        cur = env.get(key)
        if cur is None or (isinstance(cur, str) and not cur.strip()):
            env[key] = value


def load_agent2_env() -> None:
    merge_agent2_dotenv_into(os.environ)
