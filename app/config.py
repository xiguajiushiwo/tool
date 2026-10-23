from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    platform_base_url: str = os.getenv("PLATFORM_BASE_URL", "https://trade.yunxiaoquan.cn")
    platform_username: str = os.getenv("PLATFORM_USERNAME", "")
    platform_password: str = os.getenv("PLATFORM_PASSWORD", "")
    platform_mock: bool = os.getenv("PLATFORM_MOCK", "true").lower() in {"1", "true", "yes"}
    database_path: str = os.getenv("DATABASE_PATH", "data/integration.sqlite3")
    export_path: str = os.getenv("EXPORT_PATH", "data/records.xlsx")
    wecom_token: str = os.getenv("WECOM_TOKEN", "")
    wecom_encoding_aes_key: str = os.getenv("WECOM_ENCODING_AES_KEY", "")


settings = Settings()
