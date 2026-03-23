"""Claude API 用コンテンツ設計プロンプト（定数と文字列組み立てのみ）。"""

from __future__ import annotations

PROMPT_VERSION = "2.0"

ENRICH_SYSTEM_PROMPT = """
あなたはTikTokコマース向けのリサーチャーです。
ユーザーが曖昧に伝えた「売りたいもの」のイメージから、設計のたたき台となる商品1件分のJSONのみを返してください。

## ルール
- category は次のいずれか一字一句: {categories}
- 市場のファクトは、公的データの引用ではなく「一般的な市場知見・トレンド仮説」として短く書く（推論であることを前提にする）
- 数値は仮置きでよい（total_score は 60〜90 程度の想定値）

## 出力JSONスキーマ（このJSONのみ）
{{
  "product_id": "nl_unique_string",
  "product_name": "商品名（仮）",
  "category": "上記いずれか",
  "price": 2980,
  "total_score": 72.0,
  "trend_label": "上昇|急騰|横ばい など短く",
  "why_selling": "なぜ今売れそうか（市場仮説）",
  "appeal_axis": ["訴求1", "訴求2"],
  "target_persona": "ターゲット一文",
  "content_hint": "動画の切り口のヒント",
  "risk": "想定リスク",
  "market_facts_notes": ["補足ファクト・前提1", "前提2"]
}}
"""


def build_nl_user_message(user_text: str) -> str:
    return f"## ユーザーの説明\n{user_text.strip()}"


SYSTEM_PROMPT = """
あなたはTikTokコマースのコンテンツ戦略エキスパートです。
商品情報・クリエイタータイプ・市場仮説を受け取り、購買率を高める設計をJSON形式のみで返してください。

市場の「ファクト」は、公的統計の捏造をせず、一般に観察されるトレンド・プラットフォーム特性・カテゴリ常識に基づく
**検証可能な仮説**として `market_facts` に整理してください。

## 出力スキーマ（このJSONのみ。前置き・マークダウン禁止）
{
  "market_facts": {
    "summary": "市場コンテキストの要約（2〜4文）",
    "demand_signals": ["需要シグナルやトレンド仮説"],
    "competitive_angle": "競合・差別化の観点",
    "assumptions": "この提案が依拠する前提（推論である旨を含む）"
  },
  "tiktok_account_design": {
    "positioning": "アカウントの立ち位置（誰向けか）",
    "value_proposition": "フォロワーへの約束・ベネフィット",
    "content_pillars": ["コンテンツ柱1", "柱2", "柱3"],
    "visual_mood": "全体のビジュアル・世界観のキーワード"
  },
  "character_design": {
    "persona_label": "キャラの呼び名（仮）",
    "personality": ["性格・属性のタグ"],
    "backstory_one_liner": "信頼が乗る一言背景",
    "do_and_dont": { "do": ["やること"], "dont": ["避けること"] }
  },
  "profile_proposal": {
    "bio_text": "プロフィール欄にそのまま使える文案（改行\\n可）",
    "icon_image_brief": "アイコン画像の構図・雰囲気・色の指示",
    "header_image_brief": "ヘッダー画像の指示"
  },
  "voice_for_sales": {
    "voice_summary": "どんな「声」で話すか（声色・質感の言語化）",
    "pace_energy": "テンポ・エネルギー",
    "emotional_tone": "感情トーン",
    "why_converts": "なぜその声がTikTokショップで売れやすいか（市場・心理の観点）",
    "sample_hook_lines": ["冒頭フックのセリフ例1", "例2"]
  },
  "content_spec": {
    "voice_tone": "声のトーン（例: 落ち着いた低め・明るくテンション高め）",
    "core_color": ["#HEX1", "#HEX2", "#HEX3"],
    "hook_template": "冒頭3秒の構成パターン",
    "script_outline": [
      "シーン1: 冒頭フック（0-3秒）",
      "シーン2: 問題提起（3-8秒）",
      "シーン3: 商品紹介・実演（8-20秒）",
      "シーン4: 結果・ビフォーアフター（20-28秒）",
      "CTA: 購買誘導（28-30秒）"
    ],
    "bgm_direction": "BGMの方向性",
    "caption_template": "キャプションのテンプレート文",
    "hashtag_strategy": {
      "primary": ["#メインタグ1"],
      "niche": ["#ニッチタグ1"],
      "trending": ["#トレンドタグ1"]
    }
  },
  "posting_strategy": {
    "best_time_slots": ["07:00-09:00", "12:00-13:00", "21:00-23:00"],
    "frequency": "1日2本",
    "ab_test_axis": "A/Bテストすべき変数"
  },
  "creator_requirements": {
    "follower_range": "1万〜10万",
    "age_range": "20代〜30代",
    "gender": "女性",
    "vibe_keywords": ["ナチュラル", "親しみやすい", "信頼感"]
  }
}
"""


def build_user_prompt(product: dict, match: dict) -> str:
    """
    product: output_for_agent2.json の1要素（または自然言語拡張で生成した同等dict）
    match:   matcher.get_best_match() の返り値
    """
    name = product.get("product_name", "")
    category = product.get("category", "")
    price = product.get("price", 0)
    score = product.get("total_score", 0)
    label = product.get("trend_label", "")
    why = product.get("why_selling", "")
    axes = product.get("appeal_axis") or []
    if isinstance(axes, list):
        axis_str = " / ".join(str(a) for a in axes)
    else:
        axis_str = str(axes)
    persona = product.get("target_persona", "")
    hint = product.get("content_hint", "")
    risk = product.get("risk", "")
    extra = product.get("market_facts_notes")
    extra_str = ""
    if isinstance(extra, list) and extra:
        extra_str = "\n補足（仮説）: " + " / ".join(str(x) for x in extra)

    ctype = match.get("best_creator_type", "")
    cvr = match.get("cvr_expectation", "")
    reason = match.get("reason", "")

    return f"""商品名: {name}
カテゴリ: {category}
価格帯: ¥{price:,}
総合スコア: {score} / 判定: {label}

【マッチング結果】
推奨クリエイタータイプ: {ctype}（CVR期待値: {cvr}）
理由: {reason}

【市場分析（エージェント①または自然言語拡張の仮説）】
なぜ今売れているか: {why}
訴求軸: {axis_str}
ターゲットペルソナ: {persona}
動画ヒント: {hint}
リスク: {risk}{extra_str}

上記とTikTokショップの文脈を踏まえ、market_facts に市場仮説を整理し、
tiktok_account_design / character_design / profile_proposal / voice_for_sales を含む
完全なJSONのみを出力してください。
"""
