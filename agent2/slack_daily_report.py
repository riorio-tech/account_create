"""Slack export JSON から自分用の日報を自動生成する CLI."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


STOP_WORDS = {
    "です",
    "ます",
    "した",
    "する",
    "して",
    "いる",
    "ある",
    "ない",
    "これ",
    "それ",
    "ため",
    "よう",
    "こと",
    "ところ",
    "できる",
    "お願いします",
    "ありがとう",
    "thanks",
    "today",
    "from",
    "with",
    "that",
    "this",
    "will",
}

TRAIT_RULES = [
    ("仮説検証志向", ("仮説", "検証", "実験", "計測", "試す")),
    ("改善志向", ("改善", "課題", "問題", "修正", "最適化")),
    ("実行推進志向", ("実装", "対応", "進める", "完了", "リリース", "着手")),
    ("連携調整志向", ("共有", "相談", "確認", "お願い", "連携")),
    ("顧客価値志向", ("ユーザー", "顧客", "価値", "体験", "品質")),
]

ACTION_RULES = [
    ("完了/報告", re.compile(r"(完了|対応しました|リリース|マージ|done|fixed)", re.IGNORECASE)),
    ("相談/確認", re.compile(r"(？|\?|確認|相談|見てもら|レビュー)", re.IGNORECASE)),
    ("計画/着手", re.compile(r"(着手|これから|予定|やります|進めます|todo)", re.IGNORECASE)),
    ("情報共有", re.compile(r"(共有|FYI|参考|メモ|リンク)", re.IGNORECASE)),
]

KNOWN_ROOT_METADATA = {
    "users.json",
    "channels.json",
    "groups.json",
    "dms.json",
    "mpims.json",
    "integration_logs.json",
}


@dataclass(frozen=True)
class SlackPost:
    """集計に使う Slack 投稿."""

    channel: str
    timestamp: dt.datetime
    text: str


def _normalize_text(raw: str) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<([^>|]+)\|([^>]+)>", r"\2", text)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = re.sub(r"<@([A-Z0-9]+)>", r"@\1", text)
    text = re.sub(r"<!([^>]+)>", r"@\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _iter_slack_json_files(export_path: Path) -> list[tuple[str, Path]]:
    if export_path.is_file():
        return [("unknown", export_path)]

    pairs: list[tuple[str, Path]] = []
    for p in sorted(export_path.rglob("*.json")):
        if p.parent == export_path and p.name in KNOWN_ROOT_METADATA:
            continue
        channel = p.parent.name if p.parent != export_path else "unknown"
        pairs.append((channel, p))
    return pairs


def _parse_date_or_none(raw: str | None) -> dt.date | None:
    if not raw:
        return None
    return dt.date.fromisoformat(raw)


def load_user_posts(
    export_path: Path,
    user_id: str,
    tz_offset_hours: int = 9,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
) -> list[SlackPost]:
    """Slack エクスポートから対象ユーザーの投稿のみ抽出する."""

    tz = dt.timezone(dt.timedelta(hours=tz_offset_hours))
    posts: list[SlackPost] = []

    for channel, json_path in _iter_slack_json_files(export_path):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, list):
            continue

        for row in payload:
            if not isinstance(row, dict):
                continue
            if row.get("type") != "message":
                continue
            if str(row.get("user", "")) != user_id:
                continue
            if row.get("subtype") in {"bot_message", "channel_join", "channel_leave"}:
                continue

            raw_text = str(row.get("text", ""))
            text = _normalize_text(raw_text)
            if not text:
                continue

            raw_ts = str(row.get("ts", "")).strip()
            try:
                ts = dt.datetime.fromtimestamp(float(raw_ts), tz=tz)
            except ValueError:
                stem = json_path.stem
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", stem):
                    continue
                day = dt.date.fromisoformat(stem)
                ts = dt.datetime.combine(day, dt.time(12, 0), tzinfo=tz)

            day = ts.date()
            if start_date and day < start_date:
                continue
            if end_date and day > end_date:
                continue

            posts.append(SlackPost(channel=channel, timestamp=ts, text=text))

    return sorted(posts, key=lambda x: x.timestamp)


def _extract_keywords(posts: list[SlackPost], top_n: int = 8) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for p in posts:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_+\-]{2,}|[一-龥ぁ-んァ-ン]{2,}", p.text)
        for t in tokens:
            key = t.lower()
            if key in STOP_WORDS:
                continue
            if key.isdigit():
                continue
            counter[key] += 1
    return counter.most_common(top_n)


def _summarize_actions(posts: list[SlackPost]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for p in posts:
        label = "作業メモ"
        for name, rule in ACTION_RULES:
            if rule.search(p.text):
                label = name
                break
        counter[label] += 1
    return counter.most_common()


def _infer_traits(posts: list[SlackPost]) -> list[tuple[str, int, list[str]]]:
    text_blob = "\n".join(p.text for p in posts)
    results: list[tuple[str, int, list[str]]] = []
    for trait, keys in TRAIT_RULES:
        matched = [k for k in keys if k in text_blob]
        score = len(matched)
        if score > 0:
            results.append((trait, score, matched))
    return sorted(results, key=lambda x: x[1], reverse=True)


def _pick_representative_posts(posts: list[SlackPost], limit: int = 8) -> list[SlackPost]:
    scored = sorted(posts, key=lambda p: (len(p.text), p.timestamp), reverse=True)
    return sorted(scored[:limit], key=lambda p: p.timestamp)


def _render_daily_report(day: dt.date, posts: list[SlackPost]) -> str:
    if not posts:
        return f"# {day.isoformat()} 日報\n\n投稿がありませんでした。\n"

    total_chars = sum(len(p.text) for p in posts)
    channels = Counter(p.channel for p in posts)
    active_hours = Counter(p.timestamp.hour for p in posts).most_common(3)
    keywords = _extract_keywords(posts)
    actions = _summarize_actions(posts)
    traits = _infer_traits(posts)
    representative = _pick_representative_posts(posts)

    lines = [f"# {day.isoformat()} 日報", ""]
    lines += [
        "## 1日のサマリー",
        f"- 投稿数: **{len(posts)}件**",
        f"- 文字数: **{total_chars}文字**",
        f"- 参加チャンネル数: **{len(channels)}** ({', '.join(f'{k}:{v}' for k, v in channels.most_common(4))})",
    ]
    if active_hours:
        lines.append(
            "- 活発だった時間帯: "
            + ", ".join(f"{hour:02d}時台({count}件)" for hour, count in active_hours)
        )

    lines += ["", "## 何をしていたか（推定）"]
    for name, count in actions:
        lines.append(f"- {name}: {count}件")

    lines += ["", "## 思考傾向（投稿文からの推定）"]
    if traits:
        for trait, score, matched in traits:
            lines.append(f"- {trait} (シグナル{score}): {', '.join(matched)}")
    else:
        lines.append("- 目立つ傾向は抽出できませんでした。")

    lines += ["", "## 主要キーワード"]
    if keywords:
        lines.append("- " + ", ".join(f"`{k}`({c})" for k, c in keywords))
    else:
        lines.append("- キーワードを抽出できませんでした。")

    lines += ["", "## 主要アクション（投稿抜粋）"]
    for p in representative:
        short = p.text if len(p.text) <= 110 else p.text[:107] + "..."
        lines.append(f"- {p.timestamp:%H:%M} [{p.channel}] {short}")

    lines.append("")
    return "\n".join(lines)


def generate_reports(
    export_path: Path,
    user_id: str,
    output_dir: Path,
    tz_offset_hours: int = 9,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
) -> list[Path]:
    posts = load_user_posts(
        export_path=export_path,
        user_id=user_id,
        tz_offset_hours=tz_offset_hours,
        start_date=start_date,
        end_date=end_date,
    )
    grouped: dict[dt.date, list[SlackPost]] = defaultdict(list)
    for p in posts:
        grouped[p.timestamp.date()].append(p)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_paths: list[Path] = []
    for day in sorted(grouped.keys()):
        report = _render_daily_report(day, grouped[day])
        path = output_dir / f"{day.isoformat()}.md"
        path.write_text(report, encoding="utf-8")
        report_paths.append(path)

    summary_lines = [
        "# Slack 日報サマリー",
        "",
        f"- user_id: `{user_id}`",
        f"- generated_at: `{dt.datetime.now().isoformat(timespec='seconds')}`",
        f"- total_days: **{len(grouped)}**",
        f"- total_posts: **{len(posts)}**",
        "",
        "## 日別レポート",
    ]
    for day in sorted(grouped.keys()):
        summary_lines.append(f"- [{day.isoformat()}]({day.isoformat()}.md): {len(grouped[day])}件")
    summary_lines.append("")
    (output_dir / "README.md").write_text("\n".join(summary_lines), encoding="utf-8")
    return report_paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Slack export から日報を自動生成")
    parser.add_argument("--export-path", required=True, help="Slack エクスポートのディレクトリ or JSON ファイル")
    parser.add_argument("--user-id", required=True, help="自分の Slack user ID (例: U01234567)")
    parser.add_argument("--output-dir", default="output/slack_daily_reports", help="日報の出力先")
    parser.add_argument("--tz-offset-hours", type=int, default=9, help="タイムゾーンオフセット（JSTなら9）")
    parser.add_argument("--start-date", default=None, help="開始日 (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="終了日 (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    export_path = Path(args.export_path).expanduser().resolve()
    if not export_path.exists():
        raise SystemExit(f"export path not found: {export_path}")

    start_date = _parse_date_or_none(args.start_date)
    end_date = _parse_date_or_none(args.end_date)
    if start_date and end_date and start_date > end_date:
        raise SystemExit("start-date must be <= end-date")

    out = Path(args.output_dir).expanduser().resolve()
    paths = generate_reports(
        export_path=export_path,
        user_id=args.user_id.strip(),
        output_dir=out,
        tz_offset_hours=args.tz_offset_hours,
        start_date=start_date,
        end_date=end_date,
    )
    print(f"Generated {len(paths)} daily report(s) in {out}")


if __name__ == "__main__":
    main()
