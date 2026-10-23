from __future__ import annotations

import hashlib
import time
import uuid

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse

from .config import settings
from .models import DevMessageRequest, MessageEnvelope
from .pipeline import Pipeline
from .platform_client import YunxiaoquanClient
from .store import Store
from .wecom_crypto import WeComCrypto


store = Store(settings.database_path)
platform = YunxiaoquanClient(settings.platform_base_url, settings.platform_username, settings.platform_password, settings.platform_mock)
pipeline = Pipeline(store, platform, settings.platform_base_url)
app = FastAPI(title="WeCom Yunxiaoquan Integration", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "platform_mock": settings.platform_mock}


@app.post("/dev/messages")
async def dev_message(request: DevMessageRequest):
    envelope = MessageEnvelope(message_id=request.message_id or str(uuid.uuid4()), chat_id=request.chat_id, sender_id=request.sender_id, text=request.text)
    return await pipeline.process(envelope)


@app.get("/records")
async def records() -> dict:
    return {"ok": True, "records": [item.model_dump(mode="json") for item in store.list_records()]}


@app.post("/records/export")
async def export_records():
    path = store.export_xlsx(settings.export_path)
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/wecom/callback")
async def wecom_verify(msg_signature: str = Query(""), timestamp: str = Query(""), nonce: str = Query(""), echostr: str = Query("")):
    if not settings.wecom_token or not settings.wecom_encoding_aes_key:
        raise HTTPException(503, "尚未配置 WECOM_TOKEN 和 WECOM_ENCODING_AES_KEY")
    crypto = WeComCrypto(settings.wecom_token, settings.wecom_encoding_aes_key)
    if not crypto.verify(msg_signature, timestamp, nonce, echostr):
        raise HTTPException(403, "企业微信回调签名校验失败")
    return PlainTextResponse(crypto.decrypt(echostr))


@app.post("/wecom/callback")
async def wecom_callback(request: Request):
    body = await request.json()
    if "text" in body:
        envelope = MessageEnvelope(message_id=str(body.get("message_id") or uuid.uuid4()), chat_id=str(body.get("chat_id") or "wecom"), sender_id=str(body.get("sender_id") or "wecom-user"), text=str(body["text"]))
        return await pipeline.process(envelope)
    if not settings.wecom_token or not settings.wecom_encoding_aes_key:
        raise HTTPException(503, "本地明文回调可用；真实企业微信回调还需配置 Token 和 EncodingAESKey")
    encrypted = body.get("encrypt")
    if not encrypted:
        raise HTTPException(400, "缺少 encrypt")
    timestamp = request.query_params.get("timestamp", str(int(time.time())))
    nonce = request.query_params.get("nonce", "")
    signature = request.query_params.get("msg_signature", "")
    crypto = WeComCrypto(settings.wecom_token, settings.wecom_encoding_aes_key)
    if not crypto.verify(signature, timestamp, nonce, encrypted):
        raise HTTPException(403, "企业微信回调签名校验失败")
    message = crypto.decrypt_json(encrypted)
    envelope = MessageEnvelope(message_id=str(message.get("msgid") or hashlib.sha1(encrypted.encode()).hexdigest()), chat_id=str(message.get("chatid") or "wecom"), sender_id=str(message.get("from") or "wecom-user"), text=str(message.get("text", {}).get("content") or message.get("content") or ""))
    return await pipeline.process(envelope)
