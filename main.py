import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from handlers import register_handlers
from api.client import KBJUApiClient

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    bot_token = os.getenv("BOT_TOKEN")
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    if not bot_token:
        raise RuntimeError(f"Переменная окружения {BOT_TOKEN_ENV} не установлена")

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    api_client = KBJUApiClient(base_url=api_base_url)

    register_handlers(dp, api_client=api_client)

    logger.info("Запуск бота...")
    await dp.start_polling(bot, api_client=api_client)


if __name__ == "__main__":
    asyncio.run(main())
