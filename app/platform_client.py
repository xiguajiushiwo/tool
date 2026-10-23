from __future__ import annotations

from datetime import date, timedelta
import uuid

import httpx


class PlatformError(RuntimeError):
    pass


class YunxiaoquanClient:
    def __init__(self, base_url: str, username: str = "", password: str = "", mock: bool = True):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.mock = mock
        self.http = httpx.AsyncClient(base_url=self.base_url, timeout=30, follow_redirects=True)
        self.logged_in = False

    async def close(self) -> None:
        await self.http.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        response = await self.http.request(method, path, **kwargs)
        try:
            payload = response.json()
        except ValueError as exc:
            raise PlatformError(f"平台返回了非 JSON 响应：HTTP {response.status_code}") from exc
        if response.status_code == 401:
            self.logged_in = False
            raise PlatformError("云小圈登录已失效")
        if response.status_code >= 400 or payload.get("ok") is False:
            raise PlatformError(payload.get("error") or f"平台请求失败：HTTP {response.status_code}")
        return payload

    async def login(self) -> None:
        if self.mock:
            self.logged_in = True
            return
        if not self.username or not self.password:
            raise PlatformError("未配置 PLATFORM_USERNAME / PLATFORM_PASSWORD")
        await self._request("POST", "/api/auth/login", json={"username": self.username, "password": self.password, "deviceId": f"codex-local-{uuid.uuid4()}"})
        self.logged_in = True

    async def ensure_login(self) -> None:
        if self.logged_in:
            return
        if not self.mock:
            try:
                await self._request("GET", "/api/auth/session")
                self.logged_in = True
                return
            except PlatformError:
                pass
        await self.login()

    async def create_quote_draft(self) -> dict:
        await self.ensure_login()
        if self.mock:
            return {"quote": {"id": uuid.uuid4().hex[:8]}, "mock": True}
        return await self._request("POST", "/api/sales-quotes", json={"sourceEntryIds": []})

    async def parse_quote(self, quote_id: str | int, text: str) -> dict:
        await self.ensure_login()
        if self.mock:
            return {"result": {"items": [{"itemName": text[:80], "brand": "", "modelSpec": "", "unit": "个", "quantity": "", "taxIncludedUnitPrice": "", "remark": text}], "delivery": "", "warranty": ""}}
        return await self._request("POST", "/api/sales-quotes/ai/parse", json={"sessionId": str(uuid.uuid4()), "quoteId": quote_id, "inputMode": "text", "text": text})

    async def save_quote_draft(self, quote_id: str | int, result: dict) -> dict:
        await self.ensure_login()
        snapshot = {
            "companyEntityId": None, "customerId": None,
            "customerName": result.get("customerMention") or "",
            "customerContact": result.get("customerContact") or "",
            "customerPhone": result.get("customerPhone") or "",
            "customerAddress": result.get("customerAddress") or "",
            "validUntil": result.get("validUntil") or (date.today() + timedelta(days=7)).isoformat(),
            "warranty": result.get("warranty") or "", "delivery": result.get("delivery") or "", "templateCode": "nostamp",
            "items": [{"lineKey": str(uuid.uuid4()), "itemName": item.get("itemName") or "", "brand": item.get("brand") or "", "modelSpec": item.get("modelSpec") or "", "unit": item.get("unit") or "个", "quantity": item.get("quantity") or "", "taxIncludedUnitPrice": item.get("taxIncludedUnitPrice") or "", "remark": item.get("remark") or "", "sourceEntryId": None} for item in (result.get("items") or [])],
        }
        if self.mock:
            return {"quote": {"id": quote_id, "status": "draft"}, "snapshot": snapshot, "mock": True}
        return await self._request("PUT", f"/api/sales-quotes/{quote_id}/save", json=snapshot)

    async def parse_entry(self, entry_type: str, text: str) -> dict:
        await self.ensure_login()
        if self.mock:
            return {"result": {"fields": {"productType": "其他", "quantity": "", "unitPrice": "", "notes": text}}}
        return await self._request("POST", "/api/entry-ai/parse", json={"sessionId": str(uuid.uuid4()), "entryType": entry_type, "inputMode": "text", "text": text})
