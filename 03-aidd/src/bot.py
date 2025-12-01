import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from .config import LOG_LEVEL, TELEGRAM_BOT_TOKEN
from .llm import ask_llm

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Глобальная структура для хранения истории диалога по user_id
dialog_context: dict[int, list[dict]] = {}
MAX_HISTORY_LENGTH = 8  # последние 8 сообщений (между 6-10)


async def main() -> None:
    logger.info("Starting bot...")
    token = TELEGRAM_BOT_TOKEN

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        user_id = message.from_user.id
        logger.info(f"Command /start from user {user_id}")
        # Очищаем контекст диалога для пользователя
        dialog_context.pop(user_id, None)

        text = (
            "Привет! Я твой персональный туристический консультант.\n\n"
            "Помогу подобрать направление, сезон, маршрут, отели и активности под твой бюджет и предпочтения.\n\n"
            "Примеры вопросов:\n"
            "• \"Подбери маршрут по Италии на 7 дней в мае, бюджет 1500 евро на двоих\"\n"
            "• \"Куда поехать на море в сентябре с детьми 5 и 8 лет?\"\n"
        )
        await message.answer(text)

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        user_id = message.from_user.id
        logger.info(f"Command /help from user {user_id}")
        text = (
            "Я помогаю с идеями и планированием путешествий:\n"
            "- выбор страны и города;\n"
            "- подбор сезона и длительности поездки;\n"
            "- примерные маршруты по дням;\n"
            "- рекомендации по районам и типам отелей;\n"
            "- варианты активностей и достопримечательностей.\n\n"
            "Чтобы ответ был точнее, указывай:\n"
            "- примерные даты или месяц;\n"
            "- бюджет и количество людей;\n"
            "- важные предпочтения (море/города/природа, дети, формат отдыха).\n\n"
            "Важно: я не бронирую билеты и отели, а даю рекомендации и варианты."
        )
        await message.answer(text)

    @dp.message(Command("reset"))
    async def cmd_reset(message: Message) -> None:
        user_id = message.from_user.id
        logger.info(f"Command /reset from user {user_id}")
        # Очищаем контекст диалога для пользователя
        dialog_context.pop(user_id, None)
        await message.answer("История диалога очищена, начнём сначала.")

    @dp.message(F.text)
    async def llm_handler(message: Message) -> None:
        user_id = message.from_user.id
        user_text = message.text

        # Логируем входящее сообщение (обрезаем длинный текст)
        text_preview = user_text[:50] + "..." if len(user_text) > 50 else user_text
        logger.info(f"Message from user {user_id}: {text_preview}")

        # Инициализация истории для нового пользователя
        if user_id not in dialog_context:
            dialog_context[user_id] = []

        # Добавляем сообщение пользователя в историю
        dialog_context[user_id].append({"role": "user", "content": user_text})

        # Обрезаем историю до последних MAX_HISTORY_LENGTH сообщений
        if len(dialog_context[user_id]) > MAX_HISTORY_LENGTH:
            dialog_context[user_id] = dialog_context[user_id][-MAX_HISTORY_LENGTH:]

        try:
            # Передаём историю без текущего сообщения (оно уже добавлено выше)
            history = dialog_context[user_id][:-1]
            logger.info(f"Calling LLM for user {user_id}, history length: {len(history)}")
            reply = await ask_llm(user_text, history)
            reply_preview = reply[:50] + "..." if len(reply) > 50 else reply
            logger.info(f"LLM response for user {user_id}: {reply_preview}")
        except Exception as e:
            logger.error(f"Error in LLM handler for user {user_id}", exc_info=True)
            await message.answer("Сервис временно недоступен, попробуйте позже.")
            raise

        # Добавляем ответ ассистента в историю
        dialog_context[user_id].append({"role": "assistant", "content": reply})

        # Снова обрезаем на случай, если превысили лимит
        if len(dialog_context[user_id]) > MAX_HISTORY_LENGTH:
            dialog_context[user_id] = dialog_context[user_id][-MAX_HISTORY_LENGTH:]

        await message.answer(reply)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


