"""デモ用 API: .env のキーはサーバー内のみ。フロントにはフラグと結果 JSON のみ返す。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import env_load
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

AGENT2_ROOT = Path(__file__).resolve().parent.parent
DEMO_ROOT = Path(__file__).resolve().parent
STATIC_DIR = DEMO_ROOT / "static"
OUTPUT_BRIEF = AGENT2_ROOT / "output" / "content_brief.json"

env_load.load_agent2_env()

app = FastAPI(title="Agent2 Demo API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8765",
        "http://localhost:8765",
        "http://127.0.0.1:8766",
        "http://localhost:8766",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _env_configured(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _agent1_path() -> Path | None:
    raw = os.environ.get("AGENT1_OUTPUT_PATH", "").strip()
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = (AGENT2_ROOT / p).resolve()
    return p


def _input_product_count(p: Path | None) -> int | None:
    if not p or not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return len(data) if isinstance(data, list) else None


@app.get("/api/status")
def api_status():
    """API キーは値を返さず、設定済みかどうかのみ。"""
    p = _agent1_path()
    return {
        "configured": {
            "anthropic": _env_configured("ANTHROPIC_API_KEY"),
            "agent1_path": _env_configured("AGENT1_OUTPUT_PATH"),
        },
        "agent1_file_exists": p.is_file() if p else False,
        "input_product_count": _input_product_count(p),
        "content_brief_exists": OUTPUT_BRIEF.is_file(),
    }


@app.get("/api/input-preview")
def api_input_preview():
    p = _agent1_path()
    if not p or not p.is_file():
        raise HTTPException(status_code=404, detail="AGENT1_OUTPUT_PATH のファイルが見つかりません")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析エラー: {e}") from e
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="入力は JSON 配列である必要があります")
    items = []
    for row in data[:50]:
        if isinstance(row, dict):
            items.append(
                {
                    "product_id": row.get("product_id", ""),
                    "product_name": row.get("product_name", ""),
                    "category": row.get("category", ""),
                    "total_score": row.get("total_score"),
                }
            )
    return {"path": str(p), "count": len(data), "preview": items}


@app.get("/api/briefs")
def api_briefs():
    if not OUTPUT_BRIEF.is_file():
        raise HTTPException(status_code=404, detail="content_brief.json がありません。先に実行してください。")
    try:
        return json.loads(OUTPUT_BRIEF.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON 読み込みエラー: {e}") from e


def _truncate(s: str, max_len: int = 48_000) -> str:
    if len(s) <= max_len:
        return s
    return s[-max_len:]


@app.post("/api/run")
def api_run(payload: dict = Body(default_factory=dict)):
    """run_agent2.py をサブプロセスで実行。

    body: `{ "mode": "agent1" | "natural_language", "natural_language": "..." }`
    """
    mode = str(payload.get("mode") or "agent1").strip().lower()
    nl = str(payload.get("natural_language") or "").strip()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env.pop("AGENT2_NATURAL_LANGUAGE", None)
    env.pop("AGENT2_NATURAL_LANGUAGE_FILE", None)
    # 子プロセスは env のコピーだけを見る。親の os.environ が空キーでも agent2/.env で埋める
    env_load.merge_agent2_dotenv_into(env)

    if mode == "natural_language":
        if not nl:
            raise HTTPException(status_code=400, detail="natural_language が空です")
        tmp = AGENT2_ROOT / "output" / ".nl_last_request.txt"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(nl, encoding="utf-8")
        env["AGENT2_NATURAL_LANGUAGE_FILE"] = str(tmp.resolve())
    else:
        p = _agent1_path()
        if not p or not p.is_file():
            raise HTTPException(status_code=400, detail="AGENT1_OUTPUT_PATH のファイルが存在しません")

    if not (env.get("ANTHROPIC_API_KEY") or "").strip():
        p = env_load.agent2_env_file()
        hint = (
            f"agent2/.env に ANTHROPIC_API_KEY を記載してください（期待する場所: {p}）。"
            " ファイルが無い・キー名の typo・値の前後に余分な空白がないか確認し、uvicorn を再起動してください。"
        )
        raise HTTPException(status_code=400, detail=hint)

    proc = subprocess.run(
        [sys.executable, str(AGENT2_ROOT / "run_agent2.py")],
        cwd=str(AGENT2_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": _truncate(proc.stdout or ""),
        "stderr": _truncate(proc.stderr or ""),
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
