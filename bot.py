#!/usr/bin/env python3
"""
Danila Rating Bot - Telegram бот для отслеживания социального рейтинга Данилы
"""

import asyncio
import json
import os
from pathlib import Path

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, MessageReactionHandler, filters, ContextTypes

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


def get_data() -> dict:
    """Загружает данные из файла."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rating": 0, "users": {}}


def save_data(data: dict) -> None:
    """Сохраняет данные в файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_rating() -> int:
    """Рейтинг Данилы."""
    return get_data().get("rating", 0)


def save_rating(rating: int) -> None:
    """Сохраняет рейтинг Данилы."""
    data = get_data()
    data["rating"] = rating
    save_data(data)


def get_user_rating(user_id: int) -> int:
    """Рейтинг пользователя по user_id."""
    return get_data().get("users", {}).get(str(user_id), 0)


def add_to_user_rating(user_id: int, delta: int) -> int:
    """Добавляет delta к рейтингу пользователя. Возвращает новый рейтинг."""
    data = get_data()
    users = data.setdefault("users", {})
    uid = str(user_id)
    users[uid] = users.get(uid, 0) + delta
    save_data(data)
    return users[uid]


async def _cleanup_task(bot, chat_id, user_msg_id, bot_msg, delay: float) -> None:
    """Фоновая задача: удалить сообщения через delay сек."""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=user_msg_id)
    except Exception:
        pass
    await asyncio.sleep(delay)
    try:
        await bot_msg.delete()
    except Exception:
        pass


async def reply_and_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delay: float = 2.0) -> None:
    """Отправляет ответ, в фоне удаляет сообщение юзера и свой ответ через delay сек."""
    try:
        chat_id = update.effective_chat.id
        user_msg_id = update.message.message_id if update.message else None
        msg = await context.bot.send_message(chat_id=chat_id, text=text)
        if user_msg_id:
            asyncio.create_task(_cleanup_task(context.bot, chat_id, user_msg_id, msg, delay))
    except BadRequest:
        pass  # Message to be replied not found и т.п. — игнорируем


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
# Юзернейм Данилы — его сообщения проверяет нейросеть
DANILA_USERNAME = "danilalox"  # укажи реальный @username в Telegram

class DanilaFilter(filters.MessageFilter):
    """Фильтр: True если сообщение от Данилы."""
    def filter(self, message):
        if not message or not message.from_user:
            return False
        return (message.from_user.username or "").lower() == DANILA_USERNAME


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


def _get_emoji_from_reaction(r) -> str:
    """Извлекает emoji из ReactionType."""
    if hasattr(r, "emoji"):
        return r.emoji or ""
    return getattr(r, "emoji", "") or ""


def _resolve_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple | None:
    """
    Определяет целевого пользователя: из reply или из @username.
    Возвращает (user_id, display_name) или ("self", None) если сам себе, или None если не найден.
    """
    msg = update.message
    sender = update.effective_user
    if not msg or not sender:
        return None

    # 1. Reply на сообщение
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user
        if target.id == sender.id:
            return ("self", None)
        name = f"@{target.username}" if target.username else (target.first_name or str(target.id))
        return (target.id, name)

    # 2. @username в аргументах
    args = context.args or []
    users_cache = context.application.bot_data.setdefault("users_by_username", {})

    for arg in args:
        username = arg.lstrip("@").lower()
        if not username:
            continue
        target_id = users_cache.get(username)
        if target_id is not None:
            if target_id == sender.id:
                return ("self", None)
            return (target_id, f"@{username}")

    # 3. Ищем в entities (text_mention)
    if msg.entities:
        for ent in msg.entities:
            if ent.type == "text_mention" and hasattr(ent, "user") and ent.user:
                target = ent.user
                if target.id == sender.id:
                    return ("self", None)
                name = f"@{target.username}" if target.username else (target.first_name or str(target.id))
                return (target.id, name)

    return None


async def handle_message_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Реакция 🤡 = -10, реакция 🔥 = +10 к автору сообщения."""
    mr = update.message_reaction
    if not mr or not mr.new_reaction:
        return
    reactor_id = mr.user.id if mr.user else None
    cache = context.application.bot_data.setdefault("msg_cache", {})
    chat_id = mr.chat.id
    message_id = mr.message_id
    author_id = cache.get((chat_id, message_id))
    if author_id is None or (reactor_id is not None and reactor_id == author_id):
        return  # нет в кэше или сам себе
    for r in mr.new_reaction:
        emoji = _get_emoji_from_reaction(r)
        if emoji == "🤡":
            new_rating = add_to_user_rating(author_id, -10)
            try:
                await context.bot.send_message(chat_id=chat_id, text=f"🤡 -10. Рейтинг: {new_rating}")
            except BadRequest:
                pass
            return
        if emoji == "🔥":
            new_rating = add_to_user_rating(author_id, 10)
            try:
                await context.bot.send_message(chat_id=chat_id, text=f"🔥 +10. Рейтинг: {new_rating}")
            except BadRequest:
                pass
            return


async def cmd_minus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/minus или reply — -10. /minus @user тоже работает."""
    res = _resolve_target_user(update, context)
    if res is None:
        await reply_and_cleanup(update, context, "Ответь /minus на сообщение или напиши /minus @username")
        return
    if res[0] == "self":
        await reply_and_cleanup(update, context, "Самому себе менять рейтинг нельзя")
        return
    target_id, display = res
    new_rating = add_to_user_rating(target_id, -10)
    await reply_and_cleanup(update, context, f"📉 -10. Рейтинг {display}: {new_rating}")


