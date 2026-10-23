from pathlib import Path
import sqlite3
from typing import Iterable

from openpyxl import Workbook

from .models import MessageEnvelope, StructuredRecord


class Store:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    received_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_message(self, envelope: MessageEnvelope) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO messages(message_id, chat_id, sender_id, text, received_at) VALUES (?, ?, ?, ?, ?)",
                (envelope.message_id, envelope.chat_id, envelope.sender_id, envelope.text, envelope.received_at.isoformat()),
            )
            return cursor.rowcount == 1

    def save_record(self, record: StructuredRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO records(message_id, payload, created_at) VALUES (?, ?, ?)",
                (record.source_message_id, record.model_dump_json(), record.created_at.isoformat()),
            )

    def list_records(self) -> list[StructuredRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM records ORDER BY id DESC").fetchall()
        return [StructuredRecord.model_validate_json(row["payload"]) for row in rows]

    def export_xlsx(self, output_path: str, records: Iterable[StructuredRecord] | None = None) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = list(records if records is not None else self.list_records())
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "自动录入"
        sheet.append(["类型", "客户", "产品", "规格型号", "数量", "单价", "卖价", "币种", "截止日期", "交付", "质保", "备注", "来源群", "原消息ID", "状态", "原文"])
        for item in rows:
            sheet.append([item.kind, item.customer, item.product, item.model_spec, item.quantity, item.unit_price, item.sale_price, item.currency, item.deadline, item.delivery, item.warranty, item.notes, item.source_chat_id, item.source_message_id, item.status, item.raw_text])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        workbook.save(path)
        return path
