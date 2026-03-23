# エージェント② 出力スキーマ（content_brief.json）

`run_agent2.py` が生成する `output/content_brief.json` は **JSON 配列** です。各要素は次の構造に従います。

## 各要素（1商品あたり）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `input_source` | string | `"agent1"`（①の JSON）または `"natural_language"`（自然言語のみ） |
| `product_id` | string | 商品ID |
| `product_name` | string | 商品名 |
| `total_score` | number | 総合スコア |
| `account_design` | object | アカウント・クリエイター方針（マトリクス由来） |
| `market_facts` | object | 市場・プラットフォーム上の「ファクト」に相当する仮説・根拠の整理 |
| `tiktok_account_design` | object | TikTok アカウント設計（ポジション、価値提案など） |
| `character_design` | object | キャラクター設計 |
| `profile_proposal` | object | プロフィール文案・画像（アイコン／ヘッダー）の提案 |
| `voice_for_sales` | object | 売れやすい「声」（トーン・語り口の方針） |
| `content_spec` | object | LLM が生成したコンテンツ仕様 |
| `posting_strategy` | object | 投稿戦略 |
| `creator_requirements` | object | クリエイター要件 |

### `account_design`

- `account_type` (string)
- `creator_type` (string)
- `cvr_expectation` (string)
- `reason` (string)

### `market_facts`

- `summary` (string) — 市場・カテゴリ・TikTok 文脈での前提の要約
- `hypotheses` (array of string) — 検証可能な仮説
- `evidence_notes` (array of string) — 根拠の書き方（一般論・カテゴリ知識として明示。捏造データは書かない）

### `tiktok_account_design`

- `positioning` (string)
- `value_proposition` (string)
- `content_pillars` (array of string)
- （その他）`target_audience`, `differentiation` など

### `character_design`

- `persona_label` (string)
- `personality` (array of string)
- `visual_direction` (string)
- （その他）`backstory_hint`, `do_dont` など

### `profile_proposal`

- `bio_text` (string)
- `icon_image_brief` (string)
- `header_image_brief` (string)

### `voice_for_sales`

- `voice_summary` (string)
- `why_converts` (string)
- `sample_phrases` (array of string)
- （その他）`avoid` など

### `content_spec`

- `voice_tone` (string)
- `core_color` (array of string)
- `hook_template` (string)
- `script_outline` (array of string)
- （その他）`bgm_direction`, `caption_template`, `hashtag_strategy` など

### `posting_strategy`

- `best_time_slots` (array of string)
- `frequency` (string)
- （その他）`ab_test_axis` など

### `creator_requirements`

- `follower_range` (string)
- `vibe_keywords` (array of string)
- （その他）`age_range`, `gender` など
