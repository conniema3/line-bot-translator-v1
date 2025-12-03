# Line Bot 真心話翻譯機 (V1 MVP)

這是一個基於 FastAPI 和 Line Messaging API 的 Line Bot，旨在翻譯伴侶的「真心話」。

## 功能
- **角色設定**：輸入 `設定：男友` 或 `設定：女友` 來設定你的角色。
- **自動翻譯**：當你輸入 `翻譯`、`譯` 或 `1` 時，Bot 會讀取上一條訊息並透過 Google Gemini API 進行情感翻譯。
- **一對一專用**：Bot 僅支援一對一聊天，若被加入群組會自動退出。

## 安裝與執行

### 1. 安裝依賴
確保你已經安裝 Python 3.11+。
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
複製 `env.example` 為 `.env` 並填入你的 API Key。
```bash
cp env.example .env
```
你需要填入：
- `LINE_CHANNEL_SECRET`: Line Developers Console 取得
- `LINE_CHANNEL_ACCESS_TOKEN`: Line Developers Console 取得
- `GOOGLE_API_KEY`: Google AI Studio 取得

### 3. 啟動伺服器
```bash
uvicorn main:app --reload
```

### 4. 設定 Webhook
使用 ngrok 或其他工具將本地 8000 port 暴露至網際網路，並將 URL (例如 `https://xxxx.ngrok.io/callback`) 填入 Line Developers Console 的 Webhook URL 欄位。

## 專案結構
- `main.py`: FastAPI 主程式與 Line Bot Webhook 處理邏輯。
- `store.py`: 簡單的記憶體資料儲存 (MVP 用)。
- `llm_client.py`: Google Gemini API 串接邏輯。
- `requirements.txt`: 專案依賴列表。
