# 企业微信群 -> 云小圈自动填单服务

本地 MVP 接收一条模拟企业微信消息，识别报价、需求或货源，并调用云小圈接口。默认 `PLATFORM_MOCK=true`，不会访问真实平台，也不会生成正式报价单。

## 启动

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8787
```

## 本地模拟

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
Invoke-RestMethod -Method Post http://127.0.0.1:8787/dev/messages `
  -ContentType 'application/json' `
  -Body '{"message_id":"demo-1","chat_id":"销售群","sender_id":"张三","text":"请给客户李总做报价：三星64G内存100件，单价1200元，7天交货"}'
Invoke-WebRequest -Method Post http://127.0.0.1:8787/records/export -OutFile data\\records.xlsx
```

## 连接真实云小圈

在本地 `.env` 填写平台账号后设置 `PLATFORM_MOCK=false`。账号密码只放在本机环境变量中，不要提交到 Git 或发送到聊天。第一版只创建并保存报价草稿，不调用正式报价生成接口。

## 企业微信回调

本地测试可直接 POST 明文 JSON 到 `/wecom/callback`。真实智能机器人回调需要把 `/wecom/callback` 映射成公网 HTTPS，并在 `.env` 配置 `WECOM_TOKEN` 与 `WECOM_ENCODING_AES_KEY`。企业微信服务器不能直接访问 `127.0.0.1` 或局域网 IP。