async def cmd_plus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/plus или reply — +10. /plus @user тоже работает."""
    res = _resolve_target_user(update, context)
    if res is None:
        await reply_and_cleanup(update, context, "Ответь /plus на сообщение или напиши /plus @username")
        return
    if res[0] == "self":
        await reply_and_cleanup(update, context, "Самому себе менять рейтинг нельзя")
        return
    target_id, display = res
    new_rating = add_to_user_rating(target_id, 10)
    await reply_and_cleanup(update, context, f"📈 +10. Рейтинг {display}: {new_rating}")


def _user_display(user) -> str:
    """Никнейм и имя для отображения."""
    parts = []
    if user.username:
        parts.append(f"@{user.username}")
    name = " ".join(filter(None, [user.first_name, user.last_name]))
    if name:
        parts.append(f"({name})")
    return " ".join(parts) if parts else str(user.id)


async def cmd_my(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /my — мой рейтинг."""
    user = update.effective_user
    if not user:
        return
    rating = get_user_rating(user.id)
    position = get_position(rating)
    display = _user_display(user)
    try:
        await update.message.delete()
    except (BadRequest, Exception):
        pass
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📊 Рейтинг {display}: {rating}\n📍 Положение: {position}",
        )
    except BadRequest:
        pass


HELP_TEXT = """📋 Команды бота:

/danilalox — минус 10 к рейтингу Данилы
/danilaklass — плюс 10 к рейтингу Данилы
/danilarating — рейтинг Данилы
/my — мой рейтинг
/minus — ответь на сообщение или /minus @user: -10
/plus — ответь на сообщение или /plus @user: +10
Реакция 🤡 на сообщение — -10 автору
Реакция 🔥 на сообщение — +10 автору
Самому себе менять рейтинг нельзя
/help — этот список"""


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help — список команд."""
    await reply_and_cleanup(update, context, HELP_TEXT)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /clear — сброс рейтинга. Только для @PurpleTooth."""
    username = (update.effective_user.username or "").lower()
    if username != PURPLETOOTH_USERNAME:
        return  # не отвечаем чужим
    save_rating(0)
    await reply_and_cleanup(update, context, "✅ Рейтинг сброшен на 0")


async def cmd_danilarating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /danilarating — показывает социальный рейтинг. Удаляем только сообщение юзера."""
    try:
        await update.message.delete()
    except (BadRequest, Exception):
        pass
    rating = get_rating()
    position = get_position(rating)
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📊 Социальный рейтинг Данилы: {rating}\n📍 Положение: {position}",
        )
    except BadRequest:
        pass


def main() -> None:
    token = "8584176205:AAGe7iVJrleWNLXM4mBYU6PyW4SPG2amKUU"
    if not token:
        print("Установи переменную TELEGRAM_BOT_TOKEN с токеном бота")
        return

    app = Application.builder().token(token).build()

    # danilarating, my, help — первыми
    app.add_handler(CommandHandler("danilarating", cmd_danilarating))
    app.add_handler(CommandHandler("my", cmd_my))
    app.add_handler(CommandHandler("help", cmd_help))
    # Блокируем chemiakin для всего остального
    app.add_handler(MessageHandler(BlockChimiakin(), block_chemiakin))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("danilalox", cmd_danilalox))
    app.add_handler(CommandHandler("danilaklass", cmd_danila_klass))
    app.add_handler(CommandHandler("danila", cmd_danila_wrapper))
    app.add_handler(CommandHandler("minus", cmd_minus))
    app.add_handler(CommandHandler("plus", cmd_plus))
    app.add_handler(MessageHandler(filters.User(user_id=SELF_LIKER_ID) & filters.TEXT, roast_self_liker))
    app.add_handler(MessageReactionHandler(handle_message_reaction))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        if isinstance(context.error, BadRequest):
            return  # Message to be replied not found и т.п. — игнорируем
        raise context.error

    app.add_error_handler(error_handler)

    # Кэш сообщений для реакций и username->user_id для /plus @user
    msg_cache = {}
    users_by_username = {}
    app.bot_data["msg_cache"] = msg_cache
    app.bot_data["users_by_username"] = users_by_username
    orig_process = app.process_update
    async def process_with_cache(update):
        if update.message and update.message.from_user:
            msg = update.message
            u = msg.from_user
            key = (msg.chat.id, msg.message_id)
            msg_cache[key] = u.id
            if u.username:
                users_by_username[u.username.lower()] = u.id
            if msg.reply_to_message and msg.reply_to_message.from_user:
                ru = msg.reply_to_message.from_user
                if ru.username:
                    users_by_username[ru.username.lower()] = ru.id
            if len(msg_cache) > 5000:
                for k in list(msg_cache.keys())[:1000]:
                    del msg_cache[k]
        return await orig_process(update)
    app.process_update = process_with_cache

    print("Бот запущен!")
    allowed = list(Update.ALL_TYPES) if Update.ALL_TYPES else ["message"]
    if "message_reaction" not in allowed:
        allowed.append("message_reaction")
    app.run_polling(allowed_updates=allowed)


if __name__ == "__main__":
    main()
