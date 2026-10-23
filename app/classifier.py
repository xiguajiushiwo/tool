import re

from .models import MessageKind


def classify(text: str) -> MessageKind:
    value = text.strip().lower()
    if any(token in value for token in ("报价", "报个价", "给客户", "报价单")):
        return "quote"
    if any(token in value for token in ("求购", "需求", "需要", "采购")):
        return "demand"
    if any(token in value for token in ("货源", "现货", "出货", "供应", "出售", "卖")):
        return "supply"
    return "unknown"


def local_extract(text: str, kind: MessageKind, envelope: dict[str, str]) -> dict:
    amount = re.search(r"(?:数量|数目)\s*[:：]?\s*([\d,.]+)", text)
    price = re.search(r"(?:单价|价格|报价|售价|目标价)\s*[:：]?\s*([\d,.]+)", text)
    return {
        "kind": kind,
        "product": text[:120],
        "quantity": amount.group(1) if amount else None,
        "unit_price": price.group(1) if price else None,
        "source_chat_id": envelope["chat_id"],
        "source_message_id": envelope["message_id"],
        "status": "draft" if kind == "quote" else "needs_review",
        "raw_text": text,
    }
