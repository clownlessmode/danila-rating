#!/usr/bin/env python3
"""
Danila Rating Bot - Telegram бот для отслеживания социального рейтинга Данилы
"""

import asyncio
import json
import os
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Файл для хранения рейтинга
DATA_FILE = Path(__file__).parent / "rating.json"

# Система положений: (мин_балл, название) — примерно каждые 50 баллов
# Ищем первое порог где rating >= мин_балл (от большего к меньшему)
RATING_TIERS = [

    # ===== ПОЗИТИВ =====
    (500, "Бог среди смертных"),
    (475, "Легенда чата"),
    (450, "Неприкасаемый"),
    (425, "Икона стиля"),
    (400, "Царь горы"),
    (375, "Альфа-самец"),
    (350, "Босс мафии"),
    (325, "Крёстный отец"),
    (300, "Мастер кайфа"),
    (275, "Душа компании"),
    (250, "Профи"),
    (225, "Красавчик"),
    (200, "Уважаемый"),
    (175, "Свой в доску"),
    (150, "Норм пацан"),
    (125, "Поднимается"),
    (100, "Исправляется"),
    (75, "Подаёт надежды"),
    (50, "Пацан"),
    (25, "Зелёный"),
    (10, "Начал путь"),

    # ===== НЕЙТРАЛ =====
    (0, "Нейтрал"),

    # ===== НЕГАТИВ =====
    (-10, "Мусорка"),
    (-25, "Шкура"),
    (-50, "Позор рода"),
    (-75, "Чмошник"),
    (-100, "Опущенный"),
    (-125, "Шавка подзаборная"),
    (-150, "Дно пробито"),
    (-175, "Хуеприёмник"),
    (-200, "Залупочёс"),
    (-225, "Сосатель бесплатный"),
    (-250, "Пиздоглот"),
    (-275, "Чмо болотное"),
    (-300, "Огрызок хуя"),
    (-325, "Подстилка вокзальная"),
    (-350, "Хуй моржовый"),
    (-375, "Гандон штопаный"),
    (-400, "Пердёж сатаны"),
    (-425, "Выкидыш кладбища"),
    (-450, "Абсолютный ноль"),
    (-475, "Аннигилирован"),
    (-500, "Ошибка природы"),
    (-99999, "Не существует"),
]


def get_rating() -> int:
    """Загружает текущий рейтинг из файла."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rating", 0)
    return 0


def save_rating(rating: int) -> None:
    """Сохраняет рейтинг в файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"rating": rating}, f, ensure_ascii=False, indent=2)


async def reply_and_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delay: float = 2.0) -> None:
    """Отправляет ответ, удаляет сообщение юзера и свой ответ через delay сек."""
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id=chat_id, text=text)
    try:
        await update.message.delete()
    except Exception:
        pass
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


def get_position(rating: int) -> str:
    """Возвращает положение по рейтингу."""
    # Сортируем по убыванию балла
    sorted_tiers = sorted(RATING_TIERS, key=lambda x: x[0], reverse=True)
    for min_score, position in sorted_tiers:
        if rating >= min_score:
            return position
    return "Неизвестно"


async def cmd_danilalox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /danilalox — минус 10 к рейтингу."""
    rating = get_rating()
    rating -= 10
    save_rating(rating)
    await reply_and_cleanup(update, context, f"📉 -10. Рейтинг Данилы: {rating}")


async def cmd_danila_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка /danila klass (два слова)."""
    if context.args and context.args[0].lower() == "klass":
        await cmd_danila_klass(update, context)
    else:
        await reply_and_cleanup(update, context, "Использование: /danila klass — +10 к рейтингу")

CHEMIAKIN_USERNAME = "chemiakin"
PURPLETOOTH_USERNAME = "purpletooth"

class BlockChimiakin(filters.MessageFilter):
    """Фильтр: True если сообщение от chemiakin."""
    def filter(self, message):
        if not message or not message.from_user:
            return False
        return (message.from_user.username or "").lower() == CHEMIAKIN_USERNAME


async def block_chemiakin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Полная блокировка chemiakin — не отвечаем, ничего не делаем."""
    pass


async def cmd_danila_klass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /danila klass — плюс 10 к рейтингу."""
    rating = get_rating()
    rating += 10
    save_rating(rating)
    await reply_and_cleanup(update, context, f"📈 +10. Рейтинг Данилы: {rating}")


SELF_LIKER_ID = 5301118406

async def roast_self_liker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Если пишет юзер 5301118406 — ростим за самолайк."""
    if update.effective_user and update.effective_user.id == SELF_LIKER_ID:
        await reply_and_cleanup(
            update, context, "Ты еблан, самолайк — это как самоотсос, че ты делаешь?"
        )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /clear — сброс рейтинга. Только для @PurpleTooth."""
    username = (update.effective_user.username or "").lower()
    if username != PURPLETOOTH_USERNAME:
        return  # не отвечаем чужим
    save_rating(0)
    await reply_and_cleanup(update, context, "✅ Рейтинг сброшен на 0")


async def cmd_danilarating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /danilarating — показывает социальный рейтинг и положение."""
    rating = get_rating()
    position = get_position(rating)
    await reply_and_cleanup(
        update, context,
        f"📊 Социальный рейтинг Данилы: {rating}\n📍 Положение: {position}",
    )


def main() -> None:
    token = "8584176205:AAGe7iVJrleWNLXM4mBYU6PyW4SPG2amKUU"
    if not token:
        print("Установи переменную TELEGRAM_BOT_TOKEN с токеном бота")
        return

    app = Application.builder().token(token).build()

    # Сначала блокируем chemiakin — его сообщения игнорируем полностью
    app.add_handler(MessageHandler(BlockChimiakin(), block_chemiakin))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("danilalox", cmd_danilalox))
    app.add_handler(CommandHandler("danilaklass", cmd_danila_klass))
    app.add_handler(CommandHandler("danila", cmd_danila_wrapper))
    app.add_handler(CommandHandler("danilarating", cmd_danilarating))
    app.add_handler(MessageHandler(filters.User(user_id=SELF_LIKER_ID) & filters.TEXT, roast_self_liker))

    print("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
