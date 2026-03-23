# Supabase を MCP で使う（エージェント②）

`run_agent2.py` とデモ UI は **`output/content_brief.json` のみ**を書き出します。  
`content_briefs` テーブルへの保存は **Cursor 上の Supabase MCP**（または SQL エディタの手動実行）で行います。

## 1. Cursor に Supabase MCP を追加

公式ガイドに従って接続します。

- [Supabase MCP のドキュメント](https://supabase.com/docs/guides/getting-started/mcp)

接続後、**Cursor** では **Settings → Cursor Settings → Tools & MCP** で Supabase が有効か確認できます（ブラウザログインで認証されることが多いです）。

手動設定の例はリポジトリの **`.cursor/mcp.json.example`** を参照（`YOUR_PROJECT_REF` を差し替え）。  
**トークンやキーはリポジトリや `.env` にコミットしないでください。**

## 2. テーブルを用意

まだの場合は Supabase の SQL エディタ（または MCP の SQL 実行）で `db/schema.sql` を実行し、`content_briefs` を作成します。

## 3. エージェント②の実行後に反映する

1. `python run_agent2.py`（またはデモの「設計書をつくる」）で `output/content_brief.json` ができる  
2. その JSON の各要素を、Cursor で **Supabase MCP** を使って `content_briefs` に `INSERT` する  

### チャットでの依頼例

> `agent2/output/content_brief.json` の各行を読み、`content_briefs` に INSERT する SQL を Supabase MCP で実行してください。  
> カラムは `product_id`, `product_name`, `account_type`, `creator_type`, `cvr_expectation`, `content_spec`, `posting_strategy`, `creator_requirements`（JSONB は適切にエスケープ）です。

MCP が `execute_sql` 等を提供していれば、エージェントが JSON を読み込んで SQL を組み立てて実行できます。

### 1件分のカラム対応（参考）

| JSON（brief） | DB カラム |
|---------------|-----------|
| `product_id` | `product_id` |
| `product_name` | `product_name` |
| `account_design.account_type` | `account_type` |
| `account_design.creator_type` | `creator_type` |
| `account_design.cvr_expectation` | `cvr_expectation` |
| `content_spec` | `content_spec` (JSONB) |
| `posting_strategy` | `posting_strategy` (JSONB) |
| `creator_requirements` | `creator_requirements` (JSONB) |

`reason` は JSON 内の `account_design` に含まれます。DB に `reason` カラムが無い現行スキーマでは保存しなくて構いません。

## 4. GitHub Actions について

CI から Supabase に直接 INSERT する処理はありません。  
成果物の JSON を Artifact として受け取り、ローカルまたは MCP で反映する運用にしてください。
