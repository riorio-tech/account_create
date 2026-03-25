from __future__ import annotations

import json
from pathlib import Path

from slack_daily_report import generate_reports, load_user_posts


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_load_user_posts_filters_by_user_and_date(tmp_path: Path):
    export_dir = tmp_path / "slack_export"
    _write_json(
        export_dir / "general" / "2026-03-24.json",
        [
            {
                "type": "message",
                "user": "U_ME",
                "text": "実装を進めます。今日中に完了予定です。",
                "ts": "1774323600.000001",
            },
            {
                "type": "message",
                "user": "U_OTHER",
                "text": "これは他人の投稿",
                "ts": "1774327200.000001",
            },
        ],
    )
    _write_json(
        export_dir / "dev" / "2026-03-25.json",
        [
            {
                "type": "message",
                "user": "U_ME",
                "text": "改善案を共有します",
                "ts": "1774410000.000001",
            }
        ],
    )

    posts = load_user_posts(
        export_path=export_dir,
        user_id="U_ME",
        tz_offset_hours=9,
        start_date=None,
        end_date=None,
    )
    assert len(posts) == 2
    assert all("他人" not in p.text for p in posts)
    assert {p.channel for p in posts} == {"general", "dev"}

    posts_1day = load_user_posts(
        export_path=export_dir,
        user_id="U_ME",
        tz_offset_hours=9,
        start_date=posts[0].timestamp.date(),
        end_date=posts[0].timestamp.date(),
    )
    assert len(posts_1day) == 1


def test_generate_reports_creates_markdown_files(tmp_path: Path):
    export_dir = tmp_path / "slack_export"
    _write_json(
        export_dir / "project-a" / "2026-03-24.json",
        [
            {
                "type": "message",
                "user": "U_ME",
                "text": "仮説を立てて検証します。課題の原因を確認します。",
                "ts": "1774323600.000001",
            },
            {
                "type": "message",
                "user": "U_ME",
                "text": "修正を完了しました。共有します。",
                "ts": "1774327200.000001",
            },
        ],
    )

    out = tmp_path / "reports"
    paths = generate_reports(
        export_path=export_dir,
        user_id="U_ME",
        output_dir=out,
        tz_offset_hours=9,
    )
    assert len(paths) == 1
    report = paths[0].read_text(encoding="utf-8")
    assert "# 2026-03-24 日報" in report
    assert "思考傾向" in report
    assert "仮説検証志向" in report
    assert "主要キーワード" in report

    summary = (out / "README.md").read_text(encoding="utf-8")
    assert "Slack 日報サマリー" in summary
    assert "total_posts: **2**" in summary
