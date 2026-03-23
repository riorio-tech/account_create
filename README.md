# account_create

TikTok コマース向けの設計フロー用モノレポです。メインの実装は **`agent2/`**（コンテンツ設計エージェント）にあります。

- セットアップ・実行手順: [`agent2/README.md`](agent2/README.md)
- GitHub Actions: `.github/workflows/agent2.yml`（Secrets に API キー等を設定）

## Vercel について

`agent2` のデモは **FastAPI（uvicorn）＋長時間の API 呼び出し＋サブプロセス**のため、**Vercel のサーバーレスだけではそのまま動かせません**。接続して 404 になる場合は、プロジェクトに **`public/index.html`** と **`vercel.json`** があり、デプロイ後は **説明用の静的ページ**が表示される想定です（再デプロイが必要です）。

実際の Web UI をインターネット上で動かすには **Railway / Render / Fly.io** などでコンテナ実行するのが向いています。リポジトリルートから:

```bash
docker build -t agent2-demo -f agent2/Dockerfile .
docker run -p 8765:8765 --env-file agent2/.env agent2-demo
```

環境変数はホスティング側のダッシュボードで `agent2/.env` と同様に設定してください。
