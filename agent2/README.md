# エージェント②（コンテンツ設計）

**エージェント①**の商品リスト（JSON）を読むか、**自然言語だけ**で商品イメージを渡すかを選べます。`config/matrix.json` に基づきクリエイタータイプを決め、Claude で TikTok コマース向けの設計書（市場ファクトの仮説、アカウント設計、キャラ、プロフィール案、売れる「声」、コンテンツ仕様などの JSON）を生成します。結果は **`output/content_brief.json`** に保存され、環境変数を設定していれば **Google スプレッドシートにも毎回追記**されます。**Supabase の `content_briefs` への保存は Python では行わず**、Cursor の **Supabase MCP**（または SQL 手動実行）で反映します（手順は `docs/supabase_mcp.md`）。

## セットアップ（5ステップ）

1. **リポジトリのクローン**  
   モノレポの場合はルートを取得し、この README は `agent2/` を前提にしています。

2. **依存関係のインストール**

   ```bash
   cd agent2
   pip install -r requirements.txt
   ```

3. **環境変数**  
   `.env.example` をコピーして `.env` を作成し、値を埋めます。

   ```bash
   copy .env.example .env
   ```

   必須: `ANTHROPIC_API_KEY`  
   **エージェント①モード**で実行する場合: `AGENT1_OUTPUT_PATH`（①の JSON）  
   **自然言語のみ**の場合: CLI で `-n` / 環境変数 `AGENT2_NATURAL_LANGUAGE`（またはファイル `AGENT2_NATURAL_LANGUAGE_FILE`）。デモ UI では「自然言語だけ」を選ぶ。  
   **スプレッドシート追記（任意）:** `GOOGLE_SHEETS_CREDENTIALS_PATH`, `GOOGLE_SHEET_ID`（詳細は下記）  
   ※ `SUPABASE_*` は不要（DB は MCP 側）

4. **Supabase のスキーマ適用**  
   Supabase ダッシュボードの SQL エディタで `db/schema.sql` を実行し、`content_briefs` と `matrix_history` を作成します。

5. **動作確認**

   ```bash
   python run_agent2.py
   ```

   `output/content_brief.json` が生成されれば成功です。DB へは MCP で投入してください。

   自然言語のみ（1件）の例:

   ```bash
   python run_agent2.py -n "在宅向けの疲労回復ガジェットを売りたい"
   ```

---

## エージェント①との連携

### `AGENT1_OUTPUT_PATH` の設定

- **絶対パス**でも **エージェント②のカレントディレクトリからの相対パス**でも構いません。
- 例（`agent2` で実行する場合）:

  ```env
  AGENT1_OUTPUT_PATH=../agent1/output/output_for_agent2.json
  ```

- ローカル検証だけなら同梱の `fixtures/sample_input.json` を指しても構いません。

  ```env
  AGENT1_OUTPUT_PATH=fixtures/sample_input.json
  ```

### 同一リポジトリ / 別リポジトリ

| 構成 | 考え方 |
|------|--------|
| **同一リポジトリ** | ①の出力先を相対パスで指定しやすい（例: `../agent1/output/...`）。CI でもリポジトリ構造が固定されていれば同様に設定できる。 |
| **別リポジトリ** | ①の成果物をオブジェクトストレージや共有パスに置き、②からは **絶対パス** または **ダウンロード後のローカルパス** を `AGENT1_OUTPUT_PATH` に渡す。GitHub Actions では Artifact 連携や Secrets でパス・URL を管理する。 |

---

## Google スプレッドシートへの追記（任意）

1. Google Cloud でサービスアカウントを作成し、JSON キーをダウンロードする。  
2. 追記したいスプレッドシートを、そのサービスアカウントのメールアドレスに **編集者** で共有する。  
3. `.env` に次を設定する（未設定なら追記はスキップされ、ローカル JSON のみ更新される）。

   | 変数 | 説明 |
   |------|------|
   | `GOOGLE_SHEETS_CREDENTIALS_PATH` | サービスアカウント JSON のパス |
   | `GOOGLE_SHEET_ID` | スプレッドシート URL の `/d/` と `/edit` のあいだの ID |
   | `GOOGLE_SHEET_WORKSHEET` | シート名（省略時 `agent2_briefs`）。初回はヘッダ行を自動作成し、実行のたびに1行追記する。 |

**列の構成:** 設計書の主要フィールドを **プレフィックス付きの列**に分割して保存します（例: `mf_`＝市場ファクト、`tt_`＝TikTokアカウント、`ch_`＝キャラ、`pr_`＝プロフィール、`vs_`＝声、`cs_`＝コンテンツ仕様、`ps_`＝投稿戦略、`cr_`＝クリエイター要件、`ad_`＝マトリクス由来のアカウント設計）。配列はセル内で改行区切り、LLM が追加した未知のキーは各ブロックの `*_extra_json` に JSON で入ります。最後の `brief_json` に **1件分の完全 JSON**（長い場合は切り詰め）も残します。  
**既存シートとの互換:** 以前の「オブジェクトを数列の JSON にまとめた」形式の 1 行目が残っている場合、自動で **`（シート名）_v2_structured`** という別タブに追記します（旧データは触りません）。

