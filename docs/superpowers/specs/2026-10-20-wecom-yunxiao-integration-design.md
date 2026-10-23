# 企业微信群消息到云小圈草稿设计

## 目标

接收企业微信群中 `@` 智能机器人的文本，将内容识别为报价、需求或货源。报价消息调用云小圈的报价 AI 解析接口，创建并保存报价草稿，返回草稿链接；需求和货源先识别并保存待确认记录，不自动正式发布。

## 方案

服务端运行在用户本地，通过 HTTPS 客户端主动访问云小圈 API。真实企业微信回调需要使用 Cloudflare Tunnel 或 frp 暴露单个 HTTPS 回调路径。平台账号由本地环境变量提供，平台会话由 `httpx` CookieJar 保持。

## 安全边界

- 第一版不调用报价正式生成接口。
- 不保存或传输企业微信群的全量消息，只处理机器人收到的消息。
- 账号密码只存在本机环境变量，不写入代码和日志。
- 所有平台写入通过消息 ID 防止重复创建。

## 已确认的平台接口

- `POST /api/auth/login`
- `POST /api/sales-quotes`
- `POST /api/sales-quotes/ai/parse`
- `PUT /api/sales-quotes/{id}/save`
- `POST /api/entry-ai/parse`
- `POST /api/entries`（后续正式发布阶段使用）
