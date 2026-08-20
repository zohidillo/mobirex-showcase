import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.config import get_settings
from app.db import Database
from app.handlers import router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = get_settings()

    db = Database(settings.database_path)
    await db.init()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        storage = RedisStorage.from_url(settings.redis_url)
        logging.info("FSM storage: Redis (%s)", settings.redis_url)
    except Exception as exc:
        logging.warning("Redis ulanmadi (%s), MemoryStorage fallback", exc)
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # Handlerlarga dependency qilib uzatiladi:
    dp["db"] = db
    dp["support_group_id"] = settings.support_group_id

    logging.info("CRM support bot ishga tushdi")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