---

## `matrix.json` の更新方法

1. `config/matrix.json` を編集する（バックアップ推奨）。
2. `version` や `last_updated` を更新すると運用で追いやすい。
3. カテゴリ名は **既存のキーと完全一致** させる（`matcher.get_best_match` が参照する）。
4. 各セルに `cvr`（`最高` / `高` / `中` / `低`）と `reason` を必ず入れる。

### CVR 判断の考え方

- **最高**: そのカテゴリでそのクリエイタータイプが最もコンバージョンに効くと判断できるとき。
- **高 / 中 / 低**: 訴求のしやすさ、信頼・エンタメのバランス、ターゲット一致度で相対的に決める。
- `reason` は「なぜその期待値か」を短く残し、後から `matrix_history` と突き合わせやすくする。

---

## ローカル実行

`agent2` をカレントにして実行するのがおすすめです。別ディレクトリから `python agent2/run_agent2.py` のように叩いても、**`agent2/.env` はスクリプト側のパスで読み込みます**（以前はカレントだけ見ていたため「キー未設定」になりやすかった）。

**uvicorn デモ経由でキー未設定になる場合:** Windows などでシステム／ターミナルに `ANTHROPIC_API_KEY=` のように**空の変数**だけが入っていると、通常の dotenv は上書きしません。`env_load` が **未設定または空のキーだけ** `.env` で埋めます。さらに `/api/run` の子プロセスには **`agent2/.env` を環境変数辞書へ明示マージ**するため、親に空キーが残っていても `run_agent2.py` に渡ります。反映されないときは **uvicorn を再起動**し、`.env` が **`account_create/agent2/.env`** にあること（リポジトリのルートではない）を確認してください。

```bash
cd agent2
python run_agent2.py
```

入力ファイルが無い・空・JSON でない場合はエラーログの後に終了コード `1` になります。

---

## Supabase（MCP）

1. [Supabase MCP の公式手順](https://supabase.com/docs/guides/getting-started/mcp)で Cursor を接続（**Settings → Cursor Settings → Tools & MCP**）。  
2. `db/schema.sql` でテーブル作成。  
3. `run_agent2.py` 実行後、`output/content_brief.json` を MCP の `execute_sql` 等で `content_briefs` に反映。  

詳細・依頼文の例: **`docs/supabase_mcp.md`**  
設定例（コピー用）: リポジトリルートの **`.cursor/mcp.json.example`**

---

## デモ UI（フロント）

ブラウザから状態確認・入力プレビュー・`run_agent2.py` 実行・`content_brief.json` の閲覧ができます。

**前提:** `agent2/.env` に `ANTHROPIC_API_KEY`。エージェント①モードでは `AGENT1_OUTPUT_PATH` も。キーはサーバー内のみで、フロントには出ません。

```bash
cd agent2
pip install -r requirements.txt
uvicorn demo.server:app --reload --host 127.0.0.1 --port 8765
```

ブラウザで `http://127.0.0.1:8765` を開きます（**8765 が埋まっているときは** `--port 8766` など別ポート。CORS は 8766 も許可済みです）。

- **接続状態:** 各 API が「設定済みか」のみ表示（値は表示しません）
- **実行:** 「エージェント①の JSON」または「自然言語だけ」を選び、`run_agent2.py` を起動（Claude 呼び出しのため時間がかかることがあります）
- **結果:** `output/content_brief.json` をカード表示（市場ファクト、アカウント・キャラ・プロフィール・声などを要約表示）

### Windows で `WinError 10013`（ソケットのアクセス許可）になるとき

多くの場合 **ポートが既に使用中**です（前回の uvicorn が残っている、別アプリが 8765 を掴んでいるなど）。

1. PowerShell で確認: `netstat -ano | findstr :8765`
2. 既にデモを動かしているなら **そのターミナルは閉じずにそのまま使う**か、止めてからもう一度起動する。
3. 別ポートで起動:  
   `uvicorn demo.server:app --reload --host 127.0.0.1 --port 8766`  
   ブラウザは `http://127.0.0.1:8766` を開く。

---

## GitHub Actions 設定

ワークフロー: `.github/workflows/agent2.yml`（リポジトリルート）

### Secrets の登録

GitHub の **Settings → Secrets and variables → Actions → New repository secret** で次を登録します。

| Secret 名 | 用途 |
|-----------|------|
| `ANTHROPIC_API_KEY` | Claude API キー |
| `AGENT1_OUTPUT_PATH` | ①の JSON へのパス（例: `fixtures/sample_input.json`） |

**注意:** CI から Supabase へは書き込みません。生成された `content_brief.json` を Artifact 等で受け取り、ローカルで **Supabase MCP** から反映してください。

手動実行は **Actions → Agent2 → Run workflow** から `workflow_dispatch` で可能です。

---

## 出力スキーマ

`output/content_brief.json` の各要素の定義は `CLAUDE.md` を参照してください。

## テスト

```bash
cd agent2
pytest tests/
```
