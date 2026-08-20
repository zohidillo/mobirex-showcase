from dataclasses import dataclass
import os
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    support_group_id: int
    database_path: str
    redis_url: str


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    support_group_id = os.getenv("SUPPORT_GROUP_ID", "").strip()
    database_path = os.getenv("DATABASE_PATH", "data/support_bot.db").strip()
    redis_url = os.getenv("REDIS_URL", "redis://bot_redis:6379/0").strip()

    if not bot_token:
        raise RuntimeError("BOT_TOKEN .env faylda yozilmagan")

    if not support_group_id:
        raise RuntimeError("SUPPORT_GROUP_ID .env faylda yozilmagan")

    try:
        support_group_id_int = int(support_group_id)
    except ValueError as exc:
        raise RuntimeError("SUPPORT_GROUP_ID raqam bo'lishi kerak. Masalan: -1001234567890") from exc

    return Settings(
        bot_token=bot_token,
        support_group_id=support_group_id_int,
        database_path=database_path,
        redis_url=redis_url,
    )
