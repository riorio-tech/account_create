# account_create

TikTok コマース向けの設計フロー用モノレポです。メインの実装は **`agent2/`**（コンテンツ設計エージェント）にあります。

- セットアップ・実行手順: [`agent2/README.md`](agent2/README.md)
- GitHub Actions: `.github/workflows/agent2.yml`（Secrets に API キー等を設定）

## Vercel について

`agent2` のデモは **FastAPI（uvicorn）＋長時間の API 呼び出し＋サブプロセス**のため、**Vercel のサーバーレスだけではそのまま動かせません**。接続して 404 になる場合は、プロジェクトに **`public/index.html`** と **`vercel.json`** があり、デプロイ後は **説明用の静的ページ**が表示される想定です（再デプロイが必要です）。

インターネット上で同じデモ UI が必要な場合は、各クラウドの「Python / uvicorn を常時起動」手順に沿って `agent2` を配置し、環境変数は `agent2/.env` と同様にホスティング側で設定してください（Docker は使わなくて構いません）。
