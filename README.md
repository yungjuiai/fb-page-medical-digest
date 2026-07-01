# 達叔礙唬爛 FB 粉專 醫療摘要機器人

每天自動檢查 Facebook 粉專「達叔礙唬爛」的最新貼文，用 Groq（免費 LLM API）判斷是否為醫療/治療相關內容，
若是則整理重點並透過 Telegram Bot 推播給你。透過 GitHub Actions 排程，不需要自己開機。

## 運作方式

1. `scripts/fetch_post.py`：用 headless 瀏覽器（Playwright）在不登入的狀態下讀取粉專最新一篇貼文
2. `scripts/llm_filter.py`：呼叫 Groq API（Llama 3.3 模型）判斷貼文是否與醫療/治療相關，並整理重點摘要
3. `scripts/telegram_notify.py`：把摘要推播到你的 Telegram
4. `scripts/run.py`：串起以上流程，並用 `state.json` 記錄上次處理過的貼文，避免重複通知
5. `.github/workflows/daily-digest.yml`：GitHub Actions 排程，每天台灣時間 08:00 自動執行一次

## 已知限制

- Facebook 現在要求登入才能瀏覽粉專內容，本專案採用「不登入、只讀取當下顯示的最新一篇貼文」的方式，
  所以**如果粉專一天內發多篇貼文，可能只會抓到執行當下最新的那一篇**。如果想降低漏抓機率，
  可以把 `.github/workflows/daily-digest.yml` 裡的 cron 改成一天執行多次（例如每 6 小時一次）。
- Facebook 隨時可能調整頁面結構或加強反爬蟲機制，若某天機器人抓不到貼文，代表 `scripts/fetch_post.py`
  需要更新（可以請我幫忙修）。曾測試過 Firecrawl 這類第三方擷取 API，但官方明確不支援 facebook.com，
  所以改用 Playwright 直接在 GitHub Actions 裡跑無頭瀏覽器；雲端 IP 仍有被 FB 判定異常流量而擋下的風險。
- 只有「醫療/治療相關」的貼文才會推播；其他貼文（活動宣傳、閒聊等）會被過濾掉不通知。想調整判斷標準，
  修改 `scripts/llm_filter.py` 裡的 `PROMPT_TEMPLATE` 即可。

## 首次設定

### 1. 建立 Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`，傳送 `/newbot`，依指示取名字，完成後會拿到一組 **Bot Token**
   （長得像 `123456789:ABCdefGhIJKlmNoPQRstuVwXyz`）
2. 跟你剛建立的 Bot 傳一句話（隨便打字）啟動對話
3. 用瀏覽器打開這個網址（把 `<TOKEN>` 換成你的 Bot Token）：
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   在回傳的 JSON 裡找到 `"chat":{"id":數字, ...}`，這個數字就是你的 **Chat ID**

### 2. 取得 Groq API Key（免費，不需信用卡）

前往 https://console.groq.com/ 註冊，在 API Keys 頁面建立一組 Key。

### 3. 在 GitHub 設定 Secrets

到這個 repo 的 GitHub 頁面：**Settings → Secrets and variables → Actions → New repository secret**，
新增以下三組（名稱要完全一致）：

| Secret 名稱 | 內容 |
|---|---|
| `GROQ_API_KEY` | 你的 Groq API Key |
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你的 Telegram Chat ID |

（`FIRECRAWL_API_KEY` 已不再使用，可以從 Secrets 裡刪除，或留著也沒關係。）

### 4. 手動測試一次

到 repo 的 **Actions** 分頁 → 選 **Daily FB Page Digest** → **Run workflow**，手動觸發一次，
確認 Telegram 有收到訊息（或 Actions log 顯示「貼文不相關，略過通知」也代表流程是正常的）。

## 本機開發

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/playwright install chromium

export GROQ_API_KEY=xxx
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
cd scripts && ../.venv/bin/python3 run.py
```
