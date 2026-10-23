from fastapi.testclient import TestClient
import uuid

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_quote_message_creates_local_draft():
    response = client.post("/dev/messages", json={"message_id": f"test-quote-{uuid.uuid4()}", "chat_id": "sales-group", "sender_id": "alice", "text": "请给客户张三做报价：三星 64G 内存 100件，单价 1200 元，7天交货"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "quote"
    assert payload["status"] == "draft"
    assert "sales-quote-workbench.html?id=" in payload["platform_url"]


def test_duplicate_message_is_ignored():
    body = {"message_id": f"duplicate-{uuid.uuid4()}", "text": "需求：需要 10 台服务器"}
    assert client.post("/dev/messages", json=body).json()["status"] == "needs_review"
    assert client.post("/dev/messages", json=body).json()["status"] == "duplicate"
