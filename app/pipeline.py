from .classifier import classify, local_extract
from .models import MessageEnvelope, ProcessResult, StructuredRecord
from .platform_client import YunxiaoquanClient
from .store import Store


class Pipeline:
    def __init__(self, store: Store, platform: YunxiaoquanClient, platform_base_url: str):
        self.store = store
        self.platform = platform
        self.platform_base_url = platform_base_url.rstrip("/")

    async def process(self, envelope: MessageEnvelope) -> ProcessResult:
        if not self.store.save_message(envelope):
            return ProcessResult(ok=True, message_id=envelope.message_id, kind="unknown", status="duplicate", message="重复消息，已忽略")
        kind = classify(envelope.text)
        if kind == "unknown":
            record = StructuredRecord(**local_extract(envelope.text, kind, envelope.model_dump()))
            self.store.save_record(record)
            return ProcessResult(ok=True, message_id=envelope.message_id, kind=kind, status=record.status, message="未识别为报价、需求或货源，已保存待人工判断", record=record)
        try:
            if kind == "quote":
                draft = await self.platform.create_quote_draft()
                quote_id = draft["quote"]["id"]
                parsed = await self.platform.parse_quote(quote_id, envelope.text)
                saved = await self.platform.save_quote_draft(quote_id, parsed.get("result") or {})
                platform_url = f"{self.platform_base_url}/sales-quote-workbench.html?id={quote_id}"
                result = parsed.get("result") or {}
                items = result.get("items") or []
                record = StructuredRecord(kind="quote", customer=result.get("customerMention"), product=(items[0].get("itemName") if items else None), source_chat_id=envelope.chat_id, source_message_id=envelope.message_id, platform_url=platform_url, status="draft", raw_text=envelope.text, extra={"quote_id": quote_id, "platform_response": saved})
                self.store.save_record(record)
                return ProcessResult(ok=True, message_id=envelope.message_id, kind=kind, status="draft", message="报价草稿已保存，尚未确认生成正式报价单", platform_url=platform_url, record=record)
            parsed = await self.platform.parse_entry(kind, envelope.text)
            record = StructuredRecord(kind=kind, source_chat_id=envelope.chat_id, source_message_id=envelope.message_id, status="needs_review", raw_text=envelope.text, extra={"platform_parse": parsed.get("result")})
            self.store.save_record(record)
            return ProcessResult(ok=True, message_id=envelope.message_id, kind=kind, status="needs_review", message=f"已识别为{kind}，已保存待确认，暂未正式发布", record=record)
        except Exception as exc:
            record = StructuredRecord(kind=kind, source_chat_id=envelope.chat_id, source_message_id=envelope.message_id, status="failed", raw_text=envelope.text, extra={"error": str(exc)})
            self.store.save_record(record)
            return ProcessResult(ok=False, message_id=envelope.message_id, kind=kind, status="failed", message=str(exc), record=record)
