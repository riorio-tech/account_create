# 例: Railway / Render / Fly.io などで agent2 デモ API を常時起動する場合
# ビルド: docker build -t agent2-demo -f agent2/Dockerfile .
# 実行: docker run -p 8765:8765 --env-file agent2/.env agent2-demo

FROM python:3.12-slim

WORKDIR /app

COPY agent2/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent2/ /app/

ENV PYTHONUNBUFFERED=1
EXPOSE 8765

CMD ["uvicorn", "demo.server:app", "--host", "0.0.0.0", "--port", "8765"]
